"""
SVG Banner Generator for GitHub Profiles and Web Applications.

This module provides functionality to create dynamic, visually rich SVG banners. It features various generative art patterns, including chaotic attractors (Lorenz, Aizawa), flow fields, and neural network-like structures. These patterns are combined with customizable text, colors, and advanced visual effects such as glassmorphism, glows, and shadows.

The generation process is highly configurable through Pydantic models,
allowing for detailed control over dimensions, color palettes, typography,
visual effects, layout, and specific parameters for each generative pattern.
The `svgwrite` library is used for the underlying SVG creation, while `numpy`
and an optional `noise` module (with a fallback) assist in mathematical
operations and Perlin noise generation.

Key Features:
- Customizable banner dimensions, title, and subtitle.
- Sophisticated color palette system with automatic dark mode variant
  generation.
- Detailed typography settings including font choices, sizes, weights, and
  text effects.
- A suite of visual effects: blur, glassmorphism, Perlin noise, glows,
  shadows, etc.
- Multiple generative art patterns: Lorenz Attractor, Aizawa Attractor,
  Flow Fields, Neural Networks, and Micro Details.
- Layered composition of background, patterns, and foreground elements.
- Optional SVG optimization using the `svgo` command-line tool.
- Command-line interface integration via `scripts.cli` for parameterized
  generation.

The script is structured to separate utility functions (color manipulation,
SVG helpers), configuration models (Pydantic), generative art algorithms,
and the main banner orchestration logic.
"""

import base64
import colorsys
import math
import os
import random
import subprocess
from typing import Any, TypeAlias

import numpy as np
import svgwrite  # type: ignore
from pydantic import BaseModel, Field  # Field is used in Pydantic models later
from svgwrite import filters, gradients, path, shapes  # type: ignore
from svgwrite.container import Group  # type: ignore
from svgwrite.drawing import Drawing  # type: ignore # Specific import

from .utils import get_logger

# Initialize logger for the module
logger = get_logger(module=__name__)

# Module-level RNG instance; re-seeded by generate_banner() for determinism.
_rng: random.Random = random.Random()

# ------------------------------------------------------------------------------
# Constants and Type Aliases
# ------------------------------------------------------------------------------
NodePosition: TypeAlias = tuple[float, float]
"""Type alias for a 2D node position (x, y)."""

Point2D: TypeAlias = tuple[float, float]
"""Type alias for a 2D point (x, y)."""

Point3D: TypeAlias = tuple[float, float, float]
"""Type alias for a 3D point (x, y, z)."""

ColorStop: TypeAlias = tuple[str, float]
"""Type alias for a color stop (color string, position as float 0.0-1.0)."""


# ------------------------------------------------------------------------------
# Enumerations
# ------------------------------------------------------------------------------
# PatternType lives in its own lightweight module (banner_patterns.py) so
# callers that don't need svgwrite/numpy can import it without heavy deps.


# ------------------------------------------------------------------------------
# Utility Models and Classes
# ------------------------------------------------------------------------------
class Point3DModel(BaseModel):
    """
    Represents a 3D point, primarily for calculations in generative art
    algorithms like chaotic attractors.

    This model defines a point in three-dimensional space with x, y, and z
    coordinates. It includes basic vector arithmetic operations (addition
    and scalar multiplication) for convenience within attractor generation
    logic.
    """

    x: float
    y: float
    z: float

    def __add__(self, other: "Point3DModel") -> "Point3DModel":
        """
        Adds two Point3DModel instances component-wise.

        Args:
            other: Another Point3DModel instance to add to this one.

        Returns:
            A new Point3DModel representing the sum of the two points.
        """
        return Point3DModel(x=self.x + other.x, y=self.y + other.y, z=self.z + other.z)

    def __mul__(self, scalar: float) -> "Point3DModel":
        """
        Multiplies the Point3DModel by a scalar value.

        Args:
            scalar: A float scalar value to multiply each component of the
                    point by.

        Returns:
            A new Point3DModel representing the scaled point.
        """
        return Point3DModel(x=self.x * scalar, y=self.y * scalar, z=self.z * scalar)

    def to_tuple(self) -> Point3D:
        """
        Converts the Point3DModel to a tuple representation.

        Returns:
            A tuple (x, y, z) representing the point.
        """
        return (self.x, self.y, self.z)


class NoiseHandler:
    """
    Manages Perlin noise generation for visual effects within the banner.

    This class acts as a wrapper around the optional 'noise' Python module.
    If the 'noise' module is installed and importable, `NoiseHandler` will use
    it to provide true Perlin noise. If the module is not available (e.g., not
    installed in the environment), it gracefully falls back to a simpler
    trigonometric function (`sin(x*c1) * cos(y*c2)`). This fallback produces
    a procedural, wave-like pattern that can substitute for Perlin noise,
    ensuring the banner generation script can always run, albeit with a
    different aesthetic for noise-based effects if the dependency is missing.

    The initialization logic to check for the 'noise' module is performed
    lazily on the first attempt to generate noise and is executed only once
    to avoid repeated import attempts.
    """

    _noise_module_available: bool = False
    _actual_noise_module: Any | None = None  # Stores the imported noise module
    _initialized_flag: bool = False  # Tracks if initialization attempt has occurred

    @classmethod
    def _initialize(cls) -> None:
        """
        Initializes the noise generation mechanism by attempting to import
        'noise'.

        This class method is called before any noise generation if not already
        initialized. It sets internal flags based on whether the 'noise' module
        can be imported. This prevents repeated import attempts.
        """
        if cls._actual_noise_module is None and not cls._initialized_flag:
            try:
                import noise  # type: ignore # External library

                cls._actual_noise_module = noise
                cls._noise_module_available = True
                logger.info("Successfully imported 'noise' module for Perlin noise.")
            except ImportError:
                cls._noise_module_available = False
                logger.warning(
                    "The 'noise' module was not found. Using a fallback "
                    "trigonometric function for Perlin noise. For true Perlin "
                    "noise, consider installing the 'noise' package "
                    "(e.g., `pip install noise` or `uv pip install noise`)."
                )
            cls._initialized_flag = True

    def __init__(self) -> None:
        """
        Constructs a NoiseHandler instance.

        The constructor ensures that the noise generation mechanism is
        initialized by calling the `_initialize` class method.
        """
        NoiseHandler._initialize()

    @staticmethod
    def pnoise2(x: float, y: float, octaves: int = 1) -> float:
        """
        Generates 2D Perlin noise or a fallback procedural pattern.

        If the 'noise' module was successfully imported during initialization,
        this method calls `noise.pnoise2` to generate Perlin noise.
        Otherwise, it uses a simple trigonometric function based on sine and
        cosine waves to produce a deterministic, grid-like pattern as a
        fallback.

        Args:
            x: The x-coordinate for noise generation.
            y: The y-coordinate for noise generation.
            octaves: The number of octaves for Perlin noise. This parameter is
                     only used if the 'noise' module is active.

        Returns:
            A float representing the noise value. For Perlin noise, this is
            typically in the range [-1.0, 1.0]. The fallback function also
            aims for a similar range but produces a different pattern.
        """
        NoiseHandler._initialize()  # Ensure init, esp. if called as static
        if NoiseHandler._noise_module_available and NoiseHandler._actual_noise_module:
            # Type casting to float for consistency
            return float(
                NoiseHandler._actual_noise_module.pnoise2(x, y, octaves=octaves)
            )
        else:
            # Fallback: sine and cosine waves.
            # Creates a predictable, somewhat grid-like pattern.
            # 0.5 scaling keeps output range similar to Perlin noise.
            return float(np.sin(x * 0.1) * np.cos(y * 0.1) * 0.5)


# Initialize the NoiseHandler once globally.
_noise_handler_instance = NoiseHandler()


# ------------------------------------------------------------------------------
# SVG and Color Utility Functions
# ------------------------------------------------------------------------------
def optimize_with_svgo(svg_path: str) -> None:
    """
    Optimizes an SVG file using the SVGO CLI tool.

    If SVGO is not found or an error occurs, a warning is logged.

    Args:
        svg_path: The path to the SVG file to optimize.
    """
    try:
        subprocess.run(["svgo", svg_path], check=True, capture_output=True, text=True)
        logger.info("SVG optimized with SVGO: {svg_path}", svg_path=svg_path)
    except subprocess.CalledProcessError as e:
        logger.warning("SVGO optimization failed with error: {stderr}", stderr=e.stderr)
    except FileNotFoundError:
        logger.warning("SVGO command not found. Skipping SVG optimization.")


