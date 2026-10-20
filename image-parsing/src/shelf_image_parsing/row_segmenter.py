"""Shelf-row detection and segmentation component using YOLO11-seg."""

from pathlib import Path
from typing import Any, List, Optional
import cv2
import numpy as np

from .geometry import clip_box, normalize_box, polygon_to_bbox
from .schemas import ShelfRowItem


class ShelfRowSegmenter:
    """Detects and segments shelf rows from photographs using YOLO segmentation models."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        confidence: float = 0.25,
        iou: float = 0.50,
        device: str = "cpu",
        row_filter_width_ratio: float = 0.40,
        model: Optional[Any] = None,
    ):
        self.confidence = confidence
        self.iou = iou
        self.device = device
        self.row_filter_width_ratio = row_filter_width_ratio
        self.model_path = model_path
        self.model = model

        if self.model is None and model_path:
            resolved_path = Path(model_path).resolve()
            if not resolved_path.is_file():
                raise FileNotFoundError(
                    f"Shelf-row segmentation weights not found at: {model_path}. "
                    "Please review MODEL_SETUP.md for instructions on obtaining the weights."
                )
            try:
                from ultralytics import YOLO
                self.model = YOLO(str(resolved_path))
            except Exception as e:
                raise RuntimeError(f"Failed to load YOLO segmentation model from {model_path}: {e}")

    def segment(self, image: np.ndarray) -> List[ShelfRowItem]:
        """Detect and segment shelf rows in an image.

        Args:
            image: BGR numpy image (H, W, 3).

        Returns:
            List of ShelfRowItem sorted top-to-bottom with 1-indexed row numbers.
        """
        if self.model is None:
            raise RuntimeError("Segmentation model is not initialized.")

        orig_h, orig_w = image.shape[:2]
        if orig_h == 0 or orig_w == 0:
            return []

        results = self.model(
            image,
            conf=self.confidence,
            iou=self.iou,
            device=self.device,
            verbose=False,
        )

        if not results:
            return []

        res = results[0]
        masks = res.masks
        if masks is None:
            return []

        raw_rows: List[dict] = []

        # Process each detected mask
        # Ultralytics masks provide .xy (list of contour points per detection) and .data (tensor of masks)
        polygons = getattr(masks, "xy", None)
        mask_data = getattr(masks, "data", None)
        boxes = getattr(res, "boxes", None)

        num_masks = len(polygons) if polygons is not None else (len(mask_data) if mask_data is not None else 0)

        for i in range(num_masks):
            conf = None
            if boxes is not None and len(boxes) > i:
                conf = round(float(boxes[i].conf[0].item()), 4)

            # Option A: Contour polygon available directly from Ultralytics
            poly_points: Optional[List[List[int]]] = None
            x1, y1, x2, y2 = 0, 0, 0, 0

            if polygons is not None and i < len(polygons) and len(polygons[i]) > 0:
                raw_poly = polygons[i]
                poly_points = [[int(round(pt[0])), int(round(pt[1]))] for pt in raw_poly]
                x1, y1, x2, y2 = polygon_to_bbox(poly_points)
            elif mask_data is not None and i < len(mask_data):
                # Option B: Extract from binary mask tensor (reference repository method)
                raw_mask = mask_data[i].cpu().numpy().astype(np.uint8)
                resized_mask = cv2.resize(raw_mask, (orig_w, orig_h), interpolation=cv2.INTER_NEAREST)
                ys, xs = np.where(resized_mask == 1)
                if len(xs) == 0 or len(ys) == 0:
                    continue
                x1, y1, x2, y2 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())

                # Find contour for polygon representation
                contours, _ = cv2.findContours(resized_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if contours:
                    largest_c = max(contours, key=cv2.contourArea)
                    poly_points = [[int(pt[0][0]), int(pt[0][1])] for pt in largest_c]

            clipped = clip_box([x1, y1, x2, y2], orig_w, orig_h)
            width = clipped[2] - clipped[0]
            height = clipped[3] - clipped[1]

            if width <= 0 or height <= 0:
                continue

            raw_rows.append({
                "bbox": clipped,
                "polygon": poly_points,
                "confidence": conf,
                "width": width,
                "top_y": clipped[1],
            })

        if not raw_rows:
            return []

        # Filter out narrow noisy rows based on reference implementation logic
        widths = [r["width"] for r in raw_rows]
        avg_width = sum(widths) / len(widths)
        min_width_threshold = avg_width * self.row_filter_width_ratio

        filtered = [r for r in raw_rows if r["width"] >= min_width_threshold]
        if not filtered:
            filtered = raw_rows  # Fallback if all were pruned

        # Sort top to bottom by top vertical coordinate (y1)
        filtered.sort(key=lambda r: r["top_y"])

        shelf_rows: List[ShelfRowItem] = []
        for idx, row_data in enumerate(filtered):
            bbox = row_data["bbox"]
            shelf_rows.append(
                ShelfRowItem(
                    row_number=idx + 1,
                    bbox_xyxy=bbox,
                    bbox_normalized=normalize_box(bbox, orig_w, orig_h),
                    polygon=row_data["polygon"],
                    confidence=row_data["confidence"],
                )
            )

        return shelf_rows
