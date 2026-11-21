"""GitHub-only compact card refresh and snapshot contracts."""

import json
import shutil
from collections import Counter
from pathlib import Path
from unittest.mock import Mock

import pytest

from scripts.config import ReadmeProfileCards, load_config
from scripts.profile_card_snapshot import apply_snapshot
from scripts.profile_cards import (
    articles_section,
    projects_section,
    validate_retained_articles,
)
from scripts.readme_sections import BlogPost, ReadmeSectionGenerator, RepoMetadata
from scripts.readme_svg import SvgCard

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "tests/fixtures/profile-cards.json"
SHARED = Path(".github/assets/img/readme")
PROFILE = SHARED.with_name("readme-profile")
DOCS = Path("docs/public/showcase")


@pytest.fixture
def settings(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    shutil.copyfile(ROOT / "config.yaml", "config.yaml")
    config = load_config().readme_sections_settings
    assert config is not None and config.profile_cards is not None
    return config


def test_recorded_profile_is_complete_repeatable_and_scoped(settings):
    readme = Path(settings.readme_path)
    readme.write_text(
        "\n".join(
            [
                ReadmeSectionGenerator.TOP_BADGES_START,
                "prior badges",
                ReadmeSectionGenerator.TOP_BADGES_END,
                ReadmeSectionGenerator.FEATURED_START,
                ReadmeSectionGenerator.FEATURED_END,
                ReadmeSectionGenerator.BLOG_START,
                ReadmeSectionGenerator.BLOG_END,
            ]
        )
    )
    SHARED.mkdir(parents=True)
    for item in json.loads(SNAPSHOT.read_text())["articles"]:
        thumbnail = Path(item["thumbnail_source"])
        shutil.copyfile(ROOT / thumbnail, thumbnail)
    before = {p: p.read_bytes() for p in SHARED.iterdir()}
    apply_snapshot(SNAPSHOT)
    assets = {p: p.read_bytes() for p in PROFILE.iterdir()}
    md = readme.read_text()
    assert len(assets) == 29
    assert md.count('width="274" height="112"') == 24
    assert md.count('width="360" height="152"') == 5
    assert md.count(" · Apr 26, 2026") == 4
    assert md.count("Find a project by topic") == 1
    assert "prior badges" in md and not DOCS.exists()
    for name in ("NYC-recs", "hue-board", "soundlab"):
        assert md.count(f"https://github.com/wyattowalsh/{name}") == 2
    assert all(
        b"data:image/" in svg for p, svg in assets.items() if p.name.startswith("blog-")
    )
    apply_snapshot(SNAPSHOT)
    assert assets == {p: p.read_bytes() for p in PROFILE.iterdir()}
    assert md == readme.read_text()
    assert before == {p: p.read_bytes() for p in SHARED.iterdir()}


def test_normal_refresh_shares_metadata_and_keeps_docs_inventory(settings, monkeypatch):
    records = json.loads(SNAPSHOT.read_text())["projects"]
    repo_client = Mock()

    def metadata(full_name):
        row = records[full_name]
        return RepoMetadata(
            full_name=full_name,
            name=full_name.split("/")[1],
            html_url=f"https://github.com/{full_name}",
            description="Test",
            stars=row["stars"],
            homepage=None,
            topics=[],
            updated_at=None,
            language=row["language"],
        )

    repo_client.fetch_repo_metadata.side_effect = metadata
    repo_client.fetch_repo_languages.return_value = {}
    generator = ReadmeSectionGenerator(settings, repo_client=repo_client)
    monkeypatch.setattr(generator, "_build_star_history_points", lambda *args: None)
    monkeypatch.setattr(generator, "_repo_background_image", lambda *args: None)
    monkeypatch.setattr(generator, "_brand_icon_data_uri", lambda **kwargs: None)
    DOCS.mkdir(parents=True)
    markup = generator._render_featured_projects()
    assert Counter(
        c.args[0] for c in repo_client.fetch_repo_metadata.call_args_list
    ) == Counter(records.keys())
    assert len(repo_client.fetch_repo_languages.call_args_list) == 18
    assert len(list(PROFILE.glob("project-*.svg"))) == 24
    assert len(list(SHARED.glob("featured-card-*.svg"))) == 18
    manifest = SHARED / "featured-projects.manifest.json"
    assert manifest.read_bytes() == (DOCS / manifest.name).read_bytes()
    assert [p["full_name"] for p in json.loads(manifest.read_text())["projects"]] == [
        r.full_name for r in settings.featured_repos
    ]
    assert markup.index(
        'href="https://github.com/wyattowalsh/nbadb"><img'
    ) < markup.index('href="https://github.com/wyattowalsh/proxywhirl"><img')
    records["wyattowalsh/nbadb"]["stars"] += 1
    generator._render_featured_projects()
    assert "★ 80" in (PROFILE / "project-nbadb.svg").read_text()
    assert json.loads(manifest.read_text())["projects"][0]["stars"] == 80
    previous = (PROFILE / "project-nbadb.svg").read_bytes()
    repo_client.fetch_repo_metadata.side_effect = None
    repo_client.fetch_repo_metadata.return_value = None
    with pytest.raises(ValueError, match="Missing public repository metadata"):
        generator._render_featured_projects()
    assert previous == (PROFILE / "project-nbadb.svg").read_bytes()
    settings.svg.featured_projects = False
    assert "<img" not in generator._render_featured_projects()
    assert not list(PROFILE.glob("project-*.svg"))


def test_normal_article_refresh_removal_and_preservation(settings):
    blog, metadata = Mock(), Mock()
    blog.fetch_latest_posts.return_value = [
        BlogPost(
            title="Über [Research] " + "M" * 200,
            url="https://example.org/a",
            summary="An article about statistics.",
            published="2025-03-01",
        ),
        BlogPost(title="Next", url="https://example.org/b"),
    ]
    metadata.fetch_metadata.return_value = {}
    generator = ReadmeSectionGenerator(
        settings, blog_client=blog, blog_metadata_client=metadata
    )
    first = generator._render_blog_posts()
    assert first is not None and "Über [Research]" in first and "M" * 200 in first
    cards = list(PROFILE.glob("blog-*.svg"))
    assert len(cards) == 2
    assert any("…" in card.read_text() for card in cards)
    validate_retained_articles(first, PROFILE)
    with pytest.raises(ValueError, match="Invalid retained article card"):
        validate_retained_articles(
            first.replace('alt="Next"', 'alt="Other"').replace(
                'alt="Next ·', 'alt="Other ·'
            ),
            PROFILE,
        )
    orphan = PROFILE / "blog-retired.svg"
    orphan.touch()
    with pytest.raises(ValueError, match="inventory differs"):
        validate_retained_articles(first, PROFILE)
    orphan.unlink()
    blog.fetch_latest_posts.return_value = None
    assert generator._render_blog_posts() is None and all(p.is_file() for p in cards)
    settings.svg.blog_posts = False
    disabled = generator._render_blog_posts()
    assert disabled is not None and "Subscribe via RSS" in disabled
    assert not list(PROFILE.glob("blog-*.svg"))
    blog.fetch_latest_posts.return_value = []
    empty = generator._render_blog_posts()
    assert empty is not None and "No recent posts" in empty
    validate_retained_articles(empty, PROFILE)
    with pytest.raises(ValueError, match="Missing or mismatched"):
        validate_retained_articles(first, PROFILE)
    with pytest.raises(ValueError, match="no published article block"):
        validate_retained_articles("", PROFILE)


def test_invalid_roster_and_article_are_rejected(settings):
    design = settings.profile_cards.projects[0]
    with pytest.raises(ValueError, match="filenames must be unique"):
        ReadmeProfileCards(projects=[design, design])
    settings.profile_cards.projects.reverse()
    with pytest.raises(ValueError, match="shared featured roster"):
        ReadmeSectionGenerator(settings)._render_featured_projects()
    with pytest.raises(ValueError, match="star count"):
        projects_section([design], {design.full_name: ("Go", -1)}, PROFILE, images=True)
    with pytest.raises(ValueError, match=r"absolute HTTP"):
        articles_section(
            [("blog-a", SvgCard(title="Bad", url="about:blank"))],
            {},
            PROFILE,
            "index.rss",
            images=True,
        )
