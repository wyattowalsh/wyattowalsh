from pathlib import Path

import pytest

from scripts.word_clouds import (
    parse_markdown_for_word_cloud_frequencies,
    resolve_preferred_wordcloud_font_path,
)


def test_parse_markdown_skips_generic_others_bucket(tmp_path: Path) -> None:
    markdown_file = tmp_path / "topics.md"
    markdown_file.write_text(
        """
## Contents
- [python](#python)
- [others](#others)

## python
- [org/repo-one](https://example.com/repo-one)
- [org/repo-two](https://example.com/repo-two)

## others
- [org/mcp-server](https://example.com/mcp-server)
- [org/video-enhancement](https://example.com/video-enhancement)
""".strip(),
        encoding="utf-8",
    )

    frequencies = parse_markdown_for_word_cloud_frequencies(markdown_file)

    assert frequencies["python"] == 2.0
    assert "mcp" not in frequencies
    assert "video" not in frequencies
    assert "other" not in frequencies
    assert "others" not in frequencies
    assert frequencies == parse_markdown_for_word_cloud_frequencies(markdown_file)


def test_parse_markdown_fallback_filters_other_terms(tmp_path: Path) -> None:
    markdown_file = tmp_path / "languages.md"
    markdown_file.write_text(
        """
- Python
- Others
- [JavaScript](https://example.com/javascript)
- other
""".strip(),
        encoding="utf-8",
    )

    frequencies = parse_markdown_for_word_cloud_frequencies(markdown_file)

    assert frequencies == {"Python": 1.0, "JavaScript": 1.0}


def test_parse_markdown_missing_file_raises(tmp_path: Path) -> None:
    missing_file = tmp_path / "missing.md"

    with pytest.raises(FileNotFoundError):
        parse_markdown_for_word_cloud_frequencies(missing_file)


def test_resolve_preferred_wordcloud_font_path_prefers_monaspace(
    tmp_path: Path,
) -> None:
    fonts_dir = tmp_path / "fonts"
    fonts_dir.mkdir()
    monaspace_font = fonts_dir / "MonaspaceNeon-Bold.ttf"
    monaspace_font.write_bytes(b"font-data")
    (fonts_dir / "Montserrat-ExtraBold.ttf").write_bytes(b"fallback-data")

    resolved = resolve_preferred_wordcloud_font_path(
        fonts_dir=fonts_dir,
        monaspace_variants=["MonaspaceNeon-Bold.ttf"],
        fallback_font="Montserrat-ExtraBold.ttf",
    )

    assert resolved == monaspace_font.resolve()


def test_resolve_preferred_wordcloud_font_path_fallback_chain(
    tmp_path: Path,
) -> None:
    fonts_dir = tmp_path / "fonts"
    fonts_dir.mkdir()
    montserrat_font = fonts_dir / "Montserrat-ExtraBold.ttf"
    montserrat_font.write_bytes(b"fallback-data")

    resolved = resolve_preferred_wordcloud_font_path(
        fonts_dir=fonts_dir,
        monaspace_variants=["MonaspaceArgon-Bold.ttf"],
        fallback_font="Montserrat-ExtraBold.ttf",
    )

    assert resolved == montserrat_font.resolve()

    empty_fonts_dir = tmp_path / "empty-fonts"
    empty_fonts_dir.mkdir()
    assert resolve_preferred_wordcloud_font_path(
        fonts_dir=empty_fonts_dir,
        monaspace_variants=["MonaspaceArgon-Bold.ttf"],
        fallback_font="Montserrat-ExtraBold.ttf",
    ) is None
