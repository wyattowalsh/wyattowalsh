"""Word cloud generation subpackage.

Expose the public API lazily so unrelated commands can import
``scripts.config`` without pulling in optional word-cloud dependencies.
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

from .readability import LayoutReadabilityPolicy, LayoutReadabilitySettings

if TYPE_CHECKING:
    from .generate import (
        DEFAULT_FONT_PATH,
        DEFAULT_HEIGHT,
        DEFAULT_MAX_WORDS,
        DEFAULT_RENDERER,
        DEFAULT_WIDTH,
        LANGUAGES_MD_PATH,
        PROFILE_IMG_OUTPUT_DIR,
        RENDERER_CHOICES,
        TOPICS_MD_PATH,
        RendererName,
        WordCloudGenerator,
        WordCloudSettings,
        _filter_others,
        generate_all,
        generate_word_cloud,
        get_languages_word_cloud,
        get_topics_word_cloud,
        main,
        parse_frequencies_from_md,
        parse_markdown_for_word_cloud_frequencies,
    )

_GENERATE_EXPORTS = {
    "DEFAULT_FONT_PATH",
    "DEFAULT_HEIGHT",
    "DEFAULT_MAX_WORDS",
    "DEFAULT_RENDERER",
    "DEFAULT_WIDTH",
    "LANGUAGES_MD_PATH",
    "PROFILE_IMG_OUTPUT_DIR",
    "RENDERER_CHOICES",
    "TOPICS_MD_PATH",
    "RendererName",
    "WordCloudGenerator",
    "WordCloudSettings",
    "_filter_others",
    "generate_all",
    "generate_word_cloud",
    "get_languages_word_cloud",
    "get_topics_word_cloud",
    "main",
    "parse_frequencies_from_md",
    "parse_markdown_for_word_cloud_frequencies",
}

__all__ = [
    "DEFAULT_FONT_PATH",
    "DEFAULT_HEIGHT",
    "DEFAULT_MAX_WORDS",
    "DEFAULT_RENDERER",
    "DEFAULT_WIDTH",
    "LANGUAGES_MD_PATH",
    "PROFILE_IMG_OUTPUT_DIR",
    "RENDERER_CHOICES",
    "TOPICS_MD_PATH",
    "RendererName",
    "WordCloudGenerator",
    "WordCloudSettings",
    "LayoutReadabilityPolicy",
    "LayoutReadabilitySettings",
    "_filter_others",
    "generate_all",
    "generate_word_cloud",
    "get_languages_word_cloud",
    "get_topics_word_cloud",
    "main",
    "parse_frequencies_from_md",
    "parse_markdown_for_word_cloud_frequencies",
]


def __getattr__(name: str) -> Any:
    if name not in _GENERATE_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    generate_module = import_module(".generate", __name__)
    value = getattr(generate_module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
