from xml.etree import ElementTree as ET

import pytest
from pydantic import ValidationError

from scripts.word_clouds import (
    WordCloudGenerator,
    WordCloudSettings,
    generate_word_cloud,
)
from scripts.word_clouds.colors import resolve_color_func
from scripts.word_clouds.wordle import WordleRenderer


def test_palette_tokenization_option_present():
    """Settings expose the implemented palette tokenization policy."""
    # Pydantic v2 uses model_fields for introspection.
    model_fields = getattr(WordCloudSettings, "model_fields", {})
    assert "palette_tokenization" in model_fields, (
        "Expected 'palette_tokenization' setting for stronger palette tokenization"
    )


def test_palette_tokenization_controls_color_cardinality():
    continuous = resolve_color_func(
        "primary_color_func",
        tokenization="none",
        palette_override=["#000000", "#ffffff"],
    )
    coarse = resolve_color_func("primary", tokenization="coarse")
    strong = resolve_color_func("primary", tokenization="strong")

    assert continuous(1, 3) == "#808080"
    assert len({coarse(index, 40) for index in range(40)}) == 8
    assert len({strong(index, 40) for index in range(40)}) == 4


def test_palette_tokenization_default_is_consistent_across_entrypoints():
    settings = WordCloudSettings()
    renderer = WordleRenderer()
    direct_color_func = resolve_color_func("primary")

    assert settings.palette_tokenization == "coarse"
    assert renderer.palette_tokenization == "coarse"
    assert len({direct_color_func(index, 40) for index in range(40)}) == 8


@pytest.mark.parametrize(
    ("overrides", "expected_message"),
    [
        ({"custom_color_func_name": "missing"}, "Unknown color function"),
        ({"color_palette_override": ["red"]}, "#RRGGBB"),
        ({"palette_tokenization": "maximum"}, "palette_tokenization"),
        ({"unknown_option": True}, "unknown_option"),
    ],
)
def test_override_settings_are_strictly_validated(overrides, expected_message):
    generator = WordCloudGenerator()

    with pytest.raises(ValidationError, match=expected_message):
        generator.generate(frequencies={"Python": 1}, override_settings_dict=overrides)


def test_output_filename_override_rejects_paths(tmp_path):
    generator = WordCloudGenerator()

    with pytest.raises(ValueError, match="bare filename"):
        generator.generate(
            frequencies={"Python": 1},
            override_settings_dict={
                "output_dir": tmp_path,
                "output_filename": "nested/cloud.svg",
            },
        )


@pytest.mark.parametrize(
    "overrides",
    [
        {"style_variant": "topic"},
        {"color_palette_override": ["#111111"]},
        {"custom_color_func_name": "primary"},
        {"palette_tokenization": "strong"},
    ],
)
def test_classic_renderer_rejects_svg_only_style_controls(tmp_path, overrides):
    generator = WordCloudGenerator(
        base_settings=WordCloudSettings(output_dir=tmp_path),
    )

    with pytest.raises(ValueError, match="SVG-native renderer"):
        generator.generate(
            frequencies={"Python": 1},
            output_path=tmp_path / "cloud.png",
            override_settings_dict=overrides,
        )


def test_classic_renderer_rejects_direct_color_func(tmp_path):
    generator = WordCloudGenerator(
        base_settings=WordCloudSettings(output_dir=tmp_path),
    )

    with pytest.raises(ValueError, match="SVG-native renderer"):
        generator.generate(
            frequencies={"Python": 1},
            output_path=tmp_path / "cloud.png",
            color_func_name="primary",
        )


def test_classic_renderer_rejects_direct_layout_readability(tmp_path):
    generator = WordCloudGenerator(
        base_settings=WordCloudSettings(output_dir=tmp_path),
    )

    with pytest.raises(ValueError, match="SVG-native renderer"):
        generator.generate(
            frequencies={"Python": 1},
            output_path=tmp_path / "cloud.png",
            layout_readability={},
        )


def test_high_level_classic_renderer_rejects_unsupported_style_options(tmp_path):
    with pytest.raises(ValueError, match="SVG-native renderer"):
        generate_word_cloud(
            source="topics",
            renderer="classic",
            output_dir=tmp_path,
            color_func_name="primary",
        )


def test_markdown_fallback_preserves_explicit_output_target(tmp_path, monkeypatch):
    captured: dict[str, object] = {}

    def fake_parse(_md_path):
        return {"Python": 3}

    def fake_generate_classic(frequencies, output_path, **_kwargs):
        captured["frequencies"] = dict(frequencies)
        captured["output_path"] = output_path
        output_path.write_bytes(b"PNG")

    monkeypatch.setattr(
        "scripts.word_clouds.generate.parse_frequencies_from_md",
        fake_parse,
    )
    monkeypatch.setattr(
        "scripts.word_clouds.generate._generate_classic",
        fake_generate_classic,
    )
    generator = WordCloudGenerator()
    expected = tmp_path / "from-markdown.png"

    result = generator.generate(frequencies=None, output_path=expected)

    assert result == expected
    assert captured == {
        "frequencies": {"Python": 3},
        "output_path": expected,
    }


def test_layout_readability_knobs_present():
    """RED test for layout and readability tuning knobs."""
    model_fields = getattr(WordCloudSettings, "model_fields", {})
    assert "layout_readability" in model_fields, (
        "Expected 'layout_readability' setting for layout/readability tuning"
    )


def test_topic_vs_language_output_style_distinct(tmp_path):
    """Per-call overrides produce distinct, semantically identified SVGs."""
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

    assert 'id="wordcloud-topic"' in topic_svg, "Expected topic-style id in SVG"
    assert 'id="wordcloud-language"' in lang_svg, "Expected language-style id in SVG"
    topic_colors = {
        element.attrib["fill"].lower()
        for element in ET.fromstring(topic_svg).iter()
        if element.tag.endswith("text")
    }
    lang_colors = {
        element.attrib["fill"].lower()
        for element in ET.fromstring(lang_svg).iter()
        if element.tag.endswith("text")
    }
    assert topic_colors <= {"#111", "#1a1a1a", "#222"}
    assert lang_colors <= {"#aaa", "#b2b2b2", "#bbb"}
    assert topic_colors.isdisjoint(lang_colors)
    assert gen.settings.style_variant == "default"
    assert gen.settings.color_palette_override is None
