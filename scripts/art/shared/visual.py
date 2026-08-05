"""Repo layout, derived metrics, and visual-parameter helpers."""

from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .constants import HEIGHT, MAX_REPOS, WIDTH
from .seeds import hex_frac

# ---------------------------------------------------------------------------
# GitHub data → visual parameters (Phase 6)
# ---------------------------------------------------------------------------


def visual_complexity(metrics: dict[str, Any]) -> float:
    """0.0-1.0 complexity score from language diversity (Shannon entropy).

    0 languages → 0.0, 1 language → 0.15, max entropy for 10 → 1.0.
    """
    entropy = metrics.get("language_diversity", 0.0)
    return min(1.0, entropy / 3.32)


def topic_affinity_matrix(
    repos: list[dict[str, Any]],
) -> dict[tuple[int, int], float]:
    """Return affinity scores (0-1) between repo pairs based on shared topics.

    High-affinity repos share many topics and should be placed near each other.
    """
    affinities: dict[tuple[int, int], float] = {}
    for i in range(len(repos)):
        topics_i = set(repos[i].get("topics", []))
        if not topics_i:
            continue
        for j in range(i + 1, len(repos)):
            topics_j = set(repos[j].get("topics", []))
            if not topics_j:
                continue
            shared = len(topics_i & topics_j)
            union = len(topics_i | topics_j)
            if shared > 0 and union > 0:
                affinities[(i, j)] = shared / union
    return affinities


def activity_tempo(contributions_monthly: dict[str, int] | None) -> float:
    """0.0-1.0 tempo from contribution pattern.

    Bursty → higher tempo (faster animations), steady → moderate tempo.
    Measured as coefficient of variation of monthly counts.
    """
    if not contributions_monthly:
        return 0.5
    counts = [v for v in contributions_monthly.values() if isinstance(v, int | float)]
    if len(counts) < 2:
        return 0.5
    mean = sum(counts) / len(counts)
    if mean <= 0:
        return 0.0
    variance = sum((c - mean) ** 2 for c in counts) / len(counts)
    cv = math.sqrt(variance) / mean
    return min(1.0, cv / 2.0)


def stable_repo_visual_order(
    repos: Sequence[Mapping[str, Any]],
    *,
    preferred_names: Sequence[str] | None = None,
) -> list[str]:
    """Build the stable all-repo order consumed by living-art renderers.

    The contract is exhaustive and monotonic: preferred names retain their
    relative order, and every remaining repo is appended the first time it
    appears in *repos*. Callers should therefore pass repos in the desired
    accretive order.
    """
    ordered_names: list[str] = []
    seen: set[str] = set()

    for raw_name in preferred_names or ():
        name = str(raw_name).strip() if isinstance(raw_name, str) else ""
        if not name or name in seen:
            continue
        seen.add(name)
        ordered_names.append(name)

    for repo in repos:
        name = str(repo.get("name") or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        ordered_names.append(name)

    return ordered_names


def order_repos_for_visual_plan(
    repos: Sequence[dict[str, Any]],
    *,
    preferred_names: Sequence[str] | None = None,
) -> list[dict[str, Any]]:
    """Return repos ordered under the stable all-repo representation contract."""
    ordered_repos = list(repos)
    if len(ordered_repos) <= 1:
        return ordered_repos

    plan = stable_repo_visual_order(ordered_repos, preferred_names=preferred_names)
    if not plan:
        return ordered_repos

    plan_index = {name: index for index, name in enumerate(plan)}
    sorted_pairs = sorted(
        enumerate(ordered_repos),
        key=lambda item: (
            plan_index.get(
                str(item[1].get("name") or "").strip(),
                len(plan_index) + item[0],
            ),
            item[0],
        ),
    )

    deduped: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    for _index, repo in sorted_pairs:
        name = str(repo.get("name") or "").strip()
        if name:
            if name in seen_names:
                continue
            seen_names.add(name)
        deduped.append(repo)
    return deduped


def repo_visibility_score(repo: dict[str, Any]) -> float:
    """Rank repos for soft emphasis when repo density gets high.

    Scoring weights: stars (dominant), forks, watchers, topic count,
    age (capped at 6 years), and description presence.
    """
    stars = float(repo.get("stars", 0) or 0)
    forks = float(repo.get("forks", 0) or 0)
    watchers = float(repo.get("watchers", 0) or 0)
    age_months = float(repo.get("age_months", 0) or 0)
    topic_count = len(repo.get("topics") or [])
    has_description = 1.0 if repo.get("description") else 0.0
    return (
        math.log1p(stars) * 4.0
        + math.log1p(forks) * 2.2
        + math.log1p(watchers) * 1.4
        + min(age_months, 72.0) * 0.05
        + topic_count * 0.8
        + has_description * 0.4
    )


def select_primary_repos(
    repos: list[dict[str, Any]], *, limit: int = MAX_REPOS
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Expose every repo while preserving the caller's stable visual order.

    ``limit`` is retained as a soft-emphasis hint for compatibility, but living
    art renderers should consume the full repo set rather than dropping an
    overflow tail. Callers that need emphasis can derive it from
    :func:`repo_visibility_score` without omitting repos from the returned plan.
    """
    _ = limit
    return order_repos_for_visual_plan(repos), []


# ── Language-family spatial clustering ────────────────────────────────────

_LANG_FAMILIES: dict[str, str] = {
    "Python": "data",
    "Jupyter Notebook": "data",
    "R": "data",
    "JavaScript": "web",
    "TypeScript": "web",
    "HTML": "web",
    "CSS": "web",
    "Rust": "systems",
    "Go": "systems",
    "C": "systems",
    "C++": "systems",
    "Java": "enterprise",
    "Kotlin": "enterprise",
    "Scala": "enterprise",
    "Ruby": "scripting",
    "Shell": "scripting",
    "Lua": "scripting",
    "PHP": "scripting",
    "Swift": "mobile",
    "Dart": "mobile",
}

_FAMILY_QUADRANT: dict[str, tuple[float, float]] = {
    "data": (0.25, 0.30),
    "web": (0.75, 0.25),
    "systems": (0.25, 0.70),
    "enterprise": (0.75, 0.70),
    "scripting": (0.50, 0.50),
    "mobile": (0.60, 0.45),
}


def repo_to_canvas_position(
    repo: dict[str, Any],
    seed: str,
    canvas_w: float = WIDTH,
    canvas_h: float = HEIGHT,
    *,
    strategy: str = "language_cluster",
    jitter: float = 0.15,
) -> tuple[float, float]:
    """Deterministic 2D position for a repo on the art canvas.

    Strategies
    ----------
    ``"language_cluster"``
        Groups repos by language family into spatial quadrants with
        hash-based jitter within each quadrant.
    ``"hash"``
        Pure deterministic 2D hash of repo name — no clustering.
    """
    name = repo.get("name", "")
    h = hashlib.sha256(f"{seed}-{name}".encode()).hexdigest()

    if strategy == "language_cluster":
        lang = repo.get("language") or ""
        family = _LANG_FAMILIES.get(lang, "scripting")
        cx_frac, cy_frac = _FAMILY_QUADRANT.get(family, (0.5, 0.5))
        jx = (hex_frac(h, 0, 4) - 0.5) * 2 * jitter
        jy = (hex_frac(h, 4, 8) - 0.5) * 2 * jitter
        x = (cx_frac + jx) * canvas_w
        y = (cy_frac + jy) * canvas_h
    else:
        x = hex_frac(h, 0, 8) * canvas_w * 0.8 + canvas_w * 0.1
        y = hex_frac(h, 8, 16) * canvas_h * 0.8 + canvas_h * 0.1

    return (
        max(canvas_w * 0.05, min(canvas_w * 0.95, x)),
        max(canvas_h * 0.05, min(canvas_h * 0.95, y)),
    )


# ── Derived metrics ──────────────────────────────────────────────────────


@dataclass(frozen=True)
class DerivedMetrics:
    """Pre-computed secondary metrics shared across art modules."""

    contribution_intensity: float
    """contributions_last_year / account_age_years (0 if unknown)."""

    star_velocity: float
    """Fraction of total stars gained in the last year (0-1)."""

    topic_diversity: int
    """Count of distinct topics across all repos."""

    language_count: int
    """Count of distinct languages across all repos."""

    total_stars: int
    total_forks: int
    total_contributions: int


def compute_derived_metrics(metrics: dict[str, Any]) -> DerivedMetrics:
    """Compute secondary metrics from the raw metrics payload."""
    repos = metrics.get("top_repos") or metrics.get("repos") or []

    total_stars = int(metrics.get("stars", 0) or 0)
    total_forks = sum(int(r.get("forks", 0) or 0) for r in repos)
    total_contributions = int(metrics.get("contributions_last_year", 0) or 0)
    account_age_years = max(0.1, (metrics.get("account_age_days") or 365) / 365.25)

    contribution_intensity = total_contributions / account_age_years

    # Star velocity: approximate from recent vs total
    recent_stars = int(metrics.get("stars_last_year", 0) or 0)
    star_velocity = min(1.0, recent_stars / max(1, total_stars))

    all_topics: set[str] = set()
    all_languages: set[str] = set()
    for r in repos:
        all_topics.update(r.get("topics") or [])
        lang = r.get("language")
        if lang:
            all_languages.add(lang)

    return DerivedMetrics(
        contribution_intensity=contribution_intensity,
        star_velocity=star_velocity,
        topic_diversity=len(all_topics),
        language_count=len(all_languages),
        total_stars=total_stars,
        total_forks=total_forks,
        total_contributions=total_contributions,
    )


# ── Element budget ────────────────────────────────────────────────────────


class ElementBudget:
    """Track SVG element count against a maximum budget.

    Usage::

        budget = ElementBudget(25000)
        for item in items:
            if not budget.ok():
                break
            P.append(render(item))
            budget.add(1)
    """

    __slots__ = ("_max", "_count")

    def __init__(self, max_elements: int = 25000) -> None:
        self._max = max_elements
        self._count = 0

    def add(self, n: int = 1) -> None:
        self._count += n

    def ok(self) -> bool:
        return self._count < self._max

    @property
    def remaining(self) -> int:
        return max(0, self._max - self._count)

    @property
    def count(self) -> int:
        return self._count
