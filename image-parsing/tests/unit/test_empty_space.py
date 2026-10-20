"""Unit tests for empty-space refinement and area analytics."""

import pytest
from shelf_image_parsing.empty_space import EmptySpaceRefiner
from shelf_image_parsing.schemas import DetectionItem, ShelfRowItem


class TestEmptySpaceRefiner:
    def test_deduplicate_overlapping_boxes(self):
        refiner = EmptySpaceRefiner(nms_iou_threshold=0.5)

        box1 = DetectionItem(
            class_name="empty_space",
            class_id=0,
            confidence=0.92,
            bbox_xyxy=[100, 100, 200, 200],
            bbox_normalized=[0.1, 0.1, 0.2, 0.2],
        )
        box2 = DetectionItem(
            class_name="empty_space",
            class_id=0,
            confidence=0.75,
            bbox_xyxy=[105, 105, 195, 195],  # Near identical
            bbox_normalized=[0.105, 0.105, 0.195, 0.195],
        )
        box3 = DetectionItem(
            class_name="empty_space",
            class_id=0,
            confidence=0.88,
            bbox_xyxy=[400, 400, 500, 500],  # Far away
            bbox_normalized=[0.4, 0.4, 0.5, 0.5],
        )

        deduped = refiner.deduplicate([box1, box2, box3])
        assert len(deduped) == 2
        # Highest confidence box1 should be preserved, box2 pruned
        assert box1 in deduped
        assert box3 in deduped
        assert box2 not in deduped

    def test_filter_regions_outside_shelf(self):
        refiner = EmptySpaceRefiner(shelf_vertical_margin_px=30)

        # Shelf row between y=200 and y=600
        row = ShelfRowItem(
            row_number=1,
            bbox_xyxy=[50, 200, 950, 600],
            bbox_normalized=[0.05, 0.2, 0.95, 0.6],
        )

        inside_empty = DetectionItem(
            class_name="empty_space",
            class_id=0,
            confidence=0.85,
            bbox_xyxy=[100, 250, 200, 450],
            bbox_normalized=[0.1, 0.25, 0.2, 0.45],
        )
        ceiling_empty = DetectionItem(
            class_name="empty_space",
            class_id=0,
            confidence=0.80,
            bbox_xyxy=[100, 20, 200, 80],  # Far above shelf
            bbox_normalized=[0.1, 0.02, 0.2, 0.08],
        )
        floor_empty = DetectionItem(
            class_name="empty_space",
            class_id=0,
            confidence=0.80,
            bbox_xyxy=[100, 800, 200, 900],  # Far below shelf
            bbox_normalized=[0.1, 0.8, 0.2, 0.9],
        )

        filtered = refiner.filter_regions_outside_shelf([inside_empty, ceiling_empty, floor_empty], [row], 1000)
        assert len(filtered) == 1
        assert filtered[0] == inside_empty

    def test_compute_metrics_standard_formula(self):
        refiner = EmptySpaceRefiner()

        # Product area = 400 * 300 = 120,000 px
        product = DetectionItem(
            class_name="product",
            class_id=1,
            confidence=0.90,
            bbox_xyxy=[0, 0, 400, 300],
            bbox_normalized=[0.0, 0.0, 0.4, 0.3],
            row_number=1,
        )
        # Empty area = 100 * 300 = 30,000 px
        empty = DetectionItem(
            class_name="empty_space",
            class_id=0,
            confidence=0.85,
            bbox_xyxy=[400, 0, 500, 300],
            bbox_normalized=[0.4, 0.0, 0.5, 0.3],
            row_number=1,
        )
        row = ShelfRowItem(
            row_number=1,
            bbox_xyxy=[0, 0, 500, 300],
            bbox_normalized=[0.0, 0.0, 0.5, 0.3],
        )

        summary, updated_rows = refiner.compute_metrics([product], [empty], [row])

        # Combined = 120,000 + 30,000 = 150,000 px
        # Empty % = 30,000 / 150,000 * 100 = 20.0%
        # Product % = 120,000 / 150,000 * 100 = 80.0%
        assert summary.product_count == 1
        assert summary.empty_region_count == 1
        assert summary.shelf_row_count == 1
        assert summary.empty_area_percentage == 20.0
        assert summary.product_area_percentage == 80.0

        assert len(updated_rows) == 1
        assert updated_rows[0].product_count == 1
        assert updated_rows[0].empty_region_count == 1
        assert updated_rows[0].row_empty_percentage == 20.0

    def test_compute_metrics_no_detections(self):
        refiner = EmptySpaceRefiner()
        summary, updated_rows = refiner.compute_metrics([], [], [])

        assert summary.product_count == 0
        assert summary.empty_region_count == 0
        assert summary.empty_area_percentage is None
        assert summary.product_area_percentage is None
        assert updated_rows == []
