"""High-yield, deterministic coverage for living-art and banner support code."""

from __future__ import annotations

import copy
import importlib
import io
import math
import runpy
import subprocess
import sys
from concurrent.futures import Future
from datetime import UTC, date, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import numpy as np
import pytest
from PIL import Image
from pydantic import ValidationError

from scripts import banner, svg_drawing
from scripts.art import animate, artifacts, daily_snapshots, timelapse
from scripts.art.shared import color, math_helpers, metrics, timeline, world_state


def _png_bytes(size: tuple[int, int] = (4, 4), color_name: str = "red") -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, color_name).save(buffer, format="PNG")
    return buffer.getvalue()


def _snapshot(
    day_index: int,
    *,
    maturity: float = 0.5,
    metrics_dict: dict[str, Any] | None = None,
    state: world_state.WorldState | None = None,
) -> daily_snapshots.DailySnapshot:
    return daily_snapshots.DailySnapshot(
        day=date(2024, 1, 1 + day_index),
        day_index=day_index,
        total_days=10,
        progress=day_index / 9,
        maturity=maturity,
        world_state=state or world_state.WorldState(),
        metrics_dict=metrics_dict or {},
        history_dict={},
    )


def test_math_helpers_generate_deterministic_geometry() -> None:
    points = math_helpers.phyllotaxis_points(4, 10.0, 20.0, scale=2.0)
    assert len(points) == 4
    assert points[0] != points[-1]

    lines = math_helpers.flow_field_lines(
        100,
        100,
        num_lines=3,
        steps=5,
        step_size=1.0,
        freq=0.01,
        octaves=2,
        seed=7,
    )
    assert lines == math_helpers.flow_field_lines(
        100,
        100,
        num_lines=3,
        steps=5,
        step_size=1.0,
        freq=0.01,
        octaves=2,
        seed=7,
    )
    assert all(len(line) > 2 for line in lines)
    assert (
        math_helpers.flow_field_lines(
            0, 0, num_lines=1, steps=1, step_size=100.0, seed=1
        )
        == []
    )


def test_color_helpers_cover_interpolation_wrap_and_contrast() -> None:
    assert color.hsl_to_hex(0.0, 1.0, 0.5) == "#ff0000"
    assert color.lerp_color("#000000", "#ffffff", 0.5) == "#7f7f7f"
    assert len(color.oklch_gradient([(0.6, 0.1, 10), (0.7, 0.1, 350)], 5)) == 5

    adjusted = color.ensure_contrast("#555555", "#000000", min_ratio=4.5)
    assert color.wcag_contrast_ratio(adjusted, "#000000") >= 4.5
    assert color.ensure_contrast("#777777", "#777777", min_ratio=22.0) == "#777777"


def test_timeline_parsing_reversed_window_and_distribution() -> None:
    assert timeline._as_date(date(2024, 2, 3)) == date(2024, 2, 3)
    assert timeline._as_date("2024-99-99") is None
    assert timeline._as_date("2024-99") is None
    assert timeline._as_date("2024-01-99T00:00:00Z") is None
    assert timeline._as_date(7) is None

    delay = timeline.map_date_to_loop_delay(
        "2024-01-05",
        (date(2024, 1, 10), date(2024, 1, 1)),
        duration=10.0,
    )
    assert 0.0 <= delay <= 10.0
    start, end = timeline.normalize_timeline_window(
        dated_events=[7], now=date(2024, 1, 31), fallback_days=0
    )
    assert (start, end) == (date(2024, 1, 30), date(2024, 1, 31))

    for month in range(1, 13):
        for count in range(1, 32):
            distributed = timeline._distribute_monthly_count(2024, month, count)
            assert sum(distributed) == count


def test_svg_drawing_factories_and_serialization(tmp_path: Path) -> None:
    drawing = svg_drawing.Drawing(
        filename=tmp_path / "nested" / "drawing.svg",
        size=("20px", "10px"),
    )
    group = drawing.g(id="group", ignored=None)
    group["data_value"] = "a&b"
    assert group["data_value"] == "a&b"
    assert group.get("missing", "fallback") == "fallback"

    text = drawing.text("<hello>", insert=(1, 2), fill="red")
    image = drawing.image(href="data:image/png;base64,x", insert=(3, 4), size=(5, 6))
    path = drawing.path(d="M 0 0")
    path.push("L 1 1")
    group.add(text)
    group.add(image)
    group.add(path)
    group.add("<!-- literal -->")
    assert list(group)[0] is text
    drawing.add(group)

    gradient = drawing.linearGradient(id="gradient")
    gradient.add_stop_color(0.5, "#fff", 0.7)
    gradient.add_stop_color(2, "#000")
    drawing.defs.add(gradient)
    filter_element = drawing.filter(id="filter")
    assert filter_element.feOffset(dx=1, dy=2).tag == "feOffset"
    drawing.defs.add(filter_element)

    pretty = drawing.tostring(pretty=True)
    assert "&lt;hello&gt;" in pretty
    assert "xlink:href" in pretty
    assert 'offset="2"' in pretty
    drawing.save(pretty=True)
    assert (tmp_path / "nested" / "drawing.svg").read_text().startswith("<?xml")