def parse_rgba_color(rgba: str) -> tuple[str, float]:
    """
    Parses an RGBA color string into a hex color string and an opacity value.

    Example: "rgba(255, 0, 0, 0.5)" -> ("#ff0000", 0.5)

    Args:
        rgba: The RGBA string (e.g., "rgba(255,255,255,0.3)").

    Returns:
        A tuple containing the hex color string and the opacity (0.0 to 1.0).
        If parsing fails, returns the original string and opacity 1.0.
    """
    if rgba.startswith("rgba(") and rgba.endswith(")"):
        parts = rgba[5:-1].split(",")
        if len(parts) == 4:
            try:
                r = int(parts[0].strip())
                g = int(parts[1].strip())
                b = int(parts[2].strip())
                a = float(parts[3].strip())
                hex_color = f"#{r:02x}{g:02x}{b:02x}"
                return hex_color, a
            except ValueError:
                logger.warning("Invalid RGBA string format: {rgba}", rgba=rgba)
    return rgba, 1.0


def adjust_hue(hex_color: str, degrees: float) -> str:
    """
    Adjusts the hue of a given hex color by a specified number of degrees.

    Args:
        hex_color: The hex color string (e.g., "#ff0000").
        degrees: The amount in degrees to adjust the hue (-360 to 360).

    Returns:
        A new hex color string with the adjusted hue.
    """
    if not hex_color.startswith("#") or len(hex_color) not in (4, 7):
        logger.warning("Invalid hex color format for hue adjustment: {hex_color}", hex_color=hex_color)
        return hex_color

    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join([c * 2 for c in h])  # Expand shorthand #RGB to #RRGGBB

    try:
        r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        logger.warning("Cannot parse RGB components from hex: {hex_color}", hex_color=hex_color)
        return hex_color

    h_val, s_val, v_val = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    h_val = (h_val + degrees / 360.0) % 1.0
    nr, ng, nb = colorsys.hsv_to_rgb(h_val, s_val, v_val)
    return f"#{int(nr * 255):02x}{int(ng * 255):02x}{int(nb * 255):02x}"


def create_linear_gradient(
    dwg: Drawing,
    id_name: str,
    colors: list[str],
    opacities: list[float] | None = None,
    angle: float = 0,
) -> gradients.LinearGradient:
    """
    Creates an SVG linear gradient with multiple color stops.

    Args:
        dwg: The SVG drawing object.
        id_name: The ID to assign to the gradient.
        colors: List of colors for the gradient stops.
        opacities: Optional list of opacity values for each color (defaults to
                   all 1.0).
        angle: The angle in degrees for the gradient direction.

    Returns:
        The created gradient element.
    """
    # Calculate the x1, y1, x2, y2 coordinates based on the angle
    angle_rad = math.radians(angle)
    x2 = 50 + 50 * math.cos(angle_rad)
    y2 = 50 + 50 * math.sin(angle_rad)

    grad = dwg.linearGradient(id=id_name, x1="50%", y1="50%", x2=f"{x2}%", y2=f"{y2}%")

    if opacities is None:
        opacities = [1.0] * len(colors)
    elif len(opacities) != len(colors):
        logger.warning("Mismatch between colors and opacities in gradient {id_name}", id_name=id_name)
        # Extend opacities or truncate to match colors length
        if len(opacities) < len(colors):
            opacities.extend([1.0] * (len(colors) - len(opacities)))
        else:
            opacities = opacities[: len(colors)]

    for i, (color, opacity) in enumerate(zip(colors, opacities)):
        offset = f"{100 * i / max(1, len(colors) - 1)}%"
        grad.add_stop_color(offset, color, opacity)

    return dwg.defs.add(grad)


# ------------------------------------------------------------------------------
# Configuration Models (Pydantic)
# ------------------------------------------------------------------------------
class ColorPalette(BaseModel):
    """
    Defines the color schemes used throughout the banner.

    Includes primary, secondary, accent, and neutral colors, as well as specific
    palettes for different generative art patterns. Also supports dark mode
    and gradient stop generation.
    """

    primary: str = "#6a9fb5"
    secondary: list[str] = Field(default_factory=lambda: ["#4A90E2", "#357ABD"])
    accent: list[str] = Field(default_factory=lambda: ["#61DAFB", "#41B883"])
    neutral: list[str] = Field(default_factory=lambda: ["#F8F9FA", "#343A40"])
    extra_accents: list[str] = Field(default_factory=lambda: ["#ffd3ec", "#ffe8c4"])

    pattern_colors: dict[str, list[str]] = Field(
        default_factory=lambda: {
            "lorenz": ["#00e8f5", "#00a8b4"],  # Brighter cyan
            "neural": ["#9966ff", "#6633cc"],  # Rich purple
            "flow": ["#50e878", "#34a867"],  # More vibrant green
            "micro": ["#c85ae5", "#a23cc3"],  # Richer purple
            "aizawa": ["#ffaa00", "#ff8500"],  # Warmer orange
            "reaction": ["#d500f9", "#aa00ff"],
            "clifford": ["#1e88e5", "#0d47a1"],
            "flame": ["#f50057", "#c51162"],
            "pdj": ["#00bcd4", "#0097a7"],
            "ikeda": ["#e91e63", "#c2185b"],
        }
    )
    gradient_stops: list[str] = Field(default_factory=list)
    dark_mode_palette: dict[str, str] = Field(default_factory=dict)

    def model_post_init(self, __context) -> None:
        """Generate derived color schemes only for fields not explicitly set."""
        if not self.secondary:
            self.secondary = ["#bed6df", "#d3eef5"]
        if not self.accent:
            self.accent = ["#aed7e1", "#d1f3fa"]
        if not self.neutral:
            self.neutral = ["#f9fbfc", "#e9f0f2"]
        if not self.extra_accents:
            self.extra_accents = ["#ffd3ec", "#ffe8c4"]
        if not self.gradient_stops:
            self.gradient_stops = ["#6a9fb5", "#83b7ca", "#9bd0df", "#cfeff6", "#ffffff"]
        if not self.dark_mode_palette:
            self.dark_mode_palette = {
                "primary": "#3a4b52",
                "background": "#14181a",
                "surface": "#1e2427",
                "text": "#f2f2f2",
            }


class VisualEffects(BaseModel):
    """
    Configuration for advanced visual effects applied to the banner.

    Includes settings for blur, glassmorphism, noise, glow, shadows,
    and other stylistic enhancements.
    """

    blur_amount: float = 15.0
    glass_blur: float = 22.0
    glass_opacity: float = 0.18
    frosted_glass_intensity: float = 0.15
    noise_opacity: float = 0.035
    noise_scale: float = 45.0
    texture_density: float = 1.8
    glow_radius: float = 35.0
    glow_opacity: float = 0.45
    inner_glow_radius: float = 28.0
    inner_glow_opacity: float = 0.35
    light_source_angle: float = 45.0
    light_intensity: float = 0.65
    backdrop_blur: float = 18.0
    grain_intensity: float = 0.025
    chromatic_aberration: float = 1.8
    vignette_intensity: float = 0.28
    depth_layers: int = 3
    shadow_opacity: float = 0.18
    highlight_intensity: float = 0.25
    texture_complexity: float = 2.2


class Typography(BaseModel):
    """
    Typography settings for the banner's text elements.

    Defines font families, sizes, weights, letter spacing, line heights,
    and text effects like shadows and gradients. Also includes responsive
    font sizes for different screen widths.
    """

    title_font: str = "Montserrat-ExtraBold"
    subtitle_font: str = "Montserrat-Medium"
    fallback_fonts: str = (
        "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', "
        "Roboto, Ubuntu, 'Helvetica Neue', sans-serif"
    )
    title_size: int = 86
    subtitle_size: int = 28
    title_weight: str = "800"
    subtitle_weight: str = "500"
    title_letter_spacing: float = -0.025
    subtitle_letter_spacing: float = 0.02
    title_line_height: float = 1.1
    subtitle_line_height: float = 1.35
    text_shadow_color: str = "rgba(0,0,0,0.18)"
    text_shadow_offset: tuple[float, float] = (2.0, 2.0)
    text_shadow_blur: float = 3.0
    text_gradient_angle: float = 38.0
    text_outline_width: float = 0.8
    text_outline_color: str = "rgba(255,255,255,0.12)"
    enable_text_gradient: bool = True
    enable_text_glow: bool = True
    glow_color: str = "rgba(255,255,255,0.25)"
    glow_blur: float = 12.0
    mobile_title_size: int = 52
    mobile_subtitle_size: int = 20
    tablet_title_size: int = 64
    tablet_subtitle_size: int = 22


