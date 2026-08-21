"""Package-structure contracts for scripts.art.shared after the F1 split."""

from __future__ import annotations

import importlib
import math
import re
from collections.abc import Callable
from typing import Any

import pytest

pytest.importorskip("numpy", reason="scripts.art.shared requires numpy")

from scripts.art import shared as shared_pkg  # noqa: E402
from scripts.art.shared import (  # noqa: E402
    ACCRETION_CHANNELS,
    ART_PALETTE_ANCHORS,
    MAX_REPOS,
    STYLE_DIALECTS,
    ElementBudget,
    Noise2D,
    WorldState,
    accretion_log_scale,
    build_style_dialect,
    channel_mark_count,
    compute_world_state,
    extract_accretion_channels,
    oklch,
    seed_hash,
)

_EXPECTED_SUBMODULES = (
    "constants",
    "timeline",
    "world_state",
    "metrics",
    "seeds",
    "color",
    "noise",
    "math_helpers",
    "svg",
    "palette",
    "visual",
    "accretion",
)


@pytest.mark.parametrize("name", _EXPECTED_SUBMODULES)
def test_shared_submodules_importable(name: str) -> None:
    module = importlib.import_module(f"scripts.art.shared.{name}")
    assert module.__name__.endswith(name)


def test_shared_is_package_not_module() -> None:
    assert hasattr(shared_pkg, "__path__")


def test_compat_reexports_match_submodules() -> None:
    from scripts.art.shared import color, constants, noise, world_state

    assert oklch is color.oklch
    assert MAX_REPOS is constants.MAX_REPOS
    assert Noise2D is noise.Noise2D
    assert WorldState is world_state.WorldState
    assert compute_world_state is world_state.compute_world_state


def test_basic_shared_behaviors_still_work() -> None:
    digest = seed_hash({"stars": 1, "label": "x"})
    assert len(digest) == 64
    assert oklch(0.5, 0.1, 120).startswith("#")
    ws = compute_world_state({})
    assert isinstance(ws, WorldState)
    assert "sunset" in ART_PALETTE_ANCHORS
    assert MAX_REPOS == 10


def test_accretion_channels_and_style_dialects_stay_distinct() -> None:
    from scripts.art.artifacts import LIVING_ART_STYLE_KEYS
    from scripts.art.roster import CANDIDATE_STYLE_KEYS, SHIPPED_STYLE_KEYS
    from scripts.art.shared import (
        STYLE_DIALECTS,
        build_style_dialect,
        extract_accretion_channels,
    )
    from scripts.art.timelapse import ALL_STYLES

    metrics = {
        "repos": [{"name": "alpha"}, {"name": "beta"}],
        "stars": 24,
        "total_commits": 400,
        "followers": 18,
    }
    channels = extract_accretion_channels(metrics)

    assert channels.repos == 2
    assert channels.stars == 24
    assert channels.commits == 400
    assert channels.followers == 18
    assert 0.0 < channels.star_scale < 1.0
    assert set(STYLE_DIALECTS) == set(ALL_STYLES)
    assert set(SHIPPED_STYLE_KEYS) <= set(CANDIDATE_STYLE_KEYS)
    assert tuple(ALL_STYLES) == CANDIDATE_STYLE_KEYS
    assert LIVING_ART_STYLE_KEYS == SHIPPED_STYLE_KEYS
    if SHIPPED_STYLE_KEYS == CANDIDATE_STYLE_KEYS:
        assert tuple(ALL_STYLES) == LIVING_ART_STYLE_KEYS
    families = {build_style_dialect(style, metrics).family for style in ALL_STYLES}
    assert families == set(STYLE_DIALECTS.values())
    assert len(families) == len(CANDIDATE_STYLE_KEYS)


# ---------------------------------------------------------------------------
# A1 layer 1 — accretion clock (must stay green through A3)
# ---------------------------------------------------------------------------

