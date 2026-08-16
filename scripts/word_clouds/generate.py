"""Word cloud generation with multiple renderer backends.

Supports two modes:
  - "typographic" (default): fit-all SVG sized by starred-repo volume
  - "classic": bitmap PNG via the ``wordcloud`` library (legacy)
  - "wordle" | "clustered" | "shaped" | "metaheuristic-anim": other SVG engines

Usage:
    python -m scripts.word_clouds                          # typographic SVG
    python -m scripts.word_clouds --renderer wordle        # SVG wordle
    python -m scripts.word_clouds --renderer all           # every renderer
"""

from __future__ import annotations

import argparse
import html
import re
import sys
import xml.etree.ElementTree as ET
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..utils import get_logger
from .colors import COLOR_FUNCS, PaletteTokenization, normalize_color_func_name
from .readability import LayoutReadabilitySettings

logger = get_logger(module=__name__)

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

RendererName = Literal[
    "classic",
    "wordle",
    "clustered",
    "typographic",
    "shaped",
    "fractal",
    "metaheuristic-anim",
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
    "fractal",
    "metaheuristic-anim",
    "all",
]

# Shipped profile clouds: CI `generate word-cloud --from-*-md` inherits this
# via WordCloudSettings / generate_word_cloud unless a renderer is overridden.
DEFAULT_RENDERER: RendererName = "typographic"
SHIPPED_WORD_CLOUD_SOURCES: tuple[str, str] = ("topics", "languages")
DEFAULT_WIDTH = 1600
DEFAULT_HEIGHT = 520
DEFAULT_MAX_WORDS = 1000

# Resolve project root relative to this script
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent.parent
_ASSETS_DIR = _PROJECT_ROOT / ".github" / "assets" / "img"


# ---------------------------------------------------------------------------
# Markdown parsing helpers
# ---------------------------------------------------------------------------


# Awesome-stars meta headings that are not language/topic categories.
_NON_CATEGORY_HEADINGS = frozenset({"contents", "license"})
# Raw ATX ``##`` only. Do not walk rendered HTML: CommonMark treats a
# trailing ``#`` as a closer, so ``## C#`` / ``## Q#`` become ``C`` / ``Q``.
_ATX_H2_RE = re.compile(r"^##(?!#)\s+(.+?)\s*$")
_TOC_LINK_RE = re.compile(r"^-\s+\[([^\]]+)\]\([^)]+\)")
_LIST_ITEM_RE = re.compile(r"^-\s+")


def parse_frequencies_from_md(md_path: str | Path) -> dict[str, int]:
    """Parse starred-topics/languages markdown into ``{name: starred-repo-count}``.

    The ``scripts.starred_lists`` format starts with a Contents list of
    category names (link text preserves labels such as ``C#`` / ``Q#``),
    then one ``## Category`` section per name whose list items are starred
    repositories. Counts use exact heading-line equality on the source
    (not ``startswith``, not rendered HTML) so prefix-related names stay
    distinct. Values are those per-section repo counts — relative volume
    for font size/weight. Trailing meta headings such as License are
    ignored. An empty category section counts as ``0``.
    """
    text = Path(md_path).read_text(encoding="utf-8")
    toc_names: list[str] = []
    section_counts: dict[str, int] = {}
    current: str | None = None
    in_contents = False
    saw_contents = False

    for line in text.splitlines():
        heading_match = _ATX_H2_RE.match(line)
        if heading_match is not None:
            title = html.unescape(heading_match.group(1).strip())
            folded = title.casefold()
            if folded in _NON_CATEGORY_HEADINGS:
                current = None
                in_contents = folded == "contents"
                saw_contents = saw_contents or in_contents
                continue
            in_contents = False
            current = title
            section_counts[current] = 0
            continue

        if in_contents:
            toc_match = _TOC_LINK_RE.match(line)
            if toc_match is not None:
                toc_names.append(html.unescape(toc_match.group(1)))
            continue

        if current is not None and _LIST_ITEM_RE.match(line):
            section_counts[current] += 1

    if saw_contents:
        return {name: section_counts.get(name, 0) for name in toc_names}
    return dict(section_counts)


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
    style_variant: Literal["default", "topic", "language"] = "default",
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
    out = Path(output_path)
    out.write_text(svg_content, encoding="utf-8")
    # Default SVGO inlines the light fill and drops prefers-color-scheme rules.
    if "prefers-color-scheme" not in svg_content:
        from ..svg_optimize import optimize_with_svgo

        optimize_with_svgo(out)
    if style_variant != "default":
        _set_svg_style_variant(out, style_variant)