class BannerConfig(BaseModel):
    """
    Main configuration model for the entire SVG banner.

    Aggregates settings for dimensions, text content, color palettes,
    typography, visual effects, layout, and pattern generation parameters.
    """

    width: int = 1600
    height: int = 480

    title: str = "Hey, GitHub! 👋"
    subtitle: str = "Exploring technology, one commit at a time"

    colors: ColorPalette = Field(default_factory=ColorPalette)
    typography: Typography = Field(default_factory=Typography)
    effects: VisualEffects = Field(default_factory=VisualEffects)

    padding: float = 48.0
    corner_radius: float = 40.0
    text_x_position: float = 0.14
    title_y_position: float = 0.48
    subtitle_y_position: float = 0.62

    # Octocat placement - adjusted to mirror text margin
    octocat_x: float = 0.82  # Moved left from 0.86 for better symmetry
    octocat_y: float = 0.50  # Vertical center is good
    octocat_size: float = 320
    octocat_vertical_offset: float = 0.0

    # Pattern usage parameters - enhanced for more detail
    pattern_density: float = 2.0  # Increased from 1.5
    flow_complexity: float = 3.0  # Increased from 2.5
    layer_count: int = 4  # Increased from 3
    pattern_opacity: float = 0.45  # Slightly increased
    pattern_scale: float = 1.8  # Increased from 1.6

    # Fibonacci steps for chaotic attractors - increased for more detail
    phi: float = 1.618033988749895
    fibonacci_steps: list[int] = [8, 13, 21, 34]  # Added more steps

    make_responsive: bool = True  # Changed to True
    optimize_with_svgo: bool = True
    output_path: str = "./assets/img/banner.svg"
    dark_mode: bool = False
    seed: int | None = Field(
        default=None,
        description="Random seed for deterministic output",
    )

    def apply_dark_mode(self) -> None:
        """Override color palette and typography for dark mode."""
        if not self.dark_mode:
            return
        dm = self.colors.dark_mode_palette
        self.colors.primary = dm.get("primary", "#3a4b52")
        self.colors.secondary = ["#2a3b42", "#354850"]
        self.colors.accent = ["#2e4550", "#3a5560"]
        self.colors.neutral = [dm.get("background", "#14181a"), dm.get("surface", "#1e2427")]
        self.colors.extra_accents = ["#4a2040", "#3a2820"]
        self.colors.gradient_stops = ["#3a4b52", "#2a3b42", "#1e2427", "#14181a", "#0a0c0d"]
        self.typography.text_shadow_color = "rgba(255,255,255,0.08)"
        self.typography.text_outline_color = "rgba(255,255,255,0.15)"
        self.typography.glow_color = "rgba(255,255,255,0.15)"


# ------------------------------------------------------------------------------
# SVG Filter Utilities
# ------------------------------------------------------------------------------
def _create_basic_glow_filter(
    dwg: Drawing,
    filter_id: str,
    std_deviation: str | float,
    color_matrix_values: str | None = None,
) -> filters.Filter:
    """Helper to create a basic glow filter with GaussianBlur and optional ColorMatrix."""
    glow_filter = dwg.defs.add(dwg.filter(id=filter_id))
    glow_filter.feGaussianBlur(
        in_="SourceGraphic", stdDeviation=str(std_deviation), result="blur"
    )
    if color_matrix_values:
        glow_filter.feColorMatrix(
            type="matrix", values=color_matrix_values, result="matrix"
        )
        glow_filter.feMerge(
            layernames=["matrix", "SourceGraphic"]
        )  # Ensure matrix applies
    else:  # If no color matrix, just use the blur
        # This part might need adjustment based on how feGaussianBlur alone should appear
        # Often, a simple blur is not merged this way unless it's part of a larger effect.
        # For a simple glow, often the blurred SourceAlpha is colored and then merged.
        pass  # Simplification: Let caller handle merge if more complex.
    return glow_filter


def _create_complex_glow_filter(
    dwg: Drawing,
    filter_id: str,
    blur1_std_dev: float,
    blur2_std_dev: float,
    flood_color: str,
    flood_opacity: float,
    color_matrix_values: str,
    filter_units: str = "userSpaceOnUse",
    dimensions: tuple[str, str, str, str] = ("-50%", "-50%", "200%", "200%"),
) -> filters.Filter:
    """Creates a more complex glow filter with multiple stages."""
    glow_filter = dwg.defs.add(
        dwg.filter(
            id=filter_id,
            x=dimensions[0],
            y=dimensions[1],
            width=dimensions[2],
            height=dimensions[3],
            filterUnits=filter_units,
        )
    )
    # Main graphic blur
    glow_filter.feGaussianBlur(
        in_="SourceGraphic", stdDeviation=str(blur1_std_dev), result="blur1"
    )
    # Alpha blur for outer glow shape
    glow_filter.feGaussianBlur(
        in_="SourceAlpha", stdDeviation=str(blur2_std_dev), result="blur2"
    )
    glow_filter.feFlood(
        flood_color=flood_color, flood_opacity=str(flood_opacity), result="flood1"
    )
    glow_filter.feComposite(
        in2="blur2", operator="in", result="comp1"
    )  # Colored outer glow
    # Color matrix adjustment
    glow_filter.feColorMatrix(
        type="matrix", values=color_matrix_values, result="matrix1"
    )
    # Merge effects: colored outer glow, then color-adjusted main graphic, then original graphic
    glow_filter.feMerge(layernames=["comp1", "matrix1", "SourceGraphic"])
    return glow_filter


# ------------------------------------------------------------------------------
# Background and Core Effects
# ------------------------------------------------------------------------------
def define_background(dwg: Drawing, cfg: BannerConfig) -> None:
    """
    Creates the primary background for the banner.

    This includes a multi-stop linear gradient, rounded corners via a clip path,
    and overlays for noise and vignette effects.

    Args:
        dwg: The SVG drawing object.
        cfg: The banner configuration.
    """
    # Base gradient
    grad = dwg.linearGradient(id="bgGradient", x1="0%", y1="0%", x2="100%", y2="100%")
    for i, color in enumerate(cfg.colors.gradient_stops):
        offset = (i / (len(cfg.colors.gradient_stops) - 1)) * 100
        grad.add_stop_color(f"{offset}%", color, opacity=0.95)
    dwg.defs.add(grad)

    # Clip path for rounded corners
    clip_path_obj = dwg.defs.add(dwg.clipPath(id="cornerClip"))
    clip_path_obj.add(
        dwg.rect(
            insert=(0, 0),
            size=(cfg.width, cfg.height),
            rx=cfg.corner_radius,
            ry=cfg.corner_radius,
        )
    )

    # Main background rectangle
    bg_rect = shapes.Rect(
        insert=(0, 0), size=(cfg.width, cfg.height), fill="url(#bgGradient)"
    )
    bg_rect["clip-path"] = "url(#cornerClip)"
    dwg.add(bg_rect)

    # Noise filter definition
    noise_filter_def = dwg.defs.add(dwg.filter(id="noiseFilter"))
    noise_filter_def.feTurbulence(
        type="fractalNoise",
        baseFrequency="0.65",  # Example values
        numOctaves="3",
        result="turbulence",
    )
    noise_filter_def.feComposite(
        in_="SourceGraphic", in2="turbulence", operator="in", result="comp"
    )
    noise_filter_def.feColorMatrix(
        type="matrix", values=("1 0 0 0 0 " "0 1 0 0 0 " "0 0 1 0 0 " "0 0 0 0.07 0")
    )  # Low alpha from turbulence

    # Vignette filter definition
    vignette_filter_def = dwg.defs.add(dwg.filter(id="vignetteFilter"))
    vignette_filter_def.feRadialGradient(
        id="radial", cx="0.5", cy="0.5", r="0.7", fx="0.5", fy="0.5", result="grad"
    )
    vignette_filter_def.select_id("radial").add_stop_color(
        "0%", "white", opacity="0"
    )  # Transparent center
    vignette_filter_def.select_id("radial").add_stop_color(
        "100%", "black", opacity="1"
    )  # Opaque edge
    # Apply gradient as an alpha mask
    vignette_filter_def.feComposite(
        in_="SourceGraphic",
        in2="grad",
        operator="arithmetic",
        k1="0",
        k2="1",
        k3="0",
        k4="0",
        result="masked",
    )  # k2=1 takes alpha from grad

    # Noise overlay
    noise_rect = shapes.Rect(
        insert=(0, 0),
        size=(cfg.width, cfg.height),
        fill="white",  # Base for filter to operate on
        filter="url(#noiseFilter)",
        opacity=cfg.effects.noise_opacity,
    )
    noise_rect["clip-path"] = "url(#cornerClip)"
    dwg.add(noise_rect)

    # Vignette overlay
    vignette_rect = shapes.Rect(
        insert=(0, 0),
        size=(cfg.width, cfg.height),
        fill="black",  # Base color, filter will use its alpha
        filter="url(#vignetteFilter)",
        opacity=cfg.effects.vignette_intensity,
    )
    vignette_rect["clip-path"] = "url(#cornerClip)"
    dwg.add(vignette_rect)


