"""
Pattern type enumeration for the SVG banner generator.

This module contains the ``PatternType`` enum, which enumerates every
generative-art variant that the banner system knows about.  It is kept
separate from ``banner.py`` so that lightweight callers (CLI argument
parsers, tests, configuration validators) can import the enum without
pulling in the heavy ``svgwrite`` / ``numpy`` dependencies that the rest
of ``banner.py`` requires.

Active members
--------------
* ``LORENZ`` / ``NEURAL`` / ``FLOW`` / ``MICRO`` / ``AIZAWA`` — used by
  ``generate_banner()`` in ``banner.py``
* ``CLIFFORD`` — ``draw_clifford()`` is called by ``generative.py``
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
    CLIFFORD = "clifford"
