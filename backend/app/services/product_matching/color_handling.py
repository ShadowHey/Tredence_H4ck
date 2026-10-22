"""Illumination-tolerant coarse color similarity for product packshots."""

from __future__ import annotations

from PIL import Image

from .crop_preprocessing import normalize_matching_image


def color_signature(image: Image.Image, bins: int = 36) -> list[float]:
    """Return a normalized hue histogram weighted by saturation and value.

    Gray/white backgrounds contribute little, reducing sensitivity to studio padding.
    This is a supporting cue, not an identity classifier.
    """
    hsv = normalize_matching_image(image).convert("HSV")
    histogram = [0.0] * bins
    for hue, saturation, value in hsv.getdata():
        weight = (saturation / 255.0) * (0.25 + 0.75 * value / 255.0)
        histogram[min(bins - 1, hue * bins // 256)] += weight
    total = sum(histogram)
    return [item / total for item in histogram] if total else histogram


def color_similarity(left: Image.Image, right: Image.Image) -> float:
    """Compare hue distributions using histogram intersection in [0, 1]."""
    a, b = color_signature(left), color_signature(right)
    if not any(a) and not any(b):
        return 0.5  # no useful color evidence: neutral, never an artificial penalty
    return sum(min(x, y) for x, y in zip(a, b))
