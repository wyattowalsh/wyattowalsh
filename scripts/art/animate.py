"""
Generate growth animation GIFs or animated SVGs for both art styles.

GIF mode: interpolates maturity from near-zero to target, renders each
frame via cairosvg, and assembles into an animated GIF.

SVG mode (--svg): generates N static SVGs at increasing maturity levels,
then stacks them in a single SVG with CSS-timed overlays so the artwork
genuinely evolves from bare soil to its final state.

Usage:
  uv run python -m scripts.art.animate [--profile NAME] [--frames N] [--size PX] [--only inkgarden|topo]
  uv run python -m scripts.art.animate --svg [--profile NAME] [--frames N] [--only inkgarden|topo]
"""
from __future__ import annotations

import io
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from ..utils import get_logger
from . import ink_garden, topography
from ._dev_profiles import PROFILES
from .shared import compute_maturity, normalize_live_metrics, parse_cli_args, seed_hash

logger = get_logger(module=__name__)

# ---------------------------------------------------------------------------
# Animation helpers
# ---------------------------------------------------------------------------

_SVG_OPEN_RE = re.compile(r"<svg\s([^>]+)>")
_DEFS_RE = re.compile(r"<defs>.*?</defs>", re.DOTALL)
_ID_ATTR_RE = re.compile(r'\bid="([^"]+)"')
_HREF_FRAG_RE = re.compile(r'\bhref="#([^"]+)"')
_URL_FRAG_RE = re.compile(r'\burl\(#([^)]+)\)')
_BODY_EXTRACT_RE = re.compile(
    r"</defs>\s*(?:<style[^>]*>.*?</style>\s*)?",
    re.DOTALL,
)


def _namespace_ids(body: str, frame_idx: int) -> str:
    """Rename all id="X" → id="X_fN" and their references within a frame body."""
    suffix = f"_f{frame_idx}"
    body = _ID_ATTR_RE.sub(lambda m: f'id="{m.group(1)}{suffix}"', body)
    body = _HREF_FRAG_RE.sub(lambda m: f'href="#{m.group(1)}{suffix}"', body)
    body = _URL_FRAG_RE.sub(lambda m: f'url(#{m.group(1)}{suffix})', body)
    return body


def ease_in_out(t: float) -> float:
    """Cubic ease-in-out: slower at extremes, more frames mid-range."""
    if t < 0.5:
        return 4 * t * t * t
    return 1 - (-2 * t + 2) ** 3 / 2


def narrative_timing(t: float) -> float:
    """Three-act narrative timing curve for 30s growth loop.

    Maps normalized time t in [0,1] to normalized progress:
      - Act 1 (0-17%  / 0-5s):  slow emergence — roots, base terrain
      - Act 2 (17-67% / 5-20s): accelerating growth — branches, vegetation
      - Act 3 (67-100% / 20-30s): dramatic finish — blooms, snow, chrome
    Uses smoothstep blending between piecewise segments for continuity.
    """
    if t < 0.0:
        return 0.0
    if t > 1.0:
        return 1.0
    if t < 0.167:
        # Act 1: gentle quadratic ease-in (slow start)
        s = t / 0.167
        return 0.10 * s * s
    if t < 0.667:
        # Act 2: accelerating cubic (the main growth phase)
        s = (t - 0.167) / 0.5
        return 0.10 + 0.55 * (3 * s * s - 2 * s * s * s)
    # Act 3: dramatic ease-out (flourishing, details emerge)
    s = (t - 0.667) / 0.333
    return 0.65 + 0.35 * (1 - (1 - s) * (1 - s))


# CSS cubic-bezier strings for each narrative act
_ACT_EASING = {
    1: "cubic-bezier(0.25, 0.1, 0.25, 1.0)",    # gentle ease-out (roots)
    2: "cubic-bezier(0.42, 0.0, 0.58, 1.0)",     # ease-in-out (growth)
    3: "cubic-bezier(0.34, 1.56, 0.64, 1.0)",    # overshoot (dramatic arrival)
}


def _frame_act(delay: float, total: float) -> int:
    """Determine which narrative act a frame belongs to based on its delay."""
    frac = delay / max(0.001, total)
    if frac < 0.167:
        return 1
    if frac < 0.667:
        return 2
    return 3


def _extract_svg_parts(svg: str) -> tuple[str, str, str]:
    """Split an SVG string into (svg_attrs, defs_block, body_content)."""
    m = _SVG_OPEN_RE.search(svg)
    attrs = m.group(1) if m else ""
    dm = _DEFS_RE.search(svg)
    defs = dm.group(0) if dm else ""
    # Body = everything after </defs> (and optional trailing <style>) up to </svg>
    m_body = _BODY_EXTRACT_RE.search(svg)
    body_start = m_body.end() if m_body else 0
    svg_close = svg.rfind("</svg>")
    body = svg[body_start: svg_close if svg_close >= 0 else len(svg)]
    return attrs, defs, body


