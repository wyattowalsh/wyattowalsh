from __future__ import annotations

import copy
import re

import pytest
from defusedxml import ElementTree

pytest.importorskip("numpy", reason="numpy is required by scripts.art.lenia")

from scripts.art.lenia import (
    CFG,
    _augment_primary_repos,
    _build_lenia_palette,
    _derive_dynamics,
    _extract_language_mix,
    _semantic_repo_positions,
    generate,
)
from scripts.art.shared import compute_world_state

_FIXED_HASH = "0123456789abcdef" * 4


def _sample_metrics() -> dict:
    return {
        "label": "Lenia Test",
        "account_created": "2021-01-01T00:00:00Z",
        "contributions_last_year": 240,
        "contributions_monthly": {
            "2024-01": 12,
            "2024-02": 18,
        },
        "repos": [
            {
                "name": "alpha",
                "language": "Python",
                "stars": 12,
                "age_months": 24,
                "date": "2024-01-10T12:00:00Z",
            },
            {
                "name": "beta",
                "language": "Go",
                "stars": 4,
                "age_months": 12,
                "date": "2024-02-20T00:00:00Z",
            },
        ],
        "followers": 30,
        "forks": 8,
        "stars": 44,
        "total_commits": 800,
    }


def _snapshot_signal_metrics(*, active: bool) -> dict:
    metrics = copy.deepcopy(_sample_metrics())
    if active:
        metrics["repos"] = [
            {**metrics["repos"][0], "age_months": 2},
            {**metrics["repos"][1], "age_months": 8},
        ]
        metrics["repo_recency_bands"] = {
            "fresh": 1,
            "recent": 1,
            "established": 0,
            "legacy": 0,
        }
        metrics["star_velocity"] = {
            "recent_rate": 9.0,
            "peak_rate": 12.0,
            "trend": "rising",
        }
        metrics["contribution_streaks"] = {
            "current_streak_months": 8,
            "longest_streak_months": 10,
            "streak_active": True,
        }
        metrics["recent_merged_prs"] = [
            {
                "merged_at": "2024-02-18T12:00:00Z",
                "repo_name": "alpha",
                "additions": 120,
                "deletions": 24,
            },
            {
                "merged_at": "2024-02-24T12:00:00Z",
                "repo_name": "alpha",
                "additions": 180,
                "deletions": 60,
            },
        ]
        metrics["commit_hour_distribution"] = {23: 11, 0: 9, 1: 5}
        metrics["contributions_daily"] = {
            "2024-02-01": 3,
            "2024-02-10": 7,
            "2024-02-18": 8,
            "2024-02-24": 6,
        }
    else:
        metrics["repos"] = [
            {**metrics["repos"][0], "age_months": 36},
            {**metrics["repos"][1], "age_months": 48},
        ]
        metrics["repo_recency_bands"] = {
            "fresh": 0,
            "recent": 0,
            "established": 1,
            "legacy": 1,
        }
        metrics["star_velocity"] = {
            "recent_rate": 0.5,
            "peak_rate": 1.0,
            "trend": "stable",
        }
        metrics["contribution_streaks"] = {
            "current_streak_months": 1,
            "longest_streak_months": 2,
            "streak_active": False,
        }
        metrics["recent_merged_prs"] = []
        metrics["commit_hour_distribution"] = {12: 10, 13: 8}
        metrics["contributions_daily"] = {
            "2024-02-01": 1,
            "2024-02-10": 1,
        }
    return metrics


def _timeline_rows(svg: str) -> list[tuple[str, float]]:
    return [
        (when, float(delay))
        for delay, when in re.findall(
            r'data-delay="([0-9]+(?:\.[0-9]+)?)"\s+data-when="(\d{4}-\d{2}-\d{2})"',
            svg,
        )
    ]


def _count_circles(svg: str) -> int:
    root = ElementTree.fromstring(svg)
    return len(root.findall(".//{http://www.w3.org/2000/svg}circle"))


def _circle_opacities(svg: str) -> list[float]:
    return [float(opacity) for opacity in re.findall(r'opacity="([0-9.]+)"', svg)]


def _resolve_palette(metrics: dict) -> tuple[str, tuple[tuple[float, str], ...], str]:
    repos = metrics["repos"]
    language_mix = _extract_language_mix(repos, metrics.get("languages"))
    dynamics = _derive_dynamics(
        metrics,
        config=CFG,
        maturity=1.0,
        language_mix=language_mix,
        repos=repos,
        h=_FIXED_HASH,
    )
    palette = _build_lenia_palette(
        compute_world_state(metrics),
        language_mix=language_mix,
        repos=repos,
        dynamics=dynamics,
        h=_FIXED_HASH,
    )
    return palette.background, palette.ramp, palette.core


