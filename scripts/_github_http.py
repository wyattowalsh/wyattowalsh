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

from .utils import get_logger

logger = get_logger(module=__name__)

_BASE = "https://api.github.com"
_GRAPHQL_URL = "https://api.github.com/graphql"


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
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        return json.loads(resp.read().decode()), resp.headers


def _graphql(query: str, token: str) -> dict[str, Any]:
    """Execute a GitHub GraphQL query (requires token)."""
    body = json.dumps({"query": query}).encode()
    req = urllib.request.Request(
        _GRAPHQL_URL,
        data=body,
        headers=_headers(token, accept="application/json"),
        method="POST",
    )
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
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
) -> list[Any]:
    """Follow ``Link: <...>; rel="next"`` headers to collect all pages."""
    results: list[Any] = []
    next_url: str | None = url
    while next_url:
        try:
            data, headers = _get(next_url, token, accept=accept)
        except Exception as exc:
            logger.warning("Pagination request failed ({}): {}", next_url, exc)
            break
        if isinstance(data, list):
            results.extend(data)
        else:
            logger.warning("Expected list from paginated endpoint, got {}", type(data).__name__)
            break
        link_header = headers.get("Link", "")
        match = _LINK_NEXT_RE.search(link_header)
        next_url = match.group(1) if match else None
    return results
