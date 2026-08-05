"""Soft-fail contract for the shared SVGO optimize helper."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.svg_optimize import optimize_with_svgo


def test_optimize_with_svgo_missing_binary_does_not_raise(tmp_path: Path) -> None:
    svg = tmp_path / "sample.svg"
    svg.write_text("<svg xmlns='http://www.w3.org/2000/svg'></svg>", encoding="utf-8")

    with patch("scripts.svg_optimize.subprocess.run", side_effect=FileNotFoundError):
        optimize_with_svgo(svg)  # must not raise


def test_optimize_with_svgo_nonzero_exit_does_not_raise(tmp_path: Path) -> None:
    svg = tmp_path / "sample.svg"
    svg.write_text("<svg xmlns='http://www.w3.org/2000/svg'></svg>", encoding="utf-8")
    err = subprocess.CalledProcessError(1, "svgo", stderr="boom")

    with patch("scripts.svg_optimize.subprocess.run", side_effect=err):
        optimize_with_svgo(svg)  # must not raise


def test_optimize_with_svgo_success_invokes_svgo(tmp_path: Path) -> None:
    svg = tmp_path / "sample.svg"
    svg.write_text("<svg xmlns='http://www.w3.org/2000/svg'></svg>", encoding="utf-8")
    mock_run = MagicMock(return_value=subprocess.CompletedProcess(["svgo"], 0))

    with patch("scripts.svg_optimize.subprocess.run", mock_run):
        optimize_with_svgo(svg)

    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert args[0] == "svgo"
    assert str(svg) in args


def test_banner_optimize_with_svgo_delegates_to_shared(tmp_path: Path) -> None:
    from scripts import banner as banner_mod

    svg = tmp_path / "b.svg"
    svg.write_text("<svg/>", encoding="utf-8")
    with patch("scripts.svg_optimize.optimize_with_svgo") as shared:
        banner_mod.optimize_with_svgo(str(svg))
        shared.assert_called_once_with(str(svg))


def test_readme_svg_writer_does_not_call_optimize(tmp_path: Path) -> None:
    """Card SVGs keep CSS classes; writer must not run destructive SVGO."""
    from scripts.readme_svg import SvgAssetWriter

    with patch("scripts.svg_optimize.optimize_with_svgo") as shared:
        path = SvgAssetWriter(tmp_path).write("card", '<svg class="section-title"/>')
        assert path.is_file()
        assert 'class="section-title"' in path.read_text(encoding="utf-8")
        shared.assert_not_called()
