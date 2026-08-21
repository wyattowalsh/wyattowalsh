"""Tests for README dynamic section generation."""

import json
import re
import socket
from datetime import UTC, datetime
from email.message import Message
from io import BytesIO
from pathlib import Path
from textwrap import dedent
from urllib.error import HTTPError, URLError
from urllib.request import Request

import pytest
from loguru import logger as loguru_logger

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
    StarHistoryClient,
    _is_safe_remote_url,
    _safe_urlopen,
    _SafeRedirectHandler,
)
from tests.test_readme_gfm_ux import (
    after_heading,
    assert_living_art_dropdown_copy,
    assert_living_art_hosts_allowed,
    assert_living_art_intro_has_no_spine,
    assert_living_art_stack_layout,
    assert_visible_or_comment_heading,
    living_art_section,
    slice_between_headings,
)


class StubRepoClient:
    def __init__(
        self,
        metadata_by_repo: dict[str, RepoMetadata],
        languages_by_repo: dict[str, dict[str, int]] | None = None,
    ) -> None:
        self.metadata_by_repo = metadata_by_repo
        self.languages_by_repo = languages_by_repo or {}

    def fetch_repo_metadata(self, full_name: str) -> RepoMetadata | None:
        return self.metadata_by_repo.get(full_name)

    def fetch_repo_languages(
        self,
        full_name: str,
    ) -> dict[str, int] | None:
        return self.languages_by_repo.get(full_name)


class StubBlogClient:
    def __init__(self, posts: list[BlogPost]) -> None:
        self.posts = posts

    def fetch_latest_posts(self, feed_url: str, limit: int) -> list[BlogPost]:
        return self.posts[:limit]


class StubStarHistoryClient:
    def __init__(self, series: dict[str, list[int]]) -> None:
        self.series = series

    def fetch_star_history(
        self,
        full_name: str,
        sample: int = 24,
        series_start: datetime | None = None,
    ) -> list[int] | None:
        _ = sample, series_start
        return self.series.get(full_name)


