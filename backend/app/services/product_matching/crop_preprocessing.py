"""Small, deterministic image normalization helpers for product matching."""

from __future__ import annotations

from PIL import Image, ImageChops, ImageOps


def normalize_matching_image(image: Image.Image, size: int = 256) -> Image.Image:
    """Apply EXIF orientation and resize without changing the image's aspect ratio."""
    normalized = ImageOps.exif_transpose(image).convert("RGB")
    normalized.thumbnail((size, size), Image.Resampling.LANCZOS)
    return normalized


def foreground_aspect_ratio(image: Image.Image) -> float:
    """Estimate packshot aspect ratio while ignoring near-white/transparent padding.

    On shelf crops the object generally fills its detector box, so the original image
    bounds are used. On catalogue packshots, a near-white margin is removed first.
    """
    image = normalize_matching_image(image)
    width, height = image.size
    # PIL performs the per-pixel image ops in native code. A sufficiently visible
    # difference from white catches colored edges while excluding studio-white padding.
    delta = ImageChops.difference(image, Image.new("RGB", image.size, "white"))
    foreground = delta.convert("L").point(lambda value: 255 if value > 24 else 0)
    bounds = foreground.getbbox()
    if not bounds:
        return width / max(height, 1)
    left, top, right, bottom = bounds
    return (right - left) / max(bottom - top, 1)
