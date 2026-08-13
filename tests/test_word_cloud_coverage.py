"""High-yield behavioral coverage for word-cloud generation boundaries."""

from __future__ import annotations

import builtins
import importlib
import random
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any, cast

import pytest
import typer

import scripts.word_clouds.colors as colors
import scripts.word_clouds.generate as generate
import scripts.word_clouds.metaheuristic as metaheuristic
import scripts.word_clouds.solvers as solvers
from scripts.word_clouds.clustered import ClusteredRenderer
from scripts.word_clouds.core import PlacedWord
from scripts.word_clouds.metaheuristic import MetaheuristicAnimRenderer
from scripts.word_clouds.readability import (
    LayoutReadabilityPolicy,
    LayoutReadabilitySettings,
    coerce_layout_readability_policy,
)
from scripts.word_clouds.typographic import TypographicRenderer
from scripts.word_clouds.wordle import WordleRenderer

cli_word_cloud = importlib.import_module("scripts.cli.generate.word_cloud")


class _ImmediateFuture:
    def __init__(self, function: Any, argument: Any) -> None:
        self.function = function
        self.argument = argument

    def result(self) -> Any:
        return self.function(self.argument)


class _ImmediateExecutor:
    def __init__(self, *_args: object, **_kwargs: object) -> None:
        pass

    def __enter__(self) -> _ImmediateExecutor:
        return self

    def __exit__(self, *_args: object) -> bool:
        return False

    def submit(self, function: Any, argument: Any) -> _ImmediateFuture:
        return _ImmediateFuture(function, argument)


def _placement(text: str, size: float, rotation: float, opacity: float) -> PlacedWord:
    return PlacedWord(
        text=text,
        x=80.0,
        y=60.0,
        font_size=size,
        rotation=rotation,
        color="#336699",
        font_weight=700,
        opacity=opacity,
    )


def test_metaheuristic_full_animated_pipeline_is_deterministic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    renderer = MetaheuristicAnimRenderer(
        width=320,
        height=220,
        seed=7,
        hold_duration=1.0,
        fade_duration=0.25,
    )
    layouts = [
        ("AlphaSolver", [(70.0, 55.0, 0.0), (180.0, 90.0, 90.0), (95.0, 165.0, 0.0)]),
        ("BetaSolver", [(82.0, 62.0, 0.0), (195.0, 100.0, 0.0), (110.0, 155.0, -6.0)]),
        ("GammaSolver", [(90.0, 68.0, 6.0), (205.0, 108.0, 0.0), (125.0, 145.0, 0.0)]),
    ]
    monkeypatch.setattr(renderer, "_solve_all", lambda _texts, _sizes: layouts)

    svg = renderer.generate(
        {"Alpha": 9.0, "Beta": 4.0, "Gamma": 1.0},
        palette="sunset",
        source="topics",
    )

    assert svg.startswith('<svg xmlns="http://www.w3.org/2000/svg"')
    assert all(name in svg for name, _positions in layouts)
    assert svg.count('class="mf mf') == 3
    assert "@keyframes mf0" in svg
    assert "@keyframes mf2" in svg
    assert "prefers-color-scheme: light" in svg
    assert "wc-glow" in svg
    assert "rotate(" in svg
    assert renderer.color_func_name == "sunset"


def test_metaheuristic_frame_rendering_covers_visual_tiers() -> None:
    renderer = MetaheuristicAnimRenderer(width=300, height=200)
    body = renderer._render_frame_svg_body(
        [
            _placement("large", 80.0, 15.0, 0.8),
            _placement("large-2", 70.0, 0.0, 1.0),
            _placement("large-3", 60.0, 0.0, 1.0),
            _placement("middle", 50.0, 0.0, 1.0),
            _placement("small-1", 40.0, 0.0, 0.9),
            _placement("small-2", 30.0, 0.0, 0.85),
            _placement("small-3", 25.0, 0.0, 0.8),
            _placement("small-4", 20.0, 0.0, 0.75),
            _placement("small-5", 15.0, 0.0, 0.7),
            _placement("small-6", 10.0, 0.0, 0.65),
        ],
        "TierSolver",
        0,
    )
    empty_body = renderer._render_frame_svg_body([], "EmptySolver", 1)

    assert 'filter="url(#wc-glow)"' in body
    assert 'filter="url(#wc-shadow)"' in body
    assert 'opacity="0.80"' in body
    assert 'transform="rotate(15.0,80.0,60.0)"' in body
    assert "TierSolver" in body
    assert "EmptySolver" in empty_body