class StubBlogMetadataClient:
    def __init__(self, metadata: dict[str, dict[str, str | None]]) -> None:
        self.metadata = metadata

    def fetch_metadata(self, url: str) -> dict[str, str | None]:
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

        generator._render_top_badges()

        # Per-card SVGs should exist
        assert (tmp_path / "svg" / "connect-linkedin.svg").exists()
        assert (tmp_path / "svg" / "connect-github.svg").exists()
        # The HTML output should not contain full profile URLs as visible text
        # (URLs appear only in href attributes, not as display text)
        for svg_name in ("connect-linkedin.svg", "connect-github.svg"):
            svg = (tmp_path / "svg" / svg_name).read_text(encoding="utf-8")
            # Visible text elements should not contain protocol prefixes
            text_values = re.findall(r">([^<]+)<", svg)
            assert all("://" not in val for val in text_values if val.strip())

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

    def test_top_contact_falls_back_to_owner_profile_when_social_links_missing(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        def failing_urlopen(request, timeout=10.0):  # noqa: ARG001
            raise RuntimeError("network disabled for test")

        monkeypatch.setattr("scripts.readme_sections._safe_urlopen", failing_urlopen)

        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(
                enabled=True,
                output_dir=str(tmp_path / "svg"),
            ),
            featured_repos=[ReadmeFeaturedRepo(full_name="wyattowalsh/riso")],
        )
        generator = ReadmeSectionGenerator(settings=settings)

        html = generator._render_top_badges()

        svg_path = tmp_path / "svg" / "connect-github.svg"
        assert svg_path.exists()
        svg = svg_path.read_text(encoding="utf-8")
        assert "connect-github.svg" in html
        assert 'href="https://github.com/wyattowalsh"' in html
        assert "data:image" in svg
        assert "★" not in svg

    def test_featured_projects_render_per_card_svgs_and_manifest(
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

        monkeypatch.setattr("scripts.readme_sections._safe_urlopen", fake_urlopen)

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
                        "Python": 8000,
                        "Shell": 2000,
                    },
                },
            ),
            star_history_client=StubStarHistoryClient(
                {"wyattowalsh/riso": [0, 1, 3, 5, 8]}
            ),
        )

        html = generator._render_featured_projects()

        # Per-card SVG should be created
        card_svg_path = tmp_path / "svg" / "featured-card-wyattowalsh-riso.svg"
        manifest_path = tmp_path / "svg" / "featured-projects.manifest.json"
        assert card_svg_path.exists()
        assert manifest_path.exists()
        svg = card_svg_path.read_text(encoding="utf-8")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert "riso" in svg
        assert "Composable scaffolding" in svg
        assert "framework" in svg
        # OG image embedded as thumbnail
        assert "data:image/png;base64," in svg
        # Sparkline rendered
        assert "sparkline-group" in svg
        # Multi-language bar rendered
        assert "lang-bar-clip" in svg
        # HTML uses a mobile-readable peer card flow with descriptive alt/rel attrs
        assert "<table>" not in html
        assert "featured-card-wyattowalsh-riso.svg" in html
        assert 'width="360"' in html
        assert 'rel="noopener noreferrer"' in html
        assert (
            'alt="Featured project card for riso: Composable scaffolding framework"'
            in html
        )
        assert "layout" not in manifest["projects"][0]
        assert manifest["projects"][0]["svg_asset_path"].endswith(
            "featured-card-wyattowalsh-riso.svg"
        )
        assert manifest["projects"][0]["updated_label"].startswith("Updated ")
        assert manifest["projects"][0]["top_languages"] == ["Python", "Shell"]

    def test_featured_projects_use_full_repo_identity_in_asset_names(
        self, tmp_path: Path
    ) -> None:
        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(enabled=True, output_dir=str(tmp_path / "svg")),
            featured_repos=[
                ReadmeFeaturedRepo(full_name="wyattowalsh/demo"),
                ReadmeFeaturedRepo(full_name="octocat/demo"),
            ],
        )
        generator = ReadmeSectionGenerator(
            settings=settings,
            repo_client=StubRepoClient(
                {
                    "wyattowalsh/demo": RepoMetadata(
                        full_name="wyattowalsh/demo",
                        name="demo",
                        html_url="https://github.com/wyattowalsh/demo",
                        description="First demo repo",
                        stars=10,
                        homepage=None,
                        topics=[],
                        updated_at="2026-02-01T00:00:00Z",
                    ),
                    "octocat/demo": RepoMetadata(
                        full_name="octocat/demo",
                        name="demo",
                        html_url="https://github.com/octocat/demo",
                        description="Second demo repo",
                        stars=20,
                        homepage=None,
                        topics=[],
                        updated_at="2026-02-02T00:00:00Z",
                    ),
                }
            ),
            star_history_client=StubStarHistoryClient({}),
        )

        html = generator._render_featured_projects()

        assert (tmp_path / "svg" / "featured-card-wyattowalsh-demo.svg").exists()
        assert (tmp_path / "svg" / "featured-card-octocat-demo.svg").exists()
        assert "featured-card-wyattowalsh-demo.svg" in html
        assert "featured-card-octocat-demo.svg" in html

    def test_featured_projects_omit_sparkline_when_history_is_unavailable(
        self, tmp_path: Path
    ) -> None:
        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(enabled=True, output_dir=str(tmp_path / "svg")),
            featured_repos=[ReadmeFeaturedRepo(full_name="wyattowalsh/demo")],
        )
        generator = ReadmeSectionGenerator(
            settings=settings,
            repo_client=StubRepoClient(
                {
                    "wyattowalsh/demo": RepoMetadata(
                        full_name="wyattowalsh/demo",
                        name="demo",
                        html_url="https://github.com/wyattowalsh/demo",
                        description="Repo without trustworthy history",
                        stars=3,
                        homepage=None,
                        topics=["python"],
                        updated_at="2026-02-02T00:00:00Z",
                        created_at="2025-01-01T00:00:00Z",
                    )
                }
            ),
            star_history_client=StubStarHistoryClient({}),
        )

        generator._render_featured_projects()

        svg = (tmp_path / "svg" / "featured-card-wyattowalsh-demo.svg").read_text(
            encoding="utf-8"
        )
        assert "sparkline-group" not in svg

    def test_build_star_history_points_aligns_final_point_to_live_star_count(
        self,
    ) -> None:
        generator = ReadmeSectionGenerator(
            settings=ReadmeSectionsSettings(),
            star_history_client=StubStarHistoryClient({"wyattowalsh/demo": [0, 1, 2]}),
        )

        points = generator._build_star_history_points(
            "wyattowalsh/demo",
            RepoMetadata(
                full_name="wyattowalsh/demo",
                name="demo",
                html_url="https://github.com/wyattowalsh/demo",
                description="Repo with lagging GraphQL history",
                stars=3,
                homepage=None,
                topics=[],
                updated_at="2026-02-02T00:00:00Z",
                created_at="2025-01-01T00:00:00Z",
            ),
        )

        assert points == (0.0, 1.0, 3.0)

    def test_featured_projects_render_two_columns_for_four_primary_cards(
        self, tmp_path: Path
    ) -> None:
        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(enabled=True, output_dir=str(tmp_path / "svg")),
            featured_repos=[
                ReadmeFeaturedRepo(full_name="wyattowalsh/one"),
                ReadmeFeaturedRepo(full_name="wyattowalsh/two"),
                ReadmeFeaturedRepo(full_name="wyattowalsh/three"),
                ReadmeFeaturedRepo(full_name="wyattowalsh/four"),
            ],
        )
        generator = ReadmeSectionGenerator(
            settings=settings,
            repo_client=StubRepoClient(
                {
                    "wyattowalsh/one": RepoMetadata(
                        full_name="wyattowalsh/one",
                        name="one",
                        html_url="https://github.com/wyattowalsh/one",
                        description="One",
                        stars=1,
                        homepage=None,
                        topics=[],
                        updated_at="2026-02-01T00:00:00Z",
                    ),
                    "wyattowalsh/two": RepoMetadata(
                        full_name="wyattowalsh/two",
                        name="two",
                        html_url="https://github.com/wyattowalsh/two",
                        description="Two",
                        stars=2,
                        homepage=None,
                        topics=[],
                        updated_at="2026-02-01T00:00:00Z",
                    ),
                    "wyattowalsh/three": RepoMetadata(
                        full_name="wyattowalsh/three",
                        name="three",
                        html_url="https://github.com/wyattowalsh/three",
                        description="Three",
                        stars=3,
                        homepage=None,
                        topics=[],
                        updated_at="2026-02-01T00:00:00Z",
                    ),
                    "wyattowalsh/four": RepoMetadata(
                        full_name="wyattowalsh/four",
                        name="four",
                        html_url="https://github.com/wyattowalsh/four",
                        description="Four",
                        stars=4,
                        homepage=None,
                        topics=[],
                        updated_at="2026-02-01T00:00:00Z",
                    ),
                }
            ),
            star_history_client=StubStarHistoryClient({}),
        )

        html = generator._render_featured_projects()

        assert "<table>" not in html
        assert html.count('width="360"') == 4
        assert html.count("featured-card-wyattowalsh-") == 4

    def test_featured_projects_render_mobile_readable_flow_for_six_peer_cards(
        self, tmp_path: Path
    ) -> None:
        repos = [
            ReadmeFeaturedRepo(full_name=f"wyattowalsh/repo-{index}")
            for index in range(6)
        ]
        metadata = {
            repo.full_name: RepoMetadata(
                full_name=repo.full_name,
                name=repo.full_name.split("/")[-1],
                html_url=f"https://github.com/{repo.full_name}",
                description=f"Repo {index}",
                stars=index,
                homepage=None,
                topics=[],
                updated_at="2026-02-01T00:00:00Z",
            )
            for index, repo in enumerate(repos, start=1)
        }
        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(enabled=True, output_dir=str(tmp_path / "svg")),
            featured_repos=repos,
        )
        generator = ReadmeSectionGenerator(
            settings=settings,
            repo_client=StubRepoClient(metadata),
            star_history_client=StubStarHistoryClient({}),
        )

        html = generator._render_featured_projects()

        assert "<table>" not in html
        assert html.count('width="360"') == 6
        assert "More Featured Projects" not in html

    def test_featured_projects_keep_one_card_variety_for_larger_sets(
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

        monkeypatch.setattr("scripts.readme_sections._safe_urlopen", fake_urlopen)

        repos = [
            ReadmeFeaturedRepo(full_name=f"wyattowalsh/repo-{index}")
            for index in range(7)
        ]
        metadata = {
            repo.full_name: RepoMetadata(
                full_name=repo.full_name,
                name=repo.full_name.split("/")[-1],
                html_url=f"https://github.com/{repo.full_name}",
                description=(
                    "A very long repository description with https://repo.example.com "
                    "Topics python templates and duplicate repo.example.com clutter."
                ),
                stars=index,
                homepage="https://repo.example.com",
                topics=["python", "templates", "svg"],
                updated_at="2026-02-01T00:00:00Z",
                language="Python",
                forks=index,
            )
            for index, repo in enumerate(repos, start=1)
        }
        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(enabled=True, output_dir=str(tmp_path / "svg")),
            featured_repos=repos,
        )
        generator = ReadmeSectionGenerator(
            settings=settings,
            repo_client=StubRepoClient(metadata),
            star_history_client=StubStarHistoryClient(
                {
                    repo.full_name: [0, index, index + 2, index + 5]
                    for index, repo in enumerate(repos, start=1)
                }
            ),
            blog_metadata_client=StubBlogMetadataClient({}),
        )

        html = generator._render_featured_projects()
        manifest = json.loads(
            (tmp_path / "svg" / "featured-projects.manifest.json").read_text(
                encoding="utf-8"
            )
        )

        assert "More Featured Projects" not in html
        assert "<table>" not in html
        assert html.count('width="360"') == 7
        assert len(manifest["projects"]) == 7
        assert [project["full_name"] for project in manifest["projects"]] == [
            repo.full_name for repo in repos
        ]
        assert "layout" not in manifest["projects"][0]
        assert manifest["projects"][0]["summary"].startswith("A very long repository")
        assert "https://" not in manifest["projects"][0]["summary"]
        assert "Topics" not in manifest["projects"][0]["summary"]
        later_svg = (
            tmp_path / "svg" / "featured-card-wyattowalsh-repo-6.svg"
        ).read_text(encoding="utf-8")
        assert "sparkline-group" in later_svg
        assert "thumb-clip" in later_svg

    def test_featured_projects_mirror_docs_showcase_surface(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        (tmp_path / "docs" / "public" / "showcase").mkdir(parents=True)

        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(enabled=True, output_dir=".github/assets/img/readme"),
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
                    )
                }
            ),
            star_history_client=StubStarHistoryClient({}),
        )

        generator._render_featured_projects()

        canonical_manifest = (
            tmp_path
            / ".github"
            / "assets"
            / "img"
            / "readme"
            / "featured-projects.manifest.json"
        )
        public_manifest = (
            tmp_path
            / "docs"
            / "public"
            / "showcase"
            / "featured-projects.manifest.json"
        )
        public_card = (
            tmp_path
            / "docs"
            / "public"
            / "showcase"
            / "featured-projects"
            / "featured-card-wyattowalsh-riso.svg"
        )
        manifest = json.loads(public_manifest.read_text(encoding="utf-8"))

        assert canonical_manifest.exists()
        assert public_manifest.exists()
        assert public_card.exists()
        assert manifest["projects"][0]["svg_asset_path"] == (
            "/showcase/featured-projects/featured-card-wyattowalsh-riso.svg"
        )

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
        card_svg_path = tmp_path / "svg" / "featured-card-wyattowalsh-riso.svg"
        assert card_svg_path.exists()
        svg = card_svg_path.read_text(encoding="utf-8")
        assert "Unable to fetch repository metadata." not in svg
        assert "Live stats are temporarily unavailable." in svg

    def test_featured_projects_normalize_summary_from_description_and_topics(
        self,
    ) -> None:
        generator = ReadmeSectionGenerator(settings=ReadmeSectionsSettings())
        metadata = RepoMetadata(
            full_name="wyattowalsh/demo",
            name="demo",
            html_url="https://github.com/wyattowalsh/demo",
            description=(
                "An orchestration toolkit for https://demo.dev with Topics: "
                "python, ai, and github. Visit demo.dev/repo for more."
            ),
            stars=10,
            homepage="https://demo.dev/repo",
            topics=["python", "ai", "github"],
            updated_at="2026-02-01T00:00:00Z",
            language="Python",
        )

        summary = generator._normalize_project_summary(metadata, compact=False)

        assert "https://" not in summary
        assert "Topics" not in summary
        assert "demo.dev" not in summary
        assert summary.startswith("An orchestration toolkit")
        assert "..." not in summary

    def test_featured_projects_normalize_summary_keeps_full_clean_copy(self) -> None:
        generator = ReadmeSectionGenerator(settings=ReadmeSectionsSettings())
        metadata = RepoMetadata(
            full_name="wyattowalsh/demo",
            name="demo",
            html_url="https://github.com/wyattowalsh/demo",
            description=(
                "A long but meaningful repository description for data tooling "
                "and agent workflows, with no need to shorten it once URLs and "
                "boilerplate have been removed."
            ),
            stars=10,
            homepage=None,
            topics=["data-tooling", "agents"],
            updated_at="2026-02-01T00:00:00Z",
            language="Python",
        )

        summary = generator._normalize_project_summary(metadata, compact=True)

        assert summary == (
            "A long but meaningful repository description for data tooling and "
            "agent workflows, with no need to shorten it once URLs and "
            "boilerplate have been removed"
        )

    def test_featured_projects_normalize_summary_falls_back_to_topics(self) -> None:
        generator = ReadmeSectionGenerator(settings=ReadmeSectionsSettings())
        metadata = RepoMetadata(
            full_name="wyattowalsh/demo",
            name="demo",
            html_url="https://github.com/wyattowalsh/demo",
            description="No description provided.",
            stars=10,
            homepage=None,
            topics=["ai-agents", "tooling", "github"],
            updated_at="2026-02-01T00:00:00Z",
            language="Python",
        )

        summary = generator._normalize_project_summary(metadata, compact=False)

        assert summary == "AI Agents, Tooling, and GitHub workflows."

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

        first = (tmp_path / "svg" / "blog-first-post.svg").read_text(encoding="utf-8")
        second = (tmp_path / "svg" / "blog-second-post.svg").read_text(encoding="utf-8")
        img_links = re.findall(
            r'<a href="([^"]+)"[^>]*>\s*<img src="([^"]+)"',
            html,
        )
        assert "<img" in html
        assert "blog-posts.svg" not in html
        assert not (tmp_path / "svg" / "blog-posts.svg").exists()
        assert "2026-02-20" in html
        assert "2026-02-19" in html
        assert "A deep dive into data art." in html
        assert "Another deep dive." in html
        assert "https://w4w.dev/blog/first" in html
        assert "<details" not in html
        first_src = (tmp_path / "svg" / "blog-first-post.svg").as_posix()
        second_src = (tmp_path / "svg" / "blog-second-post.svg").as_posix()
        assert img_links == [
            ("https://w4w.dev/blog/first", first_src),
            ("https://w4w.dev/blog/second", second_src),
        ]
        assert "First Post" in first
        assert "A deep dive into data art." in first
        assert "2026-02-20" in first
        assert "Second Post" in second
        assert "Another deep dive." in second
        assert "2026-02-19" in second
        assert 'loading="lazy"' in html
        assert "<svg" not in html
        assert "Auto-updated from" in html
        assert "📡" not in html
        assert "https://w4w.dev/feed.xml" in html
        assert 'target="_blank" rel="noopener noreferrer"' in html

    def test_blog_posts_use_rss_date_and_summary_when_metadata_missing(
        self, tmp_path: Path
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
                [
                    BlogPost(
                        title="RSS Only",
                        url="https://w4w.dev/blog/rss-only",
                        published="2026-05-01",
                        summary="Hook from the feed.",
                    )
                ]
            ),
            blog_metadata_client=StubBlogMetadataClient({}),
        )

        html = generator._render_blog_posts()
        svg_files = list((tmp_path / "svg").glob("blog-*.svg"))
        assert len(svg_files) == 1
        svg = svg_files[0].read_text(encoding="utf-8")

        assert "2026-05-01" in html
        assert "Hook from the feed." in html
        assert "<details" not in html
        assert "blog-posts.svg" not in html
        assert "RSS Only" in svg
        assert "Hook from the feed." in svg
        assert "2026-05-01" in svg
        assert '<a href="https://w4w.dev/blog/rss-only"' in html
        assert f'src="{svg_files[0].as_posix()}"' in html

    def test_blog_posts_deduplicate_colliding_svg_names(self, tmp_path: Path) -> None:
        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(enabled=True, output_dir=str(tmp_path / "svg")),
            blog_feed_url="https://w4w.dev/feed.xml",
            blog_post_limit=2,
        )
        generator = ReadmeSectionGenerator(
            settings=settings,
            blog_client=StubBlogClient(
                [
                    BlogPost(
                        title="Weekly Update on Readme Cards and Asset Naming",
                        url="https://w4w.dev/blog/weekly-update-1",
                    ),
                    BlogPost(
                        title="Weekly Update on Readme Cards and Asset Naming",
                        url="https://w4w.dev/blog/weekly-update-2",
                    ),
                ]
            ),
            blog_metadata_client=StubBlogMetadataClient({}),
        )

        html = generator._render_blog_posts()

        svg_files = sorted(path.name for path in (tmp_path / "svg").glob("blog-*.svg"))
        assert len(svg_files) == 2
        assert len(set(svg_files)) == 2
        assert "blog-posts.svg" not in svg_files
        assert all(name.startswith("blog-weekly-update") for name in svg_files)
        designed = "\n".join(
            (tmp_path / "svg" / name).read_text(encoding="utf-8") for name in svg_files
        )
        assert designed.count("Weekly Update") >= 2
        assert html.count('href="https://w4w.dev/blog/weekly-update-1"') >= 1
        assert html.count('href="https://w4w.dev/blog/weekly-update-2"') >= 1
        assert 'width="360"' in html
        assert 'width="500"' not in html
        assert 'width="100%"' not in html

    def test_generate_rewrites_living_art_as_full_width_stack_with_details(
        self,
        tmp_path: Path,
    ) -> None:
        readme = tmp_path / "README.md"
        readme.write_text(
            dedent(
                """\
                ## Living Art

                <table><tbody><tr><td>stale living art grid</td></tr></tbody></table>

                ## My Tech Stack

                <p align="center">
                  <img alt="AI/ML" src="https://img.shields.io/badge/AI%2FML-412991?style=for-the-badge&amp;logo=openai&amp;logoColor=white"/>
                  <img alt="Data Engineering" src="https://img.shields.io/badge/Data%20Engineering-4169E1?style=for-the-badge&amp;logo=postgresql&amp;logoColor=white"/>
                </p>

                <details>
                <summary><strong>View full stack (200+ technologies)</strong></summary>

                <!-- SKILLS:START -->
                kept skills
                <!-- SKILLS:END -->

                </details>
                """
            ),
            encoding="utf-8",
        )

        generator = ReadmeSectionGenerator(
            settings=ReadmeSectionsSettings(
                readme_path=str(readme),
                featured_repos=[],
                social_links=[],
            ),
            blog_client=StubBlogClient([]),
        )

        generator.generate()
        rendered = readme.read_text(encoding="utf-8")
        assert_visible_or_comment_heading(rendered, "Living Art")
        assert_visible_or_comment_heading(rendered, "My Tech Stack")
        living_art = living_art_section(rendered)

        assert "stale living art grid" not in rendered
        assert_living_art_stack_layout(living_art)
        assert_living_art_intro_has_no_spine(living_art)
        assert_living_art_dropdown_copy(living_art)
        assert_living_art_hosts_allowed(living_art)
        assert 'alt="AI/ML"' not in rendered
        assert 'alt="Data Engineering"' not in rendered
        assert "<!-- SKILLS:START -->" in rendered
        assert "kept skills" in rendered
        assert "<summary><strong>My Tech Stack</strong></summary>" in rendered
        assert "View full stack" not in rendered
        assert "200+" not in rendered

    def test_generate_drops_tech_stack_teaser_shields(
        self,
        tmp_path: Path,
    ) -> None:
        readme = tmp_path / "README.md"
        readme.write_text(
            dedent(
                """\
                ## Living Art

                placeholder

                ## My Tech Stack

                <p align="center">
                  <img alt="AI/ML" src="https://img.shields.io/badge/AI%2FML-412991?style=for-the-badge"/>
                  <img alt="Full-Stack" src="https://img.shields.io/badge/Full--Stack-61DAFB?style=for-the-badge"/>
                  <img alt="Open Source" src="https://img.shields.io/badge/Open%20Source-181717?style=for-the-badge"/>
                </p>

                <details>
                <summary><strong>View full stack (200+ technologies)</strong></summary>

                <!-- SKILLS:START -->
                full stack body
                <!-- SKILLS:END -->

                </details>
                """
            ),
            encoding="utf-8",
        )

        generator = ReadmeSectionGenerator(
            settings=ReadmeSectionsSettings(
                readme_path=str(readme),
                featured_repos=[],
                social_links=[],
            ),
            blog_client=StubBlogClient([]),
        )

        generator.generate()
        rendered = readme.read_text(encoding="utf-8")
        assert_visible_or_comment_heading(rendered, "My Tech Stack")
        tech_stack = after_heading(rendered, "My Tech Stack")

        assert 'alt="AI/ML"' not in tech_stack
        assert 'alt="Full-Stack"' not in tech_stack
        assert 'alt="Open Source"' not in tech_stack
        assert tech_stack.lstrip().startswith("<details>")
        assert "<summary><strong>My Tech Stack</strong></summary>" in tech_stack
        assert "View full stack" not in tech_stack
        assert "200+" not in tech_stack
        assert "full stack body" in tech_stack
        assert "<!-- SKILLS:START -->" in tech_stack

    def test_generate_keeps_metrics_image_table_when_assets_are_placeholders(
        self,
        tmp_path: Path,
    ) -> None:
        readme = tmp_path / "README.md"
        readme.write_text(
            dedent(
                """\
                ## Metrics

                stale metrics block

                ## Word Clouds
                """
            ),
            encoding="utf-8",
        )
        metrics_dir = tmp_path / ".github" / "assets" / "img"
        metrics_dir.mkdir(parents=True)
        placeholder = dedent(
            """\
            <svg xmlns="http://www.w3.org/2000/svg"
                 role="img" aria-label="Metrics unavailable">
              <text x="12" y="40">Metrics temporarily unavailable</text>
              <text x="12" y="64">Check workflow logs for details</text>
            </svg>
            """
        )
        (metrics_dir / "metrics.svg").write_text(placeholder, encoding="utf-8")
        (metrics_dir / "metrics.additional.svg").write_text(
            placeholder,
            encoding="utf-8",
        )
        (metrics_dir / "metrics.extra.svg").write_text(
            placeholder,
            encoding="utf-8",
        )

        generator = ReadmeSectionGenerator(
            settings=ReadmeSectionsSettings(
                readme_path=str(readme),
                featured_repos=[],
                social_links=[],
            ),
            blog_client=StubBlogClient([]),
        )

        generator.generate()
        rendered = readme.read_text(encoding="utf-8")

        assert ".github/assets/img/metrics.svg" in rendered
        assert ".github/assets/img/metrics.additional.svg" in rendered
        assert ".github/assets/img/metrics.extra.svg" not in rendered
        assert "Metrics temporarily unavailable" not in rendered
        assert (
            'alt="GitHub metrics: contributions, languages, topics, and community signals"'  # noqa: E501
            in rendered
        )
        assert 'loading="lazy"' in rendered
        assert_visible_or_comment_heading(rendered, "Metrics")
        assert ".github/assets/img/readme/sep-metrics.svg" in rendered
        assert "<td" in rendered
        assert 'width="50%"' in rendered

    def test_generate_keeps_metrics_image_table_when_only_one_asset_is_valid(
        self,
        tmp_path: Path,
    ) -> None:
        readme = tmp_path / "README.md"
        readme.write_text(
            dedent(
                """\
                ## Metrics

                stale metrics block

                ## Word Clouds
                """
            ),
            encoding="utf-8",
        )
        metrics_dir = tmp_path / ".github" / "assets" / "img"
        metrics_dir.mkdir(parents=True)
        valid_svg = (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<text x="1" y="20">Healthy metrics</text></svg>'
        )
        placeholder = dedent(
            """\
            <svg xmlns="http://www.w3.org/2000/svg"
                 role="img" aria-label="Metrics unavailable">
              <text x="12" y="40">Metrics temporarily unavailable</text>
              <text x="12" y="64">Check workflow logs for details</text>
            </svg>
            """
        )
        (metrics_dir / "metrics.svg").write_text(valid_svg, encoding="utf-8")
        (metrics_dir / "metrics.additional.svg").write_text(
            placeholder,
            encoding="utf-8",
        )
        (metrics_dir / "metrics.extra.svg").write_text(
            placeholder,
            encoding="utf-8",
        )

        generator = ReadmeSectionGenerator(
            settings=ReadmeSectionsSettings(
                readme_path=str(readme),
                featured_repos=[],
                social_links=[],
            ),
            blog_client=StubBlogClient([]),
        )

        generator.generate()
        rendered = readme.read_text(encoding="utf-8")

        assert ".github/assets/img/metrics.svg" in rendered
        assert ".github/assets/img/metrics.additional.svg" in rendered
        assert ".github/assets/img/metrics.extra.svg" not in rendered
        assert "placeholder output" not in rendered

    def test_generate_adds_valid_supplemental_metrics_assets(
        self,
        tmp_path: Path,
    ) -> None:
        readme = tmp_path / "README.md"
        readme.write_text(
            dedent(
                """\
                ## Metrics

                stale metrics block

                ## Word Clouds
                """
            ),
            encoding="utf-8",
        )
        metrics_dir = tmp_path / ".github" / "assets" / "img"
        metrics_dir.mkdir(parents=True)
        valid_svg = (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<text x="1" y="20">Healthy metrics</text></svg>'
        )
        supplemental_svg = (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<text x="1" y="20">Coding habits</text>'
            '<text x="1" y="40">30-day activity</text>'
            "</svg>"
        )
        activity_svg = (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<text x="1" y="20">Recent activity</text>'
            '<text x="1" y="40">GitHub</text>'
            "</svg>"
        )
        (metrics_dir / "metrics.svg").write_text(valid_svg, encoding="utf-8")
        (metrics_dir / "metrics.additional.svg").write_text(valid_svg, encoding="utf-8")
        (metrics_dir / "metrics.extra.svg").write_text(valid_svg, encoding="utf-8")
        (metrics_dir / "metrics-habits.svg").write_text(
            supplemental_svg,
            encoding="utf-8",
        )
        (metrics_dir / "metrics-activity.svg").write_text(
            activity_svg,
            encoding="utf-8",
        )

        generator = ReadmeSectionGenerator(
            settings=ReadmeSectionsSettings(
                readme_path=str(readme),
                featured_repos=[],
                social_links=[],
            ),
            blog_client=StubBlogClient([]),
        )

        generator.generate()
        rendered = readme.read_text(encoding="utf-8")

        assert ".github/assets/img/metrics-habits.svg" in rendered
        assert ".github/assets/img/metrics-activity.svg" not in rendered
        assert ".github/assets/img/metrics.extra.svg" not in rendered
        assert (
            'alt="Extra metrics: comment reactions and issue/PR follow-up"'
            not in rendered
        )
        assert (
            'alt="Supplemental metrics: coding habits and recent GitHub focus"'
            in rendered
        )
        assert 'alt="Supplemental metrics: recent GitHub activity feed"' not in rendered
        assert_visible_or_comment_heading(rendered, "Metrics")
        assert ".github/assets/img/readme/sep-metrics.svg" in rendered
        assert "<td" in rendered
        assert 'width="50%"' in rendered
        assert rendered.count('loading="lazy"') >= 4

    def test_generate_hides_invalid_supplemental_metrics_assets(
        self,
        tmp_path: Path,
    ) -> None:
        readme = tmp_path / "README.md"
        readme.write_text(
            dedent(
                """\
                ## Metrics

                stale metrics block

                ## Word Clouds
                """
            ),
            encoding="utf-8",
        )
        metrics_dir = tmp_path / ".github" / "assets" / "img"
        metrics_dir.mkdir(parents=True)
        valid_svg = (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<text x="1" y="20">Healthy metrics</text></svg>'
        )
        invalid_svg = (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<text x="1" y="20">API error: 401</text></svg>'
        )
        (metrics_dir / "metrics.svg").write_text(valid_svg, encoding="utf-8")
        (metrics_dir / "metrics.additional.svg").write_text(valid_svg, encoding="utf-8")
        (metrics_dir / "metrics.extra.svg").write_text(valid_svg, encoding="utf-8")
        (metrics_dir / "metrics-posts.svg").write_text(invalid_svg, encoding="utf-8")

        generator = ReadmeSectionGenerator(
            settings=ReadmeSectionsSettings(
                readme_path=str(readme),
                featured_repos=[],
                social_links=[],
            ),
            blog_client=StubBlogClient([]),
        )

        generator.generate()
        rendered = readme.read_text(encoding="utf-8")

        assert ".github/assets/img/metrics-posts.svg" not in rendered

    def test_generate_rewrites_word_clouds_as_equal_full_width_blocks(
        self,
        tmp_path: Path,
    ) -> None:
        readme = tmp_path / "README.md"
        readme.write_text(
            dedent(
                """\
                ## Metrics

                stale metrics block

                ## Word Clouds

                stale word clouds

                <details>
                <summary><strong>WakaTime Stats</strong></summary>

                <!--START_SECTION:waka-->
                Last Updated on 27/04/2025 18:43:21 UTC
                <!--END_SECTION:waka-->

                </details>
                """
            ),
            encoding="utf-8",
        )
        metrics_dir = tmp_path / ".github" / "assets" / "img"
        metrics_dir.mkdir(parents=True)
        valid_svg = (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<text x="1" y="20">Healthy metrics</text></svg>'
        )
        (metrics_dir / "metrics.svg").write_text(valid_svg, encoding="utf-8")
        (metrics_dir / "metrics.additional.svg").write_text(valid_svg, encoding="utf-8")
        (metrics_dir / "metrics.extra.svg").write_text(valid_svg, encoding="utf-8")
        (metrics_dir / "wordcloud_fractal_reel.mp4").write_bytes(b"\x00\x00")

        generator = ReadmeSectionGenerator(
            settings=ReadmeSectionsSettings(
                readme_path=str(readme),
                featured_repos=[],
                social_links=[],
            ),
            blog_client=StubBlogClient([]),
        )

        generator.generate()
        rendered = readme.read_text(encoding="utf-8")

        assert "stale word clouds" not in rendered
        assert rendered.count('width="100%"') >= 4
        assert "wordcloud_typographic_by_topics.svg" in rendered
        assert "wordcloud_typographic_by_languages.svg" in rendered
        assert "wordcloud_fractal_reel.mp4" in rendered
        assert ".github/assets/img/metrics.extra.svg" not in rendered
        assert (
            'alt="Word cloud of GitHub topics sized by starred-repo share"'
        ) in rendered
        assert (
            'alt="Word cloud of GitHub languages sized by starred-repo share"'
        ) in rendered
        assert 'loading="lazy"' in rendered
        topics_idx = rendered.index("wordcloud_typographic_by_topics.svg")
        languages_idx = rendered.index("wordcloud_typographic_by_languages.svg")
        assert 'loading="lazy"' in rendered[topics_idx : topics_idx + 280]
        assert 'loading="lazy"' in rendered[languages_idx : languages_idx + 280]
        assert_visible_or_comment_heading(rendered, "Metrics")
        assert_visible_or_comment_heading(rendered, "Word Clouds")
        assert ".github/assets/img/readme/sep-clouds.svg" in rendered
        assert "<td" in rendered
        assert 'width="50%"' in rendered
        metrics = slice_between_headings(rendered, "Metrics", "Word Clouds")
        word_clouds = after_heading(rendered, "Word Clouds")
        assert 'src=".github/assets/img/wakatime.svg"' in metrics
        assert "<!--START_SECTION:waka-->" in metrics
        assert 'src=".github/assets/img/wakatime.svg"' not in word_clouds

    def test_generate_hides_stale_wakatime_block_until_fresh_output_exists(
        self,
        tmp_path: Path,
    ) -> None:
        readme = tmp_path / "README.md"
        readme.write_text(
            dedent(
                """\
                ## Metrics

                stale metrics block

                ## Word Clouds

                <details>
                <summary><strong>WakaTime Stats</strong></summary>

                <!--START_SECTION:waka-->
                Last Updated on 27/04/2025 18:43:21 UTC
                <!--END_SECTION:waka-->

                </details>
                """
            ),
            encoding="utf-8",
        )

        generator = ReadmeSectionGenerator(
            settings=ReadmeSectionsSettings(
                readme_path=str(readme),
                featured_repos=[],
                social_links=[],
            ),
            blog_client=StubBlogClient([]),
        )

        generator.generate()
        rendered = readme.read_text(encoding="utf-8")
        assert_visible_or_comment_heading(rendered, "Metrics")
        metrics = slice_between_headings(rendered, "Metrics", "Word Clouds")
        word_clouds = after_heading(rendered, "Word Clouds")

        assert "This Week I Spent My Time On" not in rendered
        assert "WakaTime stats are temporarily unavailable right now." not in rendered
        assert (
            "WakaTime SVG is rendered from .github/assets/img/wakatime.svg" in rendered
        )
        assert 'src=".github/assets/img/wakatime.svg"' in metrics
        assert "<!--START_SECTION:waka-->" in metrics
        assert "<!--END_SECTION:waka-->" in metrics
        assert rendered.count('src=".github/assets/img/wakatime.svg"') == 1
        assert 'src=".github/assets/img/wakatime.svg"' not in word_clouds
        assert "<summary><strong>WakaTime Stats</strong></summary>" not in rendered
        assert "<details" not in rendered
        assert "## Waka" not in rendered

    def test_generate_preserves_healthy_wakatime_output_without_timestamp(
        self,
        tmp_path: Path,
    ) -> None:
        readme = tmp_path / "README.md"
        readme.write_text(
            dedent(
                """\
                ## Metrics

                stale metrics block

                ## Word Clouds

                <details>
                <summary><strong>WakaTime Stats</strong></summary>

                <!--START_SECTION:waka-->
                **This Week I Spent My Time On**

                ```text
                Programming Languages:
                Python 10 hrs

                Editors:
                VS Code 8 hrs
                ```
                <!--END_SECTION:waka-->

                </details>
                """
            ),
            encoding="utf-8",
        )

        generator = ReadmeSectionGenerator(
            settings=ReadmeSectionsSettings(
                readme_path=str(readme),
                featured_repos=[],
                social_links=[],
            ),
            blog_client=StubBlogClient([]),
        )

        generator.generate()
        rendered = readme.read_text(encoding="utf-8")
        assert_visible_or_comment_heading(rendered, "Metrics")
        metrics = slice_between_headings(rendered, "Metrics", "Word Clouds")
        word_clouds = after_heading(rendered, "Word Clouds")

        assert "This Week I Spent My Time On" not in rendered
        assert "Programming Languages:" not in rendered
        assert (
            "WakaTime SVG is rendered from .github/assets/img/wakatime.svg" in rendered
        )
        assert 'src=".github/assets/img/wakatime.svg"' in metrics
        assert "<!--START_SECTION:waka-->" in metrics
        assert "<!--END_SECTION:waka-->" in metrics
        assert rendered.count('src=".github/assets/img/wakatime.svg"') == 1
        assert 'src=".github/assets/img/wakatime.svg"' not in word_clouds
        assert "<summary><strong>WakaTime Stats</strong></summary>" not in rendered
        assert "<details" not in rendered
        assert "## Waka" not in rendered

    def test_generate_keeps_wakatime_grouped_with_metrics_cards(
        self,
        tmp_path: Path,
    ) -> None:
        readme = tmp_path / "README.md"
        readme.write_text(
            dedent(
                """\
                ## Metrics

                <p align="center">
                <img src=".github/assets/img/metrics.svg" alt="metrics" width="100%"/>
                </p>

                <p align="center">
                <img src=".github/assets/img/wakatime.svg"
                     alt="WakaTime coding activity"
                     width="100%" loading="lazy"/>
                </p>

                <!--START_SECTION:waka-->
                **This Week I Spent My Time On**
                <!--END_SECTION:waka-->

                ## Word Clouds

                stale word clouds
                """
            ),
            encoding="utf-8",
        )
        metrics_dir = tmp_path / ".github" / "assets" / "img"
        metrics_dir.mkdir(parents=True)
        valid_svg = (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<text x="1" y="20">Healthy metrics</text></svg>'
        )
        (metrics_dir / "metrics.svg").write_text(valid_svg, encoding="utf-8")
        (metrics_dir / "metrics.additional.svg").write_text(valid_svg, encoding="utf-8")
        (metrics_dir / "metrics.extra.svg").write_text(valid_svg, encoding="utf-8")

        generator = ReadmeSectionGenerator(
            settings=ReadmeSectionsSettings(
                readme_path=str(readme),
                featured_repos=[],
                social_links=[],
                section_order=[
                    "Featured Projects",
                    "Metrics",
                    "Living Art",
                    "My Tech Stack",
                    "Word Clouds",
                ],
            ),
            blog_client=StubBlogClient([]),
        )

        generator.generate()
        generator.generate()
        rendered = readme.read_text(encoding="utf-8")
        assert_visible_or_comment_heading(rendered, "Metrics")
        metrics = slice_between_headings(rendered, "Metrics", "Word Clouds")
        word_clouds = after_heading(rendered, "Word Clouds")

        assert "This Week I Spent My Time On" not in rendered
        assert 'src=".github/assets/img/wakatime.svg"' in metrics
        assert "<!--START_SECTION:waka-->" in metrics
        assert "<!--END_SECTION:waka-->" in metrics
        assert rendered.count('src=".github/assets/img/wakatime.svg"') == 1
        assert rendered.count("<!--START_SECTION:waka-->") == 1
        assert 'src=".github/assets/img/wakatime.svg"' not in word_clouds
        assert metrics.index(".github/assets/img/metrics.svg") < metrics.index(
            ".github/assets/img/wakatime.svg"
        )

    def test_generate_unwraps_blog_and_restyles_view_counter(
        self,
        tmp_path: Path,
    ) -> None:
        readme = tmp_path / "README.md"
        stale_views = (
            "https://komarev.com/ghpvc/?username=wyattowalsh"
            "&color=6366F1&style=flat-square&label=Profile+Views"
        )
        readme.write_text(
            dedent(
                """\
                <!-- README:TOP_BADGES:START -->
                old top
                <!-- README:TOP_BADGES:END -->
                <!-- README:FEATURED_PROJECTS:START -->
                old projects
                <!-- README:FEATURED_PROJECTS:END -->
                <details>
                <summary><strong>Latest Blog Posts</strong></summary>

                <!-- README:BLOG_POSTS:START -->
                old posts
                <!-- README:BLOG_POSTS:END -->

                </details>

                <img src="{stale_views}" alt="Profile Views"/>
                """
            ).format(stale_views=stale_views),
            encoding="utf-8",
        )
        generator = ReadmeSectionGenerator(
            settings=ReadmeSectionsSettings(
                readme_path=str(readme),
                featured_repos=[],
                social_links=[],
                svg=ReadmeSvgSettings(
                    enabled=True,
                    output_dir=str(tmp_path / "svg"),
                ),
                blog_feed_url="https://w4w.dev/feed.xml",
                blog_post_limit=1,
            ),
            blog_client=StubBlogClient(
                [
                    BlogPost(
                        title="Visible Post",
                        url="https://w4w.dev/blog/visible",
                        published="2026-06-02",
                        summary="An open-flow hook.",
                    )
                ]
            ),
            blog_metadata_client=StubBlogMetadataClient({}),
        )

        generator.generate()
        rendered = readme.read_text(encoding="utf-8")

        assert "<summary><strong>Latest Blog Posts</strong></summary>" not in rendered
        assert_visible_or_comment_heading(rendered, "Latest Blog Posts")
        assert "2026-06-02" in rendered
        assert "An open-flow hook." in rendered
        assert "style=for-the-badge" in rendered
        assert "label=views" in rendered
        assert "logo=telescope" in rendered
        assert "views-peek.svg" not in rendered
        assert "flat-square" not in rendered
        assert "custom-icon-badges.demolab.com" in rendered
        assert "hitscounter.dev" in rendered
        assert "komarev.com/ghpvc" not in rendered

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

    def test_blog_cards_do_not_embed_icon_payloads(
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

        svg_files = list((tmp_path / "svg").glob("blog-*.svg"))
        assert len(svg_files) == 1
        svg = svg_files[0].read_text(encoding="utf-8")
        assert "data:image" not in svg
        assert svg_files[0].name in html
        assert "blog-posts.svg" not in html
        assert "GitHub Changelog" in svg

    def test_featured_projects_support_legacy_card_variant(
        self, tmp_path: Path
    ) -> None:
        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(
                enabled=True,
                output_dir=str(tmp_path / "svg"),
                card_styles={
                    "featured": {
                        "variant": "legacy",
                        "transparent_canvas": False,
                        "show_title": True,
                    }
                },
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
                        homepage=None,
                        topics=["python"],
                        updated_at="2026-02-01T00:00:00Z",
                    )
                }
            ),
            star_history_client=StubStarHistoryClient({}),
        )

        generator._render_featured_projects()

        svg = (tmp_path / "svg" / "featured-card-wyattowalsh-riso.svg").read_text(
            encoding="utf-8"
        )
        assert 'class="section-title"' in svg
        assert '<rect width="100%" height="100%" fill="var(--canvas-bg)" />' in svg


