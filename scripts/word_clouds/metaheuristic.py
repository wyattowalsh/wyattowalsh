"""Metaheuristic animated word cloud renderer and renderer registry."""

from __future__ import annotations

import math
import os
import random
from concurrent.futures import ProcessPoolExecutor

from .core import PlacedWord
from .colors import COLOR_FUNCS, make_shifted_color_func
from .engine import SvgWordCloudEngine
from .solvers import (
    _META_SOLVERS,
    _aesthetic_cost,
    configure_layout_readability,
    _eval_fitness,
    _random_solution,
    _solve_harmony_search,
)
from .wordle import WordleRenderer
from .clustered import ClusteredRenderer
from .typographic import TypographicRenderer
from .shaped import ShapedRenderer
from ..utils import get_logger

logger = get_logger(module=__name__)


def _run_solver(
    args: tuple[str, int, list[float], float, float, int, int, list[str], object],
) -> tuple[str, list[tuple[float, float, float]]]:
    """Worker function for parallel solver execution (top-level for pickling)."""
    name, n_words, sizes, canvas_w, canvas_h, max_iter, seed, texts, layout_readability = args
    configure_layout_readability(layout_readability)
    solver_fn = _META_SOLVERS[name]
    rng = random.Random(seed)
    placements = solver_fn(n_words, sizes, canvas_w, canvas_h, max_iter, rng, texts)
    return name, placements