def test_metaheuristic_solver_environment_and_all_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    renderer = MetaheuristicAnimRenderer(width=300, height=200, max_iter=99)
    monkeypatch.setattr(
        metaheuristic,
        "_META_SOLVERS",
        {"one": lambda *_args, **_kwargs: [], "two": lambda *_args, **_kwargs: []},
    )
    monkeypatch.setattr(metaheuristic, "ProcessPoolExecutor", _ImmediateExecutor)
    monkeypatch.setattr(metaheuristic, "as_completed", lambda futures: list(futures))
    monkeypatch.setenv("WORDCLOUD_MAX_SOLVERS", "1")
    monkeypatch.setenv("WORDCLOUD_MAX_ITER", "7")
    seen_iterations: list[int] = []

    def always_fail(arguments: tuple[Any, ...]) -> tuple[str, list[Any]]:
        seen_iterations.append(arguments[5])
        raise RuntimeError("solver unavailable")

    monkeypatch.setattr(metaheuristic, "_run_solver", always_fail)

    with pytest.raises(RuntimeError, match="All metaheuristic solvers failed"):
        renderer._solve_all(["word"], [24.0])

    assert seen_iterations == [7, 7]


def test_metaheuristic_short_paths_and_factory_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    renderer = MetaheuristicAnimRenderer(width=200, height=100)
    one = [("one", [(10.0, 10.0, 0.0)])]
    two = one + [("two", [(20.0, 20.0, 0.0)])]

    assert renderer._optimize_frame_order(one) == [0]
    assert renderer._optimize_frame_order(two) == [0, 1]
    assert renderer._refine_transitions(two, [10.0], ["word"]) is two
    renderer._log_diversity_baseline(one, [10.0], ["word"])
    assert metaheuristic._frame_hue_offset(0, 1) == 0.0
    assert metaheuristic._frame_hue_offset(1, 3) == 20.0
    assert renderer.place_words({}) == []
    assert renderer.generate({}) == '<svg xmlns="http://www.w3.org/2000/svg"></svg>'
    assert (
        renderer.generate({"others": 1.0})
        == '<svg xmlns="http://www.w3.org/2000/svg"></svg>'
    )
    with pytest.raises(ValueError, match="Unknown renderer"):
        metaheuristic.get_renderer("missing")

    real_import = builtins.__import__

    def reject_mealpy(
        name: str,
        globals: Mapping[str, object] | None = None,
        locals: Mapping[str, object] | None = None,
        fromlist: Sequence[str] | None = (),
        level: int = 0,
    ) -> ModuleType:
        if name == "mealpy":
            raise ImportError("mealpy hidden")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", reject_mealpy)
    assert metaheuristic._build_family_map() == {}

    monkeypatch.setattr(builtins, "__import__", real_import)

    class StandaloneOptimizer:
        pass

    StandaloneOptimizer.__module__ = "standalone"
    fake_mealpy = ModuleType("mealpy")
    setattr(
        fake_mealpy,
        "get_all_optimizers",
        lambda **_kwargs: {"StandaloneOptimizer": StandaloneOptimizer},
    )
    monkeypatch.setitem(sys.modules, "mealpy", fake_mealpy)
    assert metaheuristic._build_family_map() == {"StandaloneOptimizer": "unknown"}


