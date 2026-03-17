"""Smoke tests for scripts/art/ink_garden.py.

ink_garden generates SVG strings — no file I/O, no PIL, no cairosvg.
The only heavy dependency is numpy (used by Noise2D in shared.py).
Tests are safe to run in parallel with -n auto: no shared mutable state.
"""
from __future__ import annotations

import pytest

# Skip the entire module if numpy is absent — ink_garden imports it at the top
# level and cannot function without it.
pytest.importorskip("numpy", reason="numpy is required by scripts.art.ink_garden")

# Module-level imports: bring everything in once so per-test bodies stay clean
# and the linter does not flag "import outside toplevel".
from scripts.art import ink_garden  # noqa: E402
from scripts.art.ink_garden import (  # noqa: E402
    MAX_ELEMENTS,
    MAX_REPOS,
    MAX_SEGS,
    SPECIES,
    _classify_species,
    generate,
    seed_hash,
)


# ---------------------------------------------------------------------------
# Sample metrics constants — module-level, immutable, no shared state
# ---------------------------------------------------------------------------

MINIMAL_METRICS: dict = {
    "total_commits": 100,
    "stars": 5,
    "contributions_last_year": 50,
    "followers": 10,
    "forks": 2,
    "network_count": 3,
    "repos": [
        {"name": "repo-alpha", "stars": 3, "age_months": 12, "language": "Python"},
    ],
    "contributions_monthly": {},
}

RICH_METRICS: dict = {
    "total_commits": 5000,
    "stars": 150,
    "contributions_last_year": 800,
    "followers": 200,
    "forks": 40,
    "network_count": 100,
    "open_issues_count": 7,
    "orgs_count": 2,
    "watchers": 20,
    "repos": [
        {"name": "oak-repo", "stars": 200, "age_months": 36, "language": "Python"},
        {"name": "birch-repo", "stars": 25, "age_months": 30, "language": "Go"},
        {"name": "conifer-repo", "stars": 1, "age_months": 8, "language": "Rust"},
        {"name": "js-repo", "stars": 0, "age_months": 3, "language": "JavaScript"},
        {"name": "shell-repo", "stars": 0, "age_months": 7, "language": "Shell"},
    ],
    "contributions_monthly": {"2024-01": 50, "2024-02": 40},
}


# ---------------------------------------------------------------------------
# TestModuleImport
# ---------------------------------------------------------------------------

class TestModuleImport:
    """Smoke: module and public API surface are importable."""

    def test_module_object_is_not_none(self) -> None:
        """Module object exists after import."""
        assert ink_garden is not None

    def test_generate_is_callable(self) -> None:
        """generate is a callable."""
        assert callable(generate)

    def test_species_is_nonempty_dict(self) -> None:
        """SPECIES constant is a non-empty dict."""
        assert isinstance(SPECIES, dict)
        assert len(SPECIES) > 0

    def test_max_segs_positive(self) -> None:
        """MAX_SEGS hard cap is a positive integer."""
        assert isinstance(MAX_SEGS, int)
        assert MAX_SEGS > 0

    def test_max_elements_positive(self) -> None:
        """MAX_ELEMENTS hard cap is a positive integer."""
        assert isinstance(MAX_ELEMENTS, int)
        assert MAX_ELEMENTS > 0


# ---------------------------------------------------------------------------
# TestClassifySpecies
# ---------------------------------------------------------------------------

class TestClassifySpecies:
    """Unit tests for _classify_species — pure function, no I/O."""

    def test_high_stars_yields_oak(self) -> None:
        """Repos with >= 100 stars are classified as oak."""
        assert _classify_species({"stars": 100, "age_months": 12, "language": "Python"}) == "oak"

    def test_mid_stars_and_old_age_yields_birch(self) -> None:
        """Repos with >= 20 stars and >= 24 months are classified as birch."""
        assert _classify_species({"stars": 20, "age_months": 24, "language": "Go"}) == "birch"

    def test_rust_language_yields_conifer(self) -> None:
        """Rust repos (low stars) are classified as conifer."""
        assert _classify_species({"stars": 0, "age_months": 10, "language": "Rust"}) == "conifer"

    def test_javascript_language_yields_fern(self) -> None:
        """JavaScript repos (low stars) are classified as fern."""
        assert _classify_species({"stars": 0, "age_months": 10, "language": "JavaScript"}) == "fern"

    def test_shell_language_yields_bamboo(self) -> None:
        """Shell repos are classified as bamboo."""
        assert _classify_species({"stars": 0, "age_months": 10, "language": "Shell"}) == "bamboo"

    def test_very_young_repo_yields_seedling(self) -> None:
        """Repos younger than 6 months are classified as seedling."""
        assert _classify_species({"stars": 0, "age_months": 3, "language": "Python"}) == "seedling"

    def test_few_stars_mid_age_yields_shrub(self) -> None:
        """Repos with < 5 stars and age 6-18 months are classified as shrub."""
        assert _classify_species({"stars": 2, "age_months": 10, "language": "Python"}) == "shrub"

    def test_default_case_yields_wildflower(self) -> None:
        """Repos that match no other rule are classified as wildflower."""
        # stars >= 5, age >= 18 months, common language
        result = _classify_species({"stars": 8, "age_months": 20, "language": "Python"})
        assert result == "wildflower"

    def test_empty_dict_does_not_crash(self) -> None:
        """_classify_species handles an empty dict without raising."""
        result = _classify_species({})
        assert isinstance(result, str)
        assert len(result) > 0

    def test_result_is_always_a_known_species(self) -> None:
        """Classification always returns a string present in SPECIES or a known alias."""
        # The full set includes fern, bamboo, seedling which may not be in SPECIES dict
        known = set(SPECIES.keys()) | {"fern", "bamboo", "seedling"}
        for repo in [
            {"stars": 200, "age_months": 40, "language": "Python"},
            {"stars": 25, "age_months": 30, "language": "Go"},
            {"stars": 0, "age_months": 10, "language": "Rust"},
            {"stars": 0, "age_months": 10, "language": "JavaScript"},
            {"stars": 0, "age_months": 10, "language": "Shell"},
            {"stars": 0, "age_months": 2, "language": "Python"},
            {"stars": 2, "age_months": 10, "language": "Python"},
            {"stars": 8, "age_months": 20, "language": "Python"},
        ]:
            assert _classify_species(repo) in known