def test_lenia_generate_returns_valid_svg() -> None:
    svg = generate(_sample_metrics(), seed="lenia-svg")

    root = ElementTree.fromstring(svg)

    assert root.tag.endswith("svg")
    assert root.attrib["viewBox"] == "0 0 800 800"
    assert svg.rstrip().endswith("</svg>")
    assert "<circle" in svg


def test_lenia_generate_is_deterministic_for_same_seed() -> None:
    metrics = _sample_metrics()

    svg_1 = generate(metrics, seed="fixed-seed", timeline=True, loop_duration=24.0)
    svg_2 = generate(metrics, seed="fixed-seed", timeline=True, loop_duration=24.0)

    assert svg_1 == svg_2


def test_lenia_timeline_can_be_enabled_and_disabled() -> None:
    metrics = _sample_metrics()

    timeline_svg = generate(metrics, seed="lenia-timeline", timeline=True)
    legacy_svg = generate(metrics, seed="lenia-timeline", timeline=False, maturity=0.45)

    timeline_rows = _timeline_rows(timeline_svg)

    assert "@keyframes leniaReveal" in timeline_svg
    assert 'class="tl-reveal"' in timeline_svg
    assert timeline_rows
    assert 'data-when="2024-01-10"' in timeline_svg
    assert "data-delay=" in timeline_svg
    assert "@keyframes leniaReveal" not in legacy_svg
    assert 'class="tl-reveal"' not in legacy_svg
    assert "data-delay=" not in legacy_svg
    assert "opacity=" in legacy_svg


def test_lenia_timeline_svg_keeps_inline_opacity_for_static_rasterizers() -> None:
    svg = generate(
        _sample_metrics(),
        seed="lenia-timeline-static-fallback",
        timeline=True,
        maturity=0.45,
    )

    reveal_styles = re.findall(
        r'class="tl-reveal"\s+style="opacity:([0-9.]+);'
        r"--delay:([0-9.]+)s;--to:([0-9.]+);",
        svg,
    )

    assert reveal_styles
    assert any(float(opacity) > 0.0 for opacity, _, _ in reveal_styles)
    assert all(
        abs(float(opacity) - float(target)) < 0.001
        for opacity, _, target in reveal_styles
    )


def test_lenia_timeline_repo_dates_follow_chronology_in_delays() -> None:
    svg = generate(
        _sample_metrics(),
        seed="lenia-chronology",
        timeline=True,
        loop_duration=24.0,
    )

    delays_by_date: dict[str, list[float]] = {}
    for when, delay in _timeline_rows(svg):
        delays_by_date.setdefault(when, []).append(delay)

    assert "2024-01-10" in delays_by_date
    assert "2024-02-20" in delays_by_date
    assert min(delays_by_date["2024-01-10"]) < min(delays_by_date["2024-02-20"])
    assert max(delays_by_date["2024-01-10"]) < max(delays_by_date["2024-02-20"])


def test_lenia_handles_empty_and_minimal_metrics_without_crashing() -> None:
    svg = generate(
        {
            "repos": [],
            "contributions_monthly": {},
        },
        seed="lenia-empty",
        timeline=False,
        maturity=0.0,
    )

    root = ElementTree.fromstring(svg)

    assert root.tag.endswith("svg")
    assert svg.rstrip().endswith("</svg>")


def test_lenia_static_low_maturity_keeps_seed_residue_visible() -> None:
    svg = generate(
        _sample_metrics(),
        seed="lenia-static-floor",
        timeline=False,
        maturity=0.0,
    )

    opacities = _circle_opacities(svg)

    assert opacities
    assert max(opacities) >= 0.12


def test_lenia_static_adjacent_low_maturities_change_rasterized_frames() -> None:
    from hashlib import sha256
    from io import BytesIO

    from PIL import Image

    from scripts.art.timelapse import _render_single_frame

    metrics = _sample_metrics()
    png_hashes: dict[float, str] = {}

    for day_index, maturity in enumerate((0.0, 0.003, 0.009, 0.010)):
        frame = _render_single_frame(
            {
                "metrics_dict": metrics,
                "history_dict": {},
                "maturity": maturity,
                "progress": maturity,
                "day_index": day_index,
            },
            "lenia",
            "lenia-static-adjacent-export",
            96,
        )
        assert frame is not None
        rgba = Image.open(BytesIO(frame)).convert("RGBA")
        png_hashes[maturity] = sha256(rgba.tobytes()).hexdigest()

    assert png_hashes[0.0] != png_hashes[0.003]
    assert png_hashes[0.009] != png_hashes[0.010]


