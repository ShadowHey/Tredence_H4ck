import pytest

from app.services.position_calibration import map_detections_to_planogram


SHELF = {
    "width_cm": 100.0,
    "row_count": 2,
    "resolved_row_heights_cm": [20.0, 20.0],
}


def test_straight_on_row_calibration_maps_to_zero_based_row_and_cm_span():
    detections = [{"id": "prod_0001", "bbox_xyxy": [100, 40, 300, 140], "row_number": 1}]
    rows = [
        {"row_number": 1, "bbox_xyxy": [0, 0, 1000, 200]},
        {"row_number": 2, "bbox_xyxy": [0, 200, 1000, 400]},
    ]

    mapped, calibration = map_detections_to_planogram(detections, rows, SHELF, 1000, 400)

    assert calibration["status"] == "calibrated"
    assert calibration["method"] == "detected_row_linear"
    position = mapped[0]["planogram_position"]
    assert position["row_index"] == 0  # CV's 1-indexed top row -> planogram's 0-indexed top row.
    assert position["x_start_cm"] == 10.0
    assert position["x_end_cm"] == 30.0
    assert position["position_tolerance_cm"] == 1.0


def test_four_corner_calibration_rectifies_perspective_for_position_mapping():
    detections = [{"id": "prod_0001", "bbox_xyxy": [300, 300, 500, 500]}]
    skewed_corners = [[100, 100], [900, 150], [850, 900], [150, 850]]

    mapped, calibration = map_detections_to_planogram(detections, [], SHELF, 1000, 1000, skewed_corners)

    assert calibration["method"] == "four_corner_homography"
    position = mapped[0]["planogram_position"]
    assert position["row_index"] == 0
    assert position["x_start_cm"] == pytest.approx(23.43, abs=0.02)
    assert position["x_end_cm"] == pytest.approx(50.23, abs=0.02)


def test_invalid_corner_order_falls_back_to_row_calibration():
    detections = [{"id": "prod_0001", "bbox_xyxy": [100, 40, 300, 140], "row_number": 1}]
    rows = [{"row_number": 1, "bbox_xyxy": [0, 0, 1000, 200]}]
    invalid_corners = [[100, 100], [900, 900], [900, 100], [100, 900]]

    mapped, calibration = map_detections_to_planogram(detections, rows, SHELF, 1000, 1000, invalid_corners)

    assert calibration["method"] == "detected_row_linear"
    assert mapped[0]["planogram_position"]["row_index"] == 0


def test_missing_calibration_keeps_cutout_but_marks_position_unavailable():
    detections = [{"id": "prod_0001", "bbox_xyxy": [10, 10, 20, 20]}]

    mapped, calibration = map_detections_to_planogram(detections, [], SHELF, 100, 100)

    assert calibration["status"] == "needs_review"
    assert calibration["method"] == "unavailable"
    assert mapped[0]["planogram_position"] is None


def test_incomplete_detected_row_set_is_explicitly_flagged():
    detections = [{"id": "prod_0001", "bbox_xyxy": [100, 40, 300, 140], "row_number": 1}]
    rows = [{"row_number": 1, "bbox_xyxy": [0, 0, 1000, 200]}]

    mapped, calibration = map_detections_to_planogram(detections, rows, SHELF, 1000, 400)

    assert calibration["status"] == "needs_review"
    assert calibration["row_count_match"] is False
    assert mapped[0]["planogram_position"]["row_index"] == 0
