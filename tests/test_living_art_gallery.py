import re

from scripts.art.artifacts import _render_gallery


def test_gallery_links_each_style_once_with_escaped_name_path_and_size() -> None:
    gallery = _render_gallery(
        {
            "assets": [
                {
                    "channel": "timelapse_gif",
                    "style_label": "Leaf & Bloom",
                    "path": "leaf.gif?v=1&frame=2",
                    "bytes": 1536,
                },
                {
                    "channel": "timelapse_gif",
                    "style_label": "Ink Garden",
                    "path": "garden.gif",
                    "bytes": 4096,
                },
            ]
        }
    )
    cards = re.findall(r'<article class="asset-card">(.*?)</article>', gallery, re.S)
    assert len(cards) == 2
    for card, path, label, size in zip(
        cards,
        ("leaf.gif?v=1&amp;frame=2", "garden.gif"),
        ("Leaf &amp; Bloom", "Ink Garden"),
        ("1.5 KB", "4.0 KB"),
        strict=True,
    ):
        assert card.count(f'<a href="{path}">') == 1
        assert f"<h2>{label}</h2></a>" in card
        assert f'<img src="{path}" alt=""' in card
        assert '<source media="(prefers-reduced-motion: reduce)" srcset="data:' in card
        assert f"GIF · {size}" in card
