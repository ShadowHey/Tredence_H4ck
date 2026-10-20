"""Unit tests for spatial geometry and box math."""

import pytest
from shelf_image_parsing.geometry import (
    apply_nms,
    calculate_box_area,
    calculate_iou,
    clip_box,
    denormalize_box,
    get_box_center,
    normalize_box,
    polygon_to_bbox,
)


class TestGeometry:
    def test_calculate_box_area_valid(self):
        box = [10, 20, 110, 120]  # width=100, height=100
        assert calculate_box_area(box) == 10000.0

    def test_calculate_box_area_zero_and_inverted(self):
        # zero width
        assert calculate_box_area([50, 50, 50, 100]) == 0.0
        # inverted box (x2 < x1)
        assert calculate_box_area([100, 50, 20, 100]) == 0.0
        # inverted y (y2 < y1)
        assert calculate_box_area([10, 100, 50, 20]) == 0.0

    def test_clip_box_within_bounds(self):
        clipped = clip_box([10, 10, 90, 90], width=100, height=100)
        assert clipped == [10, 10, 90, 90]

    def test_clip_box_out_of_bounds(self):
        # Negative and oversized
        clipped = clip_box([-20, -10, 150, 120], width=100, height=80)
        assert clipped == [0, 0, 100, 80]

    def test_clip_box_inverts_if_needed(self):
        clipped = clip_box([80, 70, 20, 30], width=100, height=100)
        assert clipped == [20, 30, 80, 70]

    def test_normalize_and_denormalize_roundtrip(self):
        box = [100, 200, 300, 600]
        w, h = 1000, 1000

        norm = normalize_box(box, w, h)
        assert norm == [0.1, 0.2, 0.3, 0.6]

        restored = denormalize_box(norm, w, h)
        assert restored == box

    def test_calculate_iou_identical_boxes(self):
        box = [0, 0, 100, 100]
        assert calculate_iou(box, box) == 1.0

    def test_calculate_iou_disjoint_boxes(self):
        box1 = [0, 0, 50, 50]
        box2 = [60, 60, 100, 100]
        assert calculate_iou(box1, box2) == 0.0

    def test_calculate_iou_partial_overlap(self):
        # box1: [0, 0, 10, 10] -> area=100
        # box2: [5, 0, 15, 10] -> area=100
        # intersection: [5, 0, 10, 10] -> area=50
        # union: 100 + 100 - 50 = 150
        # iou = 50 / 150 = 1/3
        box1 = [0, 0, 10, 10]
        box2 = [5, 0, 15, 10]
        assert pytest.approx(calculate_iou(box1, box2), 0.001) == 0.3333

    def test_calculate_iou_zero_area_boxes(self):
        box1 = [10, 10, 10, 10]
        box2 = [20, 20, 30, 30]
        assert calculate_iou(box1, box2) == 0.0

    def test_get_box_center(self):
        box = [10, 20, 30, 40]
        cx, cy = get_box_center(box)
        assert cx == 20
        assert cy == 30

    def test_polygon_to_bbox(self):
        poly = [[10, 30], [50, 20], [80, 90], [20, 85]]
        bbox = polygon_to_bbox(poly)
        assert bbox == [10, 20, 80, 90]

    def test_polygon_to_bbox_empty(self):
        assert polygon_to_bbox([]) == [0, 0, 0, 0]

    def test_apply_nms_suppression(self):
        boxes = [
            [10, 10, 50, 50],
            [12, 12, 48, 48],  # heavy overlap with box 0
            [100, 100, 150, 150],  # independent
        ]
        scores = [0.95, 0.80, 0.90]
        keep = apply_nms(boxes, scores, iou_threshold=0.5)
        assert keep == [0, 2]  # box 1 suppressed
