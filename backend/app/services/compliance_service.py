"""Deterministic, snapshot-bound planogram compliance audit generation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from app.services.spatial_matching import build_layout_comparison

AUDIT_SCHEMA_VERSION = 1
AUDIT_VERSION = 4


def _finite_number(value: Any) -> Optional[float]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number == number and abs(number) != float("inf") else None


def _position(item: dict[str, Any]) -> Optional[dict[str, Any]]:
    value = item.get("planogram_position")
    if not isinstance(value, dict) or value.get("status") != "calibrated":
        return None
    row = value.get("row_index")
    start, end, center = (_finite_number(value.get(key)) for key in ("x_start_cm", "x_end_cm", "center_x_cm"))
    if not isinstance(row, int) or start is None or end is None or center is None or end <= start:
        return None
    return {"row_index": row, "x_start_cm": start, "x_end_cm": end, "center_x_cm": center,
            "position_tolerance_cm": _finite_number(value.get("position_tolerance_cm")) or 1.0}


def _slot_geometry(slot: dict[str, Any]) -> Optional[dict[str, Any]]:
    row = slot.get("row_index")
    start, end = (_finite_number(slot.get(key)) for key in ("x_start_cm", "x_end_cm"))
    if not isinstance(row, int) or start is None or end is None or end <= start:
        return None
    return {"row_index": row, "x_start_cm": start, "x_end_cm": end,
            "center_x_cm": (start + end) / 2}


def _slot_distance(position: dict[str, Any], slot: dict[str, Any]) -> tuple[int, float, float]:
    overlap = max(0.0, min(position["x_end_cm"], slot["x_end_cm"]) - max(position["x_start_cm"], slot["x_start_cm"]))
    width = max(1e-9, min(position["x_end_cm"] - position["x_start_cm"], slot["x_end_cm"] - slot["x_start_cm"]))
    overlap_ratio = overlap / width
    gap = max(0.0, slot["x_start_cm"] - position["x_end_cm"], position["x_start_cm"] - slot["x_end_cm"])
    center_delta = abs(position["center_x_cm"] - slot["center_x_cm"])
    return (0 if position["row_index"] == slot["row_index"] else 1, -overlap_ratio, gap + center_delta * 0.01)


def build_compliance_audit(
    *, output_id: int, job_id: int, source_filename: str, snapshot: Optional[dict[str, Any]],
    snapshot_sha256: Optional[str], products: list[dict[str, Any]], empty_spaces: list[dict[str, Any]],
    position_calibration: Optional[dict[str, Any]] = None, label_audit: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Assign product detections to facing slots and derive explainable findings.

    Assignment is deterministic: products are considered top-to-bottom and left-to-right;
    each is assigned to the best remaining physical slot, preferring its detected row.
    The matcher does not upgrade uncertain catalogue or position evidence into certainty.
    """
    now = datetime.now(timezone.utc)
    slots = snapshot.get("expected_facing_slots", []) if isinstance(snapshot, dict) else []
    if not isinstance(slots, list):
        slots = []
    valid_slots = []
    for raw in slots:
        if not isinstance(raw, dict):
            continue
        geometry = _slot_geometry(raw)
        if geometry is None:
            continue
        valid_slots.append({**raw, **geometry, "slot_id": str(raw.get("slot_id", "")),
                            "product_id": raw.get("product_id"), "sku": str(raw.get("sku", ""))})
    valid_slots.sort(key=lambda slot: (slot["row_index"], slot["x_start_cm"], slot["slot_id"]))
    try:
        shelf_width_cm = float(snapshot.get("width_cm", 0)) if isinstance(snapshot, dict) else 0.0
    except (TypeError, ValueError):
        shelf_width_cm = 0.0
    if shelf_width_cm <= 0:
        shelf_width_cm = max((slot["x_end_cm"] for slot in valid_slots), default=0.0)
    row_counts: dict[int, int] = {}
    for slot in valid_slots:
        row_counts[slot["row_index"]] = row_counts.get(slot["row_index"], 0) + 1
    slot_ordinals: dict[str, tuple[int, int]] = {}
    row_seen: dict[int, int] = {}
    for slot in valid_slots:
        row_seen[slot["row_index"]] = row_seen.get(slot["row_index"], 0) + 1
        slot_ordinals[slot["slot_id"]] = (row_seen[slot["row_index"]], row_counts[slot["row_index"]] - row_seen[slot["row_index"]] + 1)
    available = {slot["slot_id"]: slot for slot in valid_slots}
    expected_ids = {str(slot["product_id"]) for slot in valid_slots if slot.get("product_id") is not None}
    assignments: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    correctly_occupied: set[str] = set()
    observed_by_product: dict[str, int] = {}
    assigned_cutout_by_slot: dict[str, str] = {}
    assigned_item_by_slot: dict[str, dict[str, Any]] = {}

    ordered_products = sorted(products, key=lambda item: (
        (_position(item) or {}).get("row_index", 10**6),
        (_position(item) or {}).get("center_x_cm", 10**9), str(item.get("id", ""))))
    product_ordinals: dict[str, tuple[int, int]] = {}
    products_by_row: dict[int, list[dict[str, Any]]] = {}
    for item in ordered_products:
        position = _position(item)
        if position:
            products_by_row.setdefault(position["row_index"], []).append(item)
    for row_items in products_by_row.values():
        for index, item in enumerate(row_items):
            product_ordinals[str(item.get("id", "unknown"))] = (index + 1, len(row_items) - index)
    for item in ordered_products:
        cutout_id = str(item.get("id", "unknown"))
        match = item.get("catalog_match") if isinstance(item.get("catalog_match"), dict) else {}
        candidate = match.get("top_candidate") if isinstance(match.get("top_candidate"), dict) else None
        product_id = str(candidate.get("id")) if candidate and candidate.get("id") is not None else None
        sku = str(candidate.get("sku", "")) if candidate else None
        position = _position(item)
        slot = None
        if position and available:
            slot = min(available.values(), key=lambda candidate_slot: (
                *_slot_distance(position, candidate_slot), candidate_slot["row_index"],
                candidate_slot["x_start_cm"], candidate_slot["slot_id"]))
            del available[slot["slot_id"]]
            assigned_item_by_slot[slot["slot_id"]] = item
            assigned_cutout_by_slot[slot["slot_id"]] = cutout_id

        status = "needs_review"
        reason = "position_unavailable" if position is None else "catalogue_identity_unavailable"
        if match.get("status") == "unmatched":
            status, reason = "unrecognised_product", str(match.get("reason", "catalogue_match_unresolved"))
        elif match.get("status") == "needs_review":
            status, reason = "needs_review", str(match.get("reason", "catalogue_match_ambiguous"))
        elif match.get("status") == "matched" and candidate:
            observed_by_product[product_id] = observed_by_product.get(product_id, 0) + 1
            if product_id not in expected_ids:
                status, reason = "unexpected_product", "product_not_expected_on_selected_shelf"
            elif slot is None:
                status, reason = "unexpected_product", "no_remaining_expected_facing_slot"
            else:
                same_product = str(slot.get("product_id")) == product_id
                same_row = position["row_index"] == slot["row_index"]
                tolerance = max(position["position_tolerance_cm"], 1.0)
                center_in_slot = slot["x_start_cm"] - tolerance <= position["center_x_cm"] <= slot["x_end_cm"] + tolerance
                if same_product and same_row and center_in_slot:
                    status, reason = "correct", "identity_and_position_match"
                    correctly_occupied.add(slot["slot_id"])
                else:
                    status, reason = "misplaced_product", "identity_or_position_does_not_match_expected_slot"
        elif slot is not None:
            status, reason = "needs_review", "catalogue_identity_unavailable"

        assignment = {"cutout_id": cutout_id, "product_id": product_id, "sku": sku,
                      "slot_id": slot["slot_id"] if slot else None,
                      "expected_product_id": slot.get("product_id") if slot else None,
                      "expected_sku": slot.get("sku") if slot else None,
                      "row_index": position["row_index"] if position else None,
                      "x_start_cm": position["x_start_cm"] if position else None,
                      "x_end_cm": position["x_end_cm"] if position else None,
                      "status": status, "reason": reason}
        if position and shelf_width_cm > 0:
            assignment["normalized_start"] = round(position["x_start_cm"] / shelf_width_cm, 6)
            assignment["normalized_end"] = round(position["x_end_cm"] / shelf_width_cm, 6)
            assignment["normalized_center"] = round(position["center_x_cm"] / shelf_width_cm, 6)
            assignment["ordinal_from_left"], assignment["ordinal_from_right"] = product_ordinals.get(cutout_id, (None, None))
        if slot:
            assignment["expected_ordinal_from_left"], assignment["expected_ordinal_from_right"] = slot_ordinals[slot["slot_id"]]
        assignments.append(assignment)
        if status != "correct":
            issues.append({"type": status, "severity": "warning" if status == "needs_review" else "error",
                           "cutout_id": cutout_id, "slot_id": assignment["slot_id"],
                           "product_id": product_id, "sku": sku, "expected_sku": assignment["expected_sku"],
                           "row_index": assignment["row_index"], "x_start_cm": assignment["x_start_cm"],
                           "x_end_cm": assignment["x_end_cm"], "reason": reason})
            issues[-1]["normalized_start"] = assignment.get("normalized_start")
            issues[-1]["normalized_end"] = assignment.get("normalized_end")
            issues[-1]["ordinal_from_left"] = assignment.get("ordinal_from_left")
            issues[-1]["ordinal_from_right"] = assignment.get("ordinal_from_right")
            issues[-1]["expected_ordinal_from_left"] = assignment.get("expected_ordinal_from_left")

    empty_positions = [(str(item.get("id", "")), _position(item)) for item in empty_spaces]
    # Without a valid position mapping, absence cannot safely be asserted from image detections.
    positions_available = bool(isinstance(position_calibration, dict) and position_calibration.get("status") == "calibrated")
    slot_results = []
    expected_quantity: dict[str, int] = {}
    for slot in valid_slots:
        product_id = str(slot.get("product_id"))
        expected_quantity[product_id] = expected_quantity.get(product_id, 0) + 1
    for slot in valid_slots:
        is_correct = slot["slot_id"] in correctly_occupied
        occupant = assigned_item_by_slot.get(slot["slot_id"])
        occupant_match = occupant.get("catalog_match") if isinstance(occupant, dict) else None
        occupant_candidate = occupant_match.get("top_candidate") if isinstance(occupant_match, dict) else None
        if is_correct:
            status = "correct"
        elif not positions_available:
            status = "needs_review"
        elif occupant and isinstance(occupant_match, dict) and occupant_match.get("status") == "matched":
            status = "misplaced_product"
        elif occupant:
            status = "needs_review"
        else:
            product_id = str(slot.get("product_id"))
            observed = observed_by_product.get(product_id, 0)
            expected = expected_quantity.get(product_id, 0)
            status = "missing_product" if observed == 0 else (
                "insufficient_quantity" if observed < expected else "misplaced_product")
        evidence = [empty_id for empty_id, pos in empty_positions if pos and
                    pos["row_index"] == slot["row_index"] and
                    max(0.0, min(pos["x_end_cm"], slot["x_end_cm"]) - max(pos["x_start_cm"], slot["x_start_cm"])) > 0]
        cutout_evidence = [assigned_cutout_by_slot[slot["slot_id"]]] if slot["slot_id"] in assigned_cutout_by_slot else []
        entry = {"slot_id": slot["slot_id"], "placement_id": slot.get("placement_id"),
                 "product_id": slot.get("product_id"), "sku": slot.get("sku"),
                 "row_index": slot["row_index"], "x_start_cm": slot["x_start_cm"],
                 "x_end_cm": slot["x_end_cm"], "status": status,
                 "normalized_start": round(slot["x_start_cm"] / shelf_width_cm, 6) if shelf_width_cm > 0 else None,
                 "normalized_end": round(slot["x_end_cm"] / shelf_width_cm, 6) if shelf_width_cm > 0 else None,
                 "normalized_center": round(slot["center_x_cm"] / shelf_width_cm, 6) if shelf_width_cm > 0 else None,
                 "ordinal_from_left": slot_ordinals[slot["slot_id"]][0],
                 "ordinal_from_right": slot_ordinals[slot["slot_id"]][1],
                 "actual_product_id": occupant_candidate.get("id") if isinstance(occupant_candidate, dict) else None,
                 "actual_sku": occupant_candidate.get("sku") if isinstance(occupant_candidate, dict) else None,
                 "evidence": {"empty_space_cutout_ids": evidence, "product_cutout_ids": cutout_evidence}}
        slot_results.append(entry)
        if status != "correct":
            issues.append({"type": status, "severity": "warning" if status == "needs_review" else "error",
                           "slot_id": entry["slot_id"], "placement_id": entry["placement_id"],
                           "product_id": entry["product_id"], "sku": entry["sku"],
                           "row_index": entry["row_index"], "x_start_cm": entry["x_start_cm"],
                           "x_end_cm": entry["x_end_cm"], "evidence": entry["evidence"],
                           "reason": "expected_slot_not_confirmed"})
            issues[-1]["normalized_start"] = entry["normalized_start"]
            issues[-1]["normalized_end"] = entry["normalized_end"]
            issues[-1]["ordinal_from_left"] = entry["ordinal_from_left"]

    if not isinstance(snapshot, dict):
        issues.append({"type": "needs_review", "severity": "warning", "reason": "missing_audit_snapshot",
                       "message": "No frozen planogram snapshot is available; compliance cannot be asserted."})

    label_audit = label_audit if isinstance(label_audit, dict) else {"status": "unavailable", "zones": [], "issues": []}
    label_issues = label_audit.get("issues", [])
    if isinstance(label_issues, list):
        issues.extend(label_issues)

    summary: dict[str, int] = {key: 0 for key in ("correct", "misplaced_product", "missing_product",
        "insufficient_quantity", "unexpected_product", "unrecognised_product", "needs_review", "label_issue_count")}
    for assignment in assignments:
        summary[assignment["status"]] = summary.get(assignment["status"], 0) + 1
    for slot in slot_results:
        if slot["status"] in ("missing_product", "insufficient_quantity", "needs_review"):
            summary[slot["status"]] = summary.get(slot["status"], 0) + 1
    summary["label_issue_count"] = len(label_issues) if isinstance(label_issues, list) else 0
    if isinstance(label_issues, list):
        summary["needs_review"] += sum(1 for issue in label_issues
                                       if isinstance(issue, dict) and issue.get("type") == "needs_review")
    status = "needs_review" if (any(issue["type"] == "needs_review" for issue in issues)
                                  or label_audit.get("status") in ("unavailable", "needs_review")) else "complete"
    layout_comparison = build_layout_comparison(snapshot=snapshot if isinstance(snapshot, dict) else None,
        products=products, empty_spaces=empty_spaces, assignments=assignments, calibration=position_calibration)
    return {"schema_version": AUDIT_SCHEMA_VERSION, "audit_version": AUDIT_VERSION,
            "output_id": output_id, "job_id": job_id, "source_filename": source_filename,
            "audit_snapshot_sha256": snapshot_sha256, "status": status,
            "summary": summary, "assignments": assignments, "slot_results": slot_results,
            "layout_comparison": layout_comparison,
            "label_audit": label_audit,
            "issues": issues, "created_at": now.isoformat()}
