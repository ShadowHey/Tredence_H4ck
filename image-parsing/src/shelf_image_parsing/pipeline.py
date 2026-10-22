"""Pipeline orchestrator for ShelfSense AI image parsing."""

import csv
import json
from pathlib import Path
from typing import List, Optional, Union
import cv2
import numpy as np

from .config import PipelineConfig, load_config
from .calibration import detect_shelf_corner_markers
from .detector import ProductEmptySpaceDetector
from .empty_space import EmptySpaceRefiner
from .row_segmenter import ShelfRowSegmenter
from .schemas import ImageParsingResult, ImageParsingSummary
from .visualization import ShelfVisualizer

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


class ShelfImageParsingPipeline:
    """End-to-end processing pipeline for retail shelf photographs."""

    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        detector: Optional[ProductEmptySpaceDetector] = None,
        row_segmenter: Optional[ShelfRowSegmenter] = None,
        empty_refiner: Optional[EmptySpaceRefiner] = None,
        visualizer: Optional[ShelfVisualizer] = None,
    ):
        self.config = config or load_config()

        # Component injection allows full mockability in integration tests
        self.detector = detector or ProductEmptySpaceDetector(
            model_path=self.config.detection_model.path,
            confidence=self.config.detection_model.confidence,
            iou=self.config.detection_model.iou,
            device=self.config.device,
            class_mapping=self.config.detection_model.class_mapping,
        )
        self.row_segmenter = row_segmenter or ShelfRowSegmenter(
            model_path=self.config.segmentation_model.path,
            confidence=self.config.segmentation_model.confidence,
            iou=self.config.segmentation_model.iou,
            device=self.config.device,
            row_filter_width_ratio=self.config.row_filter_width_ratio,
        )
        self.empty_refiner = empty_refiner or EmptySpaceRefiner(
            nms_iou_threshold=self.config.empty_nms_threshold,
            assignment_mode=self.config.empty_assignment_mode,
        )
        self.visualizer = visualizer or ShelfVisualizer(config=self.config)

    def process_image(
        self,
        image_input: Union[str, Path, np.ndarray],
        output_dir: Optional[Union[str, Path]] = None,
        save_annotated: Optional[bool] = None,
        save_json: Optional[bool] = None,
        source_name: Optional[str] = None,
    ) -> ImageParsingResult:
        """Process an individual photograph through all stages."""
        out_dir = Path(output_dir or self.config.default_output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        do_save_img = save_annotated if save_annotated is not None else self.config.save_annotated_image
        do_save_json = save_json if save_json is not None else self.config.save_json

        # ----------------------------------------------------
        # Stage 1: Load and validate image
        # ----------------------------------------------------
        original_image: Optional[np.ndarray] = None
        input_filename = source_name or "in_memory_image.jpg"

        if isinstance(image_input, (str, Path)):
            img_path = Path(image_input)
            input_filename = img_path.name
            if not img_path.is_file():
                return ImageParsingResult(
                    source_image=input_filename,
                    image_width=0,
                    image_height=0,
                    model_status="failed",
                    summary=ImageParsingSummary(),
                    errors=[f"Image file does not exist: {img_path}"],
                )

            if img_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
                return ImageParsingResult(
                    source_image=input_filename,
                    image_width=0,
                    image_height=0,
                    model_status="failed",
                    summary=ImageParsingSummary(),
                    errors=[f"Unsupported image extension '{img_path.suffix}'. Supported: {SUPPORTED_IMAGE_EXTENSIONS}"],
                )

            original_image = cv2.imread(str(img_path))
            if original_image is None:
                return ImageParsingResult(
                    source_image=input_filename,
                    image_width=0,
                    image_height=0,
                    model_status="failed",
                    summary=ImageParsingSummary(),
                    errors=[f"Corrupt or unreadable image file: {img_path}"],
                )
        elif isinstance(image_input, np.ndarray):
            original_image = image_input.copy()
        else:
            return ImageParsingResult(
                source_image=input_filename,
                image_width=0,
                image_height=0,
                model_status="failed",
                summary=ImageParsingSummary(),
                errors=["Invalid image input type. Expected file path or numpy ndarray."],
            )

        img_h, img_w = original_image.shape[:2]
        if img_h == 0 or img_w == 0:
            return ImageParsingResult(
                source_image=input_filename,
                image_width=img_w,
                image_height=img_h,
                model_status="failed",
                summary=ImageParsingSummary(),
                errors=["Image has zero width or height."],
            )

        # Calibration markers are optional. Their centres provide projective
        # anchors for a rectified usable-shelf coordinate frame.
        calibration = detect_shelf_corner_markers(original_image)

        # ----------------------------------------------------
        # Stage 2: Detect products and empty spaces
        # ----------------------------------------------------
        products, empty_regions = self.detector.detect(original_image)

        # ----------------------------------------------------
        # Stage 3: Detect shelf rows
        # ----------------------------------------------------
        shelf_rows = self.row_segmenter.segment(original_image)

        # ----------------------------------------------------
        # Stage 4: Refine empty spaces & assign to rows
        # ----------------------------------------------------
        refined_empty = self.empty_refiner.deduplicate(empty_regions)
        refined_empty = self.empty_refiner.filter_regions_outside_shelf(
            refined_empty, shelf_rows, img_h, products=products
        )

        assigned_products = self.empty_refiner.assign_to_rows(products, shelf_rows, img_h)
        assigned_empty = self.empty_refiner.assign_to_rows(refined_empty, shelf_rows, img_h)

        # ----------------------------------------------------
        # Stage 5: Generate statistics
        # ----------------------------------------------------
        summary, updated_rows = self.empty_refiner.compute_metrics(assigned_products, assigned_empty, shelf_rows)

        stem = Path(input_filename).stem
        annotated_filename: Optional[str] = None

        # ----------------------------------------------------
        # Stage 6: Annotate and export
        # ----------------------------------------------------
        if do_save_img:
            annotated_filename = f"{stem}_annotated.jpg"
            annotated_path = out_dir / annotated_filename
            annotated_img = self.visualizer.annotate(
                original_image=original_image,
                products=assigned_products,
                empty_regions=assigned_empty,
                shelf_rows=updated_rows,
                summary=summary,
                source_name=input_filename,
            )
            cv2.imwrite(str(annotated_path), annotated_img)

        result = ImageParsingResult(
            source_image=input_filename,
            image_width=img_w,
            image_height=img_h,
            model_status="completed" if (assigned_products or updated_rows) else "no_detections",
            summary=summary,
            products=assigned_products,
            empty_regions=assigned_empty,
            shelf_rows=updated_rows,
            calibration=calibration,
            annotated_image=annotated_filename,
        )

        if do_save_json:
            json_filename = f"{stem}_detections.json"
            json_path = out_dir / json_filename
            with open(json_path, "w", encoding="utf-8") as f:
                f.write(result.model_dump_json(indent=2))

        return result

    def process_batch(
        self,
        input_path: Union[str, Path],
        output_dir: Optional[Union[str, Path]] = None,
        save_csv: Optional[bool] = None,
    ) -> List[ImageParsingResult]:
        """Process single image or entire directory of images independently."""
        in_p = Path(input_path)
        out_dir = Path(output_dir or self.config.default_output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        do_save_csv = save_csv if save_csv is not None else self.config.save_csv

        results: List[ImageParsingResult] = []

        if in_p.is_file():
            res = self.process_image(in_p, output_dir=out_dir)
            results.append(res)
        elif in_p.is_dir():
            image_files = sorted([
                f for f in in_p.iterdir()
                if f.is_file() and f.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
            ])
            for img_file in image_files:
                try:
                    res = self.process_image(img_file, output_dir=out_dir)
                    results.append(res)
                except Exception as err:
                    # Isolated error: do not abort remaining images
                    failed_res = ImageParsingResult(
                        source_image=img_file.name,
                        image_width=0,
                        image_height=0,
                        model_status="failed",
                        summary=ImageParsingSummary(),
                        errors=[str(err)],
                    )
                    results.append(failed_res)
        else:
            raise FileNotFoundError(f"Input path neither file nor directory: {input_path}")

        if do_save_csv and results:
            self._write_csv_summary(results, out_dir / "shelf_summary.csv")

        return results

    def _write_csv_summary(self, results: List[ImageParsingResult], csv_path: Path) -> None:
        """Write tabular row-level and image-level measurements to CSV."""
        fieldnames = [
            "source_image",
            "model_status",
            "image_width",
            "image_height",
            "row_number",
            "row_product_count",
            "row_empty_count",
            "row_empty_percentage",
            "total_products",
            "total_empty_slots",
            "total_shelf_rows",
            "overall_empty_percentage",
            "annotated_image",
        ]

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for res in results:
                if not res.shelf_rows:
                    # Row-less summary entry
                    writer.writerow({
                        "source_image": res.source_image,
                        "model_status": res.model_status,
                        "image_width": res.image_width,
                        "image_height": res.image_height,
                        "row_number": "N/A",
                        "row_product_count": 0,
                        "row_empty_count": 0,
                        "row_empty_percentage": "N/A",
                        "total_products": res.summary.product_count,
                        "total_empty_slots": res.summary.empty_region_count,
                        "total_shelf_rows": res.summary.shelf_row_count,
                        "overall_empty_percentage": res.summary.empty_area_percentage or "N/A",
                        "annotated_image": res.annotated_image or "",
                    })
                else:
                    for row in res.shelf_rows:
                        writer.writerow({
                            "source_image": res.source_image,
                            "model_status": res.model_status,
                            "image_width": res.image_width,
                            "image_height": res.image_height,
                            "row_number": row.row_number,
                            "row_product_count": row.product_count,
                            "row_empty_count": row.empty_region_count,
                            "row_empty_percentage": row.row_empty_percentage if row.row_empty_percentage is not None else "N/A",
                            "total_products": res.summary.product_count,
                            "total_empty_slots": res.summary.empty_region_count,
                            "total_shelf_rows": res.summary.shelf_row_count,
                            "overall_empty_percentage": res.summary.empty_area_percentage or "N/A",
                            "annotated_image": res.annotated_image or "",
                        })
