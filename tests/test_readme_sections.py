"""Tests for README dynamic section generation."""

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

        assert "<svg" in html
        assert "❈" not in html
        assert "https://w4w.dev" in html
        assert "https://linkedin.com/in/wyattowalsh" in html
        assert ".github/assets/img/gh.gif" in html
        assert (tmp_path / "svg" / "top-contact.svg").exists()

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

    def test_featured_projects_render_svg_cards_with_sparkline(self, tmp_path: Path) -> None:
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

        assert "<svg" in html
        assert "Composable scaffolding framework" in html
        assert "★ 42" in html
        assert "sparkline" in html
        assert (tmp_path / "svg" / "featured-projects.svg").exists()

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

        html = generator._render_blog_posts()

        assert "<svg" in html
        assert "First Post" in html
        assert "w4w.dev" in html
        assert "Auto-updated from" in html
        assert "https://w4w.dev/feed.xml" in html
        assert (tmp_path / "svg" / "blog-posts.svg").exists()


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
        assert "<svg" in content
        assert "First Post" in content
        assert 'href="https://w4w.dev/blog/first"' in content
        assert "Auto-updated from" in content
        assert "<!-- BLOG-POST-LIST:START -->" in content
        assert "<!-- BLOG-POST-LIST:END -->" in content
        assert "before" in content
        assert "after" in content

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

        assert not (svg_dir / "top-contact.svg").exists()
        assert (svg_dir / "featured-projects.svg").exists()
        assert not (svg_dir / "blog-posts.svg").exists()
