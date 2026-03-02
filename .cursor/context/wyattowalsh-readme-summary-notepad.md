# Wyatt O. Walsh - GitHub Profile Project (`wyattowalsh`) - LLM Context: SUMMARY

**Version:** 1.3
**Last Updated:** Current Date
**Purpose:** High-level summary of the `wyattowalsh` GitHub profile project for LLM context. For detailed information, see `@wyattowalsh-readme-details-notepad.md`.

## 1. Project Overview

- **Name:** `wyattowalsh`
- **Type:** Personal GitHub Profile Automation & Asset Generation
- **Goal:** Dynamic, engaging GitHub profile via programmatic content generation.
- **Key Tech:** Python 3.13, `uv`, `pydantic`, `typer`, `pytest`, GitHub Actions, `Makefile`.
- **Core Features:** SVG banner, vCard QR, topic/language word clouds, WakaTime/Medium integration into `[@README.md](mdc:README.md)`.
- **Status:** Active, with ongoing enhancements focused on workflow reliability, feature expansion (e.g., `[@scripts/techs.py](mdc:scripts/techs.py)`), and consistent Python 3.13 adoption. Recent refactoring consolidated multiple GitHub Actions into a single `profile-updater.yml` workflow.

## 2. Key Files & Directories

- `[@Makefile](mdc:Makefile)`: Local dev orchestration.
- `[@pyproject.toml](mdc:pyproject.toml)`: Dependencies (`uv`), tool configs.
- `[@uv.lock](mdc:uv.lock)`: Pinned dependencies.
- `[@README.md](mdc:README.md)`: Main profile README, dynamically updated.
- `[@scripts/](mdc:scripts)`: Core Python scripts for asset generation.
  - `[@scripts/banner.py](mdc:scripts/banner.py)`: SVG banner.
  - `[@scripts/qr.py](mdc:scripts/qr.py)`: QR code.
  - `[@scripts/word_clouds.py](mdc:scripts/word_clouds.py)`: Word clouds.
  - `[@scripts/cli.py](mdc:scripts/cli.py)`: `typer`-based CLI.
  - `[@scripts/techs.py](mdc:scripts/techs.py)`: Technology data processing.
- `[@.github/](mdc:.github)`: GitHub Actions workflows and assets.
  - `[@.github/assets/](mdc:.github/assets)`: Static & generated assets (images, `topics.md`, `languages.md`).
  - `[@.github/workflows/](mdc:.github/workflows)`: Automation YAML files.
    - `[@.github/workflows/profile-updater.yml](mdc:.github/workflows/profile-updater.yml)`: Unified workflow for all profile updates and asset generation.
- `[@tests/](mdc:tests)`: `pytest` tests.
- `[@docs/](mdc:docs)`: Project documentation.

## 3. Core Functionality Summary

The project automates via the `profile-updater.yml` workflow:

1.  **Starred Repo Data Fetching:** Updates `topics.md` and `languages.md` using `starred` CLI.
2.  **SVG Banner Generation:** (`[@scripts/banner.py](mdc:scripts/banner.py)`) - Complex, configurable SVG.
3.  **Artistic QR Code Generation:** (`[@scripts/qr.py](mdc:scripts/qr.py)`) - vCard PNG with SVG background.
4.  **Word Cloud Generation:** (`[@scripts/word_clouds.py](mdc:scripts/word_clouds.py)`) - From `topics.md` and `languages.md`.
5.  **GitHub Profile Metrics SVGs:** Uses `lowlighter/metrics`.
6.  **`[@README.md](mdc:README.md)` Augmentation:**
    - WakaTime stats (using `anmol098/waka-readme-stats`).
    - Medium blog posts (using `gautamkrishnar/blog-post-workflow`).
7.  **CLI for Local Generation:** (`[@scripts/cli.py](mdc:scripts/cli.py)`) orchestrates local asset generation.
8.  **Standardized Dev Env:** `uv`, `[@Makefile](mdc:Makefile)`, linters, formatters, `pytest`.

## 4. Key Data Flows

1.  **Starred Repos -> Word Clouds:** GitHub Stars -> `profile-updater.yml` (Job: `update-starred-lists`) -> `[@.github/assets/topics.md](mdc:.github/assets/topics.md)` & `[@.github/assets/languages.md](mdc:.github/assets/languages.md)` -> `profile-updater.yml` (Job: `generate-assets` via `[@scripts/cli.py](mdc:scripts/cli.py)`) -> PNGs.
2.  **QR Code:** Configured vCard data & static SVG -> `profile-updater.yml` (Job: `generate-assets` via `[@scripts/cli.py](mdc:scripts/cli.py)`) -> PNG.
3.  **Banner:** Pydantic Config -> `profile-updater.yml` (Job: `generate-assets` via `[@scripts/cli.py](mdc:scripts/cli.py)`) -> SVG.
4.  **GitHub Metrics:** `profile-updater.yml` (Job: `generate-profile-metrics` using `lowlighter/metrics`) -> GitHub API -> SVGs.
5.  **`[@README.md](mdc:README.md)` Updates:** External services (WakaTime, Medium) -> `profile-updater.yml` (Jobs: `update-readme-wakatime`, `update-readme-blog`) -> `[@README.md](mdc:README.md)`.

## 5. Known Issues & Key Action Items (High-Level)

- **`[@scripts/techs.py](mdc:scripts/techs.py)` Enhancement:** Integrate `techs.py` fully by defining a clear output format (e.g., Markdown section for `[@README.md](mdc:README.md)` or a dedicated page in `[@docs/](mdc:docs)`) and a corresponding CLI command for its generation. Explore using its data for other visual assets.
- **Python Version Consistency:**
  - Clarify/Configure MyPy's Python version target (ideally 3.13 in `[@pyproject.toml](mdc:pyproject.toml)`).
- **Font Availability:** Verify font (e.g., "Montserrat" for `[@scripts/banner.py](mdc:scripts/banner.py)`) in CI for banner generation.
- **Testing & CI Robustness:** Expand test coverage, particularly for script configurations and output validation. Ensure CI jobs are efficient and reliable.
- **Documentation:** Keep `[@docs/](mdc:docs)` and context notepads like this one up-to-date with project evolution. Consider auto-generating parts of the documentation.

Refer to `@wyattowalsh-readme-details-notepad.md` for granular script breakdowns, library lists, and specific configurations.
