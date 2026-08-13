"""Tests for scripts.generative — event-driven community/activity art."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from scripts import generative

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _community_metrics(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "stars": 12,
        "forks": 3,
        "watchers": 5,
        "open_issues_count": 2,
        "network_count": 1,
        "latest_stargazer": "alice",
        "latest_fork_owner": "bob",
    }
    base.update(overrides)
    return base


def _activity_metrics(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "public_repos": 20,
        "followers": 40,
        "orgs_count": 2,
        "contributions_last_year": 500,
        "total_commits": 10000,
        "following": 10,
    }
    base.update(overrides)
    return base


def _mock_drawing(mocker_target: str = "scripts.generative.Drawing"):
    """Patch Drawing with a saveable MagicMock hierarchy."""
    mock_dwg = MagicMock()
    mock_group = MagicMock()
    mock_dwg.g.return_value = mock_group
    mock_dwg.rect.return_value = MagicMock()
    mock_dwg.path.return_value = MagicMock()
    mock_dwg.circle.return_value = MagicMock()
    mock_filter = MagicMock()
    mock_dwg.filter.return_value = mock_filter
    mock_dwg.defs.add.return_value = mock_filter
    return patch(mocker_target, return_value=mock_dwg), mock_dwg


# ---------------------------------------------------------------------------
# generate_community_art
# ---------------------------------------------------------------------------


class TestGenerateCommunityArt:
    def test_writes_svg_and_calls_clifford(self, tmp_path: Path) -> None:
        out = tmp_path / "community.svg"
        drawing_patch, mock_dwg = _mock_drawing()
        with (
            drawing_patch,
            patch("scripts.generative.draw_clifford") as mock_clifford,
        ):
            result = generative.generate_community_art(
                _community_metrics(),
                dark_mode=False,
                output_path=out,
            )

        assert result == out
        mock_dwg.save.assert_called_once()
        mock_clifford.assert_called_once()
        kwargs = mock_clifford.call_args.kwargs
        assert kwargs["width"] == generative._WIDTH
        assert kwargs["height"] == generative._HEIGHT
        assert kwargs["dark_mode"] is False
        assert 0.8 <= kwargs["a"] <= 2.0
        assert kwargs["iterations"] >= 1_000_000

    def test_dark_mode_default_path_suffix(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        drawing_patch, mock_dwg = _mock_drawing()
        with (
            drawing_patch,
            patch("scripts.generative.draw_clifford"),
        ):
            result = generative.generate_community_art(
                _community_metrics(),
                dark_mode=True,
                output_path=None,
            )
        assert result.name == "generative-community-dark.svg"
        assert result.parent == Path(".github/assets/img")
        mock_dwg.save.assert_called_once()

    def test_deterministic_for_same_metrics(self, tmp_path: Path) -> None:
        captured: list[dict] = []

        def capture_clifford(**kwargs: object) -> None:
            captured.append(
                {
                    "a": kwargs["a"],
                    "b": kwargs["b"],
                    "c": kwargs["c"],
                    "d": kwargs["d"],
                    "hue_shift": kwargs["hue_shift"],
                }
            )

        drawing_patch, _ = _mock_drawing()
        metrics = _community_metrics(stars=99, forks=7)
        with (
            drawing_patch,
            patch("scripts.generative.draw_clifford", side_effect=capture_clifford),
        ):
            generative.generate_community_art(metrics, output_path=tmp_path / "a.svg")
            generative.generate_community_art(metrics, output_path=tmp_path / "b.svg")
        assert captured[0] == captured[1]

    def test_caps_iterations_by_grid(self, tmp_path: Path) -> None:
        drawing_patch, _ = _mock_drawing()
        with (
            drawing_patch,
            patch("scripts.generative.draw_clifford") as mock_clifford,
        ):
            generative.generate_community_art(
                _community_metrics(network_count=10_000),
                output_path=tmp_path / "c.svg",
            )
        iters = mock_clifford.call_args.kwargs["iterations"]
        grid_sz = 150
        assert iters <= grid_sz * grid_sz * 60


# ---------------------------------------------------------------------------
# generate_activity_art
# ---------------------------------------------------------------------------


class TestGenerateActivityArt:
    def test_writes_svg_with_flow_and_phyllotaxis(self, tmp_path: Path) -> None:
        out = tmp_path / "activity.svg"
        drawing_patch, mock_dwg = _mock_drawing()
        fake_lines = [
            [(0.0, 0.0), (10.0, 10.0)],
            [(1.0, 2.0)],  # skipped (< 2 points)
        ]
        fake_points = [(100.0, 100.0), (120.0, 130.0), (140.0, 110.0)]
        with (
            drawing_patch,
            patch(
                "scripts.generative.flow_field_lines", return_value=fake_lines
            ) as mock_flow,
            patch(
                "scripts.generative.phyllotaxis_points", return_value=fake_points
            ) as mock_phy,
        ):
            result = generative.generate_activity_art(
                _activity_metrics(public_repos=3),
                dark_mode=False,
                output_path=out,
            )

        assert result == out
        mock_dwg.save.assert_called_once()
        mock_flow.assert_called_once()
        mock_phy.assert_called_once()
        # One path for the valid trail; circles for each phyllotaxis point
        assert mock_dwg.path.call_count == 1
        assert mock_dwg.circle.call_count == len(fake_points)

    def test_dark_mode_default_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        drawing_patch, _ = _mock_drawing()
        with (
            drawing_patch,
            patch("scripts.generative.flow_field_lines", return_value=[]),
            patch("scripts.generative.phyllotaxis_points", return_value=[(1.0, 1.0)]),
        ):
            result = generative.generate_activity_art(
                _activity_metrics(),
                dark_mode=True,
                output_path=None,
            )
        assert result.name == "generative-activity-dark.svg"

    def test_glow_filter_when_many_points(self, tmp_path: Path) -> None:
        drawing_patch, mock_dwg = _mock_drawing()
        n = 60
        points = [(float(i), float(i)) for i in range(n)]
        with (
            drawing_patch,
            patch("scripts.generative.flow_field_lines", return_value=[]),
            patch("scripts.generative.phyllotaxis_points", return_value=points),
        ):
            generative.generate_activity_art(
                _activity_metrics(public_repos=n),
                output_path=tmp_path / "glow.svg",
            )
        mock_dwg.filter.assert_called()
        mock_dwg.defs.add.assert_called()

    def test_deterministic_seed_inputs(self, tmp_path: Path) -> None:
        flow_calls: list[dict] = []

        def capture_flow(*_a: object, **kwargs: object) -> list:
            flow_calls.append(dict(kwargs))
            return []

        drawing_patch, _ = _mock_drawing()
        metrics = _activity_metrics(followers=80, orgs_count=4)
        with (
            drawing_patch,
            patch("scripts.generative.flow_field_lines", side_effect=capture_flow),
            patch(
                "scripts.generative.phyllotaxis_points",
                return_value=[(10.0, 10.0)],
            ),
        ):
            generative.generate_activity_art(metrics, output_path=tmp_path / "d1.svg")
            generative.generate_activity_art(metrics, output_path=tmp_path / "d2.svg")
        assert flow_calls[0]["seed"] == flow_calls[1]["seed"]
        assert flow_calls[0]["octaves"] == flow_calls[1]["octaves"]


# ---------------------------------------------------------------------------
# CLI main
# ---------------------------------------------------------------------------


class TestGenerativeMain:
    def test_all_types(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        metrics_path = tmp_path / "metrics.json"
        metrics_path.write_text(
            json.dumps(_community_metrics(**_activity_metrics())), encoding="utf-8"
        )
        calls: list[str] = []

        monkeypatch.setattr(
            generative,
            "generate_community_art",
            lambda *a, **k: calls.append("community") or tmp_path / "c.svg",
        )
        monkeypatch.setattr(
            generative,
            "generate_activity_art",
            lambda *a, **k: calls.append("activity") or tmp_path / "a.svg",
        )
        monkeypatch.setattr(
            "sys.argv",
            [
                "generative",
                "--metrics",
                str(metrics_path),
                "--type",
                "all",
            ],
        )
        generative.main()
        assert calls == ["community", "activity"]

    def test_community_only_with_output(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        metrics_path = tmp_path / "metrics.json"
        metrics_path.write_text(json.dumps(_community_metrics()), encoding="utf-8")
        out = tmp_path / "custom.svg"
        captured: dict[str, object] = {}

        def fake_community(metrics: dict, dark_mode: bool = False, output_path=None):
            captured["metrics"] = metrics
            captured["dark_mode"] = dark_mode
            captured["output_path"] = output_path
            return Path(output_path or out)

        monkeypatch.setattr(generative, "generate_community_art", fake_community)
        monkeypatch.setattr(
            generative,
            "generate_activity_art",
            lambda *a, **k: (_ for _ in ()).throw(AssertionError("should not run")),
        )
        monkeypatch.setattr(
            "sys.argv",
            [
                "generative",
                "--metrics",
                str(metrics_path),
                "--type",
                "community",
                "--dark-mode",
                "--output",
                str(out),
            ],
        )
        generative.main()
        assert captured["dark_mode"] is True
        assert captured["output_path"] == out
        metrics = cast(dict[str, object], captured["metrics"])
        assert metrics["stars"] == 12
