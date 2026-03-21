"""
Topography Ultimate — Full cartographic illustration generative art.

Dense contour lines with index contours, hillshade, river systems,
vegetation/marsh symbols, trails, compass rose, coordinate grid,
elevation profile cross-section, legend, spot heights, hachures.

Light theme on cream paper.
"""
from __future__ import annotations

from datetime import timedelta
import math

import numpy as np

from .shared import (
    WIDTH, HEIGHT, LANG_HUES,
    seed_hash, hex_frac, oklch, Noise2D,
    compute_maturity,
    contributions_monthly_to_daily_series,
    map_date_to_loop_delay,
    make_radial_gradient,
    normalize_timeline_window,
)

# Map margins
MAP_L, MAP_T = 60, 60
MAP_R, MAP_B = WIDTH - 60, HEIGHT - 110
MAP_W = MAP_R - MAP_L
MAP_H = MAP_B - MAP_T

# Language → terrain character: (noise_freq, amplitude_multiplier)
LANG_TERRAIN: dict[str | None, tuple[float, float]] = {
    "Python": (8.0, 0.04),
    "Jupyter Notebook": (8.0, 0.04),
    "JavaScript": (16.0, 0.06),
    "TypeScript": (16.0, 0.06),
    "HTML": (16.0, 0.05),
    "CSS": (16.0, 0.05),
    "Rust": (12.0, 0.08),
    "Go": (12.0, 0.07),
    "C": (12.0, 0.08),
    "C++": (12.0, 0.08),
    "Shell": (5.0, 0.03),
    "Ruby": (10.0, 0.05),
    "Java": (10.0, 0.05),
    None: (10.0, 0.05),
}

# Language → biome type: (vegetation_pattern, biome_color_tint)
# Maps programming languages to cartographic biome metaphors
LANG_BIOME: dict[str | None, tuple[str, str]] = {
    "Python": ("forest", "#2a6a2e"),        # dense forest / green
    "Jupyter Notebook": ("forest", "#3a7a3e"),
    "JavaScript": ("grassland", "#8a9a3a"),  # open grassland / yellow-green
    "TypeScript": ("grassland", "#7a8a4a"),
    "HTML": ("savanna", "#b0a050"),          # savanna / warm
    "CSS": ("savanna", "#a09848"),
    "Rust": ("rocky", "#8a7060"),            # rocky peaks / brown
    "Go": ("alpine", "#6a8a7a"),             # alpine meadow / blue-green
    "C": ("rocky", "#7a6a5a"),
    "C++": ("rocky", "#8a7a6a"),
    "Shell": ("scrubland", "#7a8a5a"),       # dry scrubland
    "Ruby": ("tropical", "#4a8a3a"),         # tropical / vivid green
    "Java": ("woodland", "#5a7a4a"),         # deciduous woodland
    None: ("mixed", "#6a7a5a"),
}


def _grid_to_map(gx: float, gy: float, cell_w: float, cell_h: float):
    return MAP_L + gx * cell_w, MAP_T + gy * cell_h


# Precomputed once at module level — oklch() is pure, args are constants
# Pure OKLCH ramp: lightness marches 0.45→0.95, hue blue(240)→green(140)→brown(50)→gray(200)
_TOPO_STOPS = [
    (0.00, oklch(0.45, 0.10, 240)),   # deep water — dark blue
    (0.06, oklch(0.52, 0.09, 230)),   # shallow water — lighter blue
    (0.10, oklch(0.55, 0.12, 180)),   # shoreline — blue-green transition
    (0.16, oklch(0.58, 0.17, 140)),   # lowland — green
    (0.22, oklch(0.62, 0.15, 120)),   # low hills — yellow-green
    (0.30, oklch(0.66, 0.13, 100)),   # mid-hills — warm green
    (0.38, oklch(0.70, 0.11, 90)),    # mid-elevation — olive
    (0.46, oklch(0.74, 0.09, 75)),    # upper mid — warm tan
    (0.54, oklch(0.77, 0.08, 65)),    # highlands — light tan
    (0.62, oklch(0.80, 0.07, 55)),    # high terrain — warm brown
    (0.70, oklch(0.82, 0.06, 50)),    # upper highlands — pale brown
    (0.78, oklch(0.85, 0.05, 60)),    # sub-alpine — light brown
    (0.86, oklch(0.88, 0.03, 100)),   # alpine — pale olive-gray
    (0.92, oklch(0.91, 0.02, 200)),   # near-summit — cool gray
    (0.96, oklch(0.93, 0.01, 200)),   # summit ridge — light gray
    (1.00, oklch(0.95, 0.005, 200)),  # snow peaks — near-white gray
]


def _topo_color(e: float) -> str:
    # Swiss warm-humid hypsometric ramp (Imhof-inspired)
    stops = _TOPO_STOPS
    for i in range(len(stops) - 1):
        if e <= stops[i + 1][0]:
            t = (e - stops[i][0]) / max(0.001, stops[i + 1][0] - stops[i][0])
            c1, c2 = stops[i][1], stops[i + 1][1]
            r = int(int(c1[1:3], 16) * (1 - t) + int(c2[1:3], 16) * t)
            g = int(int(c1[3:5], 16) * (1 - t) + int(c2[3:5], 16) * t)
            b = int(int(c1[5:7], 16) * (1 - t) + int(c2[5:7], 16) * t)
            return f"#{r:02x}{g:02x}{b:02x}"
    return stops[-1][1]


def _extract_contours(elevation, grid, level, cell_w, cell_h):
    seg_list = []
    for gy in range(grid - 1):
        for gx in range(grid - 1):
            tl = elevation[gy, gx]
            tr = elevation[gy, gx + 1]
            bl = elevation[gy + 1, gx]
            br = elevation[gy + 1, gx + 1]
            edges = []
            if (tl < level) != (tr < level):
                t = (level - tl) / (tr - tl + 1e-10)
                edges.append(_grid_to_map(gx + t, gy, cell_w, cell_h))
            if (bl < level) != (br < level):
                t = (level - bl) / (br - bl + 1e-10)
                edges.append(_grid_to_map(gx + t, gy + 1, cell_w, cell_h))
            if (tl < level) != (bl < level):
                t = (level - tl) / (bl - tl + 1e-10)
                edges.append(_grid_to_map(gx, gy + t, cell_w, cell_h))
            if (tr < level) != (br < level):
                t = (level - tr) / (br - tr + 1e-10)
                edges.append(_grid_to_map(gx + 1, gy + t, cell_w, cell_h))
            if len(edges) >= 2:
                seg_list.append((edges[0], edges[1]))

    if not seg_list:
        return []

    used = [False] * len(seg_list)
    chains = []
    for start_i in range(len(seg_list)):
        if used[start_i]:
            continue
        used[start_i] = True
        chain = [seg_list[start_i][0], seg_list[start_i][1]]
        changed = True
        while changed:
            changed = False
            last = chain[-1]
            best_d, best_j, best_end = 8.0, -1, 0
            for j in range(len(seg_list)):
                if used[j]:
                    continue
                for end_idx in [0, 1]:
                    pt = seg_list[j][end_idx]
                    d = math.sqrt((pt[0] - last[0]) ** 2 + (pt[1] - last[1]) ** 2)
                    if d < best_d:
                        best_d, best_j, best_end = d, j, end_idx
            if best_j >= 0:
                used[best_j] = True
                chain.append(seg_list[best_j][1 - best_end] if best_end == 0 else seg_list[best_j][0])
                changed = True
        if len(chain) >= 3:
            chains.append(chain)
    return chains


def _point_to_segment_distance(px: float, py: float, p1: tuple, p2: tuple) -> float:
    """Compute the minimum distance from point (px, py) to line segment p1-p2."""
    x1, y1 = p1
    x2, y2 = p2
    dx = x2 - x1
    dy = y2 - y1
    len_sq = dx * dx + dy * dy
    if len_sq < 1e-12:
        return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / len_sq))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return math.sqrt((px - proj_x) ** 2 + (py - proj_y) ** 2)


def _chaikin_smooth(points: list[tuple[float, float]], iterations: int = 1, closed: bool = False) -> list[tuple[float, float]]:
    """Deterministic polyline smoothing for less angular contour and river curves."""
    if len(points) < 3 or iterations <= 0:
        return points
    smoothed = points[:]
    for _ in range(iterations):
        if len(smoothed) < 3:
            break
        nxt: list[tuple[float, float]] = []
        if not closed:
            nxt.append(smoothed[0])
        seg_count = len(smoothed) if closed else len(smoothed) - 1
        for i in range(seg_count):
            p0 = smoothed[i]
            p1 = smoothed[(i + 1) % len(smoothed)]
            qx = 0.75 * p0[0] + 0.25 * p1[0]
            qy = 0.75 * p0[1] + 0.25 * p1[1]
            rx = 0.25 * p0[0] + 0.75 * p1[0]
            ry = 0.25 * p0[1] + 0.75 * p1[1]
            nxt.append((qx, qy))
            nxt.append((rx, ry))
        if not closed:
            nxt.append(smoothed[-1])
        smoothed = nxt
    return smoothed


