"""
Pattern type enumeration for the SVG banner generator.

This module contains the ``PatternType`` enum, which enumerates every
generative-art variant that the banner system knows about.  It is kept
separate from ``banner.py`` so that lightweight callers (CLI argument
parsers, tests, configuration validators) can import the enum without
pulling in the heavy ``svgwrite`` / ``numpy`` dependencies that the rest
of ``banner.py`` requires.

Dead variants
-------------
The following enum members are defined for forward-compatibility or
historical reasons but have **no corresponding draw call** in
``generate_banner()`` and are not reachable via the CLI:

* ``REACTION``
* ``FLAME``
* ``PDJ``
* ``IKEDA``

``CLIFFORD`` is **active** — ``draw_clifford()`` in ``banner.py`` is
called by ``generative.py``.
"""

from __future__ import annotations

import enum


class PatternType(enum.Enum):
    """
    Enumeration for the different types of generative art patterns
    that can be included in the banner.
    """

    LORENZ = "lorenz"
    NEURAL = "neural"
    FLOW = "flow"
    MICRO = "micro"
    AIZAWA = "aizawa"
    # Dead variants — no draw function implemented; CLI dispatch will skip these
    REACTION = "reaction"  # Note: REACTION is defined but not used
    CLIFFORD = "clifford"  # Active: draw_clifford() used by generative.py
    FLAME = "flame"  # Note: FLAME is defined but not used
    PDJ = "pdj"  # Note: PDJ is defined but not used
    IKEDA = "ikeda"  # Note: IKEDA is defined but not used
