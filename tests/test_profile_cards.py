"""GitHub-only compact card refresh and snapshot contracts."""

import base64
import json
import shutil
from collections import Counter
from datetime import date
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock

import pytest

from scripts.config import PublicProjectStats, ReadmeProfileCards, load_config
from scripts.profile_card_snapshot import apply_snapshot
from scripts.profile_cards import (
    articles_section,
    projects_section,
    validate_retained_articles,
)
from scripts.readme_sections import (
    BlogPost,
    GitHubRepoClient,
    ReadmeSectionGenerator,
    RepoMetadata,
)
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
    for source in (ROOT / SHARED).glob("featured-card-*.svg"):
        shutil.copyfile(source, SHARED / source.name)
    for item in json.loads(SNAPSHOT.read_text())["articles"]:
        thumbnail = Path(item["thumbnail_source"])
        shutil.copyfile(ROOT / thumbnail, thumbnail)
    before = {p: p.read_bytes() for p in SHARED.iterdir()}
    apply_snapshot(SNAPSHOT)
    assets = {p: p.read_bytes() for p in PROFILE.iterdir()}
    md = readme.read_text()
    assert len(assets) == 29
    assert md.count('width="360" alt=') == 24
    assert all(
        b'viewBox="0 0 360 228"' in svg
        for path, svg in assets.items()
        if path.name.startswith("project-")
    )
    assert "79 stars, 20 forks." in md and "Python 98%, Jupyter Notebook 2%." in md
    assert "GitHub repository data as of November 21, 2026." in md
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
            repository_updated_at=row["updated_on"] + "T00:00:00Z",
            forks=row["forks"],
            license_spdx=row["license_spdx"],
            language=row["language"],
        )

    repo_client.fetch_repo_metadata.side_effect = metadata
    repo_client.fetch_repo_languages.side_effect = lambda name: records[name][
        "languages"
    ]
    image_file = SNAPSHOT.parent / "profile-project-thumbnails/soundlab.webp"
    thumbnail = (
        "data:image/webp;base64," + base64.b64encode(image_file.read_bytes()).decode()
    )
    generator = ReadmeSectionGenerator(settings, repo_client=repo_client)
    monkeypatch.setattr(generator, "_build_star_history_points", lambda *args: None)
    thumbnail_lookup = Mock(return_value=thumbnail)
    monkeypatch.setattr(generator, "_repo_background_image", thumbnail_lookup)
    monkeypatch.setattr(generator, "_brand_icon_data_uri", lambda **kwargs: None)
    DOCS.mkdir(parents=True)
    markup = generator._render_featured_projects()
    assert Counter(
        c.args[0] for c in repo_client.fetch_repo_metadata.call_args_list
    ) == Counter(records.keys())
    assert Counter(
        call.args[0] for call in repo_client.fetch_repo_languages.call_args_list
    ) == Counter(records.keys())
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
    existing = {p.name: p.read_bytes() for p in PROFILE.glob("project-*.svg")}
    assert generator._render_featured_projects() == markup
    assert existing == {p.name: p.read_bytes() for p in PROFILE.glob("project-*.svg")}
    records["wyattowalsh/nbadb"]["stars"] += 1
    generator._render_featured_projects()
    assert "80 stars, 20 forks." in (PROFILE / "project-nbadb.svg").read_text()
    assert json.loads(manifest.read_text())["projects"][0]["stars"] == 80
    # Exercise the real entry point with all previously published project files
    # and a changed upstream count. No producer may publish a partial refresh.
    readme = Path(settings.readme_path)
    shutil.copyfile(ROOT / "README.md", readme)

    def published():
        files = [readme]
        for directory in (SHARED, PROFILE, DOCS):
            files.extend(p for p in directory.rglob("*") if p.is_file())
        return {path: path.read_bytes() for path in files}

    rich = published()
    records["wyattowalsh/nbadb"]["stars"] += 1
    extra = "wyattowalsh/soundlab"
    records[extra]["languages"] = None
    with pytest.raises(ValueError, match="language data for wyattowalsh/soundlab"):
        generator.generate(require_markers=True)
    assert published() == rich
    records[extra]["languages"] = {}
    for affected in ("wyattowalsh/nbadb", extra):
        thumbnail_lookup.side_effect = lambda name, _, target=affected: (
            None if name == target else thumbnail
        )
        with pytest.raises(ValueError, match=f"thumbnail for {affected}"):
            generator.generate(require_markers=True)
        assert published() == rich

    thumbnail_lookup.side_effect = None
    generator._render_featured_projects()
    card = (PROFILE / "project-soundlab.svg").read_text()
    assert "Python." in card and "lang-bar-clip" not in card
    assert thumbnail in card
    previous = (PROFILE / "project-nbadb.svg").read_bytes()
    repo_client.fetch_repo_metadata.side_effect = None
    repo_client.fetch_repo_metadata.return_value = None
    with pytest.raises(ValueError, match="Missing public repository metadata"):
        generator._render_featured_projects()
    assert previous == (PROFILE / "project-nbadb.svg").read_bytes()
    settings.svg.featured_projects = False
    assert "<img" not in generator._render_featured_projects()
    assert not list(PROFILE.glob("project-*.svg"))


