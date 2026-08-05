#!/usr/bin/env python3
"""Heuristic scorer for README composition skeletons."""

from __future__ import annotations

import re
from pathlib import Path

CANDIDATES = Path(__file__).parent / "candidates"
FIXED_PREFIX_MARKERS = ("banner.svg", "README:TOP_BADGES:START")
FLEET_LOCKS = {
    "featured_min": 10,
    "living_styles": 6,
}


def h2_order(text: str) -> list[str]:
    return re.findall(r"^## (.+)$", text, re.M)


def score(text: str) -> dict:
    order = h2_order(text)
    featured_i = (
        order.index("Featured Projects") if "Featured Projects" in order else 99
    )
    metrics_i = order.index("Metrics") if "Metrics" in order else 99
    living_i = order.index("Living Art") if "Living Art" in order else 99
    # first-fold: content before first ## after connect is not used; use Featured early bonus
    img_before_metrics = 0
    if "Metrics" in order:
        before = text.split("## Metrics", 1)[0]
        img_before_metrics = before.count("<img")
    featured_cards = text.count("featured-card-")
    living = len(set(re.findall(r"living-([a-z]+)\.gif", text)))
    (
        "AI/ML" not in text.split("## Tech Stack", 1)[-1][:400]
        if "## Tech Stack" in text
        else True
    )
    # rough: teaser shields gone if View full stack is first after Tech Stack heading
    tech_body = ""
    if "## Tech Stack" in text:
        tech_body = text.split("## Tech Stack", 1)[1][:200]
    teaser_ok = "View full stack" in tech_body or "<details" in tech_body
    banner_connect = all(m in text[:2500] for m in FIXED_PREFIX_MARKERS)
    featured_before_living = featured_i < living_i
    # weights
    s = 0.0
    s += 25 if featured_i == 0 else (15 if featured_i == 1 else 5)
    s += 20 if featured_before_living else 8
    s += 15 if metrics_i <= 2 else (10 if metrics_i <= 3 else 4)
    s += 15 if living_i <= 3 else 6
    s += 10 if banner_connect else 0
    s += 10 if featured_cards >= FLEET_LOCKS["featured_min"] else 0
    s += 10 if living >= FLEET_LOCKS["living_styles"] else 0
    s += 5 if teaser_ok else 0
    # penalty: too many images before metrics (heavy fold)
    if img_before_metrics > 20:
        s -= 8
    elif img_before_metrics > 14:
        s -= 4
    return {
        "score": round(s, 2),
        "h2": order,
        "featured_cards": featured_cards,
        "living_styles": living,
        "img_before_metrics": img_before_metrics,
        "banner_connect": banner_connect,
        "teaser_ok": teaser_ok,
    }


def main() -> None:
    rows = []
    for path in sorted(CANDIDATES.glob("*.md")):
        data = score(path.read_text())
        data["id"] = path.stem
        rows.append(data)
    rows.sort(key=lambda r: r["score"], reverse=True)
    lines = ["# Composition scores", ""]
    lines.append("| rank | id | score | H2 order | featured | living | img≤metrics |")
    lines.append("|------|----|-------|----------|----------|--------|-------------|")
    for i, r in enumerate(rows, 1):
        lines.append(
            f"| {i} | `{r['id']}` | {r['score']} | {' → '.join(r['h2'])} | "
            f"{r['featured_cards']} | {r['living_styles']} | {r['img_before_metrics']} |"
        )
    winner = rows[0]["id"]
    lines.extend(["", f"**Heuristic winner:** `{winner}`", ""])
    out = Path(__file__).parent / "scores.md"
    out.write_text("\n".join(lines) + "\n")
    (Path(__file__).parent / "winner.json").write_text(
        __import__("json").dumps({"winner": winner, "ranking": rows}, indent=2) + "\n"
    )
    print(out)
    print("winner", winner)


if __name__ == "__main__":
    main()
