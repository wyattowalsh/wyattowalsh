"""Focused contracts for the first-party starred-list generator."""

from __future__ import annotations

import inspect
import multiprocessing
import os
from email.message import Message
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError

import pytest

from scripts import starred_lists
from scripts._github_http import _GraphQLResponse
from scripts.starred_lists import StarredListsError
from scripts.word_clouds import parse_markdown_for_word_cloud_frequencies


def _hold_cooperating_publication_lock(
    languages_output: str,
    topics_output: str,
    acquired: Any,
    release: Any,
) -> None:
    real_snapshot = starred_lists._snapshot_output
    snapshot_calls = 0

    def _block_during_first_snapshot(path: Path) -> Any:
        nonlocal snapshot_calls
        snapshot = real_snapshot(path)
        snapshot_calls += 1
        if snapshot_calls == 1:
            acquired.set()
            if not release.wait(10):
                raise RuntimeError("timed out waiting to release publication lock")
        return snapshot

    setattr(starred_lists, "_snapshot_output", _block_during_first_snapshot)
    starred_lists._transactional_write_pair(
        Path(languages_output),
        "first languages",
        Path(topics_output),
        "first topics",
    )


def _run_cooperating_publication(
    languages_output: str,
    topics_output: str,
    attempted: Any,
    completed: Any,
) -> None:
    attempted.set()
    starred_lists._transactional_write_pair(
        Path(languages_output),
        "second languages",
        Path(topics_output),
        "second topics",
    )
    completed.set()


def _node(
    node_id: str,
    name: str,
    *,
    language: str | None = "Python",
    topics: tuple[tuple[str, int], ...] = (),
    description: str = "",
    private: bool = False,
    url: str | None = None,
) -> dict[str, Any]:
    language_edges = [] if language is None else [{"node": {"name": language}}]
    return {
        "id": node_id,
        "nameWithOwner": name,
        "description": description,
        "url": url or f"https://github.com/{name}",
        "isPrivate": private,
        "languages": {"edges": language_edges},
        "repositoryTopics": {
            "nodes": [
                {"topic": {"name": topic, "stargazerCount": count}}
                for topic, count in topics
            ]
        },
    }


def _response(
    nodes: list[dict[str, Any]],
    *,
    total: int,
    has_next: bool = False,
    cursor: str | None = None,
) -> dict[str, Any]:
    return {
        "data": {
            "user": {
                "starredRepositories": {
                    "totalCount": total,
                    "nodes": nodes,
                    "pageInfo": {
                        "hasNextPage": has_next,
                        "endCursor": cursor,
                    },
                }
            }
        }
    }


def _http_error(
    status: int,
    headers: dict[str, str] | None = None,
) -> HTTPError:
    response_headers = Message()
    for name, value in (headers or {}).items():
        response_headers[name] = value
    return HTTPError(
        "https://api.github.com/graphql",
        status,
        "untrusted response text",
        hdrs=response_headers,
        fp=None,
    )


