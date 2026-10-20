"""Unit tests for row-assignment logic and ordering."""

import pytest
from shelf_image_parsing.empty_space import EmptySpaceRefiner
from shelf_image_parsing.schemas import DetectionItem, ShelfRowItem


class TestRowAssignment:
    def test_assign_to_multiple_rows_correctly(self):
        refiner = EmptySpaceRefiner()

        # 3 Shelf rows sorted top to bottom
        rows = [
            ShelfRowItem(row_number=1, bbox_xyxy=[0, 100, 1000, 300], bbox_normalized=[0, 0.1, 1, 0.3]),
            ShelfRowItem(row_number=2, bbox_xyxy=[0, 400, 1000, 600], bbox_normalized=[0, 0.4, 1, 0.6]),
            ShelfRowItem(row_number=3, bbox_xyxy=[0, 700, 1000, 900], bbox_normalized=[0, 0.7, 1, 0.9]),
        ]

        # Item 1 in Row 1 (cy = 200)
        item1 = DetectionItem(
            class_name="product", class_id=1, confidence=0.9,
            bbox_xyxy=[100, 150, 200, 250], bbox_normalized=[0.1, 0.15, 0.2, 0.25],
        )
        # Item 2 in Row 2 (cy = 500)
        item2 = DetectionItem(
            class_name="empty_space", class_id=0, confidence=0.85,
            bbox_xyxy=[300, 450, 400, 550], bbox_normalized=[0.3, 0.45, 0.4, 0.55],
        )
        # Item 3 in Row 3 (cy = 800)
        item3 = DetectionItem(
            class_name="product", class_id=1, confidence=0.95,
            bbox_xyxy=[500, 750, 600, 850], bbox_normalized=[0.5, 0.75, 0.6, 0.85],
        )

        assigned = refiner.assign_to_rows([item1, item2, item3], rows, image_height=1000)

        assert assigned[0].row_number == 1
        assert assigned[1].row_number == 2
        assert assigned[2].row_number == 3

    def test_assign_with_no_rows(self):
        refiner = EmptySpaceRefiner()
        item = DetectionItem(
            class_name="product", class_id=1, confidence=0.9,
            bbox_xyxy=[100, 100, 200, 200], bbox_normalized=[0.1, 0.1, 0.2, 0.2],
        )
        assigned = refiner.assign_to_rows([item], [], image_height=1000)
        assert len(assigned) == 1
        assert assigned[0].row_number is None

    def test_assign_with_single_row(self):
        refiner = EmptySpaceRefiner()
        row = ShelfRowItem(row_number=1, bbox_xyxy=[0, 200, 1000, 500], bbox_normalized=[0, 0.2, 1, 0.5])

        item = DetectionItem(
            class_name="empty_space", class_id=0, confidence=0.8,
            bbox_xyxy=[100, 300, 200, 400], bbox_normalized=[0.1, 0.3, 0.2, 0.4],
        )
        assigned = refiner.assign_to_rows([item], [row], image_height=1000)
        assert assigned[0].row_number == 1

    def test_assign_near_image_boundaries(self):
        refiner = EmptySpaceRefiner()
        rows = [
            ShelfRowItem(row_number=1, bbox_xyxy=[0, 100, 1000, 300], bbox_normalized=[0, 0.1, 1, 0.3]),
            ShelfRowItem(row_number=2, bbox_xyxy=[0, 700, 1000, 900], bbox_normalized=[0, 0.7, 1, 0.9]),
        ]

        top_item = DetectionItem(
            class_name="product", class_id=1, confidence=0.8,
            bbox_xyxy=[10, 0, 50, 30], bbox_normalized=[0.01, 0.0, 0.05, 0.03],
        )
        bottom_item = DetectionItem(
            class_name="product", class_id=1, confidence=0.8,
            bbox_xyxy=[10, 970, 50, 1000], bbox_normalized=[0.01, 0.97, 0.05, 1.0],
        )

        assigned = refiner.assign_to_rows([top_item, bottom_item], rows, image_height=1000)
        assert assigned[0].row_number == 1
        assert assigned[1].row_number == 2
