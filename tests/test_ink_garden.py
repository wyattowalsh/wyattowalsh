"""Smoke tests for scripts/art/ink_garden.py.

ink_garden generates SVG strings — no file I/O, no PIL, no cairosvg.
The only heavy dependency is numpy (used by Noise2D in shared.py).
Tests are safe to run in parallel with -n auto: no shared mutable state.
"""

from __future__ import annotations

from pathlib import Path

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
    _overflow_specimen_annotation,
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
        assert (
            _classify_species({"stars": 100, "age_months": 12, "language": "Python"})
            == "oak"
        )

    def test_mid_stars_and_old_age_yields_birch(self) -> None:
        """Repos with >= 20 stars and >= 24 months are classified as birch."""
        assert (
            _classify_species({"stars": 20, "age_months": 24, "language": "Go"})
            == "birch"
        )

    def test_rust_language_yields_conifer(self) -> None:
        """Rust repos (low stars) are classified as conifer."""
        assert (
            _classify_species({"stars": 0, "age_months": 10, "language": "Rust"})
            == "conifer"
        )

    def test_javascript_language_yields_fern(self) -> None:
        """JavaScript repos (low stars) are classified as fern."""
        assert (
            _classify_species({"stars": 0, "age_months": 10, "language": "JavaScript"})
            == "fern"
        )

    def test_shell_language_yields_bamboo(self) -> None:
        """Shell repos are classified as bamboo."""
        assert (
            _classify_species({"stars": 0, "age_months": 10, "language": "Shell"})
            == "bamboo"
        )

    def test_very_young_repo_yields_seedling(self) -> None:
        """Repos younger than 6 months are classified as seedling."""
        assert (
            _classify_species({"stars": 0, "age_months": 3, "language": "Python"})
            == "seedling"
        )

    def test_few_stars_mid_age_yields_shrub(self) -> None:
        """Repos with < 5 stars and age 6-18 months are classified as shrub."""
        assert (
            _classify_species({"stars": 2, "age_months": 10, "language": "Python"})
            == "shrub"
        )

    def test_default_case_yields_wildflower(self) -> None:
        """Repos that match no other rule are classified as wildflower."""
        # stars >= 5, age >= 18 months, common language
        result = _classify_species({"stars": 8, "age_months": 20, "language": "Python"})
        assert result == "wildflower"

    def test_ai_topics_yield_wisteria(self) -> None:
        """AI-oriented topics should map to the cascading wisteria species."""
        result = _classify_species(
            {
                "stars": 4,
                "age_months": 8,
                "language": "Python",
                "topics": ["ai", "agents"],
            }
        )
        assert result == "wisteria"

    def test_fork_heavy_repo_yields_banyan(self) -> None:
        """Fork-heavy repos should map to the spreading banyan species."""
        result = _classify_species(
            {
                "stars": 6,
                "forks": 8,
                "age_months": 14,
                "language": "Python",
            }
        )
        assert result == "banyan"

    def test_empty_dict_does_not_crash(self) -> None:
        """_classify_species handles an empty dict without raising."""
        result = _classify_species({})
        assert isinstance(result, str)
        assert len(result) > 0

    def test_result_is_always_a_known_species(self) -> None:
        """Classification always returns a known species string or alias."""
        # The full set includes fern, bamboo, and seedling aliases.
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

    def test_overflow_specimen_annotation_summarizes_topics(self) -> None:
        """Overflow helper should dedupe and compact topic hints."""
        summary, topics = _overflow_specimen_annotation(
            [
                {"topics": ["cli", "automation", "cli"]},
                {"topics": ["ai", "automation"]},
            ]
        )

        assert summary == "+2 specimens held back"
        assert topics == "cli / automation / ai"

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
        # The seed must be a SHA-256 hex string from seed_hash().
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
                {
                    "name": "fern",
                    "stars": 0,
                    "age_months": 10,
                    "language": "JavaScript",
                },
                {"name": "bamboo", "stars": 0, "age_months": 10, "language": "Shell"},
                {"name": "seedling", "stars": 0, "age_months": 2, "language": "Python"},
                {"name": "shrub", "stars": 2, "age_months": 10, "language": "Python"},
                {
                    "name": "wildflower",
                    "stars": 8,
                    "age_months": 20,
                    "language": "Python",
                },
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

    def test_topic_annotations_render_beneath_repo_labels(self) -> None:
        """Repo topics should appear as compact specimen annotations in labels."""
        metrics = {
            **MINIMAL_METRICS,
            "repos": [
                {
                    "name": "signal-garden",
                    "stars": 22,
                    "age_months": 18,
                    "language": "Python",
                    "topics": ["ai", "agents", "automation"],
                }
            ],
        }
        result = generate(metrics, seed=seed_hash(metrics), maturity=0.9)
        assert "signal-garden" in result
        assert "ai · agents +1" in result

    def test_repo_visibility_tiering_keeps_high_value_late_repo(self) -> None:
        """Important late repos should still survive the MAX_REPOS render cap."""
        repos = [
            {
                "name": f"tiny-repo-{index}",
                "stars": 0,
                "forks": 0,
                "age_months": 2,
                "language": "Python",
            }
            for index in range(MAX_REPOS + 2)
        ]
        repos[-1] = {
            "name": "priority-archive",
            "stars": 180,
            "forks": 28,
            "age_months": 48,
            "language": "Go",
            "topics": ["cli", "automation"],
            "description": "Important late repo that should survive tiering.",
        }
        metrics = {**RICH_METRICS, "repos": repos}
        result = generate(metrics, seed=seed_hash(metrics), maturity=0.9)
        assert "priority-archive" in result
        assert 'id="study-drawers"' in result
        assert "Study Drawers" in result
        assert "+2 specimens held back" in result
        assert f"tiny-repo-{MAX_REPOS - 1}" not in result


