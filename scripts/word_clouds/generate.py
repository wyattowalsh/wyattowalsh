"""Word cloud generation with multiple renderer backends.

Supports two modes:
  - "classic": bitmap PNG via the ``wordcloud`` library (original behavior)
  - "wordle" | "clustered" | "typographic" | "shaped": SVG-native renderers

Usage:
    python -m scripts.word_clouds                          # classic PNG
    python -m scripts.word_clouds --renderer wordle        # SVG wordle
    python -m scripts.word_clouds --renderer all           # every renderer
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal, cast

import markdown
from bs4 import BeautifulSoup
from bs4.element import Tag
from pydantic import BaseModel, ConfigDict

from .readability import LayoutReadabilitySettings
from ..utils import get_logger

logger = get_logger(module=__name__)

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

RendererName = Literal[
    "classic", "wordle", "clustered", "typographic", "shaped", "metaheuristic-anim"
]

# Default paths used by CLI (restored for backwards compat)
DEFAULT_FONT_PATH: Path | None = None
for _candidate in (
    Path("/System/Library/Fonts/Helvetica.ttc"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/TTF/DejaVuSans.ttf"),
):
    if _candidate.exists():
        DEFAULT_FONT_PATH = _candidate
        break

LANGUAGES_MD_PATH = Path(".github/assets/languages.md")
TOPICS_MD_PATH = Path(".github/assets/topics.md")
PROFILE_IMG_OUTPUT_DIR = Path(".github/assets/img")

RENDERER_CHOICES: list[str] = [
    "classic",
    "wordle",
    "clustered",
    "typographic",
    "shaped",
    "metaheuristic-anim",
    "all",
]

DEFAULT_RENDERER: RendererName = "classic"
DEFAULT_WIDTH = 1600
DEFAULT_HEIGHT = 1000
DEFAULT_MAX_WORDS = 1000

# Resolve project root relative to this script
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent.parent
_ASSETS_DIR = _PROJECT_ROOT / ".github" / "assets" / "img"


# ---------------------------------------------------------------------------
# Markdown parsing helpers
# ---------------------------------------------------------------------------


def parse_frequencies_from_md(md_path: str | Path) -> dict[str, int]:
    """Parse a starred-topics/languages markdown file into {name: count}."""
    with open(md_path, encoding="utf-8") as f:
        text = f.read()
    html = markdown.markdown(text)
    soup = BeautifulSoup(html, "html.parser")
    first_ul = soup.find("ul")
    if not isinstance(first_ul, Tag):
        return {}
    topics = [a.text for a in first_ul.find_all("a")]
    all_uls = [node for node in soup.find_all("ul") if isinstance(node, Tag)][1:]
    entries = [len(ul.find_all("li")) for ul in all_uls]
    return dict(zip(topics, entries))


_OTHERS_RE = re.compile(r"^\s*others?\s*$", re.IGNORECASE)


def _filter_others(frequencies: Mapping[str, int | float]) -> dict[str, int | float]:
    """Remove generic 'others'/'other' catch-all bucket from frequencies."""
    return {k: v for k, v in frequencies.items() if not _OTHERS_RE.match(k)}


def _limit_frequencies(
    frequencies: Mapping[str, int | float],
    max_words: int,
) -> dict[str, int | float]:
    """Keep only the most important terms when a max-word cap is configured."""

    if max_words <= 0:
        return {}
    if len(frequencies) <= max_words:
        return dict(frequencies)
    sorted_terms = sorted(frequencies.items(), key=lambda item: item[1], reverse=True)
    return dict(sorted_terms[:max_words])


# ---------------------------------------------------------------------------
# Classic (bitmap) renderer
# ---------------------------------------------------------------------------


def _generate_classic(
    frequencies: Mapping[str, int | float],
    output_path: str | Path,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    max_words: int = DEFAULT_MAX_WORDS,
) -> None:
    """Original wordcloud-library PNG generation."""
    from wordcloud import WordCloud

    wc = WordCloud(
        background_color=cast(Any, None),
        max_words=max_words,
        width=width,
        height=height,
        scale=4,
        mode="RGBA",
        relative_scaling=cast(Any, 0.5),
        colormap="cool",
        contour_color="white",
        prefer_horizontal=0.85,
        min_font_size=6,
        max_font_size=200,
        font_step=2,
        collocations=False,
    )
    wc.generate_from_frequencies(dict(frequencies))
    wc.to_file(str(output_path))


# ---------------------------------------------------------------------------
# SVG renderer dispatch
# ---------------------------------------------------------------------------


def _generate_svg(
    renderer_name: str,
    frequencies: Mapping[str, int | float],
    output_path: str | Path,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    **renderer_kwargs,
) -> None:
    """Generate an SVG word cloud using one of the SVG-native renderers."""
    from .metaheuristic import get_renderer

    renderer = get_renderer(
        renderer_name,
        width=width,
        height=height,
        **renderer_kwargs,
    )
    svg_content = renderer.generate(dict(frequencies))
    Path(output_path).write_text(svg_content, encoding="utf-8")


# ---------------------------------------------------------------------------
# High-level generators
# ---------------------------------------------------------------------------

# Default color palettes per source type -- chosen for visual distinctiveness
# and readability: ocean for topics (cool, professional), aurora for languages
# (diverse hues matching the variety of programming languages).
_SOURCE_COLOR_DEFAULTS: dict[str, str] = {
    "topics": "ocean",
    "languages": "aurora",
}


def generate_word_cloud(
    source: str,
    renderer: str = DEFAULT_RENDERER,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    max_words: int = DEFAULT_MAX_WORDS,
    output_dir: str | Path | None = None,
    color_func_name: str | None = None,
    layout_readability: LayoutReadabilitySettings | dict[str, object] | None = None,
) -> Path:
    """Generate a word cloud for the given source and renderer.

    Parameters
    ----------
    color_func_name:
        Name of the OKLCH color palette to use (e.g. "sunset", "neon",
        "gradient").  When *None*, a sensible default is chosen based on
        *source*: ``"sunset"`` for topics, ``"neon"`` for languages.

    Returns the path to the generated file.
    """
    if output_dir is None:
        output_dir = _ASSETS_DIR
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Pick source-appropriate palette when caller doesn't specify
    if color_func_name is None:
        color_func_name = _SOURCE_COLOR_DEFAULTS.get(source, "gradient")

    # Resolve input file
    md_file = _PROJECT_ROOT / ".github" / "assets" / f"{source}.md"
    if not md_file.exists():
        md_file = _PROJECT_ROOT / f"{source}.md"
    frequencies = _limit_frequencies(
        _filter_others(parse_frequencies_from_md(md_file)),
        max_words,
    )

    if renderer == "classic":
        ext = ".png"
        out = output_dir / f"wordcloud_by_{source}{ext}"
        _generate_classic(
            frequencies,
            out,
            width=width,
            height=height,
            max_words=max_words,
        )
    else:
        ext = ".svg"
        out = output_dir / f"wordcloud_{renderer}_by_{source}{ext}"
        _generate_svg(
            renderer,
            frequencies,
            out,
            width=width,
            height=height,
            color_func_name=color_func_name,
            layout_readability=layout_readability,
        )

    return out


def generate_all(
    renderer: str = DEFAULT_RENDERER,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    output_dir: str | Path | None = None,
) -> list[Path]:
    """Generate word clouds for both topics and languages.

    If renderer is "all", generates every renderer variant.
    Returns list of output paths.
    """
    renderers = (
        [
            "classic",
            "wordle",
            "clustered",
            "typographic",
            "shaped",
            "metaheuristic-anim",
        ]
        if renderer == "all"
        else [renderer]
    )

    outputs: list[Path] = []
    for r in renderers:
        for source in ("topics", "languages"):
            out = generate_word_cloud(
                source=source,
                renderer=r,
                width=width,
                height=height,
                output_dir=output_dir,
            )
            logger.info("Generated: {out}", out=out)
            outputs.append(out)
    return outputs


# ---------------------------------------------------------------------------
# Backward-compatible entry points
# ---------------------------------------------------------------------------


def get_topics_word_cloud() -> None:
    """Legacy entry point for topics word cloud."""
    generate_word_cloud("topics", renderer="classic")


def get_languages_word_cloud() -> None:
    """Legacy entry point for languages word cloud."""
    generate_word_cloud("languages", renderer="classic")


# ---------------------------------------------------------------------------
# CLI compatibility shims (consumed by scripts/cli.py)
# ---------------------------------------------------------------------------

# Alias for the CLI's expected import name
parse_markdown_for_word_cloud_frequencies = parse_frequencies_from_md


class WordCloudSettings(BaseModel):
    """Settings for word cloud generation."""

    model_config = ConfigDict(extra="forbid")
    renderer: str = DEFAULT_RENDERER
    width: int = DEFAULT_WIDTH
    height: int = DEFAULT_HEIGHT
    max_words: int = DEFAULT_MAX_WORDS
    output_dir: str = str(PROFILE_IMG_OUTPUT_DIR)
    layout_readability: LayoutReadabilitySettings = LayoutReadabilitySettings()


class WordCloudGenerator:
    """Minimal generator class expected by the CLI."""

    def __init__(self, **kwargs):
        self.settings = (
            kwargs.get("settings") or kwargs.get("base_settings") or WordCloudSettings()
        )

    def generate(
        self,
        frequencies: Mapping[str, int | float] | None = None,
        output_path: str | Path | None = None,
        source: str = "topics",
        **kwargs,
    ) -> Path:
        renderer = kwargs.get(
            "renderer", getattr(self.settings, "renderer", DEFAULT_RENDERER)
        )
        width = getattr(self.settings, "width", DEFAULT_WIDTH)
        height = getattr(self.settings, "height", DEFAULT_HEIGHT)
        max_words = kwargs.get(
            "max_words", getattr(self.settings, "max_words", DEFAULT_MAX_WORDS)
        )
        color_func_name = kwargs.get("color_func_name")
        layout_readability = kwargs.get(
            "layout_readability",
            getattr(self.settings, "layout_readability", None),
        )

        explicit_output = Path(output_path) if output_path is not None else None
        if explicit_output is not None and explicit_output.suffix:
            out_file = explicit_output
            out_dir = out_file.parent
        else:
            out_dir = explicit_output or Path(self.settings.output_dir)
            ext = ".png" if renderer == "classic" else ".svg"
            out_file = out_dir / f"wordcloud_by_{source}{ext}"

        out_dir.mkdir(parents=True, exist_ok=True)

        if frequencies:
            normalized_frequencies = _limit_frequencies(
                _filter_others(frequencies),
                max_words,
            )
            if renderer == "classic":
                _generate_classic(
                    normalized_frequencies,
                    out_file,
                    width=width,
                    height=height,
                    max_words=max_words,
                )
            else:
                _generate_svg(
                    renderer,
                    normalized_frequencies,
                    out_file,
                    width=width,
                    height=height,
                    color_func_name=color_func_name,
                    layout_readability=layout_readability,
                )
            return out_file
        else:
            # Fall back to reading from markdown
            return generate_word_cloud(
                source=source,
                renderer=renderer,
                max_words=max_words,
                output_dir=str(out_dir),
                color_func_name=color_func_name,
                layout_readability=layout_readability,
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate word clouds")
    parser.add_argument(
        "--renderer",
        choices=RENDERER_CHOICES,
        default=DEFAULT_RENDERER,
        help="Renderer backend (default: classic)",
    )
    parser.add_argument(
        "--source",
        choices=["topics", "languages", "both"],
        default="both",
        help="Which markdown source to use (default: both)",
    )
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument("--output-dir", type=str, default=None)
    args = parser.parse_args()

    # Ensure the renderers module is importable
    if str(_SCRIPT_DIR) not in sys.path:
        sys.path.insert(0, str(_SCRIPT_DIR))

    if args.source == "both":
        outputs = generate_all(
            renderer=args.renderer,
            width=args.width,
            height=args.height,
            output_dir=args.output_dir,
        )
    else:
        out = generate_word_cloud(
            source=args.source,
            renderer=args.renderer,
            width=args.width,
            height=args.height,
            output_dir=args.output_dir,
        )
        outputs = [out]

    logger.info("Done. {count} file(s) generated.", count=len(outputs))


if __name__ == "__main__":
    main()