def test_banner_noise_and_color_fallbacks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(banner.NoiseHandler, "_initialized_flag", False)
    monkeypatch.setattr(banner.NoiseHandler, "_noise_module_available", False)
    monkeypatch.setattr(banner.NoiseHandler, "_actual_noise_module", None)
    monkeypatch.setitem(sys.modules, "noise", None)
    banner.NoiseHandler._initialize()
    assert banner.NoiseHandler.pnoise2(2.0, 3.0) == pytest.approx(
        float(np.sin(0.2) * np.cos(0.3) * 0.5)
    )
    assert banner.parse_rgba_color("rgba(no, 0, 0, 1)") == (
        "rgba(no, 0, 0, 1)",
        1.0,
    )
    assert banner.adjust_hue("#ggg", 30) == "#ggg"


def test_banner_gradient_palette_and_dark_mode_defaults() -> None:
    drawing = svg_drawing.Drawing(size=(20, 20))
    short = [0.2]
    gradient = banner.create_linear_gradient(
        drawing,
        "short",
        ["#000", "#777", "#fff"],
        short,
        angle=45,
    )
    assert len(gradient.elements) == 3
    assert short == [0.2, 1.0, 1.0]
    long = [0.1, 0.2, 0.3]
    assert (
        len(banner.create_linear_gradient(drawing, "long", ["#000"], long).elements)
        == 1
    )
    assert (
        len(banner.create_linear_gradient(drawing, "none", ["#000", "#fff"]).elements)
        == 2
    )

    palette = banner.ColorPalette(
        secondary=[],
        accent=[],
        neutral=[],
        extra_accents=[],
        gradient_stops=[],
        dark_mode_palette={},
    )
    assert palette.secondary and palette.dark_mode_palette
    config = banner.BannerConfig(colors=palette, dark_mode=True)
    config.apply_dark_mode()
    assert config.colors.neutral == ["#14181a", "#1e2427"]
    assert config.typography.glow_color == "rgba(255,255,255,0.15)"


def test_draw_clifford_tiny_density_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    drawing = svg_drawing.Drawing(size=(20, 20))
    group = drawing.g()
    original_zeros = np.zeros
    density = np.array([[0.0, 1.0], [8.0, 1000.0]], dtype=np.float64)

    with monkeypatch.context() as context:
        context.setattr(banner.np, "zeros", lambda *args, **kwargs: density.copy())
        result = banner.draw_clifford(
            drawing,
            group,
            width=20,
            height=20,
            iterations=0,
            grid_size=2,
            dark_mode=True,
        )
    assert result is None
    assert len(group.elements) == 3

    with monkeypatch.context() as context:
        context.setattr(banner.np, "zeros", original_zeros)
        first_hit = banner.draw_clifford(
            drawing,
            drawing.g(),
            width=20,
            height=20,
            iterations=20,
            grid_size=4,
            return_first_hit=True,
        )
        empty = banner.draw_clifford(
            drawing,
            drawing.g(),
            width=20,
            height=20,
            iterations=0,
            grid_size=2,
        )
    assert isinstance(first_hit, np.ndarray)
    assert first_hit.shape == (4, 4)
    assert empty is None


def test_generate_banner_fails_closed_when_save_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class FailingDrawing:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def g(self, **kwargs: Any) -> svg_drawing.Group:
            return svg_drawing.Group(**kwargs)

        def add(self, element: Any) -> Any:
            return element

        def save(self, pretty: bool = False) -> None:
            raise OSError("intentional save failure")

    monkeypatch.setattr(banner, "Drawing", FailingDrawing)
    for helper_name in (
        "define_background",
        "add_glassmorphism_effect",
        "draw_flow_patterns",
        "draw_neural_network",
        "draw_lorenz",
        "draw_aizawa",
        "add_micro_details",
        "add_title_and_subtitle",
        "add_octocat",
    ):
        monkeypatch.setattr(banner, helper_name, lambda *args, **kwargs: None)

    output = tmp_path / "never-created.svg"
    with pytest.raises(OSError, match="intentional save failure"):
        banner.generate_banner(
            banner.BannerConfig(output_path=str(output), optimize_with_svgo=False)
        )
    assert not output.exists()


