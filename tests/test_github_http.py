"""Unit tests for scripts._github_http host allowlist enforcement."""

from __future__ import annotations

import json
from email.message import Message
from typing import Any
from unittest.mock import MagicMock
from urllib.error import HTTPError
from urllib.request import Request

import pytest

from scripts._github_http import (
    _ALLOWED_HOSTS,
    _AllowedHostRedirectHandler,
    _are_expected_optional_graphql_errors,
    _assert_allowed_url,
    _get,
    _graphql,
    _GraphQLResponse,
    _paginate_rest,
    _urlopen,
)


class _FakeHeaders(dict):
    """Minimal headers mapping with case-insensitive .get like http.client."""

    def get(self, key: str, default: Any = None) -> Any:  # noqa: A003
        for k, v in self.items():
            if k.lower() == key.lower():
                return v
        return default


class _FakeResponse:
    def __init__(self, body: dict | list, headers: dict | None = None) -> None:
        self._body = json.dumps(body).encode()
        self.headers = _FakeHeaders(headers or {})

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None


# ---------------------------------------------------------------------------
# _assert_allowed_url
# ---------------------------------------------------------------------------


class TestAssertAllowedUrl:
    def test_accepts_api_github_https(self) -> None:
        _assert_allowed_url("https://api.github.com/user")

    def test_rejects_api_github_http(self) -> None:
        with pytest.raises(ValueError, match="Blocked URL scheme"):
            _assert_allowed_url("http://api.github.com/user")

    def test_accepts_hostname_case_insensitive(self) -> None:
        _assert_allowed_url("https://API.GitHub.COM/graphql")

    def test_rejects_non_github_host(self) -> None:
        with pytest.raises(ValueError, match="Blocked non-allowlisted host"):
            _assert_allowed_url("https://evil.example/steal")

    def test_rejects_github_com_www(self) -> None:
        with pytest.raises(ValueError, match="Blocked non-allowlisted host"):
            _assert_allowed_url("https://github.com/wyattowalsh")

    def test_rejects_raw_githubusercontent(self) -> None:
        with pytest.raises(ValueError, match="Blocked non-allowlisted host"):
            _assert_allowed_url("https://raw.githubusercontent.com/x/y")

    def test_rejects_credentials_in_url(self) -> None:
        with pytest.raises(ValueError, match="credentials"):
            _assert_allowed_url("https://user:pass@api.github.com/user")

    def test_rejects_file_scheme(self) -> None:
        with pytest.raises(ValueError, match="Blocked URL scheme"):
            _assert_allowed_url("file:///etc/passwd")

    def test_rejects_missing_host(self) -> None:
        with pytest.raises(ValueError, match="Blocked non-allowlisted host"):
            _assert_allowed_url("https:///path")

    def test_allowed_hosts_is_api_only(self) -> None:
        assert _ALLOWED_HOSTS == frozenset({"api.github.com"})


class TestOptionalGraphqlErrors:
    @pytest.mark.parametrize(
        "errors",
        [
            [{"message": "Something went wrong while executing your query"}],
            [{"type": "FORBIDDEN", "message": "denied"}],
            [{"message": "API rate limit exceeded"}],
        ],
    )
    def test_recognizes_expected_capability_errors(self, errors: list[dict]) -> None:
        assert _are_expected_optional_graphql_errors(errors)

    @pytest.mark.parametrize(
        "errors",
        [
            [],
            [{"message": "Field 'broken' doesn't exist on type 'Query'"}],
            ["not a structured error"],
        ],
    )
    def test_rejects_unexpected_or_malformed_errors(self, errors: list) -> None:
        assert not _are_expected_optional_graphql_errors(errors)


# ---------------------------------------------------------------------------
# Redirect handler
# ---------------------------------------------------------------------------


class TestAllowedHostRedirectHandler:
    def test_allows_redirect_within_allowlist(self) -> None:
        handler = _AllowedHostRedirectHandler()
        req = Request("https://api.github.com/old")
        new_req = handler.redirect_request(
            req,
            fp=None,
            code=302,
            msg="Found",
            headers={},
            newurl="https://api.github.com/new",
        )
        assert new_req is not None
        assert new_req.full_url == "https://api.github.com/new"

    def test_rejects_redirect_off_allowlist(self) -> None:
        handler = _AllowedHostRedirectHandler()
        req = Request("https://api.github.com/old")
        with pytest.raises(ValueError, match="Blocked non-allowlisted host"):
            handler.redirect_request(
                req,
                fp=None,
                code=302,
                msg="Found",
                headers={},
                newurl="https://attacker.example/capture",
            )

    @pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
    def test_rejects_https_to_http_redirect_before_forwarding_authorization(
        self,
        status: int,
    ) -> None:
        handler = _AllowedHostRedirectHandler()
        request = Request(
            "https://api.github.com/graphql",
            data=b"{}",
            headers={"Authorization": "Bearer sentinel"},
            method="POST",
        )

        with pytest.raises(ValueError, match="Blocked URL scheme"):
            handler.redirect_request(
                request,
                fp=None,
                code=status,
                msg="redirect",
                headers={},
                newurl="http://api.github.com/graphql",
            )


# ---------------------------------------------------------------------------
# _get / _graphql / _urlopen (mocked network)
# ---------------------------------------------------------------------------


