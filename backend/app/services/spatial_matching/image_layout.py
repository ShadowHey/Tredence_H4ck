"""Normalize calibrated photo detections into row-wise ordered sequences."""

from __future__ import annotations

from typing import Any


def normalize_image_rows(products: list[dict[str, Any]], empty_spaces: list[dict[str, Any]], shelf_width_cm: float) -> dict[int, dict[str, list[dict[str, Any]]]]:
    if shelf_width_cm <= 0:
        return {}
    rows: dict[int, dict[str, list[dict[str, Any]]]] = {}
    for kind, items in (("products", products), ("empty_spaces", empty_spaces)):
        for item in items:
            pos = item.get("planogram_position")
            if not isinstance(pos, dict) or pos.get("status") != "calibrated":
                continue
            try:
                row = int(pos["row_index"])
                start, end = float(pos["x_start_cm"]), float(pos["x_end_cm"])
            except (KeyError, TypeError, ValueError):
                continue
            if row < 0 or start < 0 or end <= start or end > shelf_width_cm + 1e-6:
                continue
            rows.setdefault(row, {"products": [], "empty_spaces": []})[kind].append({
                "cutout_id": str(item.get("id", "")),
                "normalized_start": round(start / shelf_width_cm, 6),
                "normalized_end": round(end / shelf_width_cm, 6),
                "normalized_center": round((start + end) / (2 * shelf_width_cm), 6),
            })
    for row in rows.values():
        for kind in ("products", "empty_spaces"):
            row[kind].sort(key=lambda item: (item["normalized_start"], item["normalized_end"], item["cutout_id"]))
            count = len(row[kind])
            for index, item in enumerate(row[kind]):
                item["ordinal_from_left"] = index + 1
                item["ordinal_from_right"] = count - index
    return rows
