"""Package-structure contracts for scripts.art.shared after the F1 split."""

from __future__ import annotations

import importlib

import pytest

pytest.importorskip("numpy", reason="scripts.art.shared requires numpy")

from scripts.art import shared as shared_pkg  # noqa: E402
from scripts.art.shared import (  # noqa: E402
    ART_PALETTE_ANCHORS,
    MAX_REPOS,
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