_STYLE_KNOBS: dict[str, tuple[str, str, str]] = {
    "inkgarden": ("bloom_scale", "trunk_scale", "glint_count"),
    "topo": ("prominence_scale", "contour_gain", "settlement_gain"),
    "genetic": ("peak_scale", "generation_gain", "colony_gain"),
    "physarum": ("nutrient_scale", "trail_scale", "vein_gain"),
    "lenia": ("halo_scale", "field_gain", "extent_gain"),
    "ferrofluid": ("spike_scale", "ripple_gain", "field_gain"),
}

_A1_SEED = "a1-isolation"
_A1_MATURITY = 0.01
_OPEN_G = re.compile(r"<g\b", re.IGNORECASE)
_CLOSE_G = re.compile(r"</g\s*>", re.IGNORECASE)
_DIALECT_OPEN = re.compile(
    r'<g\b(?=[^>]*\bid="accretion-dialect")[^>]*>',
    re.IGNORECASE,
)
_RENDER_CACHE: dict[tuple[Any, ...], str] = {}
_GENERATOR_FNS: dict[str, Callable[..., str]] | None = None


def _clock_metrics(
    *,
    repos: list[dict[str, Any]] | None = None,
    stars: Any = 24,
    commits: Any = 400,
    followers: Any = 18,
    **extra: Any,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "stars": stars,
        "total_commits": commits,
        "followers": followers,
    }
    if repos is not None:
        payload["repos"] = repos
    payload.update(extra)
    return payload


def test_extract_accretion_channels_falls_back_to_top_repos() -> None:
    channels = extract_accretion_channels(
        _clock_metrics(
            repos=[],
            top_repos=[{"name": "north"}, {"name": "south"}, {"name": "east"}],
        )
    )
    assert channels.repos == 3
    missing_repos = extract_accretion_channels(
        _clock_metrics(top_repos=[{"name": "only"}])
    )
    assert "repos" not in _clock_metrics(top_repos=[{"name": "only"}])
    assert missing_repos.repos == 1


def test_extract_accretion_channels_falls_back_to_public_repos() -> None:
    channels = extract_accretion_channels(_clock_metrics(public_repos=7))
    assert channels.repos == 7


def test_extract_accretion_channels_counts_unnamed_repo_dicts() -> None:
    channels = extract_accretion_channels(
        _clock_metrics(
            repos=[
                {"language": "Python"},
                {"language": "Go", "stars": 3},
                "not-a-dict",
            ]
        )
    )
    assert channels.repos == 2


def test_extract_accretion_channels_list_valued_stars_are_zero() -> None:
    channels = extract_accretion_channels(
        _clock_metrics(
            repos=[{"name": "alpha"}],
            stars=[{"date": "2024-01-04T10:00:00Z", "user": "a"}],
        )
    )
    assert channels.stars == 0
    assert channels.star_scale == 0.0
    assert channels.mark_count("stars") == 0


def test_accretion_log_scale_zero_monotonic_ceiling_and_clamp() -> None:
    ceiling = 80.0
    assert accretion_log_scale(0, ceiling=ceiling) == 0.0
    previous = accretion_log_scale(1, ceiling=ceiling)
    for value in (2, 5, 13, 40, 79):
        current = accretion_log_scale(value, ceiling=ceiling)
        assert current > previous
        previous = current
    assert accretion_log_scale(ceiling, ceiling=ceiling) == 1.0
    assert accretion_log_scale(ceiling * 8, ceiling=ceiling) == 1.0


def test_channel_mark_count_zero_and_first_unit() -> None:
    assert channel_mark_count(0, 0.0) == 0
    assert channel_mark_count(0, 1.0) == 0
    assert channel_mark_count(1, 0.0) >= 1
    assert channel_mark_count(1, 0.01) >= 1


def test_build_style_dialect_unknown_style_raises_keyerror() -> None:
    with pytest.raises(KeyError, match="not-a-living-art-style"):
        build_style_dialect(
            "not-a-living-art-style",
            _clock_metrics(repos=[{"name": "alpha"}]),
        )


