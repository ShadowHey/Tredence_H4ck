from app.services.spatial_matching import build_layout_comparison


def calibrated(row, start, end):
    return {"status": "calibrated", "row_index": row, "x_start_cm": start, "x_end_cm": end}


def test_layout_uses_normalized_positions_ordinals_and_open_intervals():
    snapshot = {"width_cm": 100, "expected_facing_slots": [
        {"slot_id": "a", "row_index": 0, "x_start_cm": 0, "x_end_cm": 20, "sku": "A"},
        {"slot_id": "b", "row_index": 0, "x_start_cm": 40, "x_end_cm": 60, "sku": "B"},
    ]}
    products = [
        {"id": "p1", "planogram_position": calibrated(0, 0, 18)},
        {"id": "p2", "planogram_position": calibrated(0, 40, 60)},
    ]
    result = build_layout_comparison(snapshot=snapshot, products=products,
        empty_spaces=[{"id": "void", "planogram_position": calibrated(0, 20, 40)}],
        assignments=[{"slot_id": "a", "status": "correct"}], calibration={"status": "calibrated"})
    row = result["rows"][0]
    assert result["comparison_status"] == "ready"
    assert row["expected_facings"][1]["normalized_center"] == 0.5
    assert row["observed_products"][1]["ordinal_from_right"] == 1
    assert row["observed_empty_regions"][0]["cutout_id"] == "void"
    assert [entry["status"] for entry in row["sequence_alignment"]] == ["paired", "paired"]
    assert row["expected_free_intervals"] == [
        {"normalized_start": 0.2, "normalized_end": 0.4},
        {"normalized_start": 0.6, "normalized_end": 1.0},
    ]


def test_uncalibrated_layout_is_review_only_and_does_not_invent_actual_rows():
    result = build_layout_comparison(snapshot={"width_cm": 100, "expected_facing_slots": [
        {"slot_id": "a", "row_index": 0, "x_start_cm": 0, "x_end_cm": 20},
    ]}, products=[{"id": "p1", "planogram_position": None}], empty_spaces=[],
        assignments=[], calibration={"status": "needs_review"})
    assert result["comparison_status"] == "needs_review"
    assert result["rows"][0]["alignment_status"] == "needs_review"
    assert result["rows"][0]["observed_products"] == []


def test_sequence_alignment_keeps_missing_expected_slot_as_explicit_gap():
    snapshot = {"width_cm": 100, "expected_facing_slots": [
        {"slot_id": "a", "row_index": 0, "x_start_cm": 0, "x_end_cm": 20},
        {"slot_id": "b", "row_index": 0, "x_start_cm": 40, "x_end_cm": 60},
        {"slot_id": "c", "row_index": 0, "x_start_cm": 80, "x_end_cm": 100},
    ]}
    products = [{"id": "p-a", "planogram_position": calibrated(0, 0, 20)},
                {"id": "p-c", "planogram_position": calibrated(0, 80, 100)}]
    result = build_layout_comparison(snapshot=snapshot, products=products, empty_spaces=[], assignments=[],
                                     calibration={"status": "calibrated"})
    alignment = result["rows"][0]["sequence_alignment"]
    assert [(item["status"], item.get("slot_id"), item.get("cutout_id")) for item in alignment] == [
        ("paired", "a", "p-a"), ("missing_expected", "b", None), ("paired", "c", "p-c")]