def add_glassmorphism_effect(dwg: Drawing, cfg: BannerConfig) -> filters.Filter:
    """
    Defines and adds a glassmorphism SVG filter to the drawing's definitions.

    This filter combines blur, noise, and color adjustments to simulate a
    frosted glass effect.

    Args:
        dwg: The SVG drawing object.
        cfg: The banner configuration containing effect parameters.

    Returns:
        The created SVG filter object.
    """
    glass_filter = dwg.defs.add(dwg.filter(id="glassFilter"))
    glass_filter.feGaussianBlur(
        in_="SourceGraphic", stdDeviation=cfg.effects.glass_blur, result="blur"
    )
    glass_filter.feTurbulence(
        type="fractalNoise",
        baseFrequency="0.07",
        numOctaves=2,
        seed=_rng.randint(1, 100),
        result="noise",
    )
    glass_filter.feDisplacementMap(
        in_="blur",
        in2="noise",
        scale=cfg.effects.frosted_glass_intensity * 14,
        xChannelSelector="R",
        yChannelSelector="G",
        result="displace",
    )
    glass_filter.feColorMatrix(
        type="matrix",
        values="1 0 0 0 0.03 0 1 0 0 0.03 0 0 1 0 0.03 0 0 0 0.7 0",
        result="colorize",
    )
    return glass_filter


# ------------------------------------------------------------------------------
# Generative Art: Flow Field
# ------------------------------------------------------------------------------
def generate_flow_field(
    cfg: BannerConfig, num_points: int = 600
) -> list[tuple[float, float, float, float]]:
    """
    Generates points and vectors for a flow field pattern using Perlin noise.

    Args:
        cfg: The banner configuration, used for dimensions and complexity.
        num_points: The number of initial points for the flow field.

    Returns:
        A list of tuples, each containing (x, y, dx, dy) for a flow field
        particle.
    """
    points = []
    scale = 0.006 * cfg.flow_complexity
    for _ in range(num_points):
        x_pos = _rng.uniform(0, cfg.width)
        y_pos = _rng.uniform(0, cfg.height)
        angle = (
            _noise_handler_instance.pnoise2(x_pos * scale, y_pos * scale, octaves=2)
            * math.pi
            * 2
        )
        strength = _rng.uniform(0.4, 0.9) * cfg.pattern_scale
        dx_val = math.cos(angle) * strength
        dy_val = math.sin(angle) * strength
        points.append((x_pos, y_pos, dx_val, dy_val))
    return points


def draw_flow_patterns(cfg: BannerConfig, dwg: Drawing, group: Group) -> None:
    """
    Draws multiple layers of flow field lines onto the SVG group.

    Each line is styled with a gradient and a glow effect.

    Args:
        cfg: The banner configuration for styling and density.
        dwg: The SVG drawing object (for adding definitions).
        group: The SVG group to which the flow patterns will be added.
    """
    # Glow filter for flow lines
    _create_basic_glow_filter(
        dwg,
        filter_id="flowGlowFilter",
        std_deviation="2",
        color_matrix_values="1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 15 -5",
    )

    # Gradient for flow line strokes
    grad_id = "flowFieldGradient"
    flow_grad = dwg.defs.add(dwg.linearGradient(id=grad_id))
    flow_grad.add_stop_color(
        offset="0%", color=cfg.colors.pattern_colors["flow"][0], opacity=1
    )
    flow_grad.add_stop_color(
        offset="100%", color=cfg.colors.pattern_colors["flow"][1], opacity=1
    )

    for layer_idx in range(cfg.layer_count):
        layer_opacity = cfg.pattern_opacity * (1 - layer_idx * 0.1)
        current_points = generate_flow_field(
            cfg, num_points=int(600 * cfg.pattern_density)
        )

        for x_start, y_start, dx_val, dy_val in current_points:
            path_str = f"M{x_start},{y_start} "
            # Create a short path segment
            curr_x, curr_y = x_start, y_start
            for _ in range(4):  # Number of segments in each flow line
                curr_x += dx_val * 1.2
                curr_y += dy_val * 1.2
                path_str += f"L{curr_x},{curr_y} "

            p_element = path.Path(
                d=path_str,
                stroke=f"url(#{grad_id})",
                fill="none",
                stroke_width=1.2,
                opacity=layer_opacity,
            )
            p_element["filter"] = "url(#flowGlowFilter)"
            group.add(p_element)


# ------------------------------------------------------------------------------
# Generative Art: Lorenz Attractor
# ------------------------------------------------------------------------------
def generate_lorenz(
    points: int = 6000, sigma: float = 10.0, beta: float = 8.0 / 3.0, rho: float = 28.0
) -> list[tuple[float, float, float]]:
    """
    Generates a sequence of 3D points representing the Lorenz attractor.

    Args:
        points: The number of points to generate.
        sigma: The sigma parameter of the Lorenz system.
        beta: The beta parameter of the Lorenz system.
        rho: The rho parameter of the Lorenz system.

    Returns:
        A list of (x, y, z) tuples.
    """
    dt = 0.01
    x, y, z = 0.1, 0.0, 0.0
    output_points = []
    for _ in range(points):
        dx = sigma * (y - x) * dt
        dy = (x * (rho - z) - y) * dt
        dz = (x * y - beta * z) * dt
        x += dx
        y += dy
        z += dz
        output_points.append((x, y, z))
    return output_points


