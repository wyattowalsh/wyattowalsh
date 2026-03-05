"""RED contracts for featured README cards only."""

from __future__ import annotations

import re
from pathlib import Path

FEATURED_CARD_GLOB = "featured-projects-card-*.svg"


def _featured_card_assets() -> list[Path]:
    asset_dir = Path(__file__).resolve().parents[1] / ".github" / "assets" / "img" / "readme"
    assets = sorted(asset_dir.glob(FEATURED_CARD_GLOB))
    assert assets, "Expected generated featured card SVG assets for deterministic checks."
    return assets


def _featured_svgs() -> list[str]:
    return [asset.read_text(encoding="utf-8") for asset in _featured_card_assets()]


def test_featured_cards_preserve_transparent_card_semantics() -> None:
    for svg in _featured_svgs():
        base_fill = re.search(
            r'<rect width="\d+" height="\d+" rx="16"[^>]*fill-opacity="([0-9.]+)"',
            svg,
        )
        assert base_fill is not None
        assert float(base_fill.group(1)) <= 0.35


def test_featured_cards_expect_richer_metadata_lanes_and_chips() -> None:
    for svg in _featured_svgs():
        assert svg.count('class="card-meta-row"') >= 2
        assert 'class="card-chip"' in svg


def test_featured_cards_meet_social_hero_image_quality_contract() -> None:
    for svg in _featured_svgs():
        hero_image = re.search(
            r'(<image[^>]*preserveAspectRatio="xMidYMid slice"[^>]*opacity="([0-9.]+)"[^>]*/>)',
            svg,
        )
        assert hero_image is not None
        assert 'class="card-hero-image"' in hero_image.group(1)
        assert float(hero_image.group(2)) >= 0.35
        assert re.search(
            r'<image class="card-icon-image"[^>]*preserveAspectRatio="xMidYMid meet"',
            svg,
        )


def test_featured_cards_drop_old_dull_footer_and_label_patterns() -> None:
    for svg in _featured_svgs():
        assert 'class="card-badge"' not in svg
        assert ">Showcase<" not in svg
