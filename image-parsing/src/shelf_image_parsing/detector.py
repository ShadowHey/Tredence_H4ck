"""Product and empty shelf-space detection component using YOLO11."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from .geometry import calculate_box_area, clip_box, normalize_box
from .detection_refinement import suppress_nested_duplicates
from .schemas import DetectionItem


class ProductEmptySpaceDetector:
    """Detects products and empty shelf spaces using trained YOLO object detection weights."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        confidence: float = 0.25,
        iou: float = 0.45,
        device: str = "cpu",
        class_mapping: Optional[Dict[int, str]] = None,
        product_confidence_threshold: float = 0.60,
        model: Optional[Any] = None,
    ):
        if not 0.0 <= product_confidence_threshold <= 1.0:
            raise ValueError("product_confidence_threshold must be between 0 and 1")
        self.confidence = confidence
        self.product_confidence_threshold = product_confidence_threshold
        self.excluded_products: List[DetectionItem] = []
        self.iou = iou
        self.device = device
        self.class_mapping = class_mapping or {0: "empty_space", 1: "product"}
        self.model_path = model_path
        self.model = model

        if self.model is None and model_path:
            resolved_path = Path(model_path).resolve()
            if not resolved_path.is_file():
                raise FileNotFoundError(
                    f"Product/Empty-space detection weights not found at: {model_path}. "
                    "Please review MODEL_SETUP.md for instructions on obtaining the weights."
                )
            try:
                from ultralytics import YOLO
                self.model = YOLO(str(resolved_path))
            except Exception as e:
                raise RuntimeError(f"Failed to load YOLO detection model from {model_path}: {e}")

    def detect(self, image: np.ndarray) -> Tuple[List[DetectionItem], List[DetectionItem]]:
        """Run product and empty space inference on an image.

        Args:
            image: BGR numpy image (H, W, 3).

        Returns:
            Tuple of (products: List[DetectionItem], empty_regions: List[DetectionItem]).
        """
        if self.model is None:
            raise RuntimeError("Detection model is not initialized.")

        h, w = image.shape[:2]
        if h == 0 or w == 0:
            self.excluded_products = []
            return [], []

        self.excluded_products = []

        # Run inference
        results = self.model(
            image,
            conf=self.confidence,
            iou=self.iou,
            device=self.device,
            verbose=False,
        )

        if not results:
            return [], []

        res = results[0]
        boxes = res.boxes
        if boxes is None or len(boxes) == 0:
            return [], []

        products: List[DetectionItem] = []
        empty_regions: List[DetectionItem] = []

        for box in boxes:
            cls_id = int(box.cls[0].item())
            conf = float(box.conf[0].item())
            xyxy_raw = box.xyxy[0].cpu().numpy().tolist()

            clipped_xyxy = clip_box(xyxy_raw, w, h)
            norm_xyxy = normalize_box(clipped_xyxy, w, h)
            area = int(round(calculate_box_area(clipped_xyxy)))

            if area <= 0:
                continue

            class_name = self.class_mapping.get(cls_id, f"class_{cls_id}")

            item = DetectionItem(
                class_name=class_name,
                class_id=cls_id,
                confidence=round(conf, 4),
                bbox_xyxy=clipped_xyxy,
                bbox_normalized=norm_xyxy,
                area_px=area,
            )

            if cls_id == 0 or "empty" in class_name.lower():
                empty_regions.append(item)
            elif conf < self.product_confidence_threshold:
                # Keep geometry/confidence in a diagnostics-only collection so
                # compliance can avoid false absence claims at uncertain facings.
                self.excluded_products.append(item)
            else:
                products.append(item)

        # YOLO performs its configured IoU NMS. This additional class-aware pass is
        # deliberately stricter: it removes only near-contained duplicates, never
        # merging or expanding neighboring product detections.
        products = suppress_nested_duplicates(products)
        empty_regions = suppress_nested_duplicates(empty_regions)

        # Sort products left-to-right, top-to-bottom
        products.sort(key=lambda p: (p.bbox_xyxy[1], p.bbox_xyxy[0]))
        empty_regions.sort(key=lambda e: (e.bbox_xyxy[1], e.bbox_xyxy[0]))

        return products, empty_regions