@pytest.mark.parametrize("style", tuple(STYLE_DIALECTS))
def test_style_dialect_knobs_isolate_stars_commits_followers(style: str) -> None:
    stars_knob, commits_knob, followers_knob = _STYLE_KNOBS[style]
    base = _clock_metrics(
        repos=[{"name": "alpha"}],
        stars=8,
        commits=40,
        followers=4,
    )
    more_stars = build_style_dialect(style, {**base, "stars": 80}).knobs
    more_commits = build_style_dialect(style, {**base, "total_commits": 4000}).knobs
    more_followers = build_style_dialect(style, {**base, "followers": 90}).knobs
    baseline = build_style_dialect(style, base).knobs

    assert more_stars[stars_knob] > baseline[stars_knob]
    assert more_stars[commits_knob] == baseline[commits_knob]
    assert more_stars[followers_knob] == baseline[followers_knob]

    assert more_commits[commits_knob] > baseline[commits_knob]
    assert more_commits[stars_knob] == baseline[stars_knob]
    assert more_commits[followers_knob] == baseline[followers_knob]

    assert more_followers[followers_knob] > baseline[followers_knob]
    assert more_followers[stars_knob] == baseline[stars_knob]
    assert more_followers[commits_knob] == baseline[commits_knob]
    assert set(ACCRETION_CHANNELS) == {"repos", "stars", "commits", "followers"}


@pytest.mark.parametrize("style", tuple(STYLE_DIALECTS))
def test_repos_have_no_leased_knob(style: str) -> None:
    stars_knob, commits_knob, followers_knob = _STYLE_KNOBS[style]
    scalars = {"stars": 24, "total_commits": 400, "followers": 18}
    one_repo = _clock_metrics(repos=[{"name": "alpha"}], **scalars)
    four_repos = _clock_metrics(
        repos=[{"name": f"repo-{index}"} for index in range(4)],
        **scalars,
    )
    low_channels = extract_accretion_channels(one_repo)
    high_channels = extract_accretion_channels(four_repos)
    low_dialect = build_style_dialect(style, one_repo)
    high_dialect = build_style_dialect(style, four_repos)

    assert high_channels.repos > low_channels.repos
    assert channel_mark_count(
        high_channels.repos, high_channels.repo_scale
    ) > channel_mark_count(low_channels.repos, low_channels.repo_scale)
    assert high_dialect.knobs[stars_knob] == low_dialect.knobs[stars_knob]
    assert high_dialect.knobs[commits_knob] == low_dialect.knobs[commits_knob]
    assert high_dialect.knobs[followers_knob] == low_dialect.knobs[followers_knob]
    assert stars_knob not in {"repo_scale", "repo_gain", "repo_count"}


def test_inkgarden_glint_count_is_zero_at_zero_followers() -> None:
    dialect = build_style_dialect(
        "inkgarden",
        _clock_metrics(repos=[{"name": "alpha"}], followers=0),
    )
    assert dialect.knobs["glint_count"] == 0.0


# ---------------------------------------------------------------------------
# A1 layer 2 — on-canvas isolation
# ---------------------------------------------------------------------------


def _strip_group_tree(svg: str, open_pattern: re.Pattern[str]) -> str:
    match = open_pattern.search(svg)
    if match is None:
        return svg
    start = match.start()
    depth = 0
    pos = start
    while pos < len(svg):
        nxt_open = _OPEN_G.search(svg, pos)
        nxt_close = _CLOSE_G.search(svg, pos)
        if nxt_close is None:
            return svg[:start]
        if nxt_open is not None and nxt_open.start() < nxt_close.start():
            depth += 1
            pos = nxt_open.end()
            continue
        depth -= 1
        pos = nxt_close.end()
        if depth == 0:
            return svg[:start] + svg[pos:]
    return svg[:start]


def _strip_accretion_dialect(svg: str) -> str:
    """Drop the nested `#accretion-dialect` register without a naive regex."""
    stripped = svg
    for _ in range(4):
        nxt = _strip_group_tree(stripped, _DIALECT_OPEN)
        if nxt == stripped:
            break
        stripped = nxt
    return stripped