def _set_svg_style_variant(
    output_path: Path,
    style_variant: Literal["topic", "language"],
) -> None:
    """Attach a stable semantic identifier to an SVG root element."""

    ET.register_namespace("", "http://www.w3.org/2000/svg")
    tree = ET.parse(output_path)
    root = tree.getroot()
    if root.tag.rsplit("}", 1)[-1] != "svg":
        raise ValueError(f"Expected SVG root element in {output_path}")
    root.set("id", f"wordcloud-{style_variant}")
    root.set("data-style-variant", style_variant)
    tree.write(output_path, encoding="unicode", xml_declaration=False)


def _default_output_filename(source: str, renderer: str) -> str:
    """Return the canonical output filename for the requested renderer."""

    if renderer == "classic":
        return f"wordcloud_by_{source}.png"
    return f"wordcloud_{renderer}_by_{source}.svg"


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
    palette_tokenization: PaletteTokenization = "coarse",
    color_palette_override: list[str] | None = None,
    style_variant: Literal["default", "topic", "language"] = "default",
) -> Path:
    """Generate a word cloud for the given source and renderer.

    Parameters
    ----------
    color_func_name:
        Name of the OKLCH color palette to use (e.g. "sunset", "neon",
        "gradient").  When *None*, a sensible default is chosen based on
        *source*: ``"ocean"`` for topics, ``"aurora"`` for languages.

    Returns the path to the generated file.
    """
    if output_dir is None:
        output_dir = _ASSETS_DIR
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Resolve input file
    md_file = _PROJECT_ROOT / ".github" / "assets" / f"{source}.md"
    if not md_file.exists():
        md_file = _PROJECT_ROOT / f"{source}.md"
    frequencies = _limit_frequencies(
        _filter_others(parse_frequencies_from_md(md_file)),
        max_words,
    )

    out = output_dir / _default_output_filename(source, renderer)

    if renderer == "classic":
        if (
            style_variant != "default"
            or color_palette_override is not None
            or palette_tokenization != "coarse"
            or color_func_name is not None
            or layout_readability is not None
        ):
            raise ValueError(
                "style, color, palette tokenization, and layout readability "
                "controls require an SVG-native renderer"
            )
        _generate_classic(
            frequencies,
            out,
            width=width,
            height=height,
            max_words=max_words,
        )
    else:
        if color_func_name is None:
            color_func_name = _SOURCE_COLOR_DEFAULTS.get(source, "gradient")
        extra: dict[str, object] = {}
        if renderer == "fractal":
            extra["shape"] = "koch" if source == "topics" else "dragon"
        _generate_svg(
            renderer,
            frequencies,
            out,
            width=width,
            height=height,
            color_func_name=color_func_name,
            layout_readability=layout_readability,
            palette_tokenization=palette_tokenization,
            color_palette_override=color_palette_override,
            style_variant=style_variant,
            **extra,
        )

    return out


