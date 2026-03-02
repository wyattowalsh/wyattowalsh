# Command Line Interface (CLI)

This project utilizes `Typer` to provide a robust command-line interface (CLI) for managing configuration and generating assets. The main script is `scripts/cli.py`.

## Installation & Setup

To use the CLI, ensure you have the project's dependencies installed. It's recommended to use a virtual environment managed by `uv`.

1.  **Create and activate a virtual environment:**

    ```bash
    uv venv
    source .venv/bin/activate
    ```

2.  **Install dependencies (including extras for all CLI functionalities):**
    ```bash
    uv pip install -e .[banner,qr,word-clouds,dev]
    # Or use 'uv pip install .[all]' if an 'all' extra is defined that covers these
    ```

## Main CLI (`uv run readme`)

Once dependencies are installed and the project is (editably) installed (e.g., `uv pip install -e .`), you can access the CLI using `uv run readme`:

```bash
uv run readme --help
```

This will display the available commands and their options.

### Core Commands

#### 1. `config`

Manages the project's `config.yaml` file.

- **View Configuration:**
  ```bash
  uv run readme config view
  uv run readme config view --path custom-config.yaml
  uv run readme config view --output-format yaml
  ```
- **Save/Update Configuration:** (Saves current settings, or default if no file exists)
  ```bash
  uv run readme config save
  uv run readme config save --path custom-config.yaml
  ```
- **Generate Default Configuration:** (Overwrites if exists, with confirmation)
  ```bash
  uv run readme config generate-default
  uv run readme config generate-default --path new-default.yaml
  ```

#### 2. `generate`

Generates various assets based on the entity type specified. It primarily uses settings from `config.yaml` but allows overrides via CLI options.

**Syntax:** `uv run readme generate <ENTITY_TYPE> [OPTIONS]`

- **Supported `ENTITY_TYPE`s:**

  - `banner`: Generates the SVG profile banner.
  - `qr_code`: Generates the vCard QR code.
  - `word_cloud`: Generates word cloud images.
  - `readme`: (Planned) Functionality for README generation (currently not implemented).

- **Common Options:**

  - `--config-path <PATH>`: Specify a custom path to the `config.yaml` file.
  - `--output-path <PATH>`: Specify a custom output file path for the generated asset.

- **Example: Generate Banner**

  ```bash
  # Using defaults from config.yaml
  uv run readme generate banner

  # Overriding title and output path
  uv run readme generate banner --title "New Banner Title" --output-path .github/assets/img/custom_banner.svg
  ```

- **Example: Generate QR Code**

  ```bash
  # Using defaults from config.yaml
  uv run readme generate qr_code

  # Overriding scale and output path
  uv run readme generate qr_code --qr-scale 30 --output-path .github/assets/img/custom_qr.png
  ```

- **Example: Generate Word Cloud**
  Word clouds can be generated from specific project files (like `.github/assets/topics.md` and `.github/assets/languages.md` which are typically auto-generated from starred repositories), any arbitrary Markdown file, or a direct text prompt.

  ```bash
  # From .github/assets/topics.md (default output: .github/assets/img/wordcloud_by_topic.svg)
  uv run readme generate word_cloud --from-topics-md

  # To specify a PNG output for topics.md:
  uv run readme generate word_cloud --from-topics-md --output-path .github/assets/img/topic_cloud.png

  # From .github/assets/languages.md (default output: .github/assets/img/wordcloud_by_language.svg)
  uv run readme generate word_cloud --from-languages-md

  # To specify a PNG output for languages.md:
  uv run readme generate word_cloud --from-languages-md --output-path .github/assets/img/language_cloud.png

  # From an arbitrary Markdown file (e.g., a custom techs.md at the project root)
  uv run readme generate word_cloud --techs-path techs.md --output-path .github/assets/img/tech_custom_cloud.png

  # Using a direct prompt (text for the cloud)
  uv run readme generate word_cloud --prompt "Python FastAPI Typer Pydantic" --output-path .github/assets/img/prompt_cloud.png
  ```

#### 3. `show-settings`

Displays the current global application settings loaded from environment variables or `.env` file (relevant for settings like `LOG_LEVEL`).

```bash
uv run readme show-settings
uv run readme show-settings --output-format yaml
```

## Integration with `Makefile`

The `Makefile` provides convenient targets that wrap these CLI commands for common tasks:

- `make generate-banner`
- `make generate-qr`
- `make generate-word-clouds` (This might run multiple CLI commands for different word clouds)

Refer to the `Makefile` for the exact commands executed.

## Automation

These CLI commands are also the foundation for the automated asset generation performed by the `generate-assets` job in the `[.github/workflows/profile-updater.yml](mdc:.github/workflows/profile-updater.yml)` GitHub Action workflow.
