"""Helpers for living-art artifact manifests and preview galleries."""

from __future__ import annotations

import json
import mimetypes
import os
import re
import shutil
import tempfile
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from html import escape
from pathlib import Path
from typing import Any

from PIL import Image, ImageSequence

from .timelapse import DEFAULT_PUBLISHED_MAX_FRAMES, MIN_PUBLISHED_RUNTIME_MS

MANIFEST_FILENAME = "living-art-manifest.json"
GALLERY_FILENAME = "living-art-preview.html"
DEFAULT_PUBLIC_SURFACE_DIR = Path("docs/public/showcase")
MANIFEST_VERSION = 2
# Derived from the accepted 2026-08-12 six-style baseline with bounded encoding
# headroom. Changes are intentional contract updates, not self-adjusting limits.
LIVING_ART_BYTE_BUDGETS = {
    "living-ferrofluid.gif": 3_800_000,
    "living-genetic.gif": 2_400_000,
    "living-inkgarden.gif": 7_200_000,
    "living-lenia.gif": 1_200_000,
    "living-physarum.gif": 2_400_000,
    "living-topo.gif": 10_000_000,
}
LIVING_ART_TOTAL_BYTE_BUDGET = sum(LIVING_ART_BYTE_BUDGETS.values())
LIVING_ART_CANONICAL_DIMENSIONS = (400, 400)
LIVING_ART_CANONICAL_LOOP = 0
LIVING_ART_MIN_FRAME_COUNT = 2
LIVING_ART_MAX_FRAME_COUNT = DEFAULT_PUBLISHED_MAX_FRAMES
LIVING_ART_MIN_RUNTIME_MS = MIN_PUBLISHED_RUNTIME_MS
_MANIFEST_RUN_SPECIFIC_FIELDS = frozenset({"generated_at", "output_dir"})

LIVING_ART_STYLE_LABELS = {
    "inkgarden": "Ink Garden",
    "topo": "Topography",
    "genetic": "Genetic Landscape",
    "physarum": "Physarum",
    "lenia": "Lenia",
    "ferrofluid": "Ferrofluid",
}
LIVING_ART_STYLE_KEYS = tuple(LIVING_ART_STYLE_LABELS.keys())
_CHANNEL_LABELS = {
    "timelapse_gif": "Timelapse GIFs",
}


def _light_dark_variant(raw_variant: str | None, *, default: str = "default") -> str:
    return "dark" if raw_variant == "-dark" else default


_STYLE_KEYS = "|".join(re.escape(k) for k in LIVING_ART_STYLE_LABELS)
_TIMELAPSE_RE = re.compile(rf"^living-({_STYLE_KEYS})(-dark)?\.gif$")


def _sha256_file(path: Path) -> str:
    """Return a streaming SHA-256 digest for *path*."""
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _gif_metadata(path: Path) -> dict[str, int | list[int] | None]:
    """Read deterministic display metadata from a valid GIF asset."""
    with Image.open(path) as image:
        if image.format != "GIF":
            raise ValueError(f"Living-art asset is not a GIF: {path}")

        durations = [
            max(0, int(frame.info.get("duration", 0)))
            for frame in ImageSequence.Iterator(image)
        ]
        loop = image.info.get("loop")
        return {
            "width": image.width,
            "height": image.height,
            "frames": len(durations),
            "duration_ms": sum(durations),
            "durations_ms": durations,
            "loop": loop if isinstance(loop, int) else None,
        }


def _asset_descriptor(path: Path) -> dict[str, Any] | None:
    m = _TIMELAPSE_RE.match(path.name)
    if m:
        style, raw_variant = m.groups()
        media_metadata = _gif_metadata(path)
        return {
            "name": path.name,
            "path": path.name,
            "url": None,
            "style": style,
            "style_label": LIVING_ART_STYLE_LABELS.get(style, style),
            "channel": "timelapse_gif",
            "variant": _light_dark_variant(raw_variant),
            "backend": "repo",
            "media_type": mimetypes.guess_type(path.name)[0] or "image/gif",
            "bytes": path.stat().st_size,
            "sha256": _sha256_file(path),
            **media_metadata,
        }

    return None


