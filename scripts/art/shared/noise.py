"""Gradient noise (Perlin-like) and named presets."""

from __future__ import annotations

import math

import numpy as np

# ---------------------------------------------------------------------------
# Gradient noise (Perlin-like)
# ---------------------------------------------------------------------------


class Noise2D:
    """2D gradient noise with fBm support."""

    def __init__(self, seed: int = 0):
        rng = np.random.default_rng(seed)
        self.perm = np.tile(rng.permutation(256).astype(np.int32), 2)
        a = rng.uniform(0, 2 * np.pi, 256)
        self.grads = np.column_stack([np.cos(a), np.sin(a)])

    @staticmethod
    def _fade(t: float) -> float:
        return t * t * t * (t * (t * 6 - 15) + 10)

    def noise(self, x: float, y: float) -> float:
        xi = int(math.floor(x)) & 255
        yi = int(math.floor(y)) & 255
        xf = x - math.floor(x)
        yf = y - math.floor(y)
        u = self._fade(xf)
        v = self._fade(yf)
        aa = self.perm[self.perm[xi] + yi]
        ab = self.perm[self.perm[xi] + yi + 1]
        ba = self.perm[self.perm[xi + 1] + yi]
        bb = self.perm[self.perm[xi + 1] + yi + 1]
        ga = self.grads[aa % 256]
        gb = self.grads[ab % 256]
        gc = self.grads[ba % 256]
        gd = self.grads[bb % 256]
        x1 = (ga[0] * xf + ga[1] * yf) + u * (
            (gc[0] * (xf - 1) + gc[1] * yf) - (ga[0] * xf + ga[1] * yf)
        )
        x2 = (gb[0] * xf + gb[1] * (yf - 1)) + u * (
            (gd[0] * (xf - 1) + gd[1] * (yf - 1)) - (gb[0] * xf + gb[1] * (yf - 1))
        )
        return x1 + v * (x2 - x1)

    def fbm(self, x: float, y: float, octaves: int = 4) -> float:
        val = 0.0
        amp = 1.0
        freq = 1.0
        total = 0.0
        for _ in range(octaves):
            val += amp * self.noise(x * freq, y * freq)
            total += amp
            amp *= 0.5
            freq *= 2
        return val / total


NOISE_PRESETS: dict[str, dict[str, float | int]] = {
    "calm": {"frequency": 0.003, "octaves": 2, "step_size": 2.5, "persistence": 0.55},
    "balanced": {
        "frequency": 0.005,
        "octaves": 4,
        "step_size": 4.0,
        "persistence": 0.5,
    },
    "terrain": {
        "frequency": 0.008,
        "octaves": 5,
        "step_size": 3.5,
        "persistence": 0.58,
    },
    "storm": {"frequency": 0.014, "octaves": 6, "step_size": 5.0, "persistence": 0.68},
}


def resolve_noise_preset(
    name: str | None = None,
    **overrides: float | int | None,
) -> dict[str, float | int]:
    """Resolve a named noise preset with optional numeric overrides."""
    preset_name = name if name in NOISE_PRESETS else "balanced"
    preset = dict(NOISE_PRESETS[preset_name])
    for key, value in overrides.items():
        if value is not None:
            preset[key] = value
    return preset
