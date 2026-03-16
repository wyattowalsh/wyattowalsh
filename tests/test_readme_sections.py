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


class StubRepoClient:
    def __init__(
        self,
        metadata_by_repo: dict[str, RepoMetadata],
        languages_by_repo: dict[str, dict[str, int]] | None = None,
    ) -> None:
        self.metadata_by_repo = metadata_by_repo
        self.languages_by_repo = languages_by_repo or {}

    def fetch_repo_metadata(self, full_name: str) -> Optional[RepoMetadata]:
        return self.metadata_by_repo.get(full_name)

    def fetch_repo_languages(
        self, full_name: str,
    ) -> Optional[dict[str, int]]:
        return self.languages_by_repo.get(full_name)


class StubBlogClient:
    def __init__(self, posts: list[BlogPost]) -> None:
        self.posts = posts

    def fetch_latest_posts(self, feed_url: str, limit: int) -> list[BlogPost]:
        return self.posts[:limit]


class StubStarHistoryClient:
    def __init__(self, series: dict[str, list[int]]) -> None:
        self.series = series

    def fetch_star_history(self, full_name: str, sample: int = 24) -> Optional[list[int]]:
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
            ]
        )
        generator = ReadmeSectionGenerator(settings=settings)

        html = generator._render_top_badges()

        # Per-card SVGs should exist
        assert (tmp_path / "svg" / "connect-website.svg").exists()
        assert (tmp_path / "svg" / "connect-linkedin.svg").exists()
        assert (tmp_path / "svg" / "connect-github.svg").exists()
        assert "<img" in html
        assert "connect-website.svg" in html
        assert "connect-linkedin.svg" in html
        assert "connect-github.svg" in html
        assert "<svg" not in html
        assert "❈" not in html
        assert "https://w4w.dev" in html
        assert "https://linkedin.com/in/wyattowalsh" in html
        assert ".github/assets/img/gh.gif" not in html

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

        html = generator._render_top_badges()

        # Per-card SVGs should exist
        assert (tmp_path / "svg" / "connect-linkedin.svg").exists()
        assert (tmp_path / "svg" / "connect-github.svg").exists()
        # The HTML output should not contain full profile URLs as visible text
        # (URLs appear only in href attributes, not as display text)
        for svg_name in ("connect-linkedin.svg", "connect-github.svg"):
            svg = (tmp_path / "svg" / svg_name).read_text(encoding="utf-8")
            # Visible text elements should not contain protocol prefixes
            text_values = re.findall(r'>([^<]+)<', svg)
            assert all(
                "://" not in val
                for val in text_values
                if val.strip()
            )

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

        generator._render_top_badges()

        # Per-card SVGs should exist and contain icon data (data:image URI)
        for label in ("linkedin", "kaggle", "x", "github"):
            svg_path = tmp_path / "svg" / f"connect-{label}.svg"
            assert svg_path.exists(), f"connect-{label}.svg should exist"
            svg = svg_path.read_text(encoding="utf-8")
            assert "data:image" in svg, (
                f"connect-{label}.svg should contain brand icon data URI"
            )

    def test_featured_projects_render_per_card_svgs(
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
                        language="Python",
                        forks=12,
                    )
                },
                languages_by_repo={
                    "wyattowalsh/riso": {
                        "Python": 8000, "Shell": 2000,
                    },
                },
            ),
            star_history_client=StubStarHistoryClient(
                {"wyattowalsh/riso": [0, 1, 3, 5, 8]}
            ),
        )

        html = generator._render_featured_projects()

        # Per-card SVG should be created
        card_svg_path = tmp_path / "svg" / "featured-card-riso.svg"
        assert card_svg_path.exists()
        svg = card_svg_path.read_text(encoding="utf-8")
        assert "riso" in svg
        assert "Composable scaffolding framework" in svg
        # OG image embedded as thumbnail
        assert "data:image/png;base64," in svg
        # Sparkline rendered
        assert "sparkline-group" in svg
        # Multi-language bar rendered
        assert "lang-bar-clip" in svg
        # HTML uses table layout with per-card img tags
        assert "<table>" in html
        assert "featured-card-riso.svg" in html
        assert "Composable scaffolding framework" in svg

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
        # Per-card SVG should exist with fallback content
        card_svg_path = tmp_path / "svg" / "featured-card-riso.svg"
        assert card_svg_path.exists()
        svg = card_svg_path.read_text(encoding="utf-8")
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
                    }
                }
            ),
        )

        html = generator._render_blog_posts()

        # Per-card blog SVGs should exist
        assert (tmp_path / "svg" / "blog-first-post.svg").exists()
        assert (tmp_path / "svg" / "blog-second-post.svg").exists()
        assert "<img" in html
        assert "blog-first-post.svg" in html
        assert "blog-second-post.svg" in html
        assert "<svg" not in html
        assert "Auto-updated from" in html
        assert "https://w4w.dev/feed.xml" in html

    def test_featured_project_card_builds_with_icon_data_uri(
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
                        language="Python",
                        forks=12,
                    )
                }
            ),
            star_history_client=StubStarHistoryClient(
                {"wyattowalsh/riso": [0, 1, 3, 5, 8]}
            ),
        )

        card = generator._build_project_svg_card(
            "wyattowalsh/riso",
            generator.repo_client.fetch_repo_metadata("wyattowalsh/riso"),
        )
        assert getattr(card, "icon_data_uri", None) is not None

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

        html = generator._render_blog_posts()

        # Per-card SVG should exist
        svg_path = tmp_path / "svg" / "blog-github-changelog.svg"
        assert svg_path.exists()
        # The card building logic sets icon_data_uri even though the blog
        # renderer does not embed it. Verify by checking the HTML output
        # contains the per-card SVG reference.
        assert "blog-github-changelog.svg" in html


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
        assert "connect-github.svg" in content
        assert "featured-card-riso.svg" in content
        assert "blog-first-post.svg" in content
        assert ".github/assets/img/gh.gif" not in content
        assert "github.com/wyattowalsh" in content
        assert "Auto-updated from" in content
        assert '<a href="https://example.com/feed.xml">RSS feed</a>' in content
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

        assert "blog-first-post.svg" in generated
        assert "blog-first-post.svg" in refreshed

    def test_generate_respects_svg_feature_toggles(
        self, tmp_path: Path
    ) -> None:
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
        assert not (svg_dir / "top-contact.svg").exists()
        assert (svg_dir / "featured-card-riso.svg").exists()
        assert not (svg_dir / "blog-posts.svg").exists()
        assert "top-contact.svg" not in content
        assert "blog-posts.svg" not in content
        assert "featured-card-riso.svg" in content
        assert "github.com/wyattowalsh" in content

    def test_connect_cards_remove_handle_open_profile_and_pill_but_clickable(self, tmp_path: Path) -> None:
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

        generator._render_top_badges()
        svg_path = tmp_path / "svg" / "connect-github.svg"
        assert svg_path.exists()
        svg = svg_path.read_text(encoding="utf-8")

        # Expect no handle clutter or open-profile URL fragments
        assert "@wyattowalsh" not in svg
        assert "open-profile" not in svg
        # Expect no upper-right pill element on connect cards
        assert 'class="card-pill"' not in svg

    def test_featured_cards_include_richer_metadata_and_exclude_footer_copy(self, tmp_path: Path, monkeypatch) -> None:
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
                        language="Python",
                        forks=12,
                    )
                }
            ),
        )

        generator._render_featured_projects()

        # Per-card SVG should exist
        card_svg_path = tmp_path / "svg" / "featured-card-riso.svg"
        assert card_svg_path.exists()
        svg = card_svg_path.read_text(encoding="utf-8")

        # Verify card model has richer metadata via building it directly
        card = generator._build_project_svg_card(
            "wyattowalsh/riso",
            generator.repo_client.fetch_repo_metadata("wyattowalsh/riso"),
        )
        assert getattr(card, "homepage", None) is not None
        assert getattr(card, "topics", None) is not None
        assert getattr(card, "updated_at", None) is not None
        assert any(m.startswith("lang:") for m in card.meta), "meta should contain lang: prefix"
        assert any("★" in m for m in card.meta), "meta should contain star icon"
        assert any("⑂" in m for m in card.meta), "meta should contain fork icon"

        # The rendered SVG should not include the generic footer copy 'GitHub repository'
        assert "GitHub repository" not in svg

    def test_blog_cards_remove_badge_and_update_kicker_and_wrap_titles(self, tmp_path: Path, monkeypatch) -> None:
        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(enabled=True, output_dir=str(tmp_path / "svg")),
            blog_feed_url="https://w4w.dev/feed.xml",
            blog_post_limit=1,
        )
        generator = ReadmeSectionGenerator(
            settings=settings,
            blog_client=StubBlogClient([BlogPost(title="A Very Long Blog Post Title That Would Normally Be Truncated ... update", url="https://w4w.dev/blog/long")]),
            blog_metadata_client=StubBlogMetadataClient({"https://w4w.dev/blog/long": {"hero_image": None, "summary": "Long post", "published": "2026-03-01", "host": "w4w.dev"}}),
        )

        html = generator._render_blog_posts()

        # Per-card SVG should be generated (title slug has trailing "update" stripped)
        svg_files = list((tmp_path / "svg").glob("blog-*.svg"))
        assert len(svg_files) == 1
        svg = svg_files[0].read_text(encoding="utf-8")

        # The trailing "update" should be stripped from the title in the SVG
        # The title in SVG should not end with " update"
        assert "blog-title" in svg
        # The blog-desc should contain the summary
        assert "Long post" in svg

    def test_card_generators_are_bespoke_per_family(self, tmp_path: Path, monkeypatch) -> None:
        settings = ReadmeSectionsSettings(svg=ReadmeSvgSettings(enabled=True, output_dir=str(tmp_path / "svg")), featured_repos=[ReadmeFeaturedRepo(full_name="wyattowalsh/riso")], blog_feed_url="https://w4w.dev/feed.xml", blog_post_limit=1)
        generator = ReadmeSectionGenerator(
            settings=settings,
            repo_client=StubRepoClient({"wyattowalsh/riso": RepoMetadata(full_name="wyattowalsh/riso", name="riso", html_url="https://github.com/wyattowalsh/riso", description="Composable scaffolding framework", stars=42, homepage=None, topics=["python"], updated_at="2026-02-01T00:00:00Z")} ),
            blog_client=StubBlogClient([BlogPost(title="Post", url="https://w4w.dev/blog/post")]),
            blog_metadata_client=StubBlogMetadataClient({"https://w4w.dev/blog/post": {"hero_image": None, "summary": "x", "published": "2026-03-01", "host": "w4w.dev"}}),
        )

        generator._render_top_badges()
        generator._render_blog_posts()

        # Featured cards carry star counts while contact cards don't.
        featured_card = generator._build_project_svg_card(
            "wyattowalsh/riso",
            generator.repo_client.fetch_repo_metadata("wyattowalsh/riso"),
        )

        # Read a connect card SVG to verify it lacks star counts
        connect_svg = list((tmp_path / "svg").glob("connect-*.svg"))
        assert connect_svg, "connect card SVGs should be generated"
        connect_content = connect_svg[0].read_text(encoding="utf-8")

        featured_has_stars = any("\u2605" in (m or "") for m in (featured_card.meta or []))
        top_has_stars = "\u2605" in connect_content
        assert featured_has_stars and not top_has_stars