def draw_lorenz(
    cfg: BannerConfig,
    dwg: Drawing,
    group: Group,
    x0: float,
    y0: float,
    width: float,
    height: float,
) -> None:
    """
    Draws the Lorenz attractor pattern onto the SVG group.

    The attractor is rendered with a multi-stop gradient and a complex glow
    effect, with multiple layers to simulate depth.

    Args:
        cfg: The banner configuration.
        dwg: The SVG drawing object.
        group: The SVG group to add the Lorenz attractor to.
        x0: The x-offset for the drawing area.
        y0: The y-offset for the drawing area.
        width: The width of the drawing area.
        height: The height of the drawing area.
    """
    lorenz_points = generate_lorenz(cfg.fibonacci_steps[-1] * 400)

    grad_id = "lorenzGrad"
    lorenz_grad_def = dwg.defs.add(dwg.linearGradient(id=grad_id))
    lorenz_grad_def.add_stop_color(
        "0%", cfg.colors.pattern_colors["lorenz"][0], opacity=0.95
    )
    lorenz_grad_def.add_stop_color(
        "33%", adjust_hue(cfg.colors.pattern_colors["lorenz"][0], 15), opacity=0.9
    )
    lorenz_grad_def.add_stop_color(
        "66%", adjust_hue(cfg.colors.pattern_colors["lorenz"][1], -15), opacity=0.85
    )
    lorenz_grad_def.add_stop_color(
        "100%", cfg.colors.pattern_colors["lorenz"][1], opacity=0.8
    )

    _create_complex_glow_filter(
        dwg,
        filter_id="lorenzGlow",
        blur1_std_dev=2,
        blur2_std_dev=3,
        flood_color="#ffffff",
        flood_opacity=0.25,
        color_matrix_values="1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 8 -3",
    )

    min_x = min(p[0] for p in lorenz_points)
    max_x = max(p[0] for p in lorenz_points)
    min_y = min(p[1] for p in lorenz_points)
    max_y = max(p[1] for p in lorenz_points)
    min_z = min(p[2] for p in lorenz_points)
    max_z = max(p[2] for p in lorenz_points)

    delta_x = max_x - min_x if max_x - min_x else 1e-6
    delta_y = max_y - min_y if max_y - min_y else 1e-6
    delta_z = max_z - min_z if max_z - min_z else 1e-6

    scale_factor = min(width / delta_x, height / delta_y) * 12.0
    shift_x = x0 + width / 2
    shift_y = y0 + height / 2

    for layer_idx in range(3):  # Number of layers for depth
        opacity = 0.8 - layer_idx * 0.15
        z_offset_val = layer_idx * 50  # Visual offset for layers

        path_obj = path.Path(
            fill="none",
            stroke=f"url(#{grad_id})",
            stroke_width=1.8 - layer_idx * 0.3,
            stroke_linecap="round",
            stroke_linejoin="round",
            opacity=opacity,
        )
        path_obj["filter"] = "url(#lorenzGlow)"

        is_first_point = True
        for i, (lx, ly, lz) in enumerate(lorenz_points):
            z_norm = (lz - min_z) / delta_z
            current_scale = 1 + z_norm * 0.2

            px = shift_x + (lx - (min_x + delta_x / 2)) * scale_factor * current_scale
            py = (
                shift_y
                + (ly - (min_y + delta_y / 2)) * scale_factor * current_scale
                + z_offset_val
            )

            if is_first_point:
                path_obj.push(f"M{px},{py}")
                is_first_point = False
            elif i % 2 == 0:  # Draw line to every other point for detail
                path_obj.push(f"L{px},{py}")

        if layer_idx == 0:  # Animate only the front layer
            animate_opacity = dwg.animate(
                attributeName="stroke-opacity",
                values=f"{opacity};{opacity * 1.2};{opacity}",
                dur="4s",
                repeatCount="indefinite",
                calcMode="spline",
                keyTimes="0;0.5;1",
                keySplines="0.4 0 0.2 1;0.4 0 0.2 1",
            )
            path_obj.add(animate_opacity)
        group.add(path_obj)


# ------------------------------------------------------------------------------
# Generative Art: Aizawa Attractor
# ------------------------------------------------------------------------------
def generate_aizawa(
    num_points: int = 10000,
    dt: float = 0.01,
    a: float = 0.95,
    b: float = 0.7,
    c: float = 0.6,
    d: float = 3.5,
    e: float = 0.25,
    f: float = 0.1,
) -> list[Point3DModel]:
    """
    Generates a sequence of 3D points for the Aizawa attractor.

    Args:
        num_points: Number of points to generate.
        dt: Time step for integration.
        a, b, c, d, e, f: Parameters of the Aizawa system.

    Returns:
        A list of Point3DModel objects.
    """
    points_list = []
    x, y, z = 1.0, 0.0, 0.0  # Initial conditions

    for _ in range(num_points):
        # Aizawa system equations
        dx = (z - b) * x - d * y
        dy = d * x + (z - b) * y
        dz = c + a * z - z**3 / 3 - (x**2 + y**2) * (1 + e * z) + f * z * x**3

        x += dx * dt
        y += dy * dt
        z += dz * dt
        points_list.append(Point3DModel(x=x, y=y, z=z))
    return points_list


def draw_aizawa(dwg: Drawing, cfg: BannerConfig, group: Group) -> None:
    """
    Draws the Aizawa attractor pattern onto the SVG group.

    Features a multi-stop gradient, a complex glow effect, and layered
    rendering for a sense of depth.

    Args:
        dwg: The SVG drawing object.
        cfg: The banner configuration.
        group: The SVG group to add the Aizawa attractor to.
    """
    grad_id = "aizawaGradient"
    gradient_def = dwg.defs.add(
        gradients.LinearGradient(id=grad_id, x1="0%", y1="0%", x2="100%", y2="100%")
    )
    gradient_def.add_stop_color(0, cfg.colors.pattern_colors["aizawa"][0], opacity=0.95)
    gradient_def.add_stop_color(
        0.3, adjust_hue(cfg.colors.pattern_colors["aizawa"][0], 15), opacity=0.9
    )
    gradient_def.add_stop_color(
        0.6, adjust_hue(cfg.colors.pattern_colors["aizawa"][1], -15), opacity=0.85
    )
    gradient_def.add_stop_color(1, cfg.colors.pattern_colors["aizawa"][1], opacity=0.8)

    _create_complex_glow_filter(
        dwg,
        filter_id="aizawaGlow",
        blur1_std_dev=2,
        blur2_std_dev=3,
        flood_color="#ffffff",
        flood_opacity=0.3,  # Note: original had 0.3 vs 0.25 for Lorenz
        color_matrix_values="1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 8 -3",
        filter_units="objectBoundingBox",
    )

    # Adjusted scale and position
    width_scale = cfg.width * 0.3
    height_scale = cfg.height * 0.45
    x_offset = cfg.width * 0.75
    y_offset = cfg.height * 0.48

    # Performance: Reduced points slightly from original refactor thought
    aizawa_points = generate_aizawa(num_points=12000)

    x_vals = [p.x for p in aizawa_points]
    y_vals = [p.y for p in aizawa_points]
    z_vals = [p.z for p in aizawa_points]

    x_min, x_max = min(x_vals), max(x_vals)
    y_min, y_max = min(y_vals), max(y_vals)
    z_min, z_max = min(z_vals), max(z_vals)

    delta_x = x_max - x_min if x_max - x_min else 1e-6
    delta_y = y_max - y_min if y_max - y_min else 1e-6
    delta_z = z_max - z_min if z_max - z_min else 1e-6

    for layer_idx in range(3):  # Number of layers for depth
        path_data_segments = []
        opacity = 0.7 - layer_idx * 0.15
        # z_offset_val = layer_idx * 0.1 # This was unused, so removed.

        for i, point in enumerate(aizawa_points):
            z_norm = (point.z - z_min) / delta_z
            scale_factor = 1 + z_norm * 0.2

            x_coord = (
                (point.x - x_min) / delta_x * width_scale * scale_factor + x_offset
                if delta_x
                else x_offset
            )
            y_coord = (
                (point.y - y_min) / delta_y * height_scale * scale_factor + y_offset
                if delta_y
                else y_offset
            )

            if i == 0 or i % 3 == 0:  # Start new subpath or use L for detail
                path_data_segments.append(f"M {x_coord},{y_coord}")
            else:
                path_data_segments.append(f"L {x_coord},{y_coord}")

        aizawa_path_obj = path.Path(d=" ".join(path_data_segments))
        aizawa_path_obj["stroke"] = f"url(#{grad_id})"
        aizawa_path_obj["fill"] = "none"
        aizawa_path_obj["stroke-width"] = str(0.8 - layer_idx * 0.2)
        aizawa_path_obj["stroke-opacity"] = str(opacity)
        aizawa_path_obj["filter"] = "url(#aizawaGlow)"

        if layer_idx == 0:  # Animate only the front layer
            animate_opacity = dwg.animate(
                attributeName="stroke-opacity",
                values=f"{opacity};{opacity * 1.2};{opacity}",
                dur="4s",
                repeatCount="indefinite",
                calcMode="spline",
                keyTimes="0;0.5;1",
                keySplines="0.4 0 0.2 1;0.4 0 0.2 1",
            )
            aizawa_path_obj.add(animate_opacity)
        group.add(aizawa_path_obj)


