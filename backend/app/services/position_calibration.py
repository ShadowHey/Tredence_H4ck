"""Map image-space detection boxes into the job's frozen shelf coordinates.

Corner order for `shelf_corners_xy` is TL, TR, BR, BL. In the rectified frame,
the usable shelf area (excluding any plinth) maps to x=[0,width_cm] and y=[0,1].
"""

from __future__ import annotations

import math
from typing import Any, Optional


POSITION_TOLERANCE_FLOOR_CM = 1.0
POSITION_TOLERANCE_WIDTH_RATIO = 0.01


def _solve_linear_system(matrix: list[list[float]], vector: list[float]) -> list[float]:
    """Solve a small dense system using pivoted Gauss-Jordan elimination."""
    n = len(vector)
    augmented = [list(matrix[row]) + [float(vector[row])] for row in range(n)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(augmented[row][col]))
        if abs(augmented[pivot][col]) < 1e-10:
            raise ValueError("Calibration corners are degenerate.")
        augmented[col], augmented[pivot] = augmented[pivot], augmented[col]
        divisor = augmented[col][col]
        augmented[col] = [value / divisor for value in augmented[col]]
        for row in range(n):
            if row == col:
                continue
            factor = augmented[row][col]
            augmented[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(augmented[row], augmented[col])
            ]
    return [augmented[row][-1] for row in range(n)]


def _valid_corners(corners: Any, image_width: int, image_height: int) -> Optional[list[tuple[float, float]]]:
    if not isinstance(corners, list) or len(corners) != 4:
        return None
    try:
        points = [(float(point[0]), float(point[1])) for point in corners]
    except (TypeError, ValueError, IndexError):
        return None
    if not all(math.isfinite(x) and math.isfinite(y) for x, y in points):
        return None
    if any(x < 0 or y < 0 or x >= image_width or y >= image_height for x, y in points):
        return None
    # The required TL,TR,BR,BL ordering must form a non-self-intersecting convex quad.
    cross_products = []
    for index in range(4):
        ax, ay = points[index]
        bx, by = points[(index + 1) % 4]
        cx, cy = points[(index + 2) % 4]
        cross_products.append((bx - ax) * (cy - by) - (by - ay) * (cx - bx))
    if not all(value > 1e-6 for value in cross_products):
        return None
    area = abs(sum(
        points[index][0] * points[(index + 1) % 4][1]
        - points[(index + 1) % 4][0] * points[index][1]
        for index in range(4)
    )) / 2
    if area < image_width * image_height * 0.01:
        return None
    return points


def _make_homography(points: list[tuple[float, float]]) -> list[float]:
    targets = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    matrix: list[list[float]] = []
    values: list[float] = []
    for (x, y), (u, v) in zip(points, targets):
        matrix.append([x, y, 1.0, 0.0, 0.0, 0.0, -u * x, -u * y])
        values.append(u)
        matrix.append([0.0, 0.0, 0.0, x, y, 1.0, -v * x, -v * y])
        values.append(v)
    return _solve_linear_system(matrix, values) + [1.0]


def _project(homography: list[float], x: float, y: float) -> tuple[float, float]:
    denominator = homography[6] * x + homography[7] * y + homography[8]
    if abs(denominator) < 1e-10:
        raise ValueError("Point cannot be projected through calibration homography.")
    return (
        (homography[0] * x + homography[1] * y + homography[2]) / denominator,
        (homography[3] * x + homography[4] * y + homography[5]) / denominator,
    )


def _row_index_from_fraction(fraction: float, row_heights: list[float], row_count: int) -> Optional[int]:
    if row_count <= 0 or not math.isfinite(fraction) or fraction < 0 or fraction > 1:
        return None
    heights = row_heights[:row_count]
    if len(heights) != row_count or any(not math.isfinite(height) or height <= 0 for height in heights):
        heights = [1.0] * row_count
    total = sum(heights)
    boundary = 0.0
    for index, height in enumerate(heights):
        boundary += height / total
        if fraction <= boundary or index == row_count - 1:
            return index
    return None


