"""Build a JSON-safe, normalized row/position comparison for audit output."""

from __future__ import annotations

from typing import Any

from .image_layout import normalize_image_rows
from .planogram_layout import normalize_planogram_rows
from .sequence_alignment import align_sequences, free_intervals


def build_layout_comparison(
    *, snapshot: dict[str, Any] | None, products: list[dict[str, Any]], empty_spaces: list[dict[str, Any]],
    assignments: list[dict[str, Any]], calibration: dict[str, Any] | None,
) -> dict[str, Any]:
    snapshot = snapshot if isinstance(snapshot, dict) else {}
    calibration = calibration if isinstance(calibration, dict) else {}
    try:
        width = float(snapshot.get("width_cm") or calibration.get("shelf_width_cm") or 0)
    except (TypeError, ValueError):
        width = 0.0
    expected_slots = snapshot.get("expected_facing_slots", [])
    expected_slots = [item for item in expected_slots if isinstance(item, dict)] if isinstance(expected_slots, list) else []
    if width <= 0:
        width = max((float(item.get("x_end_cm", 0) or 0) for item in expected_slots), default=0.0)
    expected = normalize_planogram_rows(expected_slots, width)
    actual = normalize_image_rows(products, empty_spaces, width)
    assignment_by_slot = {str(item.get("slot_id")): item for item in assignments if item.get("slot_id")}
    rows = []
    row_indices = sorted(set(expected) | set(actual))
    for row_index in row_indices:
        expected_row = expected.get(row_index, [])
        actual_row = actual.get(row_index, {"products": [], "empty_spaces": []})
        rows.append({
            "row_index": row_index,
            "row_number": row_index + 1,
            "alignment_status": "aligned" if calibration.get("status") == "calibrated" else "needs_review",
            "expected_facings": [{**slot, "status": assignment_by_slot.get(slot["slot_id"], {}).get(
                "status", "missing" if calibration.get("status") == "calibrated" else "needs_review")}
                                  for slot in expected_row],
            "observed_products": actual_row["products"],
            "observed_empty_regions": actual_row["empty_spaces"],
            "sequence_alignment": align_sequences(expected_row, actual_row["products"]),
            "expected_free_intervals": free_intervals(expected_row, start_key="normalized_start", end_key="normalized_end"),
            "observed_free_intervals": free_intervals(actual_row["products"], start_key="normalized_start", end_key="normalized_end"),
        })
    return {
        "coordinate_system": "normalized_shelf_width",
        "normalized_axis": {"origin": "left", "range": [0.0, 1.0]},
        "row_order": "top_to_bottom",
        "shelf_width_cm": width or None,
        "calibration_status": calibration.get("status", "unavailable"),
        "comparison_status": "ready" if width > 0 and calibration.get("status") == "calibrated" else "needs_review",
        "rows": rows,
    }
