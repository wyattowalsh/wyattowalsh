"""Living-art candidate vs shipped roster (keys + legend slots).

``CANDIDATE_STYLE_KEYS`` is the generator registry / ``--only`` allowlist.
``SHIPPED_STYLE_KEYS`` is what README, CI, budgets, and default generate publish.

Until bake-off acceptance (K2 / S1) the two tuples are the same object: today's
six styles in registry order. Later waves import these names instead of copying
the six-list. Generators stay registered as candidates even after shrink.

README ``<details>`` legends live here (Wave RM M1): title, 1–2 sentence
metaphor, then repos/stars/commits/followers as that world's picture.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

# Generator registry / ``--only``. Do not delete styles from this tuple when
# shrinking daily CI — retire them from ``SHIPPED_STYLE_KEYS`` only (S1).
CANDIDATE_STYLE_KEYS: tuple[str, ...] = (
    "inkgarden",
    "topo",
    "genetic",
    "physarum",
    "lenia",
    "ferrofluid",
)

# README, CI matrix, byte budgets, default generate. Until K2 this *is*
# ``CANDIDATE_STYLE_KEYS`` (same six, same order). S1 rebinds to bake-off
# ``accepted`` (ordered subset, length 4–6).
SHIPPED_STYLE_KEYS: tuple[str, ...] = CANDIDATE_STYLE_KEYS


class StyleSignalMapping(BaseModel):
    """How repos, stars, commits, and followers read in one visual world."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    repos: str = Field(min_length=1)
    stars: str = Field(min_length=1)
    commits: str = Field(min_length=1)
    followers: str = Field(min_length=1)


class StyleLegend(BaseModel):
    """Per-style README ``<details>`` copy: title, metaphor, four-signal map."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    title: str = Field(min_length=1)
    metaphor: str = Field(min_length=1)
    mapping: StyleSignalMapping


def _legend(
    title: str,
    metaphor: str,
    *,
    repos: str,
    stars: str,
    commits: str,
    followers: str,
) -> StyleLegend:
    return StyleLegend(
        title=title,
        metaphor=metaphor,
        mapping=StyleSignalMapping(
            repos=repos,
            stars=stars,
            commits=commits,
            followers=followers,
        ),
    )


# One record per candidate slug. Insertion order must match
# ``CANDIDATE_STYLE_KEYS``. README ``<details>`` copy: title, metaphor, map.
STYLE_LEGENDS: dict[str, StyleLegend] = {
    "inkgarden": _legend(
        "Ink Garden",
        (
            "Each repository takes root as a tree, stem and canopy together. "
            "A day with no repos is bare soil."
        ),
        repos="plants — one tree per repository, stem and canopy",
        stars="bloom — flowers on the trees",
        commits="trunk — thicker, taller boles",
        followers="glints among the leaves (none at zero followers)",
    ),
    "topo": _legend(
        "Topography",
        (
            "A hand-drawn survey of this account, with one hill for every "
            "repository. The map fills in as the years accrue."
        ),
        repos="peaks — one hill per repository",
        stars="prominence — how tall each summit stands",
        commits="contours — the lines that mark each hill",
        followers="settlements on the map",
    ),
    "genetic": _legend(
        "Genetic Landscape",
        (
            "A landscape of competing fitness peaks, one ridge per repository. "
            "Life gathers on the high ground as the account evolves."
        ),
        repos="fitness peaks — one peak per repository",
        stars="peak height — how tall each summit stands",
        commits="generations stacked across the landscape",
        followers="colonies (none at zero followers)",
    ),
    "physarum": _legend(
        "Physarum",
        (
            "A slime mold feeding in the dark, spinning a living network from "
            "the first repository. The organism is the veins, not a lone spore."
        ),
        repos="nutrient nodes — a network grown from the first repository",
        stars="how rich each food node is",
        commits="trail and vein growth",
        followers="vein mass (not the spore)",
    ),
    "lenia": _legend(
        "Lenia",
        (
            "A continuous living field, seeded with one creature for every "
            "repository. Soft bodies pulse and wander as the account grows."
        ),
        repos="seed organisms — one body per repository",
        stars="halo — the glow around each creature",
        commits="field occupancy — how much of the medium is alive",
        followers="spatial extent — how far the field spreads",
    ),
    "ferrofluid": _legend(
        "Ferrofluid",
        (
            "Black magnetic fluid standing in towers, one column for every "
            "repository. The pool bristles, ripples, and holds a field of "
            "its own."
        ),
        repos="dipoles — one tower per repository",
        stars="spike height — how far the fluid leaps",
        commits="ripples in the pool",
        followers="magnetic field around the towers",
    ),
}


def legend_for(style: str) -> StyleLegend:
    """Return the legend record for one candidate (or shipped) style key."""
    try:
        return STYLE_LEGENDS[style]
    except KeyError as exc:
        raise KeyError(f"Unknown living-art style {style!r}") from exc


def shipped_legends() -> tuple[tuple[str, StyleLegend], ...]:
    """Ordered ``(key, legend)`` pairs for the shipped README / CI roster."""
    return tuple((key, STYLE_LEGENDS[key]) for key in SHIPPED_STYLE_KEYS)


def _validate_roster() -> None:
    """Fail closed if keys, order, or legend coverage drift."""
    if len(set(CANDIDATE_STYLE_KEYS)) != len(CANDIDATE_STYLE_KEYS):
        raise ValueError("CANDIDATE_STYLE_KEYS must be unique")
    if len(set(SHIPPED_STYLE_KEYS)) != len(SHIPPED_STYLE_KEYS):
        raise ValueError("SHIPPED_STYLE_KEYS must be unique")
    if not SHIPPED_STYLE_KEYS:
        raise ValueError("SHIPPED_STYLE_KEYS must not be empty")
    if len(SHIPPED_STYLE_KEYS) > 6:
        raise ValueError("SHIPPED_STYLE_KEYS must not exceed six styles")
    unknown_shipped = [
        key for key in SHIPPED_STYLE_KEYS if key not in CANDIDATE_STYLE_KEYS
    ]
    if unknown_shipped:
        raise ValueError(
            "SHIPPED_STYLE_KEYS contains keys that are not candidates: "
            f"{unknown_shipped!r}"
        )
    legend_keys = tuple(STYLE_LEGENDS)
    if legend_keys != CANDIDATE_STYLE_KEYS:
        raise ValueError(
            "STYLE_LEGENDS keys must match CANDIDATE_STYLE_KEYS in order "
            f"(got {legend_keys!r})"
        )


_validate_roster()


__all__ = [
    "CANDIDATE_STYLE_KEYS",
    "SHIPPED_STYLE_KEYS",
    "STYLE_LEGENDS",
    "StyleLegend",
    "StyleSignalMapping",
    "legend_for",
    "shipped_legends",
]
