from app.services.compliance_service import build_compliance_audit


def position(row, start, end):
    return {"status": "calibrated", "row_index": row, "x_start_cm": start,
            "x_end_cm": end, "center_x_cm": (start + end) / 2,
            "position_tolerance_cm": 1.0}


def product(cutout_id, product_id, sku, start, end, *, row=0, match_status="matched"):
    return {"id": cutout_id, "planogram_position": position(row, start, end),
            "catalog_match": {"status": match_status, "reason": "fixture",
                              "top_candidate": {"id": product_id, "sku": sku} if product_id else None}}


def fixture_snapshot(slots=None):
    return {"expected_facing_slots": slots or [
        {"slot_id": "a-1", "placement_id": 1, "product_id": 10, "sku": "A",
         "row_index": 0, "x_start_cm": 0, "x_end_cm": 10},
        {"slot_id": "b-1", "placement_id": 2, "product_id": 20, "sku": "B",
         "row_index": 0, "x_start_cm": 10, "x_end_cm": 20},
    ]}


def audit(products, empties=None, *, slots=None, calibration="calibrated"):
    return build_compliance_audit(
        output_id=3, job_id=7, source_filename="shelf.jpg", snapshot=fixture_snapshot(slots),
        snapshot_sha256="frozen-sha", products=products, empty_spaces=empties or [],
        position_calibration={"status": calibration},
    )


def test_assigns_left_to_right_and_reports_correct_placements():
    result = audit([product("p-b", 20, "B", 10, 20), product("p-a", 10, "A", 0, 10)])
    assert [(item["cutout_id"], item["slot_id"], item["status"]) for item in result["assignments"]] == [
        ("p-a", "a-1", "correct"), ("p-b", "b-1", "correct")]
    assert result["summary"]["correct"] == 2
    assert result["issues"] == []


def test_swapped_products_are_misplaced_without_false_quantity_shortage():
    result = audit([product("p-b", 20, "B", 0, 10), product("p-a", 10, "A", 10, 20)])
    assert result["summary"]["misplaced_product"] == 2
    assert all(slot["status"] == "misplaced_product" for slot in result["slot_results"])
    assert not any(entry["type"] in {"missing_product", "insufficient_quantity"} for entry in result["issues"])


def test_missing_and_insufficient_facings_include_empty_space_evidence():
    slots = [
        {"slot_id": "a-1", "placement_id": 1, "product_id": 10, "sku": "A", "row_index": 0, "x_start_cm": 0, "x_end_cm": 10},
        {"slot_id": "a-2", "placement_id": 1, "product_id": 10, "sku": "A", "row_index": 0, "x_start_cm": 10, "x_end_cm": 20},
        {"slot_id": "b-1", "placement_id": 2, "product_id": 20, "sku": "B", "row_index": 0, "x_start_cm": 20, "x_end_cm": 30},
    ]
    result = audit([product("p-a", 10, "A", 0, 10), product("p-b", 20, "B", 20, 30)],
                   [{"id": "void-a2", "planogram_position": position(0, 10, 20)}], slots=slots)
    slot = next(item for item in result["slot_results"] if item["slot_id"] == "a-2")
    assert slot["status"] == "insufficient_quantity"
    assert slot["evidence"]["empty_space_cutout_ids"] == ["void-a2"]


def test_unexpected_unrecognised_and_ambiguous_detections_are_distinguished():
    result = audit([
        product("p-a", 10, "A", 0, 10),
        product("p-x", 99, "X", 10, 20),
        product("p-u", None, None, 0, 10, row=1, match_status="unmatched"),
        product("p-r", None, None, 0, 10, row=2, match_status="needs_review"),
    ])
    status_by_id = {item["cutout_id"]: item["status"] for item in result["assignments"]}
    assert status_by_id == {"p-a": "correct", "p-x": "unexpected_product",
                            "p-u": "unrecognised_product", "p-r": "needs_review"}


def test_uncalibrated_audit_does_not_assert_missing_products():
    result = audit([], calibration="needs_review")
    assert result["status"] == "needs_review"
    assert all(slot["status"] == "needs_review" for slot in result["slot_results"])
    assert not any(issue["type"] == "missing_product" for issue in result["issues"])


def test_audit_is_versioned_and_linked_to_output_snapshot():
    result = audit([product("p-a", 10, "A", 0, 10)])
    assert result["schema_version"] == 1
    assert result["audit_version"] == 4
    layout = result["layout_comparison"]
    assert layout["coordinate_system"] == "normalized_shelf_width"
    assert layout["rows"][0]["expected_facings"][0]["ordinal_from_left"] == 1
    assert layout["rows"][0]["expected_facings"][1]["ordinal_from_right"] == 1
    assert (result["output_id"], result["job_id"], result["audit_snapshot_sha256"]) == (3, 7, "frozen-sha")