# ------------------------------------------------------------------------------
# Generative Art: Clifford Strange Attractor
# ------------------------------------------------------------------------------
def draw_clifford(
    dwg: Drawing,
    group: Group,
    width: int,
    height: int,
    a: float = 1.7,
    b: float = 1.7,
    c: float = 0.6,
    d: float = 1.2,
    iterations: int = 2_000_000,
    hue_shift: float = 0.0,
    dark_mode: bool = False,
    grid_size: int = 150,
    return_first_hit: bool = False,
) -> np.ndarray | None:
    """
    Draw a Clifford Strange Attractor as a density-mapped SVG raster.

    The Clifford attractor is defined by the iterative system:
        x_{n+1} = sin(a * y_n) + c * cos(a * x_n)
        y_{n+1} = sin(b * x_n) + d * cos(b * y_n)

    Points are accumulated into a density grid, log-normalised, and rendered
    as coloured ``<rect>`` elements in the SVG.

    Args:
        dwg: The SVG drawing object.
        group: The SVG group to add the attractor to.
        width: Pixel width of the output area.
        height: Pixel height of the output area.
        a, b, c, d: Clifford attractor parameters.
        iterations: Number of iterations to compute.
        hue_shift: Shift (0.0-1.0) applied to the colour palette.
        dark_mode: If ``True``, assumes a dark background and adjusts alpha.
        grid_size: Resolution of the density grid (grid_size x grid_size).
        return_first_hit: If ``True``, return an array recording the iteration
            index when each grid cell was first populated (``-1`` for cells
            never hit).  When ``False`` (default), the function returns
            ``None`` and behaves exactly as before.

    Returns:
        When *return_first_hit* is ``True``, a ``np.ndarray`` of shape
        ``(grid_size, grid_size)`` with dtype ``int64``.  Otherwise ``None``.
    """
    # 1. Iterate the attractor
    x, y = 0.1, 0.1
    density = np.zeros((grid_size, grid_size), dtype=np.float64)
    first_hit = (
        np.full((grid_size, grid_size), -1, dtype=np.int64)
        if return_first_hit
        else None
    )

    # Attractor coordinate range (empirical bounds for typical parameters)
    coord_min, coord_max = -3.0, 3.0
    coord_range = coord_max - coord_min

    for i in range(iterations):
        x_new = math.sin(a * y) + c * math.cos(a * x)
        y_new = math.sin(b * x) + d * math.cos(b * y)
        x, y = x_new, y_new

        # Map to grid indices
        gx = int((x - coord_min) / coord_range * (grid_size - 1))
        gy = int((y - coord_min) / coord_range * (grid_size - 1))

        if 0 <= gx < grid_size and 0 <= gy < grid_size:
            if first_hit is not None and density[gy, gx] == 0:
                first_hit[gy, gx] = i
            density[gy, gx] += 1.0

    # 2. Log-scale normalisation
    max_val = density.max()
    if max_val > 0:
        norm = np.log1p(density) / np.log1p(max_val)
    else:
        logger.warning("Clifford attractor produced an empty density grid")
        return None

    # 3. Pixel sizing (rounded to reduce SVG file size)
    pixel_w = round(width / grid_size, 2)
    pixel_h = round(height / grid_size, 2)

    # 4. Render density cells as <rect> elements
    for row in range(grid_size):
        for col in range(grid_size):
            val = float(norm[row, col])
            if val < 0.02:
                continue  # skip near-zero cells to reduce SVG size

            # Colour mapping with hue_shift
            if val < 0.3:
                # Low density  ->  dark blue / purple
                t = val / 0.3
                base_hue = (0.7 + hue_shift) % 1.0  # blue-purple region
                sat = 0.8 + 0.2 * t
                lit = 0.15 + 0.15 * t
            elif val < 0.6:
                # Medium density  ->  orange / warm
                t = (val - 0.3) / 0.3
                base_hue = (0.08 + hue_shift) % 1.0  # orange region
                sat = 0.9
                lit = 0.3 + 0.25 * t
            else:
                # High density  ->  white / bright
                t = (val - 0.6) / 0.4
                base_hue = (0.08 + hue_shift) % 1.0
                sat = 0.9 * (1 - t * 0.8)
                lit = 0.55 + 0.40 * t

            r, g, b_ch = colorsys.hls_to_rgb(base_hue, lit, sat)
            hex_color = f"#{int(r * 255):02x}{int(g * 255):02x}{int(b_ch * 255):02x}"

            alpha = val * (0.95 if dark_mode else 0.85)

            rect = dwg.rect(
                insert=(round(col * pixel_w, 2), round(row * pixel_h, 2)),
                size=(round(pixel_w + 0.5, 2), round(pixel_h + 0.5, 2)),
                fill=hex_color,
                opacity=alpha,
            )
            group.add(rect)

    return first_hit


# ------------------------------------------------------------------------------
# Generative Art: Neural Network
# ------------------------------------------------------------------------------
def generate_neural_network(
    num_nodes: int = 80,
    _num_connections: int = 180,  # _ to indicate not directly used for limit
) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, float]]]:
    """
    Generates node positions and connections for a neural network visualization.

    Nodes are arranged in layers with a slight curve. Connections are primarily
    forward, with some recurrent and skip connections for visual complexity.

    Args:
        num_nodes: Approximate total number of nodes.
        _num_connections: Target number of connections (parameter currently
                          illustrative).

    Returns:
        A tuple containing:
            - nodes: List of (x_norm, y_norm, activation) tuples.
            - connections: List of (source_idx, target_idx, weight) tuples.
    """
    nodes_list = []
    connections_list = []
    layers = 7
    nodes_per_layer = num_nodes // layers
    recurrent_node_indices = []

    # Generate nodes
    for layer_idx in range(layers):
        layer_x_norm = 0.1 + (layer_idx * 0.8 / (layers - 1))
        curve_offset = math.sin(layer_idx * math.pi / (layers - 1)) * 0.05

        for i in range(nodes_per_layer):
            y_base = 0.1 + (i / (nodes_per_layer - 1)) * 0.8
            y_curve = math.sin(i * math.pi / nodes_per_layer) * 0.15
            y_norm = y_base + y_curve + curve_offset
            activation = (
                0.6
                + 0.3
                * (
                    math.sin(layer_idx * math.pi / layers)
                    + math.cos(i * math.pi / nodes_per_layer)
                )
                / 2
            )
            nodes_list.append((layer_x_norm, y_norm, activation))
            if _rng.random() < 0.2:
                recurrent_node_indices.append(len(nodes_list) - 1)

    # Generate connections
    for i in range(len(nodes_list)):
        current_layer = i // nodes_per_layer
        # Forward connections
        if current_layer < layers - 1:
            next_layer_start_idx = (current_layer + 1) * nodes_per_layer
            next_layer_end_idx = min(
                next_layer_start_idx + nodes_per_layer, len(nodes_list)
            )
            num_fwd = _rng.randint(2, 6)  # Connections per node
            for _ in range(num_fwd):
                if next_layer_start_idx < next_layer_end_idx:
                    target_idx = _rng.randint(
                        next_layer_start_idx, next_layer_end_idx - 1
                    )
                    weight = (
                        0.4 + 0.4 * (nodes_list[i][2] + nodes_list[target_idx][2]) / 2
                    )
                    connections_list.append((i, target_idx, weight))

    # Recurrent connections
    for node_idx in recurrent_node_indices:
        current_layer = node_idx // nodes_per_layer
        if current_layer > 0:  # Connect to previous layer
            prev_layer_start = (current_layer - 1) * nodes_per_layer
            prev_layer_end = current_layer * nodes_per_layer
            num_rec = _rng.randint(1, 3)
            for _ in range(num_rec):
                if prev_layer_start < prev_layer_end:
                    target_idx = _rng.randint(prev_layer_start, prev_layer_end - 1)
                    weight = 0.3 + 0.3 * nodes_list[node_idx][2]
                    connections_list.append((node_idx, target_idx, weight))
            # Skip connections (multiple layers back)
        if current_layer > 2:
            far_prev_start = 0
            far_prev_end = (current_layer - 2) * nodes_per_layer
            if far_prev_end > far_prev_start and _rng.random() < 0.3:
                target_idx = _rng.randint(far_prev_start, far_prev_end - 1)
                weight = 0.2 + 0.2 * nodes_list[node_idx][2]
                connections_list.append((node_idx, target_idx, weight))

    return nodes_list, connections_list