def generate(
    metrics: dict,
    *,
    seed: str | None = None,
    maturity: float | None = None,
    chrome_maturity: float | None = None,
    timeline: bool = True,
    loop_duration: float = 30.0,
    reveal_fraction: float = 0.93,
) -> str:
    mat = maturity if maturity is not None else compute_maturity(metrics)
    chrome_mat = chrome_maturity if chrome_maturity is not None else mat
    timeline_enabled = bool(timeline and loop_duration > 0)
    growth_mat = 1.0 if timeline_enabled else mat
    chrome_mat = 1.0 if timeline_enabled else chrome_mat

    def _fade(start: float, full: float) -> float:
        """Smooth 0→1 ramp between start and full maturity."""
        return max(0.0, min(1.0, (growth_mat - start) / max(0.001, full - start)))

    h = seed_hash({"seed": seed}) if seed is not None else seed_hash(metrics)
    rng = np.random.default_rng(int(h[:8], 16))
    noise = Noise2D(seed=int(h[8:16], 16))
    noise2 = Noise2D(seed=int(h[16:24], 16))

    monthly = metrics.get("contributions_monthly", {})
    repos = metrics.get("repos", [])
    total_commits = metrics.get("total_commits", 500)
    followers = metrics.get("followers", 10)
    contributions = metrics.get("contributions_last_year", 200)
    forks = metrics.get("forks", 0)
    stars = metrics.get("stars", 0)
    metrics.get("network_count", 0)

    def _repo_date(repo: dict) -> str | None:
        for key in ("date", "created_at", "created", "pushed_at", "updated_at"):
            val = repo.get(key)
            if isinstance(val, str) and val.strip():
                if len(val) >= 10:
                    return val[:10]
                return val
        return None

    timeline_window = normalize_timeline_window(
        [
            {"date": _repo_date(repo)}
            for repo in repos
            if isinstance(repo, dict) and _repo_date(repo)
        ],
        {
            "account_created": metrics.get("account_created"),
            "repos": repos,
            "contributions_monthly": monthly,
        },
        fallback_days=365,
    )
    daily_series = contributions_monthly_to_daily_series(
        monthly,
        reference_year=timeline_window[1].year,
    )
    sorted_daily = sorted(daily_series.items(), key=lambda kv: kv[0])
    total_daily = sum(max(0, int(v)) for _, v in sorted_daily)

    def _date_for_activity_fraction(frac: float) -> str:
        frac = max(0.0, min(1.0, frac))
        if total_daily <= 0 or not sorted_daily:
            start, end = timeline_window
            span = max((end - start).days, 1)
            day_offset = int(round(frac * span))
            return (start + timedelta(days=day_offset)).isoformat()
        threshold = frac * total_daily
        running = 0.0
        for day, count in sorted_daily:
            running += max(0, int(count))
            if running >= threshold:
                return day
        return sorted_daily[-1][0]

    def _month_key_date(month_key: str, idx: int) -> str:
        mk = str(month_key).strip()
        if len(mk) == 7 and mk[4] == "-":
            return f"{mk}-01"
        if mk.isdigit():
            month_n = max(1, min(12, int(mk)))
            return f"{timeline_window[1].year:04d}-{month_n:02d}-01"
        approx_month = 1 + (idx % 12)
        return f"{timeline_window[1].year:04d}-{approx_month:02d}-01"

    def _timeline_style(when: str, opacity: float, cls: str = "tl-reveal") -> str:
        if not timeline_enabled:
            return f'opacity="{opacity:.2f}"'
        delay = map_date_to_loop_delay(
            when,
            timeline_window,
            duration=loop_duration,
            reveal_fraction=reveal_fraction,
        )
        return (
            f'class="{cls}" '
            f'style="--delay:{delay:.3f}s;--to:{max(0.0, min(1.0, opacity)):.3f};'
            f'--dur:{loop_duration:.2f}s" data-delay="{delay:.3f}" data-when="{when}"'
        )

    grid = 200
    elevation = np.zeros((grid, grid))

    # ── 1. Subtle base terrain noise ───────────────────────────────
    terrain_oct = max(3, min(7, 3 + total_commits // 6000))
    for gy in range(grid):
        for gx in range(grid):
            base_terrain = noise.fbm(gx / grid * 6, gy / grid * 6, terrain_oct) * 0.08
            macro_relief = noise2.fbm(gx / grid * 2.2 + 13.0, gy / grid * 2.2 + 7.0, 3) * 0.06
            ridge_field = abs(noise2.fbm(gx / grid * 9.0 + 91.0, gy / grid * 9.0 + 37.0, 2)) * 0.02
            elevation[gy, gx] = base_terrain + macro_relief + ridge_field

    # ── 2. Repos as PRIMARY terrain features (distinct hills) ──────
    # Relative scaling: normalize to this profile's own data range
    all_stars = [r.get("stars", 0) for r in repos] if repos else [1]
    all_ages = [r.get("age_months", 6) for r in repos] if repos else [6]
    max_stars = max(1, max(all_stars))
    min_stars = min(all_stars)
    max_age = max(6, max(all_ages))
    min_age = min(all_ages)

    repo_positions = []
    for ri, repo in enumerate(repos):
        repo_stars = repo.get("stars", 0)
        age = repo.get("age_months", 6)

        # Stars -> peak height RELATIVE to this profile's range
        star_frac = (repo_stars - min_stars) / max(1, max_stars - min_stars) if max_stars > min_stars else 0.5
        peak_h = 0.15 + star_frac * 0.6

        # Age -> hill width RELATIVE to this profile's range
        age_frac = (age - min_age) / max(1, max_age - min_age) if max_age > min_age else 0.5
        sigma = 0.03 + age_frac * 0.08

        # Organic position: hash-seeded with repulsion to avoid overlap
        a_idx = (ri * 4) % 56
        (ri * 4 + 4) % 56
        hx = hex_frac(h, a_idx, min(a_idx + 4, 64))
        c_idx = (ri * 4 + 2) % 56
        (ri * 4 + 6) % 56
        hy = hex_frac(h, c_idx, min(c_idx + 4, 64))
        rcx = 0.15 + hx * 0.7
        rcy = 0.15 + hy * 0.7

        # Push apart from existing hills (simple repulsion)
        min_sep = 0.12
        for _ in range(4):
            for px, py, _ in repo_positions:
                ddx, ddy = rcx - px, rcy - py
                d = math.sqrt(ddx * ddx + ddy * ddy)
                if 0.001 < d < min_sep:
                    push = (min_sep - d) * 0.6
                    rcx += ddx / d * push
                    rcy += ddy / d * push
            rcx = max(0.12, min(0.88, rcx))
            rcy = max(0.12, min(0.88, rcy))

        # Language-specific terrain texture on this hill
        lang = repo.get("language")
        lang_seed = int(seed_hash({"language": str(lang)})[:4], 16)
        tex_freq, tex_amp = LANG_TERRAIN.get(lang, (10.0, 0.05))

        y_lo = max(0, int((rcy - 3 * sigma) * grid))
        y_hi = min(grid, int((rcy + 3 * sigma) * grid) + 1)
        x_lo = max(0, int((rcx - 3 * sigma) * grid))
        x_hi = min(grid, int((rcx + 3 * sigma) * grid) + 1)
        for gy in range(y_lo, y_hi):
            for gx in range(x_lo, x_hi):
                fx, fy = gx / grid, gy / grid
                dx, dy = fx - rcx, fy - rcy
                base_gaussian = peak_h * math.exp(-(dx * dx + dy * dy) / (2 * sigma * sigma))
                # Language-specific texture frequency and amplitude
                texture = noise.noise(fx * tex_freq + lang_seed, fy * tex_freq) * tex_amp * base_gaussian
                ridge_tex = abs(noise2.noise((fx + lang_seed * 1e-4) * (tex_freq * 0.7), fy * (tex_freq * 0.9))) * 0.018
                elevation[gy, gx] += base_gaussian + texture + ridge_tex * base_gaussian

        repo_positions.append((rcx, rcy, repo))

    # ── 3. Ridgeline backbone from monthly contributions ───────────
    max_m = max(monthly.values()) if monthly else 100
    months_sorted = sorted(monthly.keys())
    if len(months_sorted) >= 2:
        ridge_r = 0.2
        for i in range(len(months_sorted)):
            j = (i + 1) % len(months_sorted)
            mkey1, mkey2 = months_sorted[i], months_sorted[j]
            intensity = (monthly[mkey1] + monthly[mkey2]) / (2 * max(1, max_m))
            angle1 = -math.pi / 2 + i * 2 * math.pi / len(months_sorted)
            angle2 = -math.pi / 2 + j * 2 * math.pi / len(months_sorted)
            p1 = (0.5 + ridge_r * math.cos(angle1), 0.5 + ridge_r * math.sin(angle1))
            p2 = (0.5 + ridge_r * math.cos(angle2), 0.5 + ridge_r * math.sin(angle2))
            ridge_height = intensity * 0.18
            ridge_width = 0.025
            # Bounding box for the ridge segment
            min_rx = min(p1[0], p2[0]) - 3 * ridge_width
            max_rx = max(p1[0], p2[0]) + 3 * ridge_width
            min_ry = min(p1[1], p2[1]) - 3 * ridge_width
            max_ry = max(p1[1], p2[1]) + 3 * ridge_width
            y_lo = max(0, int(min_ry * grid))
            y_hi = min(grid, int(max_ry * grid) + 1)
            x_lo = max(0, int(min_rx * grid))
            x_hi = min(grid, int(max_rx * grid) + 1)
            for gy in range(y_lo, y_hi):
                for gx in range(x_lo, x_hi):
                    fx, fy = gx / grid, gy / grid
                    d = _point_to_segment_distance(fx, fy, p1, p2)
                    elevation[gy, gx] += ridge_height * math.exp(-(d * d) / (2 * ridge_width * ridge_width))

    # ── 4. Central peak (always prominent, scaled to profile) ──────
    # Central peak is always the tallest — height relative to repo count
    central_height = 0.45 + 0.25 * min(1.0, len(repos) / max(1, len(repos) + 2))
    central_sigma = 0.06 + 0.04 * min(1.0, len(repos) / 12)
    for gy in range(grid):
        for gx in range(grid):
            fx, fy = gx / grid, gy / grid
            dx, dy = fx - 0.5, fy - 0.5
            elevation[gy, gx] += central_height * math.exp(-(dx * dx + dy * dy) / (2 * central_sigma * central_sigma))

    # ── 5. River valleys from saddle points between major peaks ────
    n_rivers = max(2, min(8, 2 + forks // 4))
    river_paths = []
    # Sort repos by peak height to find top peaks for saddle-point river starts
    sorted_repos = sorted(repo_positions, key=lambda rp: rp[2].get("stars", 0), reverse=True)
    top_peaks = sorted_repos[:max(3, min(len(sorted_repos), 5))]
    river_starts = []
    if len(top_peaks) >= 2:
        for pi in range(len(top_peaks)):
            for pj in range(pi + 1, len(top_peaks)):
                mid_x = (top_peaks[pi][0] + top_peaks[pj][0]) / 2
                mid_y = (top_peaks[pi][1] + top_peaks[pj][1]) / 2
                river_starts.append((mid_x, mid_y))
        river_starts = river_starts[:n_rivers]
    else:
        # Fallback: random starts if not enough peaks
        for rvi in range(n_rivers):
            river_starts.append((0.5 + rng.uniform(-0.3, 0.3), 0.5 + rng.uniform(-0.3, 0.3)))

    # Pad with random starts if we need more rivers
    while len(river_starts) < n_rivers:
        river_starts.append((0.5 + rng.uniform(-0.3, 0.3), 0.5 + rng.uniform(-0.3, 0.3)))

    for rvi in range(n_rivers):
        rx, ry = river_starts[rvi]
        rpts = [(rx, ry)]
        for _ in range(80):
            gxi = min(grid - 2, max(1, int(rx * grid)))
            gyi = min(grid - 2, max(1, int(ry * grid)))
            dedx = (elevation[gyi, gxi + 1] - elevation[gyi, gxi - 1]) / 2
            dedy = (elevation[gyi + 1, gxi] - elevation[gyi - 1, gxi]) / 2
            nv = noise2.noise(rx * 8 + rvi * 10, ry * 8) * 0.3
            rx += -dedx * 0.9 + nv * 0.022
            ry += -dedy * 0.9 + noise2.noise(rx * 5, ry * 5 + rvi * 5) * 0.022
            rx = max(0.02, min(0.98, rx))
            ry = max(0.02, min(0.98, ry))
            rpts.append((rx, ry))
            gxi2 = min(grid - 1, max(0, int(rx * grid)))
            gyi2 = min(grid - 1, max(0, int(ry * grid)))
            for dy in range(-2, 3):
                for dx2 in range(-2, 3):
                    yi = min(grid - 1, max(0, gyi2 + dy))
                    xi = min(grid - 1, max(0, gxi2 + dx2))
                    d = math.sqrt(dy * dy + dx2 * dx2)
                    if d < 3:
                        elevation[yi, xi] -= 0.03 * (1 - d / 3)
        main_path = _chaikin_smooth(rpts, iterations=2)
        river_paths.append(main_path)

        # Tributaries: branch from upper reaches and merge downstream.
        trib_count = 1 + (1 if forks > 20 else 0) + (1 if contributions > 1200 else 0)
        branch_origin_max = max(6, len(main_path) // 3)
        for tbi in range(min(3, trib_count)):
            bidx = 3 + int((tbi + 1) * branch_origin_max / (min(3, trib_count) + 1))
            if bidx >= len(main_path):
                continue
            brx, bry = main_path[bidx]
            tpts = [(brx, bry)]
            for _ in range(24):
                gxi = min(grid - 2, max(1, int(brx * grid)))
                gyi = min(grid - 2, max(1, int(bry * grid)))
                dedx = (elevation[gyi, gxi + 1] - elevation[gyi, gxi - 1]) / 2
                dedy = (elevation[gyi + 1, gxi] - elevation[gyi - 1, gxi]) / 2
                nudge = noise2.noise(brx * 12 + 17 * (tbi + 1), bry * 12 + 11 * (rvi + 1))
                brx += -dedx * 0.55 + nudge * 0.012
                bry += -dedy * 0.55 + noise2.noise(brx * 7, bry * 7 + 9 * (tbi + 1)) * 0.01
                brx = max(0.02, min(0.98, brx))
                bry = max(0.02, min(0.98, bry))
                tpts.append((brx, bry))
            river_paths.append(_chaikin_smooth(tpts, iterations=1))

    # Normalize
    e_min, e_max = elevation.min(), elevation.max()
    if e_max > e_min:
        elevation = (elevation - e_min) / (e_max - e_min)

    # Domain warp for organic contour feel
    warp_noise = Noise2D(seed=int(h[24:32], 16))
    warped = np.zeros_like(elevation)
    for gy in range(grid):
        for gx in range(grid):
            wx = warp_noise.fbm(gx / 40, gy / 40, 2) * 2.5
            wy = warp_noise.fbm(gx / 40 + 50, gy / 40 + 50, 2) * 2.5
            sx = max(0, min(grid - 1, gx + wx))
            sy = max(0, min(grid - 1, gy + wy))
            x0, y0 = int(sx), int(sy)
            x1_, y1_ = min(x0 + 1, grid - 1), min(y0 + 1, grid - 1)
            fx, fy = sx - x0, sy - y0
            warped[gy, gx] = (elevation[y0, x0] * (1 - fx) * (1 - fy) +
                              elevation[y0, x1_] * fx * (1 - fy) +
                              elevation[y1_, x0] * (1 - fx) * fy +
                              elevation[y1_, x1_] * fx * fy)
    elevation = warped

    cell_w = MAP_W / grid
    cell_h = MAP_H / grid

    # Hillshade
    hillshade = np.zeros((grid, grid))
    relief = np.zeros((grid, grid))
    sun_az = math.radians(315)
    sun_alt = math.radians(32)
    sun_az2 = math.radians(36)
    sun_alt2 = math.radians(18)
    for gy in range(1, grid - 1):
        for gx in range(1, grid - 1):
            dzdx = (elevation[gy, gx + 1] - elevation[gy, gx - 1]) / 2
            dzdy = (elevation[gy + 1, gx] - elevation[gy - 1, gx]) / 2
            slope = math.atan(math.sqrt(dzdx ** 2 + dzdy ** 2) * 5)
            aspect = math.atan2(-dzdy, dzdx)
            hs = math.cos(sun_alt) * math.cos(slope) + math.sin(sun_alt) * math.sin(slope) * math.cos(sun_az - aspect)
            hs2 = math.cos(sun_alt2) * math.cos(slope) + math.sin(sun_alt2) * math.sin(slope) * math.cos(sun_az2 - aspect)
            hillshade[gy, gx] = max(0, min(1, 0.68 * ((hs + 1) / 2) + 0.32 * ((hs2 + 1) / 2)))
            curvature = abs(
                elevation[gy, gx + 1]
                + elevation[gy, gx - 1]
                + elevation[gy + 1, gx]
                + elevation[gy - 1, gx]
                - 4 * elevation[gy, gx]
            )
            relief[gy, gx] = max(0.0, min(1.0, curvature * 18.0 + math.sqrt(dzdx * dzdx + dzdy * dzdy) * 6.0))

    # ══════════════════════════════════════════════════════════════
    # BUILD SVG
    # ══════════════════════════════════════════════════════════════
    P = []
    P.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">')
    if timeline_enabled:
        P.append(
            "<style>"
            "@keyframes topoReveal{0%{opacity:0}100%{opacity:var(--to,1)}}"
            ".tl-reveal{opacity:0;animation:topoReveal .8s ease-out var(--delay,0s) both}"
            ".tl-soft{animation-duration:1.15s}"
            ".tl-crisp{animation-duration:.65s}"
            "</style>"
        )

    P.append('<defs>')
    # Paper texture filter
    P.append('''<filter id="paper" x="0%" y="0%" width="100%" height="100%"
    color-interpolation-filters="linearRGB">
    <feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="5"
      seed="2" stitchTiles="stitch" result="noise"/>
    <feDiffuseLighting in="noise" lighting-color="#ffffff" surfaceScale="1.2" result="lit">
      <feDistantLight azimuth="45" elevation="55"/>
    </feDiffuseLighting>
    <feComposite operator="in" in="lit" in2="SourceGraphic"/>
  </filter>''')
    # Vegetation patterns
    P.append('''<pattern id="trees" width="18" height="16" patternUnits="userSpaceOnUse">
    <circle cx="5" cy="6" r="3" fill="none" stroke="#4a7a2e" stroke-width="0.5" opacity="0.18"/>
    <line x1="5" y1="9" x2="5" y2="13" stroke="#5a6a3a" stroke-width="0.35" opacity="0.12"/>
    <circle cx="14" cy="4" r="2.2" fill="none" stroke="#4a7a2e" stroke-width="0.4" opacity="0.15"/>
    <line x1="14" y1="6.2" x2="14" y2="10" stroke="#5a6a3a" stroke-width="0.3" opacity="0.10"/>
    <circle cx="9" cy="11" r="1.8" fill="none" stroke="#4a7a2e" stroke-width="0.35" opacity="0.12"/>
    <line x1="9" y1="12.8" x2="9" y2="15" stroke="#5a6a3a" stroke-width="0.25" opacity="0.08"/>
  </pattern>''')
    P.append('''<pattern id="marsh" width="14" height="10" patternUnits="userSpaceOnUse">
    <line x1="2" y1="7" x2="2" y2="2" stroke="#5b92c7" stroke-width="0.35" opacity="0.2"/>
    <line x1="1" y1="3" x2="3" y2="3" stroke="#5b92c7" stroke-width="0.3" opacity="0.15"/>
    <line x1="7" y1="7" x2="7" y2="3" stroke="#5b92c7" stroke-width="0.35" opacity="0.2"/>
    <line x1="6" y1="4" x2="8" y2="4" stroke="#5b92c7" stroke-width="0.3" opacity="0.15"/>
    <line x1="12" y1="7" x2="12" y2="2" stroke="#5b92c7" stroke-width="0.35" opacity="0.2"/>
    <line x1="11" y1="3" x2="13" y2="3" stroke="#5b92c7" stroke-width="0.3" opacity="0.15"/>
    <line x1="0" y1="8" x2="14" y2="8" stroke="#5b92c7" stroke-width="0.2" opacity="0.1"/>
  </pattern>''')
    P.append('''<pattern id="waves" width="24" height="8" patternUnits="userSpaceOnUse">
    <path d="M0,4 Q6,1 12,4 Q18,7 24,4" fill="none" stroke="#5b92c7" stroke-width="0.35" opacity="0.18"/>
    <path d="M0,7 Q6,4 12,7 Q18,10 24,7" fill="none" stroke="#5b92c7" stroke-width="0.25" opacity="0.10"/>
  </pattern>''')
    # Rock scree pattern for high elevations
    P.append('''<pattern id="scree" width="10" height="10" patternUnits="userSpaceOnUse">
    <path d="M2,3 L3,1 L4,3Z" fill="none" stroke="#8a7a6a" stroke-width="0.3" opacity="0.15"/>
    <path d="M7,7 L8,5 L9,7Z" fill="none" stroke="#8a7a6a" stroke-width="0.3" opacity="0.12"/>
    <circle cx="5" cy="8" r="0.4" fill="#8a7a6a" opacity="0.10"/>
  </pattern>''')
    # Biome-specific vegetation patterns (language → cartographic vegetation type)
    # Forest biome — dense deciduous canopy with stippling (Python, Ruby, etc.)
    P.append('''<pattern id="biome_forest" width="16" height="14" patternUnits="userSpaceOnUse">
    <circle cx="4" cy="5" r="3.5" fill="none" stroke="#2a6a2e" stroke-width="0.5" opacity="0.16"/>
    <circle cx="12" cy="4" r="2.8" fill="none" stroke="#3a7a3e" stroke-width="0.45" opacity="0.14"/>
    <circle cx="8" cy="10" r="2.5" fill="none" stroke="#2a6a2e" stroke-width="0.4" opacity="0.12"/>
    <circle cx="4" cy="5" r="1.2" fill="#2a6a2e" opacity="0.06"/>
    <circle cx="12" cy="4" r="0.9" fill="#3a7a3e" opacity="0.05"/>
  </pattern>''')
    # Grassland biome — open tufts and stipples (JavaScript, TypeScript)
    P.append('''<pattern id="biome_grassland" width="12" height="10" patternUnits="userSpaceOnUse">
    <line x1="3" y1="8" x2="3" y2="4" stroke="#8a9a3a" stroke-width="0.3" opacity="0.14"/>
    <line x1="2" y1="5" x2="4" y2="4" stroke="#8a9a3a" stroke-width="0.25" opacity="0.10"/>
    <line x1="9" y1="7" x2="9" y2="3.5" stroke="#7a8a4a" stroke-width="0.3" opacity="0.12"/>
    <line x1="8" y1="4.5" x2="10" y2="3.5" stroke="#7a8a4a" stroke-width="0.25" opacity="0.10"/>
    <circle cx="6" cy="6" r="0.3" fill="#8a9a3a" opacity="0.10"/>
  </pattern>''')
    # Alpine biome — sparse dots and tiny flower marks (Go)
    P.append('''<pattern id="biome_alpine" width="14" height="12" patternUnits="userSpaceOnUse">
    <circle cx="3" cy="4" r="0.5" fill="#6a8a7a" opacity="0.12"/>
    <circle cx="10" cy="3" r="0.4" fill="#6a8a7a" opacity="0.10"/>
    <circle cx="7" cy="8" r="0.6" fill="#7a9a8a" opacity="0.10"/>
    <circle cx="12" cy="10" r="0.3" fill="#6a8a7a" opacity="0.08"/>
    <path d="M5,9 L5.5,7.5 L6,9" fill="none" stroke="#6a8a7a" stroke-width="0.2" opacity="0.10"/>
  </pattern>''')
    # Rocky biome — cross-hatching for bare rock (Rust, C, C++)
    P.append('''<pattern id="biome_rocky" width="10" height="10" patternUnits="userSpaceOnUse">
    <line x1="0" y1="0" x2="10" y2="10" stroke="#8a7060" stroke-width="0.2" opacity="0.10"/>
    <line x1="10" y1="0" x2="0" y2="10" stroke="#7a6a5a" stroke-width="0.2" opacity="0.08"/>
    <path d="M3,2 L4,0.5 L5,2Z" fill="none" stroke="#8a7a6a" stroke-width="0.25" opacity="0.10"/>
  </pattern>''')
    # Scrubland biome — sparse low vegetation (Shell)
    P.append('''<pattern id="biome_scrubland" width="16" height="12" patternUnits="userSpaceOnUse">
    <circle cx="4" cy="7" r="1.8" fill="none" stroke="#7a8a5a" stroke-width="0.35" opacity="0.12"/>
    <circle cx="12" cy="5" r="1.4" fill="none" stroke="#7a8a5a" stroke-width="0.3" opacity="0.10"/>
    <circle cx="8" cy="10" r="0.5" fill="#7a8a5a" opacity="0.08"/>
  </pattern>''')
    # Vignette — dark edge framing
    P.append(make_radial_gradient('vigTopo', '50%', '48%', '65%',
        [('0%', '#000000', 0.0), ('55%', '#000000', 0.0),
         ('85%', '#1a120a', 0.12), ('100%', '#100a04', 0.1 + chrome_mat * 0.25)]))
    P.append('</defs>')

    # Background with paper texture
    P.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#f5f0e8"/>')
    P.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#f5f0e8" filter="url(#paper)" opacity="0.5"/>')

    # ── Elevation fill + hillshade ────────────────────────────────
    fill_step = 2
    for gy in range(0, grid, fill_step):
        for gx in range(0, grid, fill_step):
            e = elevation[gy, gx]
            hs = hillshade[min(gy, grid - 1), min(gx, grid - 1)]
            c = _topo_color(e)
            r_c = int(c[1:3], 16)
            g_c = int(c[3:5], 16)
            b_c = int(c[5:7], 16)
            sf = 0.30 + hs * 0.95
            rf = relief[min(gy, grid - 1), min(gx, grid - 1)]
            sf *= 0.94 + rf * 0.26
            r_c = max(0, min(255, int(r_c * sf)))
            g_c = max(0, min(255, int(g_c * sf)))
            b_c = max(0, min(255, int(b_c * sf)))
            mx, my = _grid_to_map(gx, gy, cell_w, cell_h)
            elev_op = min(0.8, 0.1 + growth_mat * 1.5)
            elev_when = _date_for_activity_fraction(e)
            P.append(f'<rect x="{mx:.1f}" y="{my:.1f}" width="{cell_w*fill_step+.5:.1f}" height="{cell_h*fill_step+.5:.1f}" '
                     f'fill="#{r_c:02x}{g_c:02x}{b_c:02x}" {_timeline_style(elev_when, elev_op, "tl-reveal tl-soft")}/>')

    # ── Water + vegetation overlays ───────────────────────────────
    # Biome type → SVG pattern id mapping
    _BIOME_PATTERN: dict[str, str] = {
        "forest": "biome_forest", "grassland": "biome_grassland",
        "alpine": "biome_alpine", "rocky": "biome_rocky",
        "scrubland": "biome_scrubland", "savanna": "biome_grassland",
        "tropical": "biome_forest", "woodland": "biome_forest",
        "mixed": "trees",
    }

    for gy in range(0, grid, 3):
        for gx in range(0, grid, 3):
            e = elevation[min(gy, grid - 1), min(gx, grid - 1)]
            if e < 0.12:
                mx, my = _grid_to_map(gx, gy, cell_w, cell_h)
                P.append(f'<rect x="{mx:.1f}" y="{my:.1f}" width="{cell_w*3+.5:.1f}" height="{cell_h*3+.5:.1f}" fill="url(#waves)" opacity="0.5"/>')
    for gy in range(0, grid, 6):
        for gx in range(0, grid, 6):
            e = elevation[min(gy, grid - 1), min(gx, grid - 1)]
            mx, my = _grid_to_map(gx, gy, cell_w, cell_h)
            sw, sh = cell_w * 6, cell_h * 6
            fx_norm, fy_norm = gx / grid, gy / grid

            if 0.10 < e < 0.93:
                # Find nearest repo peak to determine biome-specific vegetation
                nearest_biome = "mixed"
                nearest_dist = float("inf")
                for rpx, rpy, rrepo in repo_positions:
                    d = math.sqrt((fx_norm - rpx) ** 2 + (fy_norm - rpy) ** 2)
                    if d < nearest_dist:
                        nearest_dist = d
                        lang = rrepo.get("language")
                        nearest_biome = LANG_BIOME.get(lang, LANG_BIOME[None])[0]

                # Elevation-correlated biome placement:
                #   forest only below 0.6, rocky only above 0.7, alpine only above 0.6,
                #   grassland/savanna in mid-range (0.3-0.7)
                _elev_ok = {
                    "forest": e < 0.6,
                    "woodland": e < 0.6,
                    "tropical": e < 0.6,
                    "rocky": e > 0.7,
                    "alpine": e > 0.6,
                    "grassland": 0.3 < e < 0.7,
                    "savanna": 0.3 < e < 0.7,
                    "scrubland": 0.2 < e < 0.6,
                    "mixed": 0.15 < e < 0.7,
                }
                biome_fits_elevation = _elev_ok.get(nearest_biome, True)

                if 0.10 < e < 0.20:
                    # Low wetland: marsh overlay
                    marsh_op = 0.4 * _fade(0.10, 0.30)
                    if marsh_op > 0:
                        marsh_when = _date_for_activity_fraction(0.15)
                        P.append(f'<rect x="{mx:.1f}" y="{my:.1f}" width="{sw:.1f}" height="{sh:.1f}" fill="url(#marsh)" {_timeline_style(marsh_when, marsh_op)}/>')
                elif 0.80 < e < 0.93:
                    # High elevation: scree overlay
                    scree_op = 0.4 * _fade(0.15, 0.40)
                    if scree_op > 0:
                        scree_when = _date_for_activity_fraction(e)
                        P.append(f'<rect x="{mx:.1f}" y="{my:.1f}" width="{sw:.1f}" height="{sh:.1f}" fill="url(#scree)" {_timeline_style(scree_when, scree_op)}/>')
                elif 0.20 < e < 0.80 and biome_fits_elevation:
                    # Use biome-specific pattern if close to a repo peak and elevation matches
                    pattern_id = _BIOME_PATTERN.get(nearest_biome, "trees") if nearest_dist < 0.25 else "trees"
                    tree_op = 0.5 * _fade(0.05, 0.25)
                    # Proximity boost: closer to repo = denser vegetation
                    if nearest_dist < 0.15:
                        tree_op *= 1.0 + 0.4 * (1.0 - nearest_dist / 0.15)
                    if tree_op > 0:
                        tree_when = _date_for_activity_fraction(0.25 + 0.6 * e)
                        P.append(f'<rect x="{mx:.1f}" y="{my:.1f}" width="{sw:.1f}" height="{sh:.1f}" fill="url(#{pattern_id})" {_timeline_style(tree_when, min(0.6, tree_op))}/>')

    # ── Lakes/ponds in low-lying depressions ────────────────────────
    lake_fade = _fade(0.15, 0.40)
    if lake_fade > 0:
        lake_spots = []
        for gy_lk in range(4, grid - 4, 10):
            for gx_lk in range(4, grid - 4, 10):
                e = elevation[gy_lk, gx_lk]
                if e < 0.08:
                    is_basin = all(
                        elevation[min(grid - 1, max(0, gy_lk + dy_l)), min(grid - 1, max(0, gx_lk + dx_l))] >= e - 0.02
                        for dy_l in range(-3, 4, 2) for dx_l in range(-3, 4, 2)
                    )
                    if is_basin:
                        mx_lk, my_lk = _grid_to_map(gx_lk, gy_lk, cell_w, cell_h)
                        lake_spots.append((mx_lk, my_lk))
        for lk_x, lk_y in lake_spots[:3]:
            lr = 6 + rng.uniform(0, 10)
            lry = lr * rng.uniform(0.55, 0.85)
            la = rng.uniform(-15, 15)
            P.append(f'<ellipse cx="{lk_x:.1f}" cy="{lk_y:.1f}" rx="{lr:.1f}" ry="{lry:.1f}" '
                     f'fill="#a8d4f0" stroke="#5b92c7" stroke-width="0.3" opacity="{0.3 * lake_fade:.2f}" '
                     f'transform="rotate({la:.0f},{lk_x:.0f},{lk_y:.0f})"/>')
            # Bathymetric contour rings
            for ring_i in range(1, 3):
                rf = 1 - ring_i * 0.3
                P.append(f'<ellipse cx="{lk_x:.1f}" cy="{lk_y:.1f}" rx="{lr * rf:.1f}" ry="{lry * rf:.1f}" '
                         f'fill="none" stroke="#5b92c7" stroke-width="0.2" opacity="0.12" '
                         f'transform="rotate({la:.0f},{lk_x:.0f},{lk_y:.0f})"/>')

    # ── Rivers (widening downstream, fade in gradually) ───────────
    # Data mapping: activity (contributions) -> river flow volume
    activity_flow = min(2.0, 1.0 + contributions / 1500.0)
    river_fade = _fade(0.03, 0.15)
    rlabel_fade = _fade(0.15, 0.35)
    # Desaturated OKLCH blue for rivers
    river_color = oklch(0.55, 0.08, 240)
    river_shadow_color = oklch(0.40, 0.06, 240)
    river_highlight_color = oklch(0.73, 0.05, 225)
    for rvi, rpts in enumerate(river_paths if river_fade > 0 else []):
        if len(rpts) < 3:
            continue
        # Draw river in segments with width varying by downstream distance
        # Width: 0.3px at start → 1.2px at end, scaled by activity
        n_seg = len(rpts) - 1
        for j in range(0, n_seg - 1, 2):
            frac = j / max(1, n_seg)
            sw_r = (0.3 + frac * 0.9) * activity_flow
            op_r = (0.35 + frac * 0.25) * river_fade
            x1r = MAP_L + rpts[j][0] * MAP_W
            y1r = MAP_T + rpts[j][1] * MAP_H
            if j + 2 < len(rpts):
                x2r = MAP_L + rpts[j + 1][0] * MAP_W
                y2r = MAP_T + rpts[j + 1][1] * MAP_H
                x3r = MAP_L + rpts[j + 2][0] * MAP_W
                y3r = MAP_T + rpts[j + 2][1] * MAP_H
                # Shadow-side darkening stroke offset 0.5px
                seg_when = _date_for_activity_fraction(frac)
                P.append(f'<path d="M{x1r+0.5:.1f},{y1r+0.5:.1f} Q{x2r+0.5:.1f},{y2r+0.5:.1f} {x3r+0.5:.1f},{y3r+0.5:.1f}" '
                         f'fill="none" stroke="{river_shadow_color}" stroke-width="{sw_r*0.85:.2f}" {_timeline_style(seg_when, op_r*0.45, "tl-reveal tl-crisp")} stroke-linecap="round"/>')
                P.append(f'<path d="M{x1r:.1f},{y1r:.1f} Q{x2r:.1f},{y2r:.1f} {x3r:.1f},{y3r:.1f}" '
                         f'fill="none" stroke="{river_color}" stroke-width="{sw_r:.2f}" {_timeline_style(seg_when, op_r, "tl-reveal tl-crisp")} stroke-linecap="round"/>')
                P.append(f'<path d="M{x1r-0.25:.1f},{y1r-0.25:.1f} Q{x2r-0.25:.1f},{y2r-0.25:.1f} {x3r-0.25:.1f},{y3r-0.25:.1f}" '
                         f'fill="none" stroke="{river_highlight_color}" stroke-width="{max(0.18, sw_r*0.28):.2f}" {_timeline_style(seg_when, op_r*0.35, "tl-reveal tl-crisp")} stroke-linecap="round"/>')
            else:
                x2r = MAP_L + rpts[j + 1][0] * MAP_W
                y2r = MAP_T + rpts[j + 1][1] * MAP_H
                # Shadow-side darkening stroke offset 0.5px
                seg_when = _date_for_activity_fraction(frac)
                P.append(f'<line x1="{x1r+0.5:.1f}" y1="{y1r+0.5:.1f}" x2="{x2r+0.5:.1f}" y2="{y2r+0.5:.1f}" '
                         f'stroke="{river_shadow_color}" stroke-width="{sw_r*0.85:.2f}" {_timeline_style(seg_when, op_r*0.45, "tl-reveal tl-crisp")} stroke-linecap="round"/>')
                P.append(f'<line x1="{x1r:.1f}" y1="{y1r:.1f}" x2="{x2r:.1f}" y2="{y2r:.1f}" '
                         f'stroke="{river_color}" stroke-width="{sw_r:.2f}" {_timeline_style(seg_when, op_r, "tl-reveal tl-crisp")} stroke-linecap="round"/>')
                P.append(f'<line x1="{x1r-0.25:.1f}" y1="{y1r-0.25:.1f}" x2="{x2r-0.25:.1f}" y2="{y2r-0.25:.1f}" '
                         f'stroke="{river_highlight_color}" stroke-width="{max(0.18, sw_r*0.28):.2f}" {_timeline_style(seg_when, op_r*0.35, "tl-reveal tl-crisp")} stroke-linecap="round"/>')
        if len(rpts) > 10 and rlabel_fade > 0:
            mid = len(rpts) // 4
            # Build guide path from river points for textPath
            guide_end = min(mid + 5, len(rpts))
            guide_pts = rpts[mid:guide_end]
            if len(guide_pts) >= 2:
                guide_d = f"M{MAP_L + guide_pts[0][0]*MAP_W:.0f},{MAP_T + guide_pts[0][1]*MAP_H:.0f}"
                for gp in guide_pts[1:]:
                    guide_d += f" L{MAP_L + gp[0]*MAP_W:.0f},{MAP_T + gp[1]*MAP_H:.0f}"
                P.append(f'<path id="rv{rvi}" d="{guide_d}" fill="none" stroke="none"/>')
                # Halo
                P.append(f'<text font-family="Georgia,serif" font-size="6.5" fill="#f5f0e8" '
                         f'opacity="{0.5 * rlabel_fade:.2f}" font-style="italic" '
                         f'stroke="#f5f0e8" stroke-width="2.5" stroke-linejoin="round">'
                         f'<textPath href="#rv{rvi}" startOffset="50%" text-anchor="middle">R. {rvi+1}</textPath></text>')
                # Label
                P.append(f'<text font-family="Georgia,serif" font-size="6.5" fill="#1a4f8a" '
                         f'opacity="{0.5 * rlabel_fade:.2f}" font-style="italic">'
                         f'<textPath href="#rv{rvi}" startOffset="50%" text-anchor="middle">R. {rvi+1}</textPath></text>')

    # ── Contour lines (warm brown, Swiss style) ──────────────────
    n_levels = max(12, min(25, 10 + followers // 10))
    levels = [i / n_levels for i in range(1, n_levels)]
    for li, level in enumerate(levels):
        is_index = li % 5 == 0
        contour_fade = 1.0 if is_index else _fade(0.03, 0.15)
        if contour_fade <= 0:
            continue
        chains = _extract_contours(elevation, grid, level, cell_w, cell_h)
        # Contour hierarchy: every 5th level (index) gets heavier stroke
        sw = 0.6 if is_index else 0.25
        sc = "#a0522d" if is_index else "#c17d4b"
        op = (0.55 if is_index else 0.20) * contour_fade
        for chain in chains:
            if len(chain) < 2:
                continue
            smooth_chain = _chaikin_smooth(chain, iterations=2 if is_index else 1)
            pd = f"M{smooth_chain[0][0]:.1f},{smooth_chain[0][1]:.1f}"
            for j in range(1, len(smooth_chain) - 1, 2):
                if j + 1 < len(smooth_chain):
                    pd += f" Q{smooth_chain[j][0]:.1f},{smooth_chain[j][1]:.1f} {smooth_chain[j+1][0]:.1f},{smooth_chain[j+1][1]:.1f}"
                else:
                    pd += f" L{smooth_chain[j][0]:.1f},{smooth_chain[j][1]:.1f}"
            contour_when = _date_for_activity_fraction(level)
            P.append(f'<path d="{pd}" fill="none" stroke="{sc}" stroke-width="{sw}" {_timeline_style(contour_when, op)} '
                     f'stroke-linecap="round" stroke-linejoin="round"/>')
            if is_index:
                P.append(f'<path d="{pd}" fill="none" stroke="#7e4d2a" stroke-width="{max(0.3, sw * 0.55):.2f}" '
                         f'{_timeline_style(contour_when, op * 0.35, "tl-reveal tl-crisp")} stroke-linecap="round" stroke-linejoin="round"/>')
        # Elevation labels on index contours showing meters
        clabel_fade = _fade(0.10, 0.30)
        if is_index and chains and clabel_fade > 0:
            longest = _chaikin_smooth(max(chains, key=len), iterations=1)
            mid_i = len(longest) // 2
            mid = longest[mid_i]
            # Compute rotation angle along contour for label
            if mid_i + 1 < len(longest):
                nxt = longest[mid_i + 1]
                label_angle = math.degrees(math.atan2(nxt[1] - mid[1], nxt[0] - mid[0]))
            else:
                label_angle = 0
            elev = f"{int(level*1000)}m"
            P.append(f'<text x="{mid[0]:.0f}" y="{mid[1]+1:.0f}" font-family="monospace" font-size="5" '
                     f'fill="#8b4513" opacity="{0.6 * clabel_fade:.2f}" text-anchor="middle" '
                     f'stroke="rgba(245,240,232,0.8)" stroke-width="2.5" stroke-linejoin="round" paint-order="stroke fill" '
                     f'transform="rotate({label_angle:.0f},{mid[0]:.0f},{mid[1]:.0f})">{elev}</text>')

    # ── Hachures on steep slopes ──────────────────────────────────
    hachure_fade = _fade(0.10, 0.30)
    if hachure_fade > 0:
        for gy in range(2, grid - 2, 3):
            for gx in range(2, grid - 2, 3):
                e = elevation[gy, gx]
                dzdx = abs(elevation[gy, min(gx + 1, grid - 1)] - elevation[gy, max(gx - 1, 0)])
                dzdy = abs(elevation[min(gy + 1, grid - 1), gx] - elevation[max(gy - 1, 0), gx])
                slope = math.sqrt(dzdx ** 2 + dzdy ** 2)
                if slope > 0.035 and 0.55 < e < 0.93:
                    mx, my = _grid_to_map(gx, gy, cell_w, cell_h)
                    aspect = math.atan2(-dzdy, dzdx)
                    hlen = min(5, slope * 35)
                    op_h = min(0.2, slope * 2.5) * hachure_fade
                    P.append(f'<line x1="{mx:.1f}" y1="{my:.1f}" x2="{mx+hlen*math.cos(aspect):.1f}" '
                             f'y2="{my+hlen*math.sin(aspect):.1f}" stroke="#7a5a3a" stroke-width="0.3" opacity="{op_h:.2f}"/>')

    # ── Snow/ice at highest peaks ──────────────────────────────────
    snow_fade = _fade(0.25, 0.50)
    if snow_fade > 0:
        for gy in range(0, grid, 4):
            for gx in range(0, grid, 4):
                e = elevation[min(gy, grid - 1), min(gx, grid - 1)]
                if e > 0.93:
                    mx, my = _grid_to_map(gx, gy, cell_w, cell_h)
                    for _ in range(4):
                        sx = mx + rng.uniform(0, cell_w * 3)
                        sy = my + rng.uniform(0, cell_h * 3)
                        P.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="{rng.uniform(0.3,0.8):.1f}" '
                                 f'fill="#f5f4f2" opacity="0.25"/>')
                        if rng.random() > 0.5:
                            P.append(f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{sx+rng.uniform(-1.5,1.5):.1f}" '
                                     f'y2="{sy+rng.uniform(-1.5,1.5):.1f}" stroke="#d0ccc0" stroke-width="0.2" opacity="0.15"/>')

    # ── Cloud/mist wisps (atmospheric suggestion) ─────────────────
    cloud_fade = _fade(0.10, 0.30)
    if cloud_fade > 0:
        for _ in range(int(cloud_fade * 6)):
            cx_cl = rng.uniform(MAP_L + 30, MAP_R - 30)
            cy_cl = rng.uniform(MAP_T + 10, MAP_T + MAP_H * 0.35)
            cw_cl = rng.uniform(25, 70)
            ch_cl = rng.uniform(3, 8)
            # Wispy curve
            cp1x = cx_cl - cw_cl * 0.4
            cp1y = cy_cl - ch_cl * rng.uniform(0.5, 1.2)
            cp2x = cx_cl + cw_cl * 0.4
            cp2y = cy_cl - ch_cl * rng.uniform(0.3, 0.9)
            P.append(f'<path d="M{cx_cl - cw_cl * 0.5:.1f},{cy_cl:.1f} '
                     f'Q{cp1x:.1f},{cp1y:.1f} {cx_cl:.1f},{cy_cl - ch_cl * 0.6:.1f} '
                     f'Q{cp2x:.1f},{cp2y:.1f} {cx_cl + cw_cl * 0.5:.1f},{cy_cl:.1f}" '
                     f'fill="none" stroke="#c8c4b8" stroke-width="{rng.uniform(0.3, 0.7):.2f}" '
                     f'opacity="{rng.uniform(0.05, 0.10):.2f}" stroke-linecap="round"/>')
            # Secondary parallel wisp
            P.append(f'<path d="M{cx_cl - cw_cl * 0.35:.1f},{cy_cl + 2:.1f} '
                     f'Q{cx_cl:.1f},{cy_cl - ch_cl * 0.3:.1f} {cx_cl + cw_cl * 0.35:.1f},{cy_cl + 1.5:.1f}" '
                     f'fill="none" stroke="#d0ccc0" stroke-width="{rng.uniform(0.2, 0.4):.2f}" '
                     f'opacity="{rng.uniform(0.04, 0.07):.2f}" stroke-linecap="round"/>')

    # ── Spot heights (stars -> peak prominence with summit markers) ─
    # Data mapping: more stars = more prominent peaks shown
    star_prominence = min(2.5, 1.0 + stars / 100.0)
    spots = []
    for gy in range(3, grid - 3, 8):
        for gx in range(3, grid - 3, 8):
            e = elevation[gy, gx]
            if e > 0.5 and all(elevation[gy + dy, gx + dx] <= e for dy in range(-2, 3) for dx in range(-2, 3) if (dy, dx) != (0, 0)):
                spots.append((*_grid_to_map(gx, gy, cell_w, cell_h), e))
    n_spots = max(0, round(mat * 18 * star_prominence))
    spots_sorted = sorted(spots, key=lambda s: s[2], reverse=True)
    for si_spot, (sx, sy, se) in enumerate(spots_sorted[:n_spots]):
        # Top 3 peaks get larger summit markers when stars are high
        if si_spot < 3 and stars > 20:
            # Summit cross marker
            cross_sz = 3.5 + star_prominence
            P.append(f'<line x1="{sx:.0f}" y1="{sy - cross_sz:.0f}" x2="{sx:.0f}" y2="{sy + cross_sz:.0f}" '
                     f'stroke="#5a4a3a" stroke-width="0.8" opacity="0.45"/>')
            P.append(f'<line x1="{sx - cross_sz:.0f}" y1="{sy:.0f}" x2="{sx + cross_sz:.0f}" y2="{sy:.0f}" '
                     f'stroke="#5a4a3a" stroke-width="0.8" opacity="0.45"/>')
            # Bold summit label
            P.append(f'<text x="{sx + 6:.0f}" y="{sy + 2:.0f}" font-family="monospace" font-size="5.5" '
                     f'fill="#3a2a1a" opacity="0.5" font-weight="bold">{int(se * 1000)}</text>')
        else:
            P.append(f'<polygon points="{sx:.0f},{sy-3:.0f} {sx-3:.0f},{sy+3:.0f} {sx+3:.0f},{sy+3:.0f}" '
                     f'fill="none" stroke="#5a4a3a" stroke-width="0.5" opacity="0.4"/>')
            P.append(f'<text x="{sx+5:.0f}" y="{sy+2:.0f}" font-family="monospace" font-size="5" fill="#5a4a3a" opacity="0.4">{int(se*1000)}</text>')

    # ── Survey benchmarks at secondary peaks ──────────────────────
    bm_fade = _fade(0.25, 0.50)
    if bm_fade > 0:
        bm_max = max(1, round(bm_fade * 3))
        bm_count = 0
        for sx, sy, se in spots[:8]:
            if se > 0.6 and bm_count < bm_max:
                # BM symbol: circle with horizontal line through it
                P.append(f'<circle cx="{sx:.0f}" cy="{sy:.0f}" r="2.5" fill="none" '
                         f'stroke="#5a4a3a" stroke-width="0.5" opacity="0.3"/>')
                P.append(f'<line x1="{sx - 3:.0f}" y1="{sy:.0f}" x2="{sx + 3:.0f}" y2="{sy:.0f}" '
                         f'stroke="#5a4a3a" stroke-width="0.4" opacity="0.3"/>')
                P.append(f'<text x="{sx + 6:.0f}" y="{sy + 1:.0f}" font-family="monospace" font-size="4" '
                         f'fill="#5a4a3a" opacity="0.3">BM {int(se * 1000)}</text>')
                bm_count += 1

    # ── Spring labels at river sources ──────────────────────────────
    spring_fade = _fade(0.20, 0.45)
    if spring_fade > 0:
        for rvi, rpts in enumerate(river_paths):
            if len(rpts) > 3:
                sx_r, sy_r = MAP_L + rpts[0][0] * MAP_W, MAP_T + rpts[0][1] * MAP_H
                P.append(f'<circle cx="{sx_r:.0f}" cy="{sy_r:.0f}" r="2" fill="#a8d4f0" opacity="0.3" '
                         f'stroke="#5b92c7" stroke-width="0.3"/>')
                P.append(f'<text x="{sx_r + 4:.0f}" y="{sy_r + 1:.0f}" font-family="Georgia,serif" '
                         f'font-size="4" fill="#1a4f8a" opacity="0.3" font-style="italic">Spr.</text>')

    # ── Progressive repo visibility for animation ─────────────────
    n_visible_repos = max(1, round(len(repo_positions) * min(1.0, mat * 2.2)))

    # ── Chronological trail (oldest → newest → center) ────────────
    visible_rp = repo_positions[:n_visible_repos]
    chrono = sorted(visible_rp, key=lambda rp: rp[2].get("age_months", 0), reverse=True)
    waypoints = [(rcx, rcy) for rcx, rcy, _ in chrono]
    waypoints.append((0.5, 0.5))  # end at profile center

    if len(waypoints) >= 2:
        # Trail casing (white outline beneath for contrast)
        trail_d = f"M{MAP_L + waypoints[0][0] * MAP_W:.1f},{MAP_T + waypoints[0][1] * MAP_H:.1f}"
        for wi in range(len(waypoints) - 1):
            x1m = MAP_L + waypoints[wi][0] * MAP_W
            y1m = MAP_T + waypoints[wi][1] * MAP_H
            x2m = MAP_L + waypoints[wi + 1][0] * MAP_W
            y2m = MAP_T + waypoints[wi + 1][1] * MAP_H
            cx = (x1m + x2m) / 2 + rng.uniform(-15, 15)
            cy = (y1m + y2m) / 2 + rng.uniform(-15, 15)
            trail_d += f" Q{cx:.1f},{cy:.1f} {x2m:.1f},{y2m:.1f}"
        # White casing
        P.append(f'<path d="{trail_d}" fill="none" stroke="rgba(255,255,255,0.35)" stroke-width="2.5" '
                 f'{_timeline_style(_date_for_activity_fraction(0.2), 0.35)} stroke-linecap="round"/>')
        # Brown dashed trail on top
        P.append(f'<path d="{trail_d}" fill="none" stroke="#8a6840" stroke-width="0.8" '
                 f'{_timeline_style(_date_for_activity_fraction(0.25), 0.35)} stroke-dasharray="5 2.5" stroke-linecap="round"/>')

        # Diamond milestone markers with age labels
        for wi, (wx, wy, wrepo) in enumerate(chrono):
            mx_w = MAP_L + wx * MAP_W
            my_w = MAP_T + wy * MAP_H
            age_m = wrepo.get("age_months", 0)
            age_label = f"{age_m // 12}y" if age_m >= 12 else f"{age_m}mo"
            dy_off = 14
            ds = 2.5  # diamond half-size
            milestone_when = _repo_date(wrepo) or _date_for_activity_fraction(min(1.0, wi / max(1, len(chrono))))
            P.append(f'<polygon points="{mx_w:.0f},{my_w+dy_off-ds:.0f} {mx_w+ds:.0f},{my_w+dy_off:.0f} '
                     f'{mx_w:.0f},{my_w+dy_off+ds:.0f} {mx_w-ds:.0f},{my_w+dy_off:.0f}" '
                     f'fill="#8a6840" {_timeline_style(milestone_when, 0.35)} stroke="#5a4020" stroke-width="0.3"/>')
            P.append(f'<text x="{mx_w + 5:.0f}" y="{my_w + dy_off + 1:.0f}" font-family="Georgia,serif" '
                     f'font-size="4.5" fill="#5c3a1e" {_timeline_style(milestone_when, 0.4)} font-style="italic" '
                     f'stroke="rgba(245,240,232,0.6)" stroke-width="1.5" stroke-linejoin="round" paint-order="stroke fill"'
                     f'>{age_label}</text>')

    # ── Repo landmarks ────────────────────────────────────────────
    for idx_rp, (rcx, rcy, repo) in enumerate(repo_positions):
        if idx_rp >= n_visible_repos:
            continue
        lx = MAP_L + rcx * MAP_W
        ly = MAP_T + rcy * MAP_H
        repo_stars = repo.get("stars", 0)
        name = repo.get("name", "")
        hue = LANG_HUES.get(repo.get("language"), 160)
        mc = oklch(0.45, 0.18, hue)
        # Relative marker size: top-star repo gets biggest marker
        star_frac = (repo_stars - min_stars) / max(1, max_stars - min_stars) if max_stars > min_stars else 0.5
        repo_when = _repo_date(repo) or _date_for_activity_fraction(star_frac)
        if star_frac > 0.7:
            bs = 4 + int(star_frac * 4)
            P.append(f'<rect x="{lx-bs:.0f}" y="{ly-bs:.0f}" width="{bs*2:.0f}" height="{bs*2:.0f}" '
                     f'fill="{mc}" {_timeline_style(repo_when, 0.5)} stroke="#3a2a1a" stroke-width="0.4"/>')
        else:
            mr = 2.5 + star_frac * 5
            P.append(f'<circle cx="{lx:.0f}" cy="{ly:.0f}" r="{mr:.1f}" fill="{mc}" {_timeline_style(repo_when, 0.65)} stroke="#fff" stroke-width="0.5"/>')
        P.append(f'<text x="{lx+8:.0f}" y="{ly+3:.0f}" font-family="Georgia,serif" font-size="6.5" '
                 f'fill="#2c1a0e" {_timeline_style(repo_when, 0.65)} font-weight="bold" '
                 f'stroke="rgba(245,240,232,0.75)" stroke-width="2.5" stroke-linejoin="round" paint-order="stroke fill">{name}</text>')
        if repo_stars > 0:
            P.append(f'<text x="{lx+8:.0f}" y="{ly+10:.0f}" font-family="Georgia,serif" font-size="5" '
                     f'fill="#5c3a1e" {_timeline_style(repo_when, 0.45)} font-variant="small-caps" '
                     f'stroke="rgba(245,240,232,0.6)" stroke-width="2" stroke-linejoin="round" paint-order="stroke fill"'
                     f'>{repo_stars} stars</text>')

    # ── Watershed ridge lines (dashed, connecting peaks) ──────────
    ridge_fade = _fade(0.30, 0.55)
    if ridge_fade > 0 and len(sorted_repos) >= 2:
        for pi_w in range(min(3, len(sorted_repos) - 1)):
            r1 = sorted_repos[pi_w]
            r2 = sorted_repos[pi_w + 1]
            x1_w = MAP_L + r1[0] * MAP_W
            y1_w = MAP_T + r1[1] * MAP_H
            x2_w = MAP_L + r2[0] * MAP_W
            y2_w = MAP_T + r2[1] * MAP_H
            # Sinuous ridge line
            cx_w = (x1_w + x2_w) / 2 + rng.uniform(-10, 10)
            cy_w = (y1_w + y2_w) / 2 + rng.uniform(-10, 10)
            P.append(f'<path d="M{x1_w:.1f},{y1_w:.1f} Q{cx_w:.1f},{cy_w:.1f} {x2_w:.1f},{y2_w:.1f}" '
                     f'fill="none" stroke="#c09060" stroke-width="0.4" opacity="0.12" '
                     f'stroke-dasharray="3 2 1 2" stroke-linecap="round"/>')

    # Center marker
    cx_m, cy_m = MAP_L + MAP_W / 2, MAP_T + MAP_H / 2
    P.append(f'<circle cx="{cx_m:.0f}" cy="{cy_m:.0f}" r="6" fill="none" stroke="#cc3828" stroke-width="1.5" opacity="0.5"/>')
    P.append(f'<circle cx="{cx_m:.0f}" cy="{cy_m:.0f}" r="2.5" fill="#cc3828" opacity="0.65"/>')
    P.append(f'<text x="{cx_m+10:.0f}" y="{cy_m+3:.0f}" font-family="Georgia,serif" font-size="9" '
             f'fill="#1a1a1a" font-weight="bold" opacity="0.65" letter-spacing="0.5" '
             f'stroke="rgba(245,240,232,0.8)" stroke-width="3" stroke-linejoin="round" paint-order="stroke fill"'
             f'>{metrics.get("label","")}</text>')

    # ── Month markers ─────────────────────────────────────────────
    month_fade = _fade(0.05, 0.20)
    if month_fade > 0:
        month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        for mi, mkey in enumerate(months_sorted):
            angle = -math.pi / 2 + mi * 2 * math.pi / max(1, len(months_sorted))
            lx = max(MAP_L - 20, min(MAP_R + 20, MAP_L + MAP_W / 2 + (MAP_W / 2 + 10) * math.cos(angle)))
            ly = max(MAP_T - 20, min(MAP_B + 20, MAP_T + MAP_H / 2 + (MAP_H / 2 + 10) * math.sin(angle)))
            mn = int(mkey) - 1 if mkey.isdigit() else mi
            m_op = (0.25 + monthly[mkey] / max(1, max_m) * 0.45) * month_fade
            month_when = _month_key_date(mkey, mi)
            P.append(f'<text x="{lx:.0f}" y="{ly:.0f}" text-anchor="middle" dominant-baseline="central" '
                    f'font-family="Georgia,serif" font-size="7" fill="#5a4a3a" '
                    f'{_timeline_style(month_when, m_op)}>{month_labels[mn%12]}</text>')

    # ── Compass rose — complexity controlled by chrome_mat ──────────
    ccx, ccy, cr = MAP_R - 45, MAP_T + 45, 24
    if chrome_mat < 0.2:
        P.append(f'<polygon points="{ccx},{ccy - cr + 4} {ccx - 5},{ccy} {ccx + 5},{ccy}" '
                 f'fill="#2c2c2c" opacity="0.35"/>')
        P.append(f'<text x="{ccx}" y="{ccy - cr - 2}" text-anchor="middle" '
                 f'font-family="Georgia,serif" font-size="8" fill="#2c1a0e" opacity="0.5" font-weight="bold">N</text>')
    else:
        card_len = cr - 4
        card_w = 5
        for label, dx, dy in [("N", 0, -1), ("E", 1, 0), ("S", 0, 1), ("W", -1, 0)]:
            px, py = -dy, dx
            tip_x = ccx + dx * card_len
            tip_y = ccy + dy * card_len
            P.append(f'<polygon points="{ccx},{ccy} {ccx+px*card_w},{ccy+py*card_w} {tip_x},{tip_y}" '
                     f'fill="#2c2c2c" opacity="0.35" stroke="#1a1a1a" stroke-width="0.2"/>')
            P.append(f'<polygon points="{ccx},{ccy} {ccx-px*card_w},{ccy-py*card_w} {tip_x},{tip_y}" '
                     f'fill="#f0eeea" opacity="0.5" stroke="#2c2c2c" stroke-width="0.3"/>')
            lbl_d = cr + 7
            fsz = "8" if label == "N" else "6.5"
            fw = "bold" if label == "N" else "normal"
            P.append(f'<text x="{ccx+dx*lbl_d:.0f}" y="{ccy+dy*lbl_d:.0f}" text-anchor="middle" '
                     f'dominant-baseline="central" font-family="Georgia,serif" font-size="{fsz}" fill="#2c1a0e" opacity="0.5" '
                     f'font-weight="{fw}" stroke="rgba(245,240,232,0.7)" stroke-width="2" stroke-linejoin="round" paint-order="stroke fill"'
                     f'>{label}</text>')
        if chrome_mat >= 0.5:
            P.append(f'<circle cx="{ccx}" cy="{ccy}" r="{cr+2}" fill="none" stroke="#2c2c2c" stroke-width="0.8" opacity="0.35"/>')
            ic_len = card_len * 0.5
            ic_w = 3
            for dx, dy in [(1, -1), (1, 1), (-1, 1), (-1, -1)]:
                d = math.sqrt(2)
                ndx, ndy = dx / d, dy / d
                px, py = -ndy, ndx
                tip_x = ccx + ndx * ic_len
                tip_y = ccy + ndy * ic_len
                P.append(f'<polygon points="{ccx},{ccy} {ccx+px*ic_w},{ccy+py*ic_w} {tip_x},{tip_y}" '
                         f'fill="#2c2c2c" opacity="0.2"/>')
                P.append(f'<polygon points="{ccx},{ccy} {ccx-px*ic_w},{ccy-py*ic_w} {tip_x},{tip_y}" '
                         f'fill="#f0eeea" opacity="0.3" stroke="#2c2c2c" stroke-width="0.2"/>')
        if chrome_mat > 0.75:
            # Decorative double-ring border for 16-point compass
            P.append(f'<circle cx="{ccx}" cy="{ccy}" r="{cr + 4}" fill="none" stroke="#2c2c2c" stroke-width="0.3" opacity="0.2"/>')
            P.append(f'<circle cx="{ccx}" cy="{ccy}" r="{cr - 1}" fill="none" stroke="#2c2c2c" stroke-width="0.4" opacity="0.25"/>')
            # 16-point tick marks (every 22.5 degrees)
            sixteen_labels = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                              "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
            for ti, deg in enumerate(range(0, 360, 22)):
                # Approximate: 0, 22.5, 45, 67.5, ... (use 22 to step through 16)
                actual_deg = ti * 22.5
                rad = math.radians(actual_deg)
                is_cardinal = ti % 4 == 0
                is_intercardinal = ti % 2 == 0 and not is_cardinal
                if is_cardinal:
                    r_in, r_out, sw_t = cr - 2, cr + 3, 0.6
                elif is_intercardinal:
                    r_in, r_out, sw_t = cr - 1, cr + 2, 0.4
                else:
                    r_in, r_out, sw_t = cr, cr + 1.5, 0.25
                P.append(f'<line x1="{ccx + r_in * math.sin(rad):.1f}" y1="{ccy - r_in * math.cos(rad):.1f}" '
                         f'x2="{ccx + r_out * math.sin(rad):.1f}" y2="{ccy - r_out * math.cos(rad):.1f}" '
                         f'stroke="#2c2c2c" stroke-width="{sw_t}" opacity="0.3"/>')
                # Secondary direction labels (NE, SE, etc.) in smaller text
                if is_intercardinal and ti < 16:
                    lbl_r = cr + 6
                    lbl = sixteen_labels[ti]
                    P.append(f'<text x="{ccx + lbl_r * math.sin(rad):.0f}" y="{ccy - lbl_r * math.cos(rad):.0f}" '
                             f'text-anchor="middle" dominant-baseline="central" font-family="Georgia,serif" '
                             f'font-size="3.5" fill="#5a4a3a" opacity="0.3">{lbl}</text>')
            decl = 3 + int(hex_frac(h, 48, 50) * 12)
            P.append(f'<text x="{ccx:.0f}" y="{ccy + cr + 14:.0f}" text-anchor="middle" '
                     f'font-family="Georgia,serif" font-size="3.5" fill="#5a4a3a" opacity="0.3" '
                     f'font-style="italic">MN {decl}\u00b0E</text>')
        P.append(f'<circle cx="{ccx}" cy="{ccy}" r="3.5" fill="#f0eeea" stroke="#2c2c2c" stroke-width="0.6" opacity="0.45"/>')
        P.append(f'<circle cx="{ccx}" cy="{ccy}" r="1.5" fill="#2c2c2c" opacity="0.4"/>')

    # ── Neatline & Frame — complexity controlled by chrome_mat ──────
    if chrome_mat < 0.2:
        P.append(f'<rect x="{MAP_L-1}" y="{MAP_T-1}" width="{MAP_W+2}" height="{MAP_H+2}" '
                 f'fill="none" stroke="#1a1a1a" stroke-width="0.5" opacity="0.35"/>')
    else:
        P.append(f'<rect x="{MAP_L-8}" y="{MAP_T-8}" width="{MAP_W+16}" height="{MAP_H+16}" '
                 f'fill="none" stroke="#1a1a1a" stroke-width="2" rx="1" opacity="0.4"/>')
        P.append(f'<rect x="{MAP_L-1}" y="{MAP_T-1}" width="{MAP_W+2}" height="{MAP_H+2}" '
                 f'fill="none" stroke="#1a1a1a" stroke-width="0.5" opacity="0.35"/>')
        if chrome_mat >= 0.45:
            # + Alternating B&W border segments + grid lines
            n_ticks = 20
            bw = 6  # border width between neatlines
            for i in range(n_ticks):
                frac = i / n_ticks
                frac_next = (i + 1) / n_ticks
                fill_t = "#1a1a1a" if i % 2 == 0 else "#f5f0e8"
                op_t = 0.3 if i % 2 == 0 else 0.5
                # Top edge
                P.append(f'<rect x="{MAP_L + frac * MAP_W:.1f}" y="{MAP_T - 7:.0f}" '
                         f'width="{(frac_next - frac) * MAP_W:.1f}" height="{bw}" fill="{fill_t}" opacity="{op_t}"/>')
                # Bottom edge
                P.append(f'<rect x="{MAP_L + frac * MAP_W:.1f}" y="{MAP_B + 1:.0f}" '
                         f'width="{(frac_next - frac) * MAP_W:.1f}" height="{bw}" fill="{fill_t}" opacity="{op_t}"/>')
                # Left edge
                P.append(f'<rect x="{MAP_L - 7:.0f}" y="{MAP_T + frac * MAP_H:.1f}" '
                         f'width="{bw}" height="{(frac_next - frac) * MAP_H:.1f}" fill="{fill_t}" opacity="{op_t}"/>')
                # Right edge
                P.append(f'<rect x="{MAP_R + 1:.0f}" y="{MAP_T + frac * MAP_H:.1f}" '
                         f'width="{bw}" height="{(frac_next - frac) * MAP_H:.1f}" fill="{fill_t}" opacity="{op_t}"/>')
            # Interior grid lines
            for i in range(1, 10):
                gx_l = MAP_L + i * MAP_W / 10
                gy_l = MAP_T + i * MAP_H / 10
                P.append(f'<line x1="{gx_l:.0f}" y1="{MAP_T}" x2="{gx_l:.0f}" y2="{MAP_B}" stroke="#a09878" stroke-width="0.15" opacity="0.08"/>')
                P.append(f'<line x1="{MAP_L}" y1="{gy_l:.0f}" x2="{MAP_R}" y2="{gy_l:.0f}" stroke="#a09878" stroke-width="0.15" opacity="0.08"/>')
        if chrome_mat > 0.7:
            # + Coordinate tick labels
            base_lon = 120 + int(h[40:42], 16) % 30
            base_lat = 35 + int(h[42:44], 16) % 20
            for i in range(0, 11, 2):
                frac = i / 10
                # Bottom edge longitude labels
                tx = MAP_L + frac * MAP_W
                lon_min = int(hex_frac(h, (i * 2) % 56, (i * 2 + 2) % 56 + 2) * 59)
                P.append(f'<text x="{tx:.0f}" y="{MAP_B + 16:.0f}" text-anchor="middle" '
                         f'font-family="monospace" font-size="4" fill="#5a4a3a" opacity="0.3">'
                         f'{base_lon + i}\u00b0{lon_min:02d}\u2032E</text>')
                # Left edge latitude labels
                ty = MAP_T + frac * MAP_H
                lat_min = int(hex_frac(h, (i * 2 + 10) % 56, (i * 2 + 12) % 56 + 2) * 59)
                P.append(f'<text x="{MAP_L - 11:.0f}" y="{ty + 1:.0f}" text-anchor="end" '
                         f'font-family="monospace" font-size="4" fill="#5a4a3a" opacity="0.3">'
                         f'{base_lat + 10 - i}\u00b0{lat_min:02d}\u2032N</text>')

    # ── Scale bar — chrome_mat controlled ──────────────────────────
    if chrome_mat > 0.2:
        sb_x, sb_y, sb_w = MAP_L + 10, MAP_B + 25, 100
        P.append(f'<line x1="{sb_x}" y1="{sb_y}" x2="{sb_x+sb_w}" y2="{sb_y}" stroke="#5a4a3a" stroke-width="1.2"/>')
        for tx_sb in [sb_x, sb_x + sb_w, sb_x + sb_w // 2]:
            P.append(f'<line x1="{tx_sb}" y1="{sb_y-3}" x2="{tx_sb}" y2="{sb_y+3}" stroke="#5a4a3a" stroke-width="0.5"/>')
        if chrome_mat > 0.4:
            P.append(f'<rect x="{sb_x}" y="{sb_y-1.5}" width="{sb_w//4}" height="3" fill="#5a4a3a" opacity="0.5"/>')
            P.append(f'<rect x="{sb_x+sb_w//2}" y="{sb_y-1.5}" width="{sb_w//4}" height="3" fill="#5a4a3a" opacity="0.5"/>')
        P.append(f'<text x="{sb_x+sb_w//2}" y="{sb_y-6}" text-anchor="middle" font-family="Georgia,serif" font-size="6" fill="#5a4a3a" opacity="0.5">{contributions} contributions</text>')

    # ── Profile cross-section — chrome_mat controlled ──────────────
    if chrome_mat > 0.3:
        # Reference line on map (A—A')
        prof_ref_y = MAP_T + MAP_H / 2
        if chrome_mat > 0.6:
            P.append(f'<line x1="{MAP_L}" y1="{prof_ref_y:.0f}" x2="{MAP_R}" y2="{prof_ref_y:.0f}" '
                     f'stroke="#7a5a3a" stroke-width="0.5" opacity="0.15" stroke-dasharray="6 3"/>')
            P.append(f'<text x="{MAP_L - 3:.0f}" y="{prof_ref_y + 2:.0f}" text-anchor="end" '
                     f'font-family="Georgia,serif" font-size="6" fill="#7a5a3a" opacity="0.35" font-weight="bold">A</text>')
            P.append(f'<text x="{MAP_R + 3:.0f}" y="{prof_ref_y + 2:.0f}" text-anchor="start" '
                     f'font-family="Georgia,serif" font-size="6" fill="#7a5a3a" opacity="0.35" font-weight="bold">A\u2032</text>')

        # Elevation profile
        prof_x, prof_y, prof_w, prof_h = MAP_L + 150, MAP_B + 20, MAP_W - 160, 30
        P.append(f'<rect x="{prof_x}" y="{prof_y}" width="{prof_w}" height="{prof_h}" fill="#f5f0e8" stroke="#7a6a4a" stroke-width="0.4" opacity="0.4" rx="1"/>')
        P.append(f'<text x="{prof_x}" y="{prof_y-3}" font-family="Georgia,serif" font-size="5.5" fill="#5c3a1e" opacity="0.45" '
                 f'font-variant="small-caps" letter-spacing="0.5">Cross-section A\u2013A\u2032</text>')
        mid_row = grid // 2
        prof_pts = []
        for pi in range(0, grid, 2):
            px_p = prof_x + (pi / grid) * prof_w
            py_p = prof_y + prof_h - elevation[mid_row, pi] * prof_h * 0.85
            prof_pts.append(f"{px_p:.1f},{py_p:.1f}")
        P.append(f'<path d="M{prof_x},{prof_y+prof_h} L{" L".join(prof_pts)} L{prof_x+prof_w},{prof_y+prof_h} Z" '
                 f'fill="#94bf8b" opacity="0.2"/>')
        P.append(f'<polyline points="{" ".join(prof_pts)}" fill="none" stroke="#7a5a3a" stroke-width="0.6" opacity="0.45"/>')
        P.append(f'<line x1="{prof_x}" y1="{prof_y+prof_h}" x2="{prof_x+prof_w}" y2="{prof_y+prof_h}" '
                 f'stroke="#7a6a4a" stroke-width="0.3" opacity="0.3"/>')
        if chrome_mat > 0.5:
            for et in range(0, 4):
                et_y = prof_y + prof_h - (et / 3) * prof_h * 0.85
                P.append(f'<line x1="{prof_x - 2}" y1="{et_y:.1f}" x2="{prof_x}" y2="{et_y:.1f}" '
                         f'stroke="#7a6a4a" stroke-width="0.25" opacity="0.3"/>')
                P.append(f'<text x="{prof_x - 3}" y="{et_y + 1.5:.1f}" text-anchor="end" '
                         f'font-family="monospace" font-size="3" fill="#7a6a4a" opacity="0.3">{int(et * 330)}</text>')
            P.append(f'<text x="{prof_x}" y="{prof_y + prof_h + 7}" font-family="Georgia,serif" '
                     f'font-size="4.5" fill="#7a5a3a" opacity="0.35" font-weight="bold">A</text>')
            P.append(f'<text x="{prof_x + prof_w}" y="{prof_y + prof_h + 7}" text-anchor="end" '
                     f'font-family="Georgia,serif" font-size="4.5" fill="#7a5a3a" opacity="0.35" font-weight="bold">A\u2032</text>')

    # ── Legend (entry count scales with chrome_mat) ────────────────
    leg_x, leg_y = MAP_R - 125, MAP_B + 15
    n_legend_entries = 1 + int(chrome_mat * 4)
    entries = [
        ("circle", "#cc3828", "Profile center"),
        ("line", "#5b92c7", "River / lake"),
        ("dash", "#8a6840", "Timeline trail"),
        ("contour", "#a0522d", "Contour (index)"),
        ("bm", "#5a4a3a", "Benchmark"),
    ][:n_legend_entries]
    leg_w, leg_h = 115, 14 + len(entries) * 5.5 + (22 if chrome_mat > 0.5 else 0)
    P.append(f'<rect x="{leg_x}" y="{leg_y}" width="{leg_w}" height="{leg_h}" '
             f'fill="#f5f0e8" stroke="#5a4a3a" stroke-width="0.5" rx="1.5" opacity="0.92"/>')
    P.append(f'<rect x="{leg_x+2}" y="{leg_y+2}" width="{leg_w-4}" height="{leg_h-4}" '
             f'fill="none" stroke="#a09070" stroke-width="0.3" rx="0.5" opacity="0.4"/>')
    P.append(f'<text x="{leg_x+leg_w/2:.0f}" y="{leg_y+10}" text-anchor="middle" '
             f'font-family="Georgia,serif" font-size="6" fill="#2c1a0e" font-weight="bold" opacity="0.5" '
             f'letter-spacing="1.5" font-variant="small-caps">Legend</text>')
    if chrome_mat > 0.5:
        ramp_x, ramp_y, ramp_w = leg_x + 6, leg_y + 14, 60
        ramp_colors = ["#a8d4f0", "#94bf8b", "#bdcc96", "#e8e1b6", "#d4b896", "#c9a87c", "#e4e0d0", "#f5f4f2"]
        seg_w = ramp_w / len(ramp_colors)
        for ci, rc in enumerate(ramp_colors):
            P.append(f'<rect x="{ramp_x + ci * seg_w:.1f}" y="{ramp_y}" width="{seg_w + 0.5:.1f}" height="5" fill="{rc}" opacity="0.7"/>')
        P.append(f'<rect x="{ramp_x}" y="{ramp_y}" width="{ramp_w}" height="5" fill="none" stroke="#5a4a3a" stroke-width="0.3" opacity="0.4"/>')
        P.append(f'<text x="{ramp_x}" y="{ramp_y+10}" font-family="monospace" font-size="3.5" fill="#5a4a3a" opacity="0.4">Low</text>')
        P.append(f'<text x="{ramp_x+ramp_w}" y="{ramp_y+10}" text-anchor="end" font-family="monospace" font-size="3.5" fill="#5a4a3a" opacity="0.4">High</text>')
    entry_offset = (14 + 16) if chrome_mat > 0.5 else 14
    for li_l, (shape, color, text) in enumerate(entries):
        iy = leg_y + entry_offset + li_l * 5.5
        ix = leg_x + 8
        if shape == "circle":
            P.append(f'<circle cx="{ix}" cy="{iy}" r="1.8" fill="{color}" opacity="0.55"/>')
        elif shape == "line":
            P.append(f'<line x1="{ix-4}" y1="{iy}" x2="{ix+4}" y2="{iy}" stroke="{color}" stroke-width="1.2" opacity="0.5" stroke-linecap="round"/>')
        elif shape == "dash":
            P.append(f'<line x1="{ix-4}" y1="{iy}" x2="{ix+4}" y2="{iy}" stroke="{color}" stroke-width="0.7" opacity="0.4" stroke-dasharray="2 1" stroke-linecap="round"/>')
        elif shape == "contour":
            P.append(f'<line x1="{ix-4}" y1="{iy}" x2="{ix+4}" y2="{iy}" stroke="{color}" stroke-width="0.8" opacity="0.5" stroke-linecap="round"/>')
        elif shape == "bm":
            P.append(f'<circle cx="{ix}" cy="{iy}" r="1.5" fill="none" stroke="{color}" stroke-width="0.4" opacity="0.4"/>')
            P.append(f'<line x1="{ix-2}" y1="{iy}" x2="{ix+2}" y2="{iy}" stroke="{color}" stroke-width="0.3" opacity="0.4"/>')
        P.append(f'<text x="{ix+7}" y="{iy+1.5}" font-family="Georgia,serif" font-size="4.5" fill="#3a2a1a" opacity="0.45">{text}</text>')

    # ── Tiered title cartouche ────────────────────────────────────
    cart_x, cart_y = MAP_L - 5, HEIGHT - 52
    cart_w = 260
    if chrome_mat < 0.2:
        # Simple text-only
        P.append(f'<text x="{cart_x + 130}" y="{cart_y + 20}" text-anchor="middle" '
                 f'font-family="Georgia,serif" font-size="10" fill="#1a1a1a" font-weight="bold" opacity="0.5" '
                 f'letter-spacing="1">Topographic Survey</text>')
        P.append(f'<text x="{cart_x + 130}" y="{cart_y + 32}" text-anchor="middle" '
                 f'font-family="Georgia,serif" font-size="7" fill="#3a2a1a" opacity="0.4" '
                 f'font-style="italic">{metrics.get("label","")}</text>')
    else:
        cart_h = 44
        P.append(f'<rect x="{cart_x}" y="{cart_y}" width="{cart_w}" height="{cart_h}" '
                 f'fill="#f5f0e8" stroke="#2c2c2c" stroke-width="1" opacity="0.9" rx="1"/>')
        if chrome_mat > 0.3:
            P.append(f'<rect x="{cart_x+3}" y="{cart_y+3}" width="{cart_w-6}" height="{cart_h-6}" '
                     f'fill="none" stroke="#2c2c2c" stroke-width="0.3" opacity="0.3" rx="0.5"/>')
        P.append(f'<text x="{cart_x + cart_w/2:.0f}" y="{cart_y + 16}" text-anchor="middle" '
                 f'font-family="Georgia,serif" font-size="11" fill="#1a1a1a" font-weight="bold" opacity="0.6" '
                 f'letter-spacing="1">Topographic Survey</text>')
        P.append(f'<text x="{cart_x + cart_w/2:.0f}" y="{cart_y + 27}" text-anchor="middle" '
                 f'font-family="Georgia,serif" font-size="8" fill="#3a2a1a" opacity="0.5" '
                 f'font-style="italic">{metrics.get("label","")}</text>')
        if chrome_mat > 0.4:
            P.append(f'<line x1="{cart_x+10}" y1="{cart_y+31}" x2="{cart_x+cart_w-10}" y2="{cart_y+31}" '
                     f'stroke="#2c2c2c" stroke-width="0.4" opacity="0.2"/>')
            P.append(f'<text x="{cart_x + cart_w/2:.0f}" y="{cart_y + 39}" text-anchor="middle" '
                     f'font-family="Georgia,serif" font-size="5.5" fill="#5a4a3a" opacity="0.4" letter-spacing="0.3">'
                     f'{len(repos)} repositories  \u00b7  {contributions} contributions  \u00b7  {stars} stars</text>')

    # ── Survey datum note (only chrome_mat > 0.6) ─────────────────
    if chrome_mat > 0.6:
        P.append(f'<text x="{MAP_R}" y="{HEIGHT - 8}" text-anchor="end" '
                 f'font-family="Georgia,serif" font-size="3.5" fill="#8a7a6a" opacity="0.25" '
                 f'font-style="italic">Datum: WGS 84  \u00b7  Contour interval: variable  \u00b7  '
                 f'Projection: Mercator</text>')

    # ── Cloud shadows (large faint elliptical overlays) ──────────
    cloud_shadow_noise = Noise2D(seed=int(h[8:16], 16) ^ 0xBEEF)
    for cs_i in range(3):
        # Deterministic placement from seed hash
        cs_frac_x = hex_frac(h, (cs_i * 6) % 56, (cs_i * 6 + 4) % 56 + 2)
        cs_frac_y = hex_frac(h, (cs_i * 6 + 2) % 56, (cs_i * 6 + 6) % 56 + 2)
        cs_cx = MAP_L + cs_frac_x * MAP_W
        cs_cy = MAP_T + cs_frac_y * MAP_H
        # Large organic ellipse — use noise for slight shape distortion
        cs_rx = 40 + cloud_shadow_noise.noise(cs_i * 3.7, 0.5) * 25 + 30
        cs_ry = 25 + cloud_shadow_noise.noise(0.5, cs_i * 3.7) * 15 + 20
        cs_angle = cloud_shadow_noise.noise(cs_i * 2.1, cs_i * 1.3) * 30
        cs_opacity = 0.03 + (cs_i % 2) * 0.02  # 0.03, 0.05, 0.03
        P.append(f'<ellipse cx="{cs_cx:.1f}" cy="{cs_cy:.1f}" rx="{cs_rx:.1f}" ry="{cs_ry:.1f}" '
                 f'fill="#1a2a3a" opacity="{cs_opacity:.3f}" '
                 f'transform="rotate({cs_angle:.1f},{cs_cx:.1f},{cs_cy:.1f})"/>')

    # ── Foxing / age spots (scaled by mat) ────────────────────────
    for _ in range(int(mat * 8)):
        fx_a = rng.uniform(10, WIDTH - 10)
        fy_a = rng.uniform(10, HEIGHT - 10)
        fr_a = rng.uniform(1.5, 5)
        P.append(f'<circle cx="{fx_a:.0f}" cy="{fy_a:.0f}" r="{fr_a:.1f}" '
                 f'fill="#d0c0a0" opacity="{rng.uniform(0.03, 0.07):.3f}"/>')

    P.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#vigTopo)"/>')

    P.append('</svg>')
    return '\n'.join(P)
