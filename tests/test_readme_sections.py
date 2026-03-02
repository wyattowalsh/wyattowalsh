"""Tests for README dynamic section generation."""

from typing import Optional
from pathlib import Path

from scripts.config import (
    ReadmeFeaturedRepo,
    ReadmeSectionsSettings,
    ReadmeSocialLink,
)
from scripts.readme_sections import BlogPost, ReadmeSectionGenerator, RepoMetadata


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


class TestRendering:
    def test_top_badges_include_ornate_separator(self) -> None:
        settings = ReadmeSectionsSettings(
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

        assert "✦" in html
        assert html.count("❈ ┈┈ ✦ ┈┈ ❈") == 2
        assert "https://w4w.dev" in html
        assert "https://linkedin.com/in/wyattowalsh" in html

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

    def test_featured_projects_use_api_metadata(self) -> None:
        settings = ReadmeSectionsSettings(
            featured_repos=[ReadmeFeaturedRepo(full_name="wyattowalsh/riso")]
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

        html = generator._render_featured_projects()

        assert "Composable scaffolding framework" in html
        assert "★ 42" in html
        assert "https://riso.dev" in html
        assert "python" in html

    def test_blog_posts_render_as_rich_rows(self) -> None:
        settings = ReadmeSectionsSettings(
            blog_feed_url="https://w4w.dev/feed.xml",
            blog_post_limit=2,
        )
        generator = ReadmeSectionGenerator(
            settings=settings,
            blog_client=StubBlogClient(
                [BlogPost(title="First Post", url="https://w4w.dev/blog/first")]
            ),
        )

        html = generator._render_blog_posts()

        assert "<table role=\"presentation\">" in html
        assert "<strong>First Post</strong>" in html
        assert "Auto-updated from" in html
        assert "https://w4w.dev/feed.xml" in html


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
        )

        generator.generate()

        content = readme_path.read_text(encoding="utf-8")
        assert "old top" not in content
        assert "old projects" not in content
        assert "old posts" not in content
        assert "Composable scaffolding framework" in content
        assert "<strong>First Post</strong>" in content
        assert 'href="https://w4w.dev/blog/first"' in content
        assert "Auto-updated from" in content
        assert "<!-- BLOG-POST-LIST:START -->" in content
        assert "<!-- BLOG-POST-LIST:END -->" in content
        assert "before" in content
        assert "after" in content
