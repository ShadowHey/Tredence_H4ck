"""Geometric utilities and spatial math for ShelfSense AI image parsing."""

from typing import List, Sequence, Tuple
import numpy as np


def calculate_box_area(box: Sequence[float]) -> float:
    """Calculate the area of a bounding box [x1, y1, x2, y2].

    Returns 0.0 if the box has invalid coordinates (x2 <= x1 or y2 <= y1).
    """
    x1, y1, x2, y2 = box[:4]
    w = max(0.0, float(x2 - x1))
    h = max(0.0, float(y2 - y1))
    return w * h


def clip_box(box: Sequence[float], width: int, height: int) -> List[int]:
    """Clips bounding box coordinates to lie strictly within [0, width] and [0, height]."""
    x1, y1, x2, y2 = box[:4]
    cx1 = int(round(max(0, min(float(x1), width))))
    cy1 = int(round(max(0, min(float(y1), height))))
    cx2 = int(round(max(0, min(float(x2), width))))
    cy2 = int(round(max(0, min(float(y2), height))))

    # Guarantee proper order
    if cx2 < cx1:
        cx1, cx2 = cx2, cx1
    if cy2 < cy1:
        cy1, cy2 = cy2, cy1

    return [cx1, cy1, cx2, cy2]


def normalize_box(box: Sequence[float], width: int, height: int) -> List[float]:
    """Normalize box coordinates [x1, y1, x2, y2] relative to image dimensions."""
    if width <= 0 or height <= 0:
        return [0.0, 0.0, 0.0, 0.0]

    x1, y1, x2, y2 = clip_box(box, width, height)
    return [
        round(x1 / float(width), 5),
        round(y1 / float(height), 5),
        round(x2 / float(width), 5),
        round(y2 / float(height), 5),
    ]


def denormalize_box(norm_box: Sequence[float], width: int, height: int) -> List[int]:
    """Convert normalized coordinates [x1, y1, x2, y2] to absolute pixel coordinates."""
    x1, y1, x2, y2 = norm_box[:4]
    return clip_box([x1 * width, y1 * height, x2 * width, y2 * height], width, height)


def calculate_iou(box1: Sequence[float], box2: Sequence[float]) -> float:
    """Calculate Intersection-over-Union (IoU) between two bounding boxes [x1, y1, x2, y2]."""
    x1_a, y1_a, x2_a, y2_a = box1[:4]
    x1_b, y1_b, x2_b, y2_b = box2[:4]

    inter_x1 = max(x1_a, x1_b)
    inter_y1 = max(y1_a, y1_b)
    inter_x2 = min(x2_a, x2_b)
    inter_y2 = min(y2_a, y2_b)

    inter_w = max(0.0, float(inter_x2 - inter_x1))
    inter_h = max(0.0, float(inter_y2 - inter_y1))
    inter_area = inter_w * inter_h

    if inter_area <= 0.0:
        return 0.0

    area_a = calculate_box_area(box1)
    area_b = calculate_box_area(box2)
    union_area = area_a + area_b - inter_area

    if union_area <= 0.0:
        return 0.0

    return float(inter_area / union_area)


def get_box_center(box: Sequence[float]) -> Tuple[int, int]:
    """Return the (cx, cy) pixel center of a bounding box."""
    x1, y1, x2, y2 = box[:4]
    cx = int(round((x1 + x2) / 2.0))
    cy = int(round((y1 + y2) / 2.0))
    return cx, cy


def polygon_to_bbox(polygon: Sequence[Sequence[int]]) -> List[int]:
    """Extract axis-aligned bounding box [x1, y1, x2, y2] from polygon coordinates."""
    if not polygon:
        return [0, 0, 0, 0]

    xs = [pt[0] for pt in polygon]
    ys = [pt[1] for pt in polygon]
    return [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))]


def apply_nms(
    boxes: List[Sequence[float]],
    scores: List[float],
    iou_threshold: float = 0.5,
) -> List[int]:
    """Perform Non-Maximum Suppression (NMS) over bounding boxes.

    Returns indices of kept boxes sorted by descending score.
    """
    if not boxes or not scores or len(boxes) != len(scores):
        return []

    indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    keep: List[int] = []

    while indices:
        current = indices.pop(0)
        keep.append(current)
        indices = [
            i for i in indices
            if calculate_iou(boxes[current], boxes[i]) < iou_threshold
        ]

    return keep
