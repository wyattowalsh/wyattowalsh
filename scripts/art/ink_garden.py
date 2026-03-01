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

import numpy as np

from .shared import (
    WIDTH, HEIGHT, CX, CY, LANG_HUES,
    seed_hash, hex_frac, oklch, Noise2D,
    compute_maturity,
    make_radial_gradient, make_linear_gradient,
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
}


def _classify_species(repo: dict) -> str:
    """Classify a repo into a plant species based on its metrics."""
    stars = repo.get("stars", 0)
    age = repo.get("age_months", 0)
    lang = repo.get("language")

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
    if leaf_shape == "oak_lobed":
        tip_x = lx + ls * math.cos(la)
        tip_y = ly + ls * math.sin(la)
        perp = la + math.pi / 2
        dx = tip_x - lx
        dy = tip_y - ly
        fill_c = oklch_fn(0.48, 0.19, lh)
        stroke_c = oklch_fn(0.36, 0.14, lh)
        b1x = lx + dx * 0.2 + ls * 0.3 * math.cos(perp)
        b1y = ly + dy * 0.2 + ls * 0.3 * math.sin(perp)
        v1x = lx + dx * 0.35 + ls * 0.08 * math.cos(perp)
        v1y = ly + dy * 0.35 + ls * 0.08 * math.sin(perp)
        b2x = lx + dx * 0.5 + ls * 0.35 * math.cos(perp)
        b2y = ly + dy * 0.5 + ls * 0.35 * math.sin(perp)
        v2x = lx + dx * 0.65 + ls * 0.1 * math.cos(perp)
        v2y = ly + dy * 0.65 + ls * 0.1 * math.sin(perp)
        b3x = lx + dx * 0.8 + ls * 0.25 * math.cos(perp)
        b3y = ly + dy * 0.8 + ls * 0.25 * math.sin(perp)
        cp_b1x = (lx + b1x) / 2 + ls * 0.15 * math.cos(perp)
        cp_b1y = (ly + b1y) / 2 + ls * 0.15 * math.sin(perp)
        cp_v1x = (b1x + v1x) / 2
        cp_v1y = (b1y + v1y) / 2
        cp_b2x = (v1x + b2x) / 2 + ls * 0.18 * math.cos(perp)
        cp_b2y = (v1y + b2y) / 2 + ls * 0.18 * math.sin(perp)
        cp_v2x = (b2x + v2x) / 2
        cp_v2y = (b2y + v2y) / 2
        cp_b3x = (v2x + b3x) / 2 + ls * 0.12 * math.cos(perp)
        cp_b3y = (v2y + b3y) / 2 + ls * 0.12 * math.sin(perp)
        cp_tipx = (b3x + tip_x) / 2
        cp_tipy = (b3y + tip_y) / 2
        back_cp1x = (tip_x + lx) / 2 - ls * 0.1 * math.cos(perp)
        back_cp1y = (tip_y + ly) / 2 - ls * 0.1 * math.sin(perp)
        d = (f"M{lx:.1f},{ly:.1f} "
             f"Q{cp_b1x:.1f},{cp_b1y:.1f} {b1x:.1f},{b1y:.1f} "
             f"Q{cp_v1x:.1f},{cp_v1y:.1f} {v1x:.1f},{v1y:.1f} "
             f"Q{cp_b2x:.1f},{cp_b2y:.1f} {b2x:.1f},{b2y:.1f} "
             f"Q{cp_v2x:.1f},{cp_v2y:.1f} {v2x:.1f},{v2y:.1f} "
             f"Q{cp_b3x:.1f},{cp_b3y:.1f} {b3x:.1f},{b3y:.1f} "
             f"Q{cp_tipx:.1f},{cp_tipy:.1f} {tip_x:.1f},{tip_y:.1f} "
             f"Q{back_cp1x:.1f},{back_cp1y:.1f} {lx:.1f},{ly:.1f} Z")
        P.append(f'<path d="{d}" fill="{fill_c}" opacity="0.4" stroke="{stroke_c}" stroke-width="0.3"/>')
        if has_vein and budget_ok():
            P.append(f'<line x1="{lx:.1f}" y1="{ly:.1f}" x2="{tip_x:.1f}" y2="{tip_y:.1f}" '
                     f'stroke="{stroke_c}" stroke-width="0.2" opacity="0.3"/>')

    elif leaf_shape == "small_round":
        cx_l = lx + ls * 0.5 * math.cos(la)
        cy_l = ly + ls * 0.5 * math.sin(la)
        r = ls * 0.4
        fill_c = oklch_fn(0.53, 0.19, lh)
        stroke_c = oklch_fn(0.40, 0.14, lh)
        P.append(f'<circle cx="{cx_l:.1f}" cy="{cy_l:.1f}" r="{r:.1f}" '
                 f'fill="{fill_c}" opacity="0.4" stroke="{stroke_c}" stroke-width="0.3"/>')
        P.append(f'<line x1="{lx:.1f}" y1="{ly:.1f}" x2="{cx_l:.1f}" y2="{cy_l:.1f}" '
                 f'stroke="{stroke_c}" stroke-width="0.3" opacity="0.3"/>')

    elif leaf_shape == "pinnate":
        tip_x = lx + ls * math.cos(la)
        tip_y = ly + ls * math.sin(la)
        stroke_c = oklch_fn(0.40, 0.16, lh)
        fill_c = oklch_fn(0.50, 0.19, lh)
        P.append(f'<line x1="{lx:.1f}" y1="{ly:.1f}" x2="{tip_x:.1f}" y2="{tip_y:.1f}" '
                 f'stroke="{stroke_c}" stroke-width="0.3" opacity="0.4"/>')
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
                         f'stroke="{stroke_c}" stroke-width="0.2" opacity="0.35"/>')
                er = leaflet_len * 0.4
                P.append(f'<ellipse cx="{ex:.1f}" cy="{ey:.1f}" rx="{er:.1f}" ry="{er*0.6:.1f}" '
                         f'fill="{fill_c}" opacity="0.35" '
                         f'transform="rotate({math.degrees(ea):.0f},{ex:.1f},{ey:.1f})"/>')

    elif leaf_shape == "narrow_blade":
        cx_l = lx + ls * 0.4 * math.cos(la)
        cy_l = ly + ls * 0.4 * math.sin(la)
        rx = ls * 0.12
        ry = ls * 0.5
        fill_c = oklch_fn(0.50, 0.19, lh)
        stroke_c = oklch_fn(0.38, 0.14, lh)
        P.append(f'<ellipse cx="{cx_l:.1f}" cy="{cy_l:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" '
                 f'fill="{fill_c}" opacity="0.4" stroke="{stroke_c}" stroke-width="0.2" '
                 f'transform="rotate({math.degrees(la):.0f},{cx_l:.1f},{cy_l:.1f})"/>')

    elif leaf_shape == "needle_cluster":
        stroke_c = oklch_fn(0.38, 0.17, lh)
        n_needles = rng.integers(3, 5)
        for ni in range(n_needles):
            na = la + (ni - n_needles / 2.0) * 0.4
            nl = ls * rng.uniform(0.5, 0.9)
            P.append(f'<line x1="{lx:.1f}" y1="{ly:.1f}" '
                     f'x2="{lx + nl * math.cos(na):.1f}" y2="{ly + nl * math.sin(na):.1f}" '
                     f'stroke="{stroke_c}" stroke-width="0.4" opacity="0.4"/>')

    else:
        # "teardrop" — the original quad-bezier almond shape
        tip_x = lx + ls * math.cos(la)
        tip_y = ly + ls * math.sin(la)
        perp = la + math.pi / 2
        bulge = ls * 0.35
        cp1x = (lx + tip_x) / 2 + bulge * math.cos(perp)
        cp1y = (ly + tip_y) / 2 + bulge * math.sin(perp)
        cp2x = (lx + tip_x) / 2 - bulge * math.cos(perp)
        cp2y = (ly + tip_y) / 2 - bulge * math.sin(perp)
        fill_c = oklch_fn(0.50, 0.19, lh)
        stroke_c = oklch_fn(0.38, 0.14, lh)
        P.append(f'<path d="M{lx:.1f},{ly:.1f} Q{cp1x:.1f},{cp1y:.1f} {tip_x:.1f},{tip_y:.1f} '
                 f'Q{cp2x:.1f},{cp2y:.1f} {lx:.1f},{ly:.1f}" '
                 f'fill="{fill_c}" opacity="0.42" stroke="{stroke_c}" stroke-width="0.3"/>')
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
    if bloom_type == "radial_petal":
        for layer in range(petal_layers):
            lf = layer / max(1, petal_layers)
            lr = bs * (1 - lf * 0.3)
            lo = 0.4 + lf * 0.2
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


