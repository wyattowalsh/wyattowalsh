"""Compact SVG cards and their native text equivalents on the GitHub profile."""

from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import date
from html import escape
from pathlib import Path
from urllib.parse import urlsplit

from defusedxml import ElementTree
from PIL import ImageFont

from .config import ReadmeProfileProject
from .readme_svg import SvgCard

MARKS = {
    "nbadb": (
        '<circle cx="15" cy="15" r="11"/>'
        '<path d="M4 15h22M15 4v22M7 7c9 4 9 12 0 16M23 7c-9 4-9 12 0 16"/>'
    ),
    "proxywhirl": (
        '<path d="M5 12a10 10 0 0 1 17-4l3 4m0-6v6h-6M25 18a10 10 0 0 1-17 '
        '4l-3-4m0 6v-6h6"/>'
    ),
    "agents": (
        '<circle cx="6" cy="14" r="3"/>'
        '<circle cx="23" cy="6" r="3"/>'
        '<circle cx="23" cy="23" r="3"/>'
        '<path d="M9 14h3c4 0 3-8 8-8M12 14c4 0 3 9 8 9"/>'
    ),
    "profile-bits": (
        '<rect x="3.5" y="5" width="23" height="19" rx="2"/>'
        '<path d="M4 11h22M9 17h4m4 0h4M9 20h8"/>'
    ),
    "riso": ('<path d="m15 4 11 6-11 6-11-6zM4 15l11 6 11-6M4 20l11 6 11-6"/>'),
    "openopps": (
        '<rect x="3.5" y="5.5" width="18" height="16" rx="1.8"/>'
        '<path d="M8 10h9M8 14h5M8 18h3"/>'
        '<circle cx="20" cy="19" r="5"/>'
        '<path d="m24 23 4 4"/>'
    ),
    "webmedia-dl": ('<path d="M15 3v14m-5-5 5 5 5-5M4 18v6h22v-6"/>'),
    "iina-plugin-bookmarks": (
        '<path d="M7 4.5h16v21l-8-5.5-8 5.5z"/><path d="m12 9 6 3.5-6 3.5z"/>'
    ),
    "nbops": ('<path d="M4 6v18h22M6 17h4l3-8 4 12 4-9h4"/>'),
    "cwa": ('<path d="M4 4.5h20v14H12l-5.5 4v-4H4zM9 10h8M19 22l4 4 4-4m-4-4v8"/>'),
    "personal-website": (
        '<rect x="3.5" y="5" width="23" height="20" rx="1.5"/>'
        '<path d="M4 10h22M9 15h6m-6 4h10"/>'
    ),
    "prompts": ('<path d="M6 4.5h14l4 4v17H6zM19 5v5h5m-14 3 3 3-3 3m6 0h4"/>'),
    "ai-web-feeds": (
        '<circle cx="7" cy="23" r="1.5"/>'
        '<path d="M6 14a10 10 0 0 1 10 10M6 6a18 18 0 0 1 18 18"/>'
    ),
    "linkedin-profile-exporter": (
        '<rect x="3.5" y="5" width="20" height="18" rx="1.5"/>'
        '<circle cx="10" cy="12" r="2"/>'
        '<path d="M6.5 18c1-4 6-4 7 0M17 11h3m-3 3h3m-2 10h9m-4-4 4 4-4 4"/>'
    ),
    "copy-to-gmail": (
        '<path d="M8 4.5h12v5H8zM8 7H4.5v18H16M20 7h3v6"/>'
        '<rect x="10" y="14" width="17" height="12" rx="1.2"/>'
        '<path d="m11 15 7.5 6 7.5-6"/>'
    ),
    "wild-web-wrap-up": (
        '<path d="M3.5 5h18v20h-16a2 2 0 0 1-2-2zM22 10h4v12a3 3 0 0 1-3 3M7 '
        '9h11M7 14h4v5H7zM14 14h4m-4 4h4"/>'
    ),
    "fl-mcp": (
        '<path d="M6 5v20M15 5v20M24 5v20"/>'
        '<path class="solid" d="M3.5 9h5v4h-5zM12.5 16h5v4h-5zM21.5 8h5v4h-5z"/>'
    ),
    "mcp-crawl4ai": (
        '<circle cx="15" cy="15" r="11"/>'
        '<ellipse cx="15" cy="15" rx="5" ry="11"/>'
        '<path d="M5 11h20M5 19h20"/>'
    ),
    "hue-board": (
        '<path d="M10 15c-6-7 1-15 8-11 5 3 5 7 1 11l-2 4h-5zM12 22h6m-5 3h4M5 '
        '5l-2-2m22 2 2-2"/>'
    ),
    "awesome-iina": (
        '<path d="M4 5h7v19H4zM12 5h5v19h-5zM19 8l5-2 5 16-5 2zM5 18h5"/>'
    ),
    "agentic-cad": ('<path d="m15 3 11 6v12l-11 6-11-6V9zM4 9l11 6 11-6M15 15v12"/>'),
    "NYC-recs": (
        '<path d="m3 8 7-3 8 3 9-3v18l-9 3-8-3-7 3zM10 5v18m8-15v18"/>'
        '<circle cx="15" cy="14" r="2"/>'
    ),
    "iina-plugin-starter": (
        '<path d="M4 24V7h7l2 3h13v14z"/><path d="m12 14-3 3 3 3m6-6 3 3-3 3"/>'
    ),
    "soundlab": ('<path d="M2 15h4l2-6 3 13 3-18 3 22 3-15 2 4h6"/>'),
}

