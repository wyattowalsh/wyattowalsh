"""
Ink Garden Ultimate — Full botanical illustration generative art.

Root systems underground, bark texture, multi-layer blooms with stamens,
butterflies/bees/dragonflies, spider webs, mushrooms, falling seeds,
dew drops, botanical annotations, ornate border with corner flourishes.

Plant species diversity system: repos are classified into species (oak,
birch, conifer, fern, bamboo, seedling, shrub, wildflower) each with
unique growth algorithms, leaf shapes, and bloom types.

Light theme on aged paper.
"""
from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timedelta

import numpy as np

from .optimize import optimize_layout_sa, optimize_palette_hues
from .shared import (
    CX,
    CY,
    HEIGHT,
    LANG_HUES,
    WIDTH,
    Noise2D,
    compute_maturity,
    contributions_monthly_to_daily_series,
    make_linear_gradient,
    make_radial_gradient,
    map_date_to_loop_delay,
    normalize_timeline_window,
    oklch,
    seed_hash,
)

# Hard caps to prevent file-size blowout
MAX_SEGS = 4000
MAX_ROOTS = 800
MAX_REPOS = 10
MAX_LEAVES = 600
MAX_BLOOMS = 80
MAX_ELEMENTS = 25000  # total SVG elements budget

# ── Species style parameters ──────────────────────────────────────────
SPECIES = {
    "oak": {
        "branch_prob": 0.45,
        "fork_range": (2, 5),
        "length_decay": (0.4, 0.7),
        "width_decay": 0.5,
        "noise_strength": 0.25,
        "leaf_prob": 0.4,
        "leaf_shape": "oak_lobed",
        "bloom_type": "acorn",
        "min_trunk_ratio": 0.3,
        "base_angle_spread": 0.5,
    },
    "birch": {
        "branch_prob": 0.2,
        "fork_range": (1, 3),
        "length_decay": (0.5, 0.8),
        "width_decay": 0.45,
        "noise_strength": 0.15,
        "leaf_prob": 0.6,
        "leaf_shape": "small_round",
        "bloom_type": "catkin",
        "min_trunk_ratio": 0.5,
        "base_angle_spread": 0.2,
    },
    "conifer": {
        "branch_prob": 0.5,
        "fork_range": (1, 3),
        "length_decay": (0.5, 0.7),
        "width_decay": 0.5,
        "noise_strength": 0.2,
        "leaf_prob": 0.7,
        "leaf_shape": "needle_cluster",
        "bloom_type": "pine_cone",
        "min_trunk_ratio": 0.4,
        "base_angle_spread": 0.15,
        "branch_angle_range": (1.0, 1.5),
    },
    "shrub": {
        "branch_prob": 0.5,
        "fork_range": (2, 4),
        "length_decay": (0.3, 0.5),
        "width_decay": 0.6,
        "noise_strength": 0.3,
        "leaf_prob": 0.65,
        "leaf_shape": "teardrop",
        "bloom_type": "berry_cluster",
        "min_trunk_ratio": 0.0,
        "base_angle_spread": 1.2,
    },
    "wildflower": {
        "branch_prob": 0.35,
        "fork_range": (1, 4),
        "length_decay": (0.25, 0.55),
        "width_decay": 0.5,
        "noise_strength": 0.35,
        "leaf_prob": 0.55,
        "leaf_shape": "teardrop",
        "bloom_type": "radial_petal",
        "min_trunk_ratio": 0.0,
        "base_angle_spread": 0.3,
    },
    "wisteria": {
        "branch_prob": 0.3,
        "fork_range": (2, 4),
        "length_decay": (0.6, 0.85),
        "width_decay": 0.4,
        "noise_strength": 0.35,
        "leaf_prob": 0.7,
        "leaf_shape": "teardrop",
        "bloom_type": "cascade",
        "min_trunk_ratio": 0.25,
        "base_angle_spread": 0.8,
    },
    "banyan": {
        "branch_prob": 0.5,
        "fork_range": (3, 6),
        "length_decay": (0.35, 0.6),
        "width_decay": 0.55,
        "noise_strength": 0.2,
        "leaf_prob": 0.5,
        "leaf_shape": "small_round",
        "bloom_type": "aerial_root",
        "min_trunk_ratio": 0.15,
        "base_angle_spread": 1.0,
    },
}


def _classify_species(repo: dict) -> str:
    """Classify a repo into a plant species based on its metrics."""
    stars = repo.get("stars", 0)
    age = repo.get("age_months", 0)
    lang = repo.get("language")
    topics = set(repo.get("topics") or [])
    forks = repo.get("forks", 0)
    desc = (repo.get("description") or "").lower()

    # Topic-driven species (highest priority -- richest signal)
    ai_topics = {"ai", "machine-learning", "deep-learning", "neural-network", "llm", "agents", "nlp"}
    data_topics = {"database", "sql", "data", "etl", "pipeline", "data-science", "analytics"}
    web_topics = {"web", "frontend", "react", "vue", "next", "svelte", "html", "css"}
    infra_topics = {"cli", "tool", "utility", "devops", "infrastructure", "docker", "kubernetes"}
    creative_topics = {"game", "graphics", "creative", "art", "music", "visualization"}

    if topics & ai_topics:
        return "wisteria"
    if topics & data_topics:
        return "oak"
    if topics & web_topics:
        return "fern"
    if topics & infra_topics:
        return "bamboo"
    if topics & creative_topics:
        return "wildflower"

    # Fork-heavy repos -- spreading banyan
    if forks > max(stars * 0.4, 3):
        return "banyan"

    # Fall through to existing logic
    if stars >= 100:
        return "oak"
    if stars >= 20 and age >= 24:
        return "birch"
    if lang in ("Rust", "Go", "C", "C++"):
        return "conifer"
    if lang in ("JavaScript", "TypeScript", "HTML", "CSS"):
        return "fern"
    if lang == "Shell":
        return "bamboo"
    if age < 6:
        return "seedling"
    if stars < 5 and age < 18:
        return "shrub"
    return "wildflower"


def _draw_leaf(P, lx, ly, la, ls, lh, has_vein, leaf_shape, rng, budget_ok, oklch_fn):
    """Draw a single leaf with the given shape onto the SVG parts list."""
    # Deterministic imperfection: slight position jitter (1-2px) via seeded rng
    lx += rng.uniform(-1.5, 1.5)
    ly += rng.uniform(-1.5, 1.5)

    def _serrate(val, scale=1.0):
        """Micro-serration: vary a value by 10-20% for organic imperfection."""
        return val + val * rng.uniform(-0.15, 0.15) * scale

    if leaf_shape == "oak_lobed":
        tip_x = lx + ls * math.cos(la)
        tip_y = ly + ls * math.sin(la)
        perp = la + math.pi / 2
        dx = tip_x - lx
        dy = tip_y - ly
        fill_c = oklch_fn(0.48, 0.19, lh)
        stroke_c = oklch_fn(0.36, 0.14, lh)
        b1x = lx + dx * 0.2 + _serrate(ls * 0.3) * math.cos(perp)
        b1y = ly + dy * 0.2 + _serrate(ls * 0.3) * math.sin(perp)
        v1x = lx + dx * 0.35 + _serrate(ls * 0.08) * math.cos(perp)
        v1y = ly + dy * 0.35 + _serrate(ls * 0.08) * math.sin(perp)
        b2x = lx + dx * 0.5 + _serrate(ls * 0.35) * math.cos(perp)
        b2y = ly + dy * 0.5 + _serrate(ls * 0.35) * math.sin(perp)
        v2x = lx + dx * 0.65 + _serrate(ls * 0.1) * math.cos(perp)
        v2y = ly + dy * 0.65 + _serrate(ls * 0.1) * math.sin(perp)
        b3x = lx + dx * 0.8 + _serrate(ls * 0.25) * math.cos(perp)
        b3y = ly + dy * 0.8 + _serrate(ls * 0.25) * math.sin(perp)
        cp_b1x = (lx + b1x) / 2 + _serrate(ls * 0.15) * math.cos(perp)
        cp_b1y = (ly + b1y) / 2 + _serrate(ls * 0.15) * math.sin(perp)
        cp_v1x = (b1x + v1x) / 2 + rng.uniform(-0.5, 0.5)
        cp_v1y = (b1y + v1y) / 2 + rng.uniform(-0.5, 0.5)
        cp_b2x = (v1x + b2x) / 2 + _serrate(ls * 0.18) * math.cos(perp)
        cp_b2y = (v1y + b2y) / 2 + _serrate(ls * 0.18) * math.sin(perp)
        cp_v2x = (b2x + v2x) / 2 + rng.uniform(-0.5, 0.5)
        cp_v2y = (b2y + v2y) / 2 + rng.uniform(-0.5, 0.5)
        cp_b3x = (v2x + b3x) / 2 + _serrate(ls * 0.12) * math.cos(perp)
        cp_b3y = (v2y + b3y) / 2 + _serrate(ls * 0.12) * math.sin(perp)
        cp_tipx = (b3x + tip_x) / 2 + rng.uniform(-0.5, 0.5)
        cp_tipy = (b3y + tip_y) / 2 + rng.uniform(-0.5, 0.5)
        back_cp1x = (tip_x + lx) / 2 - _serrate(ls * 0.1) * math.cos(perp)
        back_cp1y = (tip_y + ly) / 2 - _serrate(ls * 0.1) * math.sin(perp)
        d = (f"M{lx:.1f},{ly:.1f} "
             f"Q{cp_b1x:.1f},{cp_b1y:.1f} {b1x:.1f},{b1y:.1f} "
             f"Q{cp_v1x:.1f},{cp_v1y:.1f} {v1x:.1f},{v1y:.1f} "
             f"Q{cp_b2x:.1f},{cp_b2y:.1f} {b2x:.1f},{b2y:.1f} "
             f"Q{cp_v2x:.1f},{cp_v2y:.1f} {v2x:.1f},{v2y:.1f} "
             f"Q{cp_b3x:.1f},{cp_b3y:.1f} {b3x:.1f},{b3y:.1f} "
             f"Q{cp_tipx:.1f},{cp_tipy:.1f} {tip_x:.1f},{tip_y:.1f} "
             f"Q{back_cp1x:.1f},{back_cp1y:.1f} {lx:.1f},{ly:.1f} Z")
        P.append(f'<path d="{d}" fill="{fill_c}" opacity="0.68" stroke="{stroke_c}" stroke-width="0.4"/>')
        if has_vein and budget_ok():
            P.append(f'<line x1="{lx:.1f}" y1="{ly:.1f}" x2="{tip_x:.1f}" y2="{tip_y:.1f}" '
                     f'stroke="{stroke_c}" stroke-width="0.25" opacity="0.4"/>')

    elif leaf_shape == "small_round":
        cx_l = lx + ls * 0.5 * math.cos(la)
        cy_l = ly + ls * 0.5 * math.sin(la)
        r = ls * 0.4
        fill_c = oklch_fn(0.53, 0.19, lh)
        stroke_c = oklch_fn(0.40, 0.14, lh)
        P.append(f'<circle cx="{cx_l:.1f}" cy="{cy_l:.1f}" r="{r:.1f}" '
                 f'fill="{fill_c}" opacity="0.68" stroke="{stroke_c}" stroke-width="0.4"/>')
        P.append(f'<line x1="{lx:.1f}" y1="{ly:.1f}" x2="{cx_l:.1f}" y2="{cy_l:.1f}" '
                 f'stroke="{stroke_c}" stroke-width="0.4" opacity="0.4"/>')

    elif leaf_shape == "pinnate":
        tip_x = lx + ls * math.cos(la)
        tip_y = ly + ls * math.sin(la)
        stroke_c = oklch_fn(0.40, 0.16, lh)
        fill_c = oklch_fn(0.50, 0.19, lh)
        P.append(f'<line x1="{lx:.1f}" y1="{ly:.1f}" x2="{tip_x:.1f}" y2="{tip_y:.1f}" '
                 f'stroke="{stroke_c}" stroke-width="0.4" opacity="0.68"/>')
        perp = la + math.pi / 2
        for pi in range(1, 4):
            t = pi / 4.0
            mx = lx + (tip_x - lx) * t
            my = ly + (tip_y - ly) * t
            leaflet_len = ls * 0.2 * (1 - t * 0.5)
            for side in [-1, 1]:
                ea = la + side * 0.7
                ex = mx + leaflet_len * math.cos(ea)
                ey = my + leaflet_len * math.sin(ea)
                P.append(f'<line x1="{mx:.1f}" y1="{my:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" '
                         f'stroke="{stroke_c}" stroke-width="0.3" opacity="0.45"/>')
                er = leaflet_len * 0.4
                P.append(f'<ellipse cx="{ex:.1f}" cy="{ey:.1f}" rx="{er:.1f}" ry="{er*0.6:.1f}" '
                         f'fill="{fill_c}" opacity="0.5" '
                         f'transform="rotate({math.degrees(ea):.0f},{ex:.1f},{ey:.1f})"/>')

    elif leaf_shape == "narrow_blade":
        cx_l = lx + ls * 0.4 * math.cos(la)
        cy_l = ly + ls * 0.4 * math.sin(la)
        rx = ls * 0.12
        ry = ls * 0.5
        fill_c = oklch_fn(0.50, 0.19, lh)
        stroke_c = oklch_fn(0.38, 0.14, lh)
        P.append(f'<ellipse cx="{cx_l:.1f}" cy="{cy_l:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" '
                 f'fill="{fill_c}" opacity="0.68" stroke="{stroke_c}" stroke-width="0.3" '
                 f'transform="rotate({math.degrees(la):.0f},{cx_l:.1f},{cy_l:.1f})"/>')

    elif leaf_shape == "needle_cluster":
        stroke_c = oklch_fn(0.38, 0.17, lh)
        n_needles = rng.integers(3, 5)
        for ni in range(n_needles):
            na = la + (ni - n_needles / 2.0) * 0.4
            nl = ls * rng.uniform(0.5, 0.9)
            P.append(f'<line x1="{lx:.1f}" y1="{ly:.1f}" '
                     f'x2="{lx + nl * math.cos(na):.1f}" y2="{ly + nl * math.sin(na):.1f}" '
                     f'stroke="{stroke_c}" stroke-width="0.5" opacity="0.68"/>')

    else:
        # "teardrop" — the original quad-bezier almond shape
        tip_x = lx + ls * math.cos(la)
        tip_y = ly + ls * math.sin(la)
        perp = la + math.pi / 2
        bulge = _serrate(ls * 0.35)
        cp1x = (lx + tip_x) / 2 + bulge * math.cos(perp) + rng.uniform(-0.5, 0.5)
        cp1y = (ly + tip_y) / 2 + bulge * math.sin(perp) + rng.uniform(-0.5, 0.5)
        cp2x = (lx + tip_x) / 2 - bulge * math.cos(perp) + rng.uniform(-0.5, 0.5)
        cp2y = (ly + tip_y) / 2 - bulge * math.sin(perp) + rng.uniform(-0.5, 0.5)
        fill_c = oklch_fn(0.50, 0.19, lh)
        stroke_c = oklch_fn(0.38, 0.14, lh)
        P.append(f'<path d="M{lx:.1f},{ly:.1f} Q{cp1x:.1f},{cp1y:.1f} {tip_x:.1f},{tip_y:.1f} '
                 f'Q{cp2x:.1f},{cp2y:.1f} {lx:.1f},{ly:.1f}" '
                 f'fill="{fill_c}" opacity="0.68" stroke="{stroke_c}" stroke-width="0.4"/>')
        if has_vein and budget_ok():
            P.append(f'<line x1="{lx:.1f}" y1="{ly:.1f}" x2="{tip_x:.1f}" y2="{tip_y:.1f}" '
                     f'stroke="{stroke_c}" stroke-width="0.2" opacity="0.3"/>')
            for vi in range(1, 3):
                vt = vi / 3
                vx = lx + (tip_x - lx) * vt
                vy = ly + (tip_y - ly) * vt
                for side in [-1, 1]:
                    va = la + side * (0.5 + vi * 0.1)
                    vl = ls * 0.2 * (1 - vt * 0.5)
                    P.append(f'<line x1="{vx:.1f}" y1="{vy:.1f}" '
                             f'x2="{vx + vl * math.cos(va):.1f}" y2="{vy + vl * math.sin(va):.1f}" '
                             f'stroke="{stroke_c}" stroke-width="0.15" opacity="0.2"/>')


