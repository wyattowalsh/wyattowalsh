from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

pytest.importorskip("numpy", reason="living-art shared contracts require numpy")
pytest.importorskip(
    "scipy.ndimage",
    reason="living-art shared contracts require scipy for physarum",
)

from scripts.art.artifacts import LIVING_ART_STYLE_KEYS  # noqa: E402
from scripts.art.shared import (  # noqa: E402
    normalize_live_metrics,
    validate_live_history_payload,
    validate_live_metrics_payload,
)
from scripts.art.timelapse import render_timelapse  # noqa: E402


def _metrics_payload() -> dict:
    return {
        "label": "Contract Test",
        "stars": 12,
        "languages": {"Python": 900, "Go": 300},
        "top_repos": [
            {
                "name": "orchid-core",
                "language": "Python",
                "stars": 8,
                "forks": 2,
                "topics": ["ai", "agents"],
                "description": "Primary repo",
                "updated_at": "2025-02-10T12:00:00Z",
            }
        ],
        "contributions_calendar": [
            {"date": "2025-01-01", "count": 2},
            {"date": "2025-01-02", "count": 4},
        ],
    }


def _history_payload() -> dict:
    return {
        "account_created": "2020-01-01T00:00:00Z",
        "repos": [
            {
                "name": "orchid-core",
                "language": "Python",
                "stars": 8,
                "topics": ["ai", "agents"],
            }
        ],
        "stars": [{"date": "2024-01-10T00:00:00Z"}],
        "forks": [{"date": "2024-03-12T00:00:00Z"}],
        "contributions_monthly": {"2025-01": 12, "2025-02": 18},
        "contributions_daily": {"2025-01-01": 2, "2025-01-02": 3},
    }


def _generator_metrics_payload() -> dict:
    return {
        "label": "Generator Contract Test",
        "stars": 18,
        "forks": 3,
        "followers": 12,
        "watchers": 4,
        "total_commits": 360,
        "contributions_last_year": 120,
        "languages": {"Python": 900, "Go": 300},
        "repos": [
            {
                "name": "orchid-core",
                "language": "Python",
                "stars": 8,
                "forks": 2,
                "topics": ["ai", "agents"],
                "description": "Primary repo",
                "date": "2025-02-10T12:00:00Z",
                "updated_at": "2025-02-10T12:00:00Z",
                "age_months": 12,
            }
        ],
        "contributions_monthly": {"2025-01": 12, "2025-02": 18},
    }


def test_validate_live_metrics_payload_accepts_fetch_metrics_shape() -> None:
    validated = validate_live_metrics_payload(_metrics_payload())

    assert validated["stars"] == 12
    assert validated["languages"] == {"Python": 900, "Go": 300}
    assert validated["top_repos"][0]["name"] == "orchid-core"
    assert "repos" not in validated


def test_validate_live_history_payload_accepts_enriched_repo_entries() -> None:
    validated = validate_live_history_payload(_history_payload())

    assert validated["account_created"] == "2020-01-01T00:00:00Z"
    assert validated["repos"][0]["name"] == "orchid-core"
    assert validated["repos"][0]["topics"] == ["ai", "agents"]


def test_validate_live_history_payload_accepts_contributions_daily() -> None:
    validated = validate_live_history_payload(_history_payload())

    assert validated["contributions_daily"]["2025-01-01"] == 2


def test_normalize_live_metrics_preserves_fetch_metrics_passthrough_fields() -> None:
    metrics = normalize_live_metrics(
        {
            **_generator_metrics_payload(),
            "public_gists": 5,
            "traffic_views_14d": 100,
            "traffic_unique_visitors_14d": 40,
            "traffic_clones_14d": 20,
            "traffic_unique_cloners_14d": 8,
            "traffic_top_referrers": ["google", "github"],
            "commit_hour_distribution_scope": "recent_push_events_window",
            "commit_hour_distribution_sample_size": 12,
            "releases_scope": "account_owned_repos",
            "releases_repo_count": 4,
        },
        owner="contract-test",
        history=_history_payload(),
    )

    assert metrics["public_gists"] == 5
    assert metrics["traffic_views_14d"] == 100
    assert metrics["traffic_unique_visitors_14d"] == 40
    assert metrics["traffic_clones_14d"] == 20
    assert metrics["traffic_unique_cloners_14d"] == 8
    assert metrics["traffic_top_referrers"] == ["google", "github"]
    assert metrics["commit_hour_distribution_scope"] == "recent_push_events_window"
    assert metrics["commit_hour_distribution_sample_size"] == 12
    assert metrics["releases_scope"] == "account_owned_repos"
    assert metrics["releases_repo_count"] == 4


