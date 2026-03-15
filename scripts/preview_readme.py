"""Render README.md like GitHub and export a PNG screenshot.

Usage:
    uv run python -m scripts.preview_readme [--readme README.md] [--output preview.png] [--width 1280]
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

import markdown

CSS = """
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans",
        Helvetica, Arial, sans-serif;
    font-size: 16px;
    line-height: 1.5;
    color: #e6edf3;
    background-color: #0d1117;
    max-width: 980px;
    margin: 0 auto;
    padding: 45px;
}
a { color: #58a6ff; text-decoration: none; }
img { max-width: 100%; }
table { border-collapse: collapse; width: 100%; }
td, th { border: 1px solid #30363d; padding: 6px 13px; }
h1, h2, h3, h4, h5, h6 { margin-top: 24px; margin-bottom: 16px; font-weight: 600; border-bottom: 1px solid #30363d; padding-bottom: .3em; }
h1 { font-size: 2em; } h2 { font-size: 1.5em; } h3 { font-size: 1.25em; }
code { background: #161b22; padding: 0.2em 0.4em; border-radius: 6px; font-size: 85%; }
pre { background: #161b22; padding: 16px; border-radius: 6px; overflow: auto; }
pre code { background: none; padding: 0; }
details { border: 1px solid #30363d; border-radius: 6px; padding: 8px 16px; margin: 8px 0; }
summary { cursor: pointer; font-weight: 600; }
blockquote { border-left: 4px solid #30363d; color: #9198a1; padding: 0 1em; margin: 0; }
hr { border: none; border-top: 1px solid #30363d; margin: 24px 0; }
"""


def render_readme(readme_path: Path, output_path: Path, width: int = 1280) -> None:
    """Render a markdown file to PNG via Playwright."""
    md_text = readme_path.read_text(encoding="utf-8")

    extensions = ["tables", "fenced_code", "codehilite", "toc", "attr_list", "md_in_html"]
    html_body = markdown.markdown(md_text, extensions=extensions)

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><style>{CSS}</style></head>
<body>{html_body}</body>
</html>"""

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
        f.write(html_doc)
        tmp_html = f.name

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 800})
        page.goto(f"file://{tmp_html}")
        page.wait_for_load_state("networkidle")
        page.screenshot(path=str(output_path), full_page=True)
        browser.close()

    Path(tmp_html).unlink(missing_ok=True)
    print(f"Screenshot saved to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Render README.md as GitHub-style PNG")
    parser.add_argument("--readme", default="README.md", help="Path to README.md")
    parser.add_argument("--output", default="preview.png", help="Output PNG path")
    parser.add_argument("--width", type=int, default=1280, help="Viewport width")
    args = parser.parse_args()

    readme_path = Path(args.readme)
    if not readme_path.exists():
        print(f"Error: {readme_path} not found", file=sys.stderr)
        sys.exit(1)

    render_readme(readme_path, Path(args.output), args.width)


if __name__ == "__main__":
    main()
