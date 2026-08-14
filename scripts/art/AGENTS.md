# scripts/art/AGENTS.md

> Living-art / generative-art subpackage. Parent: [../AGENTS.md](../AGENTS.md) · [../../AGENTS.md](../../AGENTS.md)

## Layout

```text
scripts/art/
├── shared/                 # Shared utilities package (compat: scripts.art.shared)
│   ├── __init__.py         # Re-exports public API for existing imports
│   ├── constants.py        # WIDTH/HEIGHT, LANG_HUES, MAX_REPOS
│   ├── timeline.py         # Date windows + monthly→daily series
│   ├── world_state.py      # compute_maturity, WorldState, compute_world_state
│   ├── metrics.py          # Payload contracts + normalize_live_metrics
│   ├── seeds.py            # seed_hash / hex_frac / parse_cli_args
│   ├── color.py            # OKLCH, contrast, HSL helpers
│   ├── noise.py            # Noise2D + presets
│   ├── math_helpers.py     # Phyllotaxis / flow-field geometry
│   ├── svg.py              # SVG markup, filters, weather, SMIL
│   ├── palette.py          # ART_PALETTE_ANCHORS + extended palettes
│   ├── visual.py           # Repo layout, DerivedMetrics, ElementBudget
│   └── accretion.py        # Shared daily-spine channels + style dialects
├── timelapse.py            # Style registry + GIF driver (SSOT for ALL_STYLES)
├── daily_snapshots.py      # Day-by-day snapshot evolution
├── artifacts.py            # Manifest / gallery / docs-showcase sync
├── _gif_optimize.py         # Pixel-exact, smaller-only GIF post-processing
├── animate.py              # Multi-frame maturity animation driver
├── optimize.py             # Aesthetic cost helpers
├── _dev_profiles.py        # Mock profiles for local testing
├── ink_garden.py           # Botanical generator
├── topography.py           # Cartographic generator
├── genetic_landscape.py    # Adaptive-landscape generator
├── physarum.py             # Physarum network generator
├── lenia.py                # Continuous CA generator
└── ferrofluid.py           # Magnetic-fluid generator
```

## Import contract

Prefer the stable surface:

```python
from .shared import WorldState, compute_world_state, oklch, seed_hash
```

Focused submodule imports are allowed when a caller only needs one concern:

```python
from .shared.color import oklch
from .shared.world_state import WorldState
```

Do **not** reintroduce a monolithic `shared.py` beside this package — `scripts.art.shared` is the package.

## Style registry SSOT

Canonical style names and GIF filenames live in `timelapse.py` (`_STYLE_REGISTRY` / `ALL_STYLES`).
Human-readable matrix: [`docs/content/docs/scripts/living-art-modes.mdx`](../../docs/content/docs/scripts/living-art-modes.mdx).
Shared atmosphere semantics: [`docs/content/docs/scripts/world-state.mdx`](../../docs/content/docs/scripts/world-state.mdx).

Published timelapses are optionally post-processed by `_gif_optimize.py`. A
candidate replaces its source only when it is smaller and preserves dimensions,
frame count, per-frame duration, loop behavior, and every composited RGBA frame.
CI installs `gifsicle`; local generation safely retains the source when the tool
is unavailable or any contract check fails.

Repository-owned writers use a stable same-host advisory lock plus a unique
private same-directory stage. The public GIF changes once only after the staged
candidate passes complete validation. This does not claim cross-host/NFS
serialization or power-loss durability.

`artifacts.stage_living_art_fleet()` creates the exact-six, media-only workflow
handoff. `artifacts.publish_living_art_fleet()` treats that stage as untrusted,
validates inventory, animation runtime, media, and budgets before destination
mutation, regenerates both manifest/gallery surfaces and the docs mirror, and
then verifies persisted parity. If a mutation-phase write fails, it restores
both managed surfaces to their pre-call state while preserving unmanaged files.
Never transfer manifests or galleries between jobs as an independent authority.
Manifest v2 descriptors retain ordered positive per-frame durations as well as
their frame count and aggregate runtime so the finalizer can re-prove the same
animation contract after artifact transfer.

## Generator contract

Each style module exposes:

```python
def generate(metrics: dict, *, seed: str | None = None, maturity: float | None = None) -> str:
    """Return a complete SVG document string."""
```

Generators should:

1. Call `resolve_render_metrics(metrics)` when reading timelapse envelopes.
2. Derive atmosphere via `compute_world_state(...)`.
3. Keep repo visual order via `order_repos_for_visual_plan` / `stable_repo_visual_order`.
