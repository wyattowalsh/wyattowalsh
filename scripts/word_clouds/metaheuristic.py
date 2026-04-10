"""Metaheuristic animated word cloud renderer and renderer registry."""

from __future__ import annotations

import math
import os
import random
from concurrent.futures import ProcessPoolExecutor, as_completed

from ..utils import get_logger
from .clustered import ClusteredRenderer
from .colors import COLOR_FUNCS, make_shifted_color_func
from .core import PlacedWord
from .engine import SvgWordCloudEngine
from .readability import LayoutReadabilityPolicy, LayoutReadabilitySettings
from .shaped import ShapedRenderer
from .solvers import (
    _META_SOLVERS,
    _clamp_solution,
    configure_layout_readability,
)
from .typographic import TypographicRenderer
from .wordle import WordleRenderer

logger = get_logger(module=__name__)

LayoutReadabilityConfig = (
    LayoutReadabilityPolicy | LayoutReadabilitySettings | dict[str, object] | None
)


def _build_family_map() -> dict[str, str]:
    """Map solver names to algorithm families from mealpy module paths."""
    families: dict[str, str] = {}
    try:
        from mealpy import get_all_optimizers

        all_opts = get_all_optimizers(verbose=False)
        for name, cls in all_opts.items():
            module = cls.__module__  # e.g. "mealpy.swarm_based.PSO"
            parts = module.split(".")
            if len(parts) >= 2:
                families[name] = parts[1].replace("_based", "")
            else:
                families[name] = "unknown"
    except Exception:
        pass
    return families


_SOLVER_FAMILIES: dict[str, str] = _build_family_map()


def _run_solver(args):
    """Worker function for parallel solver execution (top-level for pickling)."""
    (name, n_words, sizes, canvas_w, canvas_h, max_iter, pop_size, seed,
     texts, layout_readability, cost_weights) = args
    configure_layout_readability(layout_readability, word_sizes=sizes)
    solver_fn = _META_SOLVERS[name]
    rng = random.Random(seed)
    placements = solver_fn(
        n_words, sizes, canvas_w, canvas_h, max_iter, rng, texts,
        pop_size=pop_size, cost_weights=cost_weights,
    )
    return name, placements