def build_living_art_manifest(output_dir: Path) -> dict[str, Any]:
    """Scan an output directory and describe the current living-art artifacts."""
    output_dir = Path(output_dir)
    assets: list[dict[str, Any]] = []
    if output_dir.exists():
        for path in sorted(output_dir.iterdir()):
            if not path.is_file():
                continue
            descriptor = _asset_descriptor(path)
            if descriptor is not None:
                assets.append(descriptor)
            elif path.name.startswith("living-") and path.suffix.lower() == ".gif":
                raise ValueError(f"Unsupported living-art GIF: {path.name}")

    assets.sort(
        key=lambda item: (
            item["channel"],
            item["style_label"],
            item["variant"],
            item["name"],
        )
    )
    counts = Counter(asset["channel"] for asset in assets)
    return {
        "manifest_version": MANIFEST_VERSION,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "output_dir": str(output_dir),
        "total_assets": len(assets),
        "total_bytes": sum(asset["bytes"] for asset in assets),
        "counts": {
            "timelapse_gif": counts.get("timelapse_gif", 0),
        },
        "styles": sorted({asset["style"] for asset in assets}),
        "assets": assets,
    }


def validate_living_art_byte_budgets(
    manifest: dict[str, Any],
    *,
    budgets: Mapping[str, int] | None = None,
    total_budget: int | None = None,
) -> None:
    """Reject canonical GIFs that violate reviewed media or byte contracts."""
    effective_budgets = LIVING_ART_BYTE_BUDGETS if budgets is None else budgets
    effective_total = (
        LIVING_ART_TOTAL_BYTE_BUDGET if total_budget is None else total_budget
    )
    assets = manifest.get("assets")
    if not isinstance(assets, list):
        raise ValueError("Living-art manifest has no asset list")

    violations: list[str] = []
    observed_total = 0
    for asset in assets:
        if not isinstance(asset, dict):
            violations.append("manifest contains a non-object asset")
            continue
        name = asset.get("name")
        observed = asset.get("bytes")
        if not isinstance(name, str) or not isinstance(observed, int) or observed < 0:
            violations.append("manifest asset has invalid name/bytes metadata")
            continue
        if name not in effective_budgets:
            violations.append(f"unexpected canonical asset: {name}")
            continue
        observed_total += observed
        budget = effective_budgets[name]
        if observed > budget:
            violations.append(f"{name}: observed={observed} budget={budget}")
        width = asset.get("width")
        height = asset.get("height")
        if (width, height) != LIVING_ART_CANONICAL_DIMENSIONS:
            required_width, required_height = LIVING_ART_CANONICAL_DIMENSIONS
            violations.append(
                f"{name}: dimensions={width!r}x{height!r} "
                f"required={required_width}x{required_height}"
            )
        loop = asset.get("loop")
        if loop != LIVING_ART_CANONICAL_LOOP:
            violations.append(
                f"{name}: loop={loop!r} required={LIVING_ART_CANONICAL_LOOP}"
            )
        frames = asset.get("frames")
        if (
            not isinstance(frames, int)
            or isinstance(frames, bool)
            or not LIVING_ART_MIN_FRAME_COUNT <= frames <= LIVING_ART_MAX_FRAME_COUNT
        ):
            violations.append(
                f"{name}: frames={frames!r} required="
                f"{LIVING_ART_MIN_FRAME_COUNT}..{LIVING_ART_MAX_FRAME_COUNT}"
            )
        duration_ms = asset.get("duration_ms")
        if (
            not isinstance(duration_ms, int)
            or isinstance(duration_ms, bool)
            or duration_ms < LIVING_ART_MIN_RUNTIME_MS
        ):
            violations.append(
                f"{name}: duration_ms={duration_ms!r} "
                f"required>={LIVING_ART_MIN_RUNTIME_MS}"
            )
        durations_ms = asset.get("durations_ms")
        if not isinstance(durations_ms, list) or not all(
            isinstance(duration, int) and not isinstance(duration, bool)
            for duration in durations_ms
        ):
            violations.append(
                f"{name}: durations_ms={durations_ms!r} required=integer list"
            )
        else:
            valid_durations_ms = [
                duration
                for duration in durations_ms
                if isinstance(duration, int) and not isinstance(duration, bool)
            ]
            nonpositive_indexes = [
                index
                for index, duration in enumerate(valid_durations_ms)
                if duration <= 0
            ]
            if nonpositive_indexes:
                violations.append(
                    f"{name}: nonpositive frame durations at indexes="
                    f"{nonpositive_indexes}"
                )
            if (
                isinstance(frames, int)
                and not isinstance(frames, bool)
                and len(valid_durations_ms) != frames
            ):
                violations.append(
                    f"{name}: duration_count={len(valid_durations_ms)} frames={frames}"
                )
            if (
                isinstance(duration_ms, int)
                and not isinstance(duration_ms, bool)
                and sum(valid_durations_ms) != duration_ms
            ):
                violations.append(
                    f"{name}: duration_ms={duration_ms} "
                    f"durations_sum={sum(valid_durations_ms)}"
                )

    valid_names = [
        asset.get("name")
        for asset in assets
        if isinstance(asset, dict) and isinstance(asset.get("name"), str)
    ]
    duplicate_names = sorted(
        name for name, count in Counter(valid_names).items() if count > 1
    )
    if duplicate_names:
        violations.append(f"duplicate canonical assets: {', '.join(duplicate_names)}")
    observed_names = set(valid_names)
    missing = sorted(set(effective_budgets) - observed_names)
    if missing:
        violations.append(f"missing canonical assets: {', '.join(missing)}")
    if observed_total > effective_total:
        violations.append(
            f"canonical total: observed={observed_total} budget={effective_total}"
        )

    if violations:
        raise ValueError(
            "Living-art media/byte contract violation: " + "; ".join(violations)
        )