class MetaheuristicAnimRenderer(SvgWordCloudEngine):
    """Animated word cloud showing 25 metaheuristic optimization algorithms.

    Each algorithm solves the same word placement problem, producing a frame.
    All 25 frames are stacked in a single SVG with CSS opacity animation
    that cycles through them infinitely.
    """

    def __init__(
        self,
        *,
        hold_duration: float = 1.8,
        fade_duration: float = 0.2,
        pop_size: int = 20,
        max_iter: int = 300,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.hold_duration = hold_duration
        self.fade_duration = fade_duration
        self.pop_size = pop_size
        self.max_iter = max_iter

    def _prepare_words(
        self,
        frequencies: dict[str, float],
    ) -> tuple[list[str], list[float], list[float], list[str], list[int], list[float]]:
        """Prepare word data from frequencies.

        Filters out generic catch-all buckets like "other" and "others".
        Returns (texts, sizes, freq_values, colors, weights, opacities).
        """
        sorted_words = [
            (w, f)
            for w, f in sorted(frequencies.items(), key=lambda kv: kv[1], reverse=True)
            if w.lower() not in {"other", "others"}
        ]
        if not sorted_words:
            return [], [], [], [], [], []
        freqs = [f for _, f in sorted_words]
        min_freq = min(freqs)
        max_freq = max(freqs)
        total = len(sorted_words)

        _GOLDEN_ANGLE_FRAC = (math.sqrt(5) - 1) / 2

        texts: list[str] = []
        sizes_list: list[float] = []
        colors: list[str] = []
        weights: list[int] = []
        opacities: list[float] = []

        for idx, (word, freq) in enumerate(sorted_words):
            texts.append(word.lower())
            sizes_list.append(self._frequency_to_size(freq, min_freq, max_freq))
            weights.append(self._frequency_to_weight(freq, min_freq, max_freq))
            opacities.append(self._frequency_to_opacity(freq, min_freq, max_freq))
            color_idx = int(((idx * _GOLDEN_ANGLE_FRAC) % 1.0) * total)
            colors.append(self.color_func(color_idx, total))

        return texts, sizes_list, freqs, colors, weights, opacities

    def _solve_all(
        self,
        texts: list[str],
        sizes: list[float],
    ) -> list[tuple[str, list[tuple[float, float, float]]]]:
        """Run all 25 metaheuristic solvers in parallel and return (name, placements) pairs."""
        n_words = len(texts)
        canvas_w = float(self.width)
        canvas_h = float(self.height)

        # Build args for each solver (top-level worker for pickling)
        solver_args = [
            (
                name,
                n_words,
                sizes,
                canvas_w,
                canvas_h,
                self.max_iter,
                self.seed,
                texts,
                self.layout_readability,
            )
            for name in _META_SOLVERS
        ]

        n_workers = min(len(solver_args), os.cpu_count() or 4)
        logger.info(
            "Running {n} solvers across {w} workers",
            n=len(solver_args),
            w=n_workers,
        )

        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            results = list(executor.map(_run_solver, solver_args))

        for name, _ in results:
            logger.debug("MetaheuristicAnimRenderer: {name} completed", name=name)

        return results

    def _render_frame(
        self,
        algo_name: str,
        positions: list[tuple[float, float, float]],
        texts: list[str],
        sizes: list[float],
        colors: list[str],
        weights: list[int],
        opacities: list[float],
    ) -> list[PlacedWord]:
        """Convert solver output to PlacedWord list for one frame."""
        placed: list[PlacedWord] = []
        for i in range(len(texts)):
            x, y, rot = positions[i]
            placed.append(
                PlacedWord(
                    text=texts[i],
                    x=x,
                    y=y,
                    font_size=sizes[i],
                    rotation=rot,
                    color=colors[i],
                    font_weight=weights[i],
                    font_family=self.font_family,
                    opacity=opacities[i],
                )
            )
        return placed

    def _render_frame_svg_body(
        self,
        placed_words: list[PlacedWord],
        algo_name: str,
        frame_idx: int,
    ) -> str:
        """Render the SVG elements for a single frame (words + algorithm label)."""
        lines: list[str] = []

        glow_threshold = self._glow_size_threshold(placed_words)
        tier1_threshold = float("inf")
        tier2_threshold = float("inf")
        if placed_words:
            pw_sizes = sorted((pw.font_size for pw in placed_words), reverse=True)
            t1_idx = max(1, int(len(pw_sizes) * 0.10))
            tier1_threshold = pw_sizes[min(t1_idx, len(pw_sizes) - 1)]
            t2_idx = max(1, int(len(pw_sizes) * 0.30))
            tier2_threshold = pw_sizes[min(t2_idx, len(pw_sizes) - 1)]

        for pw in placed_words:
            # font-family, text-anchor, dominant-baseline moved to CSS
            attrs_parts = [
                f'x="{pw.x:.1f}"',
                f'y="{pw.y:.1f}"',
                f'font-size="{pw.font_size:.1f}"',
                f'fill="{pw.color}"',
                f'font-weight="{pw.font_weight}"',
            ]
            if pw.opacity < 1.0:
                attrs_parts.append(f'opacity="{pw.opacity:.2f}"')
            if pw.rotation != 0:
                attrs_parts.append(
                    f'transform="rotate({pw.rotation:.1f},{pw.x:.1f},{pw.y:.1f})"'
                )
            if pw.font_size >= glow_threshold:
                attrs_parts.append('filter="url(#wc-glow)"')
            elif pw.font_size >= tier2_threshold:
                attrs_parts.append('filter="url(#wc-shadow)"')
            if pw.font_size >= tier1_threshold:
                spacing = max(0.5, pw.font_size * 0.02)
                attrs_parts.append(f'letter-spacing="{spacing:.1f}"')

            lines.append(f"  <text {' '.join(attrs_parts)}>{pw.text}</text>")

        # Algorithm name label — pill-shaped badge (prominent)
        label_y = self.height * 0.96
        pill_w = len(algo_name) * 9.5 + 32
        pill_h = 30
        cx = self.width / 2
        lines.append(
            f'  <g class="algo-label">'
            f'<rect x="{cx - pill_w / 2:.1f}" y="{label_y - pill_h / 2:.1f}"'
            f' width="{pill_w:.1f}" height="{pill_h}" rx="{pill_h // 2}"'
            f' fill="white" fill-opacity="0.88"'
            f' stroke="#c0c0c0" stroke-width="0.75"/>'
            f'<text x="{cx:.1f}" y="{label_y:.1f}"'
            f' text-anchor="middle" dominant-baseline="central"'
            f' fill="#333"'
            f' style="font: 700 16px {self.font_family}; letter-spacing: 0.8px;">'
            f"{algo_name}</text></g>"
        )
        return "\n".join(lines)

    def _stack_frames(
        self,
        frame_bodies: list[str],
        algo_names: list[str],
    ) -> str:
        """Stack all frames into a single SVG with CSS opacity animation.

        Slideshow style: each frame held then quick fade to next, cycling
        infinitely.  Filters are shared (2 total, not per-frame) and
        repeated text attributes are in CSS for smaller file size.
        """
        n = len(frame_bodies)
        frame_time = self.hold_duration + self.fade_duration
        total_duration = frame_time * n

        # -- CSS keyframes for cycling animation --------------------------
        css_lines = [
            "/* Metaheuristic word cloud animation */",
            f".mf {{ opacity: 0; will-change: opacity; }}",
            f".mf text {{ font-family: {self.font_family};"
            f" text-anchor: middle; dominant-baseline: central; }}",
        ]

        visible_pct = (self.hold_duration / total_duration) * 100
        fade_in_pct = (self.fade_duration / total_duration) * 100
        fade_out_pct = fade_in_pct

        for i in range(n):
            start_pct = (i * frame_time / total_duration) * 100
            visible_start = start_pct + fade_in_pct
            visible_end = visible_start + visible_pct
            end_pct = visible_end + fade_out_pct
            kf_name = f"mf{i}"
            css_lines.append(f"@keyframes {kf_name} {{")
            if i == 0:
                css_lines.append("  0% { opacity: 1; }")
                css_lines.append(f"  {visible_pct:.2f}% {{ opacity: 1; }}")
                css_lines.append(
                    f"  {visible_pct + fade_out_pct:.2f}% {{ opacity: 0; visibility: hidden; }}"
                )
                css_lines.append(f"  {100 - fade_in_pct:.2f}% {{ opacity: 0; visibility: hidden; }}")
                css_lines.append("  100% { opacity: 1; }")
            else:
                if start_pct > 0:
                    css_lines.append("  0% { opacity: 0; visibility: hidden; }")
                    css_lines.append(f"  {start_pct:.2f}% {{ opacity: 0; visibility: hidden; }}")
                css_lines.append(
                    f"  {min(visible_start, 99.99):.2f}% {{ opacity: 1; visibility: visible; }}"
                )
                css_lines.append(f"  {min(visible_end, 99.99):.2f}% {{ opacity: 1; }}")
                if end_pct < 100:
                    css_lines.append(f"  {min(end_pct, 99.99):.2f}% {{ opacity: 0; visibility: hidden; }}")
                    css_lines.append("  100% { opacity: 0; visibility: hidden; }")
                else:
                    css_lines.append("  100% { opacity: 0; visibility: hidden; }")
            css_lines.append("}")
            css_lines.append(
                f".mf.mf{i} {{ animation: {kf_name} {total_duration:.1f}s infinite; }}"
            )

        # Dark mode support (prefers-color-scheme works inside SVG on GitHub)
        css_lines.append("@media (prefers-color-scheme: dark) {")
        css_lines.append("  .wc-bg { fill: #0d1117; }")
        css_lines.append("  .algo-label rect { fill: #1a1a2e; fill-opacity: 0.85; stroke: #333; }")
        css_lines.append("  .algo-label text { fill: #ccc; }")
        css_lines.append("}")

        css = "\n".join(css_lines)

        # -- Build SVG ----------------------------------------------------
        svg_parts: list[str] = [
            f'<svg xmlns="http://www.w3.org/2000/svg"'
            f' width="{self.width}" height="{self.height}"'
            f' viewBox="0 0 {self.width} {self.height}">',
            "<defs>",
        ]

        # Two shared filters (not per-frame copies)
        svg_parts.append(
            '  <filter id="wc-glow" x="-30%" y="-30%" width="160%" height="160%">'
        )
        svg_parts.append(
            '    <feGaussianBlur in="SourceGraphic" stdDeviation="2.5" result="glow1"/>'
        )
        svg_parts.append(
            '    <feGaussianBlur in="SourceGraphic" stdDeviation="0.8" result="glow2"/>'
        )
        svg_parts.append("    <feMerge>")
        svg_parts.append('      <feMergeNode in="glow1"/>')
        svg_parts.append('      <feMergeNode in="glow2"/>')
        svg_parts.append('      <feMergeNode in="SourceGraphic"/>')
        svg_parts.append("    </feMerge>")
        svg_parts.append("  </filter>")
        svg_parts.append(
            '  <filter id="wc-shadow" x="-10%" y="-10%" width="120%" height="120%">'
        )
        svg_parts.append(
            '    <feDropShadow dx="0" dy="1" stdDeviation="0.5" flood-color="#00000020"/>'
        )
        svg_parts.append("  </filter>")

        # Background gradient (light mode)
        svg_parts.append('  <radialGradient id="wc-bg-grad" cx="50%" cy="50%" r="75%">')
        svg_parts.append(
            '    <stop offset="0%" stop-color="#fafbfc" stop-opacity="1"/>'
        )
        svg_parts.append(
            '    <stop offset="100%" stop-color="#f0f1f3" stop-opacity="1"/>'
        )
        svg_parts.append("  </radialGradient>")
        svg_parts.append("</defs>")
        svg_parts.append(f"<style>\n{css}\n</style>")

        # Background rect (class for dark mode override)
        svg_parts.append(
            f'<rect class="wc-bg" width="{self.width}" height="{self.height}" fill="url(#wc-bg-grad)"/>'
        )

        # Frame groups
        for i, body in enumerate(frame_bodies):
            svg_parts.append(f'<g class="mf mf{i}">')
            svg_parts.append(body)
            svg_parts.append("</g>")

        svg_parts.append("</svg>")
        return "\n".join(svg_parts)

    def place_words(
        self,
        frequencies: dict[str, float],
    ) -> list[PlacedWord]:
        """Place words using the first metaheuristic solver (Harmony Search).

        For the animated version, use generate() directly.
        """
        if not frequencies:
            return []
        texts, sizes, _, colors, weights, opacities = self._prepare_words(frequencies)
        if not texts:
            return []
        configure_layout_readability(self.layout_readability)
        rng = random.Random(self.seed)
        positions = _solve_harmony_search(
            len(texts),
            sizes,
            float(self.width),
            float(self.height),
            self.max_iter,
            rng,
            texts,
        )
        return self._render_frame(
            "Harmony Search", positions, texts, sizes, colors, weights, opacities
        )

    def generate(
        self,
        frequencies: dict[str, float],
        palette: str | None = None,
        source: str | None = None,
    ) -> str:
        """Generate animated SVG with all 25 metaheuristic algorithm frames.

        Each frame uses a monotonic OKLCH hue advance (~1.6° per frame,
        ~40° total) from the base palette, creating a subtle chromatic
        arc as different algorithms explore the solution space.

        Parameters
        ----------
        frequencies : dict mapping word text to frequency count.
        palette : optional color palette name (uses constructor default if None).
        source : optional source label (unused, for API compatibility).
        """
        if palette is not None:
            self.color_func = COLOR_FUNCS.get(palette, self.color_func)
            self.color_func_name = palette

        if not frequencies:
            return '<svg xmlns="http://www.w3.org/2000/svg"></svg>'

        texts, sizes, _, _base_colors, weights, opacities = self._prepare_words(
            frequencies
        )
        if not texts:
            return '<svg xmlns="http://www.w3.org/2000/svg"></svg>'
        logger.info(
            "MetaheuristicAnimRenderer: solving {n} words with 25 algorithms",
            n=len(texts),
        )

        all_results = self._solve_all(texts, sizes)

        # Optimize frame ordering for smoothest visual transitions
        order = self._optimize_frame_order(all_results)
        ordered_results = [all_results[i] for i in order]

        # Determine base palette name for hue shifting
        base_palette = getattr(self, "color_func_name", "ocean") or "ocean"
        total = len(texts)
        _GOLDEN_ANGLE_FRAC = (math.sqrt(5) - 1) / 2

        frame_bodies: list[str] = []
        algo_names: list[str] = []
        n_frames = len(ordered_results)

        for frame_idx, (name, positions) in enumerate(ordered_results):
            # Per-frame hue shift: monotonic advance through OKLCH space
            hue_offset = _frame_hue_offset(frame_idx, n_frames)
            shifted_func = make_shifted_color_func(base_palette, hue_offset)

            # Regenerate colors with shifted palette
            colors = []
            for word_idx in range(total):
                color_idx = int(((word_idx * _GOLDEN_ANGLE_FRAC) % 1.0) * total)
                colors.append(shifted_func(color_idx, total))

            placed = self._render_frame(
                name,
                positions,
                texts,
                sizes,
                colors,
                weights,
                opacities,
            )
            body = self._render_frame_svg_body(
                placed,
                name,
                len(frame_bodies),
            )
            frame_bodies.append(body)
            algo_names.append(name)

        return self._stack_frames(frame_bodies, algo_names)

    @staticmethod
    def _layout_distance(
        a: list[tuple[float, float, float]],
        b: list[tuple[float, float, float]],
    ) -> float:
        """Visual distance between two layouts.

        Sum of Euclidean displacements for each word plus a rotation
        penalty.  Smaller distance = more similar layouts = smoother
        transition.
        """
        total = 0.0
        for (ax, ay, ar), (bx, by, br) in zip(a, b):
            dx = ax - bx
            dy = ay - by
            dr = (ar - br) * 2.0  # rotation diff weighted higher
            total += math.sqrt(dx * dx + dy * dy + dr * dr)
        return total

    def _optimize_frame_order(
        self,
        results: list[tuple[str, list[tuple[float, float, float]]]],
    ) -> list[int]:
        """Solve TSP on the frame distance matrix using simulated
        annealing to find the ordering with smoothest visual transitions.
        """
        n = len(results)
        if n <= 2:
            return list(range(n))

        # Build distance matrix
        positions = [r[1] for r in results]
        dist = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                d = self._layout_distance(positions[i], positions[j])
                dist[i][j] = d
                dist[j][i] = d

        def tour_cost(order: list[int]) -> float:
            return sum(dist[order[k]][order[(k + 1) % n]] for k in range(n))

        # SA for TSP: start with nearest-neighbor heuristic
        rng = random.Random(42)
        visited = [False] * n
        order = [0]
        visited[0] = True
        for _ in range(n - 1):
            last = order[-1]
            best_next = -1
            best_d = float("inf")
            for j in range(n):
                if not visited[j] and dist[last][j] < best_d:
                    best_d = dist[last][j]
                    best_next = j
            order.append(best_next)
            visited[best_next] = True

        current_cost = tour_cost(order)
        best_cost = current_cost
        best_order = list(order)
        temp = current_cost * 0.3
        cooling = 0.995

        for _ in range(5000):
            # 2-opt swap
            i = rng.randint(0, n - 2)
            j = rng.randint(i + 1, n - 1)
            order[i : j + 1] = reversed(order[i : j + 1])
            c = tour_cost(order)
            delta = c - current_cost
            if delta < 0 or rng.random() < math.exp(-delta / max(temp, 1e-10)):
                current_cost = c
                if current_cost < best_cost:
                    best_cost = current_cost
                    best_order = list(order)
            else:
                order[i : j + 1] = reversed(order[i : j + 1])
            temp *= cooling

        logger.info(
            "Frame ordering optimized: tour cost {c:.0f} (SA-TSP, 5000 iterations)",
            c=best_cost,
        )
        return best_order


def _frame_hue_offset(frame_idx: int, total_frames: int) -> float:
    """Compute monotonic OKLCH hue rotation for a frame.

    ~1.6° per frame, ~40° total across all frames.  Creates a subtle
    chromatic arc: the word cloud *breathes* through color space as
    different algorithms explore the solution space.
    """
    if total_frames <= 1:
        return 0.0
    return (frame_idx / (total_frames - 1)) * 40.0


RENDERERS: dict[str, type[SvgWordCloudEngine]] = {
    "wordle": WordleRenderer,
    "clustered": ClusteredRenderer,
    "typographic": TypographicRenderer,
    "shaped": ShapedRenderer,
    "metaheuristic-anim": MetaheuristicAnimRenderer,
}


def get_renderer(name: str, **kwargs) -> SvgWordCloudEngine:
    """Factory: create a renderer by name."""
    cls = RENDERERS.get(name)
    if cls is None:
        raise ValueError(
            f"Unknown renderer {name!r}. Choose from: {', '.join(RENDERERS)}"
        )
    return cls(**kwargs)
