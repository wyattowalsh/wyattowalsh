"""Offline generation, placement and asset ownership for profile contact links."""

from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from defusedxml import ElementTree

from scripts.config import (
    ReadmeProfileCards,
    ReadmeSectionsSettings,
    ReadmeSocialLink,
    ReadmeSvgSettings,
    load_config,
)
from scripts.profile_cards import profile_directory
from scripts.profile_contacts import render_profile_contacts
from scripts.readme_sections import ReadmeSectionGenerator


def _pair(name: str) -> str:
    return f"<!-- README:{name}:START -->\nprevious\n<!-- README:{name}:END -->"


def _template() -> str:
    return "\n\n".join(
        _pair(name)
        for name in (
            "TOP_BADGES",
            "FEATURED_PROJECTS",
            "METRICS",
            "FREQUENCIES",
            "BLOG_POSTS",
            "CONTACT_LINKS",
        )
    )


def _configured_links() -> list[ReadmeSocialLink]:
    settings = load_config().readme_sections_settings
    assert settings is not None
    return settings.social_links


@pytest.fixture
def generator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> ReadmeSectionGenerator:
    settings = ReadmeSectionsSettings(
        readme_path=str(tmp_path / "README.md"),
        social_links=_configured_links(),
        profile_cards=ReadmeProfileCards(projects=[]),
        svg=ReadmeSvgSettings(enabled=True, output_dir=str(tmp_path / "readme")),
    )
    generator = ReadmeSectionGenerator(settings)
    monkeypatch.setattr(generator, "_render_featured_projects", lambda: "")
    monkeypatch.setattr(generator, "_render_blog_posts", lambda: "")
    monkeypatch.setattr(
        generator, "_postprocess_static_sections", lambda content, **_: content
    )
    monkeypatch.setattr("scripts.readme_sections.generate_separators", lambda: None)
    Path(settings.readme_path).write_text(_template())
    return generator


def test_configured_contacts_rebuild_offline_and_match_published_marks() -> None:
    links = _configured_links()
    shared = Path(".github/assets/img/readme")
    directory = profile_directory(shared)
    result = render_profile_contacts(links, directory, images=True)
    buttons = BeautifulSoup(result.opening, "html.parser").select("p > a")
    footer = BeautifulSoup(result.footer, "html.parser").select("a")
    assert (
        [a["href"] for a in buttons]
        == [a["href"] for a in footer]
        == [link.url for link in links]
    )
    assert [a.get_text() for a in footer] == [link.label for link in links]
    assert set(result.files) == {p.name for p in directory.glob("connect-*.svg")}
    for button in buttons:
        img = button.select_one("img")
        assert (
            img is not None
            and img["alt"]
            and (img["width"], img["height"]) == ("115", "44")
        )
        path = Path(str(img["src"]))
        assert result.files[path.name].encode() == path.read_bytes()
        svg = ElementTree.parse(path).getroot()
        mark = "{http://www.w3.org/2000/svg}image"
        assert svg.get("viewBox") == "0 0 115 44"
        assert svg.find(mark).get("href") == ElementTree.parse(
            shared / path.name
        ).getroot().find(mark).get("href")


def test_contact_refresh_tracks_config_without_touching_other_families(
    generator: ReadmeSectionGenerator,
) -> None:
    settings = generator.settings
    directory = profile_directory(settings.svg.output_dir)
    directory.mkdir(parents=True)
    other = directory / "project-other.svg"
    other.write_text("unrelated")
    readme = generator.generate(require_markers=True)
    original = readme.read_bytes()
    assert generator.generate(require_markers=True).read_bytes() == original
    settings.social_links = [
        ReadmeSocialLink(
            label="LinkedIn", url="https://linkedin.com/in/another-profile"
        ),
        ReadmeSocialLink(
            label="An additional & longer contact", url="https://example.org/?a=1&b=2"
        ),
    ]
    generator.generate(require_markers=True)
    doc = BeautifulSoup(readme.read_text(), "html.parser")
    assert [a["href"] for a in doc.select("a")] == [
        link.url for link in settings.social_links
    ] * 2
    changed = doc.select_one("img")
    assert changed is not None and changed["alt"] == "LinkedIn"
    assert len(doc.select("img")) == 1
    assert {p.name for p in directory.glob("connect-*.svg")} == {"connect-linkedin.svg"}
    assert other.read_text() == "unrelated"
    settings.svg.top_contact = False
    generator.generate(require_markers=True)
    doc = BeautifulSoup(readme.read_text(), "html.parser")
    assert not doc.select("img")
    assert [a.get_text() for a in doc.select("a")] == [
        link.label for link in settings.social_links
    ] * 2
    assert not list(directory.glob("connect-*.svg"))
    assert other.read_text() == "unrelated"


@pytest.mark.parametrize(
    "broken",
    [
        "",
        "<!-- README:CONTACT_LINKS:START -->",
        "<!-- README:CONTACT_LINKS:END -->",
        _pair("CONTACT_LINKS") + "\n" + _pair("CONTACT_LINKS"),
        "<!-- README:CONTACT_LINKS:END -->\n<!-- README:CONTACT_LINKS:START -->",
    ],
)
def test_broken_contact_pair_preflights_configured_profile(
    generator: ReadmeSectionGenerator, broken: str
) -> None:
    readme = Path(generator.settings.readme_path)
    original = readme.read_text().replace(_pair("CONTACT_LINKS"), broken)
    readme.write_text(original)
    with pytest.raises(ValueError, match="CONTACT_LINKS"):
        generator.generate(require_markers=True)
    assert readme.read_text() == original
    assert not list(
        profile_directory(generator.settings.svg.output_dir).glob("connect-*.svg")
    )


def test_contact_staging_failure_preserves_previous_family_and_readme(
    generator: ReadmeSectionGenerator, monkeypatch: pytest.MonkeyPatch
) -> None:
    directory = profile_directory(generator.settings.svg.output_dir)
    directory.mkdir(parents=True)
    previous = directory / "connect-w4w-dev.svg"
    previous.write_text("previous button")
    retired = directory / "connect-retired.svg"
    retired.write_text("previously published link")
    readme = Path(generator.settings.readme_path)
    before = readme.read_bytes()

    def reject_staged_link(path: Path, data: str, *, encoding: str) -> int:
        if path.name == "connect-linkedin.svg":
            raise OSError("staging failed")
        with path.open("w", encoding=encoding) as stream:
            return stream.write(data)

    monkeypatch.setattr(Path, "write_text", reject_staged_link)
    with pytest.raises(OSError, match="staging failed"):
        generator.generate(require_markers=True)
    assert readme.read_bytes() == before
    assert set(directory.iterdir()) == {previous, retired}
    assert previous.read_text() == "previous button"
    assert retired.read_text() == "previously published link"