# ---------------------------------------------------------------------------
# TestGenerate
# ---------------------------------------------------------------------------

class TestGenerate:
    """Smoke tests for the generate() entry point."""

    def test_returns_str(self) -> None:
        """generate() returns a string."""
        result = generate(MINIMAL_METRICS)
        assert isinstance(result, str)

    def test_output_is_svg(self) -> None:
        """Output starts with <svg and ends with </svg>."""
        result = generate(MINIMAL_METRICS)
        assert result.lstrip().startswith("<svg")
        assert result.rstrip().endswith("</svg>")

    def test_svg_has_viewbox(self) -> None:
        """Generated SVG includes a viewBox attribute (required for embedding)."""
        result = generate(MINIMAL_METRICS)
        assert "viewBox" in result

    def test_deterministic_with_explicit_hex_seed(self) -> None:
        """Same hex seed produces byte-identical SVG output."""
        # The seed parameter must be a SHA-256 hex string; use seed_hash() to produce one.
        hex_seed = seed_hash(MINIMAL_METRICS)
        r1 = generate(MINIMAL_METRICS, seed=hex_seed)
        r2 = generate(MINIMAL_METRICS, seed=hex_seed)
        assert r1 == r2

    def test_maturity_zero_returns_svg(self) -> None:
        """maturity=0.0 (blank soil) still returns a valid SVG string."""
        result = generate(MINIMAL_METRICS, maturity=0.0)
        assert result.lstrip().startswith("<svg")
        assert result.rstrip().endswith("</svg>")

    def test_maturity_one_returns_svg(self) -> None:
        """maturity=1.0 (full garden) returns a valid SVG string."""
        result = generate(RICH_METRICS, maturity=1.0)
        assert result.lstrip().startswith("<svg")
        assert result.rstrip().endswith("</svg>")

    def test_empty_repos_does_not_crash(self) -> None:
        """generate() handles metrics with an empty repos list."""
        metrics = {**MINIMAL_METRICS, "repos": []}
        result = generate(metrics)
        assert isinstance(result, str)

    def test_repos_beyond_max_are_capped(self) -> None:
        """Supplying more than MAX_REPOS repos does not raise; output is valid SVG."""
        extra_repos = [
            {"name": f"repo-{i}", "stars": i, "age_months": i + 1, "language": "Python"}
            for i in range(MAX_REPOS + 5)
        ]
        result = generate({**RICH_METRICS, "repos": extra_repos}, maturity=0.5)
        assert result.lstrip().startswith("<svg")

    def test_rich_metrics_mid_maturity_produces_substantial_svg(self) -> None:
        """Rich metrics at maturity=0.5 produce more than a skeleton SVG."""
        result = generate(RICH_METRICS, maturity=0.5)
        assert len(result) > 500

    def test_all_species_classifications_handled_without_error(self) -> None:
        """Repos triggering every species classification path produce valid SVG."""
        metrics = {
            **MINIMAL_METRICS,
            "stars": 150,
            "repos": [
                {"name": "oak", "stars": 100, "age_months": 40, "language": "Python"},
                {"name": "birch", "stars": 20, "age_months": 24, "language": "Python"},
                {"name": "conifer", "stars": 0, "age_months": 10, "language": "Rust"},
                {"name": "fern", "stars": 0, "age_months": 10, "language": "JavaScript"},
                {"name": "bamboo", "stars": 0, "age_months": 10, "language": "Shell"},
                {"name": "seedling", "stars": 0, "age_months": 2, "language": "Python"},
                {"name": "shrub", "stars": 2, "age_months": 10, "language": "Python"},
                {"name": "wildflower", "stars": 8, "age_months": 20, "language": "Python"},
            ],
        }
        result = generate(metrics, maturity=0.8)
        assert result.lstrip().startswith("<svg")
        assert result.rstrip().endswith("</svg>")

    def test_two_different_seeds_both_produce_valid_svg(self) -> None:
        """Two different hex seeds both produce valid SVG (neither raises)."""
        seed_a = seed_hash(MINIMAL_METRICS)
        seed_b = seed_hash(RICH_METRICS)
        for seed in (seed_a, seed_b):
            result = generate(MINIMAL_METRICS, seed=seed)
            assert result.lstrip().startswith("<svg")
            assert result.rstrip().endswith("</svg>")
