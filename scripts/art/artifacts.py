"""Helpers for living-art artifact manifests and preview galleries."""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any

MANIFEST_FILENAME = "living-art-manifest.json"
GALLERY_FILENAME = "living-art-preview.html"

_STYLE_LABELS = {
    "inkgarden": "Ink Garden",
    "topo": "Topography",
}
_CHANNEL_LABELS = {
    "compatibility_gif": "Compatibility GIFs",
    "source_svg": "Source SVGs",
    "timelapse_gif": "Timelapse GIFs",
}


def _light_dark_variant(raw_variant: str | None, *, default: str = "default") -> str:
    return "dark" if raw_variant == "-dark" else default


def _asset_descriptor(path: Path) -> dict[str, Any] | None:
    if path.name in {"inkgarden-growth-animated.svg", "topo-growth-animated.svg"}:
        style = "inkgarden" if path.name.startswith("inkgarden") else "topo"
        return {
            "name": path.name,
            "path": path.name,
            "style": style,
            "style_label": _STYLE_LABELS[style],
            "channel": "source_svg",
            "variant": "default",
            "bytes": path.stat().st_size,
        }

    if path.name in {"inkgarden-growth.gif", "topo-growth.gif"}:
        style = "inkgarden" if path.name.startswith("inkgarden") else "topo"
        return {
            "name": path.name,
            "path": path.name,
            "style": style,
            "style_label": _STYLE_LABELS[style],
            "channel": "compatibility_gif",
            "variant": "default",
            "bytes": path.stat().st_size,
        }

    timelapse_match = re.fullmatch(r"living-(inkgarden|topo)(-dark)?\.gif", path.name)
    if timelapse_match:
        style, raw_variant = timelapse_match.groups()
        return {
            "name": path.name,
            "path": path.name,
            "style": style,
            "style_label": _STYLE_LABELS[style],
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
            "source_svg": counts.get("source_svg", 0),
            "compatibility_gif": counts.get("compatibility_gif", 0),
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
    for channel in ("source_svg", "compatibility_gif", "timelapse_gif"):
        assets = grouped.get(channel) or []
        if not assets:
            continue
        cards = []
        for asset in assets:
            meta = (
                f'{escape(asset["style_label"])} · '
                f'{escape(asset["variant"])} · '
                f'{asset["bytes"] / 1024:.1f} KB'
            )
            cards.append(
                "\n".join(
                    [
                        '<article class="asset-card">',
                        f'<a href="{escape(asset["path"])}">',
                        f'<img src="{escape(asset["path"])}" alt="{escape(asset["style_label"])} preview" loading="lazy"/>',
                        "</a>",
                        f'<h3>{escape(asset["name"])}</h3>',
                        f'<p>{meta}</p>',
                        "</article>",
                    ]
                )
            )
        sections.append(
            "\n".join(
                [
                    "<section>",
                    f'<h2>{escape(_CHANNEL_LABELS[channel])}</h2>',
                    '<div class="asset-grid">',
                    *cards,
                    "</div>",
                    "</section>",
                ]
            )
        )

    empty_state = ""
    if manifest["total_assets"] == 0:
        empty_state = '<p class="empty-state">No living-art assets were found in this directory yet.</p>'

    summary_items = "".join(
        f'<li><strong>{count}</strong> {escape(_CHANNEL_LABELS[channel])}</li>'
        for channel, count in manifest["counts"].items()
    )
    sections_markup = "\n".join(sections)
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Living Art Preview Gallery</title>
  <style>
    :root { color-scheme: light dark; }
    body { font-family: ui-serif, Georgia, serif; margin: 0; padding: 32px; background: #f4efe6; color: #211c18; }
    main { max-width: 1180px; margin: 0 auto; }
    h1, h2, h3 { margin: 0; }
    p, li { line-height: 1.5; }
    .summary { display: flex; gap: 18px; flex-wrap: wrap; padding: 0; margin: 18px 0 28px; list-style: none; }
    .summary li { background: rgba(255,255,255,0.75); border: 1px solid rgba(33,28,24,0.12); border-radius: 999px; padding: 10px 14px; }
    section { margin-top: 30px; }
    .asset-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 18px; margin-top: 14px; }
    .asset-card { background: rgba(255,255,255,0.78); border: 1px solid rgba(33,28,24,0.12); border-radius: 18px; padding: 14px; box-shadow: 0 12px 30px rgba(33,28,24,0.08); }
    .asset-card a { display: block; aspect-ratio: 1 / 1; background: #ddd4c6; border-radius: 12px; overflow: hidden; }
    .asset-card img { width: 100%; height: 100%; object-fit: contain; display: block; background: linear-gradient(135deg, #f8f3eb, #e6dccd); }
    .asset-card h3 { font-size: 0.98rem; margin-top: 12px; }
    .asset-card p { margin: 6px 0 0; color: #5d5146; font-size: 0.92rem; }
    .empty-state { margin-top: 18px; color: #5d5146; }
    @media (prefers-color-scheme: dark) {
      body { background: #151412; color: #efe6d7; }
      .summary li, .asset-card { background: rgba(35,32,29,0.88); border-color: rgba(239,230,215,0.12); }
      .asset-card p, .empty-state { color: #b8ac9c; }
      .asset-card a { background: #26211c; }
      .asset-card img { background: linear-gradient(135deg, #1f1b17, #2e2924); }
    }
  </style>
</head>
<body>
  <main>
    <h1>Living Art Preview Gallery</h1>
    <p>Canonical source SVGs, compatibility GIFs, and timelapse exports discovered in this output directory.</p>
    <ul class="summary">__SUMMARY__</ul>
    __EMPTY__
    __SECTIONS__
  </main>
</body>
</html>
""".replace("__SUMMARY__", summary_items).replace("__EMPTY__", empty_state).replace("__SECTIONS__", sections_markup)


def sync_living_art_artifacts(output_dir: Path) -> tuple[Path, Path, dict[str, Any]]:
    """Rewrite the manifest and preview gallery from the files that exist now."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = build_living_art_manifest(output_dir)
    manifest_path = output_dir / MANIFEST_FILENAME
    gallery_path = output_dir / GALLERY_FILENAME
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    gallery_path.write_text(_render_gallery(manifest), encoding="utf-8")
    return manifest_path, gallery_path, manifest


__all__ = [
    "GALLERY_FILENAME",
    "MANIFEST_FILENAME",
    "build_living_art_manifest",
    "sync_living_art_artifacts",
]