def _valid_bbox(bbox: Any) -> Optional[tuple[float, float, float, float]]:
    if not isinstance(bbox, list) or len(bbox) != 4:
        return None
    try:
        x1, y1, x2, y2 = (float(value) for value in bbox)
    except (TypeError, ValueError):
        return None
    if not all(math.isfinite(value) for value in (x1, y1, x2, y2)) or x2 <= x1 or y2 <= y1:
        return None
    return x1, y1, x2, y2


def _choose_detected_row(
    bbox: tuple[float, float, float, float],
    rows: list[dict[str, Any]],
    row_count: int,
    detection_row_number: Any = None,
) -> tuple[Optional[dict[str, Any]], Optional[int]]:
    x1, y1, x2, y2 = bbox
    center_y = (y1 + y2) / 2
    try:
        requested_row = int(detection_row_number)
    except (TypeError, ValueError):
        requested_row = 0
    if 1 <= requested_row <= row_count:
        matching = [
            row for row in rows
            if row.get("row_number") == requested_row and _valid_bbox(row.get("bbox_xyxy"))
        ]
        if len(matching) == 1:
            return matching[0], requested_row - 1

    candidates: list[tuple[float, float, dict[str, Any]]] = []
    for row in rows:
        row_bbox = _valid_bbox(row.get("bbox_xyxy"))
        if not row_bbox:
            continue
        _, ry1, _, ry2 = row_bbox
        overlap = max(0.0, min(y2, ry2) - max(y1, ry1)) / max(y2 - y1, 1.0)
        distance = abs(center_y - (ry1 + ry2) / 2)
        candidates.append((overlap, -distance, row))
    if not candidates:
        return None, None
    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    if candidates[0][0] <= 0:
        return None, None
    selected = candidates[0][2]
    try:
        one_based = int(selected.get("row_number"))
    except (TypeError, ValueError):
        one_based = 0
    if 1 <= one_based <= row_count:
        return selected, one_based - 1

    ordered = sorted(
        (item[2] for item in candidates),
        key=lambda row: (_valid_bbox(row.get("bbox_xyxy")) or (0, 0, 0, 0))[1],
    )
    if len(ordered) == row_count:
        return selected, ordered.index(selected)
    return selected, None


