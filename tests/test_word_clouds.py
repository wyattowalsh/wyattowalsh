from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.word_cloud_renderers import (
    WordleRenderer,
    resolve_preferred_wordcloud_font_path,
)
from scripts.word_clouds import (
    _filter_others,
    WordCloudGenerator,
    WordCloudSettings,
    parse_markdown_for_word_cloud_frequencies,
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

    # The parser extracts links from the first UL as topic names and counts
    # entries in subsequent ULs
    assert frequencies["python"] == 2
    assert frequencies["others"] == 2
    assert "mcp" not in frequencies
    assert "video" not in frequencies
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

    # The parser extracts link text from the first UL as topic names, but
    # with only one UL there are no subsequent ULs to count entries from,
    # so the result is empty.
    assert frequencies == {}


def test_parse_markdown_missing_file_raises(tmp_path: Path) -> None:
    missing_file = tmp_path / "missing.md"

    with pytest.raises(FileNotFoundError):
        parse_markdown_for_word_cloud_frequencies(missing_file)


@patch("subprocess.run")
def test_resolve_preferred_wordcloud_font_path_prefers_monaspace(
    mock_run: MagicMock,
) -> None:
    """Test that resolve_preferred_wordcloud_font_path finds MonaspaceNeon first."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "/usr/share/fonts/MonaspaceNeon-Bold.ttf: "
    mock_run.return_value = mock_result

    resolved = resolve_preferred_wordcloud_font_path()

    assert resolved == "/usr/share/fonts/MonaspaceNeon-Bold.ttf"
    # First call should be for MonaspaceNeon
    first_call_args = mock_run.call_args_list[0]
    assert "MonaspaceNeon" in first_call_args[0][0][1]


@patch("subprocess.run")
def test_resolve_preferred_wordcloud_font_path_fallback_chain(
    mock_run: MagicMock,
) -> None:
    """Test fallback to Montserrat, and None when nothing found."""
    # Simulate MonaspaceNeon not found, Monaspace Neon not found, Montserrat found
    mock_not_found = MagicMock()
    mock_not_found.returncode = 0
    mock_not_found.stdout = ""

    mock_montserrat = MagicMock()
    mock_montserrat.returncode = 0
    mock_montserrat.stdout = "/usr/share/fonts/Montserrat-Bold.ttf: "

    mock_run.side_effect = [mock_not_found, mock_not_found, mock_montserrat]

    resolved = resolve_preferred_wordcloud_font_path()
    assert resolved == "/usr/share/fonts/Montserrat-Bold.ttf"

    # When nothing is found at all, returns None
    mock_run.side_effect = [mock_not_found, mock_not_found, mock_not_found]
    assert resolve_preferred_wordcloud_font_path() is None


def test_filter_others_removes_variants() -> None:
    """_filter_others strips 'others', 'Others', 'other' but keeps real words."""
    freqs = {"python": 10, "others": 500, "Others": 200, "other": 50, "another": 5}
    filtered = _filter_others(freqs)
    assert "others" not in filtered
    assert "Others" not in filtered
    assert "other" not in filtered
    assert filtered["python"] == 10
    assert filtered["another"] == 5


def test_all_words_placed_wordle() -> None:
    """WordleRenderer must place every word on a sufficiently large canvas."""
    words = {f"word{i}": max(1, 100 - i) for i in range(80)}
    renderer = WordleRenderer(width=1600, height=1000, color_func_name="rainbow")
    placed = renderer.place_words(words)
    placed_texts = {pw.text for pw in placed}
    assert placed_texts == set(words.keys()), (
        f"Missing words: {set(words.keys()) - placed_texts}"
    )


def test_generator_honors_explicit_output_path_and_filters_others(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_generate_svg(
        renderer_name: str,
        frequencies: dict[str, int],
        output_path: str | Path,
        width: int = 0,
        height: int = 0,
        **kwargs,
    ) -> None:
        captured["renderer"] = renderer_name
        captured["frequencies"] = dict(frequencies)
        captured["output_path"] = Path(output_path)
        captured["color_func_name"] = kwargs.get("color_func_name")
        Path(output_path).write_text("<svg />", encoding="utf-8")

    monkeypatch.setattr("scripts.word_clouds._generate_svg", fake_generate_svg)

    generator = WordCloudGenerator(
        base_settings=WordCloudSettings(
            renderer="clustered",
            output_dir=str(tmp_path),
        )
    )
    output_path = tmp_path / "custom.svg"

    result = generator.generate(
        frequencies={"Python": 3, "others": 99},
        output_path=output_path,
        source="topics",
        color_func_name="gradient",
    )

    assert result == output_path
    assert captured["renderer"] == "clustered"
    assert captured["frequencies"] == {"Python": 3}
    assert captured["output_path"] == output_path
    assert captured["color_func_name"] == "gradient"
    assert output_path.exists()
