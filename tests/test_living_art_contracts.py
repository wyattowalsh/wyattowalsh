from __future__ import annotations

import pytest
from pydantic import ValidationError

pytest.importorskip("numpy", reason="living-art shared contracts require numpy")

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


def test_all_style_registries_have_same_keys() -> None:
    """Canonical style list, timelapse registry, and animate imports stay in sync."""
    from scripts.art import animate  # noqa: E402
    from scripts.art.timelapse import ALL_STYLES  # noqa: E402

    expected = set(LIVING_ART_STYLE_KEYS)
    assert set(ALL_STYLES) == expected, (
        f"timelapse ALL_STYLES drift: {set(ALL_STYLES)} != {expected}"
    )
    module_map = {
        "inkgarden": "ink_garden",
        "topo": "topography",
        "genetic": "genetic_landscape",
        "physarum": "physarum",
        "lenia": "lenia",
        "ferrofluid": "ferrofluid",
    }
    for style_key in LIVING_ART_STYLE_KEYS:
        assert hasattr(animate, module_map[style_key]), (
            f"animate.py missing import for style '{style_key}'"
        )