def draw_neural_network(
    cfg: BannerConfig,
    dwg: Drawing,
    group: Group,
    x0: float,
    y0: float,
    width: float,
    height: float,
) -> None:
    """
    Draws a neural network pattern onto the SVG group.

    Nodes and connections are styled with gradients and glow effects.
    Connections have a slight curve for a more organic appearance.

    Args:
        cfg: The banner configuration.
        dwg: The SVG drawing object.
        group: The SVG group to add the neural network to.
        x0, y0: Offset for the drawing area.
        width, height: Dimensions of the drawing area.
    """
    nodes, connections = generate_neural_network()

    grad_id = "neuralGrad"
    neural_grad_def = dwg.defs.add(gradients.LinearGradient(id=grad_id))
    neural_grad_def.add_stop_color(
        "0%", cfg.colors.pattern_colors["neural"][0], opacity=0.9
    )
    neural_grad_def.add_stop_color(
        "33%", adjust_hue(cfg.colors.pattern_colors["neural"][0], 15), opacity=0.85
    )
    neural_grad_def.add_stop_color(
        "66%", adjust_hue(cfg.colors.pattern_colors["neural"][1], -15), opacity=0.8
    )
    neural_grad_def.add_stop_color(
        "100%", cfg.colors.pattern_colors["neural"][1], opacity=0.75
    )

    # Main glow for nodes/connections
    glow_filter_id = "neuralMainGlow"
    main_glow = dwg.defs.add(
        filters.Filter(id=glow_filter_id, filterUnits="objectBoundingBox")
    )  # Removed size=(3,3) as it's for userSpaceOnUse usually
    main_glow.feGaussianBlur(in_="SourceGraphic", stdDeviation=2.5)
    main_glow.feColorMatrix(
        type="matrix", values="1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 6 -1"
    )

    # Subtle outer glow for depth
    outer_glow_filter_id = "neuralOuterGlow"
    outer_glow = dwg.defs.add(
        filters.Filter(id=outer_glow_filter_id, filterUnits="objectBoundingBox")
    )
    outer_glow.feGaussianBlur(in_="SourceGraphic", stdDeviation=4)
    outer_glow.feColorMatrix(
        type="matrix", values="1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 4 -0.5"
    )

    # Draw connections
    for src_idx, tgt_idx, weight in connections:
        src_x = x0 + nodes[src_idx][0] * width
        src_y = y0 + nodes[src_idx][1] * height
        tgt_x = x0 + nodes[tgt_idx][0] * width
        tgt_y = y0 + nodes[tgt_idx][1] * height

        # Curved connection path
        ctrl_x = (src_x + tgt_x) / 2 + _rng.uniform(-20, 20)
        ctrl_y = (src_y + tgt_y) / 2 + _rng.uniform(-20, 20)
        path_d = f"M {src_x},{src_y} Q {ctrl_x},{ctrl_y} {tgt_x},{tgt_y}"

        # Outer glow for connection
        glow_conn = path.Path(
            d=path_d,
            stroke=f"url(#{grad_id})",
            stroke_width=3 * weight,
            stroke_opacity=0.2 * weight,
            filter=f"url(#{outer_glow_filter_id})",
            fill="none",
        )
        group.add(glow_conn)

        # Main connection
        main_conn = path.Path(
            d=path_d,
            stroke=f"url(#{grad_id})",
            stroke_width=1.8 * weight,
            stroke_opacity=0.7 * weight,
            fill="none",
        )
        group.add(main_conn)

    # Draw nodes
    for x_norm, y_norm, activation in nodes:
        node_x = x0 + x_norm * width
        node_y = y0 + y_norm * height

        # Outer glow for node
        glow_circle_outer = dwg.circle(
            center=(node_x, node_y),
            r=7,
            fill=cfg.colors.pattern_colors["neural"][0],
            fill_opacity=0.15 * activation,
            filter=f"url(#{outer_glow_filter_id})",
        )
        group.add(glow_circle_outer)

        # Inner glow for node
        glow_circle_inner = dwg.circle(
            center=(node_x, node_y),
            r=5,
            fill=cfg.colors.pattern_colors["neural"][0],
            fill_opacity=0.3 * activation,
            filter=f"url(#{glow_filter_id})",
        )  # Assuming glow_filter_id is neuralMainGlow
        group.add(glow_circle_inner)

        # Main node
        main_node = dwg.circle(
            center=(node_x, node_y),
            r=3,
            fill=cfg.colors.pattern_colors["neural"][0],
            fill_opacity=0.9 * activation,
        )
        group.add(main_node)


# ------------------------------------------------------------------------------
# Decorative Elements: Micro Details
# ------------------------------------------------------------------------------
def add_micro_details(dwg: Drawing, cfg: BannerConfig, group: Group) -> None:
    """
    Adds small, subtle geometric shapes (circles, crosses) to the background
    for added texture and visual interest.

    Args:
        dwg: The SVG drawing object.
        cfg: The banner configuration.
        group: The SVG group to add the micro details to.
    """
    count = 8  # Reduced count for subtlety
    for _ in range(count):
        x_pos = _rng.uniform(0, cfg.width)
        y_pos = _rng.uniform(0, cfg.height)
        size = _rng.uniform(6, 14)
        opacity = _rng.uniform(0.02, 0.06)
        shape_type = _rng.random()

        if shape_type < 0.5:  # Draw a circle
            circle = dwg.circle(
                center=(x_pos, y_pos),
                r=size,
                fill=cfg.colors.pattern_colors["micro"][0],
                opacity=opacity,
            )
            group.add(circle)
        else:  # Draw a simple cross
            for angle_rad in [0, math.pi / 2]:
                x1 = x_pos + size * math.cos(angle_rad)
                y1 = y_pos + size * math.sin(angle_rad)
                x2 = x_pos - size * math.cos(angle_rad)
                y2 = y_pos - size * math.sin(angle_rad)
                line = dwg.line(
                    start=(x1, y1),
                    end=(x2, y2),
                    stroke=cfg.colors.pattern_colors["micro"][1],
                    stroke_width=0.5,
                    opacity=opacity,
                )
                group.add(line)


# ------------------------------------------------------------------------------
# Foreground Elements: Octocat and Text
# ------------------------------------------------------------------------------
def add_octocat(cfg: BannerConfig, fg_group: Group, dwg: Drawing) -> None:
    """
    Embeds the GitHub Octocat image into the foreground group.

    The Octocat is styled with a drop shadow and a subtle glow.

    Args:
        cfg: The banner configuration for positioning and sizing.
        fg_group: The SVG group for foreground elements.
        dwg: The SVG drawing object for filter definitions.
    """
    octo_svg_path = "./assets/img/octocat.svg"
    if not os.path.isfile(octo_svg_path):
        logger.warning("Octocat SVG not found at {octo_svg_path}, skipping.", octo_svg_path=octo_svg_path)
        return

    with open(octo_svg_path, encoding="utf-8") as f:
        octo_svg_content = f.read()
    octo_b64 = base64.b64encode(octo_svg_content.encode("utf-8")).decode("utf-8")
    octo_data_href = f"data:image/svg+xml;base64,{octo_b64}"

    insert_x = cfg.width * cfg.octocat_x - (cfg.octocat_size / 2)
    insert_y = (
        (cfg.height * cfg.octocat_y)
        - (cfg.octocat_size / 2)
        + cfg.octocat_vertical_offset
    )

    # Octocat drop shadow filter
    shadow_filter_id = "octoShadow"
    shadow_filter = dwg.defs.add(dwg.filter(id=shadow_filter_id))
    shadow_filter.feGaussianBlur(in_="SourceAlpha", stdDeviation="5", result="blur")
    shadow_filter.feOffset(in_="blur", dx="6", dy="6", result="offsetBlur")
    shadow_filter.feFlood(
        flood_color="#000000", flood_opacity="0.25", result="shadowColor"
    )
    shadow_filter.feComposite(
        in_="shadowColor", in2="offsetBlur", operator="in", result="dropShadow"
    )
    shadow_filter.feMerge(layernames=["dropShadow", "SourceGraphic"])

    # Octocat glow filter
    glow_filter_id = "octoGlow"
    glow_filter = dwg.defs.add(dwg.filter(id=glow_filter_id))
    glow_filter.feGaussianBlur(in_="SourceGraphic", stdDeviation="6", result="blur")
    glow_filter.feFlood(flood_color="#ffffff", flood_opacity="0.35", result="glowColor")
    glow_filter.feComposite(in_="glowColor", in2="blur", operator="in", result="glow")
    glow_filter.feMerge(layernames=["glow", "SourceGraphic"])

    # Octocat image with shadow
    octo_image = dwg.image(
        href=octo_data_href,
        insert=(insert_x, insert_y),
        size=(f"{cfg.octocat_size}px", f"{cfg.octocat_size}px"),
        filter=f"url(#{shadow_filter_id})",
    )
    fg_group.add(octo_image)

    # Octocat glow overlay
    octo_glow_image = dwg.image(
        href=octo_data_href,
        insert=(insert_x, insert_y),
        size=(f"{cfg.octocat_size}px", f"{cfg.octocat_size}px"),
        filter=f"url(#{glow_filter_id})",
        opacity=0.5,
    )
    fg_group.add(octo_glow_image)


