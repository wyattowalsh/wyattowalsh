"""Word cloud generation with multiple renderer backends.

Supports two modes:
  - "classic": bitmap PNG via the ``wordcloud`` library (original behavior)
  - "wordle" | "clustered" | "typographic" | "shaped": SVG-native renderers

Usage:
    python scripts/word_clouds.py                          # classic PNG
    python scripts/word_clouds.py --renderer wordle        # SVG wordle
    python scripts/word_clouds.py --renderer all           # every renderer
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Literal

import markdown
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

RendererName = Literal["classic", "wordle", "clustered", "typographic", "shaped"]

RENDERER_CHOICES: list[str] = [
    "classic", "wordle", "clustered", "typographic", "shaped", "all",
]

DEFAULT_RENDERER: RendererName = "classic"
DEFAULT_WIDTH = 800
DEFAULT_HEIGHT = 500
DEFAULT_MAX_WORDS = 1000

# Resolve project root relative to this script
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
_ASSETS_DIR = _PROJECT_ROOT / "assets"


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
    if first_ul is None:
        return {}
    topics = [a.text for a in first_ul.find_all("a")]
    all_uls = soup.find_all("ul")[1:]
    entries = [len(ul.find_all("li")) for ul in all_uls]
    return dict(zip(topics, entries))


# ---------------------------------------------------------------------------
# Classic (bitmap) renderer
# ---------------------------------------------------------------------------

def _generate_classic(
    frequencies: dict[str, int],
    output_path: str | Path,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    max_words: int = DEFAULT_MAX_WORDS,
) -> None:
    """Original wordcloud-library PNG generation."""
    from wordcloud import WordCloud

    wc = WordCloud(
        background_color=None,
        max_words=max_words,
        width=width,
        height=height,
        scale=4,
        mode="RGBA",
        relative_scaling=0,
        colormap="jet",
        contour_color="white",
    )
    wc.generate_from_frequencies(frequencies)
    wc.to_file(str(output_path))


# ---------------------------------------------------------------------------
# SVG renderer dispatch
# ---------------------------------------------------------------------------

def _generate_svg(
    renderer_name: str,
    frequencies: dict[str, int],
    output_path: str | Path,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    **renderer_kwargs,
) -> None:
    """Generate an SVG word cloud using one of the SVG-native renderers."""
    from word_cloud_renderers import get_renderer

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

def generate_word_cloud(
    source: Literal["topics", "languages"],
    renderer: str = DEFAULT_RENDERER,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    output_dir: str | Path | None = None,
) -> Path:
    """Generate a word cloud for the given source and renderer.

    Returns the path to the generated file.
    """
    if output_dir is None:
        output_dir = _ASSETS_DIR
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Resolve input file
    md_file = _PROJECT_ROOT / f"{source}.md"
    frequencies = parse_frequencies_from_md(md_file)

    if renderer == "classic":
        ext = ".png"
        out = output_dir / f"wordcloud_by_{source}{ext}"
        _generate_classic(frequencies, out, width=width, height=height)
    else:
        ext = ".svg"
        out = output_dir / f"wordcloud_{renderer}_by_{source}{ext}"
        _generate_svg(renderer, frequencies, out, width=width, height=height)

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
        ["classic", "wordle", "clustered", "typographic", "shaped"]
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
            print(f"  Generated: {out}")
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
# CLI
# ---------------------------------------------------------------------------

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

    print(f"\nDone. {len(outputs)} file(s) generated.")


if __name__ == "__main__":
    main()
