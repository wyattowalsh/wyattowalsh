"""Helpers for living-art artifact manifests and preview galleries."""

from __future__ import annotations

import json
import re
import shutil
from collections import Counter
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any

MANIFEST_FILENAME = "living-art-manifest.json"
GALLERY_FILENAME = "living-art-preview.html"
DEFAULT_PUBLIC_SURFACE_DIR = Path("docs/public/showcase")

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


def _asset_descriptor(path: Path) -> dict[str, Any] | None:
    m = _TIMELAPSE_RE.match(path.name)
    if m:
        style, raw_variant = m.groups()
        return {
            "name": path.name,
            "path": path.name,
            "style": style,
            "style_label": LIVING_ART_STYLE_LABELS.get(style, style),
            "channel": "timelapse_gif",
            "variant": _light_dark_variant(raw_variant),
            "bytes": path.stat().st_size,
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
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "output_dir": str(output_dir),
        "total_assets": len(assets),
        "counts": {
            "timelapse_gif": counts.get("timelapse_gif", 0),
        },
        "styles": sorted({asset["style"] for asset in assets}),
        "assets": assets,
    }


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


def _sync_public_surface(
    output_dir: Path,
    manifest: dict[str, Any],
    public_surface_dir: Path,
) -> None:
    """Mirror the canonical living-art surface to a public preview directory."""
    public_surface_dir = Path(public_surface_dir)
    public_surface_dir.mkdir(parents=True, exist_ok=True)

    if public_surface_dir.resolve() == output_dir.resolve():
        return

    staging_dir = public_surface_dir / ".living-art-sync"
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True)

    for asset in manifest["assets"]:
        shutil.copy2(output_dir / asset["path"], staging_dir / asset["path"])

    public_manifest = build_living_art_manifest(staging_dir)
    public_manifest["output_dir"] = str(public_surface_dir)
    (staging_dir / MANIFEST_FILENAME).write_text(
        json.dumps(public_manifest, indent=2),
        encoding="utf-8",
    )
    (staging_dir / GALLERY_FILENAME).write_text(
        _render_gallery(public_manifest),
        encoding="utf-8",
    )

    for path in list(public_surface_dir.iterdir()):
        if not path.is_file():
            continue
        if path.name in {MANIFEST_FILENAME, GALLERY_FILENAME}:
            path.unlink()
            continue
        if path.suffix.lower() == ".gif" and path.name.startswith("living-"):
            path.unlink()

    for path in list(staging_dir.iterdir()):
        shutil.move(str(path), public_surface_dir / path.name)
    staging_dir.rmdir()


def sync_living_art_artifacts(
    output_dir: Path,
    *,
    public_surface_dir: Path | None = None,
) -> tuple[Path, Path, dict[str, Any]]:
    """Rewrite the manifest and preview gallery from the files that exist now."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = build_living_art_manifest(output_dir)
    manifest_path = output_dir / MANIFEST_FILENAME
    gallery_path = output_dir / GALLERY_FILENAME
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    gallery_path.write_text(_render_gallery(manifest), encoding="utf-8")

    if public_surface_dir is not None:
        _sync_public_surface(output_dir, manifest, public_surface_dir)

    return manifest_path, gallery_path, manifest


__all__ = [
    "DEFAULT_PUBLIC_SURFACE_DIR",
    "GALLERY_FILENAME",
    "LIVING_ART_STYLE_KEYS",
    "LIVING_ART_STYLE_LABELS",
    "MANIFEST_FILENAME",
    "build_living_art_manifest",
    "sync_living_art_artifacts",
]
