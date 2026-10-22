"""Conservative post-processing and geometry-quality checks for detector boxes."""

from collections import defaultdict
from typing import Iterable, List, Sequence

from .geometry import calculate_box_area
from .schemas import DetectionItem


def _intersection_over_smaller(box_a: Sequence[int], box_b: Sequence[int]) -> float:
    """Return intersection divided by the smaller box area (useful for nested duplicates)."""
    intersection = max(0, min(box_a[2], box_b[2]) - max(box_a[0], box_b[0])) * max(
        0, min(box_a[3], box_b[3]) - max(box_a[1], box_b[1])
    )
    smaller_area = min(calculate_box_area(box_a), calculate_box_area(box_b))
    return intersection / smaller_area if smaller_area > 0 else 0.0


def suppress_nested_duplicates(
    detections: Iterable[DetectionItem], containment_threshold: float = 0.92
) -> List[DetectionItem]:
    """Drop only near-contained same-class duplicates, preserving adjacent distinct facings.

    This intentionally does not join or expand boxes. Standard YOLO NMS has already run;
    this second pass only catches a narrow class of nested duplicate predictions that can
    survive IoU NMS because one prediction is much smaller than the other.
    """
    if not 0.0 < containment_threshold <= 1.0:
        raise ValueError("containment_threshold must be in (0, 1]")

    indexed = list(enumerate(detections))
    kept: List[tuple[int, DetectionItem]] = []
    for index, candidate in sorted(indexed, key=lambda pair: (-pair[1].confidence, pair[0])):
        is_nested_duplicate = any(
            accepted.class_id == candidate.class_id
            and _intersection_over_smaller(accepted.bbox_xyxy, candidate.bbox_xyxy) >= containment_threshold
            for _, accepted in kept
        )
        if not is_nested_duplicate:
            kept.append((index, candidate))
    return [item for _, item in sorted(kept, key=lambda pair: pair[0])]


def assess_row_box_quality(detections: Iterable[DetectionItem]) -> List[DetectionItem]:
    """Annotate width/height outliers within each row without altering detection geometry."""
    items = list(detections)
    by_row: dict[int, list[DetectionItem]] = defaultdict(list)
    for item in items:
        if item.row_number is not None:
            by_row[item.row_number].append(item)

    row_medians: dict[int, tuple[float, float]] = {}
    for row_number, row_items in by_row.items():
        widths = sorted(max(0, item.bbox_xyxy[2] - item.bbox_xyxy[0]) for item in row_items)
        heights = sorted(max(0, item.bbox_xyxy[3] - item.bbox_xyxy[1]) for item in row_items)
        mid = len(row_items) // 2
        median_width = (widths[mid] if len(widths) % 2 else (widths[mid - 1] + widths[mid]) / 2)
        median_height = (heights[mid] if len(heights) % 2 else (heights[mid - 1] + heights[mid]) / 2)
        row_medians[row_number] = (median_width, median_height)

    assessed: List[DetectionItem] = []
    for item in items:
        flags: List[str] = []
        medians = row_medians.get(item.row_number) if item.row_number is not None else None
        if medians:
            width = max(0, item.bbox_xyxy[2] - item.bbox_xyxy[0])
            height = max(0, item.bbox_xyxy[3] - item.bbox_xyxy[1])
            median_width, median_height = medians
            if median_width > 0 and width < median_width * 0.62:
                flags.append("narrow_vs_row_median")
            if median_height > 0 and height < median_height * 0.62:
                flags.append("short_vs_row_median")
        status = "review" if flags else ("usable" if medians else "unchecked")
        assessed.append(item.model_copy(update={
            "quality_status": status,
            "quality_flags": flags,
        }))
    return assessed
