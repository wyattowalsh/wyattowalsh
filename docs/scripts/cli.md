# Command Line Interface (CLI)

This project uses Typer to provide a command-line interface.

## `readme` CLI

The `readme` CLI is the primary interface for interacting with this project's README generation and management features.

### Installation

To use the CLI, ensure you have the project installed, preferably in editable mode with the necessary dependencies:

```bash
uv pip install -e . "wyattowalsh[all]"
```

### Usage

Once installed, you can access the CLI using `uv run readme`:

```bash
uv run readme --help
```

This will display the available commands and options.

#### Example: Hello Command

```bash
uv run readme hello --name "Your Name"
```

This will output:

```
Hello Your Name!
```