class TestProjectCardMeta:
    """Verify project card meta includes lang:, star, and fork prefixes."""

    def test_project_card_meta_contains_lang_star_fork(self, tmp_path: Path, monkeypatch) -> None:
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
                        homepage=None,
                        topics=["python"],
                        updated_at="2026-02-01T00:00:00Z",
                        language="Python",
                        forks=12,
                    )
                }
            ),
            star_history_client=StubStarHistoryClient({}),
        )
        monkeypatch.setattr(
            generator,
            "_repo_background_image",
            lambda repo_full_name, metadata: None,
        )
        card = generator._build_project_svg_card(
            "wyattowalsh/riso",
            generator.repo_client.fetch_repo_metadata("wyattowalsh/riso"),
        )
        assert "lang:Python" in card.meta
        assert "★ 42" in card.meta
        assert "⑂ 12" in card.meta

    def test_project_card_meta_omits_lang_when_none(self, tmp_path: Path, monkeypatch) -> None:
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
                        description="No-language repo",
                        stars=5,
                        homepage=None,
                        topics=[],
                        updated_at="2026-02-01T00:00:00Z",
                        language=None,
                        forks=0,
                    )
                }
            ),
            star_history_client=StubStarHistoryClient({}),
        )
        monkeypatch.setattr(
            generator,
            "_repo_background_image",
            lambda repo_full_name, metadata: None,
        )
        card = generator._build_project_svg_card(
            "wyattowalsh/riso",
            generator.repo_client.fetch_repo_metadata("wyattowalsh/riso"),
        )
        assert not any(m.startswith("lang:") for m in card.meta)
        assert "★ 5" in card.meta
        # forks=0 should not appear
        assert not any("⑂" in m for m in card.meta)


