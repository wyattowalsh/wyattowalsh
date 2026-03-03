import pytest
from scripts.word_clouds import WordCloudSettings, WordCloudGenerator


def test_palette_tokenization_option_present():
    """RED test: assert a stronger palette tokenization option exists (not implemented)."""
    # Pydantic v2 uses model_fields for field introspection; assert will fail until implemented
    model_fields = getattr(WordCloudSettings, "model_fields", {})
    assert "palette_tokenization" in model_fields, (
        "Expected 'palette_tokenization' setting for stronger palette tokenization"
    )


def test_layout_readability_knobs_present():
    """RED test: assert layout/readability tuning knobs exist on settings (not implemented)."""
    model_fields = getattr(WordCloudSettings, "model_fields", {})
    assert "layout_readability" in model_fields, (
        "Expected 'layout_readability' setting for layout/readability tuning"
    )


def test_topic_vs_language_output_style_distinct(tmp_path):
    """RED test: topic vs language clouds should embed distinct style identifiers in output SVGs."""
    gen = WordCloudGenerator()

    topic_freq = {"Python": 5, "Docker": 3, "AWS": 2}
    lang_freq = {"Python": 5, "JavaScript": 4, "Go": 2}

    topic_path = gen.generate(
        frequencies=topic_freq,
        override_settings_dict={
            "output_dir": tmp_path,
            "output_filename": "topic_wc.svg",
            "style_variant": "topic",
            "custom_color_func_name": "primary_color_func",
            "color_palette_override": ["#111111", "#222222"],
        },
    )

    lang_path = gen.generate(
        frequencies=lang_freq,
        override_settings_dict={
            "output_dir": tmp_path,
            "output_filename": "lang_wc.svg",
            "style_variant": "language",
            "custom_color_func_name": "primary_color_func",
            "color_palette_override": ["#AAAAAA", "#BBBBBB"],
        },
    )

    assert topic_path is not None and topic_path.exists(), "Topic cloud not generated"
    assert lang_path is not None and lang_path.exists(), "Language cloud not generated"

    topic_svg = topic_path.read_text(encoding="utf-8")
    lang_svg = lang_path.read_text(encoding="utf-8")

    # Expect style-specific IDs — feature not implemented yet, so these assertions will fail
    assert 'id="wordcloud-topic"' in topic_svg, "Expected topic-style id in SVG"
    assert 'id="wordcloud-language"' in lang_svg, "Expected language-style id in SVG"
