"""Tests for README dynamic section generation."""

import re
from typing import Optional
from pathlib import Path

from scripts.config import (
    ReadmeFeaturedRepo,
    ReadmeSectionsSettings,
    ReadmeSocialLink,
    ReadmeSvgSettings,
)
from scripts.readme_sections import (
    BlogFeedClient,
    BlogMetadataClient,
    BlogPost,
    ReadmeSectionGenerator,
    RepoMetadata,
)
from scripts.readme_svg import SvgCardFamily


class StubRepoClient:
    def __init__(self, metadata_by_repo: dict[str, RepoMetadata]) -> None:
        self.metadata_by_repo = metadata_by_repo

    def fetch_repo_metadata(self, full_name: str) -> Optional[RepoMetadata]:
        return self.metadata_by_repo.get(full_name)


class StubBlogClient:
    def __init__(self, posts: list[BlogPost]) -> None:
        self.posts = posts

    def fetch_latest_posts(self, feed_url: str, limit: int) -> list[BlogPost]:
        return self.posts[:limit]


class StubStarHistoryClient:
    def __init__(self, series: dict[str, list[int]]) -> None:
        self.series = series

    def fetch_star_history(
        self, full_name: str, sample: int = 24
    ) -> Optional[list[int]]:
        return self.series.get(full_name)


class StubBlogMetadataClient:
    def __init__(self, metadata: dict[str, dict[str, str]]) -> None:
        self.metadata = metadata

    def fetch_metadata(self, url: str) -> dict[str, Optional[str]]:
        data = self.metadata.get(url, {})
        return {
            "hero_image": data.get("hero_image"),
            "summary": data.get("summary"),
            "published": data.get("published"),
            "host": data.get("host"),
        }


def assert_sanitizer_safe_section_embed(markup: str, expected_src: str) -> None:
    assert "<img" in markup
    assert f'src="{expected_src}"' in markup
    assert "<svg" not in markup
    assert "&lt;svg" not in markup
    assert "&lt;style&gt;" not in markup


