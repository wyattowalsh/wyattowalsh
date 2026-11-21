"""Render the profile's contact buttons from its published, offline brand artwork."""

from collections.abc import Sequence
from dataclasses import dataclass
from html import escape
from pathlib import Path
from urllib.parse import urlsplit

from defusedxml import ElementTree

from .config import ReadmeSocialLink

_SHARED_ASSETS = Path(__file__).resolve().parents[1] / ".github/assets/img/readme"
_SVG = "{http://www.w3.org/2000/svg}"
# Only the labels and brands with reviewed 115 px artwork use a button.
_ARTWORK = {
    ("w4w.dev", "w4w.dev"): ("w4w-dev", "", "Wyatt Walsh’s website, w4w.dev"),
    ("linkedin.com", "LinkedIn"): (
        "linkedin",
        "/in/wyattowalsh",
        "Wyatt Walsh on LinkedIn",
    ),
    ("kaggle.com", "Kaggle"): ("kaggle", "/wyattowalsh", "Wyatt Walsh on Kaggle"),
    ("x.com", "X.com"): ("x-com", "/wyattowalsh", "Wyatt Walsh on X"),
}


def _anchor(link: ReadmeSocialLink, body: str) -> str:
    return f'<a href="{escape(link.url, quote=True)}">{body}</a>'


def native_contact_links(links: Sequence[ReadmeSocialLink]) -> str:
    return " · ".join(_anchor(link, escape(link.label)) for link in links)


def _button(filename: str, label: str) -> str:
    original = ElementTree.parse(_SHARED_ASSETS / filename).getroot()
    image = original.find(f"{_SVG}image")
    line = original.find(f"{_SVG}rect[@height='3']")
    icon = image.get("href", "") if image is not None else ""
    accent = line.get("fill", "") if line is not None else ""
    if (
        not icon.startswith(("data:image/png;base64,", "data:image/svg+xml;base64,"))
        or not accent
    ):
        raise ValueError(f"Missing published contact artwork in {filename}")
    title = escape(label)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="115" height="44" viewBox="0 0 115 44" role="img" aria-labelledby="title">
  <title id="title">{title}</title>
  <style>
    @media (prefers-color-scheme: dark) {{
      .body {{ fill: #161b22; stroke: #657181; }}
      .label {{ fill: #e6edf3; }}
      .arrow {{ stroke: #b7c2cc; }}
    }}
  </style>
  <rect class="body" x=".5" y=".5" width="114" height="43" rx="8" fill="#ffffff" stroke="#8793a1"/>
  <path d="M8 1.5h99" stroke="{escape(accent)}" stroke-width="2" stroke-linecap="round"/>
  <image x="7" y="10" width="24" height="24" href="{escape(icon)}" preserveAspectRatio="xMidYMid meet"/>
  <text class="label" x="36" y="27" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="14" font-weight="600" fill="#1f2328">{title}</text>
  <path class="arrow" d="M99 26l8-8m-6 0h6v6" fill="none" stroke="#59636e" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""  # noqa: E501 -- preserve the published SVG serialization


@dataclass(frozen=True)
class ContactSections:
    opening: str
    footer: str
    files: dict[str, str]


def render_profile_contacts(
    links: Sequence[ReadmeSocialLink], directory: Path, *, images: bool
) -> ContactSections:
    """Prepare both sections and their complete SVG family before publishing."""
    footer = native_contact_links(links)
    if not images:
        return ContactSections(footer, footer, {})

    buttons = []
    files = {}
    for link in links:
        target = urlsplit(link.url)
        host = (target.hostname or "").removeprefix("www.")
        artwork = _ARTWORK.get((host, link.label))
        if artwork is None:
            buttons.append(_anchor(link, escape(link.label)))
            continue
        slug, profile_path, profile_alt = artwork
        alt = escape(
            profile_alt if target.path.rstrip("/") == profile_path else link.label
        )
        filename = f"connect-{slug}.svg"
        files[filename] = _button(filename, link.label)
        src = escape((directory / filename).as_posix(), quote=True)
        buttons.append(
            _anchor(link, f'<img src="{src}" width="115" height="44" alt="{alt}"/>')
        )

    opening = (
        '<p align="center">\n  ' + "\n  ".join(buttons) + "\n</p>" if files else footer
    )
    return ContactSections(opening, footer, files)
