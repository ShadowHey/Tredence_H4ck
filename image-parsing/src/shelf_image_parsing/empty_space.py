"""Empty shelf-space refinement, row-assignment, and area analytics."""

from typing import Dict, List, Optional, Tuple
import numpy as np

from .geometry import apply_nms, calculate_box_area, calculate_iou, get_box_center
from .schemas import DetectionItem, ImageParsingSummary, ShelfRowItem


class EmptySpaceRefiner:
    """Refines empty-space detections, assigns them to shelf rows, and computes utilization metrics."""

    def __init__(
        self,
        nms_iou_threshold: float = 0.50,
        assignment_mode: str = "center_band",
        filter_outside_shelf: bool = True,
        shelf_vertical_margin_px: int = 50,
    ):
        self.nms_iou_threshold = nms_iou_threshold
        self.assignment_mode = assignment_mode
        self.filter_outside_shelf = filter_outside_shelf
        self.shelf_vertical_margin_px = shelf_vertical_margin_px

    def deduplicate(self, empty_boxes: List[DetectionItem]) -> List[DetectionItem]:
        """Deduplicate heavily overlapping empty shelf detections using NMS."""
        if len(empty_boxes) <= 1:
            return empty_boxes

        boxes = [e.bbox_xyxy for e in empty_boxes]
        scores = [e.confidence for e in empty_boxes]
        keep_indices = apply_nms(boxes, scores, self.nms_iou_threshold)

        return [empty_boxes[i] for i in keep_indices]

    def filter_regions_outside_shelf(
        self,
        empty_boxes: List[DetectionItem],
        shelf_rows: List[ShelfRowItem],
        image_height: int,
        products: Optional[List[DetectionItem]] = None,
    ) -> List[DetectionItem]:
        """Prune empty boxes that fall outside the detected shelving unit (e.g. ceiling, floor)."""
        if not shelf_rows and not products:
            return empty_boxes

        y_mins = [r.bbox_xyxy[1] for r in shelf_rows]
        y_maxs = [r.bbox_xyxy[3] for r in shelf_rows]
        if products:
            y_mins.extend([p.bbox_xyxy[1] for p in products])
            y_maxs.extend([p.bbox_xyxy[3] for p in products])

        min_shelf_y = (min(y_mins) - self.shelf_vertical_margin_px) if y_mins else 0
        max_shelf_y = (max(y_maxs) + self.shelf_vertical_margin_px) if y_maxs else image_height

        valid: List[DetectionItem] = []
        for e in empty_boxes:
            _, cy = get_box_center(e.bbox_xyxy)
            if min_shelf_y <= cy <= max_shelf_y:
                valid.append(e)

        return valid

    def assign_to_rows(
        self,
        items: List[DetectionItem],
        shelf_rows: List[ShelfRowItem],
        image_height: int,
    ) -> List[DetectionItem]:
        """Assign detection items (products or empty spaces) to shelf rows using vertical band logic.

        Following the reference repository's band algorithm:
        Vertical bands are defined by the centers of consecutive shelf rows.
        """
        if not shelf_rows or not items:
            return items

        # Rows are pre-sorted top-to-bottom
        row_centers = [get_box_center(r.bbox_xyxy)[1] for r in shelf_rows]

        # Construct vertical bands between row centers
        bands: List[Tuple[float, float]] = []
        if len(row_centers) == 1:
            bands.append((0.0, float(image_height)))
        else:
            # Band 0: top of image to midway between row 0 and row 1
            bands.append((0.0, (row_centers[0] + row_centers[1]) / 2.0))
            for i in range(1, len(row_centers) - 1):
                low = (row_centers[i - 1] + row_centers[i]) / 2.0
                high = (row_centers[i] + row_centers[i + 1]) / 2.0
                bands.append((low, high))
            # Last band: midway to bottom of image
            bands.append(((row_centers[-2] + row_centers[-1]) / 2.0, float(image_height)))

        assigned_items: List[DetectionItem] = []
        for item in items:
            _, cy = get_box_center(item.bbox_xyxy)
            assigned_row = len(row_centers)  # default to last row

            for band_idx, (low, high) in enumerate(bands):
                if low <= cy < high:
                    assigned_row = band_idx + 1
                    break

            # Clone with updated row_number
            updated_item = item.model_copy(update={"row_number": assigned_row})
            assigned_items.append(updated_item)

        return assigned_items

    def compute_metrics(
        self,
        products: List[DetectionItem],
        empty_regions: List[DetectionItem],
        shelf_rows: List[ShelfRowItem],
    ) -> Tuple[ImageParsingSummary, List[ShelfRowItem]]:
        """Compute area-based shelf space metrics per the reference repository's formula:

        Empty Area % = (Total Empty Area / (Total Empty Area + Total Product Area)) * 100
        Product Area % = (Total Product Area / (Total Empty Area + Total Product Area)) * 100
        """
        total_empty_area = sum(calculate_box_area(e.bbox_xyxy) for e in empty_regions)
        total_product_area = sum(calculate_box_area(p.bbox_xyxy) for p in products)
        combined_area = total_empty_area + total_product_area

        empty_area_pct: Optional[float] = None
        product_area_pct: Optional[float] = None

        if combined_area > 0:
            empty_area_pct = round((total_empty_area / combined_area) * 100.0, 2)
            product_area_pct = round((total_product_area / combined_area) * 100.0, 2)

        # Update per-row metrics
        updated_rows: List[ShelfRowItem] = []
        for r in shelf_rows:
            row_num = r.row_number
            row_prods = [p for p in products if p.row_number == row_num]
            row_empties = [e for e in empty_regions if e.row_number == row_num]

            row_p_area = int(round(sum(calculate_box_area(p.bbox_xyxy) for p in row_prods)))
            row_e_area = int(round(sum(calculate_box_area(e.bbox_xyxy) for e in row_empties)))
            row_combined = row_p_area + row_e_area

            row_pct = round((row_e_area / row_combined) * 100.0, 2) if row_combined > 0 else None

            updated_r = r.model_copy(
                update={
                    "product_count": len(row_prods),
                    "empty_region_count": len(row_empties),
                    "product_area_px": row_p_area,
                    "empty_area_px": row_e_area,
                    "row_empty_percentage": row_pct,
                }
            )
            updated_rows.append(updated_r)

        summary = ImageParsingSummary(
            product_count=len(products),
            empty_region_count=len(empty_regions),
            shelf_row_count=len(shelf_rows),
            empty_area_percentage=empty_area_pct,
            product_area_percentage=product_area_pct,
            total_empty_area_px=int(round(total_empty_area)),
            total_product_area_px=int(round(total_product_area)),
        )

        return summary, updated_rows