def test_metaheuristic_diagnostics_and_order_improvement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    renderer = MetaheuristicAnimRenderer(width=100, height=80)
    violating = [(-50.0, -50.0, 0.0), (-50.0, -50.0, 0.0)]
    renderer._log_diversity_baseline(
        [("one", violating), ("two", violating)],
        [30.0, 20.0],
        ["alpha", "beta"],
    )

    distances = {
        frozenset((0, 1)): 1.0,
        frozenset((0, 2)): 2.0,
        frozenset((0, 3)): 10.0,
        frozenset((1, 2)): 1.0,
        frozenset((1, 3)): 2.0,
        frozenset((2, 3)): 1.0,
    }

    def layout_distance(
        left: list[tuple[float, float, float]],
        right: list[tuple[float, float, float]],
    ) -> float:
        return distances[frozenset((int(left[0][0]), int(right[0][0])))]

    class PredictableRandom:
        def __init__(self, _seed: int) -> None:
            self.calls = 0

        def randint(self, low: int, _high: int) -> int:
            self.calls += 1
            return low

        def random(self) -> float:
            return 1.0

    monkeypatch.setattr(renderer, "_layout_distance", layout_distance)
    monkeypatch.setattr(metaheuristic.random, "Random", PredictableRandom)
    results = [(str(index), [(float(index), 0.0, 0.0)]) for index in range(4)]
    assert renderer._optimize_frame_order(results) == [1, 0, 2, 3]


def test_color_palettes_conversion_and_tokenization() -> None:
    rendered = {
        name: {function(index, 5) for index in range(5)}
        for name, function in colors.COLOR_FUNCS.items()
    }
    assert set(rendered) == set(colors.COLOR_FUNCS)
    assert all(values for values in rendered.values())
    assert colors.analogous_color_func(2, 4).startswith("#")
    assert colors.complementary_color_func(1, 4).startswith("#")
    assert colors.triadic_color_func(2, 4).startswith("#")

    continuous = colors.resolve_color_func("ocean", tokenization="none")
    explicit = colors.resolve_color_func(
        "missing",
        tokenization="none",
        palette_override=["#000000", "#ffffff"],
    )
    one_token = colors.resolve_color_func(
        "primary", tokenization="strong", palette_override=["#123456"]
    )
    assert continuous(2, 5).startswith("#")
    assert explicit(1, 3) == "#808080"
    assert one_token(7, 10) == "#123456"
    assert colors._tokenized_index(-4, 10, 4) == (0, 4)
    assert colors._tokenized_index(0, 1, 8) == (0, 1)

    lightness, chroma, hue = colors._hex_to_oklch("#336699")
    assert 0.0 < lightness < 1.0
    assert chroma > 0.0
    assert 0.0 <= hue < 360.0
    shifted = colors.make_shifted_color_func("unknown-palette", 45.0)
    assert shifted(1, 3).startswith("#")
    assert colors._srgb_to_linear(0.01) < colors._srgb_to_linear(0.5)


def test_readability_policy_empty_choices_and_coercion() -> None:
    policy = LayoutReadabilityPolicy(
        standard_rotations=(),
        large_word_rotations=(),
        fallback_rotation=12.0,
    )
    assert policy.choose_rotation(random.Random(1)) == 12.0
    assert policy.snap_rotation(30.0) == 12.0
    assert coerce_layout_readability_policy(policy) is policy
    assert (
        coerce_layout_readability_policy(
            LayoutReadabilitySettings(fallback_rotation=7.0)
        ).fallback_rotation
        == 7.0
    )
    assert (
        coerce_layout_readability_policy({"fallback_rotation": 8.0}).fallback_rotation
        == 8.0
    )
    with pytest.raises(TypeError, match="Unsupported layout_readability"):
        coerce_layout_readability_policy(cast(Any, "invalid"))