def map_detections_to_planogram(
    detections: list[dict[str, Any]],
    shelf_rows: list[dict[str, Any]],
    shelf_snapshot: Optional[dict[str, Any]],
    image_width: int,
    image_height: int,
    shelf_corners_xy: Any = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Attach per-detection row and physical x-span; fail closed when uncalibrated."""
    shelf_snapshot = shelf_snapshot if isinstance(shelf_snapshot, dict) else {}
    try:
        shelf_width_cm = float(shelf_snapshot["width_cm"])
        row_count = int(shelf_snapshot["row_count"])
    except (KeyError, TypeError, ValueError):
        shelf_width_cm, row_count = 0.0, 0
    if not math.isfinite(shelf_width_cm) or shelf_width_cm <= 0 or row_count <= 0 or image_width <= 0 or image_height <= 0:
        return [dict(item, planogram_position=None) for item in detections], {
            "status": "needs_review", "method": "unavailable", "reason": "missing_valid_shelf_or_image_dimensions",
            "position_tolerance_cm": None, "row_index_origin": 0, "row_order": "top_to_bottom",
        }

    tolerance_cm = max(POSITION_TOLERANCE_FLOOR_CM, shelf_width_cm * POSITION_TOLERANCE_WIDTH_RATIO)
    resolved_heights = shelf_snapshot.get("resolved_row_heights_cm")
    row_heights = resolved_heights if isinstance(resolved_heights, list) else []
    points = _valid_corners(shelf_corners_xy, image_width, image_height)
    try:
        homography = _make_homography(points) if points else None
    except ValueError:
        homography = None
    method = "four_corner_homography" if homography else "detected_row_linear"
    valid_rows = [row for row in shelf_rows if _valid_bbox(row.get("bbox_xyxy"))]
    valid_row_numbers = set()
    for row in valid_rows:
        try:
            row_number = int(row.get("row_number"))
        except (TypeError, ValueError):
            continue
        if 1 <= row_number <= row_count:
            valid_row_numbers.add(row_number)
    rows_complete = (
        (len(valid_rows) == row_count and valid_row_numbers == set(range(1, row_count + 1)))
        or (not valid_row_numbers and len(valid_rows) == row_count)
    )
    can_map_positions = bool(homography or valid_rows)
    calibration_complete = bool(homography or (valid_rows and rows_complete))

    calibration = {
        "status": "calibrated" if calibration_complete else "needs_review",
        "method": method if can_map_positions else "unavailable",
        "reason": None if calibration_complete else (
            "detected_row_count_does_not_match_snapshot" if valid_rows
            else "no_valid_shelf_rows_or_corner_calibration"
        ),
        "position_tolerance_cm": round(tolerance_cm, 3),
        "row_index_origin": 0,
        "row_order": "top_to_bottom",
        "shelf_width_cm": shelf_width_cm,
        "straight_on_assumption": not bool(homography),
        "expected_row_count": row_count,
        "detected_row_count": len(valid_rows),
        "row_count_match": rows_complete if valid_rows else None,
    }

    mapped: list[dict[str, Any]] = []
    for item in detections:
        bbox = _valid_bbox(item.get("bbox_xyxy"))
        position = None
        if bbox and can_map_positions:
            x1, y1, x2, y2 = bbox
            if homography:
                try:
                    projected = [_project(homography, x, y) for x, y in ((x1, y1), (x2, y1), (x2, y2), (x1, y2))]
                    center_x, center_y = _project(homography, (x1 + x2) / 2, (y1 + y2) / 2)
                    row_index = _row_index_from_fraction(center_y, row_heights, row_count)
                    nx1 = min(point[0] for point in projected)
                    nx2 = max(point[0] for point in projected)
                    in_frame = 0 <= center_x <= 1 and 0 <= center_y <= 1 and nx2 > 0 and nx1 < 1
                    if in_frame and row_index is not None:
                        position = {
                            "status": "calibrated", "method": method, "row_index": row_index,
                            "x_start_cm": round(max(0.0, nx1) * shelf_width_cm, 3),
                            "x_end_cm": round(min(1.0, nx2) * shelf_width_cm, 3),
                            "center_x_cm": round(center_x * shelf_width_cm, 3),
                            "position_tolerance_cm": round(tolerance_cm, 3),
                        }
                except ValueError:
                    position = None
            else:
                row, row_index = _choose_detected_row(bbox, valid_rows, row_count, item.get("row_number"))
                row_bbox = _valid_bbox(row.get("bbox_xyxy")) if row else None
                if row_bbox and row_index is not None:
                    rx1, _, rx2, _ = row_bbox
                    if rx2 > rx1:
                        nx1 = (x1 - rx1) / (rx2 - rx1)
                        nx2 = (x2 - rx1) / (rx2 - rx1)
                        center_fraction = ((x1 + x2) / 2 - rx1) / (rx2 - rx1)
                        if 0 <= center_fraction <= 1 and nx2 > 0 and nx1 < 1:
                            position = {
                                "status": "calibrated", "method": method, "row_index": row_index,
                                "x_start_cm": round(max(0.0, nx1) * shelf_width_cm, 3),
                                "x_end_cm": round(min(1.0, nx2) * shelf_width_cm, 3),
                                "center_x_cm": round(center_fraction * shelf_width_cm, 3),
                                "position_tolerance_cm": round(tolerance_cm, 3),
                                "detected_row_number": row.get("row_number"),
                            }
        mapped.append(dict(item, planogram_position=position))
    return mapped, calibration
