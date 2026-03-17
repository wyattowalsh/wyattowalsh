"""
_github_http.py
~~~~~~~~~~~~~~~
Shared GitHub API HTTP helpers used by fetch_metrics and fetch_history.
"""
from __future__ import annotations

import json
import ssl
import urllib.request
from typing import Any

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
    with urllib.request.urlopen(req, context=ctx) as resp:
        return json.loads(resp.read().decode())
