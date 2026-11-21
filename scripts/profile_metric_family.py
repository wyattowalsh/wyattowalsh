"""Bind each public metric summary and text disclosure to its full chart."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, date, datetime
from html import escape
from pathlib import Path
from typing import cast

import defusedxml.ElementTree as ET

from .metrics_svg import validate_svg_file

METRIC_NAMES = ("metrics-languages", "metrics-habits", "wakatime", "metrics-music")
METRICS_START = "<!-- README:METRICS:START -->"
METRICS_END = "<!-- README:METRICS:END -->"
_RECEIPT = re.compile(
    r"<!-- profile-metric name=([\w-]+) chart=([0-9a-f]{64}) "
    r"summary=([0-9a-f]{64}) saved=(\d{4}-\d{2}-\d{2}) -->"
)
_SVG_NS = "{http://www.w3.org/2000/svg}"


def metric_files(name: str) -> tuple[str, str, str]:
    if name not in METRIC_NAMES:
        raise ValueError(f"Unknown profile metric: {name}")
    return f"{name}.svg", f"summary-{name}.svg", f"detail-{name}.md"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _check_disclosure(name: str, text: str) -> None:
    if (
        not text.startswith("<details>\n<summary>")
        or not text.endswith("</details>")
        or text.count("<summary>") != 1
        or text.count("</summary>") != 1
        or text.count("<details>") != 1
        or text.count("</details>") != 1
        or re.search(r"<(?!/?(?:summary|details)>)[!/a-zA-Z]", text)
        or f"](.github/assets/img/{name}.svg)" not in text
    ):
        raise ValueError(f"Invalid public disclosure for {name}")


def write_metric_detail(
    directory: Path, name: str, disclosure: str, *, saved: date | None = None
) -> Path:
    """Write the final sibling only after both SVGs exist."""
    chart, summary, detail = metric_files(name)
    body = disclosure.strip()
    _check_disclosure(name, body)
    day = saved or datetime.now(UTC).date()
    header = (
        f"<!-- profile-metric name={name} chart={_digest(directory / chart)} "
        f"summary={_digest(directory / summary)} saved={day.isoformat()} -->"
    )
    path = directory / detail
    path.write_text(f"{header}\n{body}\n", encoding="utf-8")
    return path


def read_metric_family(directory: Path, name: str) -> tuple[str, str, date]:
    """Validate the complete family before publishing or rendering it."""
    chart, summary, detail = (directory / item for item in metric_files(name))
    if not all(f.is_file() and not f.is_symlink() for f in (chart, summary, detail)):
        raise ValueError(f"Incomplete profile metric family: {name}")
    header, _, body = detail.read_text(encoding="utf-8").partition("\n")
    receipt = _RECEIPT.fullmatch(header)
    if not receipt or receipt.groups()[:3] != (name, _digest(chart), _digest(summary)):
        raise ValueError(f"Mismatched profile metric family: {name}")
    saved = date.fromisoformat(receipt.group(4))
    _check_disclosure(name, body.strip())
    if not all(validate_svg_file(f).is_valid for f in (chart, summary)):
        raise ValueError(f"Invalid profile metric SVG for {name}")
    description = ET.parse(summary).getroot().findtext(f"{_SVG_NS}desc")
    if not isinstance(description, str) or not description.strip():
        raise ValueError(f"Missing summary description for {name}")
    return cast(str, description).strip(), body.strip(), saved


def render_metric_section(directory: Path) -> str:
    cards: list[str] = []
    disclosures: list[str] = []
    dates: dict[str, str] = {}
    for name in METRIC_NAMES:
        if not any((directory / f).exists() for f in metric_files(name)):
            if name in {"metrics-languages", "metrics-habits"}:
                raise ValueError(f"Missing required profile metric: {name}")
            continue
        alt, disclosure, saved = read_metric_family(directory, name)
        dates[name] = saved.isoformat()
        disclosures.append(disclosure)
        cards.append(
            f'<img src=".github/assets/img/summary-{name}.svg" width="360" '
            f'alt="{escape(alt, quote=True)}" />'
        )
    if len(set(dates.values())) == 1:
        note = f"Charts saved on **{next(iter(dates.values()))}**."
    else:
        labels = {
            "metrics-languages": "Languages",
            "metrics-habits": "GitHub activity",
            "wakatime": "WakaTime",
            "metrics-music": "Spotify",
        }
        note = (
            "Chart dates: "
            + " · ".join(f"{labels[name]} {saved}" for name, saved in dates.items())
            + "."
        )
    return "\n\n".join(
        [note, '<p align="center">\n' + "\n".join(cards) + "\n</p>", *disclosures]
    )
