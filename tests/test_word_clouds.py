import math
import random
import re
from html import unescape
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import scripts.word_clouds.generate as generate_module
import scripts.word_clouds.metaheuristic as metaheuristic_module
import scripts.word_clouds.typographic as typographic_module
from scripts.word_clouds import (
    DEFAULT_RENDERER,
    LayoutReadabilitySettings,
    WordCloudGenerator,
    WordCloudSettings,
    _filter_others,
    parse_markdown_for_word_cloud_frequencies,
)
from scripts.word_clouds.clustered import ClusteredRenderer
from scripts.word_clouds.colors import (
    AA_LARGE_TEXT_CONTRAST,
    GITHUB_DARK_BG,
    GITHUB_LIGHT_BG,
    contrast_ratio,
    github_readable_fills,
    is_github_dual_surface_readable,
)
from scripts.word_clouds.core import PlacedWord, resolve_preferred_wordcloud_font_path
from scripts.word_clouds.metaheuristic import RENDERERS, MetaheuristicAnimRenderer
from scripts.word_clouds.shaped import ShapedRenderer
from scripts.word_clouds.solvers import (
    _aesthetic_cost,
    _mealpy_solve,
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
    renderer = MetaheuristicAnimRenderer(
        width=1200,
        height=800,
        color_func_name="ocean",
    )

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
    renderer = MetaheuristicAnimRenderer(
        width=1200,
        height=800,
        color_func_name="aurora",
    )
    frequencies = {f"Topic{i}": float(300 - i) for i in range(180)}
    frequencies["others"] = 999.0

    texts, sizes, freqs, colors, weights, opacities = renderer._prepare_words(
        frequencies
    )

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
    assert settings.layout_readability.standard_rotations.count(0.0) > (
        settings.layout_readability.standard_rotations.count(90.0)
    )


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


def test_typographic_phyllotaxis_is_not_a_two_column_magazine() -> None:
    """Exotic packer fans words around a spiral, not two ragged columns."""
    frequencies = {f"term-{i:02d}": float(40 - i) for i in range(18)}
    placed = TypographicRenderer(
        width=800,
        height=500,
        min_font_size=10.0,
        max_font_size=36.0,
        seed=3,
    ).place_words(frequencies)
    assert {word.text for word in placed} == set(frequencies)
    xs = [word.x for word in placed]
    ys = [word.y for word in placed]
    assert max(xs) - min(xs) > 120
    assert max(ys) - min(ys) > 80
    # A two-column magazine pack collapses x into a pair of gutters.
    x_buckets = {round(x / 80.0) for x in xs}
    assert len(x_buckets) >= 3
    assert any(abs(word.rotation) >= 6 for word in placed)


def test_typographic_remainder_is_not_a_left_gutter_stack() -> None:
    """Packed leftovers should not pile up in the left 15% of the banner."""
    frequencies = {f"label-{i:02d}": float(30 - i) for i in range(28)}
    placed = TypographicRenderer(
        width=1600,
        height=560,
        min_font_size=8.0,
        max_font_size=42.0,
        seed=4,
    ).place_words(frequencies)
    assert {word.text for word in placed} == set(frequencies)
    xs = [word.x for word in placed]
    left = sum(1 for x in xs if x < 1600 * 0.15)
    assert left / len(xs) < 0.45
    assert max(xs) > 1600 * 0.55


def test_typographic_snaps_unreadable_cluster_fill(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Default palettes that miss canvas AA are replaced with a readable fill."""
    monkeypatch.setitem(
        typographic_module.CLUSTER_PALETTES,
        "Other",
        ["#EEEEEE"],
    )
    placed = TypographicRenderer(
        width=400,
        height=240,
        min_font_size=10.0,
        max_font_size=20.0,
        seed=1,
    ).place_words({"zzzz-unknown": 4.0})
    assert placed
    assert placed[0].color != "#EEEEEE"
    assert is_github_dual_surface_readable(placed[0].color)


def test_typographic_renderer_keeps_horizontal_layout() -> None:
    renderer = TypographicRenderer(width=1200, height=800)
    placed = renderer.place_words({"Python": 5.0, "Go": 3.0, "Docker": 2.0})

    assert placed
    assert all(word.rotation == 0 for word in placed)


def test_typographic_places_every_term_large_vocab() -> None:
    """Fit-all packer must surface the full vocabulary on the public canvas."""
    words = {f"topic-{i:03d}": float(max(1, 400 - i)) for i in range(322)}
    renderer = TypographicRenderer(
        width=1600,
        height=520,
        min_font_size=8.0,
        max_font_size=42.0,
        require_all=True,
    )
    placed = renderer.place_words(words)
    assert {pw.text for pw in placed} == set(words.keys())
    assert all(pw.opacity == 1.0 for pw in placed)
    assert all(pw.font_size >= 8.0 for pw in placed)


def test_typographic_default_canvas_is_wide_landscape() -> None:
    """Public typographic clouds should read as stacked README banners."""
    renderer = TypographicRenderer()
    assert renderer.width == 1600
    assert renderer.height == 560
    assert renderer.width / renderer.height >= 2.5
    assert renderer.min_font_size >= 8.0
    assert generate_module.DEFAULT_WIDTH == 1600
    assert generate_module.DEFAULT_HEIGHT == 560


def test_typographic_constellation_uses_phyllotaxis_not_columns() -> None:
    """Top-frequency terms sit on a sunflower spiral, not a two-column grid."""
    renderer = TypographicRenderer(
        width=1600,
        height=520,
        min_font_size=8.0,
        max_font_size=48.0,
        seed=7,
    )
    frequencies = {f"Term{index:02d}": float(90 - index * 4) for index in range(18)}
    placed = renderer.place_words(frequencies)
    assert {word.text for word in placed} == set(frequencies)
    assert all(word.opacity == 1.0 for word in placed)
    assert all(word.font_size >= 8.0 for word in placed)
    headlines = sorted(placed, key=lambda word: word.font_size, reverse=True)[:3]
    assert all(word.rotation == 0 for word in headlines)

    slots = renderer._phyllotaxis_positions(12, 800.0, 260.0, 18.0)
    assert len(slots) == 12
    origin_radius = math.hypot(slots[0][0] - 800.0, slots[0][1] - 260.0)
    outer_radius = math.hypot(slots[-1][0] - 800.0, slots[-1][1] - 260.0)
    assert origin_radius < outer_radius

    arch = list(renderer._archimedean_positions(100.0, 50.0, step=4.0, max_steps=6))
    assert arch[0] == pytest.approx((100.0, 50.0))
    assert math.hypot(arch[-1][0] - 100.0, arch[-1][1] - 50.0) > 0.0

    split = renderer._constellation_count(len(frequencies))
    top = sorted(placed, key=lambda word: word.font_size, reverse=True)[:split]
    xs = [word.x for word in top]
    ys = [word.y for word in top]
    assert max(xs) - min(xs) > renderer.width * 0.12
    assert max(ys) - min(ys) > renderer.height * 0.10
    x_buckets = {round(x / 48.0) for x in xs}
    assert len(x_buckets) >= 3

    fills = {word.color.casefold() for word in placed}
    allowed = {color.casefold() for color in github_readable_fills()}
    assert fills <= allowed
    for word in placed:
        assert is_github_dual_surface_readable(word.color, opacity=word.opacity)


def test_metaheuristic_place_words_passes_word_sizes_to_readability_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    renderer = MetaheuristicAnimRenderer(
        width=1200,
        height=800,
        layout_readability=LayoutReadabilitySettings(),
    )
    captured: dict[str, object] = {}

    def fake_configure(layout_readability, *, word_sizes=None):
        captured["layout_readability"] = layout_readability
        captured["word_sizes"] = list(word_sizes or [])

    def fake_solve(
        n_words: int,
        sizes: list[float],
        canvas_w: float,
        canvas_h: float,
        max_iter: int,
        rng: random.Random,
        texts: list[str] | None = None,
        pop_size: int | None = None,
    ) -> list[tuple[float, float, float]]:
        return [(100.0, 120.0, 0.0)] * n_words

    def fake_render_frame(
        name: str,
        positions: list[tuple[float, float, float]],
        texts: list[str],
        sizes: list[float],
        colors: list[str],
        weights: list[int],
        opacities: list[float],
    ) -> list[PlacedWord]:
        return [
            PlacedWord(
                text=texts[index],
                font_size=sizes[index],
                x=positions[index][0],
                y=positions[index][1],
                rotation=positions[index][2],
                color=colors[index],
                font_weight=weights[index],
                opacity=opacities[index],
            )
            for index in range(len(texts))
        ]

    monkeypatch.setattr(
        metaheuristic_module,
        "configure_layout_readability",
        fake_configure,
    )
    # Patch all solvers in _META_SOLVERS to use the fake
    fake_solvers = {name: fake_solve for name in metaheuristic_module._META_SOLVERS}
    monkeypatch.setattr(metaheuristic_module, "_META_SOLVERS", fake_solvers)
    monkeypatch.setattr(renderer, "_render_frame", fake_render_frame)

    placed = renderer.place_words({"Python": 9.0, "Go": 3.0})

    assert {word.text for word in placed} == {"python", "go"}
    assert captured["layout_readability"] == renderer.layout_readability
    assert captured["word_sizes"] == [72.0, 7.0]


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


def test_generator_uses_renderer_specific_default_filename_for_svg_frequencies(
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
        captured["renderer"] = renderer_name
        captured["output_path"] = Path(output_path)
        Path(output_path).write_text("<svg />", encoding="utf-8")

    monkeypatch.setattr("scripts.word_clouds.generate._generate_svg", fake_generate_svg)

    generator = WordCloudGenerator(
        base_settings=WordCloudSettings(
            renderer="clustered",
            output_dir=str(tmp_path),
        )
    )

    result = generator.generate(
        frequencies={"Python": 4, "Go": 2},
        source="topics",
    )

    expected = tmp_path / "wordcloud_clustered_by_topics.svg"
    assert result == expected
    assert captured["renderer"] == "clustered"
    assert captured["output_path"] == expected
    assert expected.exists()


def test_run_solver_always_passes_pop_size(
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
        cost_weights: dict[str, float] | None = None,
    ) -> list[tuple[float, float, float]]:
        captured["pop_size"] = pop_size
        captured["cost_weights"] = cost_weights
        return [(100.0, 100.0, 0.0)] * n_words

    monkeypatch.setitem(
        metaheuristic_module._META_SOLVERS,
        "Particle Swarm",
        fake_solver,
    )

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
            None,
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
        args: tuple[
            str,
            int,
            list[float],
            float,
            float,
            int,
            int,
            int | None,
            list[str],
            object,
            dict[str, float] | None,
        ],
    ) -> tuple[str, list[tuple[float, float, float]]]:
        name, n_words, *_ = args
        call_counts[name] = call_counts.get(name, 0) + 1
        if name == "OriginalHS" and call_counts[name] == 1:
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
    monkeypatch.setattr(
        metaheuristic_module,
        "as_completed",
        lambda futures: list(futures),
    )

    results = renderer._solve_all(["python", "go"], [72.0, 12.0])
    result_names = {name for name, _ in results}

    assert "OriginalHS" in result_names
    assert call_counts["OriginalHS"] == 2


def test_mealpy_solve_produces_valid_placement() -> None:
    """Integration test: _mealpy_solve with a real mealpy optimizer."""
    from mealpy.swarm_based.PSO import OriginalPSO

    configure_layout_readability()
    n_words = 3
    sizes = [30.0, 20.0, 15.0]
    texts = ["alpha", "beta", "gamma"]
    canvas_w, canvas_h = 400.0, 300.0
    rng = random.Random(42)

    result = _mealpy_solve(
        OriginalPSO,
        n_words,
        sizes,
        canvas_w,
        canvas_h,
        max_iter=20,
        rng=rng,
        texts=texts,
        pop_size=10,
    )

    assert len(result) == n_words
    margin_x = canvas_w * 0.15
    margin_y = canvas_h * 0.15
    for x, y, rot in result:
        assert margin_x <= x <= canvas_w - margin_x
        assert margin_y <= y <= canvas_h - margin_y
        # rotation should be snapped to a valid value
        assert isinstance(rot, float)

    cost = _aesthetic_cost(result, sizes, canvas_w, canvas_h, texts)
    assert cost < float("inf")
    assert cost >= 0.0


def test_mealpy_solve_fallback_on_bad_optimizer() -> None:
    """_mealpy_solve falls back to random solution on optimizer failure."""

    configure_layout_readability()

    class _BrokenOptimizer:
        def __init__(self, **kwargs):
            raise RuntimeError("intentional failure")

    rng = random.Random(99)
    result = _mealpy_solve(
        _BrokenOptimizer,
        3,
        [20.0, 15.0, 10.0],
        400.0,
        300.0,
        max_iter=10,
        rng=rng,
    )
    # Should get a valid random fallback, not an exception
    assert len(result) == 3
    for x, y, rot in result:
        assert isinstance(x, float)


def test_parse_starred_markdown_maps_names_to_repo_counts(tmp_path: Path) -> None:
    """Contents labels pair with per-section starred-repo list lengths."""
    markdown_file = tmp_path / "languages.md"
    markdown_file.write_text(
        """
## Contents
- [C](#c)
- [C#](#c-1)
- [Python](#python)
- [Others](#others)

## C
- [org/libc](https://example.com/libc)
- [org/kernel](https://example.com/kernel)

## C#
- [org/runtime](https://example.com/runtime)

## Python
- [org/cpython](https://example.com/cpython)
- [org/django](https://example.com/django)
- [org/flask](https://example.com/flask)

## Others
- [org/misc](https://example.com/misc)

## License
- leftover list must not become a category
""".strip(),
        encoding="utf-8",
    )

    frequencies = parse_markdown_for_word_cloud_frequencies(markdown_file)
    assert frequencies == {"C": 2, "C#": 1, "Python": 3, "Others": 1}
    filtered = _filter_others(frequencies)
    assert filtered == {"C": 2, "C#": 1, "Python": 3}
    assert filtered["Python"] > filtered["C"] > filtered["C#"]


def test_parse_starred_markdown_empty_section_does_not_shift_counts(
    tmp_path: Path,
) -> None:
    markdown_file = tmp_path / "topics.md"
    markdown_file.write_text(
        """
## Contents
- [python](#python)
- [go](#go)
- [rust](#rust)

## python
- [org/one](https://example.com/one)

## go

## rust
- [org/two](https://example.com/two)
- [org/three](https://example.com/three)
""".strip(),
        encoding="utf-8",
    )

    frequencies = parse_markdown_for_word_cloud_frequencies(markdown_file)
    assert frequencies == {"python": 1, "go": 0, "rust": 2}


def _raw_heading_item_count(markdown: str, heading: str) -> int:
    """Count list items under an exact ``## heading`` line (not a prefix)."""
    marker = f"## {heading}"
    count = 0
    in_section = False
    for line in markdown.splitlines():
        if line.startswith("## "):
            in_section = line == marker
            continue
        if in_section and line.startswith("- "):
            count += 1
    return count


def test_parse_starred_markdown_uses_exact_heading_not_prefix(
    tmp_path: Path,
) -> None:
    """C / C# / C++ / Q# stay distinct even when section order != TOC order."""
    markdown_file = tmp_path / "languages.md"
    markdown_file.write_text(
        """
## Contents
- [C](#c)
- [C#](#c-1)
- [C++](#c-2)
- [Q#](#q)

## Q#
- [org/qsharp](https://example.com/q)

## C++
- [org/cpp-one](https://example.com/cpp-one)
- [org/cpp-two](https://example.com/cpp-two)
- [org/cpp-three](https://example.com/cpp-three)

## C#
- [org/csharp](https://example.com/csharp)

## C
- [org/c-one](https://example.com/c-one)
- [org/c-two](https://example.com/c-two)

## License
- leftover list must not become a category
""".strip(),
        encoding="utf-8",
    )

    frequencies = parse_markdown_for_word_cloud_frequencies(markdown_file)
    assert frequencies == {"C": 2, "C#": 1, "C++": 3, "Q#": 1}
    assert frequencies["C"] != frequencies["C#"]
    assert "Q" not in frequencies


def test_checked_in_starred_lists_parse_as_repo_volume() -> None:
    topics_md = generate_module._PROJECT_ROOT / ".github" / "assets" / "topics.md"
    languages_md = generate_module._PROJECT_ROOT / ".github" / "assets" / "languages.md"
    if not topics_md.is_file() or not languages_md.is_file():
        pytest.skip("checked-in starred lists are not present")

    topics = _filter_others(parse_markdown_for_word_cloud_frequencies(topics_md))
    languages = _filter_others(parse_markdown_for_word_cloud_frequencies(languages_md))

    assert topics
    assert languages
    assert all(isinstance(count, int) and count >= 1 for count in topics.values())
    assert all(isinstance(count, int) and count >= 1 for count in languages.values())
    assert "others" not in {name.casefold() for name in topics}
    assert "other" not in {name.casefold() for name in languages}
    assert max(topics.values()) > min(topics.values())
    assert max(languages.values()) > min(languages.values())
    assert topics["python"] > topics["zig"]
    assert languages["Python"] > languages["Zig"]

    language_source = languages_md.read_text(encoding="utf-8")
    for heading in ("C", "C#", "C++", "Q#"):
        assert heading in languages
        assert languages[heading] == _raw_heading_item_count(language_source, heading)
    assert languages["C"] != languages["C#"]
    assert languages["Q#"] != languages.get("Q", 0)


def test_default_renderer_ships_typographic_filenames(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert DEFAULT_RENDERER == "typographic"
    assert WordCloudSettings().renderer == "typographic"
    assert (
        generate_module._default_output_filename("topics", DEFAULT_RENDERER)
        == "wordcloud_typographic_by_topics.svg"
    )
    assert (
        generate_module._default_output_filename("languages", DEFAULT_RENDERER)
        == "wordcloud_typographic_by_languages.svg"
    )

    captured: dict[str, object] = {}

    def fake_generate_svg(
        renderer_name: str,
        frequencies: dict[str, int | float],
        output_path: str | Path,
        width: int = 0,
        height: int = 0,
        **kwargs,
    ) -> None:
        captured["renderer"] = renderer_name
        captured["output_path"] = Path(output_path)
        Path(output_path).write_text("<svg />", encoding="utf-8")

    monkeypatch.setattr(generate_module, "_generate_svg", fake_generate_svg)
    result = WordCloudGenerator(
        base_settings=WordCloudSettings(output_dir=str(tmp_path))
    ).generate(frequencies={"Python": 4, "Go": 1}, source="topics")

    expected = tmp_path / "wordcloud_typographic_by_topics.svg"
    assert result == expected
    assert captured["renderer"] == "typographic"
    assert captured["output_path"] == expected


def test_default_generate_all_ships_exact_two_typographic_svgs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert generate_module.SHIPPED_WORD_CLOUD_SOURCES == ("topics", "languages")
    emitted: list[tuple[str, str]] = []

    def fake_generate_word_cloud(
        source: str,
        renderer: str = DEFAULT_RENDERER,
        **_kwargs: object,
    ) -> Path:
        emitted.append((source, renderer))
        path = tmp_path / generate_module._default_output_filename(source, renderer)
        path.write_text("<svg />", encoding="utf-8")
        return path

    monkeypatch.setattr(
        generate_module,
        "generate_word_cloud",
        fake_generate_word_cloud,
    )
    outputs = generate_module.generate_all(output_dir=tmp_path)
    assert [path.name for path in outputs] == [
        "wordcloud_typographic_by_topics.svg",
        "wordcloud_typographic_by_languages.svg",
    ]
    assert emitted == [("topics", "typographic"), ("languages", "typographic")]
    assert len(outputs) == 2


def test_typographic_higher_count_is_larger_or_heavier() -> None:
    frequencies = {"High": 50.0, "Mid": 12.0, "Low": 1.0}
    placed = TypographicRenderer(
        width=420,
        height=240,
        min_font_size=8.0,
        max_font_size=48.0,
        require_all=True,
    ).place_words(frequencies)
    by_text = {word.text: word for word in placed}
    assert set(by_text) == set(frequencies)

    high, mid, low = by_text["High"], by_text["Mid"], by_text["Low"]
    assert high.font_size > mid.font_size > low.font_size
    assert high.font_weight >= mid.font_weight >= low.font_weight
    assert high.opacity >= mid.opacity >= low.opacity
    assert high.rotation == mid.rotation == low.rotation == 0


def _spearman(xs: list[float], ys: list[float]) -> float:
    def ranks(values: list[float]) -> list[float]:
        order = sorted(range(len(values)), key=lambda index: values[index])
        result = [0.0] * len(values)
        index = 0
        while index < len(values):
            end = index
            while (
                end + 1 < len(values) and values[order[end + 1]] == values[order[index]]
            ):
                end += 1
            average = (index + end) / 2 + 1
            for tied in range(index, end + 1):
                result[order[tied]] = average
            index = end + 1
        return result

    rx, ry = ranks(xs), ranks(ys)
    n = len(xs)
    mean_x = sum(rx) / n
    mean_y = sum(ry) / n
    num = sum((a - mean_x) * (b - mean_y) for a, b in zip(rx, ry, strict=True))
    den_x = math.sqrt(sum((a - mean_x) ** 2 for a in rx))
    den_y = math.sqrt(sum((b - mean_y) ** 2 for b in ry))
    if den_x == 0.0 or den_y == 0.0:
        return 0.0
    return num / (den_x * den_y)


def test_svg_engine_bakeoff_typographic_best_encodes_volume() -> None:
    """Typographic wins (or ties) volume fidelity among fast SVG engines."""
    frequencies = {
        "Python": 100.0,
        "TypeScript": 64.0,
        "Go": 36.0,
        "Rust": 16.0,
        "Zig": 9.0,
        "Nim": 4.0,
        "Haml": 2.0,
        "Tcl": 1.0,
    }
    engines = {
        "wordle": WordleRenderer(
            width=400,
            height=260,
            min_font_size=8.0,
            max_font_size=48.0,
            seed=42,
        ),
        "clustered": ClusteredRenderer(
            width=400,
            height=260,
            min_font_size=8.0,
            max_font_size=48.0,
            seed=42,
            show_cluster_labels=False,
        ),
        "typographic": TypographicRenderer(
            width=400,
            height=260,
            min_font_size=8.0,
            max_font_size=48.0,
            seed=42,
        ),
        "shaped": ShapedRenderer(
            width=400,
            height=260,
            min_font_size=8.0,
            max_font_size=48.0,
            seed=42,
            shape="circle",
        ),
    }
    assert set(engines).issubset(RENDERERS)

    scores: dict[str, float] = {}
    for name, renderer in engines.items():
        placed = {word.text: word for word in renderer.place_words(frequencies)}
        assert set(placed) == set(frequencies)
        labels = list(frequencies)
        scores[name] = _spearman(
            [frequencies[label] for label in labels],
            [placed[label].font_size for label in labels],
        )

    winner_score = max(scores.values())
    assert scores["typographic"] == winner_score
    assert scores["typographic"] >= 0.99
    typographic_placed = engines["typographic"].place_words(frequencies)
    headlines = sorted(
        typographic_placed, key=lambda word: word.font_size, reverse=True
    )[:4]
    assert all(word.rotation == 0 for word in headlines)


_SHIPPED_TYPOGRAPHIC_CLOUDS = (
    Path(".github/assets/img/wordcloud_typographic_by_topics.svg"),
    Path(".github/assets/img/wordcloud_typographic_by_languages.svg"),
)
# Pre-repair cluster fills still present on committed SVGs until CI regenerates.
_SHIPPED_LEGACY_TEXT_FILLS = frozenset(
    {
        "#06b6d4",
        "#10b981",
        "#155e75",
        "#1d4ed8",
        "#1e40af",
        "#1f2937",
        "#22d3ee",
        "#34d399",
        "#374151",
        "#4b5563",
        "#5b21b6",
        "#60a5fa",
        "#6d28d9",
        "#831843",
        "#92400e",
        "#991b1b",
        "#9ca3af",
        "#9d174d",
        "#a78bfa",
        "#b91c1c",
        "#f472b6",
        "#f59e0b",
        "#f87171",
        "#fbbf24",
    }
)


def _svg_text_fills(svg: str) -> set[str]:
    return {
        match.casefold()
        for match in re.findall(r"<text\b[^>]*fill=\"(#[0-9A-Fa-f]{6})\"", svg)
    }


def _svg_text_opacities(svg: str) -> list[float]:
    return [
        float(value)
        for value in re.findall(
            r"<text\b[^>]*opacity=\"([0-9.]+)\"",
            svg,
        )
    ]


def test_fact_wordcloud_bakeoff_typographic_readable_on_github_light_and_dark() -> None:
    """fact-wordcloud-bakeoff: shipped typographic winners stay readable on GitHub."""
    current_fills = {color.casefold() for color in github_readable_fills()}
    allowed_fills = current_fills | _SHIPPED_LEGACY_TEXT_FILLS
    for color in github_readable_fills():
        assert is_github_dual_surface_readable(color), (
            f"{color} is below WCAG AA large-text contrast on GitHub light/dark"
        )
        for background in (GITHUB_LIGHT_BG, GITHUB_DARK_BG):
            assert contrast_ratio(color, background) >= AA_LARGE_TEXT_CONTRAST, (
                f"{color} vs {background} is below WCAG AA large-text contrast"
            )

    for path in _SHIPPED_TYPOGRAPHIC_CLOUDS:
        assert path.is_file(), f"missing shipped typographic cloud: {path}"
        svg = path.read_text(encoding="utf-8")
        assert "rotate(" in svg
        assert 'stop-color="#fafbfc"' in svg
        assert 'stop-color="#f0f1f3"' in svg
        assert 'fill="url(#wc-bg-grad)"' in svg
        assert "url(#wc-bg-grad-dark)" in svg
        assert "@media (prefers-color-scheme: dark)" in svg
        fills = _svg_text_fills(svg)
        assert fills
        assert fills <= allowed_fills
        opacities = _svg_text_opacities(svg)
        if opacities:
            assert min(opacities) >= 0.6


def test_fact_wordclouds_size_follows_starred_share() -> None:
    """fact-wordclouds: exactly two clouds; size follows starred-repo share."""
    assert DEFAULT_RENDERER == "typographic"
    assert generate_module.SHIPPED_WORD_CLOUD_SOURCES == ("topics", "languages")
    topics_md = generate_module._PROJECT_ROOT / ".github" / "assets" / "topics.md"
    languages_md = generate_module._PROJECT_ROOT / ".github" / "assets" / "languages.md"
    assert topics_md.is_file() and languages_md.is_file()
    sources = (
        (_SHIPPED_TYPOGRAPHIC_CLOUDS[0], topics_md),
        (_SHIPPED_TYPOGRAPHIC_CLOUDS[1], languages_md),
    )
    for path, markdown in sources:
        assert path.is_file()
        frequencies = _filter_others(
            parse_markdown_for_word_cloud_frequencies(markdown)
        )
        svg = path.read_text(encoding="utf-8")
        placed: dict[str, float] = {}
        for match in re.finditer(r"<text\b([^>]*)>([^<]+)</text>", svg):
            size_match = re.search(r'font-size="([0-9.]+)"', match.group(1))
            if size_match is None:
                continue
            placed[unescape(match.group(2)).casefold()] = float(size_match.group(1))
        overlap = [word for word in frequencies if word.casefold() in placed]
        assert len(overlap) >= 8, path.name
        rho = _spearman(
            [float(frequencies[word]) for word in overlap],
            [placed[word.casefold()] for word in overlap],
        )
        assert rho >= 0.8, f"{path.name} volume Spearman {rho}"


def test_fact_wordcloud_bakeoff_shipped_fills_contrast_on_github() -> None:
    """fact-wordcloud-bakeoff: shipped winners keep dark media + AA fills."""
    current_fills = {color.casefold() for color in github_readable_fills()}
    allowed_fills = current_fills | _SHIPPED_LEGACY_TEXT_FILLS
    for path in _SHIPPED_TYPOGRAPHIC_CLOUDS:
        svg = path.read_text(encoding="utf-8")
        assert "@media (prefers-color-scheme: dark)" in svg
        fills = _svg_text_fills(svg)
        assert fills, path.name
        assert fills <= allowed_fills
        for color in fills & current_fills:
            assert is_github_dual_surface_readable(color), (
                f"{path.name} {color} is below GitHub dual-surface AA"
            )


def test_fact_wordcloud_bakeoff_typographic_generate_is_dual_surface() -> None:
    """fact-wordcloud-bakeoff: the winner emits GitHub-readable light/dark fills."""
    frequencies = {
        "pytorch": 40.0,
        "react": 32.0,
        "python": 28.0,
        "docker": 18.0,
        "markdown": 12.0,
        "security": 9.0,
        "terraform": 6.0,
        "zig": 2.0,
    }
    renderer = TypographicRenderer(
        width=640,
        height=360,
        min_font_size=10.0,
        max_font_size=42.0,
        seed=7,
    )
    placed = renderer.place_words(frequencies)
    assert {word.text for word in placed} == set(frequencies)
    headlines = sorted(placed, key=lambda word: word.font_size, reverse=True)[:3]
    assert all(word.rotation == 0 for word in headlines)
    assert all(word.opacity == 1.0 for word in placed)
    for word in placed:
        assert is_github_dual_surface_readable(word.color, opacity=word.opacity), (
            f"{word.text} fill {word.color} fails GitHub light/dark AA"
        )

    svg = renderer.generate(frequencies)
    assert "@media (prefers-color-scheme: dark)" in svg
    assert "url(#wc-bg-grad-dark)" in svg
    fills = _svg_text_fills(svg)
    assert fills
    assert fills <= {color.casefold() for color in github_readable_fills()}
    assert not _svg_text_opacities(svg)