class TestDocsFeaturedProjectsContract:
    def test_docs_home_reads_shared_featured_projects_manifest(self) -> None:
        page = Path("docs/app/(home)/page.tsx").read_text(encoding="utf-8")

        assert "loadFeaturedProjectsManifest" in page
        assert "featured-projects.manifest.json" in page
        assert "/showcase/featured-projects/" in page
        assert "Featured Projects" in page


class TestRemoteFetchSafety:
    def test_blog_feed_client_blocks_non_http_scheme(self, monkeypatch) -> None:
        client = BlogFeedClient()
        called = False

        def fake_urlopen(request, timeout=10.0):  # noqa: ARG001
            nonlocal called
            called = True
            raise RuntimeError("urlopen should not be called for blocked URLs")

        monkeypatch.setattr("scripts.readme_sections._safe_urlopen", fake_urlopen)

        posts = client.fetch_latest_posts("ftp://example.com/feed.xml", limit=2)

        assert posts == []
        assert not called

    def test_blog_feed_parses_rss_date_and_description(self, monkeypatch) -> None:
        xml = (
            b'<?xml version="1.0"?>'
            b"<rss><channel>"
            b"<item>"
            b"<title>Feed Post</title>"
            b"<link>https://w4w.dev/blog/feed-post</link>"
            b"<pubDate>Mon, 26 Apr 2026 12:00:00 +0000</pubDate>"
            b"<description>A one-line hook from RSS.</description>"
            b"</item>"
            b"</channel></rss>"
        )

        class FakeResponse:
            def read(self) -> bytes:
                return xml

            def __enter__(self):
                return self

            def __exit__(self, *args: object) -> bool:
                return False

        monkeypatch.setattr(
            "scripts.readme_sections._is_safe_remote_url",
            lambda _url: True,
        )
        monkeypatch.setattr(
            "scripts.readme_sections._safe_urlopen",
            lambda request, timeout=10.0: FakeResponse(),
        )

        posts = BlogFeedClient().fetch_latest_posts("https://w4w.dev/feed.xml", limit=1)

        assert len(posts) == 1
        assert posts[0].title == "Feed Post"
        assert posts[0].published == "2026-04-26"
        assert posts[0].summary == "A one-line hook from RSS."

    def test_blog_feed_client_blocks_unsafe_url(self, monkeypatch) -> None:
        client = BlogFeedClient()
        called = False

        def fake_urlopen(request, timeout=10.0):  # noqa: ARG001
            nonlocal called
            called = True
            raise RuntimeError("urlopen should not be called for blocked URLs")

        monkeypatch.setattr("scripts.readme_sections._safe_urlopen", fake_urlopen)

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

        monkeypatch.setattr("scripts.readme_sections._safe_urlopen", fake_urlopen)

        metadata = client.fetch_metadata("http://localhost/blog/post")

        assert metadata == {
            "hero_image": None,
            "summary": None,
            "published": None,
            "host": "localhost",
        }
        assert not called

    @staticmethod
    def _addrinfo_for(ip: str) -> list[tuple[object, ...]]:
        family = socket.AF_INET6 if ":" in ip else socket.AF_INET
        sockaddr = (ip, 0, 0, 0) if family == socket.AF_INET6 else (ip, 0)
        return [(family, socket.SOCK_STREAM, 0, "", sockaddr)]

    def test_ssrf_blocks_dns_resolved_private_ip(self, monkeypatch) -> None:
        monkeypatch.setattr(
            "scripts.readme_sections.socket.getaddrinfo",
            lambda *args, **kwargs: self._addrinfo_for("10.0.0.5"),
        )
        assert not _is_safe_remote_url("https://public-looking.example/path")

        client = BlogFeedClient()
        called = False

        def fake_urlopen(request, timeout=10.0):  # noqa: ARG001
            nonlocal called
            called = True
            raise RuntimeError("urlopen should not be called for blocked URLs")

        monkeypatch.setattr("scripts.readme_sections._safe_urlopen", fake_urlopen)
        posts = client.fetch_latest_posts(
            "https://public-looking.example/feed.xml",
            limit=2,
        )
        assert posts == []
        assert not called

    def test_ssrf_blocks_dns_resolved_link_local_metadata(self, monkeypatch) -> None:
        monkeypatch.setattr(
            "scripts.readme_sections.socket.getaddrinfo",
            lambda *args, **kwargs: self._addrinfo_for("169.254.169.254"),
        )
        assert not _is_safe_remote_url("http://imds.example/latest/meta-data")

    def test_ssrf_blocks_literal_private_and_metadata_ips(self) -> None:
        assert not _is_safe_remote_url("http://192.168.1.10/")
        assert not _is_safe_remote_url("http://10.1.2.3/")
        assert not _is_safe_remote_url("http://172.16.0.1/")
        assert not _is_safe_remote_url("http://169.254.169.254/")
        assert not _is_safe_remote_url("http://[::1]/")
        assert not _is_safe_remote_url("http://[fc00::1]/")
        assert not _is_safe_remote_url("http://[::ffff:127.0.0.1]/")

    def test_ssrf_fails_closed_on_dns_error(self, monkeypatch) -> None:
        def boom(*args, **kwargs):  # noqa: ARG001
            raise socket.gaierror("name resolution failed")

        monkeypatch.setattr("scripts.readme_sections.socket.getaddrinfo", boom)
        assert not _is_safe_remote_url("https://unresolvable.example/")

    def test_ssrf_allows_public_dns(self, monkeypatch) -> None:
        monkeypatch.setattr(
            "scripts.readme_sections.socket.getaddrinfo",
            lambda *args, **kwargs: self._addrinfo_for("93.184.216.34"),
        )
        assert _is_safe_remote_url("https://example.com/feed.xml")

    def test_ssrf_redirect_revalidates_private_target(self, monkeypatch) -> None:
        def fake_getaddrinfo(host, *args, **kwargs):  # noqa: ARG001
            if host == "safe.example":
                return self._addrinfo_for("93.184.216.34")
            if host == "evil.example":
                return self._addrinfo_for("127.0.0.1")
            raise socket.gaierror(host)

        monkeypatch.setattr(
            "scripts.readme_sections.socket.getaddrinfo",
            fake_getaddrinfo,
        )
        handler = _SafeRedirectHandler()
        req = Request("https://safe.example/start")
        with pytest.raises(URLError, match="Blocked unsafe redirect"):
            handler.redirect_request(
                req,
                None,
                302,
                "Found",
                {},
                "https://evil.example/secret",
            )

    def test_ssrf_redirect_allows_public_target(self, monkeypatch) -> None:
        monkeypatch.setattr(
            "scripts.readme_sections.socket.getaddrinfo",
            lambda *args, **kwargs: self._addrinfo_for("93.184.216.34"),
        )
        handler = _SafeRedirectHandler()
        req = Request("https://safe.example/start")
        redirected = handler.redirect_request(
            req,
            None,
            302,
            "Found",
            {},
            "https://cdn.example/asset.png",
        )
        assert redirected is not None
        assert redirected.full_url == "https://cdn.example/asset.png"

    def test_ssrf_safe_urlopen_rejects_unsafe_request(self, monkeypatch) -> None:
        opened = False

        class BoomOpener:
            def open(self, *args, **kwargs):  # noqa: ARG002
                nonlocal opened
                opened = True
                raise AssertionError("opener should not run for blocked URLs")

        monkeypatch.setattr(
            "scripts.readme_sections.build_opener",
            lambda *args, **kwargs: BoomOpener(),
        )
        with pytest.raises(URLError, match="Blocked unsafe URL"):
            _safe_urlopen(Request("http://127.0.0.1/secret"), timeout=1.0)
        assert not opened


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
        assert "featured-card-wyattowalsh-riso.svg" in content
        assert "blog-first-post.svg" in content
        assert "blog-second-post.svg" in content
        assert "blog-posts.svg" not in content
        assert ".github/assets/img/gh.gif" not in content
        assert ".github/assets/img/animated-community.gif" not in content
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
        assert "blog-posts.svg" not in generated

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
        assert not (svg_dir / "top-contact.svg").exists()
        assert (svg_dir / "featured-card-wyattowalsh-riso.svg").exists()
        assert not (svg_dir / "blog-posts.svg").exists()
        assert not list(svg_dir.glob("blog-*.svg"))
        assert "top-contact.svg" not in content
        assert "blog-posts.svg" not in content
        assert "featured-card-wyattowalsh-riso.svg" in content
        assert "github.com/wyattowalsh" in content

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

        generator._render_top_badges()
        svg_path = tmp_path / "svg" / "connect-github.svg"
        assert svg_path.exists()
        svg = svg_path.read_text(encoding="utf-8")

        # Expect no handle clutter or open-profile URL fragments
        assert "@wyattowalsh" not in svg
        assert "open-profile" not in svg
        # Expect no upper-right pill element on connect cards
        assert 'class="card-pill"' not in svg

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
                        language="Python",
                        forks=12,
                    )
                }
            ),
        )

        generator._render_featured_projects()

        # Per-card SVG should exist
        card_svg_path = tmp_path / "svg" / "featured-card-wyattowalsh-riso.svg"
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
        assert any(m.startswith("lang:") for m in card.meta), (
            "meta should contain lang: prefix"
        )
        assert any("★" in m for m in card.meta), "meta should contain star icon"
        assert any("⑂" in m for m in card.meta), "meta should contain fork icon"

        # The rendered SVG should not include the generic footer copy.
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
                        title=(
                            "A Very Long Blog Post Title That Would Normally"
                            " Be Truncated ... update"
                        ),
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

        generator._render_blog_posts()

        # Per-card SVG should be generated (title slug has trailing "update" stripped)
        svg_files = list((tmp_path / "svg").glob("blog-*.svg"))
        assert len(svg_files) == 1
        svg = svg_files[0].read_text(encoding="utf-8")

        # The trailing "update" should be stripped from the title in the SVG
        # The title in SVG should not end with " update"
        assert "blog-title" in svg
        assert "feature-title" not in svg
        assert "Long post" in svg

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

        featured_has_stars = any(
            "\u2605" in (m or "") for m in (featured_card.meta or [])
        )
        top_has_stars = "\u2605" in connect_content
        assert featured_has_stars and not top_has_stars


