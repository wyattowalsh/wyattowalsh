"""Package-structure contracts for scripts.art.shared after the F1 split."""

from __future__ import annotations

import importlib

import pytest

pytest.importorskip("numpy", reason="scripts.art.shared requires numpy")

from scripts.art import shared as shared_pkg  # noqa: E402
from scripts.art.shared import (  # noqa: E402
    ART_PALETTE_ANCHORS,
    MAX_REPOS,
    ElementBudget,
    Noise2D,
    WorldState,
    compute_world_state,
    oklch,
    seed_hash,
)

_EXPECTED_SUBMODULES = (
    "constants",
    "timeline",
    "world_state",
    "metrics",
    "seeds",
    "color",
    "noise",
    "math_helpers",
    "svg",
    "palette",
    "visual",
    "accretion",
)


@pytest.mark.parametrize("name", _EXPECTED_SUBMODULES)
def test_shared_submodules_importable(name: str) -> None:
    module = importlib.import_module(f"scripts.art.shared.{name}")
    assert module.__name__.endswith(name)


def test_shared_is_package_not_module() -> None:
    assert hasattr(shared_pkg, "__path__")


def test_compat_reexports_match_submodules() -> None:
    from scripts.art.shared import color, constants, noise, world_state

    assert oklch is color.oklch
    assert MAX_REPOS is constants.MAX_REPOS
    assert Noise2D is noise.Noise2D
    assert WorldState is world_state.WorldState
    assert compute_world_state is world_state.compute_world_state


def test_basic_shared_behaviors_still_work() -> None:
    digest = seed_hash({"stars": 1, "label": "x"})
    assert len(digest) == 64
    assert oklch(0.5, 0.1, 120).startswith("#")
    ws = compute_world_state({})
    assert isinstance(ws, WorldState)
    assert "sunset" in ART_PALETTE_ANCHORS
    assert MAX_REPOS == 10


def test_accretion_channels_and_style_dialects_stay_distinct() -> None:
    from scripts.art.shared import (
        STYLE_DIALECTS,
        build_style_dialect,
        extract_accretion_channels,
    )
    from scripts.art.timelapse import ALL_STYLES

    metrics = {
        "repos": [{"name": "alpha"}, {"name": "beta"}],
        "stars": 24,
        "total_commits": 400,
        "followers": 18,
    }
    channels = extract_accretion_channels(metrics)

    assert channels.repos == 2
    assert channels.stars == 24
    assert channels.commits == 400
    assert channels.followers == 18
    assert 0.0 < channels.star_scale < 1.0
    assert set(STYLE_DIALECTS) == set(ALL_STYLES)
    assert ALL_STYLES == [
        "inkgarden",
        "topo",
        "genetic",
        "physarum",
        "lenia",
        "ferrofluid",
    ]
    families = {build_style_dialect(style, metrics).family for style in ALL_STYLES}
    assert families == set(STYLE_DIALECTS.values())
    assert len(families) == 6


def test_element_budget_reports_truthful_state_at_and_beyond_limit() -> None:
    budget = ElementBudget(2)
    assert budget.count == 0
    assert budget.remaining == 2
    assert budget.ok() is True

    budget.add()
    assert budget.count == 1
    assert budget.remaining == 1
    assert budget.ok() is True

    budget.add()
    assert budget.count == 2
    assert budget.remaining == 0
    assert budget.ok() is False

    budget.add(3)
    assert budget.count == 5
    assert budget.remaining == 0
    assert budget.ok() is False
