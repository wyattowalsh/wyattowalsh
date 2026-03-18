# Makefile for the wyattowalsh project using uv

# ------------------------------------------------------------------------------
# Variables
# ------------------------------------------------------------------------------
PYTHON = python3.13
UV = uv
SRC_DIRS = scripts tests
SCRIPT_BANNER = scripts/banner.py # This line is illustrative, direct script calls are being phased out for CLI
SCRIPT_QR = scripts/qr.py
# SCRIPT_WORD_CLOUDS = scripts/word_clouds.py # Direct script call is being replaced by CLI
CLI_SCRIPT = scripts/cli.py
OUTPUT_DIR = .github/assets/img
BANNER_OUTPUT = $(OUTPUT_DIR)/banner.svg
QR_OUTPUT = $(OUTPUT_DIR)/qr.png
WORDCLOUD_TOPIC_OUTPUT = $(OUTPUT_DIR)/wordcloud_by_topic.svg
WORDCLOUD_LANG_OUTPUT = $(OUTPUT_DIR)/wordcloud_by_language.svg
PYPROJECT = pyproject.toml
LOCKFILE = uv.lock
VENV_DIR = .venv

# Ensure uv is available
_ := $(shell command -v $(UV) >/dev/null 2>&1 || (echo "Error: uv is not installed or not in PATH. Please install uv: https://github.com/astral-sh/uv" && exit 1))

# Default target
.DEFAULT_GOAL := all

# ------------------------------------------------------------------------------
# Core Targets
# ------------------------------------------------------------------------------
.PHONY: all
all: lint test generate ## Run linting, tests, and generate assets

.PHONY: install
install: $(LOCKFILE) ## Sync dependencies with the lock file
	@echo "Syncing environment with $(LOCKFILE)..."
	$(UV) sync --all-groups --quiet

.PHONY: format
format: install ## Format code using black, isort, and autoflake
	@echo "Formatting code..."
	$(UV) run --quiet -- python -m black $(SRC_DIRS)
	$(UV) run --quiet -- python -m isort $(SRC_DIRS)
	$(UV) run --quiet -- python -m autoflake --in-place --recursive $(SRC_DIRS)

.PHONY: lint
lint: install ## Lint code using ruff, pylint, and mypy
	@echo "Linting code with ruff..."
	$(UV) run --quiet -- python -m ruff check $(SRC_DIRS)
	@echo "Linting code with pylint..."
	$(UV) run --quiet -- python -m pylint $(SRC_DIRS)
	@echo "Type checking with mypy..."
	$(UV) run --quiet -- python -m mypy $(SRC_DIRS)

.PHONY: test
test: install ## Run tests using pytest
	@echo "Running tests..."
	$(UV) run --quiet -- python -m pytest

# ------------------------------------------------------------------------------
# Generation Targets
# ------------------------------------------------------------------------------
.PHONY: generate-banner
generate-banner: install ## Generate the SVG banner
	@echo "Generating banner..."
	$(UV) run --quiet -- $(PYTHON) -m scripts.cli generate banner

.PHONY: generate-qr
generate-qr: install ## Generate the QR code PNG
	@echo "Ensuring QR dependencies are installed..."
	$(UV) pip install -e ".[qr]" --quiet
	@echo "Generating QR code..."
	export DYLD_LIBRARY_PATH=$(shell brew --prefix cairo)/lib:$$DYLD_LIBRARY_PATH && $(UV) run --quiet -- $(PYTHON) -m scripts.cli generate qr_code

.PHONY: generate-word-clouds
generate-word-clouds:
	@echo "Syncing environment with uv.lock (all groups)..."
	$(UV) sync --all-groups --quiet
	@echo "Ensuring local package is installed in editable mode (with word-clouds extras)..."
	$(UV) pip install -e ".[word-clouds]" --quiet
	@echo "Generating profile word clouds (topics and languages)..."
	$(UV) run --quiet -- $(PYTHON) -m scripts.cli generate word_cloud --from-topics-md
	$(UV) run --quiet -- $(PYTHON) -m scripts.cli generate word_cloud --from-languages-md
	@echo "Profile word clouds generated."

.PHONY: generate-generative
generate-generative: install ## Generate event-driven generative artwork
	@echo "Generating event-driven artwork..."
	$(UV) run --quiet -- $(PYTHON) -m scripts.fetch_metrics --owner wyattowalsh --repo wyattowalsh --output /tmp/metrics.json
	$(UV) run --quiet -- $(PYTHON) -m scripts.cli generate generative --output-path /tmp/metrics.json
	@echo "Generative artwork generated."

.PHONY: generate-animated
generate-animated: install ## Generate animated historical artwork SVGs
	@echo "Fetching historical data..."
	$(UV) run --quiet -- $(PYTHON) -m scripts.fetch_history --owner wyattowalsh --repo wyattowalsh --output /tmp/history.json
	@echo "Generating animated artwork..."
	$(UV) run --quiet -- $(PYTHON) -m scripts.cli generate animated --history-path /tmp/history.json
	@echo "Animated artwork generated."

.PHONY: generate-skills
generate-skills: install ## Generate technology/skills badges
	@echo "Generating skills badges..."
	$(UV) run --quiet -- $(PYTHON) -m scripts.cli generate skills

.PHONY: generate-tech-word-cloud
generate-tech-word-cloud: install ## Generate the generic technology word cloud (from techs.md)
	@echo "Generating technology word cloud (from techs.md)..."
	$(UV) run --quiet -- $(PYTHON) -m scripts.cli generate word_cloud --output-path logs/wordcloud_examples/techs_cli_generated.png
	@echo "Technology word cloud generated in logs/wordcloud_examples/techs_cli_generated.png"

.PHONY: generate
generate: generate-banner generate-qr generate-word-clouds generate-skills generate-generative generate-animated ## Generate all profile assets

# ------------------------------------------------------------------------------
# Maintenance Targets
# ------------------------------------------------------------------------------
.PHONY: clean
clean: ## Remove cache directories and generated files
	@echo "Cleaning up..."
	rm -rf .pytest_cache .mypy_cache logs/ __pycache__/ */__pycache__/ */*/__pycache__/ $(VENV_DIR)
	rm -f $(BANNER_OUTPUT) $(QR_OUTPUT) $(WORDCLOUD_TOPIC_OUTPUT) $(WORDCLOUD_LANG_OUTPUT) .coverage
	rm -f logs/wordcloud_examples/* # Clean example word clouds too

.PHONY: clean-venv
clean-venv: ## Remove only the virtual environment
	@echo "Removing virtual environment..."
	rm -rf $(VENV_DIR)

.PHONY: venv
venv: $(LOCKFILE) ## Create virtual environment and sync dependencies
	@echo "Setting up virtual environment..."
	$(UV) venv --python $(PYTHON) $(VENV_DIR)
	$(UV) sync --quiet

.PHONY: update-deps
update-deps: $(PYPROJECT) ## Update all dependencies in pyproject.toml to latest compatible versions and update lockfile
	@echo "Updating dependencies and lockfile..."
	$(UV) lock --upgrade
	@echo "Dependencies updated. Run 'make install' or 'make venv' to apply changes."

# ------------------------------------------------------------------------------
# Help Target
# ------------------------------------------------------------------------------
.PHONY: help
help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


.PHONY: docs
docs: ## Serve the Fumadocs dev docs site locally
	cd docs && pnpm dev
# Declare targets that are not files
.PHONY: all install format lint test generate-banner generate-qr generate-word-clouds generate-skills generate-generative generate-animated generate-tech-word-cloud generate clean clean-venv venv update-deps help docs