def _canonical_living_art_names() -> tuple[str, ...]:
    """Return the exact reviewed filenames for the published GIF fleet."""
    return tuple(sorted(LIVING_ART_BYTE_BUDGETS))


def _require_real_directory(directory: Path, *, label: str) -> list[Path]:
    """Return directory entries without following a directory symlink."""
    directory = Path(directory)
    if directory.is_symlink():
        raise ValueError(f"{label} must not be a symlink: {directory}")
    if not directory.exists():
        raise ValueError(f"{label} does not exist: {directory}")
    if not directory.is_dir():
        raise ValueError(f"{label} is not a directory: {directory}")
    return list(directory.iterdir())


def _validate_canonical_inventory(
    directory: Path,
    *,
    label: str,
    exact_directory: bool,
) -> None:
    """Require the exact six canonical, regular, non-symlink GIFs."""
    directory = Path(directory)
    entries = _require_real_directory(directory, label=label)
    expected_names = set(_canonical_living_art_names())
    relevant_entries = (
        entries
        if exact_directory
        else [
            entry
            for entry in entries
            if entry.name.startswith("living-") and entry.suffix.lower() == ".gif"
        ]
    )
    observed_names = {entry.name for entry in relevant_entries}
    missing_names = sorted(expected_names - observed_names)
    unexpected_names = sorted(observed_names - expected_names)

    issues: list[str] = []
    if missing_names:
        issues.append(f"missing={missing_names}")
    if unexpected_names:
        issues.append(f"unexpected={unexpected_names}")

    for name in sorted(expected_names & observed_names):
        path = directory / name
        if path.is_symlink() or not path.is_file():
            issues.append(f"not a regular non-symlink file: {name}")

    if issues:
        raise ValueError(f"{label} inventory mismatch: " + "; ".join(issues))


