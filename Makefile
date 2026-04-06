# Makefile convenience wrapper for the wyattowalsh project
# Canonical workflow is CLI-first via: uv run readme <command>

UV = uv
CLI = $(UV) run -- readme
OUTPUT_DIR = .github/assets/img
WORDCLOUD_TOPIC_OUTPUT = $(OUTPUT_DIR)/wordcloud_wordle_by_topics.svg
WORDCLOUD_LANG_OUTPUT = $(OUTPUT_DIR)/wordcloud_wordle_by_languages.svg

# Ensure uv is available
_ := $(shell command -v $(UV) >/dev/null 2>&1 || (echo "Error: uv is not installed or not in PATH. Install: https://github.com/astral-sh/uv" && exit 1))

.DEFAULT_GOAL := all

.PHONY: all
all: lint test generate ## Run linting, tests, and generation targets

# ------------------------------------------------------------------------------
# Core Targets
# ------------------------------------------------------------------------------
.PHONY: install
install: ## Sync dependencies from uv.lock
	$(UV) sync --all-extras

.PHONY: format
format: ## Format code via Ruff (CLI wrapper)
	$(CLI) dev format

.PHONY: lint
lint: ## Lint and type-check via CLI (ruff + pylint + ty)
	$(CLI) dev lint

.PHONY: test
test: ## Run pytest via CLI
	$(CLI) dev test

# ------------------------------------------------------------------------------
# Generation Targets
# ------------------------------------------------------------------------------
.PHONY: generate-banner
generate-banner: ## Generate SVG banner
	$(CLI) generate banner

.PHONY: generate-qr
generate-qr: ## Generate QR code PNG
	$(CLI) generate qr

.PHONY: generate-word-clouds
generate-word-clouds: ## Generate canonical topics/languages word-cloud SVGs
	$(CLI) generate word-cloud --from-topics-md --output-path $(WORDCLOUD_TOPIC_OUTPUT)
	$(CLI) generate word-cloud --from-languages-md --output-path $(WORDCLOUD_LANG_OUTPUT)

.PHONY: generate-generative
generate-generative: ## Generate event-driven generative artwork
	$(CLI) generate generative

.PHONY: generate-animated
generate-animated: ## Generate animated historical artwork SVGs
	$(CLI) generate animated

.PHONY: generate-living-art
generate-living-art: ## Generate living-art outputs (timeline SVG + GIF compatibility)
	$(CLI) generate living-art

.PHONY: generate-skills
generate-skills: ## Generate technology/skills badges
	$(CLI) generate skills

.PHONY: generate-readme-sections
generate-readme-sections: ## Generate dynamic README sections
	$(CLI) generate readme-sections

.PHONY: generate
generate: generate-banner generate-qr generate-word-clouds generate-skills generate-readme-sections ## Generate standard profile assets

.PHONY: generate-all
generate-all: ## Run CLI aggregate generator command
	$(CLI) generate all

# ------------------------------------------------------------------------------
# Maintenance Targets
# ------------------------------------------------------------------------------
.PHONY: clean
clean: ## Remove cache directories and generated files
	$(CLI) dev clean --generated

.PHONY: clean-venv
clean-venv: ## Remove only the virtual environment
	rm -rf .venv

.PHONY: venv
venv: ## Create virtual environment
	$(UV) venv --python 3.13 .venv

.PHONY: update-deps
update-deps: ## Update lockfile to latest compatible versions
	$(CLI) dev update-deps

.PHONY: docs
docs: ## Serve the Fumadocs dev docs site locally
	$(CLI) dev docs

# ------------------------------------------------------------------------------
# Help Target
# ------------------------------------------------------------------------------
.PHONY: help
help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-28s\033[0m %s\n", $$1, $$2}'
