"""scripts.cli — Typer CLI package for the readme project."""

from ..config import DEFAULT_CONFIG_PATH
from ._app import app

__all__ = ["app", "DEFAULT_CONFIG_PATH"]