def test_lenia_static_timelapse_export_produces_distinct_gif_frames(tmp_path) -> None:
    from hashlib import sha256
    from io import BytesIO

    from PIL import Image, ImageSequence

    from scripts.art.timelapse import _assemble_gif, _render_single_frame

    metrics = _sample_metrics()
    png_frames: list[bytes] = []

    for day_index, maturity in enumerate((0.0, 0.01, 0.02)):
        frame = _render_single_frame(
            {
                "metrics_dict": metrics,
                "history_dict": {},
                "maturity": maturity,
                "progress": maturity,
                "day_index": day_index,
            },
            "lenia",
            "lenia-static-export",
            96,
        )
        assert frame is not None
        png_frames.append(frame)

    output_path = tmp_path / "living-lenia.gif"
    _assemble_gif(png_frames, [160] * len(png_frames), output_path)

    frames = [
        frame.copy().convert("RGBA")
        for frame in ImageSequence.Iterator(Image.open(output_path))
    ]
    frame_hashes = [sha256(frame.tobytes()).hexdigest() for frame in frames]
    frame_colors = [
        len(Image.open(BytesIO(png)).convert("RGBA").getcolors(maxcolors=100_000) or [])
        for png in png_frames
    ]

    assert len(frames) == 3
    assert len(set(frame_hashes)) == 3
    assert all(color_count > 8 for color_count in frame_colors)


def test_lenia_language_mix_changes_generated_field() -> None:
    single_language_metrics = _sample_metrics()
    single_language_metrics["repos"] = [
        {**repo, "language": "Python"} for repo in single_language_metrics["repos"]
    ]

    mixed_language_metrics = _sample_metrics()

    single_language_svg = generate(
        single_language_metrics,
        seed="language-mix",
        timeline=False,
        maturity=1.0,
    )
    mixed_language_svg = generate(
        mixed_language_metrics,
        seed="language-mix",
        timeline=False,
        maturity=1.0,
    )

    assert single_language_svg != mixed_language_svg


def test_lenia_semantic_positions_group_similar_languages() -> None:
    metrics = _sample_metrics()
    metrics["repos"] = [
        {
            "name": "py-core",
            "language": "Python",
            "stars": 18,
            "age_months": 6,
            "topics": ["agents", "ml"],
            "date": "2024-01-10T00:00:00Z",
        },
        {
            "name": "py-cli",
            "language": "Python",
            "stars": 8,
            "age_months": 18,
            "topics": ["agents", "cli"],
            "date": "2024-02-02T00:00:00Z",
        },
        {
            "name": "go-service",
            "language": "Go",
            "stars": 16,
            "age_months": 6,
            "topics": ["ops"],
            "date": "2024-02-12T00:00:00Z",
        },
    ]
    language_mix = _extract_language_mix(metrics["repos"], None)
    dynamics = _derive_dynamics(
        metrics,
        config=CFG,
        maturity=1.0,
        language_mix=language_mix,
        repos=metrics["repos"],
        h=_FIXED_HASH,
    )

    positions = _semantic_repo_positions(
        metrics["repos"],
        h=_FIXED_HASH,
        dynamics=dynamics,
    )

    def _distance(left: tuple[float, float], right: tuple[float, float]) -> float:
        return ((left[0] - right[0]) ** 2 + (left[1] - right[1]) ** 2) ** 0.5

    assert positions == _semantic_repo_positions(
        metrics["repos"],
        h=_FIXED_HASH,
        dynamics=dynamics,
    )
    assert _distance(positions[0], positions[1]) < _distance(positions[0], positions[2])
    assert _distance(positions[0], positions[1]) < _distance(positions[1], positions[2])


def test_lenia_palette_changes_with_language_mix() -> None:
    single_language_metrics = _sample_metrics()
    single_language_metrics["repos"] = [
        {**repo, "language": "Python"} for repo in single_language_metrics["repos"]
    ]
    mixed_language_metrics = _sample_metrics()

    single_background, single_ramp, single_core = _resolve_palette(
        single_language_metrics
    )
    mixed_background, mixed_ramp, mixed_core = _resolve_palette(mixed_language_metrics)

    assert single_background != mixed_background
    assert single_ramp != mixed_ramp
    assert single_core != mixed_core