class TestRendering:
    def test_top_badges_render_svg_contact_block(self, tmp_path: Path) -> None:
        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(
                enabled=True,
                output_dir=str(tmp_path / "svg"),
            ),
            social_links=[
                ReadmeSocialLink(
                    label="Website",
                    url="https://w4w.dev",
                    color="000000",
                    logo="safari",
                ),
                ReadmeSocialLink(
                    label="LinkedIn",
                    url="https://linkedin.com/in/wyattowalsh",
                    color="0A66C2",
                    logo="linkedin",
                ),
                ReadmeSocialLink(
                    label="GitHub",
                    url="https://github.com/wyattowalsh",
                    color="181717",
                    logo="github",
                ),
            ],
        )
        generator = ReadmeSectionGenerator(settings=settings)

        html = generator._render_top_badges()

        card_svgs = sorted((tmp_path / "svg").glob("top-contact-card-*.svg"))
        assert len(card_svgs) == len(settings.social_links)
        for svg_path in card_svgs:
            assert_sanitizer_safe_section_embed(html, svg_path.as_posix())
        assert "top-contact.svg" not in html
        assert "❈" not in html
        assert "https://w4w.dev" in html
        assert "https://linkedin.com/in/wyattowalsh" in html
        assert ".github/assets/img/gh.gif" not in html
        svg_payloads = [path.read_text(encoding="utf-8") for path in card_svgs]
        assert sum(svg.count('class="card-icon-image"') for svg in svg_payloads) == 3
        assert all('class="card-badge"' not in svg for svg in svg_payloads)
        assert all('class="card-kicker"' in svg for svg in svg_payloads)

    def test_top_contact_svg_meta_avoids_full_profile_urls(
        self, tmp_path: Path
    ) -> None:
        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(
                enabled=True,
                output_dir=str(tmp_path / "svg"),
            ),
            social_links=[
                ReadmeSocialLink(
                    label="LinkedIn",
                    url="https://linkedin.com/in/wyattowalsh",
                    color="0A66C2",
                    logo="linkedin",
                ),
                ReadmeSocialLink(
                    label="GitHub",
                    url="https://github.com/wyattowalsh",
                    color="181717",
                    logo="github",
                ),
            ],
        )
        generator = ReadmeSectionGenerator(settings=settings)

        generator._render_top_badges()

        card_svgs = sorted((tmp_path / "svg").glob("top-contact-card-*.svg"))
        assert len(card_svgs) == len(settings.social_links)
        visible_text: list[str] = []
        for svg_path in card_svgs:
            svg = svg_path.read_text(encoding="utf-8")
            visible_text.extend(
                re.findall(
                    r'<text class="card-(?:line|meta|kicker)"[^>]*>([^<]+)</text>',
                    svg,
                )
            )

        assert visible_text
        assert all("://" not in value for value in visible_text)
        assert all("open-profile" not in value.lower() for value in visible_text)

    def test_top_contact_cards_include_brand_icon_payloads_for_known_networks(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(
                enabled=True,
                output_dir=str(tmp_path / "svg"),
            ),
            social_links=[
                ReadmeSocialLink(
                    label="LinkedIn",
                    url="https://linkedin.com/in/wyattowalsh",
                    color="0A66C2",
                    logo="linkedin",
                ),
                ReadmeSocialLink(
                    label="Kaggle",
                    url="https://kaggle.com/wyattowalsh",
                    color="20BEFF",
                    logo="kaggle",
                ),
                ReadmeSocialLink(
                    label="X",
                    url="https://x.com/wyattowalsh",
                    color="000000",
                    logo="x",
                ),
                ReadmeSocialLink(
                    label="GitHub",
                    url="https://github.com/wyattowalsh",
                    color="181717",
                    logo="github",
                ),
            ],
        )
        generator = ReadmeSectionGenerator(settings=settings)
        captured: list[tuple[str, object]] = []

        def capture_write_svg_asset(
            *,
            asset_name: str,
            block,
            svg_markup=None,
            renderer=None,
        ) -> None:
            captured.append((asset_name, block))

        monkeypatch.setattr(generator, "_write_svg_asset", capture_write_svg_asset)

        generator._render_top_badges()

        assert len(captured) == len(settings.social_links)
        assert all(
            asset_name.startswith("top-contact-card-")
            for asset_name, _ in captured
        )
        assert all(block.family == SvgCardFamily.CONNECT for _, block in captured)
        cards_by_title = {block.cards[0].title: block.cards[0] for _, block in captured}
        for label in ("LinkedIn", "Kaggle", "X", "GitHub"):
            assert (
                getattr(cards_by_title[label], "icon_data_uri", None) is not None
            ), f"{label} should provide icon_data_uri in top contact cards"
            assert getattr(cards_by_title[label], "badge", None) is None

    def test_badge_logo_url_is_embedded_as_data_uri(self, monkeypatch) -> None:
        settings = ReadmeSectionsSettings()
        generator = ReadmeSectionGenerator(settings=settings)

        class FakeResponse:
            def __init__(self, payload: bytes) -> None:
                self._payload = payload
                self.headers = {"Content-Type": "image/x-icon"}

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return None

            def read(self) -> bytes:
                return self._payload

        def fake_urlopen(request, timeout=10.0):  # noqa: ARG001
            return FakeResponse(b"\x00\x00\x01\x00")

        monkeypatch.setattr("scripts.readme_sections.urlopen", fake_urlopen)

        badge_url = generator._build_badge_url(
            label="w4w.dev",
            color="000000",
            logo="https://w4w.dev/favicon.ico",
            logo_color="white",
        )

        assert "logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2C" in badge_url

    def test_badge_logo_url_blocks_unsafe_remote_targets(self, monkeypatch) -> None:
        settings = ReadmeSectionsSettings()
        generator = ReadmeSectionGenerator(settings=settings)
        called = False

        def fake_urlopen(request, timeout=10.0):  # noqa: ARG001
            nonlocal called
            called = True
            raise RuntimeError("urlopen should not be called for blocked URLs")

        monkeypatch.setattr("scripts.readme_sections.urlopen", fake_urlopen)

        badge_url = generator._build_badge_url(
            label="w4w.dev",
            color="000000",
            logo="http://localhost/favicon.ico",
            logo_color="white",
        )

        assert "logo=http%3A%2F%2Flocalhost%2Ffavicon.ico" in badge_url
        assert not called

    def test_featured_projects_render_svg_cards_with_sparkline(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        class FakeResponse:
            def __init__(self, payload: bytes) -> None:
                self._payload = payload
                self.headers = {"Content-Type": "image/png"}

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return None

            def read(self) -> bytes:
                return self._payload

        def fake_urlopen(request, timeout=10.0):  # noqa: ARG001
            return FakeResponse(b"mock-image-bytes")

        monkeypatch.setattr("scripts.readme_sections.urlopen", fake_urlopen)

        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(
                enabled=True,
                output_dir=str(tmp_path / "svg"),
            ),
            featured_repos=[ReadmeFeaturedRepo(full_name="wyattowalsh/riso")],
        )
        generator = ReadmeSectionGenerator(
            settings=settings,
            repo_client=StubRepoClient(
                {
                    "wyattowalsh/riso": RepoMetadata(
                        full_name="wyattowalsh/riso",
                        name="riso",
                        html_url="https://github.com/wyattowalsh/riso",
                        description="Composable scaffolding framework",
                        stars=42,
                        homepage="https://riso.dev",
                        topics=["python", "templates"],
                        updated_at="2026-02-01T00:00:00Z",
                    )
                }
            ),
            star_history_client=StubStarHistoryClient(
                {"wyattowalsh/riso": [0, 1, 3, 5, 8]}
            ),
        )

        html = generator._render_featured_projects()

        card_svgs = sorted((tmp_path / "svg").glob("featured-projects-card-*.svg"))
        assert len(card_svgs) == len(settings.featured_repos)
        for svg_path in card_svgs:
            assert_sanitizer_safe_section_embed(html, svg_path.as_posix())
        assert "Composable scaffolding framework" in html
        assert "★ 42" in html
        assert "riso" in html
        svg_path = card_svgs[0]
        svg = svg_path.read_text(encoding="utf-8")
        assert "data:image/png;base64," in svg
        assert "opengraph.githubassets.com" not in svg

    def test_featured_projects_fallback_copy_is_polished(self, tmp_path: Path) -> None:
        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(
                enabled=True,
                output_dir=str(tmp_path / "svg"),
            ),
            featured_repos=[ReadmeFeaturedRepo(full_name="wyattowalsh/riso")],
        )
        generator = ReadmeSectionGenerator(
            settings=settings,
            repo_client=StubRepoClient({}),
            star_history_client=StubStarHistoryClient({}),
        )

        html = generator._render_featured_projects()

        assert "Unable to fetch repository metadata." not in html
        assert "Live stats are temporarily unavailable" in html
        assert "open repository for details" in html
        card_svgs = sorted((tmp_path / "svg").glob("featured-projects-card-*.svg"))
        assert len(card_svgs) == 1
        svg = card_svgs[0].read_text(encoding="utf-8")
        assert "Unable to fetch repository metadata." not in svg
        assert "Live stats are temporarily unavailable." in svg

    def test_blog_posts_render_svg_cards_with_metadata(self, tmp_path: Path) -> None:
        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(
                enabled=True,
                output_dir=str(tmp_path / "svg"),
            ),
            blog_feed_url="https://w4w.dev/feed.xml",
            blog_post_limit=2,
        )
        generator = ReadmeSectionGenerator(
            settings=settings,
            blog_client=StubBlogClient(
                [
                    BlogPost(title="First Post", url="https://w4w.dev/blog/first"),
                    BlogPost(title="Second Post", url="https://w4w.dev/blog/second"),
                ]
            ),
            blog_metadata_client=StubBlogMetadataClient(
                {
                    "https://w4w.dev/blog/first": {
                        "hero_image": "https://w4w.dev/img/first.png",
                        "summary": "A deep dive into data art.",
                        "published": "2026-02-20",
                        "host": "w4w.dev",
                    },
                    "https://w4w.dev/blog/second": {
                        "hero_image": "https://w4w.dev/img/second.png",
                        "summary": "Another deep dive.",
                        "published": "2026-02-19",
                        "host": "w4w.dev",
                    },
                }
            ),
        )

        html = generator._render_blog_posts()

        card_svgs = sorted((tmp_path / "svg").glob("blog-posts-card-*.svg"))
        assert len(card_svgs) == settings.blog_post_limit
        for svg_path in card_svgs:
            assert_sanitizer_safe_section_embed(html, svg_path.as_posix())
        assert "First Post" in html
        assert "Second Post" in html
        assert "w4w.dev" in html
        assert "Auto-updated from" in html
        assert "https://w4w.dev/feed.xml" in html
        assert "blog-posts.svg" not in html
        card_embeds = re.findall(r'<a href="([^"]+)">\s*<img src="([^"]+)"', html)
        assert {href for href, _ in card_embeds} == {
            "https://w4w.dev/blog/first",
            "https://w4w.dev/blog/second",
        }
        svg_payloads = [path.read_text(encoding="utf-8") for path in card_svgs]
        assert all(svg.count('class="card"') == 1 for svg in svg_payloads)
        assert sum(svg.count('class="card-icon-image"') for svg in svg_payloads) == 2

    def test_blog_cards_use_explicit_family_and_wrapped_primary_copy(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(enabled=True, output_dir=str(tmp_path / "svg")),
            blog_feed_url="https://w4w.dev/feed.xml",
            blog_post_limit=1,
        )
        post_url = "https://w4w.dev/blog/hero-first"
        generator = ReadmeSectionGenerator(
            settings=settings,
            blog_client=StubBlogClient(
                [
                    BlogPost(
                        title=(
                            "A Very Long Blog Post Title That Would Normally Be Truncated ... update "
                            "When We Keep Crude Single-Line Rendering"
                        ),
                        url=post_url,
                    )
                ]
            ),
            blog_metadata_client=StubBlogMetadataClient(
                {
                    post_url: {
                        "hero_image": "https://w4w.dev/img/hero.png",
                        "summary": (
                            "This intentionally long summary should wrap into readable chunks "
                            "instead of becoming one clipped wall of text."
                        ),
                        "published": "2026-03-01",
                        "host": "w4w.dev",
                    }
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

        html = generator._render_blog_posts()

        assert len(captured) == 1
        asset_name, block = next(iter(captured.items()))
        assert re.fullmatch(r"blog-posts-card-01-[a-z0-9-]+", asset_name)
        assert block.family == SvgCardFamily.BLOG
        card = block.cards[0]
        assert card.badge is None
        assert card.kicker is None
        assert card.url == post_url
        assert len(card.lines) >= 2
        assert "..." not in " ".join(card.lines)
        assert "…" not in " ".join(card.lines)
        assert "update" not in " ".join(card.lines).lower()
        assert "<!-- BLOG-POST-LIST:START -->" in html
        assert "<!-- BLOG-POST-LIST:END -->" in html

    def test_blog_cards_skip_unsafe_hero_images_but_keep_clickthrough(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(enabled=True, output_dir=str(tmp_path / "svg")),
            blog_feed_url="https://w4w.dev/feed.xml",
            blog_post_limit=1,
        )
        post_url = "https://w4w.dev/blog/security"
        generator = ReadmeSectionGenerator(
            settings=settings,
            blog_client=StubBlogClient([BlogPost(title="Security Post", url=post_url)]),
            blog_metadata_client=StubBlogMetadataClient(
                {
                    post_url: {
                        "hero_image": "http://127.0.0.1/secret.png",
                        "summary": "Unsafe hero should be dropped.",
                        "published": "2026-03-02",
                        "host": "w4w.dev",
                    }
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

        generator._render_blog_posts()

        assert len(captured) == 1
        asset_name, block = next(iter(captured.items()))
        assert re.fullmatch(r"blog-posts-card-01-[a-z0-9-]+", asset_name)
        card = block.cards[0]
        assert card.background_image is None
        assert card.url == post_url

    def test_blog_cards_resolve_relative_hero_images(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(enabled=True, output_dir=str(tmp_path / "svg")),
            blog_feed_url="https://w4w.dev/feed.xml",
            blog_post_limit=1,
        )
        post_url = "https://w4w.dev/blog/security"
        generator = ReadmeSectionGenerator(
            settings=settings,
            blog_client=StubBlogClient([BlogPost(title="Security Post", url=post_url)]),
            blog_metadata_client=StubBlogMetadataClient(
                {
                    post_url: {
                        "hero_image": "img/hero.png",
                        "summary": "Relative hero path should resolve against the post URL.",
                        "published": "2026-03-02",
                        "host": "w4w.dev",
                    }
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

        generator._render_blog_posts()

        assert len(captured) == 1
        asset_name, block = next(iter(captured.items()))
        assert re.fullmatch(r"blog-posts-card-01-[a-z0-9-]+", asset_name)
        card = block.cards[0]
        assert card.background_image == "https://w4w.dev/blog/img/hero.png"
        assert card.url == post_url

    def test_featured_project_card_composition_sets_icon_data_uri_when_available(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(
                enabled=True,
                output_dir=str(tmp_path / "svg"),
            ),
            featured_repos=[ReadmeFeaturedRepo(full_name="wyattowalsh/riso")],
        )
        generator = ReadmeSectionGenerator(
            settings=settings,
            repo_client=StubRepoClient(
                {
                    "wyattowalsh/riso": RepoMetadata(
                        full_name="wyattowalsh/riso",
                        name="riso",
                        html_url="https://github.com/wyattowalsh/riso",
                        description="Composable scaffolding framework",
                        stars=42,
                        homepage="https://riso.dev",
                        topics=["python", "templates"],
                        updated_at="2026-02-01T00:00:00Z",
                    )
                }
            ),
            star_history_client=StubStarHistoryClient(
                {"wyattowalsh/riso": [0, 1, 3, 5, 8]}
            ),
        )
        monkeypatch.setattr(
            generator,
            "_repo_background_image",
            lambda repo_full_name, metadata: None,
        )
        captured: dict[str, object] = {}

        def capture_write_svg_asset(
            *,
            asset_name: str,
            block,
            svg_markup=None,
            renderer=None,
        ) -> None:
            captured["asset_name"] = asset_name
            captured["block"] = block

        monkeypatch.setattr(generator, "_write_svg_asset", capture_write_svg_asset)

        generator._render_featured_projects()

        assert re.fullmatch(
            r"featured-projects-card-01-[a-z0-9-]+", str(captured.get("asset_name"))
        )
        block = captured["block"]
        assert getattr(block.cards[0], "icon_data_uri", None) is not None

    def test_featured_project_background_uses_data_uri_fallback_when_social_preview_fails(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(
                enabled=True,
                output_dir=str(tmp_path / "svg"),
            ),
            featured_repos=[ReadmeFeaturedRepo(full_name="wyattowalsh/riso")],
        )
        generator = ReadmeSectionGenerator(
            settings=settings,
            repo_client=StubRepoClient(
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

        def fake_urlopen_failure(request, timeout=10.0):  # noqa: ARG001
            raise OSError("preview unavailable")

        monkeypatch.setattr("scripts.readme_sections.urlopen", fake_urlopen_failure)

        generator._render_featured_projects()

        asset_name, block = next(iter(captured.items()))
        assert re.fullmatch(r"featured-projects-card-01-[a-z0-9-]+", asset_name)
        card = block.cards[0]
        background_image = getattr(card, "background_image", "")
        assert isinstance(background_image, str)
        assert background_image.startswith("data:image/svg+xml;base64,")

    def test_featured_background_fetch_skips_oversized_images(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        class FakeResponse:
            def __init__(self) -> None:
                self.headers = {
                    "Content-Type": "image/png",
                    "Content-Length": str(400_000),
                }

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return None

            def read(self) -> bytes:
                return b"x" * 400_000

        def fake_urlopen(request, timeout=10.0):  # noqa: ARG001
            return FakeResponse()

        monkeypatch.setattr("scripts.readme_sections.urlopen", fake_urlopen)

        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(enabled=True, output_dir=str(tmp_path / "svg")),
            featured_repos=[ReadmeFeaturedRepo(full_name="wyattowalsh/riso")],
        )
        generator = ReadmeSectionGenerator(
            settings=settings,
            repo_client=StubRepoClient(
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

        asset_name, block = next(iter(captured.items()))
        assert re.fullmatch(r"featured-projects-card-01-[a-z0-9-]+", asset_name)
        card = block.cards[0]
        background_image = getattr(card, "background_image", "")
        assert isinstance(background_image, str)
        assert background_image.startswith("data:image/svg+xml;base64,")

    def test_blog_card_composition_sets_icon_data_uri_when_available(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(
                enabled=True,
                output_dir=str(tmp_path / "svg"),
            ),
            blog_feed_url="https://w4w.dev/feed.xml",
            blog_post_limit=1,
        )
        generator = ReadmeSectionGenerator(
            settings=settings,
            blog_client=StubBlogClient(
                [BlogPost(title="GitHub Changelog", url="https://github.com/blog/post")]
            ),
            blog_metadata_client=StubBlogMetadataClient(
                {
                    "https://github.com/blog/post": {
                        "hero_image": None,
                        "summary": "Platform update",
                        "published": "2026-03-01",
                        "host": "github.com",
                    }
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

        generator._render_blog_posts()

        assert len(captured) == 1
        asset_name, block = next(iter(captured.items()))
        assert re.fullmatch(r"blog-posts-card-01-[a-z0-9-]+", asset_name)
        assert getattr(block.cards[0], "icon_data_uri", None) is not None

    def test_top_section_renders_link_wrapped_per_card_images(
        self, tmp_path: Path
    ) -> None:
        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(enabled=True, output_dir=str(tmp_path / "svg")),
            social_links=[
                ReadmeSocialLink(
                    label="Website",
                    url="https://w4w.dev",
                    color="000000",
                    logo="safari",
                ),
                ReadmeSocialLink(
                    label="LinkedIn",
                    url="https://linkedin.com/in/wyattowalsh",
                    color="0A66C2",
                    logo="linkedin",
                ),
                ReadmeSocialLink(
                    label="GitHub",
                    url="https://github.com/wyattowalsh",
                    color="181717",
                    logo="github",
                ),
            ],
        )
        generator = ReadmeSectionGenerator(settings=settings)

        html = generator._render_top_badges()
        card_embeds = re.findall(r'<a href="([^"]+)">\s*<img src="([^"]+)"', html)
        expected_urls = {link.url for link in settings.social_links}

        assert len(card_embeds) == len(settings.social_links)
        assert {href for href, _ in card_embeds} == expected_urls
        assert len({src for _, src in card_embeds}) == len(settings.social_links)
        assert "top-contact.svg" not in html
        assert all(
            re.search(r"/top-contact-card-\d{2}-[a-z0-9-]+\.svg$", src)
            for _, src in card_embeds
        )

    def test_featured_section_renders_one_link_wrapped_image_per_repo_card(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(enabled=True, output_dir=str(tmp_path / "svg")),
            featured_repos=[
                ReadmeFeaturedRepo(full_name="wyattowalsh/riso"),
                ReadmeFeaturedRepo(full_name="wyattowalsh/vislib"),
            ],
        )
        generator = ReadmeSectionGenerator(
            settings=settings,
            repo_client=StubRepoClient(
                {
                    "wyattowalsh/riso": RepoMetadata(
                        full_name="wyattowalsh/riso",
                        name="riso",
                        html_url="https://github.com/wyattowalsh/riso",
                        description="Composable scaffolding framework",
                        stars=42,
                        homepage="https://riso.dev",
                        topics=["python", "templates"],
                        updated_at="2026-02-01T00:00:00Z",
                    ),
                    "wyattowalsh/vislib": RepoMetadata(
                        full_name="wyattowalsh/vislib",
                        name="vislib",
                        html_url="https://github.com/wyattowalsh/vislib",
                        description="Visualization toolkit",
                        stars=11,
                        homepage=None,
                        topics=["visualization"],
                        updated_at="2026-02-03T00:00:00Z",
                    ),
                }
            ),
            star_history_client=StubStarHistoryClient({}),
        )
        monkeypatch.setattr(
            generator,
            "_repo_background_image",
            lambda repo_full_name, metadata: None,
        )

        html = generator._render_featured_projects()
        card_embeds = re.findall(r'<a href="([^"]+)">\s*<img src="([^"]+)"', html)
        expected_urls = {
            "https://github.com/wyattowalsh/riso",
            "https://github.com/wyattowalsh/vislib",
        }

        assert len(card_embeds) == len(settings.featured_repos)
        assert {href for href, _ in card_embeds} == expected_urls
        assert all(
            re.search(r"/featured-projects-card-\d{2}-[a-z0-9-]+\.svg$", src)
            for _, src in card_embeds
        )

    def test_blog_section_renders_one_link_wrapped_image_per_post_and_keeps_fallback_list(
        self, tmp_path: Path
    ) -> None:
        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(enabled=True, output_dir=str(tmp_path / "svg")),
            blog_feed_url="https://w4w.dev/feed.xml",
            blog_post_limit=2,
        )
        posts = [
            BlogPost(title="First Post", url="https://w4w.dev/blog/first"),
            BlogPost(title="Second Post", url="https://w4w.dev/blog/second"),
        ]
        generator = ReadmeSectionGenerator(
            settings=settings,
            blog_client=StubBlogClient(posts),
            blog_metadata_client=StubBlogMetadataClient(
                {
                    "https://w4w.dev/blog/first": {
                        "hero_image": "https://w4w.dev/img/first.png",
                        "summary": "A deep dive into data art.",
                        "published": "2026-02-20",
                        "host": "w4w.dev",
                    },
                    "https://w4w.dev/blog/second": {
                        "hero_image": "https://w4w.dev/img/second.png",
                        "summary": "Another deep dive.",
                        "published": "2026-02-19",
                        "host": "w4w.dev",
                    },
                }
            ),
        )

        html = generator._render_blog_posts()
        card_embeds = re.findall(r'<a href="([^"]+)">\s*<img src="([^"]+)"', html)
        expected_urls = {post.url for post in posts}

        assert "<!-- BLOG-POST-LIST:START -->" in html
        assert "<!-- BLOG-POST-LIST:END -->" in html
        assert "- [First Post](https://w4w.dev/blog/first)" in html
        assert "- [Second Post](https://w4w.dev/blog/second)" in html
        assert len(card_embeds) == len(posts)
        assert {href for href, _ in card_embeds} == expected_urls
        assert all(
            re.search(r"/blog-posts-card-\d{2}-[a-z0-9-]+\.svg$", src)
            for _, src in card_embeds
        )

    def test_card_svg_assets_follow_deterministic_per_card_naming_pattern(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(enabled=True, output_dir=str(tmp_path / "svg")),
            social_links=[
                ReadmeSocialLink(
                    label="Website",
                    url="https://w4w.dev",
                    color="000000",
                    logo="safari",
                ),
                ReadmeSocialLink(
                    label="GitHub",
                    url="https://github.com/wyattowalsh",
                    color="181717",
                    logo="github",
                ),
            ],
            featured_repos=[
                ReadmeFeaturedRepo(full_name="wyattowalsh/riso"),
                ReadmeFeaturedRepo(full_name="wyattowalsh/vislib"),
            ],
            blog_feed_url="https://w4w.dev/feed.xml",
            blog_post_limit=2,
        )
        generator = ReadmeSectionGenerator(
            settings=settings,
            repo_client=StubRepoClient(
                {
                    "wyattowalsh/riso": RepoMetadata(
                        full_name="wyattowalsh/riso",
                        name="riso",
                        html_url="https://github.com/wyattowalsh/riso",
                        description="Composable scaffolding framework",
                        stars=42,
                        homepage="https://riso.dev",
                        topics=["python", "templates"],
                        updated_at="2026-02-01T00:00:00Z",
                    ),
                    "wyattowalsh/vislib": RepoMetadata(
                        full_name="wyattowalsh/vislib",
                        name="vislib",
                        html_url="https://github.com/wyattowalsh/vislib",
                        description="Visualization toolkit",
                        stars=11,
                        homepage=None,
                        topics=["visualization"],
                        updated_at="2026-02-03T00:00:00Z",
                    ),
                }
            ),
            star_history_client=StubStarHistoryClient({}),
            blog_client=StubBlogClient(
                [
                    BlogPost(title="First Post", url="https://w4w.dev/blog/first"),
                    BlogPost(title="Second Post", url="https://w4w.dev/blog/second"),
                ]
            ),
            blog_metadata_client=StubBlogMetadataClient(
                {
                    "https://w4w.dev/blog/first": {
                        "hero_image": None,
                        "summary": "One",
                        "published": "2026-02-20",
                        "host": "w4w.dev",
                    },
                    "https://w4w.dev/blog/second": {
                        "hero_image": None,
                        "summary": "Two",
                        "published": "2026-02-19",
                        "host": "w4w.dev",
                    },
                }
            ),
        )
        monkeypatch.setattr(
            generator,
            "_repo_background_image",
            lambda repo_full_name, metadata: None,
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

        generator._render_top_badges()
        generator._render_featured_projects()
        generator._render_blog_posts()

        expected_count = (
            len(settings.social_links)
            + len(settings.featured_repos)
            + settings.blog_post_limit
        )
        pattern = re.compile(
            r"^(top-contact|featured-projects|blog-posts)-card-\d{2}-[a-z0-9-]+$"
        )

        assert len(captured_asset_names) == expected_count
        assert len(set(captured_asset_names)) == len(captured_asset_names)
        assert all(pattern.fullmatch(asset_name) for asset_name in captured_asset_names)


class TestRemoteFetchSafety:
    def test_blog_feed_client_blocks_non_http_scheme(self, monkeypatch) -> None:
        client = BlogFeedClient()
        called = False

        def fake_urlopen(request, timeout=10.0):  # noqa: ARG001
            nonlocal called
            called = True
            raise RuntimeError("urlopen should not be called for blocked URLs")

        monkeypatch.setattr("scripts.readme_sections.urlopen", fake_urlopen)

        posts = client.fetch_latest_posts("ftp://example.com/feed.xml", limit=2)

        assert posts == []
        assert not called

    def test_blog_feed_client_blocks_unsafe_url(self, monkeypatch) -> None:
        client = BlogFeedClient()
        called = False

        def fake_urlopen(request, timeout=10.0):  # noqa: ARG001
            nonlocal called
            called = True
            raise RuntimeError("urlopen should not be called for blocked URLs")

        monkeypatch.setattr("scripts.readme_sections.urlopen", fake_urlopen)

        posts = client.fetch_latest_posts("http://127.0.0.1/feed.xml", limit=2)

        assert posts == []
        assert not called

    def test_blog_metadata_client_blocks_unsafe_url(self, monkeypatch) -> None:
        client = BlogMetadataClient()
        called = False

        def fake_urlopen(request, timeout=10.0):  # noqa: ARG001
            nonlocal called
            called = True
            raise RuntimeError("urlopen should not be called for blocked URLs")

        monkeypatch.setattr("scripts.readme_sections.urlopen", fake_urlopen)

        metadata = client.fetch_metadata("http://localhost/blog/post")

        assert metadata == {
            "hero_image": None,
            "summary": None,
            "published": None,
            "host": "localhost",
        }
        assert not called


class TestReadmeInjection:
    def test_generate_replaces_between_markers(self, tmp_path: Path) -> None:
        readme_path = tmp_path / "README.md"
        readme_path.write_text(
            "before\n"
            "<!-- README:TOP_BADGES:START -->\n"
            "old top\n"
            "<!-- README:TOP_BADGES:END -->\n"
            "<!-- README:FEATURED_PROJECTS:START -->\n"
            "old projects\n"
            "<!-- README:FEATURED_PROJECTS:END -->\n"
            "<!-- README:BLOG_POSTS:START -->\n"
            "old posts\n"
            "<!-- README:BLOG_POSTS:END -->\n"
            "after\n",
            encoding="utf-8",
        )

        settings = ReadmeSectionsSettings(
            readme_path=str(readme_path),
            svg=ReadmeSvgSettings(
                enabled=True,
                output_dir=str(tmp_path / "svg"),
            ),
            social_links=[
                ReadmeSocialLink(
                    label="GitHub",
                    url="https://github.com/wyattowalsh",
                    color="181717",
                    logo="github",
                )
            ],
            featured_repos=[ReadmeFeaturedRepo(full_name="wyattowalsh/riso")],
            blog_feed_url="https://example.com/feed.xml",
            blog_post_limit=2,
        )
        generator = ReadmeSectionGenerator(
            settings=settings,
            repo_client=StubRepoClient(
                {
                    "wyattowalsh/riso": RepoMetadata(
                        full_name="wyattowalsh/riso",
                        name="riso",
                        html_url="https://github.com/wyattowalsh/riso",
                        description="Composable scaffolding framework",
                        stars=42,
                        homepage=None,
                        topics=["python"],
                        updated_at="2026-02-01T00:00:00Z",
                    )
                }
            ),
            blog_client=StubBlogClient(
                [
                    BlogPost(title="First Post", url="https://w4w.dev/blog/first"),
                    BlogPost(title="Second Post", url="https://w4w.dev/blog/second"),
                ]
            ),
            star_history_client=StubStarHistoryClient({}),
            blog_metadata_client=StubBlogMetadataClient({}),
        )

        generator.generate()

        content = readme_path.read_text(encoding="utf-8")
        assert "old top" not in content
        assert "old projects" not in content
        assert "old posts" not in content
        assert "<svg" not in content
        assert "&lt;svg" not in content
        assert "&lt;style&gt;" not in content
        assert "<!-- README:TOP_BADGES:START -->" in content
        assert "<!-- README:TOP_BADGES:END -->" in content
        assert "<!-- README:FEATURED_PROJECTS:START -->" in content
        assert "<!-- README:FEATURED_PROJECTS:END -->" in content
        assert "<!-- README:BLOG_POSTS:START -->" in content
        assert "<!-- README:BLOG_POSTS:END -->" in content
        assert re.search(r"top-contact-card-\d{2}-[a-z0-9-]+\.svg", content)
        assert re.search(r"featured-projects-card-\d{2}-[a-z0-9-]+\.svg", content)
        assert re.search(r"blog-posts-card-\d{2}-[a-z0-9-]+\.svg", content)
        assert ".github/assets/img/gh.gif" not in content
        assert "[GitHub](https://github.com/wyattowalsh)" in content
        assert "[riso](https://github.com/wyattowalsh/riso)" in content
        assert "First Post" in content
        assert "[First Post](https://w4w.dev/blog/first)" in content
        assert "Auto-updated from" in content
        assert '<a href="https://example.com/feed.xml">RSS feed</a>' in content
        assert "<!-- BLOG-POST-LIST:START -->" in content
        assert "<!-- BLOG-POST-LIST:END -->" in content
        assert "before" in content
        assert "after" in content

    def test_blog_svg_embed_survives_blog_list_refresh(self, tmp_path: Path) -> None:
        readme_path = tmp_path / "README.md"
        readme_path.write_text(
            "before\n"
            "<!-- README:TOP_BADGES:START -->\n"
            "old top\n"
            "<!-- README:TOP_BADGES:END -->\n"
            "<!-- README:FEATURED_PROJECTS:START -->\n"
            "old projects\n"
            "<!-- README:FEATURED_PROJECTS:END -->\n"
            "<!-- README:BLOG_POSTS:START -->\n"
            "old posts\n"
            "<!-- README:BLOG_POSTS:END -->\n"
            "after\n",
            encoding="utf-8",
        )
        settings = ReadmeSectionsSettings(
            readme_path=str(readme_path),
            svg=ReadmeSvgSettings(
                enabled=True,
                output_dir=str(tmp_path / "svg"),
                top_contact=False,
                featured_projects=False,
                blog_posts=True,
            ),
            blog_feed_url="https://w4w.dev/feed.xml",
            blog_post_limit=1,
        )
        generator = ReadmeSectionGenerator(
            settings=settings,
            blog_client=StubBlogClient(
                [BlogPost(title="First Post", url="https://w4w.dev/blog/first")]
            ),
            blog_metadata_client=StubBlogMetadataClient(
                {
                    "https://w4w.dev/blog/first": {
                        "hero_image": "https://w4w.dev/img/first.png",
                        "summary": "A deep dive into data art.",
                        "published": "2026-02-20",
                        "host": "w4w.dev",
                    }
                }
            ),
        )

        generator.generate()

        generated = readme_path.read_text(encoding="utf-8")
        refreshed = re.sub(
            r"<!-- BLOG-POST-LIST:START -->.*?<!-- BLOG-POST-LIST:END -->",
            (
                "<!-- BLOG-POST-LIST:START -->\n"
                "- [Fresh Post](https://w4w.dev/blog/fresh)\n"
                "<!-- BLOG-POST-LIST:END -->"
            ),
            generated,
            flags=re.DOTALL,
        )

        generated_assets = set(
            re.findall(r"blog-posts-card-\d{2}-[a-z0-9-]+\.svg", generated)
        )
        refreshed_assets = set(
            re.findall(r"blog-posts-card-\d{2}-[a-z0-9-]+\.svg", refreshed)
        )

        assert generated_assets
        assert refreshed_assets == generated_assets

    def test_generate_respects_svg_feature_toggles(self, tmp_path: Path) -> None:
        readme_path = tmp_path / "README.md"
        readme_path.write_text(
            "before\n"
            "<!-- README:TOP_BADGES:START -->\n"
            "old top\n"
            "<!-- README:TOP_BADGES:END -->\n"
            "<!-- README:FEATURED_PROJECTS:START -->\n"
            "old projects\n"
            "<!-- README:FEATURED_PROJECTS:END -->\n"
            "<!-- README:BLOG_POSTS:START -->\n"
            "old posts\n"
            "<!-- README:BLOG_POSTS:END -->\n"
            "after\n",
            encoding="utf-8",
        )

        svg_dir = tmp_path / "svg-assets"
        settings = ReadmeSectionsSettings(
            readme_path=str(readme_path),
            social_links=[
                ReadmeSocialLink(
                    label="GitHub",
                    url="https://github.com/wyattowalsh",
                    color="181717",
                    logo="github",
                )
            ],
            featured_repos=[ReadmeFeaturedRepo(full_name="wyattowalsh/riso")],
            blog_feed_url="https://example.com/feed.xml",
            blog_post_limit=2,
            svg=ReadmeSvgSettings(
                enabled=True,
                output_dir=str(svg_dir),
                top_contact=False,
                featured_projects=True,
                blog_posts=False,
            ),
        )
        generator = ReadmeSectionGenerator(
            settings=settings,
            repo_client=StubRepoClient(
                {
                    "wyattowalsh/riso": RepoMetadata(
                        full_name="wyattowalsh/riso",
                        name="riso",
                        html_url="https://github.com/wyattowalsh/riso",
                        description="Composable scaffolding framework",
                        stars=42,
                        homepage=None,
                        topics=["python"],
                        updated_at="2026-02-01T00:00:00Z",
                    )
                }
            ),
            blog_client=StubBlogClient(
                [
                    BlogPost(title="First Post", url="https://w4w.dev/blog/first"),
                ]
            ),
            star_history_client=StubStarHistoryClient({}),
            blog_metadata_client=StubBlogMetadataClient({}),
        )

        generator.generate()

        content = readme_path.read_text(encoding="utf-8")
        assert not list(svg_dir.glob("top-contact-card-*.svg"))
        assert list(svg_dir.glob("featured-projects-card-*.svg"))
        assert not list(svg_dir.glob("blog-posts-card-*.svg"))
        assert "top-contact-card-" not in content
        assert "blog-posts-card-" not in content
        assert "featured-projects-card-" in content
        assert "[GitHub](https://github.com/wyattowalsh)" in content
        assert "[First Post](https://w4w.dev/blog/first)" in content

    def test_connect_cards_remove_handle_open_profile_and_pill_but_clickable(
        self, tmp_path: Path
    ) -> None:
        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(enabled=True, output_dir=str(tmp_path / "svg")),
            social_links=[
                ReadmeSocialLink(
                    label="GitHub",
                    url="https://github.com/wyattowalsh",
                    color="181717",
                    logo="github",
                )
            ],
        )
        generator = ReadmeSectionGenerator(settings=settings)

        html = generator._render_top_badges()
        card_svgs = sorted((tmp_path / "svg").glob("top-contact-card-*.svg"))
        assert len(card_svgs) == 1
        svg = card_svgs[0].read_text(encoding="utf-8")

        # Expect no handle clutter or open-profile URL fragments
        assert "@wyattowalsh" not in svg
        assert "open-profile" not in svg
        # Expect no upper-right pill element on connect cards
        assert 'class="card-pill"' not in svg
        assert 'class="card-badge"' not in svg
        # But the card should still be clickable (link present)
        assert 'href="https://github.com/wyattowalsh"' in svg

    def test_featured_cards_include_richer_metadata_and_exclude_footer_copy(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(enabled=True, output_dir=str(tmp_path / "svg")),
            featured_repos=[ReadmeFeaturedRepo(full_name="wyattowalsh/riso")],
        )
        generator = ReadmeSectionGenerator(
            settings=settings,
            repo_client=StubRepoClient(
                {
                    "wyattowalsh/riso": RepoMetadata(
                        full_name="wyattowalsh/riso",
                        name="riso",
                        html_url="https://github.com/wyattowalsh/riso",
                        description="Composable scaffolding framework",
                        stars=42,
                        homepage="https://riso.dev",
                        topics=["python", "templates"],
                        updated_at="2026-02-01T00:00:00Z",
                    )
                }
            ),
        )

        captured: dict[str, tuple[object, str]] = {}

        def capture_write_svg_asset(
            *, asset_name: str, block, svg_markup=None, renderer=None
        ) -> None:
            rendered_svg = (
                svg_markup if isinstance(svg_markup, str) else renderer.render(block)
            )
            captured[asset_name] = (block, rendered_svg)

        monkeypatch.setattr(generator, "_write_svg_asset", capture_write_svg_asset)

        generator._render_featured_projects()

        matching = [
            (asset_name, payload)
            for asset_name, payload in captured.items()
            if re.fullmatch(r"featured-projects-card-01-[a-z0-9-]+", asset_name)
        ]
        assert len(matching) == 1
        _, captured_payload = matching[0]
        block, svg = captured_payload
        card = block.cards[0]

        # Expect richer metadata fields exposed on the card model
        assert block.family == SvgCardFamily.FEATURED
        assert getattr(card, "family", None) == SvgCardFamily.FEATURED.value
        assert getattr(card, "homepage", None) is not None
        assert getattr(card, "topics", None) is not None
        assert getattr(card, "updated_at", None) is not None
        assert getattr(card, "metadata_chips", ())
        assert getattr(card, "metadata_rows", ())

        # The rendered SVG should not include the generic footer copy 'GitHub repository'
        assert "GitHub repository" not in svg

    def test_blog_cards_remove_badge_and_update_kicker_and_wrap_titles(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(enabled=True, output_dir=str(tmp_path / "svg")),
            blog_feed_url="https://w4w.dev/feed.xml",
            blog_post_limit=1,
        )
        generator = ReadmeSectionGenerator(
            settings=settings,
            blog_client=StubBlogClient(
                [
                    BlogPost(
                        title="A Very Long Blog Post Title That Would Normally Be Truncated ... update",
                        url="https://w4w.dev/blog/long",
                    )
                ]
            ),
            blog_metadata_client=StubBlogMetadataClient(
                {
                    "https://w4w.dev/blog/long": {
                        "hero_image": None,
                        "summary": "Long post",
                        "published": "2026-03-01",
                        "host": "w4w.dev",
                    }
                }
            ),
        )

        captured: dict[str, object] = {}

        def capture_write_svg_asset(
            *, asset_name: str, block, svg_markup=None, renderer=None
        ) -> None:
            rendered_svg = (
                svg_markup if isinstance(svg_markup, str) else renderer.render(block)
            )
            captured[asset_name] = (block, rendered_svg)

        monkeypatch.setattr(generator, "_write_svg_asset", capture_write_svg_asset)

        generator._render_blog_posts()

        blog_assets = {
            asset_name: payload
            for asset_name, payload in captured.items()
            if asset_name.startswith("blog-posts-card-")
        }
        assert len(blog_assets) == 1
        block, svg_markup = next(iter(blog_assets.values()))
        assert block is not None

        card = block.cards[0]
        # Expect no badge on blog cards
        assert getattr(card, "badge", None) is None
        # Expect no '... update' kicker in meta
        assert not any("update" in (m or "") for m in getattr(card, "meta", ()))

        # Expect the SVG markup to avoid ellipsis truncation and allow wrapping (multiple <tspan> for title)
        assert svg_markup is not None
        assert "..." not in svg_markup
        assert "<tspan" in svg_markup

    def test_card_generators_are_bespoke_per_family(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(enabled=True, output_dir=str(tmp_path / "svg")),
            featured_repos=[ReadmeFeaturedRepo(full_name="wyattowalsh/riso")],
            blog_feed_url="https://w4w.dev/feed.xml",
            blog_post_limit=1,
        )
        generator = ReadmeSectionGenerator(
            settings=settings,
            repo_client=StubRepoClient(
                {
                    "wyattowalsh/riso": RepoMetadata(
                        full_name="wyattowalsh/riso",
                        name="riso",
                        html_url="https://github.com/wyattowalsh/riso",
                        description="Composable scaffolding framework",
                        stars=42,
                        homepage=None,
                        topics=["python"],
                        updated_at="2026-02-01T00:00:00Z",
                    )
                }
            ),
            blog_client=StubBlogClient(
                [BlogPost(title="Post", url="https://w4w.dev/blog/post")]
            ),
            blog_metadata_client=StubBlogMetadataClient(
                {
                    "https://w4w.dev/blog/post": {
                        "hero_image": None,
                        "summary": "x",
                        "published": "2026-03-01",
                        "host": "w4w.dev",
                    }
                }
            ),
        )

        captured: dict[str, object] = {}

        def capture_write_svg_asset(
            *, asset_name: str, block, svg_markup=None, renderer=None
        ) -> None:
            captured[asset_name] = block

        monkeypatch.setattr(generator, "_write_svg_asset", capture_write_svg_asset)

        generator._render_top_badges()
        generator._render_featured_projects()
        generator._render_blog_posts()

        top_block = next(
            (
                block
                for asset_name, block in captured.items()
                if asset_name.startswith("top-contact-card-")
            ),
            None,
        )
        featured_block = next(
            (
                block
                for asset_name, block in captured.items()
                if asset_name.startswith("featured-projects-card-")
            ),
            None,
        )
        blog_block = next(
            (
                block
                for asset_name, block in captured.items()
                if asset_name.startswith("blog-posts-card-")
            ),
            None,
        )

        assert (
            top_block is not None
            and featured_block is not None
            and blog_block is not None
        )
        assert top_block.family == SvgCardFamily.CONNECT
        assert featured_block.family == SvgCardFamily.FEATURED
        assert blog_block.family == SvgCardFamily.BLOG

        top_fields = set(dir(top_block.cards[0]))
        featured_fields = set(dir(featured_block.cards[0]))
        blog_fields = set(dir(blog_block.cards[0]))

        # Expect the card models for each family to differ in their exposed attributes (i.e., bespoke generators)
        assert top_fields != featured_fields or featured_fields != blog_fields