def add_title_and_subtitle(cfg: BannerConfig, fg_group: Group, dwg: Drawing) -> None:
    """
    Renders the main title and subtitle text onto the foreground group.

    Text is styled with custom fonts, gradients, and effects for visibility
    and aesthetic appeal.

    Args:
        cfg: The banner configuration for text content and typography.
        fg_group: The SVG group for foreground elements.
        dwg: The SVG drawing object for filter and gradient definitions.
    """
    # Title gradient
    title_grad_id = "titleGradient"
    title_grad = dwg.linearGradient(
        id=title_grad_id,
        x1="0%",
        y1="0%",
        x2=f"{math.cos(math.radians(cfg.typography.text_gradient_angle)) * 100}%",
        y2=f"{math.sin(math.radians(cfg.typography.text_gradient_angle)) * 100}%",
    )
    title_grad.add_stop_color("0%", "#ffffff", "1")
    title_grad.add_stop_color("45%", "#f8f8f8", "1")
    title_grad.add_stop_color("65%", "#f0f0f0", "1")
    title_grad.add_stop_color("85%", "#e8e8e8", "1")
    title_grad.add_stop_color("100%", "#e0e0e0", "1")
    dwg.defs.add(title_grad)

    # Text effects filter (glow)
    text_effects_id = "textEffects"
    text_effects = dwg.defs.add(
        dwg.filter(id=text_effects_id, x="-20%", y="-20%", width="140%", height="140%")
    )
    text_effects.feGaussianBlur(
        in_="SourceAlpha", stdDeviation="2", result="blur1"
    )  # Outer
    text_effects.feFlood(flood_color="#ffffff", flood_opacity="0.3", result="color1")
    text_effects.feComposite(in2="blur1", operator="in", result="glow_outer")
    text_effects.feGaussianBlur(
        in_="SourceAlpha", stdDeviation="1", result="blur2"
    )  # Inner
    text_effects.feFlood(flood_color="#ffffff", flood_opacity="0.2", result="color2")
    text_effects.feComposite(
        in2="blur2", operator="out", result="glow_inner"
    )  # 'out' for inner
    text_effects.feMerge(layernames=["glow_outer", "glow_inner", "SourceGraphic"])

    # Title text element
    title_text_el = dwg.text(
        cfg.title,  # Includes emoji
        insert=(cfg.width * cfg.text_x_position, cfg.height * cfg.title_y_position),
        font_family=f"{cfg.typography.title_font}, {cfg.typography.fallback_fonts}",
        font_size=cfg.typography.title_size,
        font_weight=cfg.typography.title_weight,
        letter_spacing=cfg.typography.title_letter_spacing,
        style="paint-order: stroke fill",  # Ensures stroke is behind fill
    )
    title_text_el["fill"] = f"url(#{title_grad_id})"
    title_text_el["filter"] = f"url(#{text_effects_id})"
    title_text_el["stroke"] = "#000000"  # Subtle dark outline for definition
    title_text_el["stroke-width"] = "0.5"
    title_text_el["stroke-opacity"] = "0.2"
    fg_group.add(title_text_el)

    # Subtitle text element
    subtitle_el = dwg.text(
        cfg.subtitle,
        insert=(cfg.width * cfg.text_x_position, cfg.height * cfg.subtitle_y_position),
        font_family=f"{cfg.typography.subtitle_font}, {cfg.typography.fallback_fonts}",
        font_size=cfg.typography.subtitle_size,
        font_weight=cfg.typography.subtitle_weight,
        letter_spacing=cfg.typography.subtitle_letter_spacing,
        style="paint-order: stroke fill",
    )
    subtitle_el["fill"] = "#ffffff"  # White for good contrast
    subtitle_el["filter"] = f"url(#{text_effects_id})"
    subtitle_el["stroke"] = "#000000"  # Subtle dark outline
    subtitle_el["stroke-width"] = "0.3"
    subtitle_el["stroke-opacity"] = "0.15"
    fg_group.add(subtitle_el)


# ------------------------------------------------------------------------------
# Main Banner Generation Orchestration
# ------------------------------------------------------------------------------
def generate_banner(
    cfg: BannerConfig, *, seed: int | None = None
) -> None:
    """
    Orchestrates the generation of all SVG banner elements.

    This function initializes the SVG drawing, defines background and global effects,
    adds generative art patterns, and then renders foreground elements like the
    Octocat and text. Finally, it saves the SVG and optionally optimizes it.

    Args:
        cfg: The main banner configuration object.
        seed: Optional random seed for deterministic output.
              Falls back to ``cfg.seed`` when *seed* is ``None``.
    """
    global _rng
    _rng = random.Random(seed if seed is not None else cfg.seed)

    cfg.apply_dark_mode()
    dwg = svgwrite.Drawing(
        filename=cfg.output_path,
        size=(f"{cfg.width}px", f"{cfg.height}px"),
        profile="full",
    )  # Use 'full' profile for filters etc.

    # Define reusable filters and gradients in <defs>
    define_background(
        dwg, cfg
    )  # Includes clip path, bg gradient, noise/vignette filters
    add_glassmorphism_effect(dwg, cfg)  # Defines glass filter

    # --- Background Patterns Group ---
    # This group holds all generative art patterns drawn behind main content.
    pattern_group = dwg.g(
        id="patternGroup", opacity=0.85
    )  # Overall opacity for patterns
    dwg.add(pattern_group)

    # Draw Flow Fields
    draw_flow_patterns(cfg, dwg, pattern_group)

    # Draw Neural Network
    # Position and size are tuned for visual balance.
    neural_group = dwg.g(id="neuralGroup", opacity=0.9)  # Slightly more prominent
    pattern_group.add(neural_group)  # Add to main pattern group
    draw_neural_network(
        cfg,
        dwg,
        neural_group,
        x0=cfg.width * 0.25,
        y0=cfg.height * -0.15,  # Positioned towards top-right
        width=cfg.width * 0.85,
        height=cfg.height * 0.95,
    )

    # Draw Lorenz Attractor
    # Positioned to the left, smaller and more subtle.
    lorenz_group = dwg.g(id="lorenzGroup", opacity=0.65)  # More subtle
    pattern_group.add(lorenz_group)
    draw_lorenz(
        cfg,
        dwg,
        lorenz_group,
        x0=cfg.width * 0.05,
        y0=cfg.height * 0.15,
        width=cfg.width * 0.22,
        height=cfg.height * 0.28,
    )

    # Draw Aizawa Attractor
    # Positioned to the right, complementing other patterns.
    aizawa_group = dwg.g(id="aizawaGroup", opacity=0.75)
    pattern_group.add(aizawa_group)
    # draw_aizawa uses internally defined offsets based on cfg.width/height
    draw_aizawa(dwg, cfg, aizawa_group)

    # Add Micro Details
    # Subtle texture elements scattered in the background.
    micro_group = dwg.g(id="microDetailsGroup", opacity=0.85)
    pattern_group.add(micro_group)
    add_micro_details(dwg, cfg, micro_group)

    # --- Foreground Group ---
    # This group holds elements like text and Octocat, drawn on top of patterns.
    fg_group = dwg.g(id="foregroundGroup", opacity=1.0)  # Full opacity for foreground
    dwg.add(fg_group)

    add_title_and_subtitle(cfg, fg_group, dwg)
    add_octocat(cfg, fg_group, dwg)

    # Save the SVG file
    try:
        dwg.save(pretty=False)  # pretty=False for smaller file size
        logger.info("Banner successfully saved to {output_path}", output_path=cfg.output_path)
    except Exception as e:
        logger.error("Error saving SVG file: {e}", e=e)
        return  # Exit if saving failed

    # Optimize with SVGO if enabled
    if cfg.optimize_with_svgo:
        optimize_with_svgo(cfg.output_path)
