"""First-stage hard color gate for shelf-scoped catalogue candidates."""

from __future__ import annotations

from typing import Any, Callable, Optional

from PIL import Image

from .color_handling import color_similarity

# Initial threshold chosen to reject the reported orange-packshot/chocolate-crop
# mismatch (~0.20 in the current fixture). Must be calibrated on labeled photos.
COLOR_FILTER_MIN_SIMILARITY = 0.30
COLOR_FALLBACK_MARGIN = 0.05


def filter_candidates_by_color(
    source_crop: Image.Image,
    candidates: list[dict[str, Any]],
    image_loader: Callable[[str], Optional[Image.Image]],
    minimum_similarity: float = COLOR_FILTER_MIN_SIMILARITY,
) -> dict[str, Any]:
    """Return only color-compatible candidates, with explicit fail-open diagnostics.

    If the gate rejects everything, retain only the best color candidates within a
    small margin of the highest score and mark fallback. If no usable packshots exist,
    retain the original candidate set but mark the color stage unavailable. Callers
    must not confirm a match in either fallback case.
    """
    scores: dict[int, Optional[float]] = {}
    scored: list[tuple[float, dict[str, Any]]] = []
    missing: list[dict[str, Any]] = []
    for candidate in candidates:
        candidate_id = int(candidate["id"])
        packshot = image_loader(str(candidate.get("image_path") or ""))
        if packshot is None:
            scores[candidate_id] = None
            missing.append(candidate)
            continue
        score = color_similarity(source_crop, packshot)
        scores[candidate_id] = score
        scored.append((score, candidate))

    compatible = [candidate for score, candidate in scored if score >= minimum_similarity]
    if compatible:
        return {
            "candidates": compatible,
            "scores": scores,
            "candidate_count_before": len(candidates),
            "candidate_count_after": len(compatible),
            "threshold": minimum_similarity,
            "fallback": False,
            "fallback_reason": None,
        }

    if scored:
        best_score = max(score for score, _ in scored)
        relaxed = [candidate for score, candidate in scored if best_score - score <= COLOR_FALLBACK_MARGIN]
        # Do not add candidates with absent images to this relaxed set: their color
        # compatibility is unknown, so returning them would defeat the color gate.
        return {
            "candidates": relaxed,
            "scores": scores,
            "candidate_count_before": len(candidates),
            "candidate_count_after": len(relaxed),
            "threshold": minimum_similarity,
            "fallback": True,
            "fallback_reason": "no_candidates_passed_color_threshold",
        }

    return {
        "candidates": candidates,
        "scores": scores,
        "candidate_count_before": len(candidates),
        "candidate_count_after": len(candidates),
        "threshold": minimum_similarity,
        "fallback": True,
        "fallback_reason": "catalogue_packshot_color_unavailable",
    }
