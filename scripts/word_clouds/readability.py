"""Shared readability and orientation policy for word cloud layouts."""

from __future__ import annotations

import random
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field


DEFAULT_STANDARD_ROTATIONS = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 90.0, -6.0, 6.0)
DEFAULT_LARGE_WORD_ROTATIONS = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 90.0)


@dataclass(frozen=True, slots=True)
class LayoutReadabilityPolicy:
    """Runtime policy for layout readability and orientation."""

    standard_rotations: tuple[float, ...] = DEFAULT_STANDARD_ROTATIONS
    large_word_rotations: tuple[float, ...] = DEFAULT_LARGE_WORD_ROTATIONS
    fallback_rotation: float = 0.0
    large_word_threshold_ratio: float = 0.60
    reading_flow_weight: float = 2.25
    target_aspect_ratio: float = 1.80
    landscape_bias_weight: float = 1.35

    @property
    def valid_rotations(self) -> tuple[float, ...]:
        seen: list[float] = []
        for rotation in (*self.standard_rotations, *self.large_word_rotations, self.fallback_rotation):
            if rotation not in seen:
                seen.append(rotation)
        return tuple(seen)

    def is_large_word(self, font_size: float, min_font_size: float, max_font_size: float) -> bool:
        cutoff = min_font_size + (max_font_size - min_font_size) * self.large_word_threshold_ratio
        return font_size >= cutoff

    def choose_rotation(self, rng: random.Random, *, is_large_word: bool = False) -> float:
        choices = self.large_word_rotations if is_large_word else self.standard_rotations
        if not choices:
            return self.fallback_rotation
        return float(rng.choice(choices))

    def snap_rotation(self, rotation: float) -> float:
        valid = self.valid_rotations or (self.fallback_rotation,)
        return float(min(valid, key=lambda candidate: abs(candidate - rotation)))


class LayoutReadabilitySettings(BaseModel):
    """Serializable layout readability settings for config and generator models."""

    model_config = ConfigDict(extra="forbid")

    standard_rotations: list[float] = Field(
        default_factory=lambda: list(DEFAULT_STANDARD_ROTATIONS)
    )
    large_word_rotations: list[float] = Field(
        default_factory=lambda: list(DEFAULT_LARGE_WORD_ROTATIONS)
    )
    fallback_rotation: float = 0.0
    large_word_threshold_ratio: float = Field(default=0.60, ge=0.0, le=1.0)
    reading_flow_weight: float = Field(default=2.25, ge=0.0)
    target_aspect_ratio: float = Field(default=1.80, ge=1.0)
    landscape_bias_weight: float = Field(default=1.35, ge=0.0)

    def to_policy(self) -> LayoutReadabilityPolicy:
        return LayoutReadabilityPolicy(
            standard_rotations=tuple(self.standard_rotations),
            large_word_rotations=tuple(self.large_word_rotations),
            fallback_rotation=float(self.fallback_rotation),
            large_word_threshold_ratio=float(self.large_word_threshold_ratio),
            reading_flow_weight=float(self.reading_flow_weight),
            target_aspect_ratio=float(self.target_aspect_ratio),
            landscape_bias_weight=float(self.landscape_bias_weight),
        )


DEFAULT_LAYOUT_READABILITY_POLICY = LayoutReadabilityPolicy()


def coerce_layout_readability_policy(
    value: LayoutReadabilityPolicy | LayoutReadabilitySettings | dict[str, object] | None,
) -> LayoutReadabilityPolicy:
    """Normalize settings-like readability input to a runtime policy."""

    if value is None:
        return DEFAULT_LAYOUT_READABILITY_POLICY
    if isinstance(value, LayoutReadabilityPolicy):
        return value
    if isinstance(value, LayoutReadabilitySettings):
        return value.to_policy()
    if isinstance(value, dict):
        return LayoutReadabilitySettings(**value).to_policy()
    raise TypeError(f"Unsupported layout_readability value: {type(value)!r}")