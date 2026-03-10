"""
Thin runner for modular art prototypes.
Usage: uv run python -m scripts.art.run_prototypes [--only inkgarden|topo] [--profile NAME]
"""
from __future__ import annotations

import sys
from pathlib import Path

from .shared import PROFILES, parse_cli_args
from . import ink_garden, topography
from ..utils import get_logger

logger = get_logger(module=__name__)

GENERATORS = {
    "inkgarden": ("inkgarden-ult", ink_garden.generate),
    "topo": ("topo-ult", topography.generate),
}


def main() -> None:
    opts = parse_cli_args(sys.argv[1:])
    only = opts["only"]
    profile_filter = opts["profile"]

    out_dir = Path(".github/assets/img")
    out_dir.mkdir(parents=True, exist_ok=True)

    profiles = PROFILES
    if profile_filter:
        profiles = {k: v for k, v in PROFILES.items() if k == profile_filter}
        if not profiles:
            logger.error("Unknown profile: {}. Available: {}", profile_filter, list(PROFILES.keys()))
            return

    gens = GENERATORS
    if only:
        gens = {k: v for k, v in GENERATORS.items() if k == only}
        if not gens:
            logger.error("Unknown generator: {}. Available: {}", only, list(GENERATORS.keys()))
            return

    for pname, metrics in profiles.items():
        logger.info("--- {} ---", metrics["label"])
        for key, (slug, gen_fn) in gens.items():
            svg = gen_fn(metrics)
            out = out_dir / f"proto-v10-{slug}-{pname}.svg"
            out.write_text(svg, encoding="utf-8")
            logger.info("  {}: {} KB -> {}", slug, len(svg) // 1024, out)

    logger.info("Done")


if __name__ == "__main__":
    main()
