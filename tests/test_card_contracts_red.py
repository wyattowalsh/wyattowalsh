"""RED tests for stronger README card family contracts."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from scripts.config import ReadmeFeaturedRepo, ReadmeSectionsSettings, ReadmeSvgSettings
from scripts.readme_sections import ReadmeSectionGenerator, RepoMetadata
from scripts.readme_svg import SvgBlock, SvgBlockRenderer, SvgCard


class _RepoClient:
    def __init__(self, metadata_by_repo: dict[str, RepoMetadata]) -> None:
        self._metadata_by_repo = metadata_by_repo

    def fetch_repo_metadata(self, full_name: str) -> Optional[RepoMetadata]:
        return self._metadata_by_repo.get(full_name)


def test_blog_family_contract_is_not_title_keyword_driven() -> None:
    renderer = SvgBlockRenderer(width=920, card_height=220, padding=20)
    card = SvgCard(
        title="Deep Notes on Agentic Tooling",
        lines=("Readable blog body copy that should stay wrapped for scanability.",),
        url="https://w4w.dev/blog/deep-notes",
        badge="Read post",
    )

    canonical_svg = renderer.render(
        SvgBlock(title="Latest Blog Posts", cards=(card,), columns=1)
    )
    non_keyword_svg = renderer.render(
        SvgBlock(title="Engineering Dispatch", cards=(card,), columns=1)
    )

    assert 'class="card-badge"' not in canonical_svg
    assert 'class="card-badge"' not in non_keyword_svg
    assert re.search(r'<text class="card-title"[^>]*>\s*<tspan', non_keyword_svg)


def test_featured_cards_expose_structured_metadata_chip_row_contract(
    tmp_path: Path,
    monkeypatch,
) -> None:
    settings = ReadmeSectionsSettings(
        svg=ReadmeSvgSettings(enabled=True, output_dir=str(tmp_path / "svg")),
        featured_repos=[ReadmeFeaturedRepo(full_name="wyattowalsh/riso")],
    )
    generator = ReadmeSectionGenerator(
        settings=settings,
        repo_client=_RepoClient(
            {
                "wyattowalsh/riso": RepoMetadata(
                    full_name="wyattowalsh/riso",
                    name="riso",
                    html_url="https://github.com/wyattowalsh/riso",
                    description="Composable scaffolding framework",
                    stars=42,
                    homepage="https://riso.dev",
                    topics=["python", "templates"],
                    created_at="2023-01-01T00:00:00Z",
                    updated_at="2026-02-01T00:00:00Z",
                    forks=7,
                    size_kb=128,
                )
            }
        ),
    )
    captured: dict[str, object] = {}

    def capture_write_svg_asset(
        *,
        asset_name: str,
        block,
        svg_markup=None,
        renderer=None,
    ) -> None:
        captured[asset_name] = block

    monkeypatch.setattr(generator, "_write_svg_asset", capture_write_svg_asset)

    generator._render_featured_projects()

    featured_asset_name = next(
        key for key in captured if key.startswith("featured-projects-card-")
    )
    block = captured[featured_asset_name]
    card = block.cards[0]
    chips = getattr(card, "metadata_chips", None)

    assert chips is not None
    chip_labels = {
        (chip.get("label") if isinstance(chip, dict) else chip[0]) for chip in chips
    }
    normalized = {str(label).lower() for label in chip_labels}
    assert {"stars", "forks", "language", "size", "lifespan"}.issubset(normalized)
    rows = getattr(card, "metadata_rows", ())
    assert rows


def test_blog_body_copy_uses_wrapped_tspans_not_single_unbounded_line() -> None:
    renderer = SvgBlockRenderer(width=920, card_height=220, padding=20)
    long_body = (
        "This intentionally long blog summary should wrap into multiple readable "
        "segments rather than rendering as one overlong line."
    )
    card = SvgCard(
        title="Readable text policy",
        lines=(long_body,),
        url="https://w4w.dev/blog/readable-policy",
    )

    svg = renderer.render(SvgBlock(title="Latest Blog Posts", cards=(card,), columns=1))

    assert re.search(r'<text class="card-line"[^>]*>\s*<tspan', svg)
    assert "…" not in svg


def test_connect_cards_are_icon_first_and_filter_handle_url_noise() -> None:
    renderer = SvgBlockRenderer(width=920, card_height=180, padding=20)
    card = SvgCard(
        title="GitHub",
        lines=(
            "@wyattowalsh",
            "https://github.com/wyattowalsh",
            "Open profile",
        ),
        url="https://github.com/wyattowalsh",
        icon="GH",
        icon_data_uri="data:image/svg+xml;base64,PHN2Zy8+",
        accent="181717",
    )

    svg = renderer.render(SvgBlock(title="Connect & Contact", cards=(card,), columns=1))

    assert 'class="card-icon-image"' in svg
    assert svg.index('class="card-icon-image"') < svg.index('class="card-title"')
    visible_lines = re.findall(r'<text class="card-line"[^>]*>([^<]+)</text>', svg)
    assert visible_lines
    assert all("@" not in line and "://" not in line for line in visible_lines)
