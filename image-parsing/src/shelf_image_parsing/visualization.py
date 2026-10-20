"""Combined multi-layer visualizer for ShelfSense AI image parsing."""

from typing import List, Optional, Tuple
import cv2
import numpy as np

from .config import PipelineConfig
from .schemas import DetectionItem, ImageParsingSummary, ShelfRowItem


class ShelfVisualizer:
    """Combines product boxes, empty-space boxes, shelf rows, and analytics overlays into one annotated image."""

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()

    def draw_label(
        self,
        image: np.ndarray,
        text: str,
        origin: Tuple[int, int],
        bg_color_bgr: Tuple[int, int, int],
        text_color_bgr: Tuple[int, int, int] = (255, 255, 255),
        font_scale: float = 0.45,
        thickness: int = 1,
    ) -> None:
        """Draw text with a solid high-contrast background rectangle for readability."""
        x, y = origin
        font = cv2.FONT_HERSHEY_SIMPLEX
        (w, h), baseline = cv2.getTextSize(text, font, font_scale, thickness)

        # Ensure label fits within image boundaries
        img_h, img_w = image.shape[:2]
        y1 = max(0, y - h - baseline - 4)
        y2 = min(img_h, y1 + h + baseline + 4)
        x1 = max(0, min(x, img_w - w - 6))
        x2 = min(img_w, x1 + w + 6)

        cv2.rectangle(image, (x1, y1), (x2, y2), bg_color_bgr, cv2.FILLED)
        cv2.putText(image, text, (x1 + 3, y2 - baseline - 2), font, font_scale, text_color_bgr, thickness, cv2.LINE_AA)

    def annotate(
        self,
        original_image: np.ndarray,
        products: List[DetectionItem],
        empty_regions: List[DetectionItem],
        shelf_rows: List[ShelfRowItem],
        summary: Optional[ImageParsingSummary] = None,
        source_name: str = "",
    ) -> np.ndarray:
        """Generate a combined annotated image following strict drawing order and color specifications:

        1. Base: Original photograph (unmodified dimensions)
        2. Layer 1: Shelf row regions and outlines (Amber #FFB000)
        3. Layer 2: Empty space bounding boxes with translucent fill (Dark royal blue #1739B7)
        4. Layer 3: Product bounding boxes (Neon cyan #00E5FF)
        5. Layer 4: Labels and compact top summary telemetry
        """
        annotated = original_image.copy()
        img_h, img_w = annotated.shape[:2]

        # ----------------------------------------------------
        # 1. Shelf Rows (Amber #FFB000 -> BGR: [0, 176, 255])
        # ----------------------------------------------------
        row_cfg = self.config.shelf_row_style
        row_color = tuple(row_cfg.color_bgr)

        # Translucent overlay for row regions
        if shelf_rows and row_cfg.fill_translucent:
            row_overlay = annotated.copy()
            for r in shelf_rows:
                if r.polygon and len(r.polygon) >= 3:
                    pts = np.array(r.polygon, np.int32).reshape((-1, 1, 2))
                    cv2.fillPoly(row_overlay, [pts], row_color)
                else:
                    x1, y1, x2, y2 = r.bbox_xyxy
                    cv2.rectangle(row_overlay, (x1, y1), (x2, y2), row_color, cv2.FILLED)
            cv2.addWeighted(row_overlay, row_cfg.fill_alpha, annotated, 1.0 - row_cfg.fill_alpha, 0, annotated)

        # Row boundary outlines and Row tags
        for r in shelf_rows:
            x1, y1, x2, y2 = r.bbox_xyxy
            if r.polygon and len(r.polygon) >= 3:
                pts = np.array(r.polygon, np.int32).reshape((-1, 1, 2))
                cv2.polylines(annotated, [pts], isClosed=True, color=row_color, thickness=row_cfg.thickness)
            else:
                cv2.rectangle(annotated, (x1, y1), (x2, y2), row_color, row_cfg.thickness)

            # Row label
            row_text = f"ROW {r.row_number}"
            if r.confidence is not None:
                row_text += f" {r.confidence:.2f}"
            self.draw_label(
                annotated,
                row_text,
                origin=(max(4, x1 + 4), max(20, y1 + 18)),
                bg_color_bgr=row_color,
                text_color_bgr=(10, 10, 10),
                font_scale=row_cfg.font_scale,
                thickness=1,
            )

        # ----------------------------------------------------
        # 2. Empty Shelf Spaces (Dark Royal Blue #1739B7 -> BGR: [183, 57, 23])
        # ----------------------------------------------------
        empty_cfg = self.config.empty_space_style
        empty_color = tuple(empty_cfg.color_bgr)

        if empty_regions and empty_cfg.fill_translucent:
            empty_overlay = annotated.copy()
            for e in empty_regions:
                x1, y1, x2, y2 = e.bbox_xyxy
                cv2.rectangle(empty_overlay, (x1, y1), (x2, y2), empty_color, cv2.FILLED)
            cv2.addWeighted(empty_overlay, empty_cfg.fill_alpha, annotated, 1.0 - empty_cfg.fill_alpha, 0, annotated)

        for e in empty_regions:
            x1, y1, x2, y2 = e.bbox_xyxy
            cv2.rectangle(annotated, (x1, y1), (x2, y2), empty_color, empty_cfg.thickness)

            label = f"EMPTY SPACE {e.confidence:.2f}" if empty_cfg.show_confidence else "EMPTY SPACE"
            if e.row_number:
                label = f"R{e.row_number} " + label
            self.draw_label(
                annotated,
                label,
                origin=(x1, y1),
                bg_color_bgr=empty_color,
                text_color_bgr=(255, 255, 255),
                font_scale=empty_cfg.font_scale,
                thickness=1,
            )

        # ----------------------------------------------------
        # 3. Product Bounding Boxes (Neon Cyan #00E5FF -> BGR: [255, 229, 0])
        # ----------------------------------------------------
        prod_cfg = self.config.product_style
        prod_color = tuple(prod_cfg.color_bgr)

        for p in products:
            x1, y1, x2, y2 = p.bbox_xyxy
            cv2.rectangle(annotated, (x1, y1), (x2, y2), prod_color, prod_cfg.thickness)

            # When product box is very small, place label above or inside cleanly
            box_h = y2 - y1
            label_y = y1 if box_h > 35 else y2
            label = f"PRODUCT {p.confidence:.2f}" if prod_cfg.show_confidence else "PRODUCT"
            self.draw_label(
                annotated,
                label,
                origin=(x1, label_y),
                bg_color_bgr=(40, 40, 40),
                text_color_bgr=prod_color,
                font_scale=prod_cfg.font_scale,
                thickness=1,
            )

        # ----------------------------------------------------
        # 4. Summary Header Telemetry Bar
        # ----------------------------------------------------
        p_count = len(products)
        e_count = len(empty_regions)
        r_count = len(shelf_rows)
        empty_pct_str = f"{summary.empty_area_percentage:.1f}%" if (summary and summary.empty_area_percentage is not None) else "N/A"

        banner_text = (
            f"ShelfSense AI | Products: {p_count} | Empty Slots: {e_count} | "
            f"Rows: {r_count} | Empty Area: {empty_pct_str}"
        )
        if source_name:
            banner_text = f"[{source_name}] " + banner_text

        # Semi-transparent top bar
        bar_h = 32
        bar_overlay = annotated.copy()
        cv2.rectangle(bar_overlay, (0, 0), (img_w, bar_h), (18, 20, 26), cv2.FILLED)
        cv2.addWeighted(bar_overlay, 0.82, annotated, 0.18, 0, annotated)

        cv2.putText(
            annotated,
            banner_text,
            (12, 21),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.50,
            (240, 240, 240),
            1,
            cv2.LINE_AA,
        )

        return annotated