_PALETTES = {
    "rust": ("#92452d", "#efac91"),
    "teal": ("#276b65", "#8bd2bf"),
    "blue": ("#395f84", "#a4cceb"),
}
_SURFACE = """
.paper{fill:#faf8f3;stroke:#cec9bd}.name{fill:#254966}.desc{fill:#324452}
.meta{fill:#52616d}.solid{fill:#faf8f3}
@media(prefers-color-scheme:dark){
.paper{fill:#161b22;stroke:#424952}.name{fill:#bedcf3}
.desc{fill:#d7dfe7}.meta{fill:#b3c0ca}.solid{fill:#161b22}}
"""


def profile_directory(shared_directory: Path | str) -> Path:
    return Path(shared_directory).parent / "readme-profile"


def replace_family(directory: Path, prefix: str, files: Mapping[str, str]) -> None:
    """Replace exactly one generated family, removing retired members after render."""
    if files:
        directory.mkdir(parents=True, exist_ok=True)
    for filename, svg in files.items():
        (directory / filename).write_text(svg, encoding="utf-8")
    for path in directory.glob(f"{prefix}-*.svg"):
        if path.name not in files:
            path.unlink()


def validate_retained_articles(block: str, directory: Path) -> None:
    """Validate the previous cards when the article feed is unavailable."""
    ns = "{http://www.w3.org/2000/svg}"
    root = ElementTree.fromstring("<section>" + block + "</section>")
    images = root.findall(".//img")
    names = set()
    for image in images:
        path = Path(image.get("src", ""))
        if (
            path.parent != directory
            or not path.match("blog-*.svg")
            or path.is_symlink()
            or not path.is_file()
            or path.name in names
        ):
            raise ValueError("Missing or mismatched retained article card")
        svg = ElementTree.parse(path).getroot()
        title = svg.findtext(ns + "title")
        alt = image.get("alt", "")
        if (
            svg.tag != ns + "svg"
            or svg.get("viewBox") != "0 0 360 152"
            or not title
            or not (alt == title or alt.startswith(title + " · "))
        ):
            raise ValueError("Invalid retained article card")
        names.add(path.name)
    if names != {path.name for path in directory.glob("blog-*.svg")}:
        raise ValueError("Retained article inventory differs from its README links")
    if not names and "No recent posts available." not in block:
        raise ValueError(
            "The unavailable feed has no published article block to retain"
        )