def test_transient_graphql_failures_retry_with_deterministic_backoff(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outcomes: Any = iter(
        (
            _http_error(504),
            URLError("untrusted transport detail"),
            TimeoutError("untrusted timeout detail"),
            _response([_node("R1", "owner/repo")], total=1),
        )
    )
    calls = 0
    delays: list[float] = []
    retry_logs: list[tuple[object, ...]] = []

    def _fake_graphql(*_args: object, **_kwargs: object) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        outcome = next(outcomes)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    class _RetryLogger:
        def info(self, *args: object) -> None:
            retry_logs.append(args)

    monkeypatch.setattr(starred_lists, "_graphql", _fake_graphql)
    monkeypatch.setattr(starred_lists.time, "sleep", delays.append)
    monkeypatch.setattr(starred_lists, "logger", _RetryLogger())

    repositories = starred_lists.fetch_starred_repositories("owner", "secret-token")

    assert [repository.name_with_owner for repository in repositories] == ["owner/repo"]
    assert calls == 4
    assert delays == [1.0, 2.0, 4.0]
    assert len(retry_logs) == 3
    rendered_logs = repr(retry_logs)
    assert "secret-token" not in rendered_logs
    assert "untrusted response text" not in rendered_logs
    assert "untrusted transport detail" not in rendered_logs
    assert "untrusted timeout detail" not in rendered_logs


@pytest.mark.parametrize("status", [429, 502, 503, 504])
def test_retryable_http_status_contract(status: int) -> None:
    assert starred_lists._is_retryable_graphql_error(_http_error(status))


@pytest.mark.parametrize(
    ("headers", "expected_delay"),
    [
        ({"Retry-After": "7"}, 7.0),
        (
            {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1012"},
            12.0,
        ),
    ],
)
def test_identified_http_403_rate_limits_retry_with_authoritative_delay(
    headers: dict[str, str],
    expected_delay: float,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outcomes: Any = iter(
        (
            _http_error(403, headers),
            _response([_node("R1", "owner/repo")], total=1),
        )
    )
    calls = 0
    delays: list[float] = []

    def _fake_graphql(*_args: object, **_kwargs: object) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        outcome = next(outcomes)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(starred_lists, "_graphql", _fake_graphql)
    monkeypatch.setattr(starred_lists.time, "sleep", delays.append)
    monkeypatch.setattr(starred_lists.time, "time", lambda: 1000.0)

    repositories = starred_lists.fetch_starred_repositories("owner", "token")

    assert [repository.name_with_owner for repository in repositories] == ["owner/repo"]
    assert calls == 2
    assert delays == [expected_delay]


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"X-RateLimit-Remaining": "1", "X-RateLimit-Reset": "1012"},
        {"Retry-After": "not-a-number"},
        {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "invalid"},
    ],
)
def test_generic_or_malformed_http_403_is_not_retried(
    headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    delays: list[float] = []

    def _forbidden(*_args: object, **_kwargs: object) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        raise _http_error(403, headers)

    monkeypatch.setattr(starred_lists, "_graphql", _forbidden)
    monkeypatch.setattr(starred_lists.time, "sleep", delays.append)
    monkeypatch.setattr(starred_lists.time, "time", lambda: 1000.0)

    with pytest.raises(StarredListsError, match="request failed"):
        starred_lists.fetch_starred_repositories("owner", "token")

    assert calls == 1
    assert delays == []


@pytest.mark.parametrize(
    ("headers", "expected_delay"),
    [
        ({"Retry-After": "9"}, 9.0),
        (
            {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1014"},
            14.0,
        ),
        ({}, starred_lists._SECONDARY_RATE_LIMIT_FALLBACK_SECONDS),
    ],
)
def test_http_200_rate_limited_errors_retry_with_bounded_delay(
    headers: dict[str, str],
    expected_delay: float,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outcomes: Any = iter(
        (
            _GraphQLResponse(
                {"errors": [{"type": "RATE_LIMITED", "message": "untrusted"}]},
                response_headers=headers,
            ),
            _response([_node("R1", "owner/repo")], total=1),
        )
    )
    calls = 0
    delays: list[float] = []

    def _fake_graphql(*_args: object, **_kwargs: object) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        return next(outcomes)

    monkeypatch.setattr(starred_lists, "_graphql", _fake_graphql)
    monkeypatch.setattr(starred_lists.time, "sleep", delays.append)
    monkeypatch.setattr(starred_lists.time, "time", lambda: 1000.0)

    repositories = starred_lists.fetch_starred_repositories("owner", "token")

    assert len(repositories) == 1
    assert calls == 2
    assert delays == [expected_delay]


@pytest.mark.parametrize(
    "errors",
    [
        [{"type": "FORBIDDEN", "message": "generic"}],
        [
            {"type": "RATE_LIMITED", "message": "limited"},
            {"type": "FORBIDDEN", "message": "generic"},
        ],
        [{"message": "rate limit words without the authoritative type"}],
    ],
)
def test_generic_http_200_graphql_errors_are_not_retried(
    errors: list[dict[str, str]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    delays: list[float] = []

    def _generic_error(*_args: object, **_kwargs: object) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        return {"errors": errors, "data": None}

    monkeypatch.setattr(starred_lists, "_graphql", _generic_error)
    monkeypatch.setattr(starred_lists.time, "sleep", delays.append)

    with pytest.raises(StarredListsError, match="contained errors"):
        starred_lists.fetch_starred_repositories("owner", "token")

    assert calls == 1
    assert delays == []


def test_rate_limit_delay_that_exceeds_deadline_is_not_slept(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    delays: list[float] = []

    def _rate_limited(*_args: object, **_kwargs: object) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        return {"errors": [{"type": "RATE_LIMITED"}], "data": None}

    monkeypatch.setattr(starred_lists, "_graphql", _rate_limited)
    monkeypatch.setattr(starred_lists.time, "monotonic", lambda: 0.0)
    monkeypatch.setattr(starred_lists.time, "sleep", delays.append)
    monkeypatch.setattr(starred_lists, "_FETCH_DEADLINE_SECONDS", 30.0)

    with pytest.raises(StarredListsError, match="request failed"):
        starred_lists.fetch_starred_repositories("owner", "token")

    assert calls == 1
    assert delays == []


def test_transient_retry_exhaustion_and_nonretryable_failure_are_bounded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    delays: list[float] = []
    calls = 0

    def _always_unavailable(*_args: object, **_kwargs: object) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        raise _http_error(503)

    monkeypatch.setattr(starred_lists, "_graphql", _always_unavailable)
    monkeypatch.setattr(starred_lists.time, "sleep", delays.append)
    with pytest.raises(StarredListsError, match="request failed"):
        starred_lists.fetch_starred_repositories("owner", "token")
    assert calls == 1 + starred_lists._MAX_TRANSIENT_RETRIES
    assert delays == [1.0, 2.0, 4.0]

    calls = 0
    delays.clear()

    def _nonretryable(*_args: object, **_kwargs: object) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        raise _http_error(500)

    monkeypatch.setattr(starred_lists, "_graphql", _nonretryable)
    with pytest.raises(StarredListsError, match="request failed"):
        starred_lists.fetch_starred_repositories("owner", "token")
    assert calls == 1
    assert delays == []
    assert starred_lists._FETCH_DEADLINE_SECONDS < 30 * 60


def test_retry_deadline_stops_before_request_or_delay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    delays: list[float] = []

    def _transient_failure(*_args: object, **_kwargs: object) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        raise URLError("transient")

    monkeypatch.setattr(starred_lists, "_graphql", _transient_failure)
    monkeypatch.setattr(starred_lists.time, "sleep", delays.append)
    monkeypatch.setattr(starred_lists.time, "monotonic", lambda: 10.0)
    with pytest.raises(TimeoutError, match="deadline"):
        starred_lists._graphql_with_transient_retries(
            "owner", token="token", after=None, page_number=1, deadline=10.0
        )
    assert calls == 0

    monkeypatch.setattr(starred_lists.time, "monotonic", lambda: 0.0)
    with pytest.raises(URLError):
        starred_lists._graphql_with_transient_retries(
            "owner", token="token", after=None, page_number=1, deadline=0.5
        )
    assert calls == 1
    assert delays == []


def test_paginated_fetch_renders_both_deterministic_consumer_formats(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    description = '<b> & "quoted" [link] ' + ("x" * 240)
    pages = iter(
        [
            _response(
                [
                    _node(
                        "R3",
                        "zeta/repo",
                        topics=(("ai", 501),),
                        description=description,
                    ),
                    _node(
                        "R2",
                        "middle/no-language",
                        language=None,
                        topics=(("edge", 500),),
                    ),
                ],
                total=4,
                has_next=True,
                cursor="cursor-1",
            ),
            _response(
                [
                    _node(
                        "R4",
                        "private/hidden",
                        language="Go",
                        topics=(("ai", 9_999),),
                        private=True,
                    ),
                    _node(
                        "R1",
                        "alpha/repo",
                        topics=(("data", 900),),
                    ),
                ],
                total=4,
            ),
        ]
    )
    calls: list[dict[str, Any]] = []

    def _fake_graphql(
        query: str,
        token: str,
        *,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        assert "starredRepositories" in query
        assert token == "secret-token"
        calls.append(dict(variables or {}))
        return next(pages)

    monkeypatch.setattr(starred_lists, "_graphql", _fake_graphql)
    languages_output = tmp_path / "languages.md"
    topics_output = tmp_path / "topics.md"

    result = starred_lists.generate_starred_lists(
        owner="wyattowalsh",
        token="secret-token",
        languages_output=languages_output,
        topics_output=topics_output,
        topic_threshold=500,
    )

    assert result == (languages_output, topics_output)
    assert calls == [
        {"owner": "wyattowalsh", "after": None},
        {"owner": "wyattowalsh", "after": "cursor-1"},
    ]
    languages = languages_output.read_text(encoding="utf-8")
    assert "repository-owned `scripts.starred_lists`" in languages
    assert "maguowei" not in languages
    assert "private/hidden" not in languages
    assert languages.index("alpha/repo") < languages.index("zeta/repo")
    assert "&lt;b&gt; &amp; &quot;quoted&quot; &#91;link&#93;" in languages
    assert description not in languages

    assert parse_markdown_for_word_cloud_frequencies(languages_output) == {
        "Others": 1,
        "Python": 2,
    }
    assert parse_markdown_for_word_cloud_frequencies(topics_output) == {
        "ai": 1,
        "data": 1,
        "others": 1,
    }


def test_category_anchors_and_item_order_are_stable() -> None:
    repositories = (
        starred_lists._Repository(
            node_id="R2",
            name_with_owner="owner/zeta",
            description="",
            url="https://github.com/owner/zeta",
            is_private=False,
            primary_language="C#",
            topics=(),
        ),
        starred_lists._Repository(
            node_id="R1",
            name_with_owner="owner/alpha",
            description="",
            url="https://github.com/owner/alpha",
            is_private=False,
            primary_language="C",
            topics=(),
        ),
        starred_lists._Repository(
            node_id="R3",
            name_with_owner="owner/beta",
            description="",
            url="https://github.com/owner/beta",
            is_private=False,
            primary_language="C++",
            topics=(),
        ),
    )

    first, _ = starred_lists.render_starred_lists("owner", repositories)
    second, _ = starred_lists.render_starred_lists(
        "owner", tuple(reversed(repositories))
    )

    assert first == second
    assert "- [C](#c)" in first
    assert "- [C#](#c-1)" in first
    assert "- [C++](#c-2)" in first


def test_untrusted_field_validators_reject_malformed_values() -> None:
    with pytest.raises(StarredListsError, match="not a list"):
        starred_lists._required_sequence("not-a-list", label="field")
    with pytest.raises(StarredListsError, match="valid string"):
        starred_lists._required_string("", label="field")
    with pytest.raises(StarredListsError, match="owner"):
        starred_lists._validate_owner("-invalid")
    assert starred_lists._validate_owner("legacy-owner-") == "legacy-owner-"

    with pytest.raises(StarredListsError, match="multiple edges"):
        starred_lists._parse_primary_language(
            {
                "edges": [
                    {"node": {"name": "Python"}},
                    {"node": {"name": "Rust"}},
                ]
            },
            label="languages",
        )
    with pytest.raises(StarredListsError, match="text contract"):
        starred_lists._parse_primary_language(
            {"edges": [{"node": {"name": " "}}]},
            label="languages",
        )

    def _topic_node(name: str, count: object) -> dict[str, object]:
        return {"topic": {"name": name, "stargazerCount": count}}

    for nodes, message in (
        ([_topic_node("INVALID", 1)], "text contract"),
        ([_topic_node("-invalid", 1)], "text contract"),
        ([_topic_node("x" * 51, 1)], "text contract"),
        ([_topic_node("valid", True)], "stargazer count"),
        ([_topic_node("valid", 1), _topic_node("valid", 2)], "duplicate"),
    ):
        with pytest.raises(StarredListsError, match=message):
            starred_lists._parse_topics({"nodes": nodes}, label="topics")

    assert (
        starred_lists._parse_topics(
            {"nodes": [_topic_node("knowledge-", 1)]}, label="topics"
        )[0].name
        == "knowledge-"
    )

    invalid_name = _node("R1", "owner/repo/extra")
    with pytest.raises(StarredListsError, match="name"):
        starred_lists._parse_repository(invalid_name, page=1, index=0)
    invalid_privacy = _node("R1", "owner/repo")
    invalid_privacy["isPrivate"] = "false"
    with pytest.raises(StarredListsError, match="privacy"):
        starred_lists._parse_repository(invalid_privacy, page=1, index=0)
    missing_description = _node("R1", "owner/repo")
    missing_description["description"] = None
    assert (
        starred_lists._parse_repository(
            missing_description, page=1, index=0
        ).description
        == ""
    )
    invalid_description = _node("R1", "owner/repo")
    invalid_description["description"] = 42
    with pytest.raises(StarredListsError, match="description"):
        starred_lists._parse_repository(invalid_description, page=1, index=0)

    with pytest.raises(StarredListsError, match="GITHUB_TOKEN"):
        starred_lists.fetch_starred_repositories("owner", " ")
    with pytest.raises(StarredListsError, match="threshold"):
        starred_lists.render_starred_lists("owner", (), topic_threshold=-1)
    with pytest.raises(Exception, match="integer"):
        starred_lists._non_negative_integer("not-an-integer")
    with pytest.raises(Exception, match="non-negative"):
        starred_lists._non_negative_integer("-1")


def test_empty_public_repository_set_renders_explicit_empty_contract() -> None:
    languages, topics = starred_lists.render_starred_lists("owner", ())
    assert "_No public starred repositories._" in languages
    assert "_No public starred repositories._" in topics


@pytest.mark.parametrize(
    "response",
    [
        {"errors": [{"message": "denied"}], "data": {}},
        {"data": {"user": None}},
        _response([], total=1),
        _response(
            [_node("R1", "owner/repo", url="http://github.com/owner/repo")],
            total=1,
        ),
    ],
)
def test_graphql_or_shape_failures_leave_both_prior_outputs_unchanged(
    response: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    languages_output = tmp_path / "languages.md"
    topics_output = tmp_path / "topics.md"
    languages_output.write_text("old languages", encoding="utf-8")
    topics_output.write_text("old topics", encoding="utf-8")
    monkeypatch.setattr(starred_lists, "_graphql", lambda *_args, **_kwargs: response)

    with pytest.raises(StarredListsError):
        starred_lists.generate_starred_lists(
            owner="owner",
            token="token",
            languages_output=languages_output,
            topics_output=topics_output,
        )

    assert languages_output.read_text(encoding="utf-8") == "old languages"
    assert topics_output.read_text(encoding="utf-8") == "old topics"


def test_network_failure_leaves_prior_outputs_unchanged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    languages_output = tmp_path / "languages.md"
    topics_output = tmp_path / "topics.md"
    languages_output.write_text("old languages", encoding="utf-8")
    topics_output.write_text("old topics", encoding="utf-8")

    def _fail(*_args: object, **_kwargs: object) -> dict[str, Any]:
        raise OSError("network down")

    monkeypatch.setattr(starred_lists, "_graphql", _fail)

    with pytest.raises(StarredListsError, match="request failed"):
        starred_lists.generate_starred_lists(
            owner="owner",
            token="token",
            languages_output=languages_output,
            topics_output=topics_output,
        )

    assert languages_output.read_text(encoding="utf-8") == "old languages"
    assert topics_output.read_text(encoding="utf-8") == "old topics"


def test_second_publication_failure_rolls_back_first_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    languages_output = tmp_path / "languages.md"
    topics_output = tmp_path / "topics.md"
    languages_output.write_text("old languages", encoding="utf-8")
    topics_output.write_text("old topics", encoding="utf-8")
    monkeypatch.setattr(
        starred_lists,
        "_graphql",
        lambda *_args, **_kwargs: _response(
            [_node("R1", "owner/repo", topics=(("python", 1_000),))],
            total=1,
        ),
    )
    real_replace = starred_lists.os.replace
    replace_calls = 0

    def _fail_second_replace(source: Path, destination: Path) -> None:
        nonlocal replace_calls
        replace_calls += 1
        if replace_calls == 2:
            raise OSError("simulated second-output failure")
        real_replace(source, destination)

    monkeypatch.setattr(starred_lists.os, "replace", _fail_second_replace)

    with pytest.raises(OSError, match="second-output failure"):
        starred_lists.generate_starred_lists(
            owner="owner",
            token="token",
            languages_output=languages_output,
            topics_output=topics_output,
        )

    assert replace_calls == 3
    assert languages_output.read_text(encoding="utf-8") == "old languages"
    assert topics_output.read_text(encoding="utf-8") == "old topics"
    assert not list(tmp_path.glob(".*.publish.tmp"))


@pytest.mark.skipif(
    "spawn" not in multiprocessing.get_all_start_methods(),
    reason="cross-process advisory-lock test requires multiprocessing support",
)
def test_two_cooperating_publishers_serialize_across_distinct_parents(
    tmp_path: Path,
) -> None:
    languages_output = tmp_path / "a" / "languages.md"
    topics_output = tmp_path / "b" / "topics.md"
    languages_output.parent.mkdir()
    topics_output.parent.mkdir()
    context = multiprocessing.get_context("spawn")
    first_acquired = context.Event()
    release_first = context.Event()
    second_attempted = context.Event()
    second_completed = context.Event()
    first = context.Process(
        target=_hold_cooperating_publication_lock,
        args=(
            str(languages_output),
            str(topics_output),
            first_acquired,
            release_first,
        ),
    )
    second = context.Process(
        target=_run_cooperating_publication,
        args=(
            str(languages_output),
            str(topics_output),
            second_attempted,
            second_completed,
        ),
    )

    try:
        first.start()
        assert first_acquired.wait(5)
        second.start()
        assert second_attempted.wait(5)
        assert not second_completed.wait(0.25)
        assert second.is_alive()
        release_first.set()
        assert second_completed.wait(5)
    finally:
        release_first.set()
        for process in (first, second):
            process.join(5)
            if process.is_alive():
                process.terminate()
                process.join(5)

    assert first.exitcode == 0
    assert second.exitcode == 0
    assert languages_output.read_text(encoding="utf-8") == "second languages"
    assert topics_output.read_text(encoding="utf-8") == "second topics"


def test_prepublication_digest_check_preserves_noncooperating_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    languages_output = tmp_path / "languages.md"
    topics_output = tmp_path / "topics.md"
    languages_output.write_text("old languages", encoding="utf-8")
    topics_output.write_text("old topics", encoding="utf-8")
    initial_revision = starred_lists._output_revision(languages_output)
    real_stage_payload = starred_lists._stage_payload
    stage_calls = 0

    def _mutate_after_staging(
        path: Path,
        payload: bytes,
        *,
        mode: int,
    ) -> Path:
        nonlocal stage_calls
        stage = real_stage_payload(path, payload, mode=mode)
        stage_calls += 1
        if stage_calls == 2:
            status = languages_output.stat()
            languages_output.write_text("bad languages", encoding="utf-8")
            os.utime(
                languages_output,
                ns=(status.st_atime_ns, status.st_mtime_ns),
            )
            assert starred_lists._output_revision(languages_output) == initial_revision
        return stage

    monkeypatch.setattr(starred_lists, "_stage_payload", _mutate_after_staging)

    with pytest.raises(StarredListsError, match="changed before publication"):
        starred_lists._transactional_write_pair(
            languages_output,
            "new languages",
            topics_output,
            "new topics",
        )

    assert languages_output.read_text(encoding="utf-8") == "bad languages"
    assert topics_output.read_text(encoding="utf-8") == "old topics"
    assert not list(tmp_path.glob(".*.publish.tmp"))


def test_rollback_refuses_same_revision_noncooperating_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    languages_output = tmp_path / "languages.md"
    topics_output = tmp_path / "topics.md"
    languages_output.write_text("old languages", encoding="utf-8")
    topics_output.write_text("old topics", encoding="utf-8")
    real_replace = starred_lists.os.replace
    replace_calls = 0
    published_revision: tuple[int, int, int, int] | None = None

    def _mutate_before_rollback(source: Path, destination: Path) -> None:
        nonlocal published_revision, replace_calls
        replace_calls += 1
        if replace_calls == 1:
            real_replace(source, destination)
            published_revision = starred_lists._output_revision(languages_output)
            return
        if replace_calls == 2:
            status = languages_output.stat()
            languages_output.write_text("bad languages", encoding="utf-8")
            os.utime(
                languages_output,
                ns=(status.st_atime_ns, status.st_mtime_ns),
            )
            assert (
                starred_lists._output_revision(languages_output) == published_revision
            )
            raise OSError("simulated second-output failure")
        raise AssertionError("rollback must not replace a concurrent writer's output")

    monkeypatch.setattr(starred_lists.os, "replace", _mutate_before_rollback)

    with pytest.raises(
        StarredListsError,
        match="rollback was incomplete due to concurrent output mutation",
    ):
        starred_lists._transactional_write_pair(
            languages_output,
            "new languages",
            topics_output,
            "new topics",
        )

    assert replace_calls == 2
    assert languages_output.read_text(encoding="utf-8") == "bad languages"
    assert topics_output.read_text(encoding="utf-8") == "old topics"
    assert not list(tmp_path.glob(".*.publish.tmp"))


def test_pagination_rejects_missing_and_cyclic_cursors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = iter(
        [
            _response(
                [_node("R1", "owner/one")],
                total=2,
                has_next=True,
                cursor="cycle",
            ),
            _response(
                [_node("R2", "owner/two")],
                total=2,
                has_next=True,
                cursor="cycle",
            ),
        ]
    )
    monkeypatch.setattr(
        starred_lists,
        "_graphql",
        lambda *_args, **_kwargs: next(responses),
    )
    with pytest.raises(StarredListsError, match="cursor"):
        starred_lists.fetch_starred_repositories("owner", "token")

    monkeypatch.setattr(
        starred_lists,
        "_graphql",
        lambda *_args, **_kwargs: _response(
            [_node("R1", "owner/one")],
            total=2,
            has_next=True,
            cursor=None,
        ),
    )
    with pytest.raises(StarredListsError, match="cursor"):
        starred_lists.fetch_starred_repositories("owner", "token")


def test_pagination_metadata_and_page_limit_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        starred_lists,
        "_graphql",
        lambda *_args, **_kwargs: _response([], total=True),
    )
    with pytest.raises(StarredListsError, match="totalCount"):
        starred_lists.fetch_starred_repositories("owner", "token")

    changing_total = iter(
        (
            _response(
                [_node("R1", "owner/one")],
                total=2,
                has_next=True,
                cursor="next",
            ),
            _response([_node("R2", "owner/two")], total=3),
        )
    )
    monkeypatch.setattr(
        starred_lists,
        "_graphql",
        lambda *_args, **_kwargs: next(changing_total),
    )
    with pytest.raises(StarredListsError, match="changed during pagination"):
        starred_lists.fetch_starred_repositories("owner", "token")

    invalid_page_info = _response([], total=0)
    invalid_page_info["data"]["user"]["starredRepositories"]["pageInfo"][
        "hasNextPage"
    ] = "yes"
    monkeypatch.setattr(
        starred_lists,
        "_graphql",
        lambda *_args, **_kwargs: invalid_page_info,
    )
    with pytest.raises(StarredListsError, match="hasNextPage"):
        starred_lists.fetch_starred_repositories("owner", "token")

    monkeypatch.setattr(
        starred_lists,
        "_graphql",
        lambda *_args, **_kwargs: _response([], total=1, has_next=True, cursor="next"),
    )
    with pytest.raises(StarredListsError, match="without nodes"):
        starred_lists.fetch_starred_repositories("owner", "token")

    monkeypatch.setattr(starred_lists, "_MAX_GRAPHQL_PAGES", 1)
    monkeypatch.setattr(
        starred_lists,
        "_graphql",
        lambda *_args, **_kwargs: _response(
            [_node("R1", "owner/one")],
            total=2,
            has_next=True,
            cursor="next",
        ),
    )
    with pytest.raises(StarredListsError, match="page limit"):
        starred_lists.fetch_starred_repositories("owner", "token")


def test_duplicate_page_entry_and_invalid_threshold_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = iter(
        [
            _response(
                [_node("R1", "owner/one")],
                total=2,
                has_next=True,
                cursor="next",
            ),
            _response([_node("R1", "owner/one")], total=2),
        ]
    )
    monkeypatch.setattr(
        starred_lists,
        "_graphql",
        lambda *_args, **_kwargs: next(responses),
    )
    with pytest.raises(StarredListsError, match="duplicate"):
        starred_lists.fetch_starred_repositories("owner", "token")

    with pytest.raises(StarredListsError, match="threshold"):
        starred_lists.render_starred_lists("owner", (), topic_threshold=-1)


def test_outputs_must_be_distinct_regular_files(tmp_path: Path) -> None:
    output = tmp_path / "same.md"
    with pytest.raises(StarredListsError, match="different files"):
        starred_lists._transactional_write_pair(output, "one", output, "two")

    languages = tmp_path / "languages.md"
    languages.symlink_to(output)
    with pytest.raises(StarredListsError, match="regular file"):
        starred_lists._transactional_write_pair(
            languages,
            "one",
            tmp_path / "topics.md",
            "two",
        )


def test_cli_uses_environment_token_and_returns_nonzero_on_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    arguments = [
        "--owner",
        "owner",
        "--languages-output",
        str(tmp_path / "languages.md"),
        "--topics-output",
        str(tmp_path / "topics.md"),
        "--topic-threshold",
        "700",
    ]
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    assert starred_lists.main(arguments) == 2

    captured: dict[str, object] = {}
    monkeypatch.setenv("GITHUB_TOKEN", "environment-secret")
    monkeypatch.setattr(
        starred_lists,
        "generate_starred_lists",
        lambda **kwargs: captured.update(kwargs),
    )
    assert starred_lists.main(arguments) == 0
    assert captured["token"] == "environment-secret"
    assert captured["topic_threshold"] == 700

    monkeypatch.setattr(
        starred_lists,
        "generate_starred_lists",
        lambda **_kwargs: (_ for _ in ()).throw(StarredListsError("failed")),
    )
    assert starred_lists.main(arguments) == 1


def test_module_uses_only_shared_verified_graphql_transport() -> None:
    source = inspect.getsource(starred_lists)
    assert "from ._github_http import _graphql" in source
    for insecure_dependency in (
        "import requests",
        "import gql",
        "import aiohttp",
        "import github3",
    ):
        assert insecure_dependency not in source