def test_solver_boundary_helpers_and_wrapper(monkeypatch: pytest.MonkeyPatch) -> None:
    assert solvers._rotation_readability_penalty(90.0) == 1.0
    assert 0.0 < solvers._rotation_readability_penalty(45.0) < 1.0
    assert solvers._landscape_aspect_penalty(0.0, 2.0, 1.8, 1.35) == 1.0
    rotated = solvers._estimate_word_bbox("wide", 20.0, 50.0, 50.0, 45.0)
    assert rotated.w > 0 and rotated.h > 0
    assert solvers._aesthetic_cost([], [], 100.0, 100.0) == 0.0
    assert solvers._aesthetic_cost([(1.0, 1.0, 0.0)], [10.0], 0.0, 100.0) == float(
        "inf"
    )
    assert solvers._aesthetic_cost([(50.0, 50.0, 0.0)], [10.0], 100.0, 100.0) >= 0.0
    fitness = solvers._eval_fitness([(50.0, 50.0, 0.0)], [10.0], 100.0, 100.0)
    assert fitness <= 0.0

    captured: dict[str, object] = {}

    def fake_mealpy(
        *args: object, **kwargs: object
    ) -> list[tuple[float, float, float]]:
        captured["args"] = args
        captured["kwargs"] = kwargs
        return [(20.0, 20.0, 0.0)]

    monkeypatch.setattr(solvers, "_mealpy_solve", fake_mealpy)

    class Optimizer:
        pass

    wrapper = solvers._make_mealpy_solver(Optimizer)
    result = wrapper(1, [10.0], 100.0, 80.0, 3, random.Random(1), ["word"], 2)
    assert result == [(20.0, 20.0, 0.0)]
    assert cast(Any, wrapper).__name__ == "_solve_Optimizer"
    assert captured["args"]


def test_classic_and_svg_dispatch_without_external_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    classic_calls: dict[str, object] = {}

    class FakeWordCloud:
        def __init__(self, **kwargs: object) -> None:
            classic_calls["settings"] = kwargs

        def generate_from_frequencies(
            self, frequencies: dict[str, int | float]
        ) -> None:
            classic_calls["frequencies"] = frequencies

        def to_file(self, output_path: str) -> None:
            Path(output_path).write_bytes(b"PNG")

    fake_module = ModuleType("wordcloud")
    setattr(fake_module, "WordCloud", FakeWordCloud)
    monkeypatch.setitem(sys.modules, "wordcloud", fake_module)
    png = tmp_path / "cloud.png"
    generate._generate_classic({"python": 4}, png, width=200, height=100, max_words=2)
    assert png.read_bytes() == b"PNG"
    assert classic_calls["frequencies"] == {"python": 4}

    class FakeRenderer:
        def generate(self, frequencies: dict[str, int | float]) -> str:
            assert frequencies == {"python": 4}
            return '<svg xmlns="http://www.w3.org/2000/svg"><text>python</text></svg>'

    monkeypatch.setattr(
        metaheuristic, "get_renderer", lambda *_args, **_kwargs: FakeRenderer()
    )
    monkeypatch.setattr("scripts.svg_optimize.optimize_with_svgo", lambda _path: None)
    svg = tmp_path / "cloud.svg"
    generate._generate_svg("wordle", {"python": 4}, svg, style_variant="topic")
    content = svg.read_text(encoding="utf-8")
    assert 'id="wordcloud-topic"' in content
    assert 'data-style-variant="topic"' in content

    invalid = tmp_path / "not-svg.xml"
    invalid.write_text("<root/>", encoding="utf-8")
    with pytest.raises(ValueError, match="Expected SVG root"):
        generate._set_svg_style_variant(invalid, "language")