class TestGetAndGraphql:
    def test_get_rejects_before_network(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def boom(*_a: object, **_k: object) -> None:
            raise AssertionError("network must not be contacted for blocked hosts")

        monkeypatch.setattr("scripts._github_http.urllib.request.build_opener", boom)
        with pytest.raises(ValueError, match="Blocked non-allowlisted host"):
            _get("https://evil.example/x", "tok")

    def test_get_accepts_api_github(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: dict[str, Any] = {}

        class FakeOpener:
            def open(self, req: Request, timeout: float = 30) -> _FakeResponse:
                captured["url"] = req.full_url
                captured["timeout"] = timeout
                return _FakeResponse({"ok": True}, {"X-Test": "1"})

        monkeypatch.setattr(
            "scripts._github_http.urllib.request.build_opener",
            lambda *_a, **_k: FakeOpener(),
        )
        data, headers = _get("https://api.github.com/user", "tok")
        assert data == {"ok": True}
        assert headers.get("X-Test") == "1"
        assert captured["url"] == "https://api.github.com/user"

    def test_graphql_posts_to_allowlisted_host(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        captured: dict[str, Any] = {}
        response = _FakeResponse(
            {"data": {"viewer": {"login": "u"}}},
            {"Retry-After": "17"},
        )

        class FakeOpener:
            def open(self, req: Request, timeout: float = 30) -> _FakeResponse:
                captured["url"] = req.full_url
                captured["method"] = req.get_method()
                return response

        monkeypatch.setattr(
            "scripts._github_http.urllib.request.build_opener",
            lambda *_a, **_k: FakeOpener(),
        )
        result = _graphql("{ viewer { login } }", "tok")
        assert isinstance(result, _GraphQLResponse)
        assert result["data"]["viewer"]["login"] == "u"
        response.headers["Retry-After"] = "99"
        assert result.response_headers == {"retry-after": "17"}
        assert captured["url"] == "https://api.github.com/graphql"
        assert captured["method"] == "POST"

    def test_graphql_rejects_non_object_json(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class FakeOpener:
            def open(self, req: Request, timeout: float = 30) -> _FakeResponse:
                return _FakeResponse([])

        monkeypatch.setattr(
            "scripts._github_http.urllib.request.build_opener",
            lambda *_a, **_k: FakeOpener(),
        )

        with pytest.raises(ValueError, match="JSON object"):
            _graphql("{ viewer { login } }", "tok")

    def test_urlopen_rejects_blocked_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "scripts._github_http.urllib.request.build_opener",
            MagicMock(side_effect=AssertionError("must not open")),
        )
        with pytest.raises(ValueError, match="Blocked non-allowlisted host"):
            _urlopen(Request("https://not-github.example/"))


class TestPaginateRestAllowlist:
    def test_stops_when_next_link_host_blocked(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: list[str] = []

        def fake_get(url: str, token: str | None, *, accept: str | None = None):
            del token, accept
            calls.append(url)
            if "evil" in url:
                raise ValueError(
                    f"Blocked non-allowlisted host for GitHub API request: {url}"
                )
            return (
                [{"id": 1}],
                _FakeHeaders({"Link": '<https://evil.example/page2>; rel="next"'}),
            )

        monkeypatch.setattr("scripts._github_http._get", fake_get)
        results = _paginate_rest("https://api.github.com/page1", "tok")
        assert results == [{"id": 1}]
        assert calls == [
            "https://api.github.com/page1",
            "https://evil.example/page2",
        ]

    def test_optional_http_status_is_informational(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        error = HTTPError(
            "https://api.github.com/optional",
            403,
            "Forbidden",
            hdrs=Message(),
            fp=None,
        )
        monkeypatch.setattr(
            "scripts._github_http._get",
            MagicMock(side_effect=error),
        )
        logger = MagicMock()
        monkeypatch.setattr("scripts._github_http.logger", logger)

        result = _paginate_rest(
            "https://api.github.com/optional",
            "tok",
            optional_http_statuses=(403,),
        )

        assert result == []
        logger.info.assert_called_once_with(
            "Optional paginated endpoint unavailable ({}): HTTP {}",
            "https://api.github.com/optional",
            403,
        )
        logger.warning.assert_not_called()

    def test_unexpected_http_status_still_warns(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        error = HTTPError(
            "https://api.github.com/optional",
            500,
            "Server Error",
            hdrs=Message(),
            fp=None,
        )
        monkeypatch.setattr(
            "scripts._github_http._get",
            MagicMock(side_effect=error),
        )
        logger = MagicMock()
        monkeypatch.setattr("scripts._github_http.logger", logger)

        result = _paginate_rest(
            "https://api.github.com/optional",
            "tok",
            optional_http_statuses=(403,),
        )

        assert result == []
        logger.warning.assert_called_once_with(
            "Pagination request failed ({}): {}",
            "https://api.github.com/optional",
            error,
        )


class TestRedirectIntegration:
    def test_redirect_handler_wired_into_opener(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Ensure build_opener receives the allowlist redirect handler."""
        handlers_seen: list[type] = []

        class FakeOpener:
            def open(self, req: Request, timeout: float = 30) -> _FakeResponse:
                del timeout
                return _FakeResponse({"ok": True})

        def fake_build_opener(*handlers: object) -> FakeOpener:
            for h in handlers:
                handlers_seen.append(type(h))
            return FakeOpener()

        monkeypatch.setattr(
            "scripts._github_http.urllib.request.build_opener",
            fake_build_opener,
        )
        _get("https://api.github.com/user", None)
        assert _AllowedHostRedirectHandler in handlers_seen
