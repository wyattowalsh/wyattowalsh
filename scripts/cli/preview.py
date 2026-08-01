"""Local preview — run a generator into a disposable output directory."""

from __future__ import annotations

import shutil
import tempfile
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer

from ..utils import console, get_logger

logger = get_logger(module=__name__)


class PreviewTarget(StrEnum):
    BANNER = "banner"
    QR = "qr"
    WORD_CLOUD = "word-cloud"
    README_SECTIONS = "readme-sections"
    SKILLS = "skills"
    GENERATIVE = "generative"


def preview(
    target: Annotated[
        PreviewTarget,
        typer.Argument(help="Generator to preview."),
    ],
    output_dir: Annotated[
        Path | None,
        typer.Option(
            "--output-dir",
            "-o",
            help="Preview directory (default: temp dir under .cache/readme-preview).",
        ),
    ] = None,
    keep: Annotated[
        bool,
        typer.Option(
            "--keep/--no-keep",
            help="Keep the preview directory (default: keep).",
        ),
    ] = True,
) -> None:
    """Run *target* into a local preview directory and print output paths."""
    if output_dir is None:
        cache_root = Path(".cache") / "readme-preview"
        cache_root.mkdir(parents=True, exist_ok=True)
        output_dir = Path(tempfile.mkdtemp(prefix=f"{target.value}-", dir=cache_root))
    else:
        output_dir = output_dir.expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"[dim]Preview output:[/dim] {output_dir}")

    try:
        if target is PreviewTarget.BANNER:
            from .generate import banner

            banner(output_path=output_dir / "banner.svg")
        elif target is PreviewTarget.QR:
            from .generate import qr

            qr(output_path=output_dir / "qr.png")
        elif target is PreviewTarget.WORD_CLOUD:
            from .generate import word_cloud

            word_cloud(output_path=output_dir / "wordcloud.svg", from_topics_md=True)
        elif target is PreviewTarget.README_SECTIONS:
            from .generate import readme_sections

            # Copy current README so section rewrites land in the preview dir.
            src_readme = Path("README.md")
            dest_readme = output_dir / "README.md"
            if src_readme.is_file():
                shutil.copy2(src_readme, dest_readme)
            readme_sections(output_path=dest_readme)
        elif target is PreviewTarget.SKILLS:
            # Skills injects into the live README; preview only documents that.
            from .generate import skills

            console.print(
                "[yellow]skills[/] injects into the repo README "
                "(no isolated output path). Running against the project root."
            )
            skills()
        elif target is PreviewTarget.GENERATIVE:
            from .generate import generative_art

            generative_art(output_path=output_dir)
        else:
            console.print(f"[bold red]Unsupported preview target:[/] {target}")
            raise typer.Exit(code=1)
    except typer.Exit:
        raise
    except (OSError, ValueError, RuntimeError, ImportError) as exc:
        console.print(f"[bold red]Preview failed:[/bold red] {exc}")
        if not keep and output_dir.exists():
            shutil.rmtree(output_dir, ignore_errors=True)
        raise typer.Exit(code=1) from exc

    produced = sorted(p for p in output_dir.rglob("*") if p.is_file())
    if produced:
        console.print("[bold green]Produced:[/bold green]")
        for path in produced[:40]:
            console.print(f"  {path}")
        if len(produced) > 40:
            console.print(f"  … and {len(produced) - 40} more")
    else:
        console.print("[yellow]No files produced (generator may have skipped).[/]")

    console.print(f"[bold]Preview dir:[/bold] {output_dir}")
    if not keep:
        shutil.rmtree(output_dir, ignore_errors=True)
        console.print("[dim]Preview directory removed (--no-keep).[/dim]")