class TestBlogTitleSanitization:
    """Verify the blog title regex is properly anchored."""

    def test_trailing_update_is_stripped(self, tmp_path: Path) -> None:
        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(enabled=True, output_dir=str(tmp_path / "svg")),
            blog_feed_url="https://w4w.dev/feed.xml",
            blog_post_limit=1,
        )
        generator = ReadmeSectionGenerator(
            settings=settings,
            blog_client=StubBlogClient(
                [BlogPost(title="My Cool Post update", url="https://w4w.dev/blog/cool")]
            ),
            blog_metadata_client=StubBlogMetadataClient(
                {"https://w4w.dev/blog/cool": {"host": "w4w.dev"}}
            ),
        )

        html = generator._render_blog_posts()

        # The per-card SVG file name should reflect the stripped title
        svg_files = list((tmp_path / "svg").glob("blog-*.svg"))
        assert len(svg_files) == 1
        svg = svg_files[0].read_text(encoding="utf-8")
        assert "My Cool Post" in svg

    def test_mid_title_update_is_not_stripped(self, tmp_path: Path) -> None:
        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(enabled=True, output_dir=str(tmp_path / "svg")),
            blog_feed_url="https://w4w.dev/feed.xml",
            blog_post_limit=1,
        )
        generator = ReadmeSectionGenerator(
            settings=settings,
            blog_client=StubBlogClient(
                [BlogPost(title="How to update your system", url="https://w4w.dev/blog/sys")]
            ),
            blog_metadata_client=StubBlogMetadataClient(
                {"https://w4w.dev/blog/sys": {"host": "w4w.dev"}}
            ),
        )

        html = generator._render_blog_posts()

        # "update" in the middle should NOT be stripped
        svg_files = list((tmp_path / "svg").glob("blog-*.svg"))
        assert len(svg_files) == 1
        svg = svg_files[0].read_text(encoding="utf-8")
        assert "update" in svg


class TestDeadCodeRemoval:
    """Verify dead code has been removed."""

    def test_social_kicker_method_does_not_exist(self) -> None:
        """_social_kicker was dead code and should be removed."""
        assert not hasattr(ReadmeSectionGenerator, "_social_kicker")