def _stable_manifest_payload(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Drop only fields that are expected to vary by materialization run."""
    return {
        key: value
        for key, value in manifest.items()
        if key not in _MANIFEST_RUN_SPECIFIC_FIELDS
    }


def _assert_stable_manifests_match(
    first: Mapping[str, Any],
    second: Mapping[str, Any],
    *,
    context: str,
) -> None:
    """Require semantic identity apart from the two run-specific fields."""
    if _stable_manifest_payload(first) != _stable_manifest_payload(second):
        raise ValueError(f"Living-art manifest stable payload mismatch: {context}")


def _validated_canonical_manifest(
    directory: Path,
    *,
    label: str,
    exact_directory: bool,
) -> dict[str, Any]:
    """Validate inventory and media contracts without mutating the directory."""
    _validate_canonical_inventory(
        directory,
        label=label,
        exact_directory=exact_directory,
    )
    manifest = build_living_art_manifest(directory)
    validate_living_art_byte_budgets(manifest)
    return manifest


def _write_text_atomic(path: Path, content: str) -> None:
    """Replace one generated text file without following an existing symlink."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw_temp_path = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        text=True,
    )
    temp_path = Path(raw_temp_path)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(content)
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def _copy_file_atomic(source: Path, destination: Path) -> None:
    """Copy one validated file through a sibling before atomic replacement."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw_temp_path = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
    )
    os.close(descriptor)
    temp_path = Path(raw_temp_path)
    try:
        shutil.copy2(source, temp_path)
        os.replace(temp_path, destination)
    finally:
        temp_path.unlink(missing_ok=True)


def _is_managed_surface_name(name: str) -> bool:
    """Return whether *name* belongs to a generated living-art surface."""
    return name in {MANIFEST_FILENAME, GALLERY_FILENAME} or (
        name.startswith("living-") and Path(name).suffix.lower() == ".gif"
    )


@dataclass(frozen=True, slots=True)
class _ManagedSurfaceSnapshot:
    """Private rollback journal for the managed files in one live surface."""

    directory: Path
    backup_dir: Path
    directory_existed: bool
    file_hashes: tuple[tuple[str, str], ...]


def _snapshot_managed_surface(
    directory: Path,
    backup_dir: Path,
    *,
    label: str,
) -> _ManagedSurfaceSnapshot:
    """Copy every managed file into a private rollback journal."""
    directory = Path(directory)
    _validate_surface_destination(directory, label=label)
    directory_existed = directory.exists()
    backup_dir.mkdir(parents=True, exist_ok=False)
    file_hashes: list[tuple[str, str]] = []
    if directory_existed:
        for source in sorted(directory.iterdir()):
            if not _is_managed_surface_name(source.name):
                continue
            if source.is_symlink() or not source.is_file():
                raise ValueError(
                    f"{label} contains a managed path that is not a regular "
                    f"non-symlink file: {source.name}"
                )
            destination = backup_dir / source.name
            shutil.copy2(source, destination)
            source_hash = _sha256_file(source)
            if _sha256_file(destination) != source_hash:
                raise OSError(f"Living-art rollback snapshot checksum failed: {source}")
            file_hashes.append((source.name, source_hash))
    return _ManagedSurfaceSnapshot(
        directory=directory,
        backup_dir=backup_dir,
        directory_existed=directory_existed,
        file_hashes=tuple(file_hashes),
    )


def _restore_managed_surface(snapshot: _ManagedSurfaceSnapshot) -> None:
    """Best-effort restore one managed surface without touching collateral."""
    errors: list[str] = []
    try:
        if snapshot.directory.is_symlink():
            raise RuntimeError(
                f"rollback destination became a symlink: {snapshot.directory}"
            )
        if snapshot.directory.exists() and not snapshot.directory.is_dir():
            raise RuntimeError(
                f"rollback destination is not a directory: {snapshot.directory}"
            )
        snapshot.directory.mkdir(parents=True, exist_ok=True)
        if snapshot.directory.is_symlink() or not snapshot.directory.is_dir():
            raise RuntimeError(
                f"rollback destination is unsafe after creation: {snapshot.directory}"
            )
    except OSError as error:
        raise RuntimeError(
            f"unable to recreate rollback destination {snapshot.directory}: {error}"
        ) from error

    for path in list(snapshot.directory.iterdir()):
        if not _is_managed_surface_name(path.name):
            continue
        try:
            if path.is_symlink() or path.is_file():
                path.unlink()
            else:
                raise OSError(f"managed rollback path is not a file: {path}")
        except BaseException as error:
            errors.append(f"remove {path.name}: {error}")

    for name, _expected_hash in snapshot.file_hashes:
        try:
            _copy_file_atomic(snapshot.backup_dir / name, snapshot.directory / name)
        except BaseException as error:
            errors.append(f"restore {name}: {error}")

    try:
        observed_names = {
            path.name
            for path in snapshot.directory.iterdir()
            if _is_managed_surface_name(path.name)
        }
        expected_names = {name for name, _digest in snapshot.file_hashes}
        if observed_names != expected_names:
            errors.append(
                "managed inventory mismatch after rollback: "
                f"observed={sorted(observed_names)}, expected={sorted(expected_names)}"
            )
        for name, expected_hash in snapshot.file_hashes:
            restored_path = snapshot.directory / name
            if restored_path.is_symlink() or not restored_path.is_file():
                errors.append(f"not a regular non-symlink file after rollback: {name}")
            elif _sha256_file(restored_path) != expected_hash:
                errors.append(f"checksum mismatch after rollback: {name}")
    except BaseException as error:
        errors.append(f"verify rollback: {error}")

    if not snapshot.directory_existed:
        try:
            snapshot.directory.rmdir()
        except OSError:
            # A parent or an injected concurrent writer may have added collateral.
            # It is outside the managed rollback journal and must not be removed.
            pass

    if errors:
        raise RuntimeError("; ".join(errors))


def _rollback_managed_surfaces(
    snapshots: tuple[_ManagedSurfaceSnapshot, ...],
) -> None:
    """Attempt every rollback and report the complete set of failures."""
    errors: list[str] = []
    for snapshot in reversed(snapshots):
        try:
            _restore_managed_surface(snapshot)
        except BaseException as error:
            errors.append(f"{snapshot.directory}: {type(error).__name__}: {error}")
    if errors:
        raise RuntimeError("; ".join(errors))


def _paths_overlap(first: Path, second: Path) -> bool:
    """Return whether either resolved path contains the other."""
    first_resolved = first.resolve()
    second_resolved = second.resolve()
    return (
        first_resolved == second_resolved
        or first_resolved.is_relative_to(second_resolved)
        or second_resolved.is_relative_to(first_resolved)
    )


def _validate_surface_destination(directory: Path, *, label: str) -> None:
    """Reject destination shapes that could redirect or obstruct publication."""
    directory = Path(directory)
    if directory.is_symlink():
        raise ValueError(f"{label} must not be a symlink: {directory}")
    if not directory.exists():
        return
    if not directory.is_dir():
        raise ValueError(f"{label} is not a directory: {directory}")

    managed_names = {MANIFEST_FILENAME, GALLERY_FILENAME}
    for entry in directory.iterdir():
        is_living_gif = (
            entry.name.startswith("living-") and entry.suffix.lower() == ".gif"
        )
        is_legacy_stage = entry.name == ".living-art-sync"
        if (entry.name in managed_names or is_living_gif) and (
            entry.is_symlink() or not entry.is_file()
        ):
            raise ValueError(
                f"{label} contains a managed path that is not a regular "
                f"non-symlink file: {entry.name}"
            )
        if is_legacy_stage and (entry.is_symlink() or not entry.is_dir()):
            raise ValueError(
                f"{label} contains an unsafe legacy staging path: {entry.name}"
            )


def _render_gallery(manifest: dict[str, Any]) -> str:
    grouped: dict[str, list[dict[str, Any]]] = {key: [] for key in _CHANNEL_LABELS}
    for asset in manifest["assets"]:
        grouped.setdefault(asset["channel"], []).append(asset)

    sections: list[str] = []
    for channel in ("timelapse_gif",):
        assets = grouped.get(channel) or []
        if not assets:
            continue
        cards = []
        for asset in assets:
            meta = (
                f"{escape(asset['style_label'])} · "
                f"{escape(asset['variant'])} · "
                f"{asset['bytes'] / 1024:.1f} KB"
            )
            cards.append(
                "\n".join(
                    [
                        '<article class="asset-card">',
                        f'<a href="{escape(asset["path"])}">',
                        (
                            f'<img src="{escape(asset["path"])}" '
                            f'alt="{escape(asset["style_label"])} preview" '
                            'loading="lazy"/>'
                        ),
                        "</a>",
                        f"<h3>{escape(asset['name'])}</h3>",
                        f"<p>{meta}</p>",
                        "</article>",
                    ]
                )
            )
        sections.append(
            "\n".join(
                [
                    "<section>",
                    f"<h2>{escape(_CHANNEL_LABELS[channel])}</h2>",
                    '<div class="asset-grid">',
                    *cards,
                    "</div>",
                    "</section>",
                ]
            )
        )

    empty_state = ""
    if manifest["total_assets"] == 0:
        empty_state = (
            '<p class="empty-state">'
            "No living-art assets were found in this directory yet."
            "</p>"
        )

    summary_items = "".join(
        f"<li><strong>{count}</strong> {escape(_CHANNEL_LABELS[channel])}</li>"
        for channel, count in manifest["counts"].items()
    )
    sections_markup = "\n".join(sections)
    return (
        """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Living Art Preview Gallery</title>
  <style>
    :root { color-scheme: light dark; }
    body {
      font-family: ui-serif, Georgia, serif;
      margin: 0;
      padding: 32px;
      background: #f4efe6;
      color: #211c18;
    }
    main { max-width: 1180px; margin: 0 auto; }
    h1, h2, h3 { margin: 0; }
    p, li { line-height: 1.5; }
    .summary {
      display: flex;
      gap: 18px;
      flex-wrap: wrap;
      padding: 0;
      margin: 18px 0 28px;
      list-style: none;
    }
    .summary li {
      background: rgba(255,255,255,0.75);
      border: 1px solid rgba(33,28,24,0.12);
      border-radius: 999px;
      padding: 10px 14px;
    }
    section { margin-top: 30px; }
    .asset-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 18px;
      margin-top: 14px;
    }
    .asset-card {
      background: rgba(255,255,255,0.78);
      border: 1px solid rgba(33,28,24,0.12);
      border-radius: 18px;
      padding: 14px;
      box-shadow: 0 12px 30px rgba(33,28,24,0.08);
    }
    .asset-card a {
      display: block;
      aspect-ratio: 1 / 1;
      background: #ddd4c6;
      border-radius: 12px;
      overflow: hidden;
    }
    .asset-card img {
      width: 100%;
      height: 100%;
      object-fit: contain;
      display: block;
      background: linear-gradient(135deg, #f8f3eb, #e6dccd);
    }
    .asset-card h3 { font-size: 0.98rem; margin-top: 12px; }
    .asset-card p { margin: 6px 0 0; color: #5d5146; font-size: 0.92rem; }
    .empty-state { margin-top: 18px; color: #5d5146; }
    @media (prefers-color-scheme: dark) {
      body { background: #151412; color: #efe6d7; }
      .summary li, .asset-card {
        background: rgba(35,32,29,0.88);
        border-color: rgba(239,230,215,0.12);
      }
      .asset-card p, .empty-state { color: #b8ac9c; }
      .asset-card a { background: #26211c; }
      .asset-card img { background: linear-gradient(135deg, #1f1b17, #2e2924); }
    }
  </style>
</head>
<body>
  <main>
    <h1>Living Art Preview Gallery</h1>
    <p>Canonical living-art timelapse GIFs discovered in this output directory.</p>
    <ul class="summary">__SUMMARY__</ul>
    __EMPTY__
    __SECTIONS__
  </main>
</body>
</html>
""".replace("__SUMMARY__", summary_items)
        .replace("__EMPTY__", empty_state)
        .replace("__SECTIONS__", sections_markup)
    )


def _read_manifest(path: Path) -> dict[str, Any]:
    """Read a persisted manifest object for postcondition verification."""
    try:
        raw_manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(
            f"Unable to read persisted living-art manifest: {path}"
        ) from error
    if not isinstance(raw_manifest, dict):
        raise ValueError(f"Persisted living-art manifest is not an object: {path}")
    return raw_manifest


def _validate_persisted_surface(
    directory: Path,
    expected_manifest: Mapping[str, Any],
    *,
    label: str,
) -> tuple[dict[str, Any], str]:
    """Re-read and recompute one generated surface after publication."""
    manifest_path = directory / MANIFEST_FILENAME
    gallery_path = directory / GALLERY_FILENAME
    persisted_manifest = _read_manifest(manifest_path)
    expected_object = dict(expected_manifest)
    if persisted_manifest != expected_object:
        raise ValueError(f"{label} persisted manifest differs from generated object")

    try:
        persisted_gallery = gallery_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ValueError(
            f"Unable to read persisted living-art gallery: {gallery_path}"
        ) from error
    if persisted_gallery != _render_gallery(expected_object):
        raise ValueError(f"{label} persisted gallery differs from generated object")

    recomputed_manifest = _validated_canonical_manifest(
        directory,
        label=label,
        exact_directory=False,
    )
    _assert_stable_manifests_match(
        persisted_manifest,
        recomputed_manifest,
        context=f"{label} persisted versus recomputed",
    )
    return persisted_manifest, persisted_gallery


def _validate_persisted_surface_pair(
    output_dir: Path,
    output_manifest: Mapping[str, Any],
    public_surface_dir: Path,
    public_manifest: Mapping[str, Any],
) -> None:
    """Verify persisted primary and docs surfaces are semantic mirrors."""
    persisted_output, output_gallery = _validate_persisted_surface(
        output_dir,
        output_manifest,
        label="primary living-art surface",
    )
    persisted_public, public_gallery = _validate_persisted_surface(
        public_surface_dir,
        public_manifest,
        label="public living-art surface",
    )
    _assert_stable_manifests_match(
        persisted_output,
        persisted_public,
        context="primary versus public persisted surfaces",
    )
    if output_gallery != public_gallery:
        raise ValueError("Primary and public living-art galleries differ")


def _sync_public_surface(
    output_dir: Path,
    manifest: dict[str, Any],
    public_surface_dir: Path,
) -> dict[str, Any]:
    """Mirror the canonical living-art surface to a public preview directory."""
    public_surface_dir = Path(public_surface_dir)
    _validate_surface_destination(
        public_surface_dir,
        label="public living-art surface",
    )
    if public_surface_dir.resolve() == output_dir.resolve():
        return manifest

    public_surface_dir.parent.mkdir(parents=True, exist_ok=True)
    staging_dir = Path(
        tempfile.mkdtemp(
            prefix=".living-art-sync-",
            dir=public_surface_dir.parent,
        )
    )
    try:
        for asset in manifest["assets"]:
            shutil.copy2(output_dir / asset["path"], staging_dir / asset["path"])

        public_manifest = build_living_art_manifest(staging_dir)
        if set(asset["name"] for asset in public_manifest["assets"]) == set(
            _canonical_living_art_names()
        ):
            validate_living_art_byte_budgets(public_manifest)
        public_manifest["output_dir"] = str(public_surface_dir)
        _assert_stable_manifests_match(
            manifest,
            public_manifest,
            context="primary generated object versus public candidate",
        )
        _write_text_atomic(
            staging_dir / MANIFEST_FILENAME,
            json.dumps(public_manifest, indent=2),
        )
        _write_text_atomic(
            staging_dir / GALLERY_FILENAME,
            _render_gallery(public_manifest),
        )

        public_surface_dir.mkdir(parents=True, exist_ok=True)
        legacy_staging_dir = public_surface_dir / ".living-art-sync"
        if legacy_staging_dir.exists():
            shutil.rmtree(legacy_staging_dir)
        for path in list(public_surface_dir.iterdir()):
            if path.name in {MANIFEST_FILENAME, GALLERY_FILENAME} or (
                path.suffix.lower() == ".gif" and path.name.startswith("living-")
            ):
                path.unlink()

        for path in list(staging_dir.iterdir()):
            os.replace(path, public_surface_dir / path.name)
    finally:
        shutil.rmtree(staging_dir, ignore_errors=True)

    return public_manifest


def sync_living_art_artifacts(
    output_dir: Path,
    *,
    public_surface_dir: Path | None = None,
) -> tuple[Path, Path, dict[str, Any]]:
    """Rewrite the manifest and preview gallery from the files that exist now."""
    output_dir = Path(output_dir)
    _validate_surface_destination(output_dir, label="primary living-art surface")
    if public_surface_dir is not None:
        _validate_surface_destination(
            Path(public_surface_dir),
            label="public living-art surface",
        )
    manifest = _validated_canonical_manifest(
        output_dir,
        label="primary living-art surface",
        exact_directory=False,
    )
    manifest_path = output_dir / MANIFEST_FILENAME
    gallery_path = output_dir / GALLERY_FILENAME
    _write_text_atomic(manifest_path, json.dumps(manifest, indent=2))
    _write_text_atomic(gallery_path, _render_gallery(manifest))

    if (
        public_surface_dir is None
        or Path(public_surface_dir).resolve() == output_dir.resolve()
    ):
        _validate_persisted_surface(
            output_dir,
            manifest,
            label="primary living-art surface",
        )
    else:
        public_path = Path(public_surface_dir)
        public_manifest = _sync_public_surface(output_dir, manifest, public_path)
        _validate_persisted_surface_pair(
            output_dir,
            manifest,
            public_path,
            public_manifest,
        )

    return manifest_path, gallery_path, manifest


def stage_living_art_fleet(
    source_dir: Path,
    stage_dir: Path,
) -> dict[str, Any]:
    """Materialize an exact-six, media-only artifact from a generated surface."""
    source_dir = Path(source_dir)
    stage_dir = Path(stage_dir)
    source_manifest = _validated_canonical_manifest(
        source_dir,
        label="living-art producer source",
        exact_directory=False,
    )
    if _paths_overlap(source_dir, stage_dir):
        raise ValueError("Living-art source and stage directories must not overlap")
    if stage_dir.is_symlink():
        raise ValueError(f"Living-art stage must not be a symlink: {stage_dir}")
    if stage_dir.exists():
        if not stage_dir.is_dir():
            raise ValueError(f"Living-art stage is not a directory: {stage_dir}")
        if any(stage_dir.iterdir()):
            raise ValueError(f"Living-art stage must be empty: {stage_dir}")

    stage_dir.parent.mkdir(parents=True, exist_ok=True)
    candidate_dir = Path(
        tempfile.mkdtemp(
            prefix=f".{stage_dir.name}-candidate-",
            dir=stage_dir.parent,
        )
    )
    try:
        for name in _canonical_living_art_names():
            shutil.copy2(source_dir / name, candidate_dir / name)
        candidate_manifest = _validated_canonical_manifest(
            candidate_dir,
            label="living-art producer candidate",
            exact_directory=True,
        )
        _assert_stable_manifests_match(
            source_manifest,
            candidate_manifest,
            context="producer source versus staged candidate",
        )

        if stage_dir.exists():
            stage_dir.rmdir()
        os.replace(candidate_dir, stage_dir)
    finally:
        shutil.rmtree(candidate_dir, ignore_errors=True)

    persisted_stage = _validated_canonical_manifest(
        stage_dir,
        label="persisted living-art stage",
        exact_directory=True,
    )
    _assert_stable_manifests_match(
        source_manifest,
        persisted_stage,
        context="producer source versus persisted stage",
    )
    return source_manifest


def publish_living_art_fleet(
    stage_dir: Path,
    output_dir: Path,
    *,
    public_surface_dir: Path,
) -> tuple[Path, Path, dict[str, Any]]:
    """Publish an untrusted exact-six artifact and regenerate both surfaces."""
    stage_dir = Path(stage_dir)
    output_dir = Path(output_dir)
    public_surface_dir = Path(public_surface_dir)
    stage_manifest = _validated_canonical_manifest(
        stage_dir,
        label="downloaded living-art stage",
        exact_directory=True,
    )
    if _paths_overlap(stage_dir, output_dir) or _paths_overlap(
        stage_dir, public_surface_dir
    ):
        raise ValueError("Living-art stage must not overlap a destination surface")
    if _paths_overlap(output_dir, public_surface_dir):
        raise ValueError("Primary and public living-art surfaces must not overlap")
    _validate_surface_destination(output_dir, label="primary living-art destination")
    _validate_surface_destination(
        public_surface_dir,
        label="public living-art destination",
    )

    with tempfile.TemporaryDirectory(prefix="living-art-publish-") as temp_root:
        candidate_root = Path(temp_root)
        candidate_output = candidate_root / "primary"
        candidate_public = candidate_root / "public"
        candidate_output.mkdir()
        for name in _canonical_living_art_names():
            shutil.copy2(stage_dir / name, candidate_output / name)
        _, _, candidate_manifest = sync_living_art_artifacts(
            candidate_output,
            public_surface_dir=candidate_public,
        )
        _assert_stable_manifests_match(
            stage_manifest,
            candidate_manifest,
            context="downloaded stage versus isolated publication candidate",
        )

        # Recheck both live destinations immediately before the first mutation.
        _validate_surface_destination(
            output_dir,
            label="primary living-art destination",
        )
        _validate_surface_destination(
            public_surface_dir,
            label="public living-art destination",
        )
        snapshots = (
            _snapshot_managed_surface(
                output_dir,
                candidate_root / "rollback-primary",
                label="primary living-art destination",
            ),
            _snapshot_managed_surface(
                public_surface_dir,
                candidate_root / "rollback-public",
                label="public living-art destination",
            ),
        )
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            for path in list(output_dir.iterdir()):
                if (
                    path.name.startswith("living-")
                    and path.suffix.lower() == ".gif"
                    and path.name not in LIVING_ART_BYTE_BUDGETS
                ):
                    path.unlink()
            for name in _canonical_living_art_names():
                _copy_file_atomic(candidate_output / name, output_dir / name)

            manifest_path, gallery_path, published_manifest = sync_living_art_artifacts(
                output_dir,
                public_surface_dir=public_surface_dir,
            )
            _assert_stable_manifests_match(
                candidate_manifest,
                published_manifest,
                context="isolated candidate versus persisted publication",
            )
        except BaseException as publication_error:
            try:
                _rollback_managed_surfaces(snapshots)
            except BaseException as rollback_error:
                message = (
                    "Living-art publication failed and rollback was incomplete: "
                    f"publication={type(publication_error).__name__}: "
                    f"{publication_error}; rollback={type(rollback_error).__name__}: "
                    f"{rollback_error}"
                )
                raise RuntimeError(message) from publication_error
            raise

    return manifest_path, gallery_path, published_manifest


__all__ = [
    "DEFAULT_PUBLIC_SURFACE_DIR",
    "GALLERY_FILENAME",
    "LIVING_ART_CANONICAL_DIMENSIONS",
    "LIVING_ART_CANONICAL_LOOP",
    "LIVING_ART_MAX_FRAME_COUNT",
    "LIVING_ART_MIN_FRAME_COUNT",
    "LIVING_ART_MIN_RUNTIME_MS",
    "LIVING_ART_STYLE_KEYS",
    "LIVING_ART_STYLE_LABELS",
    "LIVING_ART_BYTE_BUDGETS",
    "LIVING_ART_TOTAL_BYTE_BUDGET",
    "MANIFEST_FILENAME",
    "MANIFEST_VERSION",
    "build_living_art_manifest",
    "publish_living_art_fleet",
    "stage_living_art_fleet",
    "sync_living_art_artifacts",
    "validate_living_art_byte_budgets",
]