def test_metrics_age_bands_and_normalization_edges(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime(2024, 7, 1, tzinfo=UTC)
    assert metrics._age_months_from_date(None, now=now) is None
    assert metrics._age_months_from_date("not-a-date", now=now) is None
    assert metrics._repo_recency_band(cast(int, math.nan)) == "legacy"
    bands = metrics._build_repo_recency_bands(
        [{"date": "not-a-date"}, {"updated_at": "2024-06-01T00:00:00Z"}],
        now=now,
    )
    assert sum(bands.values()) == 2

    monkeypatch.setattr(
        metrics,
        "validate_live_metrics_payload",
        lambda raw: {
            "stars": None,
            "top_repos": [{"name": "one", "topics": ["testing"]}],
            "contributions_calendar": [{"date": "2024-01-01", "count": 2}],
            "languages": {"Python": 0},
        },
    )
    normalized = metrics.normalize_live_metrics({}, owner="owner")
    assert normalized["stars"] == 0
    assert normalized["repos"][0]["age_months"] == 6
    assert normalized["label"] == "owner"
    assert normalized["language_diversity"] == 0.0

    monkeypatch.setattr(
        metrics,
        "validate_live_metrics_payload",
        lambda raw: {
            "repos": [{"name": "two", "date": "invalid", "age_months": 0}],
            "contributions_daily": {},
            "contributions_calendar": [{"date": "2024-02-03", "count": 4}],
            "languages": {},
        },
    )
    normalized = metrics.normalize_live_metrics({})
    assert normalized["repos"][0]["age_months"] == 6
    assert normalized["contributions_monthly"] == {"2024-02": 4}
    assert normalized["language_count"] == 0


def test_world_state_invalid_inputs_and_weather_thresholds() -> None:
    assert world_state._interpolate_hour_signal(0, [(1, 2), (2, 3)]) == 3
    weights = world_state._normalize_season_weights(
        {"spring": cast(float, "invalid")}, default="missing"
    )
    assert weights["summer"] == 1.0
    assert (
        world_state._weighted_hue(
            {"a": 0.5, "b": 0.5}, {"a": 0.0, "b": 180.0}, default=42.0
        )
        == 42.0
    )
    maturity = world_state.compute_maturity(
        {"source_contract": "evolution_state", "maturity": "invalid"}
    )
    assert 0.0 <= maturity <= 1.0

    expected = (
        ({"cloud": 0.4}, "clear"),
        ({"cloud": 1.0}, "cloudy"),
        ({"rain": 0.8}, "rainy"),
    )
    for atmosphere, weather in expected:
        state = world_state.compute_world_state({"atmosphere_weights": atmosphere})
        assert state.weather == weather

    issue_state = world_state.compute_world_state(
        {"open_issues_count": 5, "issue_stats": {"closed_count": 5}}
    )
    assert issue_state.weather == "rainy"
    invalid_state = world_state.compute_world_state(
        {
            "commit_hour_distribution": {"invalid": 9},
            "languages": {"Python": "invalid", "Rust": 2},
        }
    )
    assert invalid_state.time_of_day == "day"
    assert invalid_state.season == "winter"


def test_daily_snapshot_preindexing_and_estimation_helpers() -> None:
    assert daily_snapshots._parse_date(None) is None
    assert daily_snapshots._parse_date("2024-99-99") is None
    repos = daily_snapshots._repos_by_creation_date(
        [{"name": "bad", "date": "invalid"}, {"name": "ok", "date": "2024-01-01"}],
        [{"name": "ok", "language": "Python", "stars": 2}],
    )
    assert [repo[1]["name"] for repo in repos] == ["ok"]

    balances = {"a": 2.0}
    assert daily_snapshots._allocate_star_delta(0, {"a": 1}, balances) == {}
    allocation = daily_snapshots._allocate_star_delta(1, {"a": 1}, balances)
    assert allocation == {"a": 1}
    equal = daily_snapshots._allocate_star_delta(3, {"a": 0, "b": 0}, {})
    assert sum(equal.values()) == 3
    histogram = daily_snapshots._allocate_histogram_delta(3, {}, {})
    assert histogram[12] == 3

    identities = daily_snapshots._repo_identity_map(
        {
            "repo_visual_order": ["repo"],
            "repos": [None, {}, {"name": "repo", "age_months": 6, "topics": "bad"}],
        }
    )
    assert identities["repo"]["visual_index"] == 0
    languages = daily_snapshots._language_distribution_at_day(
        [{"language": "Python", "age_months": 3}],
        {"Python": 100, "Rust": 50},
        {"Python": 1, "Rust": 1},
    )
    assert languages == {"Python": 50}
    assert daily_snapshots._language_distribution_at_day([], {}, {}) == {}
    assert daily_snapshots._truncate_daily(
        {"invalid": 4, "2024-01-01": 2, "2024-02-01": 3}, date(2024, 1, 15)
    ) == {"2024-01-01": 2}
    assert (
        daily_snapshots._with_canonical_date(
            {"published_at": "2024-01-01"}, fallback_keys=("published_at",)
        )["date"]
        == "2024-01-01"
    )
    existing = {"date": "2024-02-01"}
    assert daily_snapshots._with_canonical_date(existing, fallback_keys=()) is existing

    assert daily_snapshots._estimate_issue_stats_at_day(
        day=date(2024, 1, 1),
        progress=0.0,
        daily_contribs={},
        open_issues_current=0,
        issue_stats_current={},
        releases_count=0,
        merged_prs_count=0,
    ) == ({"open_count": 0, "closed_count": 0}, 0)

    issue_stats, open_count = daily_snapshots._estimate_issue_stats_at_day(
        day=date(2024, 1, 1),
        progress=0.5,
        daily_contribs={},
        open_issues_current=4,
        issue_stats_current={"closed_count": 6},
        releases_count=2,
        merged_prs_count=3,
    )
    assert issue_stats["open_count"] == open_count
    assert (
        daily_snapshots._hour_from_event({"date": "invalidTvalue"}, ("date",)) is None
    )
    assert daily_snapshots._hour_from_event({"date": 3}, ("date",)) is None
    synthetic = daily_snapshots._estimate_commit_hours_at_day(
        day=date(2024, 1, 1),
        daily_contribs={},
        base_distribution={"invalid": 2},
        stars=[{"date": "2024-01-01T03:00:00Z"}],
        forks=[],
        releases=[],
        merged_prs=[],
    )
    assert len(synthetic) == 24
    assert (
        sum(
            daily_snapshots._repo_recency_bands(
                [
                    {"age_months": 1},
                    {"age_months": 6},
                    {"age_months": 24},
                    {"age_months": 48},
                ]
            ).values()
        )
        == 4
    )


def test_daily_snapshot_builder_one_day_fallbacks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FixedDate(date):
        @classmethod
        def today(cls) -> FixedDate:
            return cls(2024, 6, 1)

    monkeypatch.setattr(daily_snapshots, "dt_date", FixedDate)
    fallback_end = FixedDate.today() - daily_snapshots.timedelta(days=365)
    monkeypatch.setattr(
        daily_snapshots,
        "_timeline_end_day",
        lambda *, include_today: fallback_end,
    )
    fallback = daily_snapshots.build_daily_snapshots(
        {}, {"languages": {"Python": 0}}, include_today=False
    )
    assert len(fallback) == 1
    assert fallback[0].metrics_dict["language_diversity"] == 0.0

    current_end = FixedDate.today()
    monkeypatch.setattr(
        daily_snapshots,
        "_timeline_end_day",
        lambda *, include_today: current_end,
    )
    future = daily_snapshots.build_daily_snapshots(
        {"account_created": "2999-01-01"}, {}, include_today=False
    )
    assert len(future) == 1
    assert future[0].day == current_end


def _monotonic_payload() -> dict[str, Any]:
    cumulative: dict[str, Any] = {
        key: 1 for key in daily_snapshots.MONOTONIC_CUMULATIVE_KEYS
    }
    render: dict[str, Any] = {
        key: 1 for key in daily_snapshots.RENDER_STATE_SCALAR_KEYS
    }
    render.update(
        {key: {"item": 1} for key in daily_snapshots.RENDER_STATE_MAPPING_KEYS}
    )
    render.update(
        {
            "releases": [{"id": 1}],
            "recent_merged_prs": [{"id": 1}],
            "repos": [{"name": "repo", "stars": 1, "forks": 1, "age_months": 1}],
        }
    )
    evolution: dict[str, Any] = {
        key: 1 for key in daily_snapshots.EVOLUTION_STATE_SCALAR_KEYS
    }
    evolution.update(
        {key: {"item": 1} for key in daily_snapshots.EVOLUTION_STATE_MAPPING_KEYS}
    )
    evolution["repo_identity"] = {
        "repo": {"visual_index": 0, "language": "Python", "archetype": 0}
    }
    return {
        "cumulative_state": cumulative,
        "render_state": render,
        "evolution_state": evolution,
    }


@pytest.mark.parametrize(
    ("case", "message"),
    [
        ("cumulative", "Cumulative snapshot channel"),
        ("maturity", "Snapshot maturity"),
        ("render_scalar", "Render-state scalar"),
        ("render_mapping", "Render-state mapping"),
        ("render_sequence", "Render-state sequence"),
        ("render_repo", "Render-state repo"),
        ("evolution_scalar", "Evolution-state scalar"),
        ("evolution_mapping", "Evolution-state mapping"),
        ("identity", "Evolution-state repo identity"),
    ],
)
def test_snapshot_monotonic_contract_rejects_each_regression(
    case: str, message: str
) -> None:
    previous_payload = _monotonic_payload()
    current_payload = copy.deepcopy(previous_payload)
    previous_maturity = 0.5
    current_maturity = 0.5
    if case == "cumulative":
        current_payload["cumulative_state"]["stars"] = 0
    elif case == "maturity":
        current_maturity = 0.4
    elif case == "render_scalar":
        current_payload["render_state"]["stars"] = 0
    elif case == "render_mapping":
        current_payload["render_state"]["languages"]["item"] = 0
    elif case == "render_sequence":
        current_payload["render_state"]["releases"] = []
    elif case == "render_repo":
        current_payload["render_state"]["repos"][0]["stars"] = 0
    elif case == "evolution_scalar":
        current_payload["evolution_state"]["maturity"] = 0
    elif case == "evolution_mapping":
        current_payload["evolution_state"]["atmosphere_weights"]["item"] = 0
    else:
        current_payload["evolution_state"]["repo_identity"]["repo"]["language"] = "Rust"

    with pytest.raises(ValueError, match=message):
        daily_snapshots.validate_snapshot_monotonic_contract(
            [
                _snapshot(0, maturity=previous_maturity, metrics_dict=previous_payload),
                _snapshot(1, maturity=current_maturity, metrics_dict=current_payload),
            ]
        )


def test_snapshot_sampling_edge_and_visual_transition_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert daily_snapshots.validate_snapshot_monotonic_contract([]) is None
    assert daily_snapshots._sampling_metrics(
        _snapshot(0, metrics_dict={"render_state": {"stars": 2}})
    ) == {"stars": 2}
    before = _snapshot(
        0,
        metrics_dict={"contributions_monthly": {"2024-01": 1}},
        state=world_state.WorldState(season="summer"),
    )
    after = _snapshot(
        1,
        metrics_dict={
            "contributions_monthly": {"2024-01": 1, "2024-02": 2},
        },
        state=world_state.WorldState(season="winter"),
    )
    assert daily_snapshots._transition_score(before, after) >= 2.1
    assert (
        daily_snapshots._best_gap_split_index(
            [before, after], [0.0, 0.0], left=0, right=1
        )
        is None
    )

    snapshots = [_snapshot(index) for index in range(10)]
    assert daily_snapshots.sample_frames([], max_frames=4) == []
    assert daily_snapshots.sample_frames(snapshots, max_frames=1) == [snapshots[-1]]
    assert daily_snapshots.sample_frames(snapshots, max_frames=2) == [
        snapshots[0],
        snapshots[-1],
    ]
    monkeypatch.setattr(daily_snapshots, "_sample_gap_score", lambda *a, **k: -1.0)
    sampled = daily_snapshots.sample_frames(snapshots, max_frames=6)
    assert sampled[0] is snapshots[0] and sampled[-1] is snapshots[-1]

    with monkeypatch.context() as context:
        context.setattr(daily_snapshots, "_sample_gap_score", lambda *a, **k: 1.0)
        context.setattr(daily_snapshots, "_best_gap_split_index", lambda *a, **k: None)
        stalled = daily_snapshots.sample_frames(snapshots, max_frames=6)
    assert stalled[0] is snapshots[0] and stalled[-1] is snapshots[-1]


def _write_gif(path: Path, *, size: tuple[int, int] = (2, 2)) -> None:
    frames = [Image.new("RGB", size, color_name) for color_name in ("red", "blue")]
    frames[0].save(
        path,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=[100, 200],
        loop=0,
    )


def test_artifact_manifest_validation_gallery_and_sync(tmp_path: Path) -> None:
    not_gif = tmp_path / "not-really.gif"
    Image.new("RGB", (2, 2)).save(not_gif, format="PNG")
    with pytest.raises(ValueError, match="not a GIF"):
        artifacts._gif_metadata(not_gif)
    not_gif.unlink()

    output = tmp_path / "output"
    output.mkdir()
    (output / "subdir").mkdir()
    gif_path = output / "living-inkgarden.gif"
    _write_gif(gif_path)
    manifest = artifacts.build_living_art_manifest(output)
    assert manifest["total_assets"] == 1

    with pytest.raises(ValueError, match="no asset list"):
        artifacts.validate_living_art_byte_budgets({})
    invalid_manifest = {
        "assets": [None, {"name": None, "bytes": -1}],
    }
    with pytest.raises(ValueError, match="non-object asset"):
        artifacts.validate_living_art_byte_budgets(
            invalid_manifest,
            budgets={"living-inkgarden.gif": 1},
            total_budget=1,
        )

    gallery = artifacts._render_gallery(
        {
            "assets": [{"channel": "custom"}],
            "counts": {"timelapse_gif": 0},
            "total_assets": 0,
        }
    )
    assert "No living-art assets" in gallery

    artifacts._sync_public_surface(output, manifest, output)
    public = tmp_path / "public"
    stale_staging = public / ".living-art-sync"
    stale_staging.mkdir(parents=True)
    (stale_staging / "stale").write_text("stale")
    artifacts._sync_public_surface(output, manifest, public)
    assert (public / "living-inkgarden.gif").is_file()
    assert (public / artifacts.MANIFEST_FILENAME).is_file()
    assert not stale_staging.exists()


def test_timelapse_single_frame_success_and_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_module = SimpleNamespace(generate=lambda data, **kwargs: "<svg/>")
    monkeypatch.setitem(timelapse._STYLE_REGISTRY, "unit", ("fake.art", "generate"))
    monkeypatch.setattr(importlib, "import_module", lambda name: fake_module)
    monkeypatch.setattr(
        animate,
        "svg_to_png",
        lambda svg, size, frame_id="": Image.new("RGBA", (size, size), "red"),
    )
    snapshot_data = {"metrics_dict": {"stars": 1}, "maturity": 0.4, "day_index": 2}
    rendered = timelapse._render_single_frame(snapshot_data, "unit", "seed", 4)
    assert rendered is not None
    with Image.open(io.BytesIO(rendered)) as image:
        assert image.size == (4, 4)

    monkeypatch.setattr(animate, "svg_to_png", lambda *args, **kwargs: None)
    assert timelapse._render_single_frame(snapshot_data, "unit", "seed", 4) is None


def test_timelapse_duration_alignment_and_gif_degradation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    assert timelapse._compute_frame_durations(0) == [3000]
    assert timelapse._compute_frame_durations(2) == [1200, 3000]
    for frame_count in range(3, 18):
        durations = timelapse._compute_frame_durations(frame_count, total_ms=10)
        assert len(durations) == frame_count
        assert durations[-1] == 3000

    frames, durations = timelapse._select_valid_frames_with_durations(
        [(2, b"late"), (0, b"first"), (1, None)], [100, 200]
    )
    assert frames == [b"first"]
    assert durations == [100]

    monkeypatch.setattr(
        timelapse, "_optimize_gif_with_gifsicle", lambda output_path: False
    )
    output = tmp_path / "degraded.gif"
    result = timelapse._assemble_gif(
        [_png_bytes(color_name="red"), _png_bytes(color_name="blue")],
        [100, 200],
        output,
        max_colors=192,
        max_size_mb=-1.0,
    )
    assert result == output
    with Image.open(output) as image:
        assert image.format == "GIF"
        assert image.size == (2, 2)


class _InlineExecutor:
    def __init__(self, max_workers: int) -> None:
        self.max_workers = max_workers

    def __enter__(self) -> _InlineExecutor:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def submit(self, function: Any, *args: Any) -> Future[Any]:
        future: Future[Any] = Future()
        try:
            future.set_result(function(*args))
        except Exception as exc:
            future.set_exception(exc)
        return future


def _patch_timelapse_inputs(
    monkeypatch: pytest.MonkeyPatch,
    snapshots: list[daily_snapshots.DailySnapshot],
) -> None:
    monkeypatch.setattr(timelapse, "validate_live_history_payload", dict)
    monkeypatch.setattr(timelapse, "validate_live_metrics_payload", dict)
    monkeypatch.setattr(
        timelapse, "build_daily_snapshots", lambda *args, **kwargs: snapshots
    )
    monkeypatch.setattr(timelapse, "sample_frames", lambda items, **kwargs: items)
    monkeypatch.setattr(
        timelapse, "validate_snapshot_monotonic_contract", lambda items: None
    )
    monkeypatch.setattr(timelapse, "seed_hash", lambda data: "seed")


def test_render_timelapse_synchronous_worker_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    snapshots = [_snapshot(index) for index in range(3)]
    _patch_timelapse_inputs(monkeypatch, snapshots)
    monkeypatch.setattr(timelapse, "ProcessPoolExecutor", _InlineExecutor)
    monkeypatch.setattr(timelapse, "as_completed", lambda futures: list(futures))

    def fake_render(
        snapshot_data: dict[str, Any], style: str, seed: str, size: int
    ) -> bytes | None:
        del style, seed, size
        if snapshot_data["day_index"] == 1:
            raise RuntimeError("worker failure")
        if snapshot_data["day_index"] == 2:
            return None
        return _png_bytes()

    def fake_assemble(
        png_frames: list[bytes],
        durations: list[int],
        output_path: Path,
        **kwargs: Any,
    ) -> Path:
        assert len(png_frames) == len(durations) == 1
        output_path.write_bytes(b"GIF89a")
        return output_path

    monkeypatch.setattr(timelapse, "_render_single_frame", fake_render)
    monkeypatch.setattr(timelapse, "_assemble_gif", fake_assemble)
    clock = iter(index / 10 for index in range(20))
    monkeypatch.setattr(timelapse.time, "monotonic", lambda: next(clock))
    outputs = timelapse.render_timelapse(
        {},
        {},
        styles=["unknown", "inkgarden"],
        output_dir=tmp_path,
        workers=1,
        timeout_seconds=100,
    )
    assert outputs == [tmp_path / "living-inkgarden.gif"]


def test_render_timelapse_empty_sample_no_valid_and_timeout(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _patch_timelapse_inputs(monkeypatch, [])
    assert timelapse.render_timelapse({}, {}, output_dir=tmp_path) == []

    snapshots = [_snapshot(0)]
    _patch_timelapse_inputs(monkeypatch, snapshots)
    monkeypatch.setattr(timelapse, "sample_frames", lambda items, **kwargs: [])
    assert timelapse.render_timelapse({}, {}, output_dir=tmp_path) == []

    _patch_timelapse_inputs(monkeypatch, snapshots)
    monkeypatch.setattr(timelapse, "ProcessPoolExecutor", _InlineExecutor)
    monkeypatch.setattr(timelapse, "as_completed", lambda futures: list(futures))
    monkeypatch.setattr(timelapse, "_render_single_frame", lambda *args: None)
    assert (
        timelapse.render_timelapse(
            {}, {}, styles=["inkgarden"], output_dir=tmp_path, workers=1
        )
        == []
    )

    _patch_timelapse_inputs(monkeypatch, snapshots)
    clock = iter([0.0, 100.0, 100.0])
    monkeypatch.setattr(timelapse.time, "monotonic", lambda: next(clock))
    assert (
        timelapse.render_timelapse(
            {},
            {},
            styles=["inkgarden"],
            output_dir=tmp_path,
            timeout_seconds=1,
        )
        == []
    )


def test_timelapse_cli_success_and_errors(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    metrics_path = tmp_path / "metrics.json"
    history_path = tmp_path / "history.json"
    metrics_path.write_text("{}")
    history_path.write_text("{}")
    gif_path = tmp_path / "generated.gif"
    gif_path.write_bytes(b"GIF89a")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "timelapse",
            "--metrics-path",
            str(metrics_path),
            "--history-path",
            str(history_path),
            "--only",
            "inkgarden",
        ],
    )
    monkeypatch.setattr(timelapse, "render_timelapse", lambda *a, **k: [gif_path])
    timelapse.main()
    assert "Generated:" in capsys.readouterr().out

    metrics_path.write_text("not-json")
    with pytest.raises(SystemExit, match="Failed to load timelapse inputs"):
        timelapse.main()

    metrics_path.write_text("{}")
    validation_error = ValidationError.from_exception_data("payload", [])

    def invalid_render(*args: Any, **kwargs: Any) -> list[Path]:
        raise validation_error

    monkeypatch.setattr(timelapse, "render_timelapse", invalid_render)
    with pytest.raises(SystemExit, match="Invalid timelapse payload"):
        timelapse.main()


def test_animate_timing_and_rsvg_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert animate.ease_in_out(0.25) < 0.5
    assert animate.ease_in_out(0.75) > 0.5
    assert animate.narrative_timing(-1.0) == 0.0
    assert animate.narrative_timing(2.0) == 1.0
    assert animate.narrative_timing(0.1) < animate.narrative_timing(0.4)
    assert animate.narrative_timing(0.8) > 0.65

    monkeypatch.setitem(sys.modules, "cairosvg", None)
    monkeypatch.setattr(animate.shutil, "which", lambda name: "/fake/rsvg-convert")
    completed = subprocess.CompletedProcess(
        args=["rsvg-convert"], returncode=0, stdout=_png_bytes()
    )
    monkeypatch.setattr(animate.subprocess, "run", lambda *a, **k: completed)
    image = animate.svg_to_png("<svg/>", 4, frame_id="rsvg")
    assert image is not None and image.size == (4, 4)


def test_animate_rasterizer_failure_writes_debug_then_cleans(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setitem(sys.modules, "cairosvg", None)
    monkeypatch.setattr(animate.shutil, "which", lambda name: None)
    frame_id = f"coverage-{tmp_path.name}"
    debug_path = Path(f"/tmp/debug-{frame_id}.svg")
    try:
        assert animate.svg_to_png("<svg/>", 4, frame_id=frame_id) is None
        assert debug_path.read_text() == "<svg/>"
    finally:
        debug_path.unlink(missing_ok=True)


def test_animate_profile_and_target_fallbacks(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    known = next(iter(animate.PROFILES))
    assert animate._fallback_profile(known, metrics_requested=False) is not None
    assert animate._fallback_profile("unknown", metrics_requested=False) is None
    assert animate._fallback_profile("unknown", metrics_requested=True) is None

    null_metrics = tmp_path / "null.json"
    null_metrics.write_text("null")
    assert (
        animate._resolve_target(
            profile="unknown", metrics_file=str(null_metrics), history_file=None
        )
        is None
    )

    metrics_file = tmp_path / "metrics.json"
    history_file = tmp_path / "history.json"
    metrics_file.write_text("{}")
    history_file.write_text("invalid")
    monkeypatch.setattr(
        animate, "normalize_live_metrics", lambda *args, **kwargs: {"ok": True}
    )
    assert animate._resolve_target(
        profile="owner",
        metrics_file=str(metrics_file),
        history_file=str(history_file),
    ) == {"ok": True}

    validation_error = ValidationError.from_exception_data("payload", [])

    def invalid_metrics(*args: Any, **kwargs: Any) -> dict[str, Any]:
        raise validation_error

    monkeypatch.setattr(animate, "normalize_live_metrics", invalid_metrics)
    assert (
        animate._resolve_target(
            profile="unknown", metrics_file=str(metrics_file), history_file=None
        )
        is None
    )


def _animate_options(*, only: str | None) -> dict[str, object]:
    return {
        "profile": "owner",
        "frames": 1,
        "size": 4,
        "only": only,
        "svg": False,
        "metrics_path": None,
        "history_path": None,
    }


def test_animate_main_early_unknown_and_no_image_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        animate, "parse_cli_args", lambda *a, **k: _animate_options(only=None)
    )
    monkeypatch.setattr(animate, "_resolve_target", lambda **kwargs: None)
    animate.main()

    monkeypatch.setattr(animate, "_resolve_target", lambda **kwargs: {"stars": 1})
    monkeypatch.setattr(animate, "seed_hash", lambda target: "seed")
    monkeypatch.setattr(animate, "compute_maturity", lambda target: 0.5)
    monkeypatch.setattr(
        animate, "parse_cli_args", lambda *a, **k: _animate_options(only="unknown")
    )
    with pytest.raises(SystemExit) as exc_info:
        animate.main()
    assert exc_info.value.code == 1

    monkeypatch.setattr(
        animate, "parse_cli_args", lambda *a, **k: _animate_options(only="inkgarden")
    )
    monkeypatch.setattr(animate.ink_garden, "generate", lambda *a, **k: "<svg/>")
    monkeypatch.setattr(animate, "svg_to_png", lambda *a, **k: None)
    animate.main()
    assert not list((tmp_path / ".github" / "assets" / "img").glob("*.gif"))


def test_module_entrypoint_guards_are_safe(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "timelapse",
            "--metrics-path",
            str(tmp_path / "missing-metrics.json"),
            "--history-path",
            str(tmp_path / "missing-history.json"),
        ],
    )
    with pytest.warns(RuntimeWarning, match="found in sys.modules"):
        with pytest.raises(SystemExit, match="Failed to load timelapse inputs"):
            runpy.run_module(
                "scripts.art.timelapse", run_name="__main__", alter_sys=True
            )

    monkeypatch.setattr(sys, "argv", ["animate", "--profile", "does-not-exist"])
    with pytest.warns(RuntimeWarning, match="found in sys.modules"):
        runpy.run_module("scripts.art.animate", run_name="__main__", alter_sys=True)
