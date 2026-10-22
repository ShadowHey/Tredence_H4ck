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
    assert slot["status"] == "empty_space"
    assert slot["evidence"]["empty_space_cutout_ids"] == ["void-a2"]
    assert [issue["type"] for issue in result["issues"]].count("empty_space") == 1


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
    assert result["audit_version"] == 8
    layout = result["layout_comparison"]
    assert layout["coordinate_system"] == "normalized_shelf_width"
    assert layout["rows"][0]["expected_facings"][0]["ordinal_from_left"] == 1
    assert layout["rows"][0]["expected_facings"][1]["ordinal_from_right"] == 1
    assert (result["output_id"], result["job_id"], result["audit_snapshot_sha256"]) == (3, 7, "frozen-sha")


def _facing_slots(count, *, placement_id=17, row=0, product_id=10, sku="A"):
    return [{"slot_id": f"a-{index + 1}", "placement_id": placement_id,
             "product_id": product_id, "sku": sku, "row_index": row,
             "x_start_cm": index * 10, "x_end_cm": (index + 1) * 10}
            for index in range(count)]


def _present_products(count, *, product_id=10, sku="A"):
    return [product(f"p-{index + 1}", product_id, sku, index * 10, (index + 1) * 10)
            for index in range(count)]


def test_single_empty_facing_in_fifteen_does_not_raise_stock_alert():
    slots = _facing_slots(15)
    result = audit(_present_products(14), slots=slots)

    assert len([issue for issue in result["issues"] if issue["type"] in {"missing_product", "insufficient_quantity"}]) == 0
    assert sum(slot["status"] == "insufficient_quantity" for slot in result["slot_results"]) == 1


def test_low_stock_alert_is_emitted_at_half_occupancy_with_placement_level_evidence():
    slots = _facing_slots(10)
    result = audit(_present_products(5), slots=slots)

    alerts = [issue for issue in result["issues"] if issue["type"] == "insufficient_quantity"]
    assert len(alerts) == 1
    assert alerts[0]["expected_quantity"] == 10
    assert alerts[0]["observed_quantity"] == 5
    assert alerts[0]["occupancy_ratio"] == 0.5
    assert result["summary"]["insufficient_quantity"] == 1


def test_seven_of_fifteen_emits_one_low_stock_issue_with_exact_quantity():
    result = audit(_present_products(7), slots=_facing_slots(15))

    alerts = [issue for issue in result["issues"] if issue["type"] == "insufficient_quantity"]
    assert len(alerts) == 1
    assert (alerts[0]["observed_quantity"], alerts[0]["expected_quantity"]) == (7, 15)
    assert alerts[0]["occupancy_ratio"] == round(7 / 15, 4)


def test_isolated_empty_facing_retains_void_evidence_without_low_stock_alert():
    slots = _facing_slots(15)
    result = audit(_present_products(14),
                   [{"id": "isolated-void", "planogram_position": position(0, 140, 150)}],
                   slots=slots)

    assert not any(issue["type"] in {"missing_product", "insufficient_quantity"} for issue in result["issues"])
    vacant = next(slot for slot in result["slot_results"] if slot["slot_id"] == "a-15")
    assert vacant["status"] == "empty_space"
    assert vacant["evidence"]["empty_space_cutout_ids"] == ["isolated-void"]


def test_same_row_expected_sku_surplus_is_not_a_placement_violation():
    slots = _facing_slots(15)

    for observed_count in (13, 15, 17):
        result = audit(_present_products(observed_count), slots=slots)
        assert result["issues"] == []
        assert result["summary"]["count_variation_tolerated"] == max(0, observed_count - 15)

    beyond_tolerance = audit(_present_products(20), slots=slots)
    assert beyond_tolerance["issues"] == []
    assert beyond_tolerance["summary"]["count_variation_tolerated"] == 5


def test_reviewed_four_row_shelf_surfaces_only_lays_misplacement_and_empty_lays_facing():
    sku_by_row = {0: (17, "BEV-200"), 1: (16, "BEV-201"),
                  2: (15, "BEV-202"), 3: (14, "BEV-203")}
    slots = []
    for row, (product_id, sku) in sku_by_row.items():
        row_slots = _facing_slots(15, placement_id=195 + row, row=row,
                                  product_id=product_id, sku=sku)
        for slot in row_slots:
            slot["slot_id"] = f"row-{row + 1}-{slot['slot_id']}"
        slots.extend(row_slots)

    products = []
    for index in range(18):
        is_lays = index == 10
        products.append(product(
            f"row-1-{index + 1}", 16 if is_lays else 17,
            "BEV-201" if is_lays else "BEV-200", index * 6.5, index * 6.5 + 6,
            row=0, match_status="matched" if is_lays else "needs_review",
        ))
    for row, (product_id, sku) in sku_by_row.items():
        if row == 0:
            continue
        count = {1: 14, 2: 20, 3: 14}[row]
        positions = [index for index in range(15) if not (row == 1 and index == 8)]
        for index in range(count):
            x = (positions[index] * 10) if row == 1 else index * (120 / count)
            products.append(product(f"row-{row + 1}-{index + 1}", product_id, sku,
                                    x, x + 6, row=row))

    result = build_compliance_audit(
        output_id=8, job_id=9, source_filename="bc_image1.png", snapshot=fixture_snapshot(slots),
        snapshot_sha256="reviewed-four-row-shelf", products=products,
        empty_spaces=[{"id": "void-row-2", "planogram_position": position(1, 80, 88)}],
        position_calibration={"status": "calibrated"},
        label_audit={"status": "unavailable", "issues":[
            {"type": "needs_review", "reason": "ocr_engine_unavailable", "row_index": row}
            for row in range(60)
        ]},
    )

    assert [issue["type"] for issue in result["issues"]] == ["misplaced_product", "empty_space"], [
        (slot["slot_id"], slot["status"], slot["evidence"]) for slot in result["slot_results"]
        if slot["row_index"] == 1
    ]
    misplaced, empty = result["issues"]
    assert (misplaced["sku"], misplaced["expected_sku"], misplaced["row_index"], misplaced["target_row_number"]) == (
        "BEV-201", "BEV-200", 0, 2)
    assert empty["sku"] == "BEV-201" and empty["row_index"] == 1
    assert result["summary"]["needs_review"] == 0
    assert result["summary"]["label_issue_count"] == 0


def test_neighboring_same_sku_facings_remain_individually_compliant():
    slots = _facing_slots(15)
    result = audit(_present_products(15), slots=slots)

    assert len(result["assignments"]) == 15
    assert all(item["status"] == "correct" for item in result["assignments"])
    assert len({item["slot_id"] for item in result["assignments"]}) == 15
    assert result["issues"] == []


def test_fully_missing_placement_emits_one_missing_issue_not_one_per_facing():
    result = audit([], slots=_facing_slots(4))

    missing = [issue for issue in result["issues"] if issue["type"] == "missing_product"]
    assert len(missing) == 1
    assert missing[0]["expected_quantity"] == 4
    assert missing[0]["observed_quantity"] == 0
    assert result["summary"]["missing_product"] == 1


def test_low_stock_counts_correctly_placed_facings_within_its_placement_only():
    slots = _facing_slots(4, placement_id=17) + _facing_slots(4, placement_id=18, row=1, product_id=10)
    products = _present_products(3) + [product(f"q-{index + 1}", 10, "A", index * 10, (index + 1) * 10, row=1)
                                       for index in range(3)]
    result = audit(products, slots=slots)

    alerts = [issue for issue in result["issues"] if issue["type"] == "insufficient_quantity"]
    assert len(alerts) == 0