def _project_svg(
    project: ReadmeProfileProject,
    name: str,
    alt: str,
    language: str,
    stars: int,
) -> str:
    light, dark = _PALETTES[project.theme]
    desc1, desc2 = map(escape, project.description)
    small = " small" if len(name) > 20 else ""
    star = (
        f'<text x="258" y="99" text-anchor="end" class="meta">★ {stars:,}</text>'
        if stars
        else ""
    )
    mark = MARKS.get(name, '<path d="m9 8-7 7 7 7m12-14 7 7-7 7"/>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="274" height="112"
 viewBox="0 0 274 112" role="img" aria-labelledby="t d">
<title id="t">{escape(name)}</title><desc id="d">{escape(alt)}</desc>
<style>{_SURFACE}
text{{font-family:Arial,Helvetica,sans-serif}}
.name{{font:700 20px Georgia,"Times New Roman",serif}}
.name.small{{font-size:17px;letter-spacing:-.45px}}.desc{{font-size:15.5px}}
.meta{{font-size:13px}}.mark{{fill:none;stroke:{light};stroke-linecap:round;
stroke-linejoin:round;stroke-width:1.7}}
@media(prefers-color-scheme:dark){{.mark{{stroke:{dark}}}}}</style>
<rect x="1" y="1" width="272" height="110" rx="7" class="paper"/>
<text x="16" y="29" class="name{small}">{escape(name)}</text>
<g class="mark" transform="translate(234 9) scale(.86)">{mark}</g>
<text x="16" y="54" class="desc">{desc1}</text>
<text x="16" y="74" class="desc">{desc2}</text>
<text x="16" y="99" class="meta">{escape(language)}</text>{star}
</svg>
"""


def projects_section(
    designs: Sequence[ReadmeProfileProject],
    metadata: Mapping[str, tuple[str, int]],
    directory: Path,
    *,
    images: bool,
) -> str:
    topics: dict[str, list[tuple[str, str]]] = defaultdict(list)
    embeds = []
    files = {}
    for design in designs:
        name = design.full_name.split("/")[1]
        url = f"https://github.com/{design.full_name}"
        topics[design.topic].append((name, url))
        if images:
            language, stars = metadata[design.full_name]
            if type(stars) is not int or stars < 0:
                raise ValueError(f"Invalid star count for {design.full_name}")
            details = " ".join(
                (*design.description, language + "." if language else "")
            )
            if stars:
                details += f" {stars:,} GitHub {'star' if stars == 1 else 'stars'}."
            filename = f"project-{name}.svg"
            files[filename] = _project_svg(
                design, name, details.strip(), language, stars
            )
            alt = escape(f"{name}. {details.strip()}")
            embeds.append(
                f'<a href="{url}"><img src="{directory.as_posix()}/{filename}"'
                f' width="274" height="112" alt="{alt}"></a>'
            )
    replace_family(directory, "project", files)
    index = [
        f"- **{escape(topic)}** — "
        + " · ".join(
            f"[{name}]({url})"
            for name, url in sorted(group, key=lambda p: p[0].lower())
        )
        for topic, group in topics.items()
    ]
    if not embeds:
        return "\n".join(index) or "- No featured repositories configured."
    return "\n".join(
        [
            "<details>",
            "<summary>Find a project by topic</summary>",
            "",
            *index,
            "",
            "</details>",
            "",
            '<p align="center">',
            *embeds,
            "</p>",
        ]
    )


def _fit_lines(text: str, widths: Sequence[int], size: int) -> list[str]:
    """Wrap using Pillow's embedded scalable font. Bound even a single long token."""
    font = ImageFont.load_default(size=size)
    words = text.split()
    lines = []
    for width in widths:
        if not words:
            break
        line = words.pop(0)
        while words and font.getlength(line + " " + words[0]) < width:
            line += " " + words.pop(0)
        if font.getlength(line) > width or (len(lines) == len(widths) - 1 and words):
            line = line[:width]
            while line and font.getlength(line + "…") > width:
                line = line[:-1]
            line = line.rstrip() + "…"
        lines.append(line)
    return lines


def _article_svg(card: SvgCard, hook: str, published: str) -> str:
    image = card.background_image or ""
    # Embed the bounded data URI from the metadata fetcher as an SVG image.
    thumb = ""
    if image.startswith(
        tuple(
            f"data:image/{fmt};base64,"
            for fmt in (
                "png",
                "jpeg",
                "webp",
                "gif",
                "avif",
                "svg+xml",
            )
        )
    ):
        thumb = (
            '<image x="280" y="10" width="64" height="38" '
            'preserveAspectRatio="xMidYMid slice" clip-path="url(#thumb)" '
            f'href="{escape(image)}"/>'
        )
    widths = (232, 232, 309, 309) if thumb else (309,) * 4
    lines = _fit_lines(card.title, widths, 20)
    y0 = 40 if len(lines) <= 2 else 29
    yhook = 88 if len(lines) <= 2 else y0 + (len(lines) - 1) * 21 + 24
    titles = "\n".join(
        f'<text x="16" y="{y0 + i * 21}" class="name">{escape(line)}</text>'
        for i, line in enumerate(lines)
    )
    short_hook = next(iter(_fit_lines(hook, (316,), 15)), "")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="360" height="152"
 viewBox="0 0 360 152" role="img" aria-labelledby="t d">
<title id="t">{escape(card.title)}</title>
<desc id="d">{escape(published)}. {escape(hook)}</desc>
<style>{_SURFACE}
.name{{font:700 18px Georgia,"Times New Roman",serif}}
.desc{{font:14.5px Arial,Helvetica,sans-serif}}
.meta{{font:13.5px Arial,Helvetica,sans-serif}}
</style>
<defs><clipPath id="thumb">
<rect x="280" y="10" width="64" height="38" rx="4"/></clipPath></defs>
<rect x="1" y="1" width="358" height="150" rx="7" class="paper"/>
{thumb}
{titles}
<text x="16" y="{yhook}" class="desc">{escape(short_hook)}</text>
<text x="16" y="135" class="meta">{escape(published)}</text>
</svg>
"""


def articles_section(
    cards: Sequence[tuple[str, SvgCard]],
    hooks: Mapping[str, str],
    directory: Path,
    feed_url: str,
    *,
    images: bool,
) -> str:
    files = {}
    embeds = []
    links = []
    for name, card in cards:
        url = card.url or ""
        if urlsplit(url).scheme not in ("http", "https") or not urlsplit(url).netloc:
            raise ValueError("Article link requires an absolute HTTP(S) URL")
        hook = hooks.get(url) or next(iter(card.lines), "")
        date_string = next(
            (
                m.removeprefix("Published ")
                for m in card.meta
                if m.startswith("Published ")
            ),
            "",
        )
        stamp = ""
        if date_string:
            day = date.fromisoformat(date_string)
            stamp = f"{day:%b} {day.day}, {day.year}"
        caption = " · ".join(filter(None, (card.title, stamp, hook)))
        filename = f"{name}.svg"
        if images:
            files[filename] = _article_svg(card, hook, stamp)
            embeds.append(
                f'<a href="{escape(url)}"><img src="{directory.as_posix()}/{filename}" '
                f'alt="{escape(caption)}" width="360" height="152"/></a>'
            )
        links.append(
            f'- <a href="{escape(url)}">{escape(card.title)}</a>'
            + (f" · {stamp}" if stamp else "")
        )
    replace_family(directory, "blog", files)
    result = []
    if embeds:
        result += [
            '<p align="center">',
            *embeds,
            "</p>",
            "",
            "<details>",
            "<summary>Read the post titles as text</summary>",
            "",
            *links,
            "",
            "</details>",
        ]
    else:
        result += links or ["No recent posts available."]
    return "\n".join(
        [*result, "", f'<a href="{escape(feed_url)}">Subscribe via RSS</a>']
    )
