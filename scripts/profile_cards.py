"""Compact SVG cards and their native text equivalents on the GitHub profile."""

from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import date
from html import escape
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit

from defusedxml import ElementTree
from PIL import ImageFont

from .config import PublicProjectStats, ReadmeProfileProject
from .readme_svg import (
    CLOCK_ICON_PATH,
    FORK_ICON_PATH,
    LANGUAGE_COLORS,
    LAW_ICON_PATH,
    REPO_ICON_PATH,
    STAR_ICON_PATH,
    SvgCard,
    SvgRepoCardRenderer,
    _card_shell,
    _shadow_filter_defs,
)

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
    """Stage the whole family, replace each file atomically, then prune old members."""
    if files:
        directory.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(dir=directory, prefix=f".{prefix}-") as tmp:
            staging = Path(tmp)
            for filename, svg in files.items():
                (staging / filename).write_text(svg, encoding="utf-8")
            for filename in files:
                (staging / filename).replace(directory / filename)
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


def _display_date(value: date, *, long_month: bool = False) -> str:
    month = value.strftime("%B" if long_month else "%b")
    return f"{month} {value.day}, {value.year}"


class _ProfileProjectRenderer(SvgRepoCardRenderer):
    """Reflow the shared GitHub card chrome for a 238px-wide profile column."""

    def __init__(self) -> None:
        super().__init__(width=360, height=228)
        # Pillow embeds this font, so CI and local snapshots use identical advances.
        self.font = ImageFont.load_default(size=19)

    def _wrap(self, value: str) -> list[str]:
        lines: list[str] = [""]
        for word in value.split():
            candidate = (lines[-1] + " " + word).strip()
            if lines[-1] and self.font.getlength(candidate) > 314:
                lines.append(word)
            else:
                lines[-1] = candidate
        return lines

    @staticmethod
    def _icon(path: str, x: int, y: int) -> str:
        return (
            f'<svg x="{x}" y="{y}" width="17" height="17" viewBox="0 0 16 16" '
            f'fill="var(--meta-color)" aria-hidden="true"><path d="{path}"/></svg>'
        )

    def _text(self, style: str, x: int, y: int, value: str, width: int = 325) -> str:
        # Keep the full accessible name even if one identifier exceeds a whole line.
        if self.font.getlength(value) > width:
            while value and self.font.getlength(value + "…") > width:
                value = value[:-1]
            value = value.rstrip() + "…"
        return f'<text class="{style}" x="{x}" y="{y}">{escape(value)}</text>'

    def render_project(
        self, design: ReadmeProfileProject, data: PublicProjectStats
    ) -> tuple[str, str]:
        name = design.full_name.split("/")[1]
        summary = " ".join(design.description).strip()
        source = data.languages
        total = sum(source.values())
        top = sorted(source, key=lambda key: source[key], reverse=True)[:2]
        labels = []
        for language in top:
            share = 100 * source[language] / total
            labels.append(
                (language, f"{language} " + ("<1%" if share < 1 else f"{share:.0f}%"))
            )
        if not labels and data.language not in (None, ""):
            labels.append((data.language, data.language))
        color = LANGUAGE_COLORS.get(top[0] if top else data.language or "", "#8b949e")
        updated = _display_date(data.updated_on) if data.updated_on else None
        license_id = (
            data.license_spdx
            if data.license_spdx not in {None, "", "NOASSERTION", "OTHER"}
            else None
        )
        counts = f"{data.stars:,} {'star' if data.stars == 1 else 'stars'}"
        if data.forks is not None:
            counts += f", {data.forks:,} {'fork' if data.forks == 1 else 'forks'}"
        facts = [summary, counts + "."]
        if labels:
            facts.append(", ".join(label for _, label in labels) + ".")
        if updated is not None:
            facts.append(f"Updated {updated}.")
        if license_id is not None:
            facts.append(f"{license_id} license.")
        detail = " ".join(facts)
        alt = f"{name}. {detail}"

        desc = self._wrap(summary)
        shift = max(0, len(desc) - 3) * 24
        body = [
            self._icon(REPO_ICON_PATH, 17, 23),
            self._text(
                "rc-title", 40, 38, name, 223 if data.thumbnail is not None else 295
            ),
        ]
        body.extend(
            self._text("rc-desc", 17, 83 + index * 24, line)
            for index, line in enumerate(desc)
        )
        stats = [(STAR_ICON_PATH, f"{data.stars:,}")]
        if data.forks is not None:
            stats.append((FORK_ICON_PATH, f"{data.forks:,}"))
        if license_id is not None:
            stats.append((LAW_ICON_PATH, license_id))
        x = 16
        for icon, label in stats:
            width = int(self.font.getlength(label))
            if x + 21 + width > 344:
                shift += 26
                x = 16
            body.extend(
                [
                    self._icon(icon, x, 151 + shift),
                    self._text("rc-meta", x + 21, 166 + shift, label),
                ]
            )
            x += 21 + width + (13 if icon == STAR_ICON_PATH else 12)
        if updated is not None:
            if x > 202:
                shift += 26
            body.extend(
                [
                    self._icon(CLOCK_ICON_PATH, 202, 151 + shift),
                    self._text("rc-meta", 223, 166 + shift, updated, 126),
                ]
            )
        if source:
            self._render_lang_bar(body, source, 16, 183 + shift, 328)
        x = 15
        for language, label in labels:
            width = int(self.font.getlength(label))
            if x > 15 and x + 11 + width > 351:
                x = 15
                shift += 24
            dot = LANGUAGE_COLORS.get(language, "#8b949e")
            body.extend(
                [
                    f'<circle cx="{x + 4}" cy="{207 + shift}" r="4" fill="{dot}"/>',
                    self._text("rc-meta", x + 11, 213 + shift, label, 329),
                ]
            )
            x += 11 + width + 9
        height = self.height + shift
        css = (
            self._build_css(color) + "\n.rc-title{font-size:20px}"
            ".rc-desc,.rc-meta,.rc-lang-label{font-size:18.5px}\n"
        )
        thumb_clip = (
            '<clipPath id="thumb-clip"><rect x="278" y="16" '
            'width="64" height="42" rx="6"/></clipPath>'
            if data.thumbnail is not None
            else ""
        )
        lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="360" height="{height}" '
            f'viewBox="0 0 360 {height}" role="img" aria-labelledby="title detail">',
            f'<title id="title">{escape(name)}</title>'
            f'<desc id="detail">{escape(detail)}</desc>',
            f'<defs><style>{css}</style><clipPath id="card-clip">'
            f'<rect width="360" height="{height}" rx="10"/></clipPath>'
            f"{thumb_clip}{_shadow_filter_defs()}</defs>",
            *_card_shell(360, height, rx=10, accent_fill=color, clip_id="card-clip"),
        ]
        if data.thumbnail is not None:
            lines.extend(
                [
                    '<image x="278" y="16" width="64" height="42" '
                    'preserveAspectRatio="xMidYMid slice" clip-path="url(#thumb-clip)" '
                    f'href="{escape(data.thumbnail, quote=True)}"/>',
                    '<rect x="278" y="16" width="64" height="42" rx="6" '
                    'fill="none" stroke="var(--card-border)" stroke-opacity=".6"/>',
                ]
            )
        return "\n".join([*lines, *body, "</svg>", ""]), alt


def projects_section(
    designs: Sequence[ReadmeProfileProject],
    metadata: Mapping[str, PublicProjectStats],
    directory: Path,
    *,
    images: bool,
    as_of: date,
) -> str:
    renderer = _ProfileProjectRenderer()
    topics: dict[str, list[tuple[str, str]]] = defaultdict(list)
    embeds = []
    files = {}
    for design in designs:
        name = design.full_name.split("/")[1]
        url = f"https://github.com/{design.full_name}"
        topics[design.topic].append((name, url))
        if images:
            filename = f"project-{name}.svg"
            files[filename], alt = renderer.render_project(
                design, metadata[design.full_name]
            )
            embeds.append(
                f'<a href="{url}"><img src="{directory.as_posix()}/{filename}"'
                f' width="360" alt="{escape(alt, quote=True)}"></a>'
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
            "",
            f'<p align="center"><sub>GitHub repository data as of '
            f"{_display_date(as_of, long_month=True)}.</sub></p>",
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