def generate_all(
    renderer: str = DEFAULT_RENDERER,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    output_dir: str | Path | None = None,
) -> list[Path]:
    """Generate the shipped topics + languages clouds.

    The public default is exactly two SVGs (typographic × those sources).
    If renderer is ``"all"``, also writes every local renderer variant.
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
        for source in SHIPPED_WORD_CLOUD_SOURCES:
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
    """Runtime settings for word cloud generation.

    Prefer constructing from YAML via :meth:`from_yaml_model` rather than
    hand-copying overlapping fields from ``WordCloudSettingsModel``.
    """

    model_config = ConfigDict(extra="forbid")
    renderer: str = DEFAULT_RENDERER
    width: int = DEFAULT_WIDTH
    height: int = DEFAULT_HEIGHT
    max_words: int = DEFAULT_MAX_WORDS
    output_dir: str | Path = str(PROFILE_IMG_OUTPUT_DIR)
    layout_readability: LayoutReadabilitySettings = LayoutReadabilitySettings()
    palette_tokenization: PaletteTokenization = "coarse"
    style_variant: Literal["default", "topic", "language"] = "default"
    custom_color_func_name: str | None = None
    color_palette_override: list[str] | None = Field(default=None, min_length=1)
    max_solvers: int | None = None
    max_iter: int | None = None

    @field_validator("custom_color_func_name")
    @classmethod
    def _validate_custom_color_func_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = normalize_color_func_name(value)
        if normalized not in COLOR_FUNCS:
            supported = ", ".join(sorted(COLOR_FUNCS))
            raise ValueError(
                f"Unknown color function {value!r}; choose one of: {supported}"
            )
        return value

    @field_validator("color_palette_override")
    @classmethod
    def _validate_color_palette_override(
        cls,
        value: list[str] | None,
    ) -> list[str] | None:
        if value is None:
            return None
        invalid = [
            color for color in value if not re.fullmatch(r"#[0-9a-fA-F]{6}", color)
        ]
        if invalid:
            raise ValueError("color_palette_override entries must use #RRGGBB syntax")
        return value

    @classmethod
    def from_yaml_model(
        cls,
        model: Any | None = None,
        **overrides: object,
    ) -> WordCloudSettings:
        """Build runtime settings from YAML ``WordCloudSettingsModel``.

        Shared fields: ``output_dir``, ``max_words``, ``layout_readability``.
        YAML-only fields (``prompt``, ``stopwords``, ``output_filename``) are
        ignored here. Non-``None`` *overrides* take precedence.
        """
        data: dict[str, Any] = {}
        if model is not None:
            data["output_dir"] = model.output_dir
            data["max_words"] = model.max_words
            data["layout_readability"] = model.layout_readability
        data.update({k: v for k, v in overrides.items() if v is not None})
        return cls(**data)

    def to_yaml_model(self, **yaml_only: object) -> Any:
        """Project runtime settings back onto YAML ``WordCloudSettingsModel``.

        Generator-only fields (``renderer``, ``width``, ``height``, …) are
        dropped. Pass YAML-only extras (``prompt``, ``stopwords``, …) as kwargs.
        """
        from ..config import WordCloudSettingsModel

        data: dict[str, Any] = {
            "output_dir": self.output_dir,
            "max_words": self.max_words,
            "layout_readability": self.layout_readability,
        }
        data.update({k: v for k, v in yaml_only.items() if v is not None})
        return WordCloudSettingsModel(**data)


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
        override_settings_dict: Mapping[str, object] | None = None,
        **kwargs,
    ) -> Path:
        override_data = dict(override_settings_dict or {})
        output_filename_value = override_data.pop("output_filename", None)
        if output_filename_value is not None and not isinstance(
            output_filename_value, str
        ):
            raise TypeError("output_filename override must be a string")

        active_settings = WordCloudSettings.model_validate(
            {**self.settings.model_dump(), **override_data}
        )
        renderer_explicit = "renderer" in override_data or "renderer" in kwargs
        color_func_explicit = (
            "color_func_name" in kwargs
            or active_settings.custom_color_func_name is not None
        )
        layout_readability_explicit = (
            "layout_readability" in kwargs or "layout_readability" in override_data
        )
        renderer = kwargs.get("renderer", active_settings.renderer)
        width = active_settings.width
        height = active_settings.height
        max_words = kwargs.get("max_words", active_settings.max_words)
        color_func_name = kwargs.get(
            "color_func_name",
            active_settings.custom_color_func_name,
        )
        if color_func_name is None:
            color_func_name = _SOURCE_COLOR_DEFAULTS.get(source, "gradient")
        layout_readability = kwargs.get(
            "layout_readability",
            active_settings.layout_readability,
        )

        explicit_output = Path(output_path) if output_path is not None else None
        if explicit_output is not None and explicit_output.suffix:
            out_file = explicit_output
            out_dir = out_file.parent
        else:
            out_dir = explicit_output or Path(active_settings.output_dir)
            if output_filename_value is None:
                out_file = out_dir / _default_output_filename(source, renderer)
            else:
                requested_filename = Path(output_filename_value)
                if requested_filename.name != output_filename_value:
                    raise ValueError("output_filename override must be a bare filename")
                out_file = out_dir / requested_filename

        if out_file.suffix.lower() == ".svg" and renderer == "classic":
            if renderer_explicit:
                raise ValueError("The classic renderer cannot write SVG output")
            renderer = "wordle"
        elif out_file.suffix.lower() == ".png" and renderer != "classic":
            if renderer_explicit:
                raise ValueError("SVG-native renderers cannot write PNG output")
            renderer = "classic"
        elif out_file.suffix.lower() not in {".png", ".svg"}:
            raise ValueError("Word-cloud output filename must end in .png or .svg")

        if renderer == "classic" and (
            active_settings.style_variant != "default"
            or active_settings.color_palette_override is not None
            or active_settings.palette_tokenization != "coarse"
            or color_func_explicit
            or layout_readability_explicit
        ):
            raise ValueError(
                "style, color, palette tokenization, and layout readability "
                "controls require an SVG-native renderer"
            )

        out_dir.mkdir(parents=True, exist_ok=True)

        if frequencies is not None:
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
                extra_kwargs = {}
                if active_settings.max_solvers is not None:
                    extra_kwargs["max_solvers"] = active_settings.max_solvers
                if active_settings.max_iter is not None:
                    extra_kwargs["max_iter"] = active_settings.max_iter
                for font_key in ("min_font_size", "max_font_size", "padding"):
                    if font_key in kwargs and kwargs[font_key] is not None:
                        extra_kwargs[font_key] = kwargs[font_key]
                _generate_svg(
                    renderer,
                    normalized_frequencies,
                    out_file,
                    width=width,
                    height=height,
                    color_func_name=color_func_name,
                    layout_readability=layout_readability,
                    palette_tokenization=active_settings.palette_tokenization,
                    color_palette_override=active_settings.color_palette_override,
                    style_variant=active_settings.style_variant,
                    **extra_kwargs,
                )
            return out_file
        else:
            md_file = _PROJECT_ROOT / ".github" / "assets" / f"{source}.md"
            if not md_file.exists():
                md_file = _PROJECT_ROOT / f"{source}.md"
            parsed_frequencies = _limit_frequencies(
                _filter_others(parse_frequencies_from_md(md_file)),
                max_words,
            )
            fallback_kwargs: dict[str, object] = {}
            if renderer != "classic":
                fallback_kwargs = {
                    "color_func_name": color_func_name,
                    "layout_readability": layout_readability,
                }
            return self.generate(
                frequencies=parsed_frequencies,
                output_path=out_file,
                source=source,
                override_settings_dict={
                    **override_data,
                    "renderer": renderer,
                },
                **fallback_kwargs,
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate word clouds")
    parser.add_argument(
        "--renderer",
        choices=RENDERER_CHOICES,
        default=DEFAULT_RENDERER,
        help="Renderer backend (default: typographic)",
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
