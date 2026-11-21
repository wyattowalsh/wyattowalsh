"""
_github_http.py
~~~~~~~~~~~~~~~
Shared GitHub API HTTP helpers used by fetch_metrics and fetch_history.
"""

from __future__ import annotations

import json
import re
import ssl
import urllib.request
from collections.abc import Collection, Mapping
from email.message import Message
from typing import Any, override
from urllib.error import HTTPError
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request

from .utils import get_logger

logger = get_logger(module=__name__)

_BASE = "https://api.github.com"
_GRAPHQL_URL = "https://api.github.com/graphql"
_ALLOWED_HOSTS = frozenset({"api.github.com"})
_ALLOWED_SCHEMES = frozenset({"https"})
_EXPECTED_OPTIONAL_GRAPHQL_ERROR_TYPES = frozenset(
    {"FORBIDDEN", "INTERNAL", "RATE_LIMITED", "SERVICE_UNAVAILABLE"}
)
_EXPECTED_OPTIONAL_GRAPHQL_ERROR_MESSAGES = (
    "something went wrong while executing your query",
    "resource not accessible by integration",
    "insufficient scope",
    "rate limit",
)


class _GraphQLResponse(dict[str, Any]):
    """GraphQL JSON object with a detached, case-normalized header snapshot."""

    def __init__(
        self,
        payload: Mapping[str, Any],
        *,
        response_headers: Any,
    ) -> None:
        super().__init__(payload)
        items = getattr(response_headers, "items", None)
        self.response_headers: dict[str, str] = (
            {str(name).casefold(): str(value) for name, value in items()}
            if callable(items)
            else {}
        )


def _are_expected_optional_graphql_errors(errors: Any) -> bool:
    """Return whether every GraphQL error is an expected capability gap."""
    if not isinstance(errors, list) or not errors:
        return False
    for error in errors:
        if not isinstance(error, dict):
            return False
        error_type = str(error.get("type") or "").upper()
        message = str(error.get("message") or "").casefold()
        if error_type in _EXPECTED_OPTIONAL_GRAPHQL_ERROR_TYPES:
            continue
        if any(
            fragment in message
            for fragment in _EXPECTED_OPTIONAL_GRAPHQL_ERROR_MESSAGES
        ):
            continue
        return False
    return True


def _assert_allowed_url(url: str) -> None:
    """Reject URLs whose host is outside the GitHub API allowlist."""
    try:
        parsed = urlparse(url)
    except ValueError as exc:
        raise ValueError(f"Invalid URL for GitHub API request: {url}") from exc

    scheme = (parsed.scheme or "").lower()
    if scheme not in _ALLOWED_SCHEMES:
        raise ValueError(f"Blocked URL scheme for GitHub API request: {url}")

    if parsed.username is not None or parsed.password is not None:
        raise ValueError(f"Blocked URL with credentials for GitHub API request: {url}")

    host = (parsed.hostname or "").lower()
    if not host or host not in _ALLOWED_HOSTS:
        raise ValueError(f"Blocked non-allowlisted host for GitHub API request: {url}")


class _AllowedHostRedirectHandler(HTTPRedirectHandler):
    """Revalidate each redirect hop against the GitHub API host allowlist."""

    @override
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        _assert_allowed_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _urlopen(req: Request):
    """Open *req* after allowlist checks, revalidating redirect hops."""
    _assert_allowed_url(req.full_url)
    ctx = ssl.create_default_context()
    opener = urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=ctx),
        _AllowedHostRedirectHandler(),
    )
    return opener.open(req, timeout=30)