def test_high_level_generation_all_renderers_and_legacy_entrypoints(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(generate, "_PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(generate, "_ASSETS_DIR", tmp_path / "default-output")
    (tmp_path / "custom.md").write_text("ignored", encoding="utf-8")
    (tmp_path / "topics.md").write_text("ignored", encoding="utf-8")
    monkeypatch.setattr(
        generate, "parse_frequencies_from_md", lambda _path: {"other": 8, "python": 5}
    )
    calls: list[tuple[str, Path, dict[str, object]]] = []

    def fake_svg(
        renderer: str,
        frequencies: dict[str, int | float],
        output: Path,
        **kwargs: object,
    ) -> None:
        calls.append((renderer, output, kwargs))
        assert frequencies == {"python": 5}
        output.write_text("<svg/>", encoding="utf-8")

    def fake_classic(
        frequencies: dict[str, int | float], output: Path, **kwargs: object
    ) -> None:
        calls.append(("classic", output, kwargs))
        assert frequencies == {"python": 5}
        output.write_bytes(b"PNG")

    monkeypatch.setattr(generate, "_generate_svg", fake_svg)
    monkeypatch.setattr(generate, "_generate_classic", fake_classic)

    svg = generate.generate_word_cloud("custom", renderer="wordle")
    png = generate.generate_word_cloud(
        "topics", renderer="classic", output_dir=tmp_path / "png"
    )
    assert svg.name == "wordcloud_wordle_by_custom.svg"
    assert png.name == "wordcloud_by_topics.png"
    assert calls[0][2]["color_func_name"] == "gradient"

    emitted: list[tuple[str, str]] = []

    def fake_generate_word_cloud(
        source: str, renderer: str = "classic", **_kwargs: object
    ) -> Path:
        emitted.append((source, renderer))
        return tmp_path / f"{source}-{renderer}"

    monkeypatch.setattr(generate, "generate_word_cloud", fake_generate_word_cloud)
    outputs = generate.generate_all(renderer="all", output_dir=tmp_path)
    generate.get_topics_word_cloud()
    generate.get_languages_word_cloud()
    assert len(outputs) == 12
    assert emitted[-2:] == [("topics", "classic"), ("languages", "classic")]


def test_generator_output_contract_errors_and_svg_options(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generator = generate.WordCloudGenerator(
        base_settings=generate.WordCloudSettings(output_dir=tmp_path)
    )
    with pytest.raises(TypeError, match="must be a string"):
        generator.generate(
            frequencies={"python": 1},
            override_settings_dict={"output_filename": 3},
        )
    with pytest.raises(ValueError, match="classic renderer cannot write SVG"):
        generator.generate(
            frequencies={"python": 1},
            output_path=tmp_path / "bad.svg",
            renderer="classic",
        )
    with pytest.raises(ValueError, match="cannot write PNG"):
        generator.generate(
            frequencies={"python": 1},
            output_path=tmp_path / "bad.png",
            renderer="wordle",
        )
    with pytest.raises(ValueError, match="must end in"):
        generator.generate(frequencies={"python": 1}, output_path=tmp_path / "bad.txt")

    captured: dict[str, object] = {}

    def fake_svg(*args: object, **kwargs: object) -> None:
        captured["args"] = args
        captured["kwargs"] = kwargs
        Path(cast(str | Path, args[2])).write_text("<svg/>", encoding="utf-8")

    monkeypatch.setattr(generate, "_generate_svg", fake_svg)
    configured = generate.WordCloudGenerator(
        base_settings=generate.WordCloudSettings(
            renderer="wordle",
            output_dir=tmp_path,
            max_solvers=2,
            max_iter=3,
        )
    )
    result = configured.generate(
        frequencies={"other": 8, "python": 5},
        output_path=tmp_path / "configured.svg",
        min_font_size=5.0,
        max_font_size=30.0,
        padding=1.0,
    )
    assert result.exists()
    options = cast(dict[str, object], captured["kwargs"])
    assert options["max_solvers"] == 2
    assert options["max_iter"] == 3
    assert options["min_font_size"] == 5.0

    assert generate._limit_frequencies({"python": 1}, 0) == {}
    monkeypatch.setattr(
        generate,
        "_generate_classic",
        lambda _frequencies, output, **_kwargs: Path(output).write_bytes(b"PNG"),
    )
    inferred = configured.generate(
        frequencies={"python": 1},
        output_path=tmp_path / "inferred.png",
    )
    assert inferred.read_bytes() == b"PNG"


def test_generator_markdown_recursion_and_module_main(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(generate, "_PROJECT_ROOT", tmp_path)
    (tmp_path / "custom.md").write_text("ignored", encoding="utf-8")
    monkeypatch.setattr(
        generate, "parse_frequencies_from_md", lambda _path: {"python": 5}
    )
    monkeypatch.setattr(
        generate,
        "_generate_svg",
        lambda _renderer, _frequencies, output, **_kwargs: Path(output).write_text(
            "<svg/>", encoding="utf-8"
        ),
    )
    generator = generate.WordCloudGenerator(
        base_settings=generate.WordCloudSettings(renderer="wordle", output_dir=tmp_path)
    )
    output = generator.generate(
        frequencies=None,
        source="custom",
        output_path=tmp_path / "recursive.svg",
    )
    assert output.exists()

    generated = [tmp_path / "one.svg", tmp_path / "two.svg"]
    monkeypatch.setattr(generate, "generate_all", lambda **_kwargs: generated)
    monkeypatch.setattr(
        sys, "argv", ["word-cloud", "--renderer", "wordle", "--source", "both"]
    )
    monkeypatch.setattr(
        sys,
        "path",
        [entry for entry in sys.path if entry != str(generate._SCRIPT_DIR)],
    )
    generate.main()
    assert str(generate._SCRIPT_DIR) in sys.path

    monkeypatch.setattr(
        generate, "generate_word_cloud", lambda **_kwargs: tmp_path / "single.svg"
    )
    monkeypatch.setattr(
        sys, "argv", ["word-cloud", "--renderer", "wordle", "--source", "topics"]
    )
    generate.main()


def test_typographic_grid_and_fallback_policies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    renderer = TypographicRenderer(
        width=90,
        height=50,
        min_font_size=7.0,
        max_font_size=72.0,
        scale_passes=1,
    )
    assert renderer._grid_force_all([], 0.0, 0.0) == []
    words = [(f"long-word-{index}", float(300 - index)) for index in range(210)]
    grid = renderer._grid_force_all(words, 1.0, 300.0)
    assert len(grid) == len(words)
    assert all(0 <= word.x <= renderer.width for word in grid)
    assert all(0 <= word.y <= renderer.height for word in grid)

    original_min = renderer.min_font_size
    original_max = renderer.max_font_size
    monkeypatch.setattr(renderer, "_place_at_scale", lambda *_args, **_kwargs: None)
    fallback = renderer.place_words(dict(words))
    assert len(fallback) == len(words)
    assert renderer.min_font_size == original_min
    assert renderer.max_font_size == original_max

    partial_renderer = TypographicRenderer(require_all=False, scale_passes=1)
    monkeypatch.setattr(
        partial_renderer, "_place_at_scale", lambda *_args, **_kwargs: None
    )
    assert partial_renderer.place_words({"word": 1.0}) == []
    assert partial_renderer.place_words({}) == []
    assert partial_renderer._freq_to_weight(1.0, 1.0, 1.0) == 500
    assert partial_renderer._frequency_to_size(1.0, 1.0, 1.0) > 0


@pytest.mark.parametrize("success_call", [2, 7])
def test_wordle_progressive_and_grid_fallbacks(
    success_call: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    renderer = WordleRenderer(
        width=40, height=40, min_font_size=7.0, max_font_size=72.0
    )
    monkeypatch.setattr(
        renderer, "_spiral_positions", lambda *_args, **_kwargs: iter([(20.0, 20.0)])
    )
    monkeypatch.setattr(renderer, "_in_bounds", lambda _bbox: True)
    calls = 0

    def collision(_bbox: object, _placed: object) -> bool:
        nonlocal calls
        calls += 1
        return calls != success_call

    monkeypatch.setattr(renderer, "_check_collision", collision)
    placed = renderer.place_words({"word": 1.0})
    assert [word.text for word in placed] == ["word"]
    if success_call == 2:
        assert placed[0].font_size < 40.0
    else:
        assert placed[0].font_size == 4.0


def test_wordle_absolute_micro_placement(monkeypatch: pytest.MonkeyPatch) -> None:
    renderer = WordleRenderer(width=8, height=8, min_font_size=7.0, max_font_size=20.0)
    monkeypatch.setattr(
        renderer, "_spiral_positions", lambda *_args, **_kwargs: iter([(4.0, 4.0)])
    )
    monkeypatch.setattr(renderer, "_in_bounds", lambda _bbox: True)
    calls = 0

    def collision(_bbox: object, _placed: object) -> bool:
        nonlocal calls
        calls += 1
        return calls > 1

    monkeypatch.setattr(renderer, "_check_collision", collision)
    placed = renderer.place_words({"first": 2.0, "second": 1.0})
    assert {word.text for word in placed} == {"first", "second"}
    assert placed[-1].font_size == 4.0
    assert placed[-1].opacity == 0.55


def test_wordle_configuration_empty_and_densify_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert WordleRenderer(rotation_choices=[12.0]).rotation_choices == [12.0]
    assert WordleRenderer(allow_angled=False).rotation_choices == [0, 90]
    renderer = WordleRenderer(
        width=40,
        height=40,
        min_font_size=7.0,
        max_font_size=20.0,
    )
    assert renderer.place_words({}) == []
    monkeypatch.setattr(
        renderer,
        "_spiral_positions",
        lambda *_args, **_kwargs: iter([(20.0, 20.0)]),
    )
    monkeypatch.setattr(renderer, "_in_bounds", lambda _bbox: True)
    calls = 0

    def collision(_bbox: object, _placed: object) -> bool:
        nonlocal calls
        calls += 1
        return calls not in {1, 29}

    monkeypatch.setattr(renderer, "_check_collision", collision)
    placed = renderer.place_words({"first": 2.0, "second": 1.0})
    assert [word.text for word in placed] == ["first", "second"]
    assert placed[-1].opacity == 0.7


def test_clustered_reduced_size_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    renderer = ClusteredRenderer(
        width=300,
        height=200,
        min_font_size=7.0,
        max_font_size=72.0,
        show_cluster_labels=False,
    )
    monkeypatch.setattr(
        renderer, "_spiral_gen", lambda *_args, **_kwargs: iter([(150.0, 100.0)])
    )
    collisions = iter([True, False])
    monkeypatch.setattr(renderer, "_check_collision", lambda *_args: next(collisions))
    placed = renderer.place_words({"python": 1.0})
    assert len(placed) == 1
    assert placed[0].font_size < (renderer.min_font_size + renderer.max_font_size) / 2

    clamped = ClusteredRenderer(
        width=300,
        height=200,
        min_font_size=40.0,
        max_font_size=20.0,
        show_cluster_labels=False,
    )
    monkeypatch.setattr(
        clamped, "_spiral_gen", lambda *_args, **_kwargs: iter([(150.0, 100.0)])
    )
    monkeypatch.setattr(clamped, "_check_collision", lambda *_args: False)
    assert clamped.place_words({"python": 1.0})[0].font_size == 40.0


def test_cli_lazy_import_failure_is_actionable(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def reject_techs(
        name: str,
        globals: Mapping[str, object] | None = None,
        locals: Mapping[str, object] | None = None,
        fromlist: Sequence[str] | None = (),
        level: int = 0,
    ) -> ModuleType:
        if name in {"techs", "scripts.techs"}:
            raise ImportError("techs unavailable")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", reject_techs)
    with pytest.raises(typer.Exit) as raised:
        cli_word_cloud._wc_import()
    assert raised.value.exit_code == 1


def test_cli_markdown_helper_missing_empty_and_dense(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generated: list[dict[str, object]] = []

    class Settings:
        @classmethod
        def from_yaml_model(cls, _model: object = None, **kwargs: object) -> object:
            return SimpleNamespace(**kwargs)

    class Generator:
        def __init__(self, **kwargs: object) -> None:
            generated.append({"init": kwargs})

        def generate(self, **kwargs: object) -> Path:
            generated.append(dict(kwargs))
            output = Path(cast(str | Path, kwargs["output_path"]))
            output.write_text("<svg/>", encoding="utf-8")
            return output

    wc = SimpleNamespace(
        parse_markdown_for_word_cloud_frequencies=lambda _path: {},
        PROFILE_IMG_OUTPUT_DIR=tmp_path / "default",
        WordCloudSettings=Settings,
        WordCloudGenerator=Generator,
    )
    assert (
        cli_word_cloud._wc_from_markdown(
            wc, tmp_path / "missing.md", "topics", "ocean", None, [], 10
        )
        is None
    )
    md = tmp_path / "topics.md"
    md.write_text("ignored", encoding="utf-8")
    assert (
        cli_word_cloud._wc_from_markdown(wc, md, "topics", "ocean", None, [], 10)
        is None
    )

    wc.parse_markdown_for_word_cloud_frequencies = lambda _path: {
        f"term-{index}": index + 1 for index in range(102)
    }
    output = tmp_path / "explicit" / "dense.svg"
    result = cli_word_cloud._wc_from_markdown(
        wc,
        md,
        "topics",
        "ocean",
        output,
        [],
        3,
        layout_readability={"fallback_rotation": 0.0},
    )
    assert result == output
    assert output.exists()
    call = generated[-1]
    assert call["min_font_size"] == 5.0
    assert call["max_font_size"] == 42.0


def test_cli_tech_and_prompt_helpers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Settings:
        output_dir = tmp_path / "default"

        @classmethod
        def from_yaml_model(cls, _model: object = None, **kwargs: object) -> object:
            return SimpleNamespace(**kwargs)

    class Generator:
        def __init__(self, **_kwargs: object) -> None:
            pass

        def generate(self, **kwargs: object) -> Path:
            output_value = (
                kwargs.get("output_path") or tmp_path / f"{kwargs['source']}.svg"
            )
            output = Path(cast(str | Path, output_value))
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text("<svg/>", encoding="utf-8")
            return output

    wc = SimpleNamespace(
        load_technologies=lambda _path: [],
        WordCloudSettings=Settings,
        WordCloudGenerator=Generator,
    )
    techs_path = tmp_path / "techs.md"
    techs_path.write_text("ignored", encoding="utf-8")
    assert cli_word_cloud._wc_from_techs(wc, techs_path, None, [], 5) is None

    wc.load_technologies = lambda _path: [SimpleNamespace(name="Python", level=5)]
    assert cli_word_cloud._wc_from_techs(wc, techs_path, None, ["python"], 5) is None
    tech_output = tmp_path / "out" / "techs.svg"
    assert (
        cli_word_cloud._wc_from_techs(wc, techs_path, tech_output, [], 5) == tech_output
    )

    monkeypatch.setattr(
        cli_word_cloud, "_prompt_to_frequencies", lambda _text, _stop: {}
    )
    assert cli_word_cloud._wc_from_prompt(wc, "the", None, [], 5) is None
    monkeypatch.setattr(
        cli_word_cloud,
        "_prompt_to_frequencies",
        lambda _text, _stop: {"python": 2.0},
    )
    prompt_output = tmp_path / "out" / "prompt.svg"
    assert (
        cli_word_cloud._wc_from_prompt(wc, "python", prompt_output, [], 5)
        == prompt_output
    )


def test_cli_word_cloud_routes_all_sources_and_reports_results(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ConfigModel:
        stopwords = ["skip"]
        output_dir = tmp_path
        max_words = 0
        prompt: str | None = None

        def to_word_cloud_settings(self) -> object:
            return SimpleNamespace(
                max_words=self.max_words,
                layout_readability=LayoutReadabilitySettings(),
            )

        def model_dump(self, **_kwargs: object) -> dict[str, object]:
            return {"prompt": self.prompt} if self.prompt is not None else {}

    model = ConfigModel()
    monkeypatch.setattr(
        cli_word_cloud,
        "_load_project_config",
        lambda _path: SimpleNamespace(word_cloud_settings=model),
    )
    monkeypatch.setattr(cli_word_cloud, "_wc_import", lambda: SimpleNamespace())
    calls: list[str] = []

    def emitted(name: str) -> Any:
        def helper(*_args: object, **_kwargs: object) -> Path:
            calls.append(name)
            output = tmp_path / f"{name}.svg"
            output.write_text("<svg/>", encoding="utf-8")
            return output

        return helper

    monkeypatch.setattr(cli_word_cloud, "_wc_from_topics", emitted("topics"))
    monkeypatch.setattr(cli_word_cloud, "_wc_from_languages", emitted("languages"))
    monkeypatch.setattr(cli_word_cloud, "_wc_from_techs", emitted("techs"))
    monkeypatch.setattr(cli_word_cloud, "_wc_from_prompt", emitted("prompt"))

    cli_word_cloud.word_cloud(None, tmp_path / "both.svg", None, None, True, True)
    techs_path = tmp_path / "techs.md"
    techs_path.write_text("ignored", encoding="utf-8")
    cli_word_cloud.word_cloud(None, None, techs_path, None, False, False)
    cli_word_cloud.word_cloud(None, None, None, "direct", False, False)
    model.prompt = "configured"
    cli_word_cloud.word_cloud(None, None, None, None, False, False)
    model.prompt = None
    cli_word_cloud.word_cloud(None, None, None, None, False, False)

    assert calls == ["topics", "languages", "techs", "prompt", "prompt"]
