"""Development tools — replaces the Makefile with Typer subcommands."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Annotated

import typer

from ..utils import console, get_logger

logger = get_logger(module=__name__)

dev_app = typer.Typer(
    name="dev",
    help="[bold]Development tools[/bold] — lint, format, test, and clean.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

SRC_DIRS = ["scripts", "tests"]


def _run(
    cmd: list[str], *, cwd: str | None = None, check: bool = True
) -> subprocess.CompletedProcess[bytes]:
    """Run a subprocess, streaming output.

    Raises typer.Exit on failure when *check* is True.
    """
    console.print(f"[dim]$ {' '.join(cmd)}[/dim]")
    result = subprocess.run(cmd, cwd=cwd)
    if check and result.returncode != 0:
        console.print(f"[bold red]Command failed (exit {result.returncode})[/bold red]")
        raise typer.Exit(code=result.returncode)
    return result


def _sync_optional_dependencies(*extras: str, all_extras: bool = False) -> None:
    """Sync optional dependency extras using the project's uv extras contract."""
    cmd = ["uv", "sync"]
    if all_extras:
        cmd.append("--all-extras")
    else:
        cmd.append("--inexact")
        for extra in extras:
            cmd.extend(["--extra", extra])
    _run(cmd)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@dev_app.command(help="Sync all dependencies from the lockfile.")
def install() -> None:
    """Install/sync project dependencies."""
    _sync_optional_dependencies(all_extras=True)
    console.print("[bold green]Dependencies synced.[/bold green]")


@dev_app.command(
    name="format",
    help="Format code with [cyan]ruff[/cyan].",
)
def format_code() -> None:
    """Auto-format source code."""
    _sync_optional_dependencies("format")
    _run(["uv", "run", "--", "python", "-m", "ruff", "check", "--fix", *SRC_DIRS])
    _run(["uv", "run", "--", "python", "-m", "ruff", "format", *SRC_DIRS])
    console.print("[bold green]Formatting complete.[/bold green]")


@dev_app.command(
    help="Lint with [cyan]ruff[/cyan], [cyan]pylint[/cyan], and [cyan]ty[/cyan].",
)
def lint() -> None:
    """Run all linters."""
    _sync_optional_dependencies("lint")
    _run(["uv", "run", "--", "python", "-m", "ruff", "check", *SRC_DIRS])
    _run(["uv", "run", "--", "python", "-m", "pylint", *SRC_DIRS])
    _run(["uv", "run", "--", "ty", "check", *SRC_DIRS])
    console.print("[bold green]All linters passed.[/bold green]")


@dev_app.command(help="Run the test suite with [cyan]pytest[/cyan].")
def test(
    coverage: Annotated[
        bool,
        typer.Option("--coverage/--no-coverage", help="Enable coverage reporting."),
    ] = True,
    filter_expr: Annotated[
        str | None,
        typer.Option("-k", help="pytest -k filter expression."),
    ] = None,
    marker: Annotated[
        str | None,
        typer.Option("-m", help="pytest -m marker expression."),
    ] = None,
) -> None:
    """Run pytest."""
    _sync_optional_dependencies("test")
    cmd = ["uv", "run", "--", "python", "-m", "pytest"]
    if not coverage:
        cmd.append("--no-cov")
    if filter_expr:
        cmd.extend(["-k", filter_expr])
    if marker:
        cmd.extend(["-m", marker])
    _run(cmd)


@dev_app.command(help="Remove caches, build artifacts, and generated files.")
def clean(
    venv: Annotated[
        bool,
        typer.Option("--venv/--no-venv", help="Also remove .venv directory."),
    ] = False,
    generated: Annotated[
        bool,
        typer.Option(
            "--generated/--no-generated",
            help="Also remove generated assets.",
        ),
    ] = False,
) -> None:
    """Clean up caches and optional artifacts."""
    removed = 0

    # Walk and remove __pycache__ dirs
    for p in Path(".").rglob("__pycache__"):
        shutil.rmtree(p, ignore_errors=True)
        removed += 1

    # Remove specific dirs
    for name in [".pytest_cache", "logs"]:
        target = Path(name)
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
            removed += 1

    # Remove coverage files
    for cov in Path(".").glob(".coverage*"):
        cov.unlink(missing_ok=True)
        removed += 1

    if venv:
        venv_dir = Path(".venv")
        if venv_dir.exists():
            shutil.rmtree(venv_dir)
            removed += 1
            console.print("[yellow]Removed .venv[/yellow]")

    if generated:
        gen_dir = Path(".github/assets/img")
        for pat in [
            "banner*.svg",
            "qr*.png",
            "wordcloud_*.svg",
            "generative-*.svg",
            "animated-*.svg",
        ]:
            for f in gen_dir.glob(pat):
                f.unlink(missing_ok=True)
                removed += 1

    console.print(f"[bold green]Cleaned {removed} items.[/bold green]")


@dev_app.command(help="Serve the Fumadocs dev docs site locally.")
def docs() -> None:
    """Start the local documentation server."""
    docs_dir = Path("docs")
    if not docs_dir.exists():
        console.print("[bold red]Error:[/bold red] docs/ directory not found.")
        raise typer.Exit(code=1)
    _run(["pnpm", "dev"], cwd="docs")


@dev_app.command(
    name="update-deps",
    help="Update all dependencies to latest compatible versions.",
)
def update_deps() -> None:
    """Recompile the lockfile with latest versions."""
    _run(["uv", "lock", "--upgrade"])
    console.print(
        "[bold green]Lockfile updated. "
        "Run [cyan]readme dev install[/cyan] to sync.[/bold green]"
    )
