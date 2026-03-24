from pathlib import Path
import random
from unittest.mock import MagicMock, patch

import pytest

import scripts.word_clouds.metaheuristic as metaheuristic_module
from scripts.word_clouds import (
    LayoutReadabilitySettings,
    WordCloudGenerator,
    WordCloudSettings,
    _filter_others,
    parse_markdown_for_word_cloud_frequencies,
)
from scripts.word_clouds.core import resolve_preferred_wordcloud_font_path
from scripts.word_clouds.metaheuristic import MetaheuristicAnimRenderer
from scripts.word_clouds.solvers import (
    _aesthetic_cost,
    _random_solution,
    configure_layout_readability,
)
from scripts.word_clouds.typographic import TypographicRenderer
from scripts.word_clouds.wordle import WordleRenderer


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


def test_metaheuristic_prepare_words_lowercases_and_filters_generic_buckets() -> None:
    renderer = MetaheuristicAnimRenderer(width=1200, height=800, color_func_name="ocean")

    texts, sizes, freqs, colors, weights, opacities = renderer._prepare_words(
        {"Python": 3, "OTHER": 10, "Go": 2, "Others": 7}
    )

    assert texts == ["python", "go"]
    assert freqs == [3, 2]
    assert len(sizes) == len(texts)
    assert len(colors) == len(texts)
    assert len(weights) == len(texts)
    assert len(opacities) == len(texts)


def test_metaheuristic_prepare_words_keeps_all_non_others_items() -> None:
    renderer = MetaheuristicAnimRenderer(width=1200, height=800, color_func_name="aurora")
    frequencies = {f"Topic{i}": float(300 - i) for i in range(180)}
    frequencies["others"] = 999.0

    texts, sizes, freqs, colors, weights, opacities = renderer._prepare_words(frequencies)

    assert len(texts) == 180
    assert len(set(texts)) == 180
    assert all(text == text.lower() for text in texts)
    assert len(sizes) == 180
    assert len(freqs) == 180
    assert len(colors) == 180
    assert len(weights) == 180
    assert len(opacities) == 180


def test_metaheuristic_place_words_returns_empty_for_only_generic_buckets() -> None:
    renderer = MetaheuristicAnimRenderer(width=1200, height=800)

    assert renderer.place_words({"other": 5, "Others": 3}) == []


def test_wordcloud_settings_include_layout_readability() -> None:
    settings = WordCloudSettings()

    assert isinstance(settings.layout_readability, LayoutReadabilitySettings)
    assert settings.layout_readability.target_aspect_ratio > 1.0
    assert settings.layout_readability.standard_rotations.count(0.0) > settings.layout_readability.standard_rotations.count(90.0)


def test_aesthetic_cost_prefers_horizontal_landscape_layout() -> None:
    sizes = [72.0, 56.0, 42.0]
    texts = ["python", "docker", "aws"]

    readable = [
        (420.0, 380.0, 0.0),
        (620.0, 380.0, 0.0),
        (820.0, 380.0, 0.0),
    ]
    unreadable = [
        (620.0, 200.0, 90.0),
        (620.0, 400.0, 90.0),
        (620.0, 600.0, 90.0),
    ]

    assert _aesthetic_cost(readable, sizes, 1200.0, 800.0, texts) < _aesthetic_cost(
        unreadable, sizes, 1200.0, 800.0, texts
    )


def test_random_solution_uses_large_word_rotation_policy() -> None:
    settings = LayoutReadabilitySettings(
        standard_rotations=[90.0],
        large_word_rotations=[0.0],
        large_word_threshold_ratio=0.5,
    )

    try:
        configure_layout_readability(settings, word_sizes=[72.0, 12.0])
        solution = _random_solution(2, 1200.0, 800.0, random.Random(0))
    finally:
        configure_layout_readability()

    assert solution[0][2] == 0.0
    assert solution[1][2] == 90.0