def _draw_bloom(P, bx, by, bs, bh, n_petals, petal_layers, bloom_type, rng, budget_ok, oklch_fn):
    """Draw a bloom of the given type onto the SVG parts list."""
    # Deterministic imperfection: slight position jitter (1-2px)
    bx += rng.uniform(-1.5, 1.5)
    by += rng.uniform(-1.5, 1.5)
    if bloom_type == "radial_petal":
        for layer in range(petal_layers):
            lf = layer / max(1, petal_layers)
            lr = bs * (1.15 - lf * 0.3)
            lo = 0.55 + lf * 0.2
            rot_off = layer * 0.3
            ph = (bh + layer * 15) % 360
            pc = oklch_fn(0.56 + lf * 0.14, 0.26 - lf * 0.06, ph)
            pd = oklch_fn(0.46 + lf * 0.08, 0.22, ph)
            for pi in range(n_petals):
                pa = pi * 2 * math.pi / n_petals + rot_off + rng.uniform(-0.08, 0.08)
                pr = lr * 0.75
                tip_x = bx + pr * math.cos(pa)
                tip_y = by + pr * math.sin(pa)
                cp_r = pr * 0.55
                cp1x = bx + cp_r * math.cos(pa + 0.35)
                cp1y = by + cp_r * math.sin(pa + 0.35)
                cp2x = bx + cp_r * math.cos(pa - 0.35)
                cp2y = by + cp_r * math.sin(pa - 0.35)
                P.append(f'<path d="M{bx:.1f},{by:.1f} Q{cp1x:.1f},{cp1y:.1f} {tip_x:.1f},{tip_y:.1f} '
                         f'Q{cp2x:.1f},{cp2y:.1f} {bx:.1f},{by:.1f}" '
                         f'fill="{pc}" opacity="{lo:.2f}" stroke="{pd}" stroke-width="0.2"/>')
                P.append(f'<line x1="{bx:.1f}" y1="{by:.1f}" x2="{tip_x:.1f}" y2="{tip_y:.1f}" '
                         f'stroke="{pd}" stroke-width="0.15" opacity="0.15"/>')
        # Center + stamens
        P.append(f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="{bs * 0.18:.1f}" fill="{oklch_fn(0.72, 0.15, (bh + 60) % 360)}" opacity="0.8"/>')
        for si_st in range(max(3, n_petals - 2)):
            sa = si_st * 2 * math.pi / max(3, n_petals - 2) + 0.15
            sr = bs * 0.35
            stx = bx + sr * math.cos(sa)
            sty = by + sr * math.sin(sa)
            P.append(f'<line x1="{bx:.1f}" y1="{by:.1f}" x2="{stx:.1f}" y2="{sty:.1f}" '
                     f'stroke="{oklch_fn(0.65, 0.10, (bh + 40) % 360)}" stroke-width="0.3" opacity="0.4"/>')
            P.append(f'<circle cx="{stx:.1f}" cy="{sty:.1f}" r="0.8" fill="{oklch_fn(0.70, 0.18, 50)}" opacity="0.6"/>')

    elif bloom_type == "acorn":
        body_c = oklch_fn(0.45, 0.12, 35)
        body_dark = oklch_fn(0.38, 0.10, 30)
        cap_c = oklch_fn(0.38, 0.08, 30)
        cap_dark = oklch_fn(0.30, 0.06, 28)
        body_r = bs * 0.35
        cap_h = bs * 0.25
        # Stem nub at top
        P.append(f'<line x1="{bx:.1f}" y1="{by - body_r * 0.6 - cap_h:.1f}" '
                 f'x2="{bx:.1f}" y2="{by - body_r * 0.6 - cap_h - 3:.1f}" '
                 f'stroke="{cap_dark}" stroke-width="0.6" opacity="0.45" stroke-linecap="round"/>')
        # Acorn body with outline and subtle shading
        P.append(f'<ellipse cx="{bx:.1f}" cy="{by + body_r * 0.3:.1f}" rx="{body_r:.1f}" ry="{body_r * 1.2:.1f}" '
                 f'fill="{body_c}" opacity="0.6" stroke="{body_dark}" stroke-width="0.3"/>')
        # Body longitudinal grain lines
        for gi_a in range(-1, 2):
            P.append(f'<line x1="{bx + gi_a * body_r * 0.3:.1f}" y1="{by - body_r * 0.7:.1f}" '
                     f'x2="{bx + gi_a * body_r * 0.25:.1f}" y2="{by + body_r * 1.3:.1f}" '
                     f'stroke="{body_dark}" stroke-width="0.15" opacity="0.12"/>')
        # Body highlight
        P.append(f'<ellipse cx="{bx - body_r * 0.25:.1f}" cy="{by:.1f}" rx="{body_r * 0.25:.1f}" ry="{body_r * 0.6:.1f}" '
                 f'fill="#fff" opacity="0.08"/>')
        # Cap with cross-hatching texture
        P.append(f'<ellipse cx="{bx:.1f}" cy="{by - body_r * 0.4:.1f}" rx="{body_r * 1.1:.1f}" ry="{cap_h:.1f}" '
                 f'fill="{cap_c}" opacity="0.55" stroke="{cap_dark}" stroke-width="0.3"/>')
        # Cap cross-hatch pattern (tiny scale marks)
        n_cap_lines = max(3, int(body_r * 1.5))
        for ci_cap in range(n_cap_lines):
            cx_off = -body_r * 0.9 + ci_cap * body_r * 1.8 / max(1, n_cap_lines - 1)
            cy_cap = by - body_r * 0.4
            hlen = cap_h * 0.6 * (1 - abs(cx_off) / (body_r * 1.1))
            if hlen > 0.5:
                P.append(f'<line x1="{bx + cx_off:.1f}" y1="{cy_cap - hlen:.1f}" '
                         f'x2="{bx + cx_off:.1f}" y2="{cy_cap + hlen:.1f}" '
                         f'stroke="{cap_dark}" stroke-width="0.15" opacity="0.15"/>')
        # Point at bottom of acorn
        P.append(f'<circle cx="{bx:.1f}" cy="{by + body_r * 1.45:.1f}" r="0.5" '
                 f'fill="{body_dark}" opacity="0.4"/>')

    elif bloom_type == "catkin":
        stroke_c = oklch_fn(0.50, 0.08, 80)
        dot_c = oklch_fn(0.58, 0.12, 55)
        droop_len = bs * 1.2
        cpx = bx + rng.uniform(-5, 5)
        cpy = by + droop_len * 0.5
        ex = bx + rng.uniform(-3, 3)
        ey = by + droop_len
        P.append(f'<path d="M{bx:.1f},{by:.1f} Q{cpx:.1f},{cpy:.1f} {ex:.1f},{ey:.1f}" '
                 f'fill="none" stroke="{stroke_c}" stroke-width="0.5" opacity="0.45"/>')
        n_dots = rng.integers(5, 8)
        for di in range(n_dots):
            t = (di + 1) / (n_dots + 1)
            t2 = t
            dx = (1 - t2) ** 2 * bx + 2 * (1 - t2) * t2 * cpx + t2 ** 2 * ex
            dy = (1 - t2) ** 2 * by + 2 * (1 - t2) * t2 * cpy + t2 ** 2 * ey
            P.append(f'<circle cx="{dx:.1f}" cy="{dy:.1f}" r="{rng.uniform(0.8, 1.5):.1f}" '
                     f'fill="{dot_c}" opacity="0.45"/>')
        # Pollen particles drifting from catkin
        for pi_p in range(rng.integers(3, 6)):
            px_p = ex + rng.uniform(-8, 8)
            py_p = ey + rng.uniform(-3, 8)
            P.append(f'<circle cx="{px_p:.1f}" cy="{py_p:.1f}" r="{rng.uniform(0.3, 0.6):.1f}" '
                     f'fill="#d8c870" opacity="{rng.uniform(0.15, 0.30):.2f}"/>')

    elif bloom_type == "berry_cluster":
        berry_c = oklch_fn(0.40, 0.22, (bh + 180) % 360)
        n_berries = rng.integers(4, 7)
        for bi in range(n_berries):
            angle = bi * 2 * math.pi / n_berries + rng.uniform(-0.3, 0.3)
            dist = rng.uniform(0, bs * 0.35)
            bcx = bx + dist * math.cos(angle)
            bcy = by + dist * math.sin(angle)
            br = rng.uniform(bs * 0.12, bs * 0.22)
            P.append(f'<circle cx="{bcx:.1f}" cy="{bcy:.1f}" r="{br:.1f}" '
                     f'fill="{berry_c}" opacity="0.55" stroke="{oklch_fn(0.32, 0.18, (bh + 180) % 360)}" stroke-width="0.2"/>')
            P.append(f'<circle cx="{bcx - br * 0.25:.1f}" cy="{bcy - br * 0.25:.1f}" r="{br * 0.3:.1f}" '
                     f'fill="#fff" opacity="0.2"/>')

    elif bloom_type == "pine_cone":
        cone_c1 = oklch_fn(0.40, 0.10, 30)
        cone_c2 = oklch_fn(0.35, 0.08, 25)
        cone_c3 = oklch_fn(0.45, 0.10, 35)
        cone_c4 = oklch_fn(0.42, 0.12, 32)
        cone_outline = oklch_fn(0.28, 0.06, 22)
        # Overall cone outline (elongated oval)
        P.append(f'<ellipse cx="{bx:.1f}" cy="{by:.1f}" rx="{bs * 0.45:.1f}" ry="{bs * 0.7:.1f}" '
                 f'fill="{cone_c2}" opacity="0.3" stroke="{cone_outline}" stroke-width="0.3"/>')
        # Overlapping scales in rows (5 rows, alternating offset)
        n_rows = 5
        for row in range(n_rows):
            row_frac = row / n_rows
            row_y = by - bs * 0.5 + row * bs * 0.22
            row_w = bs * 0.4 * (1 - abs(row_frac - 0.4) * 1.2)
            n_scales = max(2, 3 + row % 2)
            scale_w = row_w * 2 / n_scales
            offset = scale_w * 0.4 if row % 2 else 0
            c = [cone_c1, cone_c3, cone_c4, cone_c2, cone_c1][row]
            for si_sc in range(n_scales):
                sx = bx - row_w + offset + si_sc * scale_w
                # Individual scale — pointed arch shape
                P.append(f'<path d="M{sx:.1f},{row_y + bs * 0.12:.1f} '
                         f'Q{sx + scale_w * 0.2:.1f},{row_y - bs * 0.02:.1f} {sx + scale_w * 0.5:.1f},{row_y - bs * 0.08:.1f} '
                         f'Q{sx + scale_w * 0.8:.1f},{row_y - bs * 0.02:.1f} {sx + scale_w:.1f},{row_y + bs * 0.12:.1f}" '
                         f'fill="{c}" opacity="0.45" stroke="{cone_outline}" stroke-width="0.15"/>')
        # Stem at top
        P.append(f'<line x1="{bx:.1f}" y1="{by - bs * 0.65:.1f}" x2="{bx:.1f}" y2="{by - bs * 0.85:.1f}" '
                 f'stroke="{cone_outline}" stroke-width="0.5" opacity="0.4" stroke-linecap="round"/>')
        # Shadow beneath
        P.append(f'<ellipse cx="{bx:.1f}" cy="{by + bs * 0.75:.1f}" rx="{bs * 0.3:.1f}" ry="{bs * 0.06:.1f}" '
                 f'fill="#5a4a30" opacity="0.04"/>')

    elif bloom_type == "cascade":
        # Wisteria cascade — drooping chains of small florets
        cascade_c = oklch_fn(0.58, 0.22, bh)
        cascade_d = oklch_fn(0.48, 0.18, (bh + 20) % 360)
        n_chains = max(2, min(5, n_petals // 2))
        for ci_c in range(n_chains):
            chain_angle = -math.pi / 2 + (ci_c - n_chains / 2.0) * 0.3 + rng.uniform(-0.15, 0.15)
            chain_len = bs * rng.uniform(0.8, 1.5)
            n_florets = max(3, int(chain_len / 4))
            cx_c, cy_c = bx, by
            for fi_c in range(n_florets):
                if not budget_ok():
                    break
                t = fi_c / n_florets
                cx_c += rng.uniform(-1.5, 1.5)
                cy_c += chain_len / n_florets
                fr = max(1, bs * 0.12 * (1 - t * 0.4))
                fc = cascade_c if fi_c % 2 == 0 else cascade_d
                P.append(f'<circle cx="{cx_c:.1f}" cy="{cy_c:.1f}" r="{fr:.1f}" '
                         f'fill="{fc}" opacity="{0.55 - t * 0.15:.2f}"/>')

    elif bloom_type == "aerial_root":
        # Banyan aerial roots — thin dangling lines from branches
        root_c = oklch_fn(0.42, 0.08, 40)
        n_roots_ar = max(2, min(6, n_petals // 2))
        for ri_ar in range(n_roots_ar):
            if not budget_ok():
                break
            rx_ar = bx + rng.uniform(-bs * 0.6, bs * 0.6)
            ry_ar = by
            root_len = bs * rng.uniform(0.5, 1.8)
            mid_x = rx_ar + rng.uniform(-4, 4)
            mid_y = ry_ar + root_len * 0.5
            end_y = ry_ar + root_len
            P.append(f'<path d="M{rx_ar:.1f},{ry_ar:.1f} Q{mid_x:.1f},{mid_y:.1f} {rx_ar + rng.uniform(-2, 2):.1f},{end_y:.1f}" '
                     f'fill="none" stroke="{root_c}" stroke-width="{rng.uniform(0.4, 1.0):.2f}" '
                     f'opacity="0.35" stroke-linecap="round"/>')


def generate(
    metrics: dict,
    *,
    seed: str | None = None,
    maturity: float | None = None,
    timeline: bool = False,
    loop_duration: float = 60.0,
    reveal_fraction: float = 0.93,
) -> str:
    base_mat = maturity if maturity is not None else compute_maturity(metrics)
    timeline_enabled = bool(timeline and loop_duration > 0)
    mat = 1.0 if timeline_enabled else base_mat
    h = seed if seed is not None else seed_hash(metrics)
    base_seed = int(h[:8], 16)
    noise = Noise2D(seed=int(h[8:16], 16))

    repos = metrics.get("repos", [])[:MAX_REPOS]
    monthly = metrics.get("contributions_monthly", {})
    forks = metrics.get("forks", 0)
    watchers = metrics.get("watchers", 0)
    total_commits = metrics.get("total_commits", 500)
    open_issues = metrics.get("open_issues_count", 0)
    network = metrics.get("network_count", 0)
    stars_total = metrics.get("stars", 0)
    contributions = metrics.get("contributions_last_year", 200)
    orgs = metrics.get("orgs_count", 1)

    # ── Enriched metric extraction ────────────────────────────────
    streaks = metrics.get("contribution_streaks", {})
    current_streak = streaks.get("current_streak_months", 0) if isinstance(streaks, dict) else 0
    streak_active = streaks.get("streak_active", False) if isinstance(streaks, dict) else False
    vigor_multiplier = 1.0 + min(0.5, current_streak * 0.04)  # up to 1.5x

    lang_bytes = metrics.get("languages", {})
    if lang_bytes and isinstance(lang_bytes, dict):
        dominant_lang = max(lang_bytes, key=lang_bytes.get)
    else:
        dominant_lang = None

    # Sky and atmosphere tinting based on dominant language
    lang_sky_tint = {
        "Python": (0.58, 0.03, 150),    # cool green-blue
        "JavaScript": (0.62, 0.04, 65),  # warm amber
        "TypeScript": (0.56, 0.04, 230), # cool blue
        "Rust": (0.55, 0.03, 30),        # warm rust
        "Go": (0.58, 0.04, 185),         # teal
        "Ruby": (0.56, 0.04, 350),       # rosy
    }.get(dominant_lang, (0.58, 0.02, 150))

    def _repo_date(repo: dict) -> str | None:
        for key in ("date", "created_at", "created", "pushed_at", "updated_at"):
            val = repo.get(key)
            if isinstance(val, str) and val.strip():
                return val[:10] if len(val) >= 10 else val
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
    timeline_start, timeline_end = timeline_window
    timeline_span_days = max((timeline_end - timeline_start).days, 1)
    daily_series = contributions_monthly_to_daily_series(
        monthly,
        reference_year=timeline_end.year,
    )
    sorted_daily = sorted(daily_series.items(), key=lambda kv: kv[0])
    total_daily = sum(max(0, int(v)) for _, v in sorted_daily)

    def _parse_date(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            if len(value) == 10:
                return datetime.fromisoformat(value)
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            return None

    def _date_at_fraction(frac: float) -> str:
        frac = max(0.0, min(1.0, frac))
        day_offset = int(round(frac * timeline_span_days))
        return (timeline_start + timedelta(days=day_offset)).isoformat()

    def _date_for_activity_fraction(frac: float) -> str:
        frac = max(0.0, min(1.0, frac))
        if total_daily <= 0 or not sorted_daily:
            return _date_at_fraction(frac)
        threshold = frac * total_daily
        running = 0.0
        for day, count in sorted_daily:
            running += max(0, int(count))
            if running >= threshold:
                return day
        return sorted_daily[-1][0]

    def _offset_date(when: str, frac_offset: float) -> str:
        base = _parse_date(when)
        if base is None:
            base = datetime.combine(timeline_start, datetime.min.time())
        add_days = int(round(max(0.0, frac_offset) * timeline_span_days))
        shifted = (base + timedelta(days=add_days)).date()
        if shifted < timeline_start:
            shifted = timeline_start
        if shifted > timeline_end:
            shifted = timeline_end
        return shifted.isoformat()

    def _month_key_date(month_key: str, idx: int) -> str:
        mk = str(month_key).strip()
        if len(mk) == 7 and mk[4] == "-":
            return f"{mk}-01"
        if mk.isdigit():
            month_n = max(1, min(12, int(mk)))
            return f"{timeline_end.year:04d}-{month_n:02d}-01"
        approx_month = 1 + (idx % 12)
        return f"{timeline_end.year:04d}-{approx_month:02d}-01"

    def _timeline_style(
        when: str,
        opacity: float,
        cls: str = "tl-reveal",
        *,
        delay_offset_frac: float = 0.0,
        duration_scale: float = 1.0,
        ease: str = "ease-out",
    ) -> str:
        if not timeline_enabled:
            return f'opacity="{opacity}"'
        delay = map_date_to_loop_delay(
            when,
            timeline_window,
            duration=loop_duration,
            reveal_fraction=reveal_fraction,
        )
        delay += max(-0.08, min(0.12, delay_offset_frac)) * loop_duration
        delay = max(0.0, min(loop_duration, delay))
        duration = max(0.35, 0.9 * duration_scale)
        return (
            f'class="{cls}" '
            f'style="--delay:{delay:.3f}s;--to:{max(0.0, min(1.0, opacity)):.3f};'
            f'--dur:{duration:.3f}s;--ease:{ease}" data-delay="{delay:.3f}" data-when="{when}"'
        )

    # Ground line — slightly below center, gentle hills
    GROUND_Y = CY + 40

    def ground_y_at(x):
        return GROUND_Y + noise.noise(x * 0.008, 0) * 25 + noise.noise(x * 0.02, 5) * 8

    # Collect all visual elements
    all_segs = []   # (x1,y1,x2,y2,sw,hue,depth,is_main,bark_mat,when)
    roots = []       # (x1,y1,x2,y2,sw,when)
    leaves = []      # (x,y,angle,size,hue,has_vein,leaf_shape,when)
    blooms = []      # (x,y,size,hue,n_petals,layers,bloom_type,when)
    buds = []        # (x,y,size,hue,when)
    berries = []     # (x,y,size,hue,when)
    tendrils = []    # list of point-lists
    mushrooms_list = []  # (x,y,size,hue)
    insects = []     # (x,y,type,size,hue)
    webs = []        # (cx,cy,radius,n_spokes)
    dew_drops = []   # (x,y,size)
    seeds = []       # (x,y,angle,size)
    labels = []      # (lx,ly,text,ax,ay,when)

    # Track plant base positions for ground cover enhancement
    plant_bases = []

    # ── Plant generation (progressive: blank soil → full garden) ────
    n_repos = len(repos)
    spread = min(MAX_REPOS, n_repos)
    cluster_rng = np.random.default_rng(base_seed ^ 0xC1A55EED)
    cluster_sizes = []
    remaining = spread
    while remaining > 0:
        max_size = min(4, remaining)
        min_size = 1 if remaining <= 2 else 2
        size = int(cluster_rng.integers(min_size, max_size + 1))
        if remaining - size == 1 and size > min_size:
            size -= 1
        cluster_sizes.append(size)
        remaining -= size
    cluster_count = len(cluster_sizes)
    if cluster_count > 1:
        cluster_centers_base = np.linspace(95, WIDTH - 95, cluster_count)
    else:
        cluster_centers_base = np.array([CX], dtype=float)
    cluster_centers = []
    for ci, base_center in enumerate(cluster_centers_base):
        nudge = noise.fbm(ci * 2.3 + 0.7, spread * 0.41 + 0.3, 3) * 36 + cluster_rng.uniform(-16, 16)
        cluster_centers.append(float(max(85, min(WIDTH - 85, base_center + nudge))))
    cluster_slot = {}
    cursor = 0
    for ci, size in enumerate(cluster_sizes):
        for local_idx in range(size):
            cluster_slot[cursor + local_idx] = (ci, local_idx, size)
        cursor += size

    # ── Metaheuristic layout + palette optimization ───────────────
    if len(repos) >= 2:
        initial_positions = [
            (WIDTH * (0.12 + 0.76 * i / max(len(repos) - 1, 1)), GROUND_Y)
            for i in range(len(repos))
        ]
        tree_weights = [max(1, repo.get("stars", 0)) for repo in repos]
        optimized = optimize_layout_sa(
            initial_positions,
            tree_weights,
            WIDTH,
            HEIGHT,
            min_spacing=WIDTH / max(len(repos) + 1, 2) * 0.7,
            iterations=200,
            seed=int(h[:8], 16) if h else 42,
        )
        tree_x_positions = [pos[0] for pos in optimized]
    else:
        tree_x_positions = [WIDTH / 2]

    repo_hues = [LANG_HUES.get(repo.get("language"), 155) for repo in repos]
    if len(repo_hues) >= 2:
        repo_hues = optimize_palette_hues(
            repo_hues,
            max_shift=12.0,
            iterations=150,
            seed=int(h[:8], 16) if h else 42,
        )

    RAMP = 0.15  # growth ramp width (mat units)
    first_start = 0.03
    last_full = max(first_start + RAMP, mat)
    last_start = last_full - RAMP

    for ri, repo in enumerate(repos):
        # Per-tree growth: stagger birth times, grow from seedling → full
        tree_start = first_start + (ri / max(1, n_repos - 1)) * (last_start - first_start) if n_repos > 1 else first_start
        tree_t = max(0.0, min(1.0, (mat - tree_start) / RAMP))

        if tree_t <= 0:
            continue  # not yet sprouted

        # Per-repo RNG — each tree is fully deterministic regardless
        # of how many other trees are visible (stable across frames)
        rng = np.random.default_rng(base_seed ^ ((ri + 1) * 0x9E3779B9))

        lang = repo.get("language")
        hue = repo_hues[ri] if ri < len(repo_hues) else LANG_HUES.get(lang, 160)
        repo_stars = repo.get("stars", 0)
        age = repo.get("age_months", 6)
        repo_date = _repo_date(repo) or _date_for_activity_fraction(ri / max(1, n_repos))
        trunk_when = repo_date
        branch_when = _offset_date(repo_date, 0.08)
        leaf_when = _offset_date(repo_date, 0.14)
        bloom_when = _offset_date(repo_date, 0.22)
        root_when = _offset_date(repo_date, 0.05)

        species = _classify_species(repo)
        style = SPECIES.get(species)

        # Seasonal color variation: date-aware hue drift + mature autumn accent.
        is_autumn = mat > 0.7 and ri >= n_repos - 2 and n_repos >= 2
        repo_dt = _parse_date(repo_date)
        repo_month = repo_dt.month if repo_dt else timeline_end.month
        season_phase = ((repo_month - 1) / 12.0) * 2 * math.pi
        leaf_hue_shift = 16 * math.sin(season_phase - 0.4) + rng.uniform(-5, 5)
        bloom_hue_shift = 22 * math.cos(season_phase - 0.2) + rng.uniform(-8, 8)
        autumn_leaf_hue = rng.integers(30, 50) if is_autumn else None
        # Use metaheuristic-optimized x position (SA layout optimizer)
        base_x = tree_x_positions[ri] if ri < len(tree_x_positions) else CX
        base_x += rng.uniform(-8, 8)
        base_x = max(80, min(WIDTH - 80, base_x))
        gy = ground_y_at(base_x)

        base_angle = -math.pi / 2 + rng.uniform(-0.3, 0.3)
        # Data mapping: commits -> trunk height, total_commits scales globally
        commit_factor = min(1.5, 1.0 + math.log1p(total_commits) / 20.0)
        main_length = max(50, (70 + min(280, age * 3.5)) * tree_t * commit_factor)
        max_depth = max(1, round(max(2, min(6, 2 + age // 12)) * tree_t))
        # Data mapping: commits -> trunk thickness (vigor from contribution streaks)
        stem_sw = max(2.5, (3.2 + min(3.5, age * 0.06) + min(1.8, total_commits / 4000.0)) * (0.4 + 0.6 * tree_t))
        stem_sw *= vigor_multiplier
        # Data mapping: age -> bark maturity factor (drives bark texture density)
        bark_maturity = min(1.0, age / 60.0)
        # Data mapping: stars -> bloom density multiplier (vigor boosts blooms)
        bloom_boost = min(2.0, 1.0 + stars_total / 200.0) * vigor_multiplier

        if main_length >= 5:
            labels.append((base_x, gy + 18, repo.get("name", ""), base_x, gy, trunk_when))
        plant_bases.append((base_x, gy))

        # ── Fern growth (special algorithm) ───────────────────────
        if species == "fern":
            def _grow_frond(fx, fy, f_angle, f_length, f_hue):
                """Grow a single fern frond: arcing spine with pinnate leaflets."""
                n_spine = max(8, int(f_length / 8))
                cx_, cy_ = fx, fy
                cur_angle = f_angle
                for si in range(n_spine):
                    if len(all_segs) >= MAX_SEGS:
                        break
                    t = si / n_spine
                    # Arc: starts upward, curves over gracefully
                    cur_angle += 0.05 + t * 0.08
                    sl = f_length / n_spine * (1 - t * 0.3)
                    nx_ = cx_ + sl * math.cos(cur_angle)
                    ny_ = cy_ + sl * math.sin(cur_angle)
                    sw = max(0.3, stem_sw * 0.5 * (1 - t * 0.7))
                    all_segs.append((cx_, cy_, nx_, ny_, sw, f_hue, 1, si < 3, bark_maturity, branch_when))

                    # Pinnate leaflets along both sides (alternating, shrinking)
                    if si > 1 and si < n_spine - 1:
                        leaflet_size = f_length * 0.08 * (1 - t * 0.6)
                        side = 1 if si % 2 == 0 else -1
                        perp = cur_angle + side * math.pi / 2
                        la = perp + rng.uniform(-0.2, 0.2)
                        if len(leaves) < MAX_LEAVES:
                            _lhue = autumn_leaf_hue if is_autumn else (f_hue + 15 + leaf_hue_shift) % 360
                            leaves.append((nx_, ny_, la, max(2, leaflet_size), _lhue, False, "pinnate", leaf_when))

                    cx_, cy_ = nx_, ny_

                # Fiddlehead spiral at the tip
                spiral_segs = 5
                for si in range(spiral_segs):
                    if len(all_segs) >= MAX_SEGS:
                        break
                    t = si / spiral_segs
                    cur_angle += 0.5 + t * 0.8
                    sl = 3 * (1 - t * 0.5)
                    nx_ = cx_ + sl * math.cos(cur_angle)
                    ny_ = cy_ + sl * math.sin(cur_angle)
                    all_segs.append((cx_, cy_, nx_, ny_, 0.3, f_hue, 2, False, bark_maturity, branch_when))
                    cx_, cy_ = nx_, ny_

            n_fronds = max(2, min(5, 2 + age // 12))
            for fi in range(n_fronds):
                f_angle = base_angle + (fi - n_fronds / 2.0) * 0.4 + rng.uniform(-0.15, 0.15)
                f_length = main_length * rng.uniform(0.6, 1.0)
                _grow_frond(base_x, gy, f_angle, f_length, hue)

        # ── Bamboo growth (special algorithm) ─────────────────────
        elif species == "bamboo":
            def _grow_bamboo(bx, by, b_hue):
                """Grow a bamboo cane: straight vertical with joints and leaf clusters."""
                cane_height = min(300, main_length * 1.5)
                joint_spacing = rng.uniform(18, 28)
                n_joints = max(3, int(cane_height / joint_spacing))
                sw = 1.5
                cx_, cy_ = bx, by
                for ji in range(n_joints):
                    if len(all_segs) >= MAX_SEGS:
                        break
                    t = ji / n_joints
                    # Mostly vertical, very slight sway
                    sway = noise.noise(bx * 0.01 + ji * 0.5, by * 0.01) * 2
                    nx_ = cx_ + sway
                    ny_ = cy_ - joint_spacing
                    all_segs.append((cx_, cy_, nx_, ny_, sw, b_hue, 0, True, bark_maturity, trunk_when))

                    # Visible joint (short horizontal widening)
                    jw = sw * 1.8
                    all_segs.append((nx_ - jw, ny_, nx_ + jw, ny_, sw * 0.6, b_hue, 1, False, bark_maturity, branch_when))

                    # Narrow leaf clusters at alternating joints
                    if ji % 2 == 0 and ji > 0:
                        n_blades = rng.integers(2, 5)
                        side = rng.choice([-1, 1])
                        for bi in range(n_blades):
                            la = -math.pi / 2 + side * (0.8 + bi * 0.2) + rng.uniform(-0.15, 0.15)
                            ls = rng.uniform(6, 14) * (1 - t * 0.3)
                            if len(leaves) < MAX_LEAVES:
                                _lhue = autumn_leaf_hue if is_autumn else (b_hue + 20 + leaf_hue_shift) % 360
                                leaves.append((nx_, ny_, la, ls, _lhue, False, "narrow_blade", leaf_when))

                    cx_, cy_ = nx_, ny_

            n_canes = max(1, min(3, 1 + age // 24))
            for ci in range(n_canes):
                offset = (ci - n_canes / 2.0) * 6
                _grow_bamboo(base_x + offset, gy, hue)

        # ── Seedling (small version of wildflower style) ──────────
        elif species == "seedling":
            seedling_style = {
                "branch_prob": 0.15,
                "fork_range": (1, 2),
                "length_decay": (0.3, 0.5),
                "width_decay": 0.5,
                "noise_strength": 0.2,
                "leaf_prob": 0.7,
                "leaf_shape": "teardrop",
                "bloom_type": "radial_petal",
                "min_trunk_ratio": 0.0,
                "base_angle_spread": 0.3,
            }
            short_length = min(60, main_length * 0.4)
            short_depth = min(2, max_depth)

            def _grow(x, y, angle, depth, length, sw, style_d=seedling_style, max_d=short_depth):
                if depth > max_d or length < 5 or len(all_segs) >= MAX_SEGS:
                    return
                n_s = max(2, int(length / 12))
                cx_, cy_ = x, y
                for si in range(n_s):
                    if len(all_segs) >= MAX_SEGS:
                        break
                    nv = noise.fbm(cx_ * 0.005 + ri * 7, cy_ * 0.005, 3)
                    a = angle + nv * style_d["noise_strength"] * (1 + depth * 0.25)
                    sl = length / n_s * rng.uniform(0.85, 1.15)
                    nx_ = cx_ + sl * math.cos(a)
                    ny_ = cy_ + sl * math.sin(a)
                    if ny_ > ground_y_at(nx_) - 5:
                        a -= 0.3
                        nx_ = cx_ + sl * math.cos(a)
                        ny_ = cy_ + sl * math.sin(a)
                    if nx_ < 30 or nx_ > WIDTH - 30 or ny_ < 30:
                        a += (math.atan2(CY - ny_, CX - nx_) - a) * 0.4
                        nx_ = cx_ + sl * math.cos(a)
                        ny_ = cy_ + sl * math.sin(a)

                    all_segs.append((cx_, cy_, nx_, ny_, sw, hue, depth, depth == 0, bark_maturity, trunk_when if depth == 0 else branch_when))

                    if depth >= 1 and rng.random() < style_d["leaf_prob"]:
                        side = rng.choice([-1, 1])
                        la = a + side * (0.5 + rng.uniform(0, 0.6))
                        ls = 5 + rng.uniform(0, 6) * (1 - depth / (max_d + 1))
                        _lhue = autumn_leaf_hue if is_autumn else (hue + 25 + leaf_hue_shift) % 360
                        leaves.append((nx_, ny_, la, ls, _lhue, rng.random() < 0.7, style_d["leaf_shape"], leaf_when))
                        if rng.random() < 0.15:
                            dew_drops.append((
                                nx_ + ls * 0.5 * math.cos(la),
                                ny_ + ls * 0.5 * math.sin(la),
                                rng.uniform(1, 2.5),
                            ))

                    if depth >= 2 and rng.random() < 0.12:
                        buds.append((nx_, ny_, rng.uniform(2, 4), hue, bloom_when))

                    cx_, cy_ = nx_, ny_
                    angle = a

                    # Murray's Law: child branch width from parent^3 = child1^3 + child2^3
                    if len(all_segs) < MAX_SEGS and rng.random() < style_d["branch_prob"] * (1 - depth / max_d):
                        fa = rng.uniform(0.4, 1.1) * rng.choice([-1, 1])
                        decay_lo, decay_hi = style_d["length_decay"]
                        # Murray's law: assume remaining trunk takes ~70% of flow
                        child_sw = (sw ** 3 * 0.3) ** (1.0 / 3.0)
                        _grow(cx_, cy_, a + fa, depth + 1, length * rng.uniform(decay_lo, decay_hi), child_sw, style_d, max_d)

                # Terminal fork
                if depth < max_d and len(all_segs) < MAX_SEGS:
                    fork_lo, fork_hi = style_d["fork_range"]
                    n_forks = rng.integers(fork_lo, fork_hi)
                    # Murray's Law: parent_sw^3 = sum(child_sw_i^3)
                    # Equal split among n_forks children
                    child_sw_fork = (sw ** 3 / max(1, n_forks)) ** (1.0 / 3.0)
                    for _ in range(n_forks):
                        if len(all_segs) >= MAX_SEGS:
                            break
                        fa = rng.uniform(0.3, 1.0) * rng.choice([-1, 1])
                        decay_lo, decay_hi = style_d["length_decay"]
                        _grow(cx_, cy_, angle + fa, depth + 1, length * rng.uniform(decay_lo, decay_hi), child_sw_fork, style_d, max_d)

                # Blooms at tips — bloom probability boosted by total stars
                if depth >= max_d - 1 and rng.random() < min(0.85, 0.6 * bloom_boost):
                    n_petals = max(4, min(12, 4 + repo_stars // 2))
                    bloom_size = max(12, 7 + min(22, repo_stars * 1.0))
                    petal_layers = 1 + min(3, repo_stars // 5)
                    blooms.append((cx_, cy_, bloom_size, (hue + bloom_hue_shift) % 360, n_petals, petal_layers, style_d["bloom_type"], bloom_when))

                # Berries
                if depth >= max_d and rng.random() < 0.2:
                    for _ in range(rng.integers(2, 6)):
                        berries.append((
                            cx_ + rng.uniform(-6, 6),
                            cy_ + rng.uniform(-6, 6),
                            rng.uniform(1.5, 3),
                            (hue + 180) % 360,
                            bloom_when,
                        ))

            _grow(base_x, gy, base_angle, 0, short_length, stem_sw * 0.6)

        # ── Standard species-driven growth (oak, birch, conifer, shrub, wildflower) ──
        elif style is not None:
            def _grow(x, y, angle, depth, length, sw, style_d=style, max_d=max_depth, seg_idx=0):
                if depth > max_d or length < 5 or len(all_segs) >= MAX_SEGS:
                    return
                n_s = max(2, int(length / 12))
                cx_, cy_ = x, y
                for si in range(n_s):
                    if len(all_segs) >= MAX_SEGS:
                        break
                    nv = noise.fbm(cx_ * 0.005 + ri * 7, cy_ * 0.005, 3)
                    a = angle + nv * style_d["noise_strength"] * (1 + depth * 0.25)
                    sl = length / n_s * rng.uniform(0.85, 1.15)
                    nx_ = cx_ + sl * math.cos(a)
                    ny_ = cy_ + sl * math.sin(a)
                    if ny_ > ground_y_at(nx_) - 5:
                        a -= 0.3
                        nx_ = cx_ + sl * math.cos(a)
                        ny_ = cy_ + sl * math.sin(a)
                    if nx_ < 30 or nx_ > WIDTH - 30 or ny_ < 30:
                        a += (math.atan2(CY - ny_, CX - nx_) - a) * 0.4
                        nx_ = cx_ + sl * math.cos(a)
                        ny_ = cy_ + sl * math.sin(a)

                    all_segs.append((cx_, cy_, nx_, ny_, sw, hue, depth, depth == 0, bark_maturity, trunk_when if depth == 0 else branch_when))

                    if depth >= 1 and rng.random() < style_d["leaf_prob"]:
                        side = rng.choice([-1, 1])
                        la = a + side * (0.5 + rng.uniform(0, 0.6))
                        ls = 5 + rng.uniform(0, 6) * (1 - depth / (max_d + 1))
                        _lhue = autumn_leaf_hue if is_autumn else (hue + 25 + leaf_hue_shift) % 360
                        leaves.append((nx_, ny_, la, ls, _lhue, rng.random() < 0.7, style_d["leaf_shape"], leaf_when))
                        if rng.random() < 0.15:
                            dew_drops.append((
                                nx_ + ls * 0.5 * math.cos(la),
                                ny_ + ls * 0.5 * math.sin(la),
                                rng.uniform(1, 2.5),
                            ))

                    if depth >= 2 and rng.random() < 0.12:
                        buds.append((nx_, ny_, rng.uniform(2, 4), hue, bloom_when))

                    cx_, cy_ = nx_, ny_
                    angle = a

                    # min_trunk_ratio: for depth==0, don't branch until past trunk portion
                    trunk_ok = True
                    if depth == 0:
                        trunk_ok = (si + seg_idx) > n_s * style_d["min_trunk_ratio"]

                    # Murray's Law: child branch width from parent^3 = child1^3 + child2^3
                    if trunk_ok and len(all_segs) < MAX_SEGS and rng.random() < style_d["branch_prob"] * (1 - depth / max_d):
                        angle_range = style_d.get("branch_angle_range", (0.4, 1.1))
                        fa = rng.uniform(angle_range[0], angle_range[1]) * rng.choice([-1, 1])
                        decay_lo, decay_hi = style_d["length_decay"]
                        # Murray's law: assume remaining trunk takes ~70% of flow
                        child_sw = (sw ** 3 * 0.3) ** (1.0 / 3.0)
                        _grow(cx_, cy_, a + fa, depth + 1, length * rng.uniform(decay_lo, decay_hi), child_sw, style_d, max_d, si)

                # Terminal fork — Murray's Law: parent_sw^3 = sum(child_sw_i^3)
                if depth < max_d and len(all_segs) < MAX_SEGS:
                    fork_lo, fork_hi = style_d["fork_range"]
                    n_forks = rng.integers(fork_lo, fork_hi)
                    # Equal split among n_forks children
                    child_sw_fork = (sw ** 3 / max(1, n_forks)) ** (1.0 / 3.0)
                    for _ in range(n_forks):
                        if len(all_segs) >= MAX_SEGS:
                            break
                        spread_a = style_d["base_angle_spread"] if depth == 0 else 1.0
                        lo_a, hi_a = sorted((0.3, spread_a))
                        fa = rng.uniform(lo_a, hi_a) * rng.choice([-1, 1])
                        decay_lo, decay_hi = style_d["length_decay"]
                        _grow(cx_, cy_, angle + fa, depth + 1, length * rng.uniform(decay_lo, decay_hi), child_sw_fork, style_d, max_d, 0)

                # Blooms at tips (fern and bamboo have no blooms — handled above)
                # bloom probability boosted by total stars
                if depth >= max_d - 1 and rng.random() < min(0.85, 0.6 * bloom_boost):
                    n_petals = max(4, min(12, 4 + repo_stars // 2))
                    bloom_size = max(12, 7 + min(22, repo_stars * 1.0))
                    petal_layers = 1 + min(3, repo_stars // 5)
                    blooms.append((cx_, cy_, bloom_size, (hue + bloom_hue_shift) % 360, n_petals, petal_layers, style_d["bloom_type"], bloom_when))

                # Berries
                if depth >= max_d and rng.random() < 0.2:
                    for _ in range(rng.integers(2, 6)):
                        berries.append((
                            cx_ + rng.uniform(-6, 6),
                            cy_ + rng.uniform(-6, 6),
                            rng.uniform(1.5, 3),
                            (hue + 180) % 360,
                            bloom_when,
                        ))

            _grow(base_x, gy, base_angle, 0, main_length, stem_sw)

        # ── Root system (scales with tree growth; forks -> root spread) ─
        # Data mapping: forks -> wider root spread angle and more root count
        fork_spread = min(1.2, 0.5 + forks / 20.0)
        root_depth = (40 + min(100, age * 1.2)) * tree_t
        n_roots = max(1, round(max(2, min(7, 2 + forks // 5)) * tree_t)) if root_depth >= 1 else 0
        for rootn in range(n_roots):
            if len(roots) >= MAX_ROOTS:
                break
            ra = math.pi / 2 + rng.uniform(-fork_spread, fork_spread)
            rx, ry = base_x + rng.uniform(-8 * fork_spread, 8 * fork_spread), gy
            r_len = root_depth * rng.uniform(0.5, 1.0)
            r_segs = max(3, int(r_len / 10))
            r_sw = stem_sw * 0.5
            for rsi in range(r_segs):
                if len(roots) >= MAX_ROOTS:
                    break
                nv = noise.fbm(rx * 0.01 + rootn * 3, ry * 0.01, 2)
                ra += nv * 0.3
                sl = r_len / r_segs
                nrx = rx + sl * math.cos(ra)
                nry = ry + sl * math.sin(ra)
                roots.append((rx, ry, nrx, nry, r_sw * (1 - rsi / r_segs * 0.6), root_when))
                rx, ry = nrx, nry
                r_sw *= 0.92
                if rng.random() < 0.2 and len(roots) < MAX_ROOTS:
                    bra = ra + rng.choice([-1, 1]) * rng.uniform(0.3, 0.8)
                    brx, bry = rx, ry
                    for _ in range(rng.integers(2, 4)):
                        if len(roots) >= MAX_ROOTS:
                            break
                        bnrx = brx + 8 * math.cos(bra) + rng.uniform(-2, 2)
                        bnry = bry + 8 * math.sin(bra) + rng.uniform(-1, 1)
                        roots.append((brx, bry, bnrx, bnry, r_sw * 0.4, root_when))
                        brx, bry = bnrx, bnry

    # Restore stable RNG for ambient elements (independent of n_visible)
    rng = np.random.default_rng(base_seed ^ 0xA5A5A5A5)

    # ── Tendrils ──────────────────────────────────────────────────
    n_tendrils = min(6, metrics.get("following", 0) // 12)
    for ti in range(n_tendrils):
        if all_segs:
            seg = all_segs[rng.integers(0, len(all_segs))]
            tx, ty = seg[2], seg[3]
            ta = rng.uniform(0, 2 * math.pi)
            pts = [(tx, ty)]
            for step in range(12):
                ta += 0.4 * math.sin(step * 0.8 + ti)
                tx += 4 * math.cos(ta)
                ty += 4 * math.sin(ta)
                pts.append((tx, ty))
            tendrils.append(pts)

    # ── Mushrooms ─────────────────────────────────────────────────
    for mi in range(min(6, open_issues)):
        mx = 60 + rng.uniform(0, WIDTH - 120)
        mushrooms_list.append((mx, ground_y_at(mx) + rng.uniform(-3, 5), 4 + rng.uniform(0, 6), 30 + rng.integers(0, 40)))

    # ── Insects (data-driven: PRs -> pollinators, reviews -> bees) ──
    total_prs_count = metrics.get("total_prs", 0) or 0
    review_count = metrics.get("pr_review_count", 0) or 0
    n_butterflies = min(8, max(1, total_prs_count // 20))
    n_bees = min(4, max(0, review_count // 40))
    n_dragonflies = min(3, max(0, (metrics.get("public_gists", 0) or 0) // 10))
    n_ladybugs = min(4, max(1, len(repos) // 3))

    for _ in range(n_butterflies):
        insects.append((rng.uniform(50, WIDTH - 50), rng.uniform(40, GROUND_Y - 20), "butterfly", rng.uniform(8, 16), rng.integers(0, 360)))
    for _ in range(n_bees):
        insects.append((rng.uniform(80, WIDTH - 80), rng.uniform(60, GROUND_Y - 40), "bee", rng.uniform(4, 8), 45))
    for _ in range(n_dragonflies):
        insects.append((rng.uniform(60, WIDTH - 60), rng.uniform(30, GROUND_Y - 50), "dragonfly", rng.uniform(10, 18), rng.integers(0, 360)))
    for _ in range(n_ladybugs):
        insects.append((rng.uniform(60, WIDTH - 60), rng.uniform(GROUND_Y - 15, GROUND_Y + 5), "ladybug", rng.uniform(3, 5), 0))

    # ── Webs ──────────────────────────────────────────────────────
    if mat > 0.25:
        for _ in range(min(3, network // 10)):
            if all_segs:
                seg = all_segs[rng.integers(0, len(all_segs))]
                webs.append((seg[2], seg[3], rng.uniform(12, 25), rng.integers(5, 9)))

    # ── Falling seeds (dandelion wisps + maple samaras) ───────────
    if mat > 0.2:
        for _ in range(min(10, stars_total // 5)):
            seeds.append((rng.uniform(40, WIDTH - 40), rng.uniform(30, GROUND_Y - 10), rng.uniform(-0.3, 0.3), rng.uniform(2, 5)))
    # Maple samaras — spinning helicopter seeds
    samaras = []
    if mat > 0.35:
        for _ in range(min(6, stars_total // 8)):
            samaras.append((rng.uniform(50, WIDTH - 50), rng.uniform(40, GROUND_Y - 20),
                            rng.uniform(-0.8, 0.8), rng.uniform(3, 7)))

    # ══════════════════════════════════════════════════════════════
    # BUILD SVG
    # ══════════════════════════════════════════════════════════════
    P = []  # parts list
    P.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">')
    if timeline_enabled:
        P.append(
            "<style>"
            "@keyframes inkGardenReveal{0%{opacity:0}100%{opacity:var(--to,1)}}"
            ".tl-reveal{opacity:0;animation:inkGardenReveal var(--dur,.9s) var(--ease,ease-out) var(--delay,0s) both}"
            "</style>"
        )

    # ── defs ──────────────────────────────────────────────────────
    P.append('<defs>')
    # Canvas/paper texture overlay — subtle woven linen feel via feTurbulence + feDisplacementMap
    P.append('''<filter id="canvas" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="turbulence" baseFrequency="0.35 0.25" numOctaves="3" seed="19" result="weave"/>
    <feDisplacementMap in="SourceGraphic" in2="weave" scale="0.8" xChannelSelector="R" yChannelSelector="G"/>
  </filter>''')
    # Ink displacement — subtle organic wobble
    P.append('''<filter id="ink" x="-3%" y="-3%" width="106%" height="106%">
    <feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="4" seed="42" result="n"/>
    <feDisplacementMap in="SourceGraphic" in2="n" scale="1.2" xChannelSelector="R" yChannelSelector="G"/>
  </filter>''')
    # Paper grain — diffuse lighting for tactile parchment feel
    P.append('''<filter id="paper" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="5" seed="7" result="noise"/>
    <feDiffuseLighting in="noise" lighting-color="#f8f3ea" surfaceScale="1.2" result="lit">
      <feDistantLight azimuth="225" elevation="55"/>
    </feDiffuseLighting>
    <feComposite in="SourceGraphic" in2="lit" operator="arithmetic" k1="0.6" k2="0.5" k3="0.1" k4="0"/>
  </filter>''')
    # Soft glow for dew and highlights
    P.append('''<filter id="dew">
    <feGaussianBlur in="SourceGraphic" stdDeviation="0.6"/>
    <feComposite in="SourceGraphic" operator="over"/>
  </filter>''')
    # Dew drop radial gradient
    P.append('''<radialGradient id="dewGrad" cx="30%" cy="30%">
    <stop offset="0%" stop-color="#ffffff" stop-opacity="0.95"/>
    <stop offset="35%" stop-color="#e8f4ff" stop-opacity="0.65"/>
    <stop offset="100%" stop-color="#a8d4ee" stop-opacity="0.15"/>
  </radialGradient>''')
    # Vignette gradient — subtle edge darkening for aged look
    P.append(f'''<radialGradient id="vignette" cx="50%" cy="48%" r="52%">
    <stop offset="0%" stop-color="#f5f0e6" stop-opacity="0"/>
    <stop offset="55%" stop-color="#f5f0e6" stop-opacity="0"/>
    <stop offset="80%" stop-color="#c8b890" stop-opacity="0.12"/>
    <stop offset="92%" stop-color="#b0986a" stop-opacity="{0.20 + mat * 0.30:.3f}"/>
    <stop offset="100%" stop-color="#8a7850" stop-opacity="{0.28 + mat * 0.32:.3f}"/>
  </radialGradient>''')
    # Sky gradient — pale blue at top fading to parchment
    P.append(make_linear_gradient('skyGrad', '0', '0', '0', '1',
        [('0%', '#dce8f0', 0.6), ('30%', '#eef3ee', 0.3), ('55%', '#f5f0e6', 0.0)]))
    # Bloom center glow — white hot-spot overlay
    P.append(make_radial_gradient('petalGlow', '50%', '60%', '70%',
        [('0%', '#ffffff', 0.45), ('40%', '#ffffff', 0.15), ('100%', '#ffffff', 0.0)]))
    # Atmospheric light from upper-left
    P.append(make_radial_gradient('lightRay', '12%', '-2%', '90%',
        [('0%', '#fffbe8', mat * 0.18), ('40%', '#fff8e0', mat * 0.07), ('100%', '#f5f0e6', 0.0)]))
    # Grass — multiple blade types, seed heads, varied greens
    P.append('''<pattern id="grass" width="18" height="10" patternUnits="userSpaceOnUse">
    <line x1="2" y1="10" x2="1" y2="2" stroke="#6a8a4a" stroke-width="0.5" opacity="0.4"/>
    <line x1="4" y1="10" x2="5" y2="3" stroke="#7a9a5a" stroke-width="0.5" opacity="0.38"/>
    <path d="M7,10 Q6,5 8,1" fill="none" stroke="#5a7a3a" stroke-width="0.45" opacity="0.35"/>
    <line x1="10" y1="10" x2="9" y2="2" stroke="#8aaa6a" stroke-width="0.5" opacity="0.36"/>
    <path d="M13,10 Q14,6 12,1" fill="none" stroke="#6a8a4a" stroke-width="0.45" opacity="0.34"/>
    <circle cx="12" cy="1" r="0.6" fill="#a09a60" opacity="0.3"/>
    <line x1="16" y1="10" x2="15" y2="4" stroke="#7a8a5a" stroke-width="0.45" opacity="0.32"/>
  </pattern>''')
    # Soil layers — rich earth tones with organic texture
    P.append('''<pattern id="soil1" width="24" height="8" patternUnits="userSpaceOnUse">
    <rect width="24" height="8" fill="#c0a070"/>
    <circle cx="5" cy="3" r="1.1" fill="#a08050" opacity="0.45"/>
    <circle cx="16" cy="5" r="0.8" fill="#907040" opacity="0.4"/>
    <circle cx="20" cy="2" r="0.5" fill="#b09860" opacity="0.3"/>
    <path d="M0,6 Q6,5 12,6.5 Q18,7 24,6" fill="none" stroke="#a08858" stroke-width="0.4" opacity="0.25"/>
  </pattern>''')
    P.append('''<pattern id="soil2" width="20" height="7" patternUnits="userSpaceOnUse">
    <rect width="20" height="7" fill="#a88860"/>
    <circle cx="4" cy="3" r="1.1" fill="#988050" opacity="0.3"/>
    <circle cx="14" cy="5" r="0.7" fill="#907848" opacity="0.25"/>
    <path d="M0,4 C5,3 10,5 20,4" fill="none" stroke="#9a8858" stroke-width="0.25" opacity="0.15"/>
  </pattern>''')
    P.append('''<pattern id="soil3" width="16" height="6" patternUnits="userSpaceOnUse">
    <rect width="16" height="6" fill="#907850"/>
    <circle cx="8" cy="3" r="0.5" fill="#807040" opacity="0.2"/>
    <path d="M0,2 Q4,3 8,2 Q12,1 16,2" fill="none" stroke="#806840" stroke-width="0.2" opacity="0.12"/>
  </pattern>''')
    P.append('</defs>')


    # ── Background (aged parchment with canvas texture) ──────────
    P.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#f0e8d8" filter="url(#paper)"/>')
    # Canvas texture overlay — subtle woven linen feel
    P.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#e8e0d0" filter="url(#canvas)" opacity="0.18"/>')
    # Sky gradient — pale blue wash at top
    P.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#skyGrad)"/>')
    # Atmospheric light wash from upper-left
    P.append(f'<rect x="0" y="0" width="{WIDTH}" height="{GROUND_Y:.0f}" fill="url(#lightRay)"/>')
    # Water stain marks — large, very faint irregular patches
    for _ in range(max(2, int(mat * 7))):
        wcx = rng.uniform(80, WIDTH - 80)
        wcy = rng.uniform(80, HEIGHT - 80)
        wrx = rng.uniform(40, 100)
        wry = rng.uniform(30, 80)
        P.append(f'<ellipse cx="{wcx:.0f}" cy="{wcy:.0f}" rx="{wrx:.0f}" ry="{wry:.0f}" '
                 f'fill="#d8c8a0" opacity="{rng.uniform(0.04,0.09):.3f}" '
                 f'transform="rotate({rng.uniform(-20,20):.0f},{wcx:.0f},{wcy:.0f})"/>')
    # Foxing spots — varied sizes and warm tones
    fox_colors = ["#d0b888", "#c8b090", "#ccb894", "#c0a880"]
    for _ in range(max(8, int(mat * 45))):
        P.append(f'<circle cx="{rng.uniform(20,WIDTH-20):.0f}" cy="{rng.uniform(20,HEIGHT-20):.0f}" '
                 f'r="{rng.uniform(1.5,8):.1f}" fill="{rng.choice(fox_colors)}" '
                 f'opacity="{rng.uniform(0.04,0.12):.3f}"/>')
    # Vignette overlay — subtle edge darkening
    P.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#vignette)"/>')

    # ── Atmospheric layers (morning mist + light rays) ─────────
    # Morning mist: 3-4 blurred radial gradient ellipses at ground level
    atmo_rng = np.random.default_rng(base_seed ^ 0xF0F0F0F0)
    n_mist = atmo_rng.integers(3, 5)
    for mi_atm in range(n_mist):
        mist_id = f"mist{mi_atm}"
        mist_cx = atmo_rng.uniform(80, WIDTH - 80)
        mist_cy = GROUND_Y + atmo_rng.uniform(-30, 10)
        mist_rx = atmo_rng.uniform(80, 180)
        mist_ry = atmo_rng.uniform(20, 50)
        mist_op = atmo_rng.uniform(0.04, 0.08)
        mist_grad = make_radial_gradient(mist_id, '50%', '50%', '60%',
            [('0%', '#f0f0f0', mist_op), ('50%', '#e8e8e8', mist_op * 0.5), ('100%', '#f5f0e6', 0.0)])
        P.append(f'<defs>{mist_grad}</defs>')
        P.append(f'<ellipse cx="{mist_cx:.0f}" cy="{mist_cy:.0f}" rx="{mist_rx:.0f}" ry="{mist_ry:.0f}" '
                 f'fill="url(#{mist_id})"/>')

    # Light rays: 2-3 diagonal linear gradient bands from upper-left
    n_rays = atmo_rng.integers(2, 4)
    for ray_i in range(n_rays):
        ray_id = f"lightray{ray_i}"
        # Diagonal band from upper-left toward lower-right
        ray_x = atmo_rng.uniform(50, WIDTH * 0.5)
        ray_y = atmo_rng.uniform(20, GROUND_Y * 0.4)
        ray_w = atmo_rng.uniform(40, 100)
        ray_h = atmo_rng.uniform(200, 500)
        ray_op = 0.03
        ray_rot = atmo_rng.uniform(20, 45)
        ray_grad = make_linear_gradient(ray_id, '0', '0', '1', '1',
            [('0%', '#fffbe8', ray_op), ('40%', '#fff8e0', ray_op * 0.6), ('100%', '#f5f0e6', 0.0)])
        P.append(f'<defs>{ray_grad}</defs>')
        P.append(f'<rect x="{ray_x:.0f}" y="{ray_y:.0f}" width="{ray_w:.0f}" height="{ray_h:.0f}" '
                 f'fill="url(#{ray_id})" transform="rotate({ray_rot:.0f},{ray_x:.0f},{ray_y:.0f})"/>')

    # ── Issue-driven weather ──────────────────────────────────────
    issue_stats = metrics.get("issue_stats", {})
    open_issues_count = issue_stats.get("open_count", 0) if isinstance(issue_stats, dict) else 0
    closed_issues_count = issue_stats.get("closed_count", 0) if isinstance(issue_stats, dict) else 0

    if open_issues_count == 0 and closed_issues_count > 10:
        # Clear skies: sunbeams through canopy
        for sb_i in range(3):
            sx = 150 + sb_i * 250 + rng.uniform(-40, 40)
            P.append(
                f'<line x1="{sx:.0f}" y1="0" x2="{sx + 60:.0f}" y2="{GROUND_Y:.0f}" '
                f'stroke="{oklch(0.95, 0.05, 80)}" stroke-width="12" '
                f'opacity="0.08" stroke-linecap="round"/>'
            )
    elif open_issues_count > 20:
        # Storm clouds
        for ci in range(min(4, open_issues_count // 15)):
            cx = 100 + ci * 180 + rng.uniform(-30, 30)
            cy = 30 + rng.uniform(0, 20)
            P.append(
                f'<ellipse cx="{cx:.0f}" cy="{cy:.0f}" rx="{rng.uniform(60, 100):.0f}" '
                f'ry="{rng.uniform(20, 35):.0f}" fill="{oklch(0.55, 0.03, 240)}" opacity="0.15"/>'
            )
        # Rain drops
        if open_issues_count > 40:
            for _ in range(min(20, open_issues_count // 3)):
                rx = rng.uniform(30, WIDTH - 30)
                ry = rng.uniform(50, GROUND_Y - 20)
                P.append(
                    f'<line x1="{rx:.0f}" y1="{ry:.0f}" x2="{rx - 2:.0f}" y2="{ry + 8:.0f}" '
                    f'stroke="{oklch(0.7, 0.08, 220)}" stroke-width="0.8" opacity="0.2"/>'
                )

    # ── Underground strata ────────────────────────────────────────
    max((r.get("age_months", 6) for r in repos), default=12)
    n_strata = 1 + int(mat * 3)
    ground_pts = [(gx_i, ground_y_at(gx_i)) for gx_i in range(0, WIDTH + 5, 5)]
    ground_path = f"M{ground_pts[0][0]},{ground_pts[0][1]:.1f}" + "".join(
        f" L{x:.1f},{y:.1f}" for x, y in ground_pts[1:]
    )
    soil_fills = ["url(#soil3)", "url(#soil2)", "url(#soil1)"]
    for si in range(min(n_strata, 3)):
        layer_pts = [(x, y + 15 + si * 30) for x, y in ground_pts]
        lp = f"M{layer_pts[0][0]},{layer_pts[0][1]:.1f}" + "".join(
            f" L{x:.1f},{y:.1f}" for x, y in layer_pts[1:]
        )
        lp += f" L{WIDTH},{HEIGHT} L0,{HEIGHT} Z"
        P.append(f'<path d="{lp}" fill="{soil_fills[si]}" opacity="0.65"/>')

    # Tiny soil creatures — beetles and earthworm segments
    for _ in range(int(mat * 6)):
        scx = rng.uniform(50, WIDTH - 50)
        scy = rng.uniform(GROUND_Y + 12, min(HEIGHT - 30, GROUND_Y + n_strata * 30))
        creature = rng.choice(["beetle", "worm_seg"])
        if creature == "beetle":
            # Tiny beetle silhouette
            P.append(f'<ellipse cx="{scx:.0f}" cy="{scy:.0f}" rx="2" ry="1.5" '
                     f'fill="#4a3a20" opacity="0.08"/>')
            P.append(f'<line x1="{scx - 2:.0f}" y1="{scy:.0f}" x2="{scx + 2:.0f}" y2="{scy:.0f}" '
                     f'stroke="#4a3a20" stroke-width="0.2" opacity="0.06"/>')
        else:
            # Earthworm segment — small curved pink-brown
            rng.uniform(-0.5, 0.5)
            P.append(f'<path d="M{scx:.0f},{scy:.0f} Q{scx + 6:.0f},{scy + 3:.0f} {scx + 12:.0f},{scy + 1:.0f}" '
                     f'fill="none" stroke="#b0887a" stroke-width="1" opacity="0.06" stroke-linecap="round"/>')
    # Worm trails — sinuous paths between strata
    for _ in range(int(mat * 7)):
        wx = rng.uniform(40, WIDTH - 40)
        wy = rng.uniform(GROUND_Y + 15, min(HEIGHT - 40, GROUND_Y + n_strata * 30))
        wd = f"M{wx:.0f},{wy:.0f}"
        for step in range(8):
            wx += rng.uniform(6, 14) * rng.choice([-1, 1])
            wy += rng.uniform(1, 5)
            wd += f" L{wx:.0f},{wy:.0f}"
        P.append(f'<path d="{wd}" fill="none" stroke="#a89870" stroke-width="0.4" '
                 f'opacity="0.08" stroke-linecap="round"/>')
    # Tiny fossils (spiral ammonites) in deeper strata
    if mat > 0.6:
        for _ in range(int((mat - 0.6) * 8)):
            fx_f = rng.uniform(60, WIDTH - 60)
            fy_f = rng.uniform(GROUND_Y + 40, min(HEIGHT - 40, GROUND_Y + n_strata * 30))
            fr_f = rng.uniform(2, 5)
            # Spiral shell fossil
            foss_d = f"M{fx_f + fr_f:.1f},{fy_f:.1f}"
            for ft in range(20):
                fa_f = ft * 0.5
                fr_cur = fr_f * (1 - ft * 0.04)
                if fr_cur < 0.3:
                    break
                foss_d += f" L{fx_f + fr_cur * math.cos(fa_f):.1f},{fy_f + fr_cur * math.sin(fa_f):.1f}"
            P.append(f'<path d="{foss_d}" fill="none" stroke="#c0b090" stroke-width="0.3" opacity="0.06"/>')
            P.append(f'<circle cx="{fx_f:.1f}" cy="{fy_f:.1f}" r="{fr_f:.1f}" fill="none" '
                     f'stroke="#b8a880" stroke-width="0.25" opacity="0.05"/>')
    # Pebbles with highlights
    pebble_colors = ["#a09070", "#b0a080", "#c0b090", "#a8987a", "#b8a888"]
    for _ in range(2 + int(mat * 10)):
        px = rng.uniform(30, WIDTH - 30)
        py = rng.uniform(GROUND_Y + 10, min(HEIGHT - 20, GROUND_Y + n_strata * 30 + 30))
        prx = rng.uniform(1.5, 4)
        pry = rng.uniform(1, 2.8)
        prot = rng.uniform(-20, 20)
        pc = rng.choice(pebble_colors)
        P.append(f'<ellipse cx="{px:.0f}" cy="{py:.0f}" rx="{prx:.1f}" ry="{pry:.1f}" '
                 f'fill="{pc}" opacity="{rng.uniform(0.12,0.25):.2f}" '
                 f'transform="rotate({prot:.0f},{px:.0f},{py:.0f})"/>')
        # Tiny highlight on each pebble
        P.append(f'<ellipse cx="{px - prx * 0.2:.1f}" cy="{py - pry * 0.3:.1f}" '
                 f'rx="{prx * 0.3:.1f}" ry="{pry * 0.25:.1f}" fill="#f0e8d8" opacity="0.06" '
                 f'transform="rotate({prot:.0f},{px:.0f},{py:.0f})"/>')

    # ── Roots ─────────────────────────────────────────────────────
    root_colors = [oklch(0.42, 0.06, 35), oklch(0.40, 0.07, 30), oklch(0.44, 0.05, 40)]
    P.append('<g opacity="0.4">')
    for ri_r, (rx1, ry1, rx2, ry2, rsw, when) in enumerate(roots):
        rc = root_colors[ri_r % len(root_colors)]
        mx = (rx1 + rx2) / 2 + rng.uniform(-1.5, 1.5)
        my = (ry1 + ry2) / 2 + rng.uniform(-1.5, 1.5)
        P.append(f'<path d="M{rx1:.1f},{ry1:.1f} Q{mx:.1f},{my:.1f} {rx2:.1f},{ry2:.1f}" '
                 f'fill="none" stroke="{rc}" stroke-width="{rsw:.1f}" {_timeline_style(when, 0.4)} stroke-linecap="round"/>')
        # Root hairs at fine tips
        if rsw < 0.5 and rng.random() < 0.3:
            for _ in range(rng.integers(2, 5)):
                ha = rng.uniform(0, 2 * math.pi)
                hl = rng.uniform(1.5, 4)
                P.append(f'<line x1="{rx2:.1f}" y1="{ry2:.1f}" '
                         f'x2="{rx2 + hl * math.cos(ha):.1f}" y2="{ry2 + hl * math.sin(ha):.1f}" '
                         f'stroke="{rc}" stroke-width="0.15" {_timeline_style(when, 0.3)}/>')
    P.append('</g>')

    # Mycorrhizal network — dashed threads with nutrient exchange nodes
    if len(repos) > 1 and forks > 0:
        P.append('<g opacity="0.12">')
        myco_nodes = []
        myco_count = min(15, forks)
        for my_i in range(myco_count):
            mx1 = rng.uniform(60, WIDTH - 60)
            my1 = rng.uniform(GROUND_Y + 20, GROUND_Y + 70)
            mx2 = mx1 + rng.uniform(-90, 90)
            my2 = my1 + rng.uniform(-15, 15)
            mid_x = (mx1 + mx2) / 2
            mid_y = my1 + rng.uniform(8, 22)
            my_when = _date_for_activity_fraction((my_i + 1) / (myco_count + 1))
            P.append(f'<path d="M{mx1:.0f},{my1:.0f} Q{mid_x:.0f},{mid_y:.0f} {mx2:.0f},{my2:.0f}" '
                     f'fill="none" stroke="#a09060" stroke-width="0.5" stroke-dasharray="2 3" '
                     f'{_timeline_style(my_when, 0.25, delay_offset_frac=-0.02, duration_scale=1.25, ease="linear")}/>')
            myco_nodes.append((mid_x, mid_y, my_when))
        # Nutrient exchange nodes (tiny circles at junctions)
        for nx, ny, n_when in myco_nodes[:8]:
            P.append(f'<circle cx="{nx:.0f}" cy="{ny:.0f}" r="1.2" fill="#b0a060" '
                     f'{_timeline_style(n_when, 0.5, delay_offset_frac=0.01, duration_scale=0.8)}/>')
        P.append('</g>')

    # ── Ground surface ────────────────────────────────────────────
    P.append(f'<path d="{ground_path} L{WIDTH},{GROUND_Y+15} L0,{GROUND_Y+15} Z" fill="url(#grass)" opacity="0.8"/>')
    # Main ground line — warm earth tone, thicker for visibility
    P.append(f'<path d="{ground_path}" fill="none" stroke="#6a5a2a" stroke-width="2.0" opacity="0.6"/>')
    # Secondary ground line — lighter, offset slightly below for depth
    sub_ground = f"M{ground_pts[0][0]},{ground_pts[0][1]+1.5:.1f}" + "".join(
        f" L{x:.1f},{y+1.5:.1f}" for x, y in ground_pts[1:]
    )
    P.append(f'<path d="{sub_ground}" fill="none" stroke="#8a7a4a" stroke-width="0.7" opacity="0.35"/>')

    # Branch density map for ground cover enhancement
    bd = defaultdict(int)
    for x1, y1, x2, y2, *_ in all_segs:
        bd[(int((x1 + x2) / 2 / 30), int((y1 + y2) / 2 / 30))] += 1
    max_bd = max(bd.values()) if bd else 1

    # Ground cover (enhanced with fern frondlets, moss patches, clover)
    for _ in range(40 + int(mat * 120)):
        gcx = rng.uniform(20, WIDTH - 20)
        gcy = ground_y_at(gcx) + rng.uniform(-3, 3)
        r_val = rng.random()
        if r_val < 0.4:
            # Grass tufts
            for _ in range(rng.integers(3, 7)):
                ga = -math.pi / 2 + rng.uniform(-0.5, 0.5)
                gl = rng.uniform(4, 12)
                P.append(f'<line x1="{gcx:.0f}" y1="{gcy:.0f}" '
                         f'x2="{gcx+gl*math.cos(ga):.0f}" y2="{gcy+gl*math.sin(ga):.0f}" '
                         f'stroke="#6a8a4a" stroke-width="0.5" opacity="0.35"/>')
        elif r_val < 0.55:
            # Stones
            P.append(f'<circle cx="{gcx:.0f}" cy="{gcy:.0f}" r="{rng.uniform(0.8,2.2):.1f}" fill="#a09070" opacity="0.3"/>')
        elif r_val < 0.7 and mat > 0.25:
            # Small fern frondlets at ground level (where branch density is high)
            grid_key = (int(gcx / 30), int(gcy / 30))
            local_density = bd.get(grid_key, 0) / max_bd if max_bd > 0 else 0
            if local_density > 0.2:
                frond_a = -math.pi / 2 + rng.uniform(-0.6, 0.6)
                frond_len = rng.uniform(4, 10)
                cx_f, cy_f = gcx, gcy
                for fs in range(4):
                    t = fs / 4.0
                    fa = frond_a + t * 0.3
                    fsl = frond_len / 4
                    nx_f = cx_f + fsl * math.cos(fa)
                    ny_f = cy_f + fsl * math.sin(fa)
                    P.append(f'<line x1="{cx_f:.1f}" y1="{cy_f:.1f}" x2="{nx_f:.1f}" y2="{ny_f:.1f}" '
                             f'stroke="#6a9a4a" stroke-width="0.3" opacity="0.2"/>')
                    if fs > 0:
                        for side in [-1, 1]:
                            pa = fa + side * 1.0
                            pl = fsl * 0.5 * (1 - t)
                            P.append(f'<line x1="{nx_f:.1f}" y1="{ny_f:.1f}" '
                                     f'x2="{nx_f + pl * math.cos(pa):.1f}" y2="{ny_f + pl * math.sin(pa):.1f}" '
                                     f'stroke="#7aaa5a" stroke-width="0.2" opacity="0.18"/>')
                    cx_f, cy_f = nx_f, ny_f
        elif r_val < 0.85 and mat > 0.4:
            # Moss patches: clusters of tiny dots near plant bases
            near_base = any(abs(gcx - bx) < 30 for bx, _ in plant_bases)
            if near_base:
                n_dots = rng.integers(4, 9)
                for _ in range(n_dots):
                    dx = gcx + rng.uniform(-4, 4)
                    dy = gcy + rng.uniform(-2, 2)
                    P.append(f'<circle cx="{dx:.1f}" cy="{dy:.1f}" r="{rng.uniform(0.3, 0.8):.1f}" '
                             f'fill="#5a8a3a" opacity="{rng.uniform(0.12, 0.25):.2f}"/>')
        elif r_val < 0.90 and mat > 0.4:
            # Clover: 3-circle trefoil
            clover_r = rng.uniform(1.2, 2.5)
            clover_c = "#5a9a4a"
            for ci in range(3):
                ca = ci * 2 * math.pi / 3 - math.pi / 2
                ccx = gcx + clover_r * 0.5 * math.cos(ca)
                ccy = gcy + clover_r * 0.5 * math.sin(ca)
                P.append(f'<circle cx="{ccx:.1f}" cy="{ccy:.1f}" r="{clover_r * 0.45:.1f}" '
                         f'fill="{clover_c}" opacity="0.2"/>')
            # Tiny stem
            P.append(f'<line x1="{gcx:.1f}" y1="{gcy:.1f}" x2="{gcx:.1f}" y2="{gcy + clover_r * 1.2:.1f}" '
                     f'stroke="#4a7a3a" stroke-width="0.3" opacity="0.2"/>')
        elif r_val < 0.95 and mat > 0.55:
            # Tiny wildflower: stem + 4-5 petal rosette
            wf_h = rng.uniform(4, 9)
            wf_hue = rng.choice([0, 45, 270, 320, 55])
            wf_c = oklch(0.62, 0.22, wf_hue)
            oklch(0.50, 0.16, wf_hue)
            # Stem
            P.append(f'<line x1="{gcx:.1f}" y1="{gcy:.1f}" x2="{gcx:.1f}" y2="{gcy - wf_h:.1f}" '
                     f'stroke="#6a8a4a" stroke-width="0.3" opacity="0.2"/>')
            # Petals
            n_wp = rng.integers(4, 6)
            pr = wf_h * 0.15
            for wp in range(n_wp):
                wa = wp * 2 * math.pi / n_wp
                px = gcx + pr * math.cos(wa)
                py = gcy - wf_h + pr * math.sin(wa)
                P.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{pr * 0.6:.1f}" '
                         f'fill="{wf_c}" opacity="0.2"/>')
            # Center dot
            P.append(f'<circle cx="{gcx:.1f}" cy="{gcy - wf_h:.1f}" r="{pr * 0.3:.1f}" '
                     f'fill="#e0c850" opacity="0.25"/>')
        elif mat > 0.7:
            # Snail: spiral shell + body
            sn_r = rng.uniform(2, 4)
            sn_c = oklch(0.58, 0.06, 35)
            sn_dark = oklch(0.42, 0.08, 30)
            # Body — soft slug shape
            P.append(f'<ellipse cx="{gcx + sn_r * 0.6:.1f}" cy="{gcy:.1f}" '
                     f'rx="{sn_r * 0.9:.1f}" ry="{sn_r * 0.3:.1f}" '
                     f'fill="{oklch(0.55, 0.04, 45)}" opacity="0.2"/>')
            # Shell spiral (3/4 turn)
            shell_pts = []
            for st in range(12):
                sa = st * 0.5 + math.pi * 0.5
                sr = sn_r * (1 - st * 0.07)
                shell_pts.append((gcx + sr * math.cos(sa), gcy - sn_r * 0.15 + sr * 0.6 * math.sin(sa)))
            if len(shell_pts) > 2:
                shell_d = f"M{shell_pts[0][0]:.1f},{shell_pts[0][1]:.1f}"
                for sp in shell_pts[1:]:
                    shell_d += f" L{sp[0]:.1f},{sp[1]:.1f}"
                P.append(f'<path d="{shell_d}" fill="none" stroke="{sn_dark}" '
                         f'stroke-width="0.4" opacity="0.18"/>')
            P.append(f'<ellipse cx="{gcx:.1f}" cy="{gcy - sn_r * 0.1:.1f}" '
                     f'rx="{sn_r * 0.55:.1f}" ry="{sn_r * 0.45:.1f}" '
                     f'fill="{sn_c}" opacity="0.2" stroke="{sn_dark}" stroke-width="0.2"/>')
            # Tentacles
            P.append(f'<line x1="{gcx + sn_r * 0.8:.1f}" y1="{gcy - sn_r * 0.15:.1f}" '
                     f'x2="{gcx + sn_r * 1.2:.1f}" y2="{gcy - sn_r * 0.5:.1f}" '
                     f'stroke="{sn_dark}" stroke-width="0.2" opacity="0.15"/>')
            P.append(f'<line x1="{gcx + sn_r * 0.9:.1f}" y1="{gcy - sn_r * 0.15:.1f}" '
                     f'x2="{gcx + sn_r * 1.3:.1f}" y2="{gcy - sn_r * 0.4:.1f}" '
                     f'stroke="{sn_dark}" stroke-width="0.2" opacity="0.15"/>')

    # ── Mushrooms (with gills, stem detail, ground shadow) ───────
    for mx, my, ms, mh in mushrooms_list:
        # Ground shadow
        P.append(f'<ellipse cx="{mx:.1f}" cy="{my + 1:.1f}" rx="{ms * 0.5:.1f}" ry="{ms * 0.15:.1f}" '
                 f'fill="#6a5a3a" opacity="0.06"/>')
        # Stem with subtle gradient feel
        stem_c = oklch(0.72, 0.04, 45)
        stem_dark = oklch(0.62, 0.05, 40)
        P.append(f'<rect x="{mx - ms * 0.12:.1f}" y="{my - ms:.1f}" width="{ms * 0.24:.1f}" '
                 f'height="{ms:.1f}" fill="{stem_c}" opacity="0.7" rx="1"/>')
        # Stem texture lines
        for si_m in range(2):
            sx_off = mx - ms * 0.04 + si_m * ms * 0.06
            P.append(f'<line x1="{sx_off:.1f}" y1="{my - ms * 0.9:.1f}" x2="{sx_off:.1f}" y2="{my:.1f}" '
                     f'stroke="{stem_dark}" stroke-width="0.15" opacity="0.15"/>')
        # Cap — dome shape
        cap_c = oklch(0.55, 0.12, mh)
        cap_dark = oklch(0.45, 0.10, mh)
        cap_top = my - ms
        P.append(f'<ellipse cx="{mx:.1f}" cy="{cap_top:.1f}" rx="{ms * 0.6:.1f}" ry="{ms * 0.4:.1f}" '
                 f'fill="{cap_c}" opacity="0.65" stroke="{cap_dark}" stroke-width="0.3"/>')
        # Gills — radial lines under cap
        n_gills = max(4, int(ms * 1.5))
        for gi in range(n_gills):
            gf = gi / n_gills
            gx = mx - ms * 0.45 + gf * ms * 0.9
            P.append(f'<line x1="{gx:.1f}" y1="{cap_top + ms * 0.25:.1f}" x2="{gx:.1f}" y2="{cap_top + ms * 0.38:.1f}" '
                     f'stroke="{cap_dark}" stroke-width="0.2" opacity="0.15"/>')
        # Cap spots
        for _ in range(rng.integers(2, 5)):
            P.append(f'<circle cx="{mx + rng.uniform(-ms * 0.3, ms * 0.3):.1f}" '
                     f'cy="{cap_top + rng.uniform(-ms * 0.2, ms * 0.08):.1f}" '
                     f'r="{rng.uniform(0.4, 1.3):.1f}" fill="#f0e8d0" opacity="0.45"/>')
        # Lichen/moss at mushroom base
        if mat > 0.4:
            n_lichen = rng.integers(2, 5)
            for _ in range(n_lichen):
                lx_m = mx + rng.uniform(-ms * 0.4, ms * 0.4)
                ly_m = my + rng.uniform(-1, 2)
                lr_m = rng.uniform(0.8, 2.0)
                P.append(f'<circle cx="{lx_m:.1f}" cy="{ly_m:.1f}" r="{lr_m:.1f}" '
                         f'fill="#8aaa6a" opacity="{rng.uniform(0.08, 0.15):.2f}"/>')
        # Mycelium threads radiating from base
        if mat > 0.55:
            for _ in range(rng.integers(1, 3)):
                ma_m = rng.uniform(-0.5, 0.5) + math.pi / 2
                ml_m = rng.uniform(4, 10)
                P.append(f'<path d="M{mx:.1f},{my:.1f} Q{mx + ml_m * 0.5 * math.cos(ma_m) + rng.uniform(-2, 2):.1f},'
                         f'{my + ml_m * 0.5 * math.sin(ma_m):.1f} '
                         f'{mx + ml_m * math.cos(ma_m):.1f},{my + ml_m * math.sin(ma_m):.1f}" '
                         f'fill="none" stroke="#d0c8a0" stroke-width="0.15" opacity="0.08"/>')

    # ── Atmospheric wash (faint watercolor sky suggestion, language-tinted) ─
    tint_l, tint_c, tint_h = lang_sky_tint
    for wash_i in range(int(mat * 6)) if mat >= 0.15 else ():
        awx = rng.uniform(60, WIDTH - 60)
        awy = rng.uniform(36, GROUND_Y - 80)
        awrx = rng.uniform(50, 120)
        awry = rng.uniform(20, 50)
        # Alternate between default washes and language-tinted washes
        if wash_i % 3 == 0 and dominant_lang is not None:
            wash_c = oklch(tint_l + rng.uniform(-0.03, 0.03), tint_c, tint_h + rng.uniform(-10, 10))
        else:
            wash_c = rng.choice(["#d0dce8", "#e0e8e8", "#d8e0e0", "#d8d8e4"])
        P.append(f'<ellipse cx="{awx:.0f}" cy="{awy:.0f}" rx="{awrx:.0f}" ry="{awry:.0f}" '
                 f'fill="{wash_c}" opacity="{rng.uniform(0.02, 0.04):.3f}" '
                 f'transform="rotate({rng.uniform(-10, 10):.0f},{awx:.0f},{awy:.0f})"/>')

    # ── Bird silhouettes (distant, high in sky) ──────────────────
    if mat > 0.35:
        n_birds = int((mat - 0.35) * 8)
        for _ in range(n_birds):
            bx_b = rng.uniform(60, WIDTH - 60)
            by_b = rng.uniform(30, GROUND_Y * 0.3)
            bsz = rng.uniform(2, 5)
            # Simple M-shape bird
            P.append(f'<path d="M{bx_b - bsz:.1f},{by_b:.1f} Q{bx_b - bsz * 0.4:.1f},{by_b - bsz * 0.6:.1f} '
                     f'{bx_b:.1f},{by_b:.1f} Q{bx_b + bsz * 0.4:.1f},{by_b - bsz * 0.6:.1f} '
                     f'{bx_b + bsz:.1f},{by_b:.1f}" '
                     f'fill="none" stroke="#6a5a4a" stroke-width="{0.3 + bsz * 0.05:.2f}" '
                     f'opacity="{rng.uniform(0.06, 0.12):.2f}" stroke-linecap="round"/>')

    # ── Plant shadow patches (stippled shadows on ground) ─────────
    # Sun from upper-left → shadows offset toward lower-right
    for bx_s, by_s in plant_bases:
        shadow_w = 20 + rng.uniform(0, 15)
        shadow_cx = bx_s + 5   # offset right (sun from left)
        shadow_cy = by_s + 2   # offset down (sun from above)
        n_stipple = max(30, min(50, int(30 + mat * 20)))
        for _ in range(n_stipple):
            # Distribute dots in elliptical region, biased toward lower-right
            angle_s = rng.uniform(0, 2 * math.pi)
            dist_s = rng.uniform(0, 1) ** 0.5  # sqrt for uniform area distribution
            sx_s = shadow_cx + dist_s * shadow_w * math.cos(angle_s) + rng.uniform(0, 3)
            sy_s = shadow_cy + dist_s * shadow_w * 0.2 * math.sin(angle_s) + rng.uniform(0, 2)
            sr_s = rng.uniform(0.3, 0.8)
            so_s = rng.uniform(0.05, 0.15)
            P.append(f'<circle cx="{sx_s:.1f}" cy="{sy_s:.1f}" r="{sr_s:.1f}" '
                     f'fill="#5a5030" opacity="{so_s:.3f}"/>')
    # Branch-cast shadows to break fence-line symmetry and add depth
    seg_shadow_budget = min(220, max(80, int(len(all_segs) * 0.35)))
    shadow_step = max(1, len(all_segs) // max(1, seg_shadow_budget))
    for si_shadow, (x1, y1, x2, y2, sw, _hue, depth, is_main, _bark_mat, when) in enumerate(all_segs[::shadow_step]):
        if depth > 2 and not is_main:
            continue
        if max(y1, y2) < GROUND_Y - 140:
            continue
        proj = 4 + sw * 1.8 + depth * 1.2
        skew = 1.5 + depth * 0.5
        sx1, sy1 = x1 + proj, y1 + skew
        sx2, sy2 = x2 + proj, y2 + skew
        op_base = 0.04 + min(0.12, sw * 0.015) * (1.0 - min(0.75, depth * 0.12))
        if si_shadow % 2 == 0:
            P.append(
                f'<path d="M{sx1:.1f},{sy1:.1f} Q{(sx1 + sx2) / 2 + 1.2:.1f},{(sy1 + sy2) / 2 + 1.0:.1f} {sx2:.1f},{sy2:.1f}" '
                f'fill="none" stroke="#5f5536" stroke-width="{max(0.35, sw * 0.85):.2f}" stroke-linecap="round" '
                f'{_timeline_style(when, op_base, delay_offset_frac=0.01, duration_scale=1.15, ease="linear")}/>'
            )

    # ── Above ground: ink filter group ────────────────────────────
    P.append('<g filter="url(#ink)">')

    # Cross-hatching — engraving-style with variable direction per cell
    elem_count = len(P)
    if mat >= 0.15:
        for (gx, gy_h), cnt in bd.items():
            if cnt < 3:
                continue
            df = cnt / max_bd * mat
            cx_h = gx * 30 + 15
            cy_h = gy_h * 30 + 15
            # Primary hatch direction varies by cell position
            hatch_angle = 0.4 + (gx * 0.3 + gy_h * 0.2) % 1.0
            cos_h = math.cos(hatch_angle)
            sin_h = math.sin(hatch_angle)
            n_lines = int(df * 6)
            for hi in range(n_lines):
                off = (hi - n_lines / 2) * 2.5
                x1_h = cx_h - 12 * cos_h + off * sin_h
                y1_h = cy_h - 12 * sin_h - off * cos_h
                x2_h = cx_h + 12 * cos_h + off * sin_h
                y2_h = cy_h + 12 * sin_h - off * cos_h
                P.append(f'<line x1="{x1_h:.1f}" y1="{y1_h:.1f}" x2="{x2_h:.1f}" y2="{y2_h:.1f}" '
                         f'stroke="#9a9070" stroke-width="0.25" opacity="{df * 0.13:.3f}"/>')
            # Cross-hatch (perpendicular) for dense areas
            if df > 0.45:
                cos_c = math.cos(hatch_angle + math.pi / 2)
                sin_c = math.sin(hatch_angle + math.pi / 2)
                for hi in range(int(df * 4)):
                    off = (hi - int(df * 5) / 2) * 3
                    x1_c = cx_h - 10 * cos_c + off * sin_c
                    y1_c = cy_h - 10 * sin_c - off * cos_c
                    x2_c = cx_h + 10 * cos_c + off * sin_c
                    y2_c = cy_h + 10 * sin_c - off * cos_c
                    P.append(f'<line x1="{x1_c:.1f}" y1="{y1_c:.1f}" x2="{x2_c:.1f}" y2="{y2_c:.1f}" '
                             f'stroke="#9a9070" stroke-width="0.2" opacity="{df * 0.08:.3f}"/>')

    # Stipple from monthly activity
    max_m = max(monthly.values()) if monthly else 100
    for m_idx, (mkey, count) in enumerate(monthly.items()):
        intensity = count / max(1, max_m)
        mi_val = int(mkey) - 1 if mkey.isdigit() else 0
        angle = -math.pi / 2 + mi_val * 2 * math.pi / 12
        cx_m = CX + 200 * math.cos(angle)
        cy_m = min(CY - 80 + 180 * math.sin(angle), GROUND_Y - 30)
        m_when = _month_key_date(str(mkey), m_idx)
        for _ in range(int(intensity * 30)):
            dx = cx_m + rng.normal(0, 50)
            dy = cy_m + rng.normal(0, 50)
            if dy > GROUND_Y - 5:
                continue
            P.append(f'<circle cx="{dx:.0f}" cy="{dy:.0f}" r="{rng.uniform(0.15,0.5):.1f}" '
                     f'fill="#c8bfa8" {_timeline_style(m_when, 0.06 + intensity * 0.12)}/>')

    # PASS 1: Main stems with rich bark texture
    for x1, y1, x2, y2, sw, hue, depth, is_main, bark_mat, when in all_segs:
        if not is_main:
            continue
        # Main stroke — warm dark brown
        color = oklch(0.28, 0.06, hue)
        color_light = oklch(0.35, 0.05, hue)
        mx = (x1 + x2) / 2 + rng.uniform(-1, 1)
        my = (y1 + y2) / 2 + rng.uniform(-1, 1)
        if sw > 3:
            # Shadow layer (darker, full width)
            P.append(f'<path d="M{x1:.1f},{y1:.1f} Q{mx:.1f},{my:.1f} {x2:.1f},{y2:.1f}" '
                     f'fill="none" stroke="{oklch(0.22, 0.07, hue)}" stroke-width="{sw:.1f}" '
                     f'{_timeline_style(when, 0.9)} stroke-linecap="round"/>')
            # Core layer (current color, narrower)
            P.append(f'<path d="M{x1:.1f},{y1:.1f} Q{mx:.1f},{my:.1f} {x2:.1f},{y2:.1f}" '
                     f'fill="none" stroke="{color}" stroke-width="{sw*0.55:.1f}" '
                     f'{_timeline_style(when, 0.55)} stroke-linecap="round"/>')
        else:
            P.append(f'<path d="M{x1:.1f},{y1:.1f} Q{mx:.1f},{my:.1f} {x2:.1f},{y2:.1f}" '
                     f'fill="none" stroke="{color}" stroke-width="{sw:.1f}" '
                     f'{_timeline_style(when, 0.85)} stroke-linecap="round"/>')
        # Highlight edge — subtle lighter line on one side
        if sw > 2.5:
            perp = math.atan2(y2 - y1, x2 - x1) + math.pi / 2
            hoff = sw * 0.3
            P.append(f'<path d="M{x1 + hoff * math.cos(perp):.1f},{y1 + hoff * math.sin(perp):.1f} '
                     f'Q{mx + hoff * math.cos(perp):.1f},{my + hoff * math.sin(perp):.1f} '
                     f'{x2 + hoff * math.cos(perp):.1f},{y2 + hoff * math.sin(perp):.1f}" '
                     f'fill="none" stroke="{color_light}" stroke-width="0.3" {_timeline_style(when, 0.25)}/>')
        # Bark texture — longitudinal grain lines, density driven by bark_mat
        # bark_mat: 0.0 = young (smooth bark) → 1.0 = old (deeply furrowed)
        bark_thresh = max(2.5, 3.5 - bark_mat * 1.0)  # young trees need thicker stems for bark
        if sw > bark_thresh and mat > 0.3 and len(P) - elem_count < MAX_ELEMENTS:
            seg_len = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            if seg_len > 8:
                perp = math.atan2(y2 - y1, x2 - x1) + math.pi / 2
                bark_c = oklch(0.32 - bark_mat * 0.04, 0.04 + bark_mat * 0.02, hue)
                n_grain = min(6, max(1, int(sw * (0.5 + bark_mat * 0.5))))
                grain_opacity = 0.10 + bark_mat * 0.08
                for bi in range(n_grain):
                    off = (bi - n_grain / 2) * 0.7
                    jitter = 0.6 + bark_mat * 0.4  # older = more irregular
                    jx1, jy1 = rng.uniform(-jitter, jitter), rng.uniform(-jitter, jitter)
                    jx2, jy2 = rng.uniform(-jitter, jitter), rng.uniform(-jitter, jitter)
                    line_w = 0.15 + rng.uniform(0, 0.15) + bark_mat * 0.08
                    P.append(f'<line x1="{x1 + off * math.cos(perp) + jx1:.1f}" '
                             f'y1="{y1 + off * math.sin(perp) + jy1:.1f}" '
                             f'x2="{x2 + off * math.cos(perp) + jx2:.1f}" '
                             f'y2="{y2 + off * math.sin(perp) + jy2:.1f}" '
                             f'stroke="{bark_c}" stroke-width="{line_w:.2f}" '
                             f'{_timeline_style(when, grain_opacity)}/>')
                # Occasional knot mark — probability increases with bark maturity
                knot_prob = 0.04 + bark_mat * 0.08
                if seg_len > 15 and rng.random() < knot_prob and mat > 0.4:
                    kx = (x1 + x2) / 2 + rng.uniform(-2, 2)
                    ky = (y1 + y2) / 2 + rng.uniform(-2, 2)
                    kr = sw * rng.uniform(0.15, 0.3) * (0.8 + bark_mat * 0.4)
                    P.append(f'<circle cx="{kx:.1f}" cy="{ky:.1f}" r="{kr:.1f}" fill="none" '
                             f'stroke="{bark_c}" stroke-width="{0.25 + bark_mat * 0.15:.2f}" '
                             f'{_timeline_style(when, 0.10 + bark_mat * 0.06)}/>')
                    # Mature bark: add concentric ring inside knot
                    if bark_mat > 0.6 and kr > 1:
                        P.append(f'<circle cx="{kx:.1f}" cy="{ky:.1f}" r="{kr * 0.55:.1f}" fill="none" '
                                 f'stroke="{bark_c}" stroke-width="0.15" {_timeline_style(when, 0.06 + bark_mat * 0.04)}/>')

    # Water droplet trails on thick stems
    for x1, y1, x2, y2, sw, hue, depth, is_main, _bark_mat, when in all_segs:
        if is_main and sw > 3.5 and rng.random() < 0.04 and mat > 0.4 and len(P) - elem_count < MAX_ELEMENTS:
            seg_len = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            if seg_len > 12:
                # Small droplets trailing down stem
                trail_x = (x1 + x2) / 2 + rng.uniform(-sw * 0.3, sw * 0.3)
                trail_y = min(y1, y2)
                for di_t in range(rng.integers(2, 5)):
                    ty_t = trail_y + di_t * rng.uniform(3, 6)
                    if ty_t > max(y1, y2):
                        break
                    dr_t = 0.6 - di_t * 0.08
                    if dr_t > 0.2:
                        P.append(f'<circle cx="{trail_x + rng.uniform(-0.5, 0.5):.1f}" cy="{ty_t:.1f}" '
                                 f'r="{dr_t:.1f}" fill="url(#dewGrad)" {_timeline_style(when, 0.3)}/>')

    # PASS 2: Secondary branches
    for x1, y1, x2, y2, sw, hue, depth, is_main, _bark_mat, when in all_segs:
        if is_main:
            continue
        d_frac = depth / 6
        color = oklch(0.32 + d_frac * 0.12, 0.10 + d_frac * 0.04, hue)
        op = max(0.3, 0.80 - depth * 0.08)
        mx = (x1 + x2) / 2 + rng.uniform(-2, 2)
        my = (y1 + y2) / 2 + rng.uniform(-2, 2)
        P.append(f'<path d="M{x1:.1f},{y1:.1f} Q{mx:.1f},{my:.1f} {x2:.1f},{y2:.1f}" '
                 f'fill="none" stroke="{color}" stroke-width="{sw:.1f}" {_timeline_style(when, op)} stroke-linecap="round"/>')

    # PASS 3: Tendrils with leaf buds
    for pts in tendrils:
        if len(pts) < 3:
            continue
        pd = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
        for j in range(1, len(pts) - 1, 2):
            if j + 1 < len(pts):
                pd += f" Q{pts[j][0]:.1f},{pts[j][1]:.1f} {pts[j+1][0]:.1f},{pts[j+1][1]:.1f}"
        # Main tendril — tapered stroke
        P.append(f'<path d="{pd}" fill="none" stroke="#5a8a3a" stroke-width="0.5" '
                 f'opacity="0.35" stroke-linecap="round"/>')
        # Tiny leaf buds at alternating points along tendril
        for j in range(2, len(pts) - 1, 3):
            bx_t, by_t = pts[j]
            if j + 1 < len(pts):
                dx_t = pts[j + 1][0] - pts[j - 1][0]
                dy_t = pts[j + 1][1] - pts[j - 1][1]
                perp_a = math.atan2(dy_t, dx_t) + math.pi / 2
                bud_r = rng.uniform(1, 2)
                bud_x = bx_t + bud_r * math.cos(perp_a)
                bud_y = by_t + bud_r * math.sin(perp_a)
                P.append(f'<circle cx="{bud_x:.1f}" cy="{bud_y:.1f}" r="{bud_r * 0.4:.1f}" '
                         f'fill="#7aaa5a" opacity="0.25"/>')

    # PASS 4: Leaves with species-specific shapes (capped)
    def budget_ok():
        return len(P) - elem_count < MAX_ELEMENTS
    for leaf_tuple in leaves[:MAX_LEAVES]:
        if not budget_ok():
            break
        lx, ly, la, ls, lh, has_vein, leaf_shape, leaf_when = leaf_tuple
        if ls > 3.2 and budget_ok():
            shx = lx + 2.0 + math.cos(la) * 0.8
            shy = ly + 1.8 + math.sin(la) * 0.6
            stx = shx + ls * 0.82 * math.cos(la)
            sty = shy + ls * 0.82 * math.sin(la)
            sperp = la + math.pi / 2
            sbulge = ls * 0.22
            sc1x = (shx + stx) / 2 + sbulge * math.cos(sperp)
            sc1y = (shy + sty) / 2 + sbulge * math.sin(sperp)
            sc2x = (shx + stx) / 2 - sbulge * 0.85 * math.cos(sperp)
            sc2y = (shy + sty) / 2 - sbulge * 0.85 * math.sin(sperp)
            P.append(
                f'<path d="M{shx:.1f},{shy:.1f} Q{sc1x:.1f},{sc1y:.1f} {stx:.1f},{sty:.1f} '
                f'Q{sc2x:.1f},{sc2y:.1f} {shx:.1f},{shy:.1f}" fill="#574c33" '
                f'{_timeline_style(leaf_when, 0.07, delay_offset_frac=-0.015, duration_scale=1.2, ease="linear")}/>'
            )
        P.append(f'<g {_timeline_style(leaf_when, 1.0, delay_offset_frac=0.004 * math.sin(la), duration_scale=0.95)}>')
        _draw_leaf(P, lx, ly, la, ls, lh, has_vein, leaf_shape, rng, budget_ok, oklch)
        if has_vein and ls > 5 and budget_ok():
            tip_x = lx + ls * math.cos(la)
            tip_y = ly + ls * math.sin(la)
            P.append(
                f'<line x1="{lx:.1f}" y1="{ly:.1f}" x2="{tip_x:.1f}" y2="{tip_y:.1f}" '
                f'stroke="#f5efdf" stroke-width="0.16" '
                f'{_timeline_style(leaf_when, 0.16, delay_offset_frac=0.02, duration_scale=0.7)}/>'
            )
        P.append('</g>')

    # PASS 5: Buds with sepals
    for bx, by, bs, bh, when in buds:
        bud_rot = rng.uniform(-30, 30)
        bud_c = oklch(0.58, 0.18, bh)
        sepal_c = oklch(0.42, 0.14, (bh + 120) % 360)
        # Sepals — small protective leaves wrapping the bud
        for si_s in range(2):
            sa_s = bud_rot + (si_s - 0.5) * 40
        P.append(f'<ellipse cx="{bx:.1f}" cy="{by + bs * 0.3:.1f}" rx="{bs * 0.35:.1f}" ry="{bs * 0.6:.1f}" '
                 f'fill="{sepal_c}" {_timeline_style(when, 0.3)} '
                 f'transform="rotate({sa_s:.0f},{bx:.1f},{by:.1f})"/>')
        # Bud body
        P.append(f'<ellipse cx="{bx:.1f}" cy="{by:.1f}" rx="{bs * 0.4:.1f}" ry="{bs:.1f}" '
                 f'fill="{bud_c}" {_timeline_style(when, 0.5)} stroke="{oklch(0.45, 0.14, bh)}" stroke-width="0.2" '
                 f'transform="rotate({bud_rot:.0f},{bx:.1f},{by:.1f})"/>')

    # PASS 6: Multi-layer blooms with species-specific types (capped)
    for bloom_tuple in blooms[:MAX_BLOOMS]:
        if not budget_ok():
            break
        bx, by, bs, bh, n_petals, petal_layers, bloom_type, when = bloom_tuple
        P.append(
            f'<ellipse cx="{bx + 2.2:.1f}" cy="{by + bs * 0.58:.1f}" rx="{bs * 0.55:.1f}" ry="{max(1.2, bs * 0.18):.1f}" '
            f'fill="#61563a" {_timeline_style(when, 0.08, delay_offset_frac=-0.012, duration_scale=1.25, ease="linear")}/>'
        )
        P.append(f'<g {_timeline_style(when, 1.0, delay_offset_frac=0.008, duration_scale=0.9)}>')
        _draw_bloom(P, bx, by, bs, bh, n_petals, petal_layers, bloom_type, rng, budget_ok, oklch)
        # Bloom center glow overlay
        P.append(f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="{bs*0.6:.1f}" '
                 f'fill="url(#petalGlow)" {_timeline_style(when, 0.5, delay_offset_frac=0.025, duration_scale=0.75)}/>')
        P.append('</g>')

    # PASS 7: Berries with calyx and richer highlights
    for bi_idx, (bx, by, bs, bh, when) in enumerate(berries):
        if not budget_ok():
            break
        # Tiny stem + calyx (only on first 20 berries to save budget)
        if bi_idx < 20:
            P.append(f'<line x1="{bx:.1f}" y1="{by - bs:.1f}" x2="{bx:.1f}" y2="{by - bs * 1.5:.1f}" '
                     f'stroke="#6a5a3a" stroke-width="0.3" {_timeline_style(when, 0.35)}/>')
            for ci_b in range(3):
                ca_b = ci_b * 2 * math.pi / 3 - math.pi / 2
                P.append(f'<line x1="{bx:.1f}" y1="{by - bs:.1f}" '
                         f'x2="{bx + bs * 0.3 * math.cos(ca_b):.1f}" y2="{by - bs + bs * 0.3 * math.sin(ca_b):.1f}" '
                         f'stroke="#5a7a3a" stroke-width="0.2" {_timeline_style(when, 0.3)}/>')
        # Berry body
        P.append(f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="{bs:.1f}" fill="{oklch(0.42, 0.24, bh)}" '
                 f'{_timeline_style(when, 0.6)} stroke="{oklch(0.33, 0.18, bh)}" stroke-width="0.3"/>')
        # Highlight
        P.append(f'<circle cx="{bx - bs * 0.25:.1f}" cy="{by - bs * 0.25:.1f}" r="{bs * 0.28:.1f}" '
                 f'fill="#fff" {_timeline_style(when, 0.25)}/>')

    P.append('</g>')  # end ink filter

    # ── Spider webs (delicate, with dew beading) ─────────────────
    for wcx, wcy, wr, n_sp in webs:
        # Radial threads — thicker near hub
        for si_sp in range(n_sp):
            sa = si_sp * 2 * math.pi / n_sp
            ex = wcx + wr * math.cos(sa)
            ey = wcy + wr * math.sin(sa)
            P.append(f'<line x1="{wcx:.1f}" y1="{wcy:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" '
                     f'stroke="#c0b8a0" stroke-width="0.25" opacity="0.2"/>')
            # Dew drops along radial threads
            if rng.random() < 0.5:
                dt = rng.uniform(0.3, 0.8)
                ddx = wcx + (ex - wcx) * dt
                ddy = wcy + (ey - wcy) * dt
                P.append(f'<circle cx="{ddx:.1f}" cy="{ddy:.1f}" r="{rng.uniform(0.4, 1.0):.1f}" '
                         f'fill="url(#dewGrad)" opacity="0.4"/>')
        # Spiral capture threads — closer spacing near center
        for ring in range(3, int(wr), 3):
            ring_pts = []
            for s in range(n_sp + 1):
                angle = s * 2 * math.pi / n_sp
                # Slight sag between spokes
                sag = 0.8 if s % 2 == 0 else 1.0
                r_eff = ring * sag
                ring_pts.append(f"{wcx + r_eff * math.cos(angle):.1f},{wcy + r_eff * math.sin(angle):.1f}")
            rpts = " ".join(ring_pts)
            P.append(f'<polyline points="{rpts}" fill="none" stroke="#c8c0a8" '
                     f'stroke-width="0.15" opacity="{0.12 + 0.03 * (ring / wr):.2f}"/>')
        # Hub — tiny spiral at center
        P.append(f'<circle cx="{wcx:.1f}" cy="{wcy:.1f}" r="1.2" fill="none" '
                 f'stroke="#b8b098" stroke-width="0.3" opacity="0.2"/>')

    # ── Dew drops ─────────────────────────────────────────────────
    for dx, dy, ds in dew_drops:
        P.append(f'<circle cx="{dx:.1f}" cy="{dy:.1f}" r="{ds:.1f}" fill="url(#dewGrad)" filter="url(#dew)"/>')

    # ── Fireflies (star velocity driven) ─────────────────────────
    star_vel = metrics.get("star_velocity", {})
    star_rate = star_vel.get("recent_rate", 0) if isinstance(star_vel, dict) else 0
    n_fireflies = min(12, max(0, int(star_rate * 2)))
    if n_fireflies > 0:
        P.append('<g id="fireflies">')
        for fi in range(n_fireflies):
            fx = rng.uniform(60, WIDTH - 60)
            fy = rng.uniform(GROUND_Y - 200, GROUND_Y - 30)
            glow_r = 3 + star_rate * 0.3
            pulse_dur = rng.uniform(2.0, 4.0)
            delay = rng.uniform(0, 6)
            glow_color = oklch(0.85, 0.15, 85)
            if timeline_enabled:
                when = _date_for_activity_fraction(0.7 + fi * 0.02)
                P.append(
                    f'<circle cx="{fx:.0f}" cy="{fy:.0f}" r="{glow_r:.1f}" '
                    f'fill="{glow_color}" filter="url(#dew)" '
                    f'{_timeline_style(when, 0.6)}/>'
                )
            else:
                P.append(
                    f'<circle cx="{fx:.0f}" cy="{fy:.0f}" r="{glow_r:.1f}" '
                    f'fill="{glow_color}" filter="url(#dew)" opacity="0">'
                    f'<animate attributeName="opacity" values="0;0.7;0.7;0" '
                    f'dur="{pulse_dur:.1f}s" begin="{delay:.1f}s" repeatCount="indefinite"/>'
                    f'</circle>'
                )
        P.append('</g>')

    # ── Insects (detailed, naturalist style) ──────────────────────
    for ix, iy, itype, isz, ihue in insects:
        if itype == "butterfly":
            # Flight path — natural cubic Bezier arc showing trajectory
            cp1x = ix + rng.uniform(-30, -10)
            cp1y = iy + rng.uniform(-20, -5)
            cp2x = ix + rng.uniform(10, 30)
            cp2y = iy + rng.uniform(-15, 5)
            trail_end_x = ix + rng.uniform(15, 40)
            trail_end_y = iy + rng.uniform(-25, -5)
            P.append(f'<path d="M{ix - rng.uniform(15, 35):.0f},{iy + rng.uniform(5, 20):.0f} '
                     f'C{cp1x:.0f},{cp1y:.0f} {cp2x:.0f},{cp2y:.0f} {trail_end_x:.0f},{trail_end_y:.0f}" '
                     f'fill="none" stroke="#c8c0a8" stroke-width="0.2" opacity="0.06" '
                     f'stroke-dasharray="1.5 2" stroke-linecap="round"/>')
            # Body
            P.append(f'<ellipse cx="{ix:.0f}" cy="{iy:.0f}" rx="1" ry="{isz * 0.3:.1f}" '
                     f'fill="#3a3020" opacity="0.6"/>')
            wc1 = oklch(0.62, 0.22, ihue)
            wc2 = oklch(0.55, 0.18, (ihue + 30) % 360)
            wc_vein = oklch(0.40, 0.10, ihue)
            for side in [-1, 1]:
                # Upper wings — natural Bezier outline
                uwx = ix + side * isz * 0.5
                uwy = iy - isz * 0.2
                # Wing shape as cubic Bezier path for more natural silhouette
                w_tip_x = ix + side * isz * 0.65
                w_tip_y = iy - isz * 0.45
                w_cp1x = ix + side * isz * 0.15
                w_cp1y = iy - isz * 0.5
                w_cp2x = ix + side * isz * 0.7
                w_cp2y = iy - isz * 0.35
                w_cp3x = ix + side * isz * 0.55
                w_cp3y = iy + isz * 0.05
                w_cp4x = ix + side * isz * 0.1
                w_cp4y = iy + isz * 0.02
                P.append(f'<path d="M{ix:.0f},{iy:.0f} '
                         f'C{w_cp1x:.0f},{w_cp1y:.0f} {w_cp2x:.0f},{w_cp2y:.0f} {w_tip_x:.0f},{w_tip_y:.0f} '
                         f'C{w_cp3x:.0f},{w_cp3y:.0f} {w_cp4x:.0f},{w_cp4y:.0f} {ix:.0f},{iy:.0f}" '
                         f'fill="{wc1}" opacity="0.45" stroke="{wc_vein}" stroke-width="0.3"/>')
                # Wing spot
                P.append(f'<circle cx="{uwx:.0f}" cy="{uwy:.0f}" r="{isz * 0.08:.1f}" fill="#fff" opacity="0.3"/>')
                # Wing venation — 3 veins per wing using curved paths
                for vi in range(3):
                    va = (vi - 1) * 0.4 + side * 0.2
                    vex = uwx + isz * 0.35 * math.cos(va + side * 1.2)
                    vey = uwy + isz * 0.25 * math.sin(va - 0.5)
                    vmx = (ix + vex) / 2 + side * isz * 0.05
                    vmy = (iy + vey) / 2 - isz * 0.08
                    P.append(f'<path d="M{ix:.0f},{iy:.0f} Q{vmx:.0f},{vmy:.0f} {vex:.0f},{vey:.0f}" '
                             f'fill="none" stroke="{wc_vein}" stroke-width="0.2" opacity="0.15"/>')
                # Lower wings
                lwx = ix + side * isz * 0.35
                lwy = iy + isz * 0.15
                P.append(f'<ellipse cx="{lwx:.0f}" cy="{lwy:.0f}" rx="{isz * 0.25:.1f}" ry="{isz * 0.2:.1f}" '
                         f'fill="{wc2}" opacity="0.4"/>')
            # Antennae with clubbed tips
            for side in [-1, 1]:
                P.append(f'<path d="M{ix},{iy - isz * 0.3:.0f} Q{ix + side * 3},{iy - isz * 0.6:.0f} '
                         f'{ix + side * 5},{iy - isz * 0.7:.0f}" fill="none" stroke="#3a3020" '
                         f'stroke-width="0.3" opacity="0.4"/>')
                P.append(f'<circle cx="{ix + side * 5:.0f}" cy="{iy - isz * 0.7:.0f}" r="0.6" '
                         f'fill="#3a3020" opacity="0.35"/>')
        elif itype == "bee":
            # Fuzzy thorax
            P.append(f'<ellipse cx="{ix - isz * 0.1:.0f}" cy="{iy:.0f}" rx="{isz * 0.2:.1f}" ry="{isz * 0.18:.1f}" '
                     f'fill="#c89020" opacity="0.55"/>')
            # Striped abdomen
            P.append(f'<ellipse cx="{ix + isz * 0.1:.0f}" cy="{iy:.0f}" rx="{isz * 0.28:.1f}" ry="{isz * 0.2:.1f}" '
                     f'fill="#d4a030" opacity="0.6"/>')
            for si_b in range(4):
                bsx = ix + isz * 0.1 - isz * 0.15 + si_b * isz * 0.1
                P.append(f'<line x1="{bsx:.0f}" y1="{iy - isz * 0.18:.0f}" x2="{bsx:.0f}" '
                         f'y2="{iy + isz * 0.18:.0f}" stroke="#2a2010" stroke-width="0.7" opacity="0.25"/>')
            # Wings (pair, translucent)
            for side in [-1, 1]:
                P.append(f'<ellipse cx="{ix:.0f}" cy="{iy + side * isz * 0.25:.0f}" '
                         f'rx="{isz * 0.3:.1f}" ry="{isz * 0.1:.1f}" '
                         f'fill="#e8e0d0" opacity="0.25" stroke="#c8c0b0" stroke-width="0.2"/>')
            # Head
            P.append(f'<circle cx="{ix - isz * 0.3:.0f}" cy="{iy:.0f}" r="{isz * 0.1:.1f}" '
                     f'fill="#3a2a10" opacity="0.5"/>')
        elif itype == "dragonfly":
            # Segmented body
            for si_d in range(5):
                df = si_d / 5
                dsx = ix - isz * 0.4 + si_d * isz * 0.2
                dsr = isz * 0.06 * (1 - df * 0.4)
                P.append(f'<circle cx="{dsx:.0f}" cy="{iy:.0f}" r="{dsr:.1f}" fill="#4a6a80" opacity="0.45"/>')
            # Head
            P.append(f'<circle cx="{ix - isz * 0.5:.0f}" cy="{iy:.0f}" r="{isz * 0.08:.1f}" '
                     f'fill="#3a5a70" opacity="0.5"/>')
            # Wings — 4 translucent with venation
            for side in [-1, 1]:
                for pair, off in enumerate([-0.15, 0.05]):
                    wx = ix + off * isz
                    wy = iy + side * isz * 0.25
                    wrx = isz * (0.38 - pair * 0.06)
                    wry = isz * 0.08
                    P.append(f'<ellipse cx="{wx:.0f}" cy="{wy:.0f}" rx="{wrx:.1f}" ry="{wry:.1f}" '
                             f'fill="#d8e8f0" opacity="0.22" stroke="#a0b8c8" stroke-width="0.2" '
                             f'transform="rotate({side * (8 + pair * 5)},{wx:.0f},{wy:.0f})"/>')
                    # Single vein line through wing
                    P.append(f'<line x1="{wx - wrx * 0.8:.0f}" y1="{wy:.0f}" x2="{wx + wrx * 0.8:.0f}" y2="{wy:.0f}" '
                             f'stroke="#a0b8c8" stroke-width="0.15" opacity="0.15" '
                             f'transform="rotate({side * (8 + pair * 5)},{wx:.0f},{wy:.0f})"/>')

        elif itype == "ladybug":
            lb_c = oklch(0.48, 0.24, 20)  # red-orange
            lb_dark = "#2a1a0a"
            # Body
            P.append(f'<ellipse cx="{ix:.0f}" cy="{iy:.0f}" rx="{isz * 0.4:.1f}" ry="{isz * 0.45:.1f}" '
                     f'fill="{lb_c}" opacity="0.55" stroke="{lb_dark}" stroke-width="0.3"/>')
            # Center line (wing split)
            P.append(f'<line x1="{ix:.0f}" y1="{iy - isz * 0.4:.0f}" x2="{ix:.0f}" y2="{iy + isz * 0.4:.0f}" '
                     f'stroke="{lb_dark}" stroke-width="0.3" opacity="0.35"/>')
            # Spots (3-4 per side)
            n_spots_lb = rng.integers(2, 4)
            for spi in range(n_spots_lb):
                for side in [-1, 1]:
                    spx = ix + side * isz * rng.uniform(0.1, 0.25)
                    spy = iy - isz * 0.2 + spi * isz * 0.2
                    P.append(f'<circle cx="{spx:.1f}" cy="{spy:.1f}" r="{isz * 0.06:.1f}" '
                             f'fill="{lb_dark}" opacity="0.4"/>')
            # Head
            P.append(f'<ellipse cx="{ix:.0f}" cy="{iy - isz * 0.45:.0f}" rx="{isz * 0.2:.1f}" ry="{isz * 0.12:.1f}" '
                     f'fill="{lb_dark}" opacity="0.45"/>')
            # Tiny legs
            for li_lb in range(3):
                for side in [-1, 1]:
                    ly_lb = iy - isz * 0.1 + li_lb * isz * 0.15
                    P.append(f'<line x1="{ix + side * isz * 0.3:.0f}" y1="{ly_lb:.0f}" '
                             f'x2="{ix + side * isz * 0.55:.0f}" y2="{ly_lb + 1:.0f}" '
                             f'stroke="{lb_dark}" stroke-width="0.2" opacity="0.2"/>')

    # ── Fallen leaves on ground ───────────────────────────────────
    n_fallen = int(mat * 10)
    for _ in range(n_fallen):
        flx = rng.uniform(40, WIDTH - 40)
        fly = ground_y_at(flx) + rng.uniform(-2, 4)
        fl_rot = rng.uniform(-60, 60)
        fl_size = rng.uniform(3, 7)
        fl_hue = rng.choice([120, 45, 30, 15, 150])  # green → autumn tones
        fl_c = oklch(0.52, 0.14, fl_hue)
        fl_sc = oklch(0.42, 0.10, fl_hue)
        # Simple teardrop leaf shape, rotated flat on ground
        tip_fx = flx + fl_size
        perp_a = math.pi / 2
        cp1_fx = (flx + tip_fx) / 2 + fl_size * 0.3
        cp1_fy = fly - fl_size * 0.25
        cp2_fx = (flx + tip_fx) / 2 + fl_size * 0.3
        cp2_fy = fly + fl_size * 0.25
        P.append(f'<path d="M{flx:.1f},{fly:.1f} Q{cp1_fx:.1f},{cp1_fy:.1f} {tip_fx:.1f},{fly:.1f} '
                 f'Q{cp2_fx:.1f},{cp2_fy:.1f} {flx:.1f},{fly:.1f}" '
                 f'fill="{fl_c}" opacity="0.2" stroke="{fl_sc}" stroke-width="0.2" '
                 f'transform="rotate({fl_rot:.0f},{flx:.1f},{fly:.1f})"/>')
        # Midvein
        P.append(f'<line x1="{flx:.1f}" y1="{fly:.1f}" x2="{tip_fx:.1f}" y2="{fly:.1f}" '
                 f'stroke="{fl_sc}" stroke-width="0.15" opacity="0.15" '
                 f'transform="rotate({fl_rot:.0f},{flx:.1f},{fly:.1f})"/>')

    # ── Falling seeds (dandelion-like wisps) ──────────────────────
    for sx, sy, sa, ss in seeds:
        # Seed body — tiny dark teardrop
        P.append(f'<ellipse cx="{sx:.0f}" cy="{sy + ss * 0.15:.0f}" rx="{ss * 0.12:.1f}" ry="{ss * 0.2:.1f}" '
                 f'fill="#a09060" opacity="0.35"/>')
        # Pappus filaments — radiating upward like a dandelion clock
        n_filaments = rng.integers(6, 12)
        for fi in range(n_filaments):
            fa = -math.pi / 2 + (fi - n_filaments / 2) * (math.pi * 0.8 / n_filaments) + sa
            fl = ss * rng.uniform(0.7, 1.1)
            # Curved filament
            cpx = sx + fl * 0.5 * math.cos(fa) + rng.uniform(-1, 1)
            cpy = sy + fl * 0.5 * math.sin(fa) + rng.uniform(-0.5, 0.5)
            tip_x = sx + fl * math.cos(fa)
            tip_y = sy + fl * math.sin(fa)
            P.append(f'<path d="M{sx:.0f},{sy:.0f} Q{cpx:.1f},{cpy:.1f} {tip_x:.1f},{tip_y:.1f}" '
                     f'fill="none" stroke="#c8c0a0" stroke-width="0.15" opacity="0.2"/>')
            # Tiny barb at tip
            P.append(f'<circle cx="{tip_x:.1f}" cy="{tip_y:.1f}" r="0.3" fill="#d8d0b0" opacity="0.2"/>')

    # ── Maple samaras (helicopter seeds) ───────────────────────────
    for smx, smy, sma, sms in samaras:
        sm_rot = math.degrees(sma) + rng.uniform(-30, 30)
        seed_c = oklch(0.50, 0.08, 35)
        wing_c = oklch(0.58, 0.06, 40)
        # Seed body (round nut)
        P.append(f'<circle cx="{smx:.1f}" cy="{smy:.1f}" r="{sms * 0.15:.1f}" '
                 f'fill="{seed_c}" opacity="0.35"/>')
        # Wing — elongated teardrop
        wing_len = sms
        wing_w = sms * 0.2
        wx_tip = smx + wing_len * math.cos(math.radians(sm_rot))
        wy_tip = smy + wing_len * math.sin(math.radians(sm_rot))
        perp_sm = math.radians(sm_rot) + math.pi / 2
        cp1_sm = (smx + wx_tip) / 2 + wing_w * math.cos(perp_sm)
        cp2_sm = (smy + wy_tip) / 2 + wing_w * math.sin(perp_sm)
        cp3_sm = (smx + wx_tip) / 2 - wing_w * 0.3 * math.cos(perp_sm)
        cp4_sm = (smy + wy_tip) / 2 - wing_w * 0.3 * math.sin(perp_sm)
        P.append(f'<path d="M{smx:.1f},{smy:.1f} Q{cp1_sm:.1f},{cp2_sm:.1f} {wx_tip:.1f},{wy_tip:.1f} '
                 f'Q{cp3_sm:.1f},{cp4_sm:.1f} {smx:.1f},{smy:.1f}" '
                 f'fill="{wing_c}" opacity="0.2" stroke="{seed_c}" stroke-width="0.2"/>')
        # Wing vein
        P.append(f'<line x1="{smx:.1f}" y1="{smy:.1f}" x2="{wx_tip:.1f}" y2="{wy_tip:.1f}" '
                 f'stroke="{seed_c}" stroke-width="0.15" opacity="0.15"/>')

    # ── Labels (botanical plate annotation with halos) ────────────
    P.append('<g font-family="Georgia,serif" font-size="7.5" fill="#5a4a3a">')
    for li, (lx, ly, text, ax, ay, when) in enumerate(labels):
        # Dashed leader line with small arrowhead
        P.append(f'<line x1="{ax:.0f}" y1="{ay:.0f}" x2="{lx:.0f}" y2="{ly:.0f}" '
                 f'stroke="#a09070" stroke-width="0.35" {_timeline_style(when, 0.3)} stroke-dasharray="1.5 2"/>')
        # Anchor dot — small circle at plant base
        P.append(f'<circle cx="{ax:.0f}" cy="{ay:.0f}" r="1.2" fill="none" '
                 f'stroke="#a09070" stroke-width="0.4" {_timeline_style(when, 0.3)}/>')
        P.append(f'<circle cx="{ax:.0f}" cy="{ay:.0f}" r="0.4" fill="#a09070" {_timeline_style(when, 0.3)}/>')
        # Label text with paint-order halo for readability
        P.append(f'<text x="{lx:.0f}" y="{ly:.0f}" text-anchor="middle" font-style="italic" '
                 f'{_timeline_style(when, 0.55)} paint-order="stroke fill" stroke="#f5f0e6" stroke-width="2.5" '
                 f'stroke-linejoin="round">{text}</text>')
        # Plate number annotation (small, upright)
        P.append(f'<text x="{lx:.0f}" y="{ly + 9:.0f}" text-anchor="middle" font-size="5" '
                 f'{_timeline_style(when, 0.3)} font-style="normal" paint-order="stroke fill" stroke="#f5f0e6" '
                 f'stroke-width="2" stroke-linejoin="round">Fig. {li + 1}</text>')
    P.append('</g>')

    # ── Tiered botanical border ────────────────────────────────────
    m = 16
    label = metrics.get("label", "")
    plate_num = abs(hash(label)) % 100 + 1

    # --- Border neatlines ---
    if mat < 0.15:
        # Single thin neatline
        P.append(f'<rect x="{m}" y="{m}" width="{WIDTH - 2 * m}" height="{HEIGHT - 2 * m}" '
                 f'fill="none" stroke="#9a8a68" stroke-width="1.0" rx="1"/>')
    elif mat < 0.35:
        # Double neatline
        P.append(f'<rect x="{m}" y="{m}" width="{WIDTH - 2 * m}" height="{HEIGHT - 2 * m}" '
                 f'fill="none" stroke="#7a6a50" stroke-width="1.6" rx="2"/>')
        P.append(f'<rect x="{m + 4}" y="{m + 4}" width="{WIDTH - 2 * m - 8}" height="{HEIGHT - 2 * m - 8}" '
                 f'fill="none" stroke="#a09878" stroke-width="0.6" rx="1"/>')
    else:
        # Triple neatline (mat >= 0.35)
        P.append(f'<rect x="{m}" y="{m}" width="{WIDTH - 2 * m}" height="{HEIGHT - 2 * m}" '
                 f'fill="none" stroke="#7a6a50" stroke-width="2.0" rx="2"/>')
        P.append(f'<rect x="{m + 5}" y="{m + 5}" width="{WIDTH - 2 * m - 10}" height="{HEIGHT - 2 * m - 10}" '
                 f'fill="none" stroke="#a09878" stroke-width="0.7" rx="1"/>')
        P.append(f'<rect x="{m + 2.5}" y="{m + 2.5}" width="{WIDTH - 2 * m - 5}" height="{HEIGHT - 2 * m - 5}" '
                 f'fill="none" stroke="#b8b098" stroke-width="0.35" rx="1.5" stroke-dasharray="4 2"/>')

    # --- Corner dots (mat 0.35–0.6) or scrollwork (mat >= 0.6) ---
    if 0.35 <= mat < 0.6:
        for cx_c, cy_c in [(m + 5, m + 5), (WIDTH - m - 5, m + 5),
                           (WIDTH - m - 5, HEIGHT - m - 5), (m + 5, HEIGHT - m - 5)]:
            P.append(f'<circle cx="{cx_c}" cy="{cy_c}" r="1.5" fill="#a09070" opacity="0.2"/>')
    elif mat >= 0.6:
        for cx_c, cy_c, rot in [
            (m + 5, m + 5, 0), (WIDTH - m - 5, m + 5, 90),
            (WIDTH - m - 5, HEIGHT - m - 5, 180), (m + 5, HEIGHT - m - 5, 270),
        ]:
            P.append(f'<g transform="rotate({rot},{cx_c},{cy_c})">')
            P.append(f'<path d="M{cx_c},{cy_c} Q{cx_c + 15},{cy_c + 1} {cx_c + 25},{cy_c + 8}" '
                     f'fill="none" stroke="#a09070" stroke-width="0.7" opacity="0.4"/>')
            P.append(f'<path d="M{cx_c},{cy_c} Q{cx_c + 1},{cy_c + 15} {cx_c + 8},{cy_c + 25}" '
                     f'fill="none" stroke="#a09070" stroke-width="0.7" opacity="0.4"/>')
            P.append(f'<path d="M{cx_c + 25},{cy_c + 8} Q{cx_c + 28},{cy_c + 12} {cx_c + 24},{cy_c + 14} '
                     f'Q{cx_c + 20},{cy_c + 12} {cx_c + 22},{cy_c + 9}" '
                     f'fill="none" stroke="#a09070" stroke-width="0.5" opacity="0.35"/>')
            P.append(f'<path d="M{cx_c + 8},{cy_c + 25} Q{cx_c + 12},{cy_c + 28} {cx_c + 14},{cy_c + 24} '
                     f'Q{cx_c + 12},{cy_c + 20} {cx_c + 9},{cy_c + 22}" '
                     f'fill="none" stroke="#a09070" stroke-width="0.5" opacity="0.35"/>')
            P.append(f'<path d="M{cx_c + 4},{cy_c + 4} Q{cx_c + 10},{cy_c + 1} {cx_c + 14},{cy_c + 6} '
                     f'Q{cx_c + 10},{cy_c + 9} {cx_c + 4},{cy_c + 4}" '
                     f'fill="#b8c898" opacity="0.12" stroke="#a0b078" stroke-width="0.25"/>')
            P.append(f'<path d="M{cx_c + 4},{cy_c + 4} Q{cx_c + 1},{cy_c + 10} {cx_c + 6},{cy_c + 14} '
                     f'Q{cx_c + 9},{cy_c + 10} {cx_c + 4},{cy_c + 4}" '
                     f'fill="#b8c898" opacity="0.12" stroke="#a0b078" stroke-width="0.25"/>')
            P.append(f'<line x1="{cx_c + 4}" y1="{cy_c + 4}" x2="{cx_c + 13}" y2="{cx_c + 5}" '
                     f'stroke="#90a868" stroke-width="0.2" opacity="0.15"/>')
            P.append(f'<circle cx="{cx_c + 16}" cy="{cy_c + 4}" r="1" fill="#c09070" opacity="0.15"/>')
            P.append(f'<circle cx="{cx_c + 4}" cy="{cy_c + 16}" r="1" fill="#c09070" opacity="0.15"/>')
            P.append('</g>')

    # --- Top vine (mat >= 0.6) ---
    if mat >= 0.6:
        vine_y = m + 3
        vine_pts = []
        vx = m + 30
        while vx < WIDTH - m - 30:
            vy = vine_y + math.sin(vx * 0.04) * 2
            vine_pts.append((vx, vy))
            vx += 8
        if len(vine_pts) > 2:
            vine_d = f"M{vine_pts[0][0]:.1f},{vine_pts[0][1]:.1f}"
            for j in range(1, len(vine_pts) - 1, 2):
                if j + 1 < len(vine_pts):
                    vine_d += f" Q{vine_pts[j][0]:.1f},{vine_pts[j][1]:.1f} {vine_pts[j+1][0]:.1f},{vine_pts[j+1][1]:.1f}"
            P.append(f'<path d="{vine_d}" fill="none" stroke="#a0b078" stroke-width="0.4" opacity="0.15"/>')
            for j in range(0, len(vine_pts), 3):
                vvx, vvy = vine_pts[j]
                side = 1 if j % 2 == 0 else -1
                P.append(f'<ellipse cx="{vvx + 2:.0f}" cy="{vvy + side * 3:.0f}" rx="2" ry="1" '
                         f'fill="#b0c890" opacity="0.08" '
                         f'transform="rotate({side * 20},{vvx + 2:.0f},{vvy + side * 3:.0f})"/>')

    # --- Bottom vine (mat > 0.8) ---
    if mat > 0.8:
        vine_y_b = HEIGHT - m - 3
        vine_pts_b = []
        vx_b = m + 30
        while vx_b < WIDTH - m - 30:
            vy_b = vine_y_b + math.sin(vx_b * 0.035 + 1.5) * 2
            vine_pts_b.append((vx_b, vy_b))
            vx_b += 9
        if len(vine_pts_b) > 2:
            vine_d_b = f"M{vine_pts_b[0][0]:.1f},{vine_pts_b[0][1]:.1f}"
            for j in range(1, len(vine_pts_b) - 1, 2):
                if j + 1 < len(vine_pts_b):
                    vine_d_b += f" Q{vine_pts_b[j][0]:.1f},{vine_pts_b[j][1]:.1f} {vine_pts_b[j+1][0]:.1f},{vine_pts_b[j+1][1]:.1f}"
            P.append(f'<path d="{vine_d_b}" fill="none" stroke="#a0b078" stroke-width="0.35" opacity="0.12"/>')
            for j in range(0, len(vine_pts_b), 4):
                vvx_b, vvy_b = vine_pts_b[j]
                side = 1 if j % 2 == 0 else -1
                P.append(f'<ellipse cx="{vvx_b + 1.5:.0f}" cy="{vvy_b + side * 2.5:.0f}" rx="1.8" ry="0.9" '
                         f'fill="#b0c890" opacity="0.06" '
                         f'transform="rotate({side * 25},{vvx_b + 1.5:.0f},{vvy_b + side * 2.5:.0f})"/>')

    # ── Tiered title cartouche ──────────────────────────────────
    cart_w = max(140, len(label) * 8 + 60)
    cart_h = 32 if mat >= 0.35 else 18
    cart_x = CX - cart_w / 2
    cart_y = HEIGHT - m - 6 - cart_h

    if mat < 0.15:
        # Plain italic text, no box
        P.append(f'<text x="{CX}" y="{cart_y + 12:.0f}" text-anchor="middle" font-family="Georgia,serif" '
                 f'font-size="9" fill="#5a4a3a" opacity="0.5" font-style="italic" '
                 f'paint-order="stroke fill" stroke="#f5f0e6" stroke-width="2" stroke-linejoin="round">'
                 f'{label}</text>')
    elif mat < 0.35:
        # Simple box + text
        P.append(f'<rect x="{cart_x:.0f}" y="{cart_y:.0f}" width="{cart_w:.0f}" height="{cart_h}" '
                 f'fill="#f5f0e6" opacity="0.8" rx="2"/>')
        P.append(f'<rect x="{cart_x:.0f}" y="{cart_y:.0f}" width="{cart_w:.0f}" height="{cart_h}" '
                 f'fill="none" stroke="#a09070" stroke-width="0.6" rx="2"/>')
        P.append(f'<text x="{CX}" y="{cart_y + 12:.0f}" text-anchor="middle" font-family="Georgia,serif" '
                 f'font-size="9" fill="#5a4a3a" opacity="0.55" font-style="italic" '
                 f'paint-order="stroke fill" stroke="#f5f0e6" stroke-width="2" stroke-linejoin="round">'
                 f'{label}</text>')
    elif mat < 0.6:
        # Box + subtitle
        P.append(f'<rect x="{cart_x:.0f}" y="{cart_y:.0f}" width="{cart_w:.0f}" height="{cart_h}" '
                 f'fill="#f5f0e6" opacity="0.85" rx="3"/>')
        P.append(f'<rect x="{cart_x:.0f}" y="{cart_y:.0f}" width="{cart_w:.0f}" height="{cart_h}" '
                 f'fill="none" stroke="#a09070" stroke-width="0.7" rx="3"/>')
        P.append(f'<text x="{CX}" y="{cart_y + 13:.0f}" text-anchor="middle" font-family="Georgia,serif" '
                 f'font-size="10" fill="#5a4a3a" opacity="0.6" font-style="italic" '
                 f'paint-order="stroke fill" stroke="#f5f0e6" stroke-width="2" stroke-linejoin="round">'
                 f'{label}</text>')
        P.append(f'<text x="{CX}" y="{cart_y + 25:.0f}" text-anchor="middle" font-family="Georgia,serif" '
                 f'font-size="5.5" fill="#8a7a6a" opacity="0.35" letter-spacing="2" '
                 f'paint-order="stroke fill" stroke="#f5f0e6" stroke-width="1.5" stroke-linejoin="round">'
                 f'BOTANICAL GARDEN</text>')
    elif mat < 0.8:
        # Full cartouche + leaf ornaments
        P.append(f'<rect x="{cart_x:.0f}" y="{cart_y:.0f}" width="{cart_w:.0f}" height="{cart_h}" '
                 f'fill="#f5f0e6" opacity="0.85" rx="3"/>')
        P.append(f'<rect x="{cart_x:.0f}" y="{cart_y:.0f}" width="{cart_w:.0f}" height="{cart_h}" '
                 f'fill="none" stroke="#a09070" stroke-width="0.8" rx="3"/>')
        P.append(f'<rect x="{cart_x + 2.5:.1f}" y="{cart_y + 2.5:.1f}" width="{cart_w - 5:.0f}" height="{cart_h - 5}" '
                 f'fill="none" stroke="#c8c0a8" stroke-width="0.3" rx="2"/>')
        P.append(f'<text x="{CX}" y="{cart_y + 14:.0f}" text-anchor="middle" font-family="Georgia,serif" '
                 f'font-size="10" fill="#5a4a3a" opacity="0.6" font-style="italic" '
                 f'paint-order="stroke fill" stroke="#f5f0e6" stroke-width="2" stroke-linejoin="round">'
                 f'{label}</text>')
        P.append(f'<text x="{CX}" y="{cart_y + 25:.0f}" text-anchor="middle" font-family="Georgia,serif" '
                 f'font-size="5.5" fill="#8a7a6a" opacity="0.4" letter-spacing="2" '
                 f'paint-order="stroke fill" stroke="#f5f0e6" stroke-width="1.5" stroke-linejoin="round">'
                 f'BOTANICAL GARDEN</text>')
        for side in [-1, 1]:
            lx_d = CX + side * (cart_w / 2 - 18)
            ly_d = cart_y + 13
            P.append(f'<path d="M{lx_d:.0f},{ly_d:.0f} Q{lx_d + side * 5:.0f},{ly_d - 3:.0f} '
                     f'{lx_d + side * 8:.0f},{ly_d:.0f} Q{lx_d + side * 5:.0f},{ly_d + 2:.0f} '
                     f'{lx_d:.0f},{ly_d:.0f}" fill="#b0c090" opacity="0.2"/>')
    else:
        # Full + dividing rule + plate number (mat > 0.8)
        P.append(f'<rect x="{cart_x:.0f}" y="{cart_y:.0f}" width="{cart_w:.0f}" height="{cart_h}" '
                 f'fill="#f5f0e6" opacity="0.85" rx="3"/>')
        P.append(f'<rect x="{cart_x:.0f}" y="{cart_y:.0f}" width="{cart_w:.0f}" height="{cart_h}" '
                 f'fill="none" stroke="#a09070" stroke-width="0.8" rx="3"/>')
        P.append(f'<rect x="{cart_x + 2.5:.1f}" y="{cart_y + 2.5:.1f}" width="{cart_w - 5:.0f}" height="{cart_h - 5}" '
                 f'fill="none" stroke="#c8c0a8" stroke-width="0.3" rx="2"/>')
        P.append(f'<line x1="{cart_x + 15}" y1="{cart_y + cart_h * 0.62:.0f}" '
                 f'x2="{cart_x + cart_w - 15}" y2="{cart_y + cart_h * 0.62:.0f}" '
                 f'stroke="#c0b898" stroke-width="0.3" opacity="0.4"/>')
        P.append(f'<text x="{CX}" y="{cart_y + 14:.0f}" text-anchor="middle" font-family="Georgia,serif" '
                 f'font-size="10" fill="#5a4a3a" opacity="0.6" font-style="italic" '
                 f'paint-order="stroke fill" stroke="#f5f0e6" stroke-width="2" stroke-linejoin="round">'
                 f'{label}</text>')
        P.append(f'<text x="{CX}" y="{cart_y + 25:.0f}" text-anchor="middle" font-family="Georgia,serif" '
                 f'font-size="5.5" fill="#8a7a6a" opacity="0.4" letter-spacing="2" '
                 f'paint-order="stroke fill" stroke="#f5f0e6" stroke-width="1.5" stroke-linejoin="round">'
                 f'BOTANICAL GARDEN</text>')
        for side in [-1, 1]:
            lx_d = CX + side * (cart_w / 2 - 18)
            ly_d = cart_y + 13
            P.append(f'<path d="M{lx_d:.0f},{ly_d:.0f} Q{lx_d + side * 5:.0f},{ly_d - 3:.0f} '
                     f'{lx_d + side * 8:.0f},{ly_d:.0f} Q{lx_d + side * 5:.0f},{ly_d + 2:.0f} '
                     f'{lx_d:.0f},{ly_d:.0f}" fill="#b0c090" opacity="0.2"/>')

    # ── Tiered legend / scale bar / plate number ─────────────────
    if mat >= 0.35:
        # Scale bar (top-right)
        sb_x = WIDTH - m - 65
        sb_y = m + 12
        sb_len = 50
        P.append(f'<line x1="{sb_x}" y1="{sb_y}" x2="{sb_x + sb_len}" y2="{sb_y}" '
                 f'stroke="#8a7a6a" stroke-width="0.6" opacity="0.25"/>')
        for tick_x in [sb_x, sb_x + sb_len / 2, sb_x + sb_len]:
            P.append(f'<line x1="{tick_x}" y1="{sb_y - 2}" x2="{tick_x}" y2="{sb_y + 2}" '
                     f'stroke="#8a7a6a" stroke-width="0.4" opacity="0.25"/>')
        P.append(f'<rect x="{sb_x}" y="{sb_y - 0.8}" width="{sb_len / 2}" height="1.6" '
                 f'fill="#8a7a6a" opacity="0.15"/>')
        P.append(f'<text x="{sb_x + sb_len / 2}" y="{sb_y + 7}" text-anchor="middle" '
                 f'font-family="Georgia,serif" font-size="4" fill="#8a7a6a" opacity="0.25" '
                 f'paint-order="stroke fill" stroke="#f5f0e6" stroke-width="1.5" '
                 f'stroke-linejoin="round">scale</text>')

    if mat >= 0.6:
        # Species legend (bottom-left)
        leg_x = m + 10
        leg_y = HEIGHT - m - 12
        species_shown = set()
        legend_items = []
        for repo in repos[:MAX_REPOS]:
            sp = _classify_species(repo)
            if sp not in species_shown and len(legend_items) < 4:
                species_shown.add(sp)
                legend_items.append(sp)
        if legend_items:
            P.append('<g font-family="Georgia,serif" font-size="5" fill="#8a7a6a" opacity="0.35">')
            for li_l, sp_name in enumerate(legend_items):
                liy = leg_y + li_l * 8
                if sp_name in ("oak", "birch"):
                    P.append(f'<circle cx="{leg_x + 3}" cy="{liy}" r="2" fill="none" '
                             f'stroke="#8a7a6a" stroke-width="0.4"/>')
                elif sp_name == "conifer":
                    P.append(f'<path d="M{leg_x + 3},{liy - 2.5} L{leg_x + 5.5},{liy + 2} '
                             f'L{leg_x + 0.5},{liy + 2} Z" fill="none" stroke="#8a7a6a" stroke-width="0.4"/>')
                elif sp_name in ("fern",):
                    P.append(f'<path d="M{leg_x + 1},{liy + 2} Q{leg_x + 3},{liy - 2} {leg_x + 5},{liy + 1}" '
                             f'fill="none" stroke="#8a7a6a" stroke-width="0.4"/>')
                else:
                    P.append(f'<rect x="{leg_x + 1}" y="{liy - 2}" width="4" height="4" fill="none" '
                             f'stroke="#8a7a6a" stroke-width="0.4" rx="0.5"/>')
                P.append(f'<text x="{leg_x + 10}" y="{liy + 1.5}" font-style="italic">{sp_name}</text>')
            P.append('</g>')

    if mat > 0.8:
        # Plate number (bottom-right)
        P.append(f'<text x="{WIDTH - m - 12}" y="{HEIGHT - m - 8}" text-anchor="end" '
                 f'font-family="Georgia,serif" font-size="5.5" fill="#a09080" opacity="0.3" '
                 f'paint-order="stroke fill" stroke="#f5f0e6" stroke-width="1.5" stroke-linejoin="round">'
                 f'Pl. {plate_num}</text>')

    P.append('</svg>')
    return '\n'.join(P)