def test_lenia_recent_activity_and_streaks_intensify_field() -> None:
    quiet_metrics = _sample_metrics()
    quiet_metrics["contributions_daily"] = {"2024-01-10": 1}
    quiet_metrics["contribution_streaks"] = {
        "current_streak_months": 0,
        "longest_streak_months": 1,
        "streak_active": False,
    }
    quiet_metrics["star_velocity"] = {
        "recent_rate": 0.0,
        "peak_rate": 0.0,
        "trend": "stable",
    }
    quiet_metrics["traffic_views_14d"] = 0
    quiet_metrics["traffic_clones_14d"] = 0
    quiet_metrics["releases"] = []

    active_metrics = _sample_metrics()
    active_metrics["contributions_daily"] = {
        f"2024-02-{day:02d}": 8 + (day % 3) for day in range(1, 15)
    }
    active_metrics["contribution_streaks"] = {
        "current_streak_months": 6,
        "longest_streak_months": 8,
        "streak_active": True,
    }
    active_metrics["star_velocity"] = {
        "recent_rate": 5.0,
        "peak_rate": 8.0,
        "trend": "rising",
    }
    active_metrics["traffic_views_14d"] = 420
    active_metrics["traffic_clones_14d"] = 140
    active_metrics["releases"] = [
        {"date": "2024-01-15T00:00:00Z"},
        {"date": "2024-02-10T00:00:00Z"},
    ]

    quiet_svg = generate(
        quiet_metrics,
        seed="lenia-activity",
        timeline=False,
        maturity=0.65,
    )
    active_svg = generate(
        active_metrics,
        seed="lenia-activity",
        timeline=False,
        maturity=0.65,
    )

    assert quiet_svg != active_svg
    assert _count_circles(active_svg) > _count_circles(quiet_svg)


def test_lenia_palette_changes_with_recent_snapshot_signals() -> None:
    quiet_background, quiet_ramp, quiet_core = _resolve_palette(
        _snapshot_signal_metrics(active=False)
    )
    active_background, active_ramp, active_core = _resolve_palette(
        _snapshot_signal_metrics(active=True)
    )

    assert quiet_background != active_background
    assert quiet_ramp != active_ramp
    assert quiet_core != active_core


def test_lenia_augment_primary_repos_promotes_recent_merged_repo() -> None:
    primary_repos = [
        {"name": "legacy-core", "language": "Python", "stars": 45, "age_months": 48},
        {"name": "stable-cli", "language": "Go", "stars": 30, "age_months": 24},
    ]
    all_repos = primary_repos + [
        {"name": "fresh-merge", "language": "Rust", "stars": 2, "age_months": 2},
    ]

    selected = _augment_primary_repos(
        primary_repos,
        all_repos,
        merged_repo_names=frozenset({"fresh-merge"}),
        limit=2,
    )

    assert [repo["name"] for repo in selected] == ["fresh-merge", "legacy-core"]


def test_lenia_derived_dynamics_use_recent_snapshot_signals() -> None:
    quiet_metrics = _snapshot_signal_metrics(active=False)
    active_metrics = _snapshot_signal_metrics(active=True)

    quiet_dynamics = _derive_dynamics(
        quiet_metrics,
        config=CFG,
        maturity=1.0,
        language_mix=_extract_language_mix(
            quiet_metrics["repos"],
            quiet_metrics.get("languages"),
        ),
        repos=quiet_metrics["repos"],
        h=_FIXED_HASH,
    )
    active_dynamics = _derive_dynamics(
        active_metrics,
        config=CFG,
        maturity=1.0,
        language_mix=_extract_language_mix(
            active_metrics["repos"],
            active_metrics.get("languages"),
        ),
        repos=active_metrics["repos"],
        h=_FIXED_HASH,
    )

    assert active_dynamics.mu > quiet_dynamics.mu
    assert active_dynamics.sigma > quiet_dynamics.sigma
    assert active_dynamics.sim_steps > quiet_dynamics.sim_steps
    assert active_dynamics.kernel_profile != quiet_dynamics.kernel_profile
    assert active_dynamics.seed_drift != quiet_dynamics.seed_drift
    assert active_dynamics.satellite_count > quiet_dynamics.satellite_count
    assert "alpha" in active_dynamics.merged_repo_names


def test_lenia_recent_snapshot_signals_change_generated_field() -> None:
    quiet_svg = generate(
        _snapshot_signal_metrics(active=False),
        seed="signal-coupling",
        timeline=False,
        maturity=1.0,
    )
    active_svg = generate(
        _snapshot_signal_metrics(active=True),
        seed="signal-coupling",
        timeline=False,
        maturity=1.0,
    )

    assert quiet_svg != active_svg
