"""Contracts for the repository's authoritative pytest coverage run."""

import shlex
import tomllib
from pathlib import Path


def _pytest_options() -> tuple[list[str], list[str]]:
    pyproject = tomllib.loads(
        (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(
            encoding="utf-8"
        )
    )
    pytest_config = pyproject["tool"]["pytest"]["ini_options"]
    return pytest_config["required_plugins"], shlex.split(pytest_config["addopts"])


def test_authoritative_coverage_starts_fresh_with_reproduced_floor() -> None:
    required_plugins, options = _pytest_options()

    assert "pytest-cov" in required_plugins
    assert options.count("--cov=./scripts") == 1
    assert "--cov-append" not in options
    assert not any(option.startswith("--html") for option in options)
    assert not any(option.startswith("--junitxml") for option in options)
    assert not any(option.startswith("--cov-report") for option in options)
    assert options.count("--cov-fail-under=95.0") == 1