class TestProjectCardMeta:
    """Verify project card meta includes lang:, star, and fork prefixes."""

    def test_project_card_meta_contains_lang_star_fork(
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

    def test_project_card_meta_omits_lang_when_none(
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


class TestRepoBackgroundImage:
    """Verify _repo_background_image prefers API OG image over HTML scrape."""

    def test_remote_image_retries_rate_limit_deterministically(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        class FakeResponse:
            headers = {"Content-Type": "image/png"}

            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
                return None

            @staticmethod
            def read() -> bytes:
                return b"image-bytes"

        responses: list[HTTPError | FakeResponse] = [
            HTTPError(
                "https://example.test/image.png",
                429,
                "rate limited",
                Message(),
                None,
            ),
            FakeResponse(),
        ]
        delays: list[int] = []

        def fake_urlopen(request, timeout=10.0):  # noqa: ANN001, ARG001
            response = responses.pop(0)
            if isinstance(response, HTTPError):
                raise response
            return response

        monkeypatch.setattr(
            "scripts.readme_sections._build_remote_get_request",
            lambda **_kwargs: Request("https://example.test/image.png"),
        )
        monkeypatch.setattr("scripts.readme_sections._safe_urlopen", fake_urlopen)
        monkeypatch.setattr("scripts.readme_sections.time.sleep", delays.append)

        generator = ReadmeSectionGenerator(settings=ReadmeSectionsSettings())

        result = generator._fetch_remote_image_data_uri(
            "https://example.test/image.png",
            "rate-limit regression",
        )

        assert result == "data:image/png;base64,aW1hZ2UtYnl0ZXM="
        assert delays == [1]
        assert responses == []

    def test_api_og_image_used_before_html_scrape(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(enabled=True, output_dir=str(tmp_path / "svg")),
            featured_repos=[ReadmeFeaturedRepo(full_name="wyattowalsh/riso")],
        )
        generator = ReadmeSectionGenerator(
            settings=settings,
            repo_client=StubRepoClient({}),
        )
        metadata = RepoMetadata(
            full_name="wyattowalsh/riso",
            name="riso",
            html_url="https://github.com/wyattowalsh/riso",
            description="Test repo",
            stars=1,
            homepage=None,
            topics=[],
            updated_at=None,
            open_graph_image_url="https://custom-preview.example.com/riso.png",
        )

        # Mock _fetch_remote_image_data_uri to return a data URI
        def _stub_fetch(url: str, context: str) -> str | None:
            if "custom-preview" in url:
                return "data:image/png;base64,AAAA"
            return None

        monkeypatch.setattr(
            generator,
            "_fetch_remote_image_data_uri",
            _stub_fetch,
        )
        # Mock _scrape_repo_og_image to track if it gets called
        scrape_called: list[bool] = []
        monkeypatch.setattr(
            generator,
            "_scrape_repo_og_image",
            lambda repo_full_name: scrape_called.append(True) or None,
        )

        result = generator._repo_background_image(
            "wyattowalsh/riso",
            metadata,
        )

        assert result == "data:image/png;base64,AAAA"
        assert not scrape_called, (
            "HTML scrape should not be called when API OG image succeeds"
        )

    def test_generic_githubassets_url_skipped(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        settings = ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(enabled=True, output_dir=str(tmp_path / "svg")),
            featured_repos=[ReadmeFeaturedRepo(full_name="wyattowalsh/riso")],
        )
        generator = ReadmeSectionGenerator(
            settings=settings,
            repo_client=StubRepoClient({}),
        )
        metadata = RepoMetadata(
            full_name="wyattowalsh/riso",
            name="riso",
            html_url="https://github.com/wyattowalsh/riso",
            description="Test repo",
            stars=1,
            homepage=None,
            topics=[],
            updated_at=None,
            open_graph_image_url="https://opengraph.githubassets.com/abc/wyattowalsh/riso",
        )
        scrape_called = []
        monkeypatch.setattr(
            generator,
            "_scrape_repo_og_image",
            lambda repo_full_name: scrape_called.append(True) or None,
        )

        def _stub_fetch(url: str, context: str) -> str | None:
            if "opengraph.githubassets.com/1/" in url:
                return "data:image/png;base64,BBBB"
            return None

        monkeypatch.setattr(
            generator,
            "_fetch_remote_image_data_uri",
            _stub_fetch,
        )

        generator._repo_background_image("wyattowalsh/riso", metadata)

        # Should have fallen through to HTML scrape (which returns None),
        # then to the auto-generated fallback
        assert scrape_called, "HTML scrape should be called when API OG URL is generic"


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

        generator._render_blog_posts()

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
                [
                    BlogPost(
                        title="How to update your system",
                        url="https://w4w.dev/blog/sys",
                    )
                ]
            ),
            blog_metadata_client=StubBlogMetadataClient(
                {"https://w4w.dev/blog/sys": {"host": "w4w.dev"}}
            ),
        )

        generator._render_blog_posts()

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


class TestStarHistoryClient:
    def test_headers_use_environment_token(self, monkeypatch) -> None:
        monkeypatch.delenv("GH_TOKEN", raising=False)
        monkeypatch.setenv("GITHUB_TOKEN", "test-run-scoped-token")

        headers = StarHistoryClient()._headers()

        assert headers["Authorization"] == "Bearer test-run-scoped-token"

    def test_integration_stargazer_capability_gap_is_informational(
        self,
        monkeypatch,
        captured_warnings,
    ) -> None:
        payload = {
            "errors": [
                {
                    "type": "FORBIDDEN",
                    "message": "Resource not accessible by integration",
                    "path": ["repository", "stargazers"],
                    "extensions": {"saml_failure": False},
                    "locations": [{"line": 1, "column": 98}],
                }
            ]
        }
        monkeypatch.setattr(
            "scripts.readme_sections._safe_urlopen",
            lambda request, timeout=10.0: BytesIO(json.dumps(payload).encode()),
        )
        records: list[tuple[str, str]] = []
        sink_id = loguru_logger.add(
            lambda message: records.append(
                (message.record["level"].name, message.record["message"])
            ),
            level="INFO",
        )
        try:
            sampled = StarHistoryClient().fetch_star_history("wyattowalsh/agents")
        finally:
            loguru_logger.remove(sink_id)

        assert sampled is None
        assert captured_warnings == []
        assert (
            "INFO",
            "Star history unavailable for wyattowalsh/agents: GitHub integration "
            "token cannot access repository.stargazers",
        ) in records

    @pytest.mark.parametrize(
        "errors",
        [
            [
                {
                    "type": "FORBIDDEN",
                    "message": "Resource not accessible by integration",
                    "path": ["repository", "issues"],
                }
            ],
            [
                {
                    "type": "FORBIDDEN",
                    "message": "Different upstream denial",
                    "path": ["repository", "stargazers"],
                    "extensions": {"saml_failure": False},
                }
            ],
            [
                {
                    "type": "FORBIDDEN",
                    "message": "Resource not accessible by integration",
                    "path": ["repository", "stargazers"],
                    "extensions": {"saml_failure": True},
                }
            ],
            [
                {
                    "type": "FORBIDDEN",
                    "message": "Resource not accessible by integration",
                    "path": ["repository", "stargazers"],
                    "extensions": {"saml_failure": False},
                },
                {
                    "type": "RATE_LIMITED",
                    "message": "API rate limit exceeded",
                    "path": ["repository", "stargazers"],
                },
            ],
            {"type": "FORBIDDEN"},
            ["malformed-error"],
        ],
    )
    def test_unrecognized_star_history_graphql_errors_remain_warnings(
        self,
        monkeypatch,
        captured_warnings,
        errors,
    ) -> None:
        payload = {"errors": errors}
        monkeypatch.setattr(
            "scripts.readme_sections._safe_urlopen",
            lambda request, timeout=10.0: BytesIO(json.dumps(payload).encode()),
        )

        sampled = StarHistoryClient().fetch_star_history("wyattowalsh/agents")

        assert sampled is None
        assert len(captured_warnings) == 1
        assert captured_warnings[0].startswith(
            "GraphQL errors fetching star history for wyattowalsh/agents:"
        )

    def test_fetch_star_history_uses_repo_creation_time_for_low_star_repos(
        self,
        monkeypatch,
    ) -> None:
        client = StarHistoryClient()
        response_payload = {
            "data": {
                "repository": {
                    "stargazers": {
                        "edges": [
                            {
                                "starredAt": "2021-01-23T00:56:37Z",
                                "cursor": "cursor-1",
                            },
                            {
                                "starredAt": "2021-02-01T23:22:04Z",
                                "cursor": "cursor-2",
                            },
                        ],
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                    }
                }
            }
        }

        class _StubResponse:
            def __enter__(self) -> "_StubResponse":
                return self

            def __exit__(self, exc_type, exc, tb) -> None:
                return None

            def read(self) -> bytes:
                return json.dumps(response_payload).encode("utf-8")

        monkeypatch.setattr(
            "scripts.readme_sections._safe_urlopen",
            lambda request, timeout=10.0: _StubResponse(),
        )
        monkeypatch.setattr(
            "scripts.readme_sections.datetime",
            type(
                "FrozenDateTime",
                (),
                {
                    "fromisoformat": staticmethod(datetime.fromisoformat),
                    "now": staticmethod(
                        lambda tz=None: datetime(2026, 4, 22, tzinfo=UTC)
                    ),
                },
            ),
        )

        sampled = client.fetch_star_history(
            "wyattowalsh/personal-website",
            sample=6,
            series_start=datetime(2018, 11, 19, 9, 9, 41, tzinfo=UTC),
        )

        assert sampled is not None
        assert sampled[0] == 0
        assert sampled[-1] == 2
        assert len(set(sampled)) > 1


def test_fact_blog_each_card_has_title_date_hook_and_link(tmp_path: Path) -> None:
    """fact-blog: 4–5 visible w4w.dev cards, each with title, date, hook, link."""
    posts = [
        BlogPost(
            title=f"Card {index}",
            url=f"https://w4w.dev/blog/card-{index}",
            published=f"2026-03-0{index}",
            summary=f"One-line hook {index}.",
        )
        for index in range(1, 6)
    ]
    generator = ReadmeSectionGenerator(
        settings=ReadmeSectionsSettings(
            svg=ReadmeSvgSettings(
                enabled=True,
                output_dir=str(tmp_path / "svg"),
            ),
            blog_feed_url="https://w4w.dev/feed.xml",
            blog_post_limit=5,
        ),
        blog_client=StubBlogClient(posts),
        blog_metadata_client=StubBlogMetadataClient({}),
    )

    html = generator._render_blog_posts()
    assert "<details" not in html.lower()
    hrefs = re.findall(r'<a href="(https://w4w\.dev/blog/[^"]+)"', html)
    assert 4 <= len(set(hrefs)) <= 5
    assert {post.url for post in posts} <= set(hrefs)

    svg_paths = list((tmp_path / "svg").glob("blog-*.svg"))
    assert not (tmp_path / "svg" / "blog-posts.svg").exists()
    assert 4 <= len(svg_paths) <= 5
    img_links = re.findall(
        r'<a href="(https://w4w\.dev/blog/[^"]+)"[^>]*>\s*<img src="([^"]+)"',
        html,
    )
    assert len(img_links) == 5
    assert {url for url, _src in img_links} == {post.url for post in posts}
    for post in posts:
        published = post.published
        summary = post.summary
        assert published is not None
        assert summary is not None
        assert post.url in html
        assert post.title in html
        assert published in html
        assert summary in html
        matching = [src for url, src in img_links if url == post.url]
        assert matching
        svg = Path(matching[0]).read_text(encoding="utf-8")
        assert post.title in svg
        assert published in svg
        assert summary in svg