class MetaheuristicAnimRenderer(SvgWordCloudEngine):
    """Animated word cloud showing all registered metaheuristic optimization algorithms.

    Each algorithm solves the same word placement problem, producing a frame.
    All frames are stacked in a single SVG with CSS opacity animation
    that cycles through them infinitely.
    """

    def __init__(
        self,
        *,
        hold_duration: float = 1.8,
        fade_duration: float = 0.2,
        pop_size: int = 20,
        max_iter: int = 300,
        max_solvers: int | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.hold_duration = hold_duration
        self.fade_duration = fade_duration
        self.pop_size = pop_size
        self.max_iter = max_iter
        self.max_solvers = max_solvers

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
        """Run all metaheuristic solvers and return their placement results."""
        n_words = len(texts)
        canvas_w = float(self.width)
        canvas_h = float(self.height)

        # Select solvers: either all or a random subset.
        # Supports WORDCLOUD_MAX_SOLVERS env var for CI timeout control.
        solver_names = list(_META_SOLVERS.keys())
        effective_max_solvers = self.max_solvers
        if effective_max_solvers is None:
            env_max = os.environ.get("WORDCLOUD_MAX_SOLVERS")
            if env_max is not None:
                effective_max_solvers = int(env_max)
        if effective_max_solvers is not None and effective_max_solvers < len(solver_names):
            weight_rng_seed = self.seed if self.seed else 42
            subset_rng = random.Random(weight_rng_seed)
            solver_names = sorted(subset_rng.sample(solver_names, effective_max_solvers))
            logger.info(
                "Using {n}/{total} solvers (max_solvers={m})",
                n=len(solver_names), total=len(_META_SOLVERS), m=effective_max_solvers,
            )

        # Per-solver weight perturbation: Gaussian noise on soft cost components
        # to produce diverse layouts exploring the aesthetic Pareto front.
        DEFAULT_WEIGHTS = {
            "packing": 3.0, "balance": 2.0, "uniformity": 2.0,
            "reading_flow": 2.25, "landscape": 1.0, "size_gradient": 1.0,
        }
        weight_rng = random.Random(self.seed if self.seed else 42)
        solver_weights: list[dict[str, float]] = []
        for _ in solver_names:
            w = {}
            for key, default in DEFAULT_WEIGHTS.items():
                noise = weight_rng.gauss(0, 0.3)
                w[key] = max(0.5, min(5.0, default + noise))
            solver_weights.append(w)

        # Build args for each solver (top-level worker for pickling)
        solver_args = [
            (
                name,
                n_words,
                sizes,
                canvas_w,
                canvas_h,
                self.max_iter,
                self.pop_size,
                self.seed,
                texts,
                self.layout_readability,
                weights,
            )
            for (name, weights) in zip(solver_names, solver_weights)
        ]

        n_workers = min(len(solver_args), os.cpu_count() or 4)
        logger.info(
            "Running {n} solvers across {w} workers",
            n=len(solver_args),
            w=n_workers,
        )

        results_by_name: dict[str, tuple[str, list[tuple[float, float, float]]]] = {}
        failed_args: list[tuple] = []

        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            future_to_args = {
                executor.submit(_run_solver, args): args for args in solver_args
            }
            for future in as_completed(future_to_args):
                args = future_to_args[future]
                name = args[0]
                try:
                    result = future.result()
                except Exception as exc:
                    logger.warning(
                        "MetaheuristicAnimRenderer: {name} worker failed; "
                        "retrying locally: {error}",
                        name=name,
                        error=exc,
                    )
                    failed_args.append(args)
                    continue

                results_by_name[name] = result
                logger.debug("MetaheuristicAnimRenderer: {name} completed", name=name)

        for args in failed_args:
            name = args[0]
            try:
                results_by_name[name] = _run_solver(args)
            except Exception as exc:
                logger.warning(
                    "MetaheuristicAnimRenderer: {name} local retry failed; "
                    "skipping frame: {error}",
                    name=name,
                    error=exc,
                )
                continue

            logger.debug(
                "MetaheuristicAnimRenderer: {name} completed via local retry",
                name=name,
            )

        results = [
            results_by_name[name]
            for name in _META_SOLVERS
            if name in results_by_name
        ]
        if not results:
            raise RuntimeError("All metaheuristic solvers failed")

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
            ".mf { opacity: 0; will-change: opacity; }",
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
                    f"  {visible_pct + fade_out_pct:.2f}% {{ opacity: 0; "
                    "visibility: hidden; }"
                )
                css_lines.append(
                    f"  {100 - fade_in_pct:.2f}% {{ opacity: 0; "
                    "visibility: hidden; }"
                )
                css_lines.append("  100% { opacity: 1; }")
            else:
                if start_pct > 0:
                    css_lines.append("  0% { opacity: 0; visibility: hidden; }")
                    css_lines.append(
                        f"  {start_pct:.2f}% {{ opacity: 0; "
                        "visibility: hidden; }"
                    )
                css_lines.append(
                    f"  {min(visible_start, 99.99):.2f}% {{ opacity: 1; "
                    "visibility: visible; }"
                )
                css_lines.append(f"  {min(visible_end, 99.99):.2f}% {{ opacity: 1; }}")
                # NOTE: The `}}` above is correct — it's inside an f-string, escaping to `}`
                if end_pct < 100:
                    css_lines.append(
                        f"  {min(end_pct, 99.99):.2f}% {{ opacity: 0; "
                        "visibility: hidden; }"
                    )
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
        css_lines.append(
            "  .algo-label rect { fill: #1a1a2e; fill-opacity: 0.85; "
            "stroke: #333; }"
        )
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
            "    <feDropShadow dx=\"0\" dy=\"1\" stdDeviation=\"0.5\" "
            'flood-color="#00000020"/>'
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
            f'<rect class="wc-bg" width="{self.width}" '
            f'height="{self.height}" fill="url(#wc-bg-grad)"/>'
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
        """Place words using the first registered metaheuristic solver.

        For the animated version, use generate() directly.
        """
        if not frequencies:
            return []
        texts, sizes, _, colors, weights, opacities = self._prepare_words(frequencies)
        if not texts:
            return []
        configure_layout_readability(self.layout_readability, word_sizes=sizes)
        rng = random.Random(self.seed)
        first_name = next(iter(_META_SOLVERS))
        solver_fn = _META_SOLVERS[first_name]
        positions = solver_fn(
            len(texts),
            sizes,
            float(self.width),
            float(self.height),
            self.max_iter,
            rng,
            texts,
        )
        return self._render_frame(
            first_name, positions, texts, sizes, colors, weights, opacities
        )

    def generate(
        self,
        frequencies: dict[str, float],
        palette: str | None = None,
        source: str | None = None,
    ) -> str:
        """Generate animated SVG with all registered metaheuristic algorithm frames.

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
            "MetaheuristicAnimRenderer: solving {n} words with {k} algorithms",
            n=len(texts),
            k=len(_META_SOLVERS),
        )

        all_results = self._solve_all(texts, sizes)
        self._log_diversity_baseline(all_results, sizes, texts)

        # Optimize frame ordering for smoothest visual transitions
        order = self._optimize_frame_order(all_results)
        ordered_results = [all_results[i] for i in order]

        # Nudge each frame toward its neighbors for smoother transitions
        ordered_results = self._refine_transitions(ordered_results, sizes, texts)

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

    def _log_diversity_baseline(
        self,
        results: list[tuple[str, list[tuple[float, float, float]]]],
        sizes: list[float],
        texts: list[str],
    ) -> None:
        """Log diversity metrics for the solver results as a diagnostic baseline."""
        n = len(results)
        if n < 2:
            return

        # Pairwise layout distances
        positions = [r[1] for r in results]
        distances: list[float] = []
        for i in range(n):
            for j in range(i + 1, n):
                distances.append(self._layout_distance(positions[i], positions[j]))

        mean_dist = sum(distances) / len(distances)
        min_dist = min(distances)
        max_dist = max(distances)
        variance = sum((d - mean_dist) ** 2 for d in distances) / len(distances)
        std_dist = variance**0.5

        # Per-frame cost (uses default weights — diagnostic only)
        from .solvers import _aesthetic_cost

        costs = []
        hard_violations = 0
        canvas_w = float(self.width)
        canvas_h = float(self.height)
        for _name, pos in results:
            cost = _aesthetic_cost(pos, sizes, canvas_w, canvas_h, texts)
            costs.append(cost)
            if cost >= 1000.0:
                hard_violations += 1

        mean_cost = sum(costs) / len(costs)
        min_cost = min(costs)
        max_cost = max(costs)

        logger.info(
            "Diversity baseline: {n} frames, "
            "layout distance mean={mean:.0f} std={std:.0f} "
            "min={min:.0f} max={max:.0f}, "
            "cost mean={cmean:.2f} min={cmin:.2f} max={cmax:.2f}, "
            "hard violations={hv}",
            n=n,
            mean=mean_dist,
            std=std_dist,
            min=min_dist,
            max=max_dist,
            cmean=mean_cost,
            cmin=min_cost,
            cmax=max_cost,
            hv=hard_violations,
        )

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

        # Build distance matrix with family cohesion bonus
        positions = [r[1] for r in results]
        names = [r[0] for r in results]
        dist = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                d = self._layout_distance(positions[i], positions[j])
                # Same family gets 10% distance discount for softer grouping
                if _SOLVER_FAMILIES.get(names[i]) == _SOLVER_FAMILIES.get(names[j]):
                    d *= 0.9
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

    def _refine_transitions(
        self,
        ordered: list[tuple[str, list[tuple[float, float, float]]]],
        sizes: list[float],
        texts: list[str],
    ) -> list[tuple[str, list[tuple[float, float, float]]]]:
        """Nudge each frame toward its neighbors for smoother animation transitions.

        For each frame, compute a target position that blends the current layout
        with adjacent frames. Run a short local refinement that balances aesthetic
        quality (70%) with transition smoothness (30%).
        """
        n = len(ordered)
        if n < 3:
            return ordered

        canvas_w = float(self.width)
        canvas_h = float(self.height)
        refined: list[tuple[str, list[tuple[float, float, float]]]] = []

        for i in range(n):
            name, positions = ordered[i]
            prev_pos = ordered[(i - 1) % n][1]
            next_pos = ordered[(i + 1) % n][1]
            n_words = len(positions)

            # Compute neighbor-weighted target: average of prev and next
            nudged: list[tuple[float, float, float]] = []
            for j in range(n_words):
                cx, cy, cr = positions[j]
                # Target = midpoint of prev and next frame positions for this word
                tx = (prev_pos[j][0] + next_pos[j][0]) / 2
                ty = (prev_pos[j][1] + next_pos[j][1]) / 2
                # Blend: 70% original, 30% neighbor target
                nx = cx * 0.7 + tx * 0.3
                ny = cy * 0.7 + ty * 0.3
                nudged.append((nx, ny, cr))  # keep rotation unchanged

            # Clamp to canvas bounds
            nudged = _clamp_solution(nudged, canvas_w, canvas_h)
            refined.append((name, nudged))

        logger.info("Transition refinement applied to {n} frames", n=n)
        return refined


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
