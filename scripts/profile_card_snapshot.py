"""Render the compact profile families from a recorded public metadata fixture."""

import argparse
import base64
import json
from datetime import date
from pathlib import Path

from defusedxml import ElementTree

from .config import PublicProjectStats, load_config
from .profile_cards import articles_section, profile_directory, projects_section
from .readme_sections import ReadmeSectionGenerator
from .readme_svg import SvgCard


def apply_snapshot(path: Path) -> None:
    settings = load_config().readme_sections_settings
    if settings is None or settings.profile_cards is None:
        raise ValueError("The profile card configuration is required")
    profile = settings.profile_cards
    snapshot = json.loads(path.read_bytes())
    if set(snapshot["projects"]) != {p.full_name for p in profile.projects}:
        raise ValueError("Recorded repository roster differs from configuration")
    stats = {}
    for full_name, record in snapshot["projects"].items():
        source = Path(record["thumbnail_source"])
        shared_name = "featured-card-" + full_name.lower().replace("/", "-") + ".svg"
        extra_name = full_name.split("/")[1] + ".webp"
        if source == Path(settings.svg.output_dir) / shared_name:
            image = ElementTree.parse(source).find(
                ".//{http://www.w3.org/2000/svg}image"
            )
            thumbnail = image.get("href") if image is not None else None
            if not thumbnail or not thumbnail.startswith("data:image/"):
                raise ValueError(f"Missing recorded project thumbnail for {full_name}")
        elif source == Path("tests/fixtures/profile-project-thumbnails") / extra_name:
            raw = (path.parent / source.parent.name / source.name).read_bytes()
            if raw[:4] != b"RIFF" or raw[8:12] != b"WEBP":
                raise ValueError(f"Invalid recorded WebP for {full_name}")
            thumbnail = "data:image/webp;base64," + base64.b64encode(raw).decode(
                "ascii"
            )
        else:
            raise ValueError(f"Invalid recorded project thumbnail for {full_name}")
        stats[full_name] = PublicProjectStats(**record, thumbnail=thumbnail)
    generator = ReadmeSectionGenerator(settings)
    readme = Path(settings.readme_path)
    source = readme.read_text(encoding="utf-8")
    generator._require_marker_pairs(source)
    cards = []
    for article in snapshot["articles"][: settings.blog_post_limit]:
        previous = Path(article["thumbnail_source"])
        if previous.parent != Path(settings.svg.output_dir) or not previous.match(
            "blog-*.svg"
        ):
            raise ValueError("Invalid source for recorded blog thumbnail")
        root = ElementTree.parse(previous)
        image = root.find(".//{http://www.w3.org/2000/svg}image")
        uri = image.get("href") if image is not None else None
        card = SvgCard(
            title=article["title"],
            url=article["url"],
            lines=(),
            meta=("Published " + article["published"],),
            background_image=uri,
        )
        cards.append((previous.stem, card))
    directory = profile_directory(settings.svg.output_dir)
    projects = projects_section(
        profile.projects,
        stats,
        directory,
        images=generator._svg_section_enabled("featured_projects"),
        as_of=date.fromisoformat(snapshot["projects_as_of"]),
    )
    articles = articles_section(
        cards,
        profile.article_hooks,
        directory,
        settings.blog_feed_url,
        images=generator._svg_section_enabled("blog_posts"),
    )
    source = generator._inject_block(
        source, generator.FEATURED_START, generator.FEATURED_END, projects
    )
    source = generator._inject_block(
        source, generator.BLOG_START, generator.BLOG_END, articles
    )
    readme.write_text(source, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    apply_snapshot(parser.parse_args().snapshot)
