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
from typing import Any
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request

from .utils import get_logger

logger = get_logger(module=__name__)

_BASE = "https://api.github.com"
_GRAPHQL_URL = "https://api.github.com/graphql"
_ALLOWED_HOSTS = frozenset({"api.github.com"})
_ALLOWED_SCHEMES = frozenset({"http", "https"})


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
        raise ValueError(
            f"Blocked non-allowlisted host for GitHub API request: {url}"
        )


class _AllowedHostRedirectHandler(HTTPRedirectHandler):
    """Revalidate each redirect hop against the GitHub API host allowlist."""

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
    if token:
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
    if variables:
        payload["variables"] = variables
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        _GRAPHQL_URL,
        data=body,
        headers=_headers(token, accept="application/json"),
        method="POST",
    )
    with _urlopen(req) as resp:
        return json.loads(resp.read().decode())


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

_LINK_NEXT_RE = re.compile(r'<([^>]+)>;\s*rel="next"')


def _paginate_rest(
    url: str,
    token: str | None,
    *,
    accept: str | None = None,
    max_pages: int = 100,
) -> list[Any]:
    """Follow ``Link: <...>; rel="next"`` headers to collect all pages."""
    results: list[Any] = []
    next_url: str | None = url
    page_count = 0
    while next_url:
        if page_count >= max_pages:
            logger.warning("Reached max page limit ({}) for {}", max_pages, url)
            break
        page_count += 1
        try:
            data, headers = _get(next_url, token, accept=accept)
        except Exception as exc:
            logger.warning("Pagination request failed ({}): {}", next_url, exc)
            break
        if isinstance(data, list):
            results.extend(data)
        else:
            logger.warning(
                "Expected list from paginated endpoint, got {}",
                type(data).__name__,
            )
            break
        link_header = headers.get("Link", "")
        match = _LINK_NEXT_RE.search(link_header)
        next_url = match.group(1) if match else None
    return results
