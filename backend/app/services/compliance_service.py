"""Deterministic, snapshot-bound planogram compliance audit generation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from app.services.spatial_matching import build_layout_comparison

AUDIT_SCHEMA_VERSION = 1
AUDIT_VERSION = 11
LOW_STOCK_OCCUPANCY_THRESHOLD = 0.50
SAME_ROW_COUNT_VARIATION_TOLERANCE = 2
COMPLIANCE_SCORE_FORMULA_VERSION = 1
COMPLIANCE_SCORE_MIN_EVIDENCE_COVERAGE_PERCENT = 80.0


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


def _build_compliance_score(
    *, snapshot_available: bool, positions_available: bool, slot_results: list[dict[str, Any]],
    assignments: list[dict[str, Any]], issues: list[dict[str, Any]], excluded_product_count: int,
) -> dict[str, Any]:
    """Return a facing-based score without treating inconclusive evidence as failure.

    The score measures only expected, physically addressable facings. Review-only
    slots reduce evidence coverage, not the score itself. A recognised unexpected
    product outside all expected slots is the sole non-slot penalty.
    """
    expected_slot_ids = {str(slot.get("slot_id")) for slot in slot_results if slot.get("slot_id")}
    correct_slot_ids = {
        str(slot["slot_id"]) for slot in slot_results
        if slot.get("slot_id") and slot.get("status") == "correct"
    }
    non_compliant_statuses = {"misplaced_product", "missing_product", "insufficient_quantity", "empty_space"}
    non_compliant_slot_ids = {
        str(slot["slot_id"]) for slot in slot_results
        if slot.get("slot_id") and slot.get("status") in non_compliant_statuses
    }
    # A recognised product from outside the selected shelf catalogue can occupy an
    # expected slot even though the slot result is conservatively marked review.
    for assignment in assignments:
        slot_id = assignment.get("slot_id")
        if assignment.get("status") in {"misplaced_product", "unexpected_product"} and slot_id:
            slot_id = str(slot_id)
            if slot_id in expected_slot_ids:
                non_compliant_slot_ids.add(slot_id)
    correct_slot_ids -= non_compliant_slot_ids

    unexpected_cutout_ids = {
        str(assignment.get("cutout_id") or f"unexpected-{index}")
        for index, assignment in enumerate(assignments)
        if assignment.get("status") == "unexpected_product" and not assignment.get("slot_id")
    }
    expected_facing_count = len(expected_slot_ids)
    correct_facing_count = len(correct_slot_ids)
    non_compliant_facing_count = len(non_compliant_slot_ids)
    unexpected_product_count = len(unexpected_cutout_ids)
    assessed_facing_count = correct_facing_count + non_compliant_facing_count
    review_facing_count = max(0, expected_facing_count - assessed_facing_count)
    coverage_percent = round(
        (assessed_facing_count / expected_facing_count) * 100 if expected_facing_count else 0.0,
        1,
    )
    score_denominator = assessed_facing_count + unexpected_product_count
    review_blockers = any(
        issue.get("type") == "needs_review" and not issue.get("provisional", False)
        for issue in issues
        if isinstance(issue, dict)
    )

    reasons: list[str] = []
    if not snapshot_available:
        reasons.append("missing_audit_snapshot")
    if not positions_available:
        reasons.append("position_calibration_unavailable")
    if expected_facing_count == 0:
        reasons.append("no_expected_facings")
    if assessed_facing_count == 0:
        reasons.append("no_definitive_facing_outcomes")
    if coverage_percent < COMPLIANCE_SCORE_MIN_EVIDENCE_COVERAGE_PERCENT:
        reasons.append("insufficient_evidence_coverage")

    cannot_score = bool(
        not snapshot_available
        or not positions_available
        or expected_facing_count == 0
        or assessed_facing_count == 0
        or coverage_percent < COMPLIANCE_SCORE_MIN_EVIDENCE_COVERAGE_PERCENT
    )
    if cannot_score:
        state = "not_scored"
        score = None
    else:
        if excluded_product_count:
            reasons.append("low_confidence_product_detections_excluded")
        if review_facing_count:
            reasons.append("facing_slots_need_review")
        if review_blockers:
            reasons.append("audit_review_required")
        state = "provisional" if reasons else "verified"
        score = round((correct_facing_count / score_denominator) * 100, 1) if score_denominator else None

    return {
        "formula_version": COMPLIANCE_SCORE_FORMULA_VERSION,
        "score": score,
        "state": state,
        "evidence_coverage_percent": coverage_percent,
        "evidence_coverage_threshold_percent": COMPLIANCE_SCORE_MIN_EVIDENCE_COVERAGE_PERCENT,
        "expected_facing_count": expected_facing_count,
        "correct_facing_count": correct_facing_count,
        "non_compliant_facing_count": non_compliant_facing_count,
        "unexpected_product_count": unexpected_product_count,
        "review_facing_count": review_facing_count,
        "assessed_facing_count": assessed_facing_count,
        "score_denominator": score_denominator,
        "reasons": reasons,
    }


def build_compliance_audit(
    *, output_id: int, job_id: int, source_filename: str, snapshot: Optional[dict[str, Any]],
    snapshot_sha256: Optional[str], products: list[dict[str, Any]], empty_spaces: list[dict[str, Any]],
    excluded_products: Optional[list[dict[str, Any]]] = None,
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
    available_by_row: dict[int, dict[str, dict[str, Any]]] = {}
    expected_product_by_row: dict[int, set[str]] = {}
    expected_sku_by_product: dict[str, str] = {}
    expected_row_by_product: dict[str, int] = {}
    expected_name_by_product: dict[str, str] = {}
    if isinstance(snapshot, dict):
        for placement in snapshot.get("expected_placements", []):
            if isinstance(placement, dict) and placement.get("product_id") is not None:
                expected_name_by_product[str(placement["product_id"])] = str(placement.get("product_name", ""))
    for slot in valid_slots:
        available_by_row.setdefault(slot["row_index"], {})[slot["slot_id"]] = slot
        product_id = str(slot.get("product_id"))
        expected_product_by_row.setdefault(slot["row_index"], set()).add(product_id)
        expected_sku_by_product[product_id] = slot.get("sku", "")
        expected_row_by_product.setdefault(product_id, slot["row_index"])
    row_expected_product = {
        row: next(iter(product_ids)) for row, product_ids in expected_product_by_row.items()
        if len(product_ids) == 1
    }
    expected_ids = {str(slot["product_id"]) for slot in valid_slots if slot.get("product_id") is not None}
    assignments: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    correctly_occupied: set[str] = set()
    observed_by_product_row: dict[tuple[str, int], int] = {}
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
    expected_quantity_by_product_row: dict[tuple[str, int], int] = {}
    for slot in valid_slots:
        key = (str(slot.get("product_id")), slot["row_index"])
        expected_quantity_by_product_row[key] = expected_quantity_by_product_row.get(key, 0) + 1
    observed_quantity_by_product_row: dict[tuple[str, int], int] = {}
    for item in ordered_products:
        match = item.get("catalog_match") if isinstance(item.get("catalog_match"), dict) else {}
        candidate = match.get("top_candidate") if isinstance(match.get("top_candidate"), dict) else None
        position = _position(item)
        if (match.get("status") in {"matched", "needs_review"} and candidate
                and candidate.get("id") is not None and position
                and str(candidate["id"]) == row_expected_product.get(position["row_index"])):
            key = (str(candidate["id"]), position["row_index"])
            observed_quantity_by_product_row[key] = observed_quantity_by_product_row.get(key, 0) + 1
    for item in ordered_products:
        cutout_id = str(item.get("id", "unknown"))
        match = item.get("catalog_match") if isinstance(item.get("catalog_match"), dict) else {}
        candidate = match.get("top_candidate") if isinstance(match.get("top_candidate"), dict) else None
        product_id = str(candidate.get("id")) if candidate and candidate.get("id") is not None else None
        sku = str(candidate.get("sku", "")) if candidate else None
        position = _position(item)
        slot = None
        row_available = available_by_row.get(position["row_index"], {}) if position else {}
        if position and row_available:
            slot = min(row_available.values(), key=lambda candidate_slot: (
                *_slot_distance(position, candidate_slot), candidate_slot["row_index"],
                candidate_slot["x_start_cm"], candidate_slot["slot_id"]))
            del row_available[slot["slot_id"]]
            assigned_item_by_slot[slot["slot_id"]] = item
            assigned_cutout_by_slot[slot["slot_id"]] = cutout_id
        elif position:
            row_slots = [candidate_slot for candidate_slot in valid_slots
                         if candidate_slot["row_index"] == position["row_index"]]
            if row_slots:
                slot = min(row_slots, key=lambda candidate_slot: (
                    *_slot_distance(position, candidate_slot), candidate_slot["x_start_cm"], candidate_slot["slot_id"]))

        status = "needs_review"
        reason = "position_unavailable" if position is None else "catalogue_identity_unavailable"
        expected_for_row = row_expected_product.get(position["row_index"]) if position else None
        row_consensus_match = bool(product_id and expected_for_row and product_id == expected_for_row
                                   and match.get("status") in {"matched", "needs_review"})
        if match.get("status") == "unmatched":
            status, reason = "unrecognised_product", str(match.get("reason", "catalogue_match_unresolved"))
        elif row_consensus_match:
            observed_key = (product_id, position["row_index"])
            observed_by_product_row[observed_key] = observed_by_product_row.get(observed_key, 0) + 1
            if slot is not None and slot["slot_id"] in assigned_item_by_slot and assigned_item_by_slot[slot["slot_id"]] is item:
                status, reason = "correct", "row_catalogue_consensus_matches_expected_product"
                correctly_occupied.add(slot["slot_id"])
            else:
                # Same-row expected-SKU surplus is not a compliance violation; it can
                # be caused by real facings beyond the planogram count or detector crops.
                status, reason = "count_variation_tolerated", "expected_product_present_on_correct_row"
        elif match.get("status") == "needs_review":
            status, reason = "needs_review", str(match.get("reason", "catalogue_match_ambiguous"))
        elif match.get("status") == "matched" and candidate:
            observed_key = (product_id, position["row_index"]) if position else None
            if observed_key:
                observed_by_product_row[observed_key] = observed_by_product_row.get(observed_key, 0) + 1
            if product_id not in expected_ids:
                status, reason = "unexpected_product", "product_not_expected_on_selected_shelf"
            elif (position and expected_for_row is not None and product_id != expected_for_row
                  and product_id in expected_row_by_product):
                status, reason = "misplaced_product", "recognized_product_on_wrong_planogram_row"
            elif slot is None:
                count_key = (product_id, position["row_index"])
                expected_count = expected_quantity_by_product_row.get(count_key, 0)
                observed_count = observed_quantity_by_product_row.get(count_key, 0)
                if (expected_count > 0
                        and observed_count <= expected_count + SAME_ROW_COUNT_VARIATION_TOLERANCE):
                    status, reason = "count_variation_tolerated", "same_row_same_sku_count_delta_within_tolerance"
                else:
                    status, reason = "unexpected_product", "no_remaining_expected_facing_slot"
            else:
                same_product = str(slot.get("product_id")) == product_id
                same_row = position["row_index"] == slot["row_index"]
                tolerance = max(position["position_tolerance_cm"], 1.0)
                center_in_slot = slot["x_start_cm"] - tolerance <= position["center_x_cm"] <= slot["x_end_cm"] + tolerance
                if same_product and same_row and center_in_slot:
                    status, reason = "correct", "identity_and_position_match"
                    correctly_occupied.add(slot["slot_id"])
                elif (position and expected_for_row is None and same_product and same_row):
                    # A heterogeneous row still uses exact local facing geometry;
                    # only homogeneous rows can use row-level identity consensus.
                    status, reason = "correct", "identity_matches_nearest_row_facing"
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
        if status in {"misplaced_product", "unexpected_product", "unrecognised_product"}:
            issue = {"type": status, "severity": "error",
                           "cutout_id": cutout_id, "slot_id": assignment["slot_id"],
                           "product_id": product_id, "sku": sku, "expected_sku": assignment["expected_sku"],
                           "product_name": candidate.get("name") if candidate else None,
                           "expected_product_name": expected_name_by_product.get(str(slot.get("product_id"))) if slot else None,
                           "row_index": assignment["row_index"], "x_start_cm": assignment["x_start_cm"],
                           "x_end_cm": assignment["x_end_cm"], "reason": reason}
            if status == "misplaced_product" and product_id in expected_row_by_product:
                issue["target_row_number"] = expected_row_by_product[product_id] + 1
            issues.append(issue)
            issues[-1]["normalized_start"] = assignment.get("normalized_start")
            issues[-1]["normalized_end"] = assignment.get("normalized_end")
            issues[-1]["ordinal_from_left"] = assignment.get("ordinal_from_left")
            issues[-1]["ordinal_from_right"] = assignment.get("ordinal_from_right")
            issues[-1]["expected_ordinal_from_left"] = assignment.get("expected_ordinal_from_left")

    empty_positions = [(str(item.get("id", "")), _position(item)) for item in empty_spaces]
    excluded_positions = [_position(item) for item in (excluded_products or [])]
    excluded_positions = [position for position in excluded_positions if position]

    def slot_has_excluded_candidate(slot: dict[str, Any]) -> bool:
        return any(
            candidate["row_index"] == slot["row_index"]
            and max(0.0, min(candidate["x_end_cm"], slot["x_end_cm"])
                    - max(candidate["x_start_cm"], slot["x_start_cm"])) > 0
            for candidate in excluded_positions
        )
    # Without a valid position mapping, absence cannot safely be asserted from image detections.
    positions_available = bool(isinstance(position_calibration, dict) and position_calibration.get("status") == "calibrated")
    slot_results = []
    # Inventory thresholds are evaluated per planogram placement, not per facing
    # and not across every occurrence of a SKU on the entire shelf.
    placement_groups: dict[tuple[str, str, int], list[dict[str, Any]]] = {}
    for slot in valid_slots:
        placement_key = (str(slot.get("placement_id") or slot["slot_id"]),
                         str(slot.get("product_id")), slot["row_index"])
        placement_groups.setdefault(placement_key, []).append(slot)
    placement_occupancy: dict[tuple[str, str, int], tuple[int, int]] = {}
    for key, group_slots in placement_groups.items():
        _placement_id, product_id, row_index = key
        # Count recognized units in this row even when misplaced within it; a
        # position error is not itself evidence of a stock shortage.
        reliable_slots = [slot for slot in group_slots if not slot_has_excluded_candidate(slot)]
        occupied = min(len(reliable_slots), observed_by_product_row.get((product_id, row_index), 0))
        placement_occupancy[key] = (occupied, len(reliable_slots))

    for slot in valid_slots:
        is_correct = slot["slot_id"] in correctly_occupied
        occupant = assigned_item_by_slot.get(slot["slot_id"])
        occupant_match = occupant.get("catalog_match") if isinstance(occupant, dict) else None
        occupant_candidate = occupant_match.get("top_candidate") if isinstance(occupant_match, dict) else None
        if is_correct:
            status = "correct"
        elif occupant and occupant.get("id") and any(
                assignment["cutout_id"] == occupant.get("id") and assignment["status"] == "misplaced_product"
                for assignment in assignments):
            status = "misplaced_product"
        elif not positions_available:
            status = "needs_review"
        elif occupant:
            status = "needs_review"
        elif slot_has_excluded_candidate(slot):
            status = "needs_review"
        else:
            placement_key = (str(slot.get("placement_id") or slot["slot_id"]),
                             str(slot.get("product_id")), slot["row_index"])
            occupied, _expected = placement_occupancy[placement_key]
            status = "missing_product" if occupied == 0 else "insufficient_quantity"
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

    # Empty detector regions are operator-visible findings even when the SKU still
    # exceeds the low-stock threshold. Emit at most one finding per empty expected slot.
    empty_reported_slots: set[str] = set()
    if positions_available:
        for empty_id, empty_position in empty_positions:
            if empty_position is None:
                continue
            row_slots = [slot for slot in valid_slots if slot["row_index"] == empty_position["row_index"]]
            overlaps = [(max(0.0, min(empty_position["x_end_cm"], slot["x_end_cm"])
                             - max(empty_position["x_start_cm"], slot["x_start_cm"])), slot)
                        for slot in row_slots]
            overlap, empty_slot = max(overlaps, key=lambda item: (item[0], -abs(
                (item[1]["x_start_cm"] + item[1]["x_end_cm"]) / 2 - empty_position["center_x_cm"])),
                default=(0.0, None))
            if empty_slot is None or overlap <= 0 or empty_slot["slot_id"] in assigned_item_by_slot:
                continue
            if slot_has_excluded_candidate(empty_slot):
                continue
            if empty_slot["slot_id"] in empty_reported_slots:
                continue
            empty_reported_slots.add(empty_slot["slot_id"])
            slot_result = next((item for item in slot_results if item["slot_id"] == empty_slot["slot_id"]), None)
            if slot_result:
                slot_result["status"] = "empty_space"
                slot_result["evidence"]["empty_space_cutout_ids"] = [empty_id]
            issues.append({"type": "empty_space", "severity": "warning", "row_index": empty_position["row_index"],
                           "x_start_cm": empty_position["x_start_cm"], "x_end_cm": empty_position["x_end_cm"],
                           "slot_id": empty_slot["slot_id"], "placement_id": empty_slot.get("placement_id"),
                           "product_id": empty_slot.get("product_id"), "sku": empty_slot.get("sku"),
                           "expected_sku": empty_slot.get("sku"), "cutout_id": empty_id,
                           "expected_product_name": expected_name_by_product.get(str(empty_slot.get("product_id"))),
                           "evidence": {"empty_space_cutout_ids": [empty_id], "product_cutout_ids": []},
                           "reason": "empty_detected_inside_expected_facing"})

    # Emit one actionable availability alert per placement only when half or less
    # of its expected facings are correctly present. Slot-level gaps above remain
    # available as detailed report evidence even when below the alert threshold.
    for (placement_id, product_id, row_index), group_slots in placement_groups.items():
        occupied, expected = placement_occupancy[(placement_id, product_id, row_index)]
        occupancy_ratio = occupied / expected if expected else 1.0
        if (not positions_available or expected == 0 or occupied == expected
                or occupancy_ratio > LOW_STOCK_OCCUPANCY_THRESHOLD):
            continue
        status = "missing_product" if occupied == 0 else "insufficient_quantity"
        evidence = [empty_id for empty_id, pos in empty_positions if pos and pos["row_index"] == row_index
                    and any(max(0.0, min(pos["x_end_cm"], slot["x_end_cm"])
                                - max(pos["x_start_cm"], slot["x_start_cm"])) > 0
                            for slot in group_slots)]
        issues.append({
            "type": status,
            "severity": "error" if occupied == 0 else "warning",
            "placement_id": group_slots[0].get("placement_id"),
            "product_id": group_slots[0].get("product_id"),
            "sku": group_slots[0].get("sku"),
            "row_index": row_index,
            "x_start_cm": min(slot["x_start_cm"] for slot in group_slots),
            "x_end_cm": max(slot["x_end_cm"] for slot in group_slots),
            "expected_quantity": expected,
            "observed_quantity": occupied,
            "occupancy_ratio": round(occupancy_ratio, 4),
            "evidence": {"empty_space_cutout_ids": sorted(set(evidence)),
                         "product_cutout_ids": [assigned_cutout_by_slot[slot["slot_id"]]
                                                for slot in group_slots if slot["slot_id"] in assigned_cutout_by_slot]},
            "reason": "placement_occupancy_at_or_below_half" if occupied else "no_attributable_facing_in_row",
        })

    if not isinstance(snapshot, dict):
        issues.append({"type": "needs_review", "severity": "warning", "reason": "missing_audit_snapshot",
                       "message": "No frozen planogram snapshot is available; compliance cannot be asserted."})

    label_audit = label_audit if isinstance(label_audit, dict) else {"status": "unavailable", "zones": [], "issues": []}
    label_issues = label_audit.get("issues", [])
    actionable_label_issues = [issue for issue in label_issues if isinstance(issue, dict)
                               and issue.get("type") != "ocr_engine_unavailable"
                               and issue.get("reason") != "ocr_engine_unavailable"] if isinstance(label_issues, list) else []
    issues.extend(actionable_label_issues)

    summary: dict[str, int] = {key: 0 for key in ("correct", "count_variation_tolerated", "misplaced_product", "missing_product",
        "insufficient_quantity", "unexpected_product", "unrecognised_product", "empty_space", "needs_review", "label_issue_count")}
    for assignment in assignments:
        summary[assignment["status"]] = summary.get(assignment["status"], 0) + 1
    summary["missing_product"] = sum(1 for issue in issues if issue["type"] == "missing_product")
    summary["insufficient_quantity"] = sum(1 for issue in issues if issue["type"] == "insufficient_quantity")
    summary["empty_space"] = sum(1 for issue in issues if issue["type"] == "empty_space")
    summary["needs_review"] = sum(1 for issue in issues if issue["type"] == "needs_review")
    summary["label_issue_count"] = len(actionable_label_issues)
    summary["excluded_low_confidence_products"] = len(excluded_positions)
    status = "needs_review" if (any(issue["type"] == "needs_review" for issue in issues)
                                  or excluded_positions or not positions_available or not isinstance(snapshot, dict)) else "complete"
    layout_comparison = build_layout_comparison(snapshot=snapshot if isinstance(snapshot, dict) else None,
        products=products, empty_spaces=empty_spaces, assignments=assignments, calibration=position_calibration)
    compliance_score = _build_compliance_score(
        snapshot_available=isinstance(snapshot, dict), positions_available=positions_available,
        slot_results=slot_results, assignments=assignments, issues=issues,
        excluded_product_count=len(excluded_positions),
    )
    return {"schema_version": AUDIT_SCHEMA_VERSION, "audit_version": AUDIT_VERSION,
            "output_id": output_id, "job_id": job_id, "source_filename": source_filename,
            "audit_snapshot_sha256": snapshot_sha256, "status": status,
            "summary": summary, "assignments": assignments, "slot_results": slot_results,
            "layout_comparison": layout_comparison,
            "compliance_score": compliance_score,
            "excluded_low_confidence_products": len(excluded_positions),
            "product_confidence_threshold": 0.60,
            "label_audit": label_audit,
            "issues": issues, "created_at": now.isoformat()}
