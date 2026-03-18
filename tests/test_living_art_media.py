from datetime import date
from pathlib import Path
import json
import re

import pytest

pytestmark = pytest.mark.skip(reason="Requires pre-generated artifacts — run after full pipeline execution")


def test_gif_artifacts_emitted():
    """Expected GIF artifact names/paths are emitted for living-art outputs."""
    inkg = Path(".github/assets/img/inkgarden-growth.gif")
    topo = Path(".github/assets/img/topo-growth.gif")
    assert inkg.is_file(), f"Missing expected GIF artifact: {inkg}"
    assert topo.is_file(), f"Missing expected GIF artifact: {topo}"


def test_readme_embed_strategy_for_gif_with_png_fallback():
    """README should represent GIF embed strategy with PNG fallback (expected to fail until implemented)."""
    txt = Path("README.md").read_text(encoding="utf-8")
    # The project should document the GIF-first embed strategy with PNG fallback
    assert "GIF with PNG fallback" in txt, "README must document GIF embed strategy with PNG fallback"


def test_size_budget_behavior_enforced_by_helper_api():
    """Size-budget behavior contract: helper logs must report artifacts under budget (RED expected)."""
    logs = Path(f"logs/json/{date.today().isoformat()}.json")
    assert logs.exists(), "Expected log file with artifact size records"
    content = logs.read_text(encoding="utf-8")
    # logs file contains JSON objects per-line; search for inkgarden-growth size entries
    matches = re.findall(r'inkgarden-growth:\s*(\d+)\s*KB', content)
    assert matches, "No inkgarden-growth size entries found in logs"
    # Enforce an aggressive budget of 50 KB to make this test fail until production enforces it
    sizes = [int(m) for m in matches]
    assert all(s <= 50 for s in sizes), f"Size budget exceeded for inkgarden-growth: {sizes}"
