"""RED contracts for deterministic per-card README assets and embeds."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pytest

from scripts.config import (
    ReadmeSectionsSettings,
    ReadmeSvgSettings,
)
from scripts.readme_sections import BlogPost, ReadmeSectionGenerator, RepoMetadata
from scripts.readme_svg import SvgBlockRenderer, SvgCard, SvgCardFamily


class _RepoClient:
    def __init__(self, metadata_by_repo: dict[str, RepoMetadata]) -> None:
        self._metadata_by_repo = metadata_by_repo

    def fetch_repo_metadata(self, full_name: str) -> Optional[RepoMetadata]:
        return self._metadata_by_repo.get(full_name)


class _BlogClient:
    def __init__(self, posts: list[BlogPost]) -> None:
        self._posts = posts

    def fetch_latest_posts(self, feed_url: str, limit: int) -> list[BlogPost]:
        return self._posts[:limit]


class _BlogMetadataClient:
    def __init__(self, metadata: dict[str, dict[str, Optional[str]]]) -> None:
        self._metadata = metadata

    def fetch_metadata(self, url: str) -> dict[str, Optional[str]]:
        return self._metadata.get(
            url,
            {
                "hero_image": None,
                "summary": None,
                "published": None,
                "host": None,
            },
        )


class _StarHistoryClient:
    def fetch_star_history(
        self, full_name: str, sample: int = 24
    ) -> Optional[list[int]]:  # noqa: ARG002
        return None


@pytest.mark.parametrize(
    ("section_asset_name", "original_card", "renamed_card"),
    [
        (
            "top-contact",
            SvgCard(
                title="Primary Funnel",
                url="https://linkedin.com/in/wyattowalsh",
            ),
            SvgCard(
                title="Career Profile",
                url="https://linkedin.com/in/wyattowalsh",
            ),
        ),
        (
            "featured-projects",
            SvgCard(
                title="RISO Launchpad",
                url="https://github.com/wyattowalsh/riso",
            ),
            SvgCard(
                title="RISO Framework",
                url="https://github.com/wyattowalsh/riso",
            ),
        ),
        (
            "blog-posts",
            SvgCard(
                title="🚨 Weekly Dispatch",
                url="https://w4w.dev/blog/deterministic-asset-slugs",
            ),
            SvgCard(
                title="Shipping Notes #42",
                url="https://w4w.dev/blog/deterministic-asset-slugs",
            ),
        ),
    ],
    ids=["connect", "featured", "blog"],
)
def test_per_family_asset_name_contract_is_stable_under_title_changes(
    tmp_path: Path,
    section_asset_name: str,
    original_card: SvgCard,
    renamed_card: SvgCard,
) -> None:
    generator = ReadmeSectionGenerator(
        settings=ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(enabled=True, output_dir=str(tmp_path / "svg"))
        )
    )

    original_asset = generator._per_card_svg_asset_name(
        section_asset_name=section_asset_name,
        card_index=0,
        card=original_card,
    )
    renamed_asset = generator._per_card_svg_asset_name(
        section_asset_name=section_asset_name,
        card_index=0,
        card=renamed_card,
    )

    assert renamed_asset == original_asset


def test_per_card_embeds_contract_always_emits_link_wrapped_images(
    tmp_path: Path, monkeypatch
) -> None:
    generator = ReadmeSectionGenerator(
        settings=ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(enabled=True, output_dir=str(tmp_path / "svg"))
        )
    )
    monkeypatch.setattr(generator, "_write_svg_asset", lambda **kwargs: None)

    embeds = generator._render_per_card_svg_embeds(
        section_flag="blog_posts",
        asset_name="blog-posts",
        block_title="Latest Blog Posts",
        cards=(
            SvgCard(title="With Link", url="https://w4w.dev/blog/with-link"),
            SvgCard(title="No Link", url=None),
        ),
        renderer=SvgBlockRenderer(width=1100, card_height=220, padding=28),
        alt_prefix="Latest blog post card",
        family=SvgCardFamily.BLOG,
    )

    assert embeds
    assert all(embed.startswith('<a href="') and embed.endswith("</a>") for embed in embeds)


def test_card_sort_index_contract_assigns_indexes_after_canonical_sort(
    tmp_path: Path, monkeypatch
) -> None:
    generator = ReadmeSectionGenerator(
        settings=ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(enabled=True, output_dir=str(tmp_path / "svg"))
        )
    )
    captured_asset_names: list[str] = []

    def capture_write_svg_asset(
        *,
        asset_name: str,
        block,
        svg_markup=None,
        renderer=None,
    ) -> None:
        captured_asset_names.append(asset_name)

    monkeypatch.setattr(generator, "_write_svg_asset", capture_write_svg_asset)

    generator._render_per_card_svg_embeds(
        section_flag="featured_projects",
        asset_name="featured-projects",
        block_title="Featured Projects",
        cards=(
            SvgCard(title="Zulu Toolkit", url="https://github.com/example/zulu"),
            SvgCard(title="Alpha Toolkit", url="https://github.com/example/alpha"),
            SvgCard(title="Beta Toolkit", url="https://github.com/example/beta"),
        ),
        renderer=SvgBlockRenderer(width=1100, card_height=220, padding=28),
        alt_prefix="Featured project card",
        family=SvgCardFamily.FEATURED,
    )

    assert captured_asset_names == [
        "featured-projects-card-01-alpha-toolkit",
        "featured-projects-card-02-beta-toolkit",
        "featured-projects-card-03-zulu-toolkit",
    ]


def test_readme_marker_contract_rejects_legacy_section_wide_svg_fallbacks(
    tmp_path: Path,
) -> None:
    readme_path = tmp_path / "README.md"
    readme_path.write_text(
        "before\n"
        "<!-- README:TOP_BADGES:START -->\n"
        "old top\n"
        "<!-- README:TOP_BADGES:END -->\n"
        "<!-- README:FEATURED_PROJECTS:START -->\n"
        "old featured\n"
        "<!-- README:FEATURED_PROJECTS:END -->\n"
        "<!-- README:BLOG_POSTS:START -->\n"
        "old blog\n"
        "<!-- README:BLOG_POSTS:END -->\n"
        "after\n",
        encoding="utf-8",
    )
    generator = ReadmeSectionGenerator(
        settings=ReadmeSectionsSettings(
            readme_path=str(readme_path),
            social_links=[],
            featured_repos=[],
            blog_feed_url="https://w4w.dev/feed.xml",
            blog_post_limit=2,
            svg=ReadmeSvgSettings(enabled=True, output_dir=str(tmp_path / "svg")),
        ),
        repo_client=_RepoClient({}),
        blog_client=_BlogClient([]),
        blog_metadata_client=_BlogMetadataClient({}),
        star_history_client=_StarHistoryClient(),
    )

    generator.generate()
    content = readme_path.read_text(encoding="utf-8")

    assert "top-contact.svg" not in content
    assert "featured-projects.svg" not in content
    assert "blog-posts.svg" not in content
    assert "top-contact-card-" in content
    assert "featured-projects-card-" in content
    assert "blog-posts-card-" in content