def test_typographic_renderer_keeps_horizontal_layout() -> None:
    renderer = TypographicRenderer(width=1200, height=800)
    placed = renderer.place_words({"Python": 5.0, "Go": 3.0, "Docker": 2.0})

    assert placed
    assert all(word.rotation == 0 for word in placed)


def test_all_words_placed_wordle() -> None:
    """WordleRenderer must place every word on a sufficiently large canvas."""
    words = {f"word{i}": float(max(1, 100 - i)) for i in range(80)}
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

    monkeypatch.setattr("scripts.word_clouds.generate._generate_svg", fake_generate_svg)

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


def test_generator_limits_svg_frequencies_to_max_words(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_generate_svg(
        renderer_name: str,
        frequencies: dict[str, int | float],
        output_path: str | Path,
        width: int = 0,
        height: int = 0,
        **kwargs,
    ) -> None:
        captured["frequencies"] = dict(frequencies)
        Path(output_path).write_text("<svg />", encoding="utf-8")

    monkeypatch.setattr("scripts.word_clouds.generate._generate_svg", fake_generate_svg)

    generator = WordCloudGenerator(
        base_settings=WordCloudSettings(
            renderer="clustered",
            output_dir=str(tmp_path),
            max_words=2,
        )
    )

    generator.generate(
        frequencies={"Python": 10, "Rust": 8, "Go": 6},
        output_path=tmp_path / "limited.svg",
        source="topics",
    )

    assert captured["frequencies"] == {"Python": 10, "Rust": 8}


def test_run_solver_passes_pop_size_to_population_tuned_solver(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_solver(
        n_words: int,
        sizes: list[float],
        canvas_w: float,
        canvas_h: float,
        max_iter: int,
        rng: random.Random,
        texts: list[str] | None = None,
        pop_size: int | None = None,
    ) -> list[tuple[float, float, float]]:
        captured["pop_size"] = pop_size
        return [(100.0, 100.0, 0.0)] * n_words

    monkeypatch.setitem(metaheuristic_module._META_SOLVERS, "Particle Swarm", fake_solver)

    name, placements = metaheuristic_module._run_solver(
        (
            "Particle Swarm",
            2,
            [72.0, 12.0],
            1200.0,
            800.0,
            10,
            7,
            123,
            ["python", "go"],
            LayoutReadabilitySettings(),
        )
    )

    assert name == "Particle Swarm"
    assert len(placements) == 2
    assert captured["pop_size"] == 7


def test_metaheuristic_solver_failures_retry_locally(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    renderer = MetaheuristicAnimRenderer(width=800, height=600, max_iter=5, pop_size=4)
    call_counts: dict[str, int] = {}

    def fake_run_solver(
        args: tuple[str, int, list[float], float, float, int, int, int | None, list[str], object],
    ) -> tuple[str, list[tuple[float, float, float]]]:
        name, n_words, *_ = args
        call_counts[name] = call_counts.get(name, 0) + 1
        if name == "Harmony Search" and call_counts[name] == 1:
            raise RuntimeError("worker boom")
        return name, [(100.0, 100.0, 0.0)] * n_words

    class FakeFuture:
        def __init__(self, fn, args) -> None:
            self._fn = fn
            self._args = args

        def result(self):
            return self._fn(self._args)

    class FakeExecutor:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

        def submit(self, fn, args):
            return FakeFuture(fn, args)

    monkeypatch.setattr(metaheuristic_module, "_run_solver", fake_run_solver)
    monkeypatch.setattr(metaheuristic_module, "ProcessPoolExecutor", FakeExecutor)
    monkeypatch.setattr(metaheuristic_module, "as_completed", lambda futures: list(futures))

    results = renderer._solve_all(["python", "go"], [72.0, 12.0])
    result_names = {name for name, _ in results}

    assert "Harmony Search" in result_names
    assert call_counts["Harmony Search"] == 2