def test_strip_accretion_dialect_handles_nested_groups() -> None:
    svg = (
        '<svg><g id="scene"><circle r="1"/>'
        '<g id="accretion-dialect" data-role="accretion-dialect">'
        '<g data-channel="stars"><g><text>24</text></g></g></g>'
        '<g class="repo-tree"/></g></svg>'
    )
    stripped = _strip_accretion_dialect(svg)
    assert 'id="accretion-dialect"' not in stripped
    assert "data-channel" not in stripped
    assert 'class="repo-tree"' in stripped
    assert "<circle r=\"1\"/>" in stripped


def _a1_accretion_metrics(
    *,
    repos: int,
    stars: int,
    commits: int,
    followers: int,
    language: str | None = None,
) -> dict[str, Any]:
    repo_entries: list[dict[str, Any]] = []
    languages: dict[str, int] = {}
    for index in range(repos):
        repo_language = language or ("Python" if index % 2 == 0 else "Go")
        repo_entries.append(
            {
                "name": f"repo-{index}",
                "language": repo_language,
                "stars": max(1, stars // max(1, repos - index)),
                "forks": 1 + index,
                "topics": ["ai" if index % 2 == 0 else "cli"],
                "description": f"Repo {index}",
                "age_months": 4 + index * 3,
                "date": f"2024-01-{index + 1:02d}T12:00:00Z",
            }
        )
        languages[repo_language] = languages.get(repo_language, 0) + 800 * (index + 1)
    return {
        "label": "A1 Isolation",
        "account_created": "2023-01-01T00:00:00Z",
        "repos": repo_entries,
        "repo_visual_order": [repo["name"] for repo in repo_entries],
        "stars": stars,
        "forks": repos,
        "followers": followers,
        "watchers": repos * 2,
        "public_repos": repos,
        "network_count": repos * 2,
        "total_commits": commits,
        "total_prs": max(1, repos * 3),
        "total_issues": repos * 2,
        "total_repos_contributed": repos,
        "public_gists": repos,
        "pr_review_count": repos,
        "contributions_last_year": max(8, commits // 4),
        "contributions_monthly": {"2024-01": max(4, commits // 20)},
        "contributions_daily": {
            f"2024-01-{day:02d}": 1 + (day % 3) for day in range(1, 6)
        },
        "languages": languages,
        "language_count": len(languages),
        "language_diversity": 0.4 + repos * 0.1,
        "topic_clusters": {"ai": max(1, repos // 2), "cli": max(0, repos // 2)},
        "repo_recency_bands": {"fresh": 1, "recent": max(0, repos - 1)},
        "releases": [],
        "recent_merged_prs": [],
        "commit_hour_distribution": {12: 4, 18: 2},
        "star_velocity": {
            "recent_rate": 0.0,
            "peak_rate": 0.0,
            "trend": "flat",
        },
        "contribution_streaks": {
            "current_streak_months": 1,
            "longest_streak_months": 2,
            "streak_active": True,
        },
        "issue_stats": {"open_count": 1, "closed_count": 3},
        "open_issues_count": 1,
    }


def _generators() -> dict[str, Callable[..., str]]:
    global _GENERATOR_FNS
    if _GENERATOR_FNS is None:
        from scripts.art.ferrofluid import generate as generate_ferrofluid
        from scripts.art.genetic_landscape import generate as generate_genetic
        from scripts.art.ink_garden import generate as generate_ink_garden
        from scripts.art.lenia import generate as generate_lenia
        from scripts.art.physarum import generate as generate_physarum
        from scripts.art.topography import generate as generate_topography

        _GENERATOR_FNS = {
            "inkgarden": generate_ink_garden,
            "topo": generate_topography,
            "genetic": generate_genetic,
            "physarum": generate_physarum,
            "lenia": generate_lenia,
            "ferrofluid": generate_ferrofluid,
        }
    return _GENERATOR_FNS


def _render_style(
    style: str,
    metrics: dict[str, Any],
    *,
    monkeypatch: pytest.MonkeyPatch | None = None,
) -> str:
    velocity = metrics.get("star_velocity")
    assert isinstance(velocity, dict)
    assert velocity.get("recent_rate", 1) == 0
    assert velocity.get("peak_rate", 1) == 0
    assert "evolution_state" not in metrics
    assert "render_state" not in metrics
    cache_key = (
        style,
        metrics.get("stars"),
        metrics.get("total_commits"),
        metrics.get("followers"),
        tuple(repo.get("name") for repo in metrics.get("repos", [])),
        tuple(repo.get("language") for repo in metrics.get("repos", [])),
    )
    cached = _RENDER_CACHE.get(cache_key)
    if cached is not None:
        return cached
    if style == "topo":
        import scripts.art.topography as topography_module

        if monkeypatch is not None:
            monkeypatch.setattr(topography_module, "TOPOGRAPHY_GRID_SIZE", 48)
        else:
            topography_module.TOPOGRAPHY_GRID_SIZE = 48
    svg = _generators()[style](
        metrics,
        seed=_A1_SEED,
        maturity=_A1_MATURITY,
        timeline=False,
    )
    _RENDER_CACHE[cache_key] = svg
    return svg


def _picture(svg: str) -> str:
    assert 'id="accretion-dialect"' in svg
    stripped = _strip_accretion_dialect(svg)
    assert 'id="accretion-dialect"' not in stripped
    return stripped


def _count(pattern: str, svg: str) -> int:
    return len(re.findall(pattern, svg))


def _floats(pattern: str, svg: str) -> list[float]:
    return [float(value) for value in re.findall(pattern, svg)]


def _max_or_zero(values: list[float]) -> float:
    return max(values) if values else 0.0


def _primary_repo_mark_count(style: str, svg: str) -> int:
    picture = svg if 'id="accretion-dialect"' not in svg else _picture(svg)
    if style == "inkgarden":
        return _count(r'<g class="repo-tree">', picture)
    if style == "topo":
        return _count(r'data-role="repo-peak"', picture)
    if style == "genetic":
        return _count(r'data-role="genetic-peak-core"', picture)
    if style == "physarum":
        return _count(r'data-role="physarum-node-core"', picture)
    if style == "lenia":
        return _count(r'data-role="lenia-seed-halo"[^>]*data-kind="repo"', picture)
    return _count(r'data-role="ferro-dipole"', picture)


def _firefly_count(svg: str) -> int:
    return _count(r'data-role="ink-glint"', svg)


def _max_stroke_width(svg: str) -> float:
    return _max_or_zero(_floats(r'stroke-width="([0-9.]+)"', svg))


def _ellipse_count(svg: str) -> int:
    return _count(r"<ellipse\b", svg)


def _hex_luminance(color: str) -> float:
    match = re.fullmatch(r"#([0-9a-fA-F]{6})", color.strip())
    if match is None:
        return 0.0
    raw = match.group(1)
    red = int(raw[0:2], 16) / 255.0
    green = int(raw[2:4], 16) / 255.0
    blue = int(raw[4:6], 16) / 255.0
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _attr(tag: str, name: str, default: str = "") -> str:
    match = re.search(rf'\b{re.escape(name)}="([^"]*)"', tag)
    return match.group(1) if match else default


def _genetic_peak_brighter_than_organisms(svg: str) -> bool:
    cores = re.findall(r"<circle\b[^>]*data-role=\"genetic-peak-core\"[^>]*>", svg)
    organisms = re.findall(
        r"<circle\b[^>]*data-role=\"genetic-organism\"[^>]*>",
        svg,
    )
    if not cores:
        return False

    def _ink(tag: str) -> float:
        opacity = float(_attr(tag, "opacity", "1") or 1)
        return _hex_luminance(_attr(tag, "fill", "#000000")) * opacity

    core_ink = min(_ink(tag) for tag in cores)
    if not organisms:
        return core_ink > 0.0 and _max_tagged_radius(svg, "genetic-peak-core") > 0.0
    return core_ink > max(_ink(tag) for tag in organisms)


def _genetic_generation_mark_count(svg: str) -> int:
    return _count(r'data-role="genetic-generation-ring"', svg) + _count(
        r'data-role="genetic-generation-contour"',
        svg,
    )


def _max_tagged_radius(svg: str, role: str) -> float:
    radii: list[float] = []
    for tag in re.findall(rf"<circle\b[^>]*data-role=\"{re.escape(role)}\"[^>]*>", svg):
        radii.append(float(_attr(tag, "r", "0") or 0))
    if not radii:
        for tag in re.findall(
            rf'<circle\b[^>]*r="([0-9.]+)"[^>]*data-role="{re.escape(role)}"[^>]*>',
            svg,
        ):
            radii.append(float(tag))
    return _max_or_zero(radii)


def _tagged_opacity(svg: str, role: str) -> float:
    values: list[float] = []
    role_tags = rf"<[a-zA-Z]+[^>]*data-role=\"{re.escape(role)}\"[^>]*>"
    for tag in re.findall(role_tags, svg):
        raw = _attr(tag, "opacity", "")
        if raw:
            values.append(float(raw))
    return _max_or_zero(values)


def _topo_peak_radius(svg: str) -> float:
    radii: list[float] = []
    for block in re.findall(
        r'<g class="repo-peak"[^>]*>(.*?)</g>', svg, flags=re.DOTALL
    ):
        radii.extend(_floats(r'<circle\b[^>]* r="([0-9.]+)"', block))
        widths = _floats(r'<rect\b[^>]* width="([0-9.]+)"', block)
        radii.extend(width / 2.0 for width in widths)
    return _max_or_zero(radii)


def _topo_settlement_size(svg: str) -> float:
    radii = _floats(
        r'data-role="topo-settlement-mark"[^>]* r="([0-9.]+)"',
        svg,
    )
    if not radii:
        radii = _floats(
            r'<circle[^>]* r="([0-9.]+)"[^>]*data-role="topo-settlement-mark"',
            svg,
        )
    return _max_or_zero(radii)


def _topo_contour_signature(svg: str) -> tuple[int, str]:
    paths = re.findall(r"<path\b[^>]*>", svg)
    return (len(paths), "|".join(paths[:12]))


def _max_ferro_spike_height(svg: str) -> float:
    heights: list[float] = []
    for points in re.findall(
        r'data-role="ferro-spike"[^>]*points="([^"]+)"',
        svg,
    ):
        ys = [float(part.split(",")[1]) for part in points.split() if "," in part]
        if ys:
            heights.append(max(ys) - min(ys))
    return _max_or_zero(heights)


def _ferro_dipole_xs(svg: str) -> list[float]:
    xs = _floats(r'data-role="ferro-dipole"[^>]*\scx="([0-9.]+)"', svg)
    if not xs:
        xs = _floats(r'\scx="([0-9.]+)"[^>]*data-role="ferro-dipole"', svg)
    return xs


def _lenia_satellite_spread(svg: str) -> float:
    host = re.search(
        r'data-role="lenia-seed-halo"[^>]*data-kind="repo"[^>]*\scx="([0-9.]+)"[^>]*\scy="([0-9.]+)"',
        svg,
    )
    if host is None:
        host = re.search(
            r'data-kind="repo"[^>]*data-role="lenia-seed-halo"[^>]*\scx="([0-9.]+)"[^>]*\scy="([0-9.]+)"',
            svg,
        )
    if host is None:
        return 0.0
    hx, hy = float(host.group(1)), float(host.group(2))
    spread = 0.0
    for tag in re.findall(
        r"<[a-zA-Z]+[^>]*data-role=\"lenia-seed-(?:orbit|halo)\"[^>]*>",
        svg,
    ):
        if 'data-kind="repo"' in tag:
            continue
        cx = float(_attr(tag, "cx", "0") or 0)
        cy = float(_attr(tag, "cy", "0") or 0)
        spread = max(spread, math.hypot(cx - hx, cy - hy))
    return spread


def _physarum_vein_mass(svg: str) -> float:
    widths = _floats(
        r'data-role="physarum-vein"[^>]*stroke-width="([0-9.]+)"',
        svg,
    )
    return _max_or_zero(widths) + 0.25 * _count(r'data-role="physarum-vein"', svg)


def _physarum_vein_spread(svg: str) -> float:
    xs = _floats(r'data-role="physarum-vein"[^>]*\s[^>]*(?:x1|cx)="([0-9.]+)"', svg)
    ys = _floats(r'data-role="physarum-vein"[^>]*\s[^>]*(?:y1|cy)="([0-9.]+)"', svg)
    if len(xs) < 2 or len(ys) < 2:
        return 0.0
    return math.hypot(max(xs) - min(xs), max(ys) - min(ys))


def _t0_metrics() -> dict[str, Any]:
    return _a1_accretion_metrics(repos=1, stars=2, commits=20, followers=1)


def _isolated_metrics(channel: str, *, high: bool) -> dict[str, Any]:
    counts = {"repos": 1, "stars": 2, "commits": 20, "followers": 1}
    if channel == "followers" and not high:
        counts["followers"] = 0
    if high:
        counts.update(
            {
                "repos": 4 if channel == "repos" else 1,
                "stars": 24 if channel == "stars" else 2,
                "commits": 400 if channel == "commits" else 20,
                "followers": 18 if channel == "followers" else counts["followers"],
            }
        )
    language = "Python" if channel == "repos" else None
    return _a1_accretion_metrics(language=language, **counts)


@pytest.mark.parametrize("style", tuple(STYLE_DIALECTS))
def test_on_canvas_t0_primary_repo_marks(
    style: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    svg = _picture(_render_style(style, _t0_metrics(), monkeypatch=monkeypatch))
    assert _primary_repo_mark_count(style, svg) >= 1
    if style == "inkgarden":
        assert _ellipse_count(svg) >= 1 or "<path" in svg


@pytest.mark.parametrize("style", tuple(STYLE_DIALECTS))
def test_on_canvas_repos_isolation_moves_primary_mark_count(
    style: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    low = _picture(
        _render_style(
            style, _isolated_metrics("repos", high=False), monkeypatch=monkeypatch
        )
    )
    high = _picture(
        _render_style(
            style, _isolated_metrics("repos", high=True), monkeypatch=monkeypatch
        )
    )
    assert _primary_repo_mark_count(style, high) > _primary_repo_mark_count(style, low)


@pytest.mark.parametrize("style", tuple(STYLE_DIALECTS))
def test_on_canvas_stars_isolation_picture(
    style: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    low = _picture(
        _render_style(
            style, _isolated_metrics("stars", high=False), monkeypatch=monkeypatch
        )
    )
    high = _picture(
        _render_style(
            style, _isolated_metrics("stars", high=True), monkeypatch=monkeypatch
        )
    )
    if style == "inkgarden":
        assert _ellipse_count(high) > _ellipse_count(low)
    elif style == "topo":
        assert _topo_peak_radius(high) > _topo_peak_radius(low)
    elif style == "genetic":
        assert _max_tagged_radius(high, "genetic-peak-core") > _max_tagged_radius(
            low, "genetic-peak-core"
        )
        assert _max_tagged_radius(high, "genetic-peak-glow") > _max_tagged_radius(
            low, "genetic-peak-glow"
        )
    elif style == "physarum":
        assert _max_tagged_radius(high, "physarum-node-core") > _max_tagged_radius(
            low, "physarum-node-core"
        )
    elif style == "lenia":
        assert _max_tagged_radius(high, "lenia-seed-halo") > _max_tagged_radius(
            low, "lenia-seed-halo"
        )
        assert _tagged_opacity(high, "lenia-seed-halo") > _tagged_opacity(
            low, "lenia-seed-halo"
        )
    else:
        assert _max_ferro_spike_height(high) > _max_ferro_spike_height(low)


@pytest.mark.parametrize("style", tuple(STYLE_DIALECTS))
def test_on_canvas_commits_isolation_picture(
    style: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    low = _picture(
        _render_style(
            style, _isolated_metrics("commits", high=False), monkeypatch=monkeypatch
        )
    )
    high = _picture(
        _render_style(
            style, _isolated_metrics("commits", high=True), monkeypatch=monkeypatch
        )
    )
    if style == "inkgarden":
        assert _max_stroke_width(high) > _max_stroke_width(low)
    elif style == "topo":
        low_sig = _topo_contour_signature(low)
        high_sig = _topo_contour_signature(high)
        assert high_sig != low_sig
        followers_only = _picture(
            _render_style(
                style,
                _a1_accretion_metrics(repos=1, stars=2, commits=20, followers=18),
                monkeypatch=monkeypatch,
            )
        )
        assert _topo_contour_signature(followers_only) == low_sig
    elif style == "genetic":
        assert _genetic_generation_mark_count(high) > _genetic_generation_mark_count(
            low
        )
    elif style == "physarum":
        assert _physarum_vein_mass(high) > _physarum_vein_mass(low)
    elif style == "lenia":
        assert _count(r"<circle\b", high) > _count(r"<circle\b", low)
    else:
        assert _count(r'data-role="ferro-ripple"', high) > _count(
            r'data-role="ferro-ripple"', low
        )


@pytest.mark.parametrize("style", tuple(STYLE_DIALECTS))
def test_on_canvas_followers_isolation_picture(
    style: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    low = _picture(
        _render_style(
            style, _isolated_metrics("followers", high=False), monkeypatch=monkeypatch
        )
    )
    high = _picture(
        _render_style(
            style, _isolated_metrics("followers", high=True), monkeypatch=monkeypatch
        )
    )
    if style == "inkgarden":
        assert _firefly_count(low) == 0
        assert _firefly_count(high) > _firefly_count(low)
    elif style == "topo":
        assert _topo_settlement_size(high) > 1.0
        assert _topo_settlement_size(high) > _topo_settlement_size(low)
    elif style == "genetic":
        assert _count(r'data-role="gl-micro-colony"', low) == 0
        assert _count(r'data-role="gl-micro-colony"', high) > 0
        assert _genetic_peak_brighter_than_organisms(high)
    elif style == "physarum":
        assert _physarum_vein_spread(high) >= _physarum_vein_spread(low)
        assert _count(r'data-role="physarum-vein"', high) >= 1
    elif style == "lenia":
        assert _tagged_opacity(high, "lenia-seed-halo") > 0.12
        assert _lenia_satellite_spread(high) > _lenia_satellite_spread(low)
    else:
        assert _tagged_opacity(high, "ferro-dipole") > _tagged_opacity(
            low, "ferro-dipole"
        ) or _max_tagged_radius(high, "ferro-dipole") > _max_tagged_radius(
            low, "ferro-dipole"
        )


def test_on_canvas_ferrofluid_same_language_repos_form_columns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    svg = _picture(
        _render_style(
            "ferrofluid",
            _a1_accretion_metrics(
                repos=4,
                stars=2,
                commits=20,
                followers=1,
                language="Python",
            ),
            monkeypatch=monkeypatch,
        )
    )
    xs = sorted(_ferro_dipole_xs(svg))
    assert xs == pytest.approx([160.0, 320.0, 480.0, 640.0], abs=1.0)
    gaps = [right - left for left, right in zip(xs, xs[1:])]
    assert min(gaps) >= 48.0


def test_element_budget_reports_truthful_state_at_and_beyond_limit() -> None:
    budget = ElementBudget(2)
    assert budget.count == 0
    assert budget.remaining == 2
    assert budget.ok() is True

    budget.add()
    assert budget.count == 1
    assert budget.remaining == 1
    assert budget.ok() is True

    budget.add()
    assert budget.count == 2
    assert budget.remaining == 0
    assert budget.ok() is False

    budget.add(3)
    assert budget.count == 5
    assert budget.remaining == 0
    assert budget.ok() is False
