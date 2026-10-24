"""Integration tests for the full ShelfSense AI image parsing pipeline using mocked models."""

from pathlib import Path
import cv2
import numpy as np
import pytest

from shelf_image_parsing.config import PipelineConfig
from shelf_image_parsing.detector import ProductEmptySpaceDetector
from shelf_image_parsing.empty_space import EmptySpaceRefiner
from shelf_image_parsing.pipeline import ShelfImageParsingPipeline
from shelf_image_parsing.row_segmenter import ShelfRowSegmenter
from shelf_image_parsing.schemas import DetectionItem, ImageParsingResult, ShelfRowItem
from shelf_image_parsing.visualization import ShelfVisualizer


class MockDetector:
    """Mock object detector returning predetermined product and empty-space boxes."""

    def __init__(self, products=None, empty_spaces=None):
        self.products = products or []
        self.empty_spaces = empty_spaces or []
        self.excluded_products = []

    def detect(self, image: np.ndarray):
        return list(self.products), list(self.empty_spaces)


class MockSegmenter:
    """Mock row segmenter returning predetermined shelf rows."""

    def __init__(self, rows=None):
        self.rows = rows or []

    def segment(self, image: np.ndarray):
        return list(self.rows)


class TestPipelineIntegration:
    @pytest.fixture
    def synthetic_shelf_image(self, tmp_path):
        """Generate a synthetic 800x600 test photograph with distinct shelf bands."""
        img = np.full((600, 800, 3), 220, dtype=np.uint8)
        # Draw 3 dark shelf slats
        cv2.rectangle(img, (50, 180), (750, 200), (80, 80, 80), -1)
        cv2.rectangle(img, (50, 380), (750, 400), (80, 80, 80), -1)
        cv2.rectangle(img, (50, 560), (750, 580), (80, 80, 80), -1)

        img_path = tmp_path / "synthetic_shelf.jpg"
        cv2.imwrite(str(img_path), img)
        return img_path

    def test_full_pipeline_mock_execution(self, synthetic_shelf_image, tmp_path):
        output_dir = tmp_path / "outputs"

        mock_products = [
            DetectionItem(
                class_name="product", class_id=1, confidence=0.92,
                bbox_xyxy=[100, 80, 180, 180], bbox_normalized=[0.125, 0.133, 0.225, 0.3],
            ),
            DetectionItem(
                class_name="product", class_id=1, confidence=0.88,
                bbox_xyxy=[200, 80, 280, 180], bbox_normalized=[0.25, 0.133, 0.35, 0.3],
            ),
            DetectionItem(
                class_name="product", class_id=1, confidence=0.95,
                bbox_xyxy=[100, 260, 220, 380], bbox_normalized=[0.125, 0.433, 0.275, 0.633],
            ),
        ]
        mock_empty = [
            DetectionItem(
                class_name="empty_space", class_id=0, confidence=0.85,
                bbox_xyxy=[350, 80, 480, 180], bbox_normalized=[0.4375, 0.133, 0.6, 0.3],
            )
        ]
        mock_rows = [
            ShelfRowItem(row_number=1, bbox_xyxy=[50, 60, 750, 200], bbox_normalized=[0.0625, 0.1, 0.9375, 0.333]),
            ShelfRowItem(row_number=2, bbox_xyxy=[50, 240, 750, 400], bbox_normalized=[0.0625, 0.4, 0.9375, 0.666]),
        ]

        cfg = PipelineConfig(default_output_dir=str(output_dir))
        pipeline = ShelfImageParsingPipeline(
            config=cfg,
            detector=MockDetector(products=mock_products, empty_spaces=mock_empty),
            row_segmenter=MockSegmenter(rows=mock_rows),
        )

        result = pipeline.process_image(synthetic_shelf_image, output_dir=output_dir)

        # 1. Assert result schema
        assert isinstance(result, ImageParsingResult)
        assert result.model_status == "completed"
        assert result.image_width == 800
        assert result.image_height == 600
        assert result.summary.product_count == 3
        assert result.summary.excluded_product_count == 0
        assert result.summary.product_confidence_threshold == 0.60
        assert result.summary.empty_region_count == 1
        assert result.summary.shelf_row_count == 2
        assert result.summary.empty_area_percentage is not None
        assert result.summary.empty_area_percentage > 0

        # 2. Check exported JSON file
        json_file = output_dir / "synthetic_shelf_detections.json"
        assert json_file.is_file()
        import json
        with open(json_file, "r") as f:
            data = json.load(f)
        assert data["source_image"] == "synthetic_shelf.jpg"
        assert len(data["products"]) == 3
        assert len(data["empty_regions"]) == 1

        # 3. Check exported annotated image
        annotated_file = output_dir / "synthetic_shelf_annotated.jpg"
        assert annotated_file.is_file()
        reopened = cv2.imread(str(annotated_file))
        assert reopened is not None
        # Verify resolution preserved exactly
        assert reopened.shape == (600, 800, 3)

    def test_batch_execution_and_csv_generation(self, tmp_path):
        input_dir = tmp_path / "inputs"
        output_dir = tmp_path / "outputs"
        input_dir.mkdir()

        # Create two test images
        for name in ["shelf_a.jpg", "shelf_b.png"]:
            cv2.imwrite(str(input_dir / name), np.full((300, 400, 3), 150, dtype=np.uint8))

        # Also add an invalid dummy file to test error isolation
        (input_dir / "broken.jpg").write_text("not an image")

        mock_rows = [
            ShelfRowItem(row_number=1, bbox_xyxy=[10, 10, 390, 150], bbox_normalized=[0.025, 0.033, 0.975, 0.5])
        ]
        pipeline = ShelfImageParsingPipeline(
            detector=MockDetector(products=[], empty_spaces=[]),
            row_segmenter=MockSegmenter(rows=mock_rows),
        )

        results = pipeline.process_batch(input_path=input_dir, output_dir=output_dir, save_csv=True)

        # 3 inputs: 2 valid, 1 broken
        assert len(results) == 3
        statuses = {r.source_image: r.model_status for r in results}
        assert statuses["shelf_a.jpg"] in ("completed", "no_detections")
        assert statuses["shelf_b.png"] in ("completed", "no_detections")
        assert statuses["broken.jpg"] == "failed"

        # Check CSV generation
        csv_file = output_dir / "shelf_summary.csv"
        assert csv_file.is_file()
        content = csv_file.read_text()
        assert "source_image" in content
        assert "shelf_a.jpg" in content
        assert "broken.jpg" in content
