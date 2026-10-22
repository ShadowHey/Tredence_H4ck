"""Convert physical planogram facings to shelf-width-relative row sequences."""

from __future__ import annotations

from typing import Any


def normalize_planogram_rows(slots: list[dict[str, Any]], shelf_width_cm: float) -> dict[int, list[dict[str, Any]]]:
    if shelf_width_cm <= 0:
        return {}
    rows: dict[int, list[dict[str, Any]]] = {}
    for slot in slots:
        try:
            row = int(slot["row_index"])
            start, end = float(slot["x_start_cm"]), float(slot["x_end_cm"])
        except (KeyError, TypeError, ValueError):
            continue
        if row < 0 or start < 0 or end <= start or end > shelf_width_cm + 1e-6:
            continue
        rows.setdefault(row, []).append({
            "slot_id": str(slot.get("slot_id", "")),
            "product_id": slot.get("product_id"),
            "sku": str(slot.get("sku", "")),
            "row_index": row,
            "normalized_start": round(start / shelf_width_cm, 6),
            "normalized_end": round(end / shelf_width_cm, 6),
            "normalized_center": round((start + end) / (2 * shelf_width_cm), 6),
        })
    for row in rows.values():
        row.sort(key=lambda item: (item["normalized_start"], item["normalized_end"], item["slot_id"]))
        count = len(row)
        for index, item in enumerate(row):
            item["ordinal_from_left"] = index + 1
            item["ordinal_from_right"] = count - index
    return rows