def _build_stacked_svg(
    frame_svgs: list[str],
    delays: list[float],
    transition: float = 1.2,
    total_duration: float = 30.0,
) -> str:
    """Stack N SVG frames into a single animated SVG.

    Each frame overlays the previous via CSS opacity animation with
    narrative timing: act-specific cubic-bezier easing so early frames
    emerge gently and later frames arrive with dramatic impact.

    Pure CSS @keyframes only -- no JS, no SMIL.
    """
    n = len(frame_svgs)
    parts = [_extract_svg_parts(svg) for svg in frame_svgs]

    # SVG wrapper attrs from first frame; defs from last (most complete)
    svg_attrs = parts[0][0]
    defs = parts[-1][1]

    # Per-act @keyframes with tailored opacity curves
    css_lines = [
        "/* Narrative growth animation: 3-act timing */",
        ".f{opacity:0}",
        ".f0{opacity:1}",
        # Act 1 keyframes: gentle fade-in (roots/terrain emerge slowly)
        "@keyframes emerge{0%{opacity:0}40%{opacity:0.3}100%{opacity:1}}",
        # Act 2 keyframes: confident build (standard opacity ramp)
        "@keyframes grow{from{opacity:0}to{opacity:1}}",
        # Act 3 keyframes: dramatic reveal with slight overshoot
        "@keyframes bloom{0%{opacity:0}70%{opacity:1}85%{opacity:0.95}100%{opacity:1}}",
    ]

    for i in range(1, n):
        act = _frame_act(delays[i], total_duration)
        easing = _ACT_EASING[act]
        # Act 1 gets longer transitions for gentle emergence
        # Act 3 gets slightly longer for dramatic impact
        act_dur = {1: transition * 1.5, 2: transition, 3: transition * 1.3}[act]
        kf_name = {1: "emerge", 2: "grow", 3: "bloom"}[act]
        css_lines.append(
            f".f{i}{{animation:{kf_name} {act_dur:.1f}s {delays[i]:.1f}s {easing} both}}"
        )

    css = "\n".join(css_lines)

    out = [f"<svg {svg_attrs}>", defs, f"<style>\n{css}\n</style>"]
    for i, (_, _, body) in enumerate(parts):
        body = _namespace_ids(body, i)
        out.append(f'<g class="f f{i}">')
        out.append(body)
        out.append("</g>")
    out.append("</svg>")
    return "\n".join(out)


