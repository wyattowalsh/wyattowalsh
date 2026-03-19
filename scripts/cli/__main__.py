"""Allow ``python -m scripts.cli`` to invoke the CLI app."""

from ._app import app

if __name__ == "__main__":
    app()
