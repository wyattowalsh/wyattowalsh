"""Reconcile private metrics artifacts in a disposable finalizer checkout."""

from __future__ import annotations

import argparse
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from .metrics_svg import validate_svg_file
from .profile_metric_family import METRIC_NAMES, metric_files, read_metric_family
from .supplemental_metrics import ASSET_SPECS, validate_supplemental_metrics
from .wakatime_readme import (
    DEFAULT_ARTIFACT_NAME,
    DEFAULT_WAKATIME_SVG_PATH,
    MARKER_END,
    MARKER_START,
    SKIP_MARKER_NAME,
    WAKA_SVG_POINTER,
    apply_waka_section,
)

MANIFEST_NAME = "metrics-supplemental.manifest.json"


def _inventory(stage: Path) -> set[str]:
    names: set[str] = set()
    for entry in stage.iterdir():
        if entry.is_symlink() or not entry.is_file():
            raise ValueError(f"Unexpected non-file in metrics artifact: {entry.name}")
        names.add(entry.name)
    return names


def _waka_enabled(waka: Path) -> bool:
    names = _inventory(waka)
    if names == {SKIP_MARKER_NAME}:
        if not (waka / SKIP_MARKER_NAME).read_text(encoding="utf-8").strip():
            raise ValueError("Empty WakaTime skip marker")
        return False
    svg = waka / DEFAULT_WAKATIME_SVG_PATH.name
    if names != {DEFAULT_ARTIFACT_NAME, *metric_files("wakatime")}:
        raise ValueError("Expected a complete WakaTime family, or a skip marker alone")
    body = (waka / DEFAULT_ARTIFACT_NAME).read_text(encoding="utf-8").strip()
    if body != WAKA_SVG_POINTER or not validate_svg_file(svg).is_valid:
        raise ValueError("Invalid WakaTime section or SVG")
    if ET.parse(svg).getroot().get("aria-label") != "WakaTime coding activity":
        raise ValueError("Expected the generated WakaTime card")
    read_metric_family(waka, "wakatime")
    return True


def publish_metrics(metrics: Path, waka: Path, readme: Path) -> None:
    """Validate both stages before replacing any managed metric or marker."""
    names = _inventory(metrics)
    managed = {f"{spec.asset_name}.svg" for spec in ASSET_SPECS.values()}
    for name in METRIC_NAMES:
        if name != "wakatime":
            managed.update(metric_files(name))
    if names - managed - {MANIFEST_NAME}:
        raise ValueError("Unexpected file in supplemental metrics artifact")
    errors = validate_supplemental_metrics(
        output_dir=metrics, manifest_path=metrics / MANIFEST_NAME
    )
    if errors:
        raise ValueError("; ".join(errors))

    for name in METRIC_NAMES:
        if name == "wakatime":
            continue
        family = metric_files(name)
        if names.intersection(family):
            read_metric_family(metrics, name)

    enabled = _waka_enabled(waka)
    content = readme.read_text(encoding="utf-8")
    if (
        content.count(MARKER_START) != 1
        or content.count(MARKER_END) != 1
        or content.index(MARKER_END) < content.index(MARKER_START)
    ):
        raise ValueError("Expected one WakaTime marker pair in README")
    output_dir = readme.parent / DEFAULT_WAKATIME_SVG_PATH.parent
    active_waka = enabled
    if not enabled and any((output_dir / f).exists() for f in metric_files("wakatime")):
        read_metric_family(output_dir, "wakatime")
        active_waka = True
    for filename in (*managed, *metric_files("wakatime")):
        target = output_dir / filename
        if target.is_symlink() or (target.exists() and not target.is_file()):
            raise ValueError(f"Invalid metric destination: {filename}")
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename in sorted(managed):
        if filename in names:
            shutil.copyfile(metrics / filename, output_dir / filename)
        else:
            (output_dir / filename).unlink(missing_ok=True)
    if enabled:
        for filename in metric_files("wakatime"):
            shutil.copyfile(waka / filename, output_dir / filename)
    apply_waka_section(readme, WAKA_SVG_POINTER if active_waka else "")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--waka", type=Path, required=True)
    parser.add_argument("--readme", type=Path, required=True)
    args = parser.parse_args()
    publish_metrics(args.metrics, args.waka, args.readme)


if __name__ == "__main__":
    main()
