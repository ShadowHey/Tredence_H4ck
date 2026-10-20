"""Unit tests for visualization and annotation rendering."""

import numpy as np
import cv2
import pytest
from shelf_image_parsing.visualization import ShelfVisualizer
from shelf_image_parsing.schemas import DetectionItem, ImageParsingSummary, ShelfRowItem


class TestVisualization:
    def test_output_dimensions_strictly_preserved(self):
        h, w = 600, 800
        blank_image = np.full((h, w, 3), 180, dtype=np.uint8)

        visualizer = ShelfVisualizer()

        product = DetectionItem(
            class_name="product", class_id=1, confidence=0.92,
            bbox_xyxy=[50, 100, 150, 300], bbox_normalized=[0.0625, 0.166, 0.1875, 0.5],
            row_number=1,
        )
        empty = DetectionItem(
            class_name="empty_space", class_id=0, confidence=0.85,
            bbox_xyxy=[200, 100, 300, 300], bbox_normalized=[0.25, 0.166, 0.375, 0.5],
            row_number=1,
        )
        row = ShelfRowItem(
            row_number=1, bbox_xyxy=[20, 80, 780, 320], bbox_normalized=[0.025, 0.133, 0.975, 0.533],
        )

        annotated = visualizer.annotate(
            original_image=blank_image,
            products=[product],
            empty_regions=[empty],
            shelf_rows=[row],
            summary=ImageParsingSummary(product_count=1, empty_region_count=1, shelf_row_count=1),
        )

        assert annotated.shape == (h, w, 3)
        assert annotated.dtype == np.uint8

    def test_original_image_not_mutated(self):
        blank_image = np.full((100, 100, 3), 50, dtype=np.uint8)
        copy_before = blank_image.copy()

        visualizer = ShelfVisualizer()
        _ = visualizer.annotate(
            original_image=blank_image,
            products=[],
            empty_regions=[],
            shelf_rows=[],
        )

        # Original array must be completely unaltered
        np.testing.assert_array_equal(blank_image, copy_before)

    def test_color_tokens_and_rendering(self):
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        visualizer = ShelfVisualizer()

        product = DetectionItem(
            class_name="product", class_id=1, confidence=0.90,
            bbox_xyxy=[10, 10, 50, 50], bbox_normalized=[0.05, 0.05, 0.25, 0.25],
        )
        annotated = visualizer.annotate(
            original_image=img,
            products=[product],
            empty_regions=[],
            shelf_rows=[],
        )

        # Confirm some cyan pixels exist in the annotated image (B=255, G=229, R=0)
        # Check around the rectangle border
        bgr = visualizer.config.product_style.color_bgr
        assert bgr == [255, 229, 0]
        # At least one pixel should have high blue and green
        assert np.any((annotated[:, :, 0] == 255) & (annotated[:, :, 1] == 229))

    def test_reopenable_valid_image(self, tmp_path):
        img = np.full((400, 500, 3), 100, dtype=np.uint8)
        visualizer = ShelfVisualizer()

        annotated = visualizer.annotate(
            original_image=img,
            products=[],
            empty_regions=[],
            shelf_rows=[],
        )

        out_file = tmp_path / "test_annotated.jpg"
        cv2.imwrite(str(out_file), annotated)

        reopened = cv2.imread(str(out_file))
        assert reopened is not None
        assert reopened.shape == (400, 500, 3)
