# Workflows

# GitHub Actions Workflows

This project utilizes a unified GitHub Actions workflow, defined in `[.github/workflows/profile-updater.yml](mdc:.github/workflows/profile-updater.yml)`, to automate the generation of profile assets and updates to the main `README.md`. This single workflow has replaced multiple individual workflow files for better maintainability and consistency.

## Unified Workflow: `profile-updater.yml`

This workflow is triggered on:

- Manual dispatch (`workflow_dispatch`)
- A daily schedule (`cron: "0 1 * * *"`)
- Pushes to `master` or `main` branches

It consists of several dependent jobs:

### 1. `update-starred-lists`

- **Purpose:** Fetches the latest starred repositories and categorizes them by language and topic.
- **Key Steps:**
  - Checks out the repository.
  - Sets up Python 3.13 and `uv` (for dependency management).
  - Installs the `.[script-tools]` dependencies (which includes the `starred` CLI tool).
  - Runs the `starred` CLI tool twice:
    - Once to generate `.github/assets/languages.md`.
    - Once to generate `.github/assets/topics.md`.
  - Commits these two Markdown files to the repository if changes are detected, using `stefanzweifel/git-auto-commit-action@v5`.
- **Permissions:** `contents: write` (to commit the Markdown files).
- **Outputs:** A boolean `starred_lists_changed` indicating if the files were modified.

### 2. `generate-assets`

- **Purpose:** Generates all visual assets for the profile using the project's Python scripts, orchestrated by `scripts/cli.py`.
- **Dependency:** Runs after `update-starred-lists` completes.
- **Key Steps:**
  - Checks out the repository (ensuring it fetches any commits made by the previous job).
  - Sets up Python 3.13 and `uv`.
  - Installs `.[qr,word-clouds,banner]` dependencies.
  - Executes `python scripts/cli.py generate <asset_type>` for:
    - `qr_code`: Generates the vCard QR code.
    - `word_cloud` (for topics): Uses `.github/assets/topics.md` to generate `wordcloud_by_topic.png`.
    - `word_cloud` (for languages): Uses `.github/assets/languages.md` to generate `wordcloud_by_language.png`.
    - `banner`: Generates the profile banner SVG.
  - All CLI commands use `config.yaml` for base configuration, which can be overridden by CLI arguments specified in the workflow if necessary (though currently, it relies heavily on `config.yaml` and specific output paths for word clouds).
  - Commits the generated image assets (`qr*.png`, `wordcloud_*.png`, `banner.svg`) located in `.github/assets/img/` if changes are detected.
- **Permissions:** `contents: write` (to commit the generated assets).

### 3. `update-readme-wakatime`

- **Purpose:** Updates the `README.md` file with WakaTime coding statistics.
- **Key Steps:**
  - Checks out the repository.
  - Uses the `anmol098/waka-readme-stats@v4` action.
  - Requires `WAKATIME_API_KEY` and `GH_TOKEN` secrets.
- **Permissions:** `contents: write` (to update `README.md`).

### 4. `update-readme-blog`

- **Purpose:** Updates the `README.md` file with the latest blog posts from a Medium feed.
- **Key Steps:**
  - Checks out the repository.
  - Uses the `gautamkrishnar/blog-post-workflow@v1` action.
  - Configured with a Medium feed URL.
- **Permissions:** `contents: write` (to update `README.md`).

### 5. `generate-profile-metrics`

- **Purpose:** Generates SVG images displaying various GitHub profile metrics.
- **Key Steps:**
  - Checks out the repository.
  - Uses the `lowlighter/metrics@latest` action twice to generate two different SVG files:
    - `.github/assets/img/metrics.svg`
    - `.github/assets/img/metrics.additional.svg`
  - Requires `METRICS_TOKEN` and `GITHUB_TOKEN` secrets.
- **Permissions:** `contents: write` (to commit the metric SVGs).

## Invocation

- **Automated:** The workflow runs automatically based on its triggers (schedule, push, manual dispatch).
- **Local Generation:** For local development and testing of asset generation, use the `Makefile` targets (e.g., `make generate-banner`, `make generate-qr`, `make generate-word-clouds`) or directly use the `python scripts/cli.py generate ...` commands. These local methods use the same underlying Python scripts as the `generate-assets` job.

This consolidated approach streamlines automation, improves readability of the CI/CD process, and centralizes dependency management using Python 3.13 and `uv`.
