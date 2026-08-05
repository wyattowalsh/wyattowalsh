"""Deterministic seed hashing and lightweight CLI arg parsing."""

from __future__ import annotations

import hashlib


def parse_cli_args(
    argv: list[str], extra_keys: dict[str, type] | None = None
) -> dict[str, str | int | bool | None]:
    """Parse common CLI args: --profile, --only, plus extras.

    Boolean flags (type=bool) are standalone (no value argument).
    """
    result: dict[str, str | int | bool | None] = {"profile": None, "only": None}
    keys: dict[str, tuple[str, type]] = {
        "--profile": ("profile", str),
        "--only": ("only", str),
    }
    if extra_keys:
        keys.update({f"--{k.replace('_', '-')}": (k, v) for k, v in extra_keys.items()})
    i = 0
    while i < len(argv):
        if argv[i] in keys:
            name, typ = keys[argv[i]]
            if typ is bool:
                result[name] = True
                i += 1
            elif i + 1 < len(argv):
                result[name] = typ(argv[i + 1])
                i += 2
            else:
                import sys

                print(
                    f"Warning: flag {argv[i]} has no value, ignoring", file=sys.stderr
                )
                i += 1
        else:
            i += 1
    return result


def seed_hash(m: dict) -> str:
    """Deterministic SHA-256 hex digest from metrics dict."""
    s = "-".join(
        str(m.get(k, 0))
        for k in sorted(m.keys())
        if k not in ("label", "repos", "contributions_monthly")
    )
    return hashlib.sha256(s.encode()).hexdigest()


def hex_frac(h: str, a: int, b: int) -> float:
    """Extract a 0-1 float from hex slice h[a:b]."""
    return int(h[a:b], 16) / (16 ** (b - a))


def _seed_hash(seed_str: str) -> str:
    """SHA-256 hex digest of a seed string."""
    return hashlib.sha256(seed_str.encode()).hexdigest()


def _hex_slice(h: str, start: int, end: int) -> float:
    """Extract a normalized float [0, 1) from hex digest slice."""
    return int(h[start:end], 16) / (16 ** (end - start))