def generate(metrics: dict, *, seed: str | None = None, maturity: float | None = None) -> str:
    mat = maturity if maturity is not None else compute_maturity(metrics)
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

    # Ground line — slightly below center, gentle hills
    GROUND_Y = CY + 40

    def ground_y_at(x):
        return GROUND_Y + noise.noise(x * 0.008, 0) * 25 + noise.noise(x * 0.02, 5) * 8

    # Collect all visual elements
    all_segs = []   # (x1,y1,x2,y2,sw,hue,depth,is_main)
    roots = []       # (x1,y1,x2,y2,sw)
    leaves = []      # (x,y,angle,size,hue,has_vein,leaf_shape)
    blooms = []      # (x,y,size,hue,n_petals,layers,bloom_type)
    buds = []        # (x,y,size,hue)
    berries = []     # (x,y,size,hue)
    tendrils = []    # list of point-lists
    mushrooms_list = []  # (x,y,size,hue)
    insects = []     # (x,y,type,size,hue)
    webs = []        # (cx,cy,radius,n_spokes)
    dew_drops = []   # (x,y,size)
    seeds = []       # (x,y,angle,size)
    labels = []      # (lx,ly,text,ax,ay)

    # Track plant base positions for ground cover enhancement
    plant_bases = []

    # ── Plant generation (progressive: blank soil → full garden) ────
    n_repos = len(repos)

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
        hue = LANG_HUES.get(lang, 160)
        repo_stars = repo.get("stars", 0)
        age = repo.get("age_months", 6)

        species = _classify_species(repo)
        style = SPECIES.get(species)

        spread = min(MAX_REPOS, n_repos)
        base_x = 80 + (WIDTH - 160) * (ri / max(1, spread - 1)) if spread > 1 else CX
        base_x += rng.uniform(-20, 20)
        gy = ground_y_at(base_x)

        base_angle = -math.pi / 2 + rng.uniform(-0.3, 0.3)
        # Scale growth by tree_t: seedlings are short/thin, mature trees are full
        main_length = (50 + min(250, age * 3.0)) * tree_t
        max_depth = max(1, round(max(2, min(6, 2 + age // 12)) * tree_t))
        stem_sw = (2.5 + min(3.0, age * 0.05)) * (0.3 + 0.7 * tree_t)

        if main_length >= 5:
            labels.append((base_x, gy + 18, repo.get("name", ""), base_x, gy))
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
                    all_segs.append((cx_, cy_, nx_, ny_, sw, f_hue, 1, si < 3))

                    # Pinnate leaflets along both sides (alternating, shrinking)
                    if si > 1 and si < n_spine - 1:
                        leaflet_size = f_length * 0.08 * (1 - t * 0.6)
                        side = 1 if si % 2 == 0 else -1
                        perp = cur_angle + side * math.pi / 2
                        la = perp + rng.uniform(-0.2, 0.2)
                        if len(leaves) < MAX_LEAVES:
                            leaves.append((nx_, ny_, la, max(2, leaflet_size), (f_hue + 15) % 360, False, "pinnate"))

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
                    all_segs.append((cx_, cy_, nx_, ny_, 0.3, f_hue, 2, False))
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
                    all_segs.append((cx_, cy_, nx_, ny_, sw, b_hue, 0, True))

                    # Visible joint (short horizontal widening)
                    jw = sw * 1.8
                    all_segs.append((nx_ - jw, ny_, nx_ + jw, ny_, sw * 0.6, b_hue, 1, False))

                    # Narrow leaf clusters at alternating joints
                    if ji % 2 == 0 and ji > 0:
                        n_blades = rng.integers(2, 5)
                        side = rng.choice([-1, 1])
                        for bi in range(n_blades):
                            la = -math.pi / 2 + side * (0.8 + bi * 0.2) + rng.uniform(-0.15, 0.15)
                            ls = rng.uniform(6, 14) * (1 - t * 0.3)
                            if len(leaves) < MAX_LEAVES:
                                leaves.append((nx_, ny_, la, ls, (b_hue + 20) % 360, False, "narrow_blade"))

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

                    all_segs.append((cx_, cy_, nx_, ny_, sw, hue, depth, depth == 0))

                    if depth >= 1 and rng.random() < style_d["leaf_prob"]:
                        side = rng.choice([-1, 1])
                        la = a + side * (0.5 + rng.uniform(0, 0.6))
                        ls = 5 + rng.uniform(0, 6) * (1 - depth / (max_d + 1))
                        leaves.append((nx_, ny_, la, ls, (hue + 25) % 360, rng.random() < 0.7, style_d["leaf_shape"]))
                        if rng.random() < 0.15:
                            dew_drops.append((
                                nx_ + ls * 0.5 * math.cos(la),
                                ny_ + ls * 0.5 * math.sin(la),
                                rng.uniform(1, 2.5),
                            ))

                    if depth >= 2 and rng.random() < 0.12:
                        buds.append((nx_, ny_, rng.uniform(2, 4), hue))

                    cx_, cy_ = nx_, ny_
                    angle = a

                    if len(all_segs) < MAX_SEGS and rng.random() < style_d["branch_prob"] * (1 - depth / max_d):
                        fa = rng.uniform(0.4, 1.1) * rng.choice([-1, 1])
                        decay_lo, decay_hi = style_d["length_decay"]
                        _grow(cx_, cy_, a + fa, depth + 1, length * rng.uniform(decay_lo, decay_hi), sw * style_d["width_decay"], style_d, max_d)

                # Terminal fork
                if depth < max_d and len(all_segs) < MAX_SEGS:
                    fork_lo, fork_hi = style_d["fork_range"]
                    for _ in range(rng.integers(fork_lo, fork_hi)):
                        if len(all_segs) >= MAX_SEGS:
                            break
                        fa = rng.uniform(0.3, 1.0) * rng.choice([-1, 1])
                        decay_lo, decay_hi = style_d["length_decay"]
                        _grow(cx_, cy_, angle + fa, depth + 1, length * rng.uniform(decay_lo, decay_hi), sw * style_d["width_decay"], style_d, max_d)

                # Blooms at tips
                if depth >= max_d - 1 and rng.random() < 0.6:
                    n_petals = max(4, min(12, 4 + repo_stars // 2))
                    bloom_size = 5 + min(18, repo_stars * 0.8)
                    petal_layers = 1 + min(3, repo_stars // 5)
                    blooms.append((cx_, cy_, bloom_size, hue, n_petals, petal_layers, style_d["bloom_type"]))

                # Berries
                if depth >= max_d and rng.random() < 0.2:
                    for _ in range(rng.integers(2, 6)):
                        berries.append((
                            cx_ + rng.uniform(-6, 6),
                            cy_ + rng.uniform(-6, 6),
                            rng.uniform(1.5, 3),
                            (hue + 180) % 360,
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

                    all_segs.append((cx_, cy_, nx_, ny_, sw, hue, depth, depth == 0))

                    if depth >= 1 and rng.random() < style_d["leaf_prob"]:
                        side = rng.choice([-1, 1])
                        la = a + side * (0.5 + rng.uniform(0, 0.6))
                        ls = 5 + rng.uniform(0, 6) * (1 - depth / (max_d + 1))
                        leaves.append((nx_, ny_, la, ls, (hue + 25) % 360, rng.random() < 0.7, style_d["leaf_shape"]))
                        if rng.random() < 0.15:
                            dew_drops.append((
                                nx_ + ls * 0.5 * math.cos(la),
                                ny_ + ls * 0.5 * math.sin(la),
                                rng.uniform(1, 2.5),
                            ))

                    if depth >= 2 and rng.random() < 0.12:
                        buds.append((nx_, ny_, rng.uniform(2, 4), hue))

                    cx_, cy_ = nx_, ny_
                    angle = a

                    # min_trunk_ratio: for depth==0, don't branch until past trunk portion
                    trunk_ok = True
                    if depth == 0:
                        trunk_ok = (si + seg_idx) > n_s * style_d["min_trunk_ratio"]

                    if trunk_ok and len(all_segs) < MAX_SEGS and rng.random() < style_d["branch_prob"] * (1 - depth / max_d):
                        angle_range = style_d.get("branch_angle_range", (0.4, 1.1))
                        fa = rng.uniform(angle_range[0], angle_range[1]) * rng.choice([-1, 1])
                        decay_lo, decay_hi = style_d["length_decay"]
                        _grow(cx_, cy_, a + fa, depth + 1, length * rng.uniform(decay_lo, decay_hi), sw * style_d["width_decay"], style_d, max_d, si)

                # Terminal fork
                if depth < max_d and len(all_segs) < MAX_SEGS:
                    fork_lo, fork_hi = style_d["fork_range"]
                    for _ in range(rng.integers(fork_lo, fork_hi)):
                        if len(all_segs) >= MAX_SEGS:
                            break
                        spread_a = style_d["base_angle_spread"] if depth == 0 else 1.0
                        fa = rng.uniform(0.3, spread_a) * rng.choice([-1, 1])
                        decay_lo, decay_hi = style_d["length_decay"]
                        _grow(cx_, cy_, angle + fa, depth + 1, length * rng.uniform(decay_lo, decay_hi), sw * style_d["width_decay"], style_d, max_d, 0)

                # Blooms at tips (fern and bamboo have no blooms — handled above)
                if depth >= max_d - 1 and rng.random() < 0.6:
                    n_petals = max(4, min(12, 4 + repo_stars // 2))
                    bloom_size = 5 + min(18, repo_stars * 0.8)
                    petal_layers = 1 + min(3, repo_stars // 5)
                    blooms.append((cx_, cy_, bloom_size, hue, n_petals, petal_layers, style_d["bloom_type"]))

                # Berries
                if depth >= max_d and rng.random() < 0.2:
                    for _ in range(rng.integers(2, 6)):
                        berries.append((
                            cx_ + rng.uniform(-6, 6),
                            cy_ + rng.uniform(-6, 6),
                            rng.uniform(1.5, 3),
                            (hue + 180) % 360,
                        ))

            _grow(base_x, gy, base_angle, 0, main_length, stem_sw)

        # ── Root system (scales with tree growth) ────────────────
        root_depth = (40 + min(100, age * 1.2)) * tree_t
        n_roots = max(1, round(max(2, min(5, 2 + forks // 8)) * tree_t)) if root_depth >= 1 else 0
        for rootn in range(n_roots):
            if len(roots) >= MAX_ROOTS:
                break
            ra = math.pi / 2 + rng.uniform(-0.8, 0.8)
            rx, ry = base_x + rng.uniform(-8, 8), gy
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
                roots.append((rx, ry, nrx, nry, r_sw * (1 - rsi / r_segs * 0.6)))
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
                        roots.append((brx, bry, bnrx, bnry, r_sw * 0.4))
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

    # ── Insects ───────────────────────────────────────────────────
    if mat > 0.15:
        for _ in range(min(5, watchers // 2)):
            insects.append((rng.uniform(50, WIDTH - 50), rng.uniform(40, GROUND_Y - 20), "butterfly", rng.uniform(8, 16), rng.integers(0, 360)))
    if mat > 0.25:
        for _ in range(min(4, contributions // 500)):
            insects.append((rng.uniform(80, WIDTH - 80), rng.uniform(60, GROUND_Y - 40), "bee", rng.uniform(4, 8), 45))
    if mat > 0.35:
        for _ in range(min(3, orgs)):
            insects.append((rng.uniform(60, WIDTH - 60), rng.uniform(30, GROUND_Y - 50), "dragonfly", rng.uniform(10, 18), rng.integers(0, 360)))
    if mat > 0.45:
        for _ in range(min(3, stars_total // 8)):
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

    # ── defs ──────────────────────────────────────────────────────
    P.append('<defs>')
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
    P.append(f'''<radialGradient id="vignette" cx="50%" cy="48%" r="55%">
    <stop offset="0%" stop-color="#f5f0e6" stop-opacity="0"/>
    <stop offset="65%" stop-color="#f5f0e6" stop-opacity="0"/>
    <stop offset="88%" stop-color="#d8c8a0" stop-opacity="0.15"/>
    <stop offset="100%" stop-color="#b0986a" stop-opacity="{0.12 + mat * 0.28:.3f}"/>
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
    <line x1="2" y1="10" x2="1" y2="2" stroke="#7a9a5a" stroke-width="0.35" opacity="0.3"/>
    <line x1="4" y1="10" x2="5" y2="3" stroke="#8aaa6a" stroke-width="0.4" opacity="0.28"/>
    <path d="M7,10 Q6,5 8,1" fill="none" stroke="#6a8a4a" stroke-width="0.3" opacity="0.25"/>
    <line x1="10" y1="10" x2="9" y2="2" stroke="#9aba7a" stroke-width="0.35" opacity="0.26"/>
    <path d="M13,10 Q14,6 12,1" fill="none" stroke="#7a9a5a" stroke-width="0.3" opacity="0.24"/>
    <circle cx="12" cy="1" r="0.5" fill="#b0aa70" opacity="0.2"/>
    <line x1="16" y1="10" x2="15" y2="4" stroke="#8a9a6a" stroke-width="0.3" opacity="0.22"/>
  </pattern>''')
    # Soil layers — rich earth tones with organic texture
    P.append('''<pattern id="soil1" width="24" height="8" patternUnits="userSpaceOnUse">
    <rect width="24" height="8" fill="#c4a87a"/>
    <circle cx="5" cy="3" r="0.9" fill="#b09060" opacity="0.35"/>
    <circle cx="16" cy="5" r="0.6" fill="#a08050" opacity="0.3"/>
    <circle cx="20" cy="2" r="0.4" fill="#c0a870" opacity="0.2"/>
    <path d="M0,6 Q6,5 12,6.5 Q18,7 24,6" fill="none" stroke="#b09868" stroke-width="0.3" opacity="0.15"/>
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


    # ── Background (aged parchment) ──────────────────────────────
    P.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#f5f0e6" filter="url(#paper)"/>')
    # Sky gradient — pale blue wash at top
    P.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#skyGrad)"/>')
    # Atmospheric light wash from upper-left
    P.append(f'<rect x="0" y="0" width="{WIDTH}" height="{GROUND_Y:.0f}" fill="url(#lightRay)"/>')
    # Water stain marks — large, very faint irregular patches
    for _ in range(int(mat * 5)):
        wcx = rng.uniform(80, WIDTH - 80)
        wcy = rng.uniform(80, HEIGHT - 80)
        wrx = rng.uniform(40, 100)
        wry = rng.uniform(30, 80)
        P.append(f'<ellipse cx="{wcx:.0f}" cy="{wcy:.0f}" rx="{wrx:.0f}" ry="{wry:.0f}" '
                 f'fill="#ddd0b0" opacity="{rng.uniform(0.02,0.05):.3f}" '
                 f'transform="rotate({rng.uniform(-20,20):.0f},{wcx:.0f},{wcy:.0f})"/>')
    # Foxing spots — varied sizes and warm tones
    fox_colors = ["#d8c8a8", "#cfc0a0", "#d0c4a4", "#c8b898"]
    if mat >= 0.05:
        for _ in range(int(mat * 35)):
            P.append(f'<circle cx="{rng.uniform(20,WIDTH-20):.0f}" cy="{rng.uniform(20,HEIGHT-20):.0f}" '
                     f'r="{rng.uniform(1.5,7):.1f}" fill="{rng.choice(fox_colors)}" '
                     f'opacity="{rng.uniform(0.02,0.07):.3f}"/>')
    # Vignette overlay — subtle edge darkening
    P.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#vignette)"/>')

    # ── Underground strata ────────────────────────────────────────
    account_age = max((r.get("age_months", 6) for r in repos), default=12)
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
        P.append(f'<path d="{lp}" fill="{soil_fills[si]}" opacity="0.5"/>')

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
            wsa = rng.uniform(-0.5, 0.5)
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
    for ri_r, (rx1, ry1, rx2, ry2, rsw) in enumerate(roots):
        rc = root_colors[ri_r % len(root_colors)]
        mx = (rx1 + rx2) / 2 + rng.uniform(-1.5, 1.5)
        my = (ry1 + ry2) / 2 + rng.uniform(-1.5, 1.5)
        P.append(f'<path d="M{rx1:.1f},{ry1:.1f} Q{mx:.1f},{my:.1f} {rx2:.1f},{ry2:.1f}" '
                 f'fill="none" stroke="{rc}" stroke-width="{rsw:.1f}" stroke-linecap="round"/>')
        # Root hairs at fine tips
        if rsw < 0.5 and rng.random() < 0.3:
            for _ in range(rng.integers(2, 5)):
                ha = rng.uniform(0, 2 * math.pi)
                hl = rng.uniform(1.5, 4)
                P.append(f'<line x1="{rx2:.1f}" y1="{ry2:.1f}" '
                         f'x2="{rx2 + hl * math.cos(ha):.1f}" y2="{ry2 + hl * math.sin(ha):.1f}" '
                         f'stroke="{rc}" stroke-width="0.15" opacity="0.3"/>')
    P.append('</g>')

    # Mycorrhizal network — dashed threads with nutrient exchange nodes
    if len(repos) > 1 and forks > 0:
        P.append('<g opacity="0.12">')
        myco_nodes = []
        for _ in range(min(15, forks)):
            mx1 = rng.uniform(60, WIDTH - 60)
            my1 = rng.uniform(GROUND_Y + 20, GROUND_Y + 70)
            mx2 = mx1 + rng.uniform(-90, 90)
            my2 = my1 + rng.uniform(-15, 15)
            mid_x = (mx1 + mx2) / 2
            mid_y = my1 + rng.uniform(8, 22)
            P.append(f'<path d="M{mx1:.0f},{my1:.0f} Q{mid_x:.0f},{mid_y:.0f} {mx2:.0f},{my2:.0f}" '
                     f'fill="none" stroke="#a09060" stroke-width="0.5" stroke-dasharray="2 3"/>')
            myco_nodes.append((mid_x, mid_y))
        # Nutrient exchange nodes (tiny circles at junctions)
        for nx, ny in myco_nodes[:8]:
            P.append(f'<circle cx="{nx:.0f}" cy="{ny:.0f}" r="1.2" fill="#b0a060" opacity="0.5"/>')
        P.append('</g>')

    # ── Ground surface ────────────────────────────────────────────
    P.append(f'<path d="{ground_path} L{WIDTH},{GROUND_Y+15} L0,{GROUND_Y+15} Z" fill="url(#grass)" opacity="0.6"/>')
    # Main ground line — warm earth tone, slightly thicker
    P.append(f'<path d="{ground_path}" fill="none" stroke="#7a6a3a" stroke-width="1.4" opacity="0.45"/>')
    # Secondary ground line — lighter, offset slightly below for depth
    sub_ground = f"M{ground_pts[0][0]},{ground_pts[0][1]+1.5:.1f}" + "".join(
        f" L{x:.1f},{y+1.5:.1f}" for x, y in ground_pts[1:]
    )
    P.append(f'<path d="{sub_ground}" fill="none" stroke="#9a8a5a" stroke-width="0.5" opacity="0.25"/>')

    # Branch density map for ground cover enhancement
    bd = defaultdict(int)
    for x1, y1, x2, y2, *_ in all_segs:
        bd[(int((x1 + x2) / 2 / 30), int((y1 + y2) / 2 / 30))] += 1
    max_bd = max(bd.values()) if bd else 1

    # Ground cover (enhanced with fern frondlets, moss patches, clover)
    for _ in range(10 + int(mat * 60)):
        gcx = rng.uniform(20, WIDTH - 20)
        gcy = ground_y_at(gcx) + rng.uniform(-3, 3)
        r_val = rng.random()
        if r_val < 0.4:
            # Grass tufts
            for _ in range(rng.integers(2, 5)):
                ga = -math.pi / 2 + rng.uniform(-0.4, 0.4)
                gl = rng.uniform(3, 8)
                P.append(f'<line x1="{gcx:.0f}" y1="{gcy:.0f}" '
                         f'x2="{gcx+gl*math.cos(ga):.0f}" y2="{gcy+gl*math.sin(ga):.0f}" '
                         f'stroke="#7a9a5a" stroke-width="0.4" opacity="0.25"/>')
        elif r_val < 0.55:
            # Stones
            P.append(f'<circle cx="{gcx:.0f}" cy="{gcy:.0f}" r="{rng.uniform(0.5,1.5):.1f}" fill="#b0a080" opacity="0.2"/>')
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
            wf_sc = oklch(0.50, 0.16, wf_hue)
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

    # ── Atmospheric wash (faint watercolor sky suggestion) ────────
    for _ in range(int(mat * 6)) if mat >= 0.15 else ():
        awx = rng.uniform(60, WIDTH - 60)
        awy = rng.uniform(36, GROUND_Y - 80)
        awrx = rng.uniform(50, 120)
        awry = rng.uniform(20, 50)
        # Very faint blue-gray watercolor washes
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

    # ── Plant shadow patches (cast shadows on ground) ────────────
    for bx_s, by_s in plant_bases:
        # Soft elliptical shadow beneath each plant
        shadow_w = 20 + rng.uniform(0, 15)
        P.append(f'<ellipse cx="{bx_s + 5:.0f}" cy="{by_s + 2:.0f}" rx="{shadow_w:.0f}" ry="{shadow_w * 0.2:.0f}" '
                 f'fill="#5a5030" opacity="{0.01 + mat * 0.04:.3f}"/>')

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
    for mkey, count in monthly.items():
        intensity = count / max(1, max_m)
        mi_val = int(mkey) - 1 if mkey.isdigit() else 0
        angle = -math.pi / 2 + mi_val * 2 * math.pi / 12
        cx_m = CX + 200 * math.cos(angle)
        cy_m = min(CY - 80 + 180 * math.sin(angle), GROUND_Y - 30)
        for _ in range(int(intensity * 30)):
            dx = cx_m + rng.normal(0, 50)
            dy = cy_m + rng.normal(0, 50)
            if dy > GROUND_Y - 5:
                continue
            P.append(f'<circle cx="{dx:.0f}" cy="{dy:.0f}" r="{rng.uniform(0.15,0.5):.1f}" '
                     f'fill="#c8bfa8" opacity="{0.06+intensity*0.12:.2f}"/>')

    # PASS 1: Main stems with rich bark texture
    for x1, y1, x2, y2, sw, hue, depth, is_main in all_segs:
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
                     f'fill="none" stroke="{oklch(0.22, 0.07, hue)}" stroke-width="{sw:.1f}" opacity="0.9" stroke-linecap="round"/>')
            # Core layer (current color, narrower)
            P.append(f'<path d="M{x1:.1f},{y1:.1f} Q{mx:.1f},{my:.1f} {x2:.1f},{y2:.1f}" '
                     f'fill="none" stroke="{color}" stroke-width="{sw*0.55:.1f}" opacity="0.55" stroke-linecap="round"/>')
        else:
            P.append(f'<path d="M{x1:.1f},{y1:.1f} Q{mx:.1f},{my:.1f} {x2:.1f},{y2:.1f}" '
                     f'fill="none" stroke="{color}" stroke-width="{sw:.1f}" opacity="0.85" stroke-linecap="round"/>')
        # Highlight edge — subtle lighter line on one side
        if sw > 2.5:
            perp = math.atan2(y2 - y1, x2 - x1) + math.pi / 2
            hoff = sw * 0.3
            P.append(f'<path d="M{x1 + hoff * math.cos(perp):.1f},{y1 + hoff * math.sin(perp):.1f} '
                     f'Q{mx + hoff * math.cos(perp):.1f},{my + hoff * math.sin(perp):.1f} '
                     f'{x2 + hoff * math.cos(perp):.1f},{y2 + hoff * math.sin(perp):.1f}" '
                     f'fill="none" stroke="{color_light}" stroke-width="0.3" opacity="0.25"/>')
        # Bark texture — longitudinal grain lines
        if sw > 3.5 and mat > 0.3 and len(P) - elem_count < MAX_ELEMENTS:
            seg_len = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            if seg_len > 8:
                perp = math.atan2(y2 - y1, x2 - x1) + math.pi / 2
                bark_c = oklch(0.32, 0.04, hue)
                for bi in range(min(4, int(sw))):
                    off = (bi - sw / 2) * 0.7
                    jx1, jy1 = rng.uniform(-0.6, 0.6), rng.uniform(-0.6, 0.6)
                    jx2, jy2 = rng.uniform(-0.6, 0.6), rng.uniform(-0.6, 0.6)
                    P.append(f'<line x1="{x1 + off * math.cos(perp) + jx1:.1f}" '
                             f'y1="{y1 + off * math.sin(perp) + jy1:.1f}" '
                             f'x2="{x2 + off * math.cos(perp) + jx2:.1f}" '
                             f'y2="{y2 + off * math.sin(perp) + jy2:.1f}" '
                             f'stroke="{bark_c}" stroke-width="{0.15 + rng.uniform(0, 0.15):.2f}" opacity="0.14"/>')
                # Occasional knot mark
                if seg_len > 15 and rng.random() < 0.08 and mat > 0.5:
                    kx = (x1 + x2) / 2 + rng.uniform(-2, 2)
                    ky = (y1 + y2) / 2 + rng.uniform(-2, 2)
                    kr = sw * rng.uniform(0.15, 0.3)
                    P.append(f'<circle cx="{kx:.1f}" cy="{ky:.1f}" r="{kr:.1f}" fill="none" '
                             f'stroke="{bark_c}" stroke-width="0.3" opacity="0.12"/>')

    # Water droplet trails on thick stems
    for x1, y1, x2, y2, sw, hue, depth, is_main in all_segs:
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
                                 f'r="{dr_t:.1f}" fill="url(#dewGrad)" opacity="0.3"/>')

    # PASS 2: Secondary branches
    for x1, y1, x2, y2, sw, hue, depth, is_main in all_segs:
        if is_main:
            continue
        d_frac = depth / 6
        color = oklch(0.32 + d_frac * 0.12, 0.10 + d_frac * 0.04, hue)
        op = max(0.3, 0.80 - depth * 0.08)
        mx = (x1 + x2) / 2 + rng.uniform(-2, 2)
        my = (y1 + y2) / 2 + rng.uniform(-2, 2)
        P.append(f'<path d="M{x1:.1f},{y1:.1f} Q{mx:.1f},{my:.1f} {x2:.1f},{y2:.1f}" '
                 f'fill="none" stroke="{color}" stroke-width="{sw:.1f}" opacity="{op:.2f}" stroke-linecap="round"/>')

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
    budget_ok = lambda: len(P) - elem_count < MAX_ELEMENTS
    for leaf_tuple in leaves[:MAX_LEAVES]:
        if not budget_ok():
            break
        lx, ly, la, ls, lh, has_vein, leaf_shape = leaf_tuple
        _draw_leaf(P, lx, ly, la, ls, lh, has_vein, leaf_shape, rng, budget_ok, oklch)

    # PASS 5: Buds with sepals
    for bx, by, bs, bh in buds:
        bud_rot = rng.uniform(-30, 30)
        bud_c = oklch(0.58, 0.18, bh)
        sepal_c = oklch(0.42, 0.14, (bh + 120) % 360)
        # Sepals — small protective leaves wrapping the bud
        for si_s in range(2):
            sa_s = bud_rot + (si_s - 0.5) * 40
            P.append(f'<ellipse cx="{bx:.1f}" cy="{by + bs * 0.3:.1f}" rx="{bs * 0.35:.1f}" ry="{bs * 0.6:.1f}" '
                     f'fill="{sepal_c}" opacity="0.3" '
                     f'transform="rotate({sa_s:.0f},{bx:.1f},{by:.1f})"/>')
        # Bud body
        P.append(f'<ellipse cx="{bx:.1f}" cy="{by:.1f}" rx="{bs * 0.4:.1f}" ry="{bs:.1f}" '
                 f'fill="{bud_c}" opacity="0.5" stroke="{oklch(0.45, 0.14, bh)}" stroke-width="0.2" '
                 f'transform="rotate({bud_rot:.0f},{bx:.1f},{by:.1f})"/>')

    # PASS 6: Multi-layer blooms with species-specific types (capped)
    for bloom_tuple in blooms[:MAX_BLOOMS]:
        if not budget_ok():
            break
        bx, by, bs, bh, n_petals, petal_layers, bloom_type = bloom_tuple
        _draw_bloom(P, bx, by, bs, bh, n_petals, petal_layers, bloom_type, rng, budget_ok, oklch)
        # Bloom center glow overlay
        P.append(f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="{bs*0.6:.1f}" '
                 f'fill="url(#petalGlow)" opacity="0.5"/>')

    # PASS 7: Berries with calyx and richer highlights
    for bi_idx, (bx, by, bs, bh) in enumerate(berries):
        if not budget_ok():
            break
        # Tiny stem + calyx (only on first 20 berries to save budget)
        if bi_idx < 20:
            P.append(f'<line x1="{bx:.1f}" y1="{by - bs:.1f}" x2="{bx:.1f}" y2="{by - bs * 1.5:.1f}" '
                     f'stroke="#6a5a3a" stroke-width="0.3" opacity="0.35"/>')
            for ci_b in range(3):
                ca_b = ci_b * 2 * math.pi / 3 - math.pi / 2
                P.append(f'<line x1="{bx:.1f}" y1="{by - bs:.1f}" '
                         f'x2="{bx + bs * 0.3 * math.cos(ca_b):.1f}" y2="{by - bs + bs * 0.3 * math.sin(ca_b):.1f}" '
                         f'stroke="#5a7a3a" stroke-width="0.2" opacity="0.3"/>')
        # Berry body
        P.append(f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="{bs:.1f}" fill="{oklch(0.42, 0.24, bh)}" '
                 f'opacity="0.6" stroke="{oklch(0.33, 0.18, bh)}" stroke-width="0.3"/>')
        # Highlight
        P.append(f'<circle cx="{bx - bs * 0.25:.1f}" cy="{by - bs * 0.25:.1f}" r="{bs * 0.28:.1f}" '
                 f'fill="#fff" opacity="0.25"/>')

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

    # ── Insects (detailed, naturalist style) ──────────────────────
    for ix, iy, itype, isz, ihue in insects:
        if itype == "butterfly":
            # Body
            P.append(f'<ellipse cx="{ix:.0f}" cy="{iy:.0f}" rx="1" ry="{isz * 0.3:.1f}" '
                     f'fill="#3a3020" opacity="0.6"/>')
            wc1 = oklch(0.62, 0.22, ihue)
            wc2 = oklch(0.55, 0.18, (ihue + 30) % 360)
            wc_vein = oklch(0.40, 0.10, ihue)
            for side in [-1, 1]:
                # Upper wings
                uwx = ix + side * isz * 0.5
                uwy = iy - isz * 0.2
                P.append(f'<ellipse cx="{uwx:.0f}" cy="{uwy:.0f}" rx="{isz * 0.4:.1f}" ry="{isz * 0.3:.1f}" '
                         f'fill="{wc1}" opacity="0.45" stroke="{wc_vein}" stroke-width="0.3" '
                         f'transform="rotate({side * 15},{uwx:.0f},{uwy:.0f})"/>')
                # Wing spot
                P.append(f'<circle cx="{uwx:.0f}" cy="{uwy:.0f}" r="{isz * 0.08:.1f}" fill="#fff" opacity="0.3"/>')
                # Wing venation — 3 veins per wing
                for vi in range(3):
                    va = (vi - 1) * 0.4 + side * 0.2
                    vex = uwx + isz * 0.35 * math.cos(va + side * 1.2)
                    vey = uwy + isz * 0.25 * math.sin(va - 0.5)
                    P.append(f'<line x1="{ix:.0f}" y1="{iy:.0f}" x2="{vex:.0f}" y2="{vey:.0f}" '
                             f'stroke="{wc_vein}" stroke-width="0.2" opacity="0.15"/>')
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
    P.append(f'<g font-family="Georgia,serif" font-size="7.5" fill="#5a4a3a">')
    for li, (lx, ly, text, ax, ay) in enumerate(labels):
        # Dashed leader line with small arrowhead
        P.append(f'<line x1="{ax:.0f}" y1="{ay:.0f}" x2="{lx:.0f}" y2="{ly:.0f}" '
                 f'stroke="#a09070" stroke-width="0.35" opacity="0.3" stroke-dasharray="1.5 2"/>')
        # Anchor dot — small circle at plant base
        P.append(f'<circle cx="{ax:.0f}" cy="{ay:.0f}" r="1.2" fill="none" '
                 f'stroke="#a09070" stroke-width="0.4" opacity="0.3"/>')
        P.append(f'<circle cx="{ax:.0f}" cy="{ay:.0f}" r="0.4" fill="#a09070" opacity="0.3"/>')
        # Label text with paint-order halo for readability
        P.append(f'<text x="{lx:.0f}" y="{ly:.0f}" text-anchor="middle" font-style="italic" '
                 f'opacity="0.55" paint-order="stroke fill" stroke="#f5f0e6" stroke-width="2.5" '
                 f'stroke-linejoin="round">{text}</text>')
        # Plate number annotation (small, upright)
        P.append(f'<text x="{lx:.0f}" y="{ly + 9:.0f}" text-anchor="middle" font-size="5" '
                 f'opacity="0.3" font-style="normal" paint-order="stroke fill" stroke="#f5f0e6" '
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
                 f'fill="none" stroke="#b0a888" stroke-width="0.6" rx="1"/>')
    elif mat < 0.35:
        # Double neatline
        P.append(f'<rect x="{m}" y="{m}" width="{WIDTH - 2 * m}" height="{HEIGHT - 2 * m}" '
                 f'fill="none" stroke="#8a7a60" stroke-width="1.2" rx="2"/>')
        P.append(f'<rect x="{m + 4}" y="{m + 4}" width="{WIDTH - 2 * m - 8}" height="{HEIGHT - 2 * m - 8}" '
                 f'fill="none" stroke="#c0b898" stroke-width="0.4" rx="1"/>')
    else:
        # Triple neatline (mat >= 0.35)
        P.append(f'<rect x="{m}" y="{m}" width="{WIDTH - 2 * m}" height="{HEIGHT - 2 * m}" '
                 f'fill="none" stroke="#8a7a60" stroke-width="1.5" rx="2"/>')
        P.append(f'<rect x="{m + 5}" y="{m + 5}" width="{WIDTH - 2 * m - 10}" height="{HEIGHT - 2 * m - 10}" '
                 f'fill="none" stroke="#c0b898" stroke-width="0.5" rx="1"/>')
        P.append(f'<rect x="{m + 2.5}" y="{m + 2.5}" width="{WIDTH - 2 * m - 5}" height="{HEIGHT - 2 * m - 5}" '
                 f'fill="none" stroke="#d0c8b0" stroke-width="0.25" rx="1.5" stroke-dasharray="4 2"/>')

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
            P.append(f'<g font-family="Georgia,serif" font-size="5" fill="#8a7a6a" opacity="0.35">')
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