def svg_to_png(svg_str: str, size: int, frame_id: str = ""):
    """Convert SVG string to PIL Image at given size. Returns None on failure."""
    from PIL import Image

    try:
        try:
            import cairosvg

            png_data = cairosvg.svg2png(
                bytestring=svg_str.encode("utf-8"),
                output_width=size,
                output_height=size,
            )
        except (ImportError, OSError) as exc:
            rsvg_convert = shutil.which("rsvg-convert")
            if not rsvg_convert:
                raise RuntimeError("Neither cairosvg nor rsvg-convert is available") from exc

            with tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False) as tmp_svg:
                tmp_svg.write(svg_str)
                tmp_svg_path = Path(tmp_svg.name)
            try:
                result = subprocess.run(
                    [
                        rsvg_convert,
                        "-w",
                        str(size),
                        "-h",
                        str(size),
                        str(tmp_svg_path),
                    ],
                    check=True,
                    capture_output=True,
                )
            finally:
                tmp_svg_path.unlink(missing_ok=True)
            png_data = result.stdout
        return Image.open(io.BytesIO(png_data)).convert("RGBA")
    except Exception as exc:
        logger.error("SVG-to-PNG failed for {}: {}", frame_id, exc)
        debug_path = Path(f"/tmp/debug-{frame_id}.svg")
        debug_path.write_text(svg_str, encoding="utf-8")
        logger.info("Dumped failing SVG to {}", debug_path)
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    opts = parse_cli_args(
        sys.argv[1:],
        extra_keys={
            "frames": int, "size": int, "svg": bool,
            "metrics_path": str, "history_path": str,
        },
    )
    profile = opts["profile"] or "wyatt"
    n_frames = opts.get("frames") or 24
    size = opts.get("size") or 400
    only = opts["only"]

    metrics_file = opts.get("metrics_path")
    history_file = opts.get("history_path")

    if metrics_file:
        import json

        try:
            raw = json.loads(Path(str(metrics_file)).read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load metrics from {}: {}. Falling back to mock profiles.", metrics_file, exc)
            raw = None

        if raw is not None:
            history = None
            if history_file:
                try:
                    history = json.loads(Path(str(history_file)).read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError) as exc:
                    logger.warning("Failed to load history from {}: {}", history_file, exc)
            target = normalize_live_metrics(raw, owner=str(profile), history=history)
            logger.info("Loaded live metrics from {}", metrics_file)
        else:
            if profile not in PROFILES:
                logger.error("No valid metrics and unknown profile: {}. Available: {}", profile, list(PROFILES.keys()))
                return
            target = PROFILES[profile]
    elif profile in PROFILES:
        target = PROFILES[profile]
    else:
        logger.error("Unknown profile: {} and no --metrics-path given. Available: {}", profile, list(PROFILES.keys()))
        return

    fixed_seed = seed_hash(target)
    target_mat = compute_maturity(target)
    out_dir = Path(".github/assets/img")
    out_dir.mkdir(parents=True, exist_ok=True)

    generators = {}
    if only != "topo":
        generators["inkgarden"] = ("inkgarden-growth", ink_garden.generate)
    if only != "inkgarden":
        generators["topo"] = ("topo-growth", topography.generate)

    # ── Animated SVG mode (multi-frame stacking) ──────────────
    if opts.get("svg"):
        svg_frames = opts.get("frames") or 7
        total_dur = 60.0
        logger.info(
            "SVG mode: profile={}  target_mat={:.3f}  frames={}",
            profile, target_mat, svg_frames,
        )

        for key, (slug, gen_fn) in generators.items():
            frame_svgs: list[str] = []
            delays: list[float] = []

            for fi in range(svg_frames):
                raw_t = fi / max(1, svg_frames - 1)
                # Use narrative timing for maturity progression:
                # slow start (roots), accelerating middle, dramatic finish
                t = narrative_timing(raw_t)
                mat = 0.02 + (target_mat - 0.02) * t
                # Delays follow the narrative curve too — early frames linger,
                # middle frames arrive faster, final frames have breathing room
                delay = narrative_timing(raw_t) * total_dur * 0.85 if fi > 0 else 0.0
                # First frame at t=0 always starts immediately
                logger.info(
                    "  {} frame {:2d}/{}  mat={:.3f}  delay={:.1f}s  act={}",
                    slug, fi + 1, svg_frames, mat, delay,
                    _frame_act(delay, total_dur),
                )

                kw: dict[str, object] = {"seed": fixed_seed, "maturity": mat}
                if key == "topo":
                    kw["chrome_maturity"] = target_mat
                    kw["timeline"] = False
                frame_svgs.append(gen_fn(target, **kw))
                delays.append(delay)

            animated_svg = _build_stacked_svg(frame_svgs, delays, total_duration=total_dur)
            out_path = out_dir / f"{slug}-animated.svg"
            out_path.write_text(animated_svg, encoding="utf-8")
            size_kb = out_path.stat().st_size // 1024
            logger.info("{}: {} KB ({} frames) -> {}", slug, size_kb, svg_frames, out_path)

        logger.info("Done (animated SVGs)")
        return

    # ── GIF mode ──────────────────────────────────────────────
    from PIL import Image

    logger.info("Profile: {}  target_mat={:.3f}  frames={}", profile, target_mat, n_frames)

    # Generate frames — same metrics every frame, only maturity changes
    frames: dict[str, list[Image.Image]] = {k: [] for k in generators}

    for fi in range(n_frames):
        raw_t = fi / max(1, n_frames - 1)
        t = narrative_timing(raw_t)
        # Interpolate maturity from near-zero to target using narrative curve
        mat = 0.02 + (target_mat - 0.02) * t
        logger.info("Frame {:2d}/{}  t={:.3f}  mat={:.3f}", fi + 1, n_frames, t, mat)

        for key, (slug, gen_fn) in generators.items():
            kw: dict[str, object] = {"seed": fixed_seed, "maturity": mat}
            if key == "topo":
                kw["chrome_maturity"] = target_mat  # chrome always full
                kw["timeline"] = False
            svg = gen_fn(target, **kw)
            img = svg_to_png(svg, size, frame_id=f"{slug}-f{fi:02d}")
            if img is not None:
                frames[key].append(img)

    # Assemble GIFs
    for key, (slug, _) in generators.items():
        imgs = frames[key]
        if not imgs:
            continue

        # Convert RGBA -> palettized with Floyd-Steinberg dithering for smoother GIF
        pal_imgs = [
            img.convert("RGB").quantize(
                colors=256,
                method=Image.Quantize.MEDIANCUT,
                dither=Image.Dither.FLOYDSTEINBERG,
            )
            for img in imgs
        ]

        # Narrative-paced frame durations: slow start, faster middle, dramatic hold
        n_pal = len(pal_imgs)
        durations = []
        for fi_d in range(n_pal):
            frac = fi_d / max(1, n_pal - 1)
            if frac < 0.167:
                durations.append(450)    # Act 1: linger on emergence
            elif frac < 0.667:
                durations.append(250)    # Act 2: faster growth
            else:
                durations.append(350)    # Act 3: dramatic but not rushed
        durations[-1] = 2000  # Hold final frame

        out_path = out_dir / f"{slug}.gif"
        pal_imgs[0].save(
            out_path,
            save_all=True,
            append_images=pal_imgs[1:],
            duration=durations,
            loop=0,
            optimize=True,
        )
        size_kb = out_path.stat().st_size // 1024
        logger.info("{}: {} KB -> {}", slug, size_kb, out_path)

    logger.info("Done")


if __name__ == "__main__":
    main()
