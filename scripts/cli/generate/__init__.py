"""Generate subcommands package — domain modules register on generate_app."""

from __future__ import annotations

import sys  # re-exported for tests that patch scripts.cli.generate.sys

from ...config import load_config

# Import domain modules so @generate_app.command decorators register.
from . import all_cmd as _all_cmd  # noqa: F401
from . import art as _art  # noqa: F401
from . import banner as _banner  # noqa: F401
from . import qr as _qr  # noqa: F401
from . import readme_cmd as _readme_cmd  # noqa: F401
from . import word_cloud as _word_cloud  # noqa: F401
from ._common import (
    _load_project_config,
    _refresh_living_art_artifacts,
    generate_app,
    logger,
)
from .all_cmd import all_assets
from .art import animated, generative_art, living_art, timelapse
from .banner import banner
from .qr import qr
from .readme_cmd import readme_sections, skills, supplemental_metrics, wakatime
from .word_cloud import (
    _wc_from_languages,
    _wc_from_topics,
    _wc_import,
    word_cloud,
)

__all__ = [
    "generate_app",
    "load_config",
    "banner",
    "qr",
    "word_cloud",
    "generative_art",
    "animated",
    "living_art",
    "timelapse",
    "skills",
    "supplemental_metrics",
    "readme_sections",
    "wakatime",
    "all_assets",
    "_wc_import",
    "_wc_from_topics",
    "_wc_from_languages",
    "_load_project_config",
    "_refresh_living_art_artifacts",
    "logger",
    "sys",
]