@pytest.mark.parametrize(
    "changes",
    [
        {"private": True},
        {"private": None},
        {"visibility": "internal"},
        {"full_name": "someone-else/renamed"},
    ],
)
def test_unverified_public_identity_is_rejected(monkeypatch, changes):
    payload = {"private": False, "full_name": "owner/repo", "stargazers_count": 1}
    payload.update(changes)
    monkeypatch.setattr("scripts.readme_sections._build_remote_get_request", Mock())
    monkeypatch.setattr(
        "scripts.readme_sections._safe_urlopen",
        lambda *_args, **_kwargs: BytesIO(json.dumps(payload).encode()),
    )
    assert GitHubRepoClient().fetch_repo_metadata("owner/repo") is None


@pytest.mark.parametrize(
    "body,expected",
    [(b"{}", {}), (b"null", None), (b'{"Python":false}', None), (b'{"Python":', None)],
)
def test_language_response_distinguishes_empty_from_unavailable(
    monkeypatch, body, expected
):
    monkeypatch.setattr("scripts.readme_sections._build_remote_get_request", Mock())
    monkeypatch.setattr(
        "scripts.readme_sections._safe_urlopen", lambda *_args, **_kwargs: BytesIO(body)
    )
    assert GitHubRepoClient().fetch_repo_languages("owner/repo") == expected


def test_required_thumbnail_uses_decodable_fallback(settings, monkeypatch):
    generator = ReadmeSectionGenerator(settings)
    image = (SNAPSHOT.parent / "profile-project-thumbnails/soundlab.webp").read_bytes()
    requests = []
    fallback = "https://opengraph.githubassets.com/1/owner/repo"

    class ImageResponse(BytesIO):
        headers = {"Content-Type": "image/png"}

    def response(url, **_kwargs):
        requests.append(url)
        return ImageResponse(image if url == fallback else b"<html>Unavailable</html>")

    monkeypatch.setattr(
        generator, "_scrape_repo_og_image", lambda _: "https://example.org/invalid"
    )
    monkeypatch.setattr(
        "scripts.readme_sections._build_remote_get_request", lambda url, **_: url
    )
    monkeypatch.setattr("scripts.readme_sections._safe_urlopen", response)
    uri = generator._repo_background_image("owner/repo", None)
    assert uri == "data:image/webp;base64," + base64.b64encode(image).decode()
    assert requests == ["https://example.org/invalid", fallback]


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
    with pytest.raises(ValueError, match="stars"):
        PublicProjectStats(stars=-1)
    markup = projects_section(
        [design],
        {design.full_name: PublicProjectStats(stars=0, language="Go")},
        PROFILE,
        images=True,
        as_of=date(2026, 11, 21),
    )
    assert "0 stars. Go." in markup and "fork" not in markup
    assert "Go 100%" not in (PROFILE / "project-nbadb.svg").read_text()
    with pytest.raises(ValueError, match=r"absolute HTTP"):
        articles_section(
            [("blog-a", SvgCard(title="Bad", url="about:blank"))],
            {},
            PROFILE,
            "index.rss",
            images=True,
        )
