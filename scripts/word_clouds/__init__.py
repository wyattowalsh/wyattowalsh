"""Word cloud generation subpackage.

Re-exports public API from submodules for backward compatibility.
All existing ``from scripts.word_clouds import X`` imports continue to work.
"""

from __future__ import annotations

# -- Generation pipeline (formerly word_clouds.py) --------------------------
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
from .readability import LayoutReadabilityPolicy, LayoutReadabilitySettings

__all__ = [
    # Generation pipeline
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