def test_normalize_live_metrics_keeps_monthly_only_payloads_working() -> None:
    payload = _generator_metrics_payload()
    payload.pop("contributions_daily", None)

    metrics = normalize_live_metrics(payload, owner="contract-test", history=None)

    assert metrics["contributions_monthly"] == {"2025-01": 12, "2025-02": 18}


def test_normalize_live_metrics_rejects_invalid_top_repo_shape() -> None:
    payload = _metrics_payload()
    payload["top_repos"] = ["broken"]

    with pytest.raises(ValidationError):
        normalize_live_metrics(
            payload,
            owner="contract-test",
            history=_history_payload(),
        )


def test_validate_live_history_payload_rejects_invalid_monthly_shape() -> None:
    payload = _history_payload()
    payload["contributions_monthly"] = ["2025-01"]

    with pytest.raises(ValidationError):
        validate_live_history_payload(payload)


def test_render_timelapse_rejects_invalid_metrics_payload() -> None:
    with pytest.raises(ValidationError):
        render_timelapse(
            history=_history_payload(),
            current_metrics={"languages": ["Python"]},
            styles=list(LIVING_ART_STYLE_KEYS),
            max_frames=2,
            size=64,
        )


def test_render_timelapse_uses_validated_contributions_daily(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, dict[str, int]] = {}

    def _fake_build_daily_snapshots(
        history: dict[str, Any],
        current_metrics: dict[str, Any],
        *,
        owner: str = "",
        include_today: bool = False,
        **_: Any,
    ) -> list[object]:
        del current_metrics, owner, include_today
        captured["contributions_daily"] = history["contributions_daily"]
        return []

    monkeypatch.setattr(
        "scripts.art.timelapse.build_daily_snapshots",
        _fake_build_daily_snapshots,
    )

    history = _history_payload()
    history["contributions_daily"] = {"2025-01-01": "7"}

    assert (
        render_timelapse(
            history=history,
            current_metrics=_generator_metrics_payload(),
            styles=["topo"],
            max_frames=2,
            size=64,
        )
        == []
    )
    assert captured["contributions_daily"] == {"2025-01-01": 7}


def test_all_style_registries_have_same_keys() -> None:
    """Canonical style list, timelapse registry, and animate imports stay in sync."""
    from scripts.art import animate
    from scripts.art.artifacts import LIVING_ART_STYLE_KEYS
    from scripts.art.timelapse import ALL_STYLES

    expected = set(LIVING_ART_STYLE_KEYS)
    assert set(ALL_STYLES) == expected
    module_map = {
        "inkgarden": "ink_garden",
        "topo": "topography",
        "genetic": "genetic_landscape",
        "physarum": "physarum",
        "lenia": "lenia",
        "ferrofluid": "ferrofluid",
    }
    for style_key in LIVING_ART_STYLE_KEYS:
        assert hasattr(animate, module_map[style_key])


@pytest.mark.parametrize(
    ("style_key", "generator"),
    [
        ("inkgarden", "ink_garden"),
        ("topo", "topography"),
        ("genetic", "genetic_landscape"),
        ("physarum", "physarum"),
        ("lenia", "lenia"),
        ("ferrofluid", "ferrofluid"),
    ],
)
def test_all_generators_accept_plain_seed_strings(
    style_key: str,
    generator: str,
) -> None:
    """Every living-art generator should accept a normal seed string."""
    from scripts.art import (
        ferrofluid,
        genetic_landscape,
        ink_garden,
        lenia,
        physarum,
        topography,
    )

    module_map = {
        "ink_garden": ink_garden,
        "topography": topography,
        "genetic_landscape": genetic_landscape,
        "physarum": physarum,
        "lenia": lenia,
        "ferrofluid": ferrofluid,
    }

    svg = module_map[generator].generate(
        _generator_metrics_payload(),
        seed=f"{style_key}-plain-seed",
        maturity=0.5,
        timeline=False,
    )

    assert svg.lstrip().startswith("<svg")
    assert svg.rstrip().endswith("</svg>")


def test_readme_living_art_section_uses_canonical_timelapse_gifs() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    for style in LIVING_ART_STYLE_KEYS:
        assert f".github/assets/img/living-{style}.gif" in readme
        assert f".github/assets/img/{style}-growth.gif" not in readme


def test_docs_homepage_uses_mirrored_canonical_timelapses() -> None:
    homepage = Path("docs/app/(home)/page.tsx").read_text(encoding="utf-8")

    for style in LIVING_ART_STYLE_KEYS:
        assert f"/showcase/living-{style}.gif" in homepage
    assert "/showcase/living-art-preview.html" in homepage
    assert "/showcase/living-art-manifest.json" in homepage
    assert "growth.gif" not in homepage