def _headers(token: str | None, *, accept: str | None = None) -> dict[str, str]:
    """Build request headers, optionally with auth and custom Accept."""
    hdrs: dict[str, str] = {
        "Accept": accept or "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token is not None and token != "":
        hdrs["Authorization"] = f"Bearer {token}"
    return hdrs


def _get(url: str, token: str | None, *, accept: str | None = None) -> tuple[Any, Any]:
    """Perform an authenticated GET and return (parsed_json, response_headers)."""
    req = urllib.request.Request(url, headers=_headers(token, accept=accept))
    with _urlopen(req) as resp:
        return json.loads(resp.read().decode()), resp.headers


def _graphql(
    query: str,
    token: str,
    *,
    variables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute a GitHub GraphQL query (requires token)."""
    payload: dict[str, Any] = {"query": query}
    if variables is not None and len(variables) > 0:
        payload["variables"] = variables
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        _GRAPHQL_URL,
        data=body,
        headers=_headers(token, accept="application/json"),
        method="POST",
    )
    with _urlopen(req) as resp:
        payload = json.loads(resp.read().decode())
        if not isinstance(payload, dict):
            raise ValueError("GitHub GraphQL response was not a JSON object")
        return _GraphQLResponse(payload, response_headers=resp.headers)


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

_LINK_TARGET = re.compile(r"\s*<([^<>\s]+)>\s*")
_LINK_PARAM = re.compile(
    r""";\s*([!#$%&'*+.^_`|~A-Za-z0-9-]+)\s*"""
    r"""(?:=\s*(?:"((?:\\.|[^"\\])*)"|([^"=,;\s]+)))?\s*"""
)


def _next_page_url(header: str, page_url: str) -> str | None:
    """Read a GitHub Link field, preserving delimiters inside quoted parameters."""
    pos = 0
    next_url = None
    while pos < len(header):
        target = _LINK_TARGET.match(header, pos)
        if target is None:
            raise ValueError("Malformed GitHub pagination Link target")
        pos = target.end()
        relations: str | None = None
        while parameter := _LINK_PARAM.match(header, pos):
            name, quoted, token = parameter.groups()
            if name.lower() == "rel":
                if relations is not None:
                    raise ValueError("Duplicate relation in GitHub pagination Link")
                relations = str(quoted if quoted is not None else token or "")
            pos = parameter.end()
        if relations is None or not relations.strip():
            raise ValueError("Missing relation in GitHub pagination Link")
        if "next" in relations.lower().split():
            if next_url is not None:
                raise ValueError("Ambiguous next target in GitHub pagination Link")
            next_url = urljoin(page_url, str(target.group(1)))
        if pos == len(header):
            break
        if header[pos] != ",":
            raise ValueError("Malformed GitHub pagination Link separator")
        pos += 1
    return next_url


def _paginate_rest(
    url: str,
    token: str | None,
    *,
    accept: str | None = None,
    max_pages: int = 100,
    optional_http_statuses: Collection[int] = (),
    require_complete: bool = False,
) -> list[Any]:
    """Follow ``Link`` headers and collect pages from a REST endpoint.

    ``optional_http_statuses`` identifies capability-related response codes for
    a specific caller. Those codes stop pagination at INFO while all other
    request failures remain warnings. Callers must opt in explicitly; the
    default behavior is unchanged. Required inventories raise instead of
    returning a partial list when traversal is interrupted.
    """
    results: list[Any] = []
    next_url: str | None = url
    page_count = 0
    while next_url is not None and next_url != "":
        if page_count >= max_pages:
            if require_complete:
                raise ValueError("Required GitHub inventory exceeded its page limit")
            logger.warning("Reached max page limit ({}) for {}", max_pages, url)
            break
        page_count += 1
        try:
            data, headers = _get(next_url, token, accept=accept)
        except Exception as exc:
            if require_complete:
                raise
            if isinstance(exc, HTTPError) and exc.code in optional_http_statuses:
                logger.info(
                    "Optional paginated endpoint unavailable ({}): HTTP {}",
                    next_url,
                    exc.code,
                )
            else:
                logger.warning("Pagination request failed ({}): {}", next_url, exc)
            break
        if isinstance(data, list):
            results.extend(data)
        else:
            if require_complete:
                raise TypeError("Required GitHub inventory page must be a list")
            logger.warning(
                "Expected list from paginated endpoint, got {}",
                type(data).__name__,
            )
            break
        try:
            link_header = (
                ",".join(headers.get_all("Link", []))
                if isinstance(headers, Message)
                else headers.get("Link", "")
            )
            if not isinstance(link_header, str):
                raise TypeError("Invalid GitHub pagination Link header")
            next_url = _next_page_url(link_header.strip(), next_url)
        except (TypeError, ValueError) as exc:
            if require_complete:
                raise
            logger.warning("Stopping optional GitHub pagination: {}", exc)
            break
    return results
