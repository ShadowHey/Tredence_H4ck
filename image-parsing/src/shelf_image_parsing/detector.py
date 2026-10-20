"""Product and empty shelf-space detection component using YOLO11."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from .geometry import calculate_box_area, clip_box, normalize_box
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
        model: Optional[Any] = None,
    ):
        self.confidence = confidence
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
            return [], []

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
            else:
                products.append(item)

        # Sort products left-to-right, top-to-bottom
        products.sort(key=lambda p: (p.bbox_xyxy[1], p.bbox_xyxy[0]))
        empty_regions.sort(key=lambda e: (e.bbox_xyxy[1], e.bbox_xyxy[0]))

        return products, empty_regions