# ---------------------------------------------------------------------------
# TestGoldenFiles
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "ink_garden"


@pytest.mark.skipif(
    not (FIXTURES_DIR / "minimal_full.svg").exists(),
    reason="Golden fixtures not generated yet — run generate_fixtures script",
)
class TestGoldenFiles:
    """Regression tests: compare generate() output against stored golden SVGs.

    To regenerate golden files after an intentional output change, call
    generate() directly with the same parameters used in each test, e.g.::

        uv run python -c "
        import json
        from pathlib import Path
        from scripts.art.ink_garden import generate, seed_hash

        FIXTURES = Path('tests/fixtures/ink_garden')
        FIXTURES.mkdir(parents=True, exist_ok=True)

        # See MINIMAL_METRICS / RICH_METRICS constants at top of test file.
        from tests.test_ink_garden import MINIMAL_METRICS, RICH_METRICS

        (FIXTURES / 'minimal_full.svg').write_text(
            generate(MINIMAL_METRICS, seed=seed_hash(MINIMAL_METRICS), maturity=1.0)
        )
        (FIXTURES / 'rich_full.svg').write_text(
            generate(RICH_METRICS, seed=seed_hash(RICH_METRICS), maturity=1.0)
        )
        (FIXTURES / 'rich_mid.svg').write_text(
            generate(RICH_METRICS, seed=seed_hash(RICH_METRICS), maturity=0.5)
        )
        "

    See TestGoldenFiles source for the exact regeneration parameters.

    Note: Golden SVG files contain numpy-generated floating-point path data.
    Byte-exact comparison is valid only when numpy is pinned (see uv.lock).
    Regenerate golden files after any numpy version bump.
    """

    def _load_golden(self, name: str) -> str:
        path = FIXTURES_DIR / name
        if not path.exists():
            pytest.skip(f"Golden file {name} not found — run fixture generator first")
        return path.read_text()

    def test_minimal_full_maturity_matches_golden(self) -> None:
        """Minimal metrics at full maturity produce identical SVG to stored golden."""
        expected = self._load_golden("minimal_full.svg")
        hex_seed = seed_hash(MINIMAL_METRICS)
        actual = generate(MINIMAL_METRICS, seed=hex_seed, maturity=1.0)
        assert actual == expected, (
            "SVG output changed — if intentional, delete tests/fixtures/ink_garden/ "
            "and re-run to regenerate golden files."
        )

    def test_rich_full_maturity_matches_golden(self) -> None:
        """Rich metrics at full maturity produce identical SVG to stored golden."""
        expected = self._load_golden("rich_full.svg")
        hex_seed = seed_hash(RICH_METRICS)
        actual = generate(RICH_METRICS, seed=hex_seed, maturity=1.0)
        assert actual == expected, (
            "SVG output changed — if intentional, regenerate golden files."
        )

    def test_rich_mid_maturity_matches_golden(self) -> None:
        """Rich metrics at mid maturity produce identical SVG to stored golden."""
        expected = self._load_golden("rich_mid.svg")
        hex_seed = seed_hash(RICH_METRICS)
        actual = generate(RICH_METRICS, seed=hex_seed, maturity=0.5)
        assert actual == expected, (
            "SVG output changed — if intentional, regenerate golden files."
        )

    def test_golden_files_are_valid_svg(self) -> None:
        """All stored golden files are valid SVG (start with <svg, end with </svg>)."""
        for name in ("minimal_full.svg", "rich_full.svg", "rich_mid.svg"):
            content = self._load_golden(name)
            assert content.lstrip().startswith("<svg"), (
                f"{name} does not start with <svg"
            )
            assert content.rstrip().endswith("</svg>"), (
                f"{name} does not end with </svg>"
            )
