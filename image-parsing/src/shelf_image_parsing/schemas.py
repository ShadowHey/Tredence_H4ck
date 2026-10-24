"""Pydantic data schemas for ShelfSense AI image parsing pipeline."""

from typing import List, Optional
from pydantic import BaseModel, Field


class DetectionItem(BaseModel):
    """Represents a single product or empty-space detection."""
    class_name: str = Field(description="Name of detected class (product, empty_space)")
    class_id: int = Field(description="Model class ID (0 for empty_space, 1 for product)")
    confidence: float = Field(description="Detection confidence score between 0.0 and 1.0")
    bbox_xyxy: List[int] = Field(description="Pixel bounding box [x1, y1, x2, y2]")
    bbox_normalized: List[float] = Field(description="Normalized coordinates [x1_norm, y1_norm, x2_norm, y2_norm]")
    row_number: Optional[int] = Field(default=None, description="1-indexed shelf row number from top to bottom")
    area_px: Optional[int] = Field(default=None, description="Area in square pixels")
    quality_status: str = Field(default="unchecked", description="Detection geometry quality: unchecked, usable, or review")
    quality_flags: List[str] = Field(default_factory=list, description="Non-destructive warnings about suspicious detection geometry")


class ShelfRowItem(BaseModel):
    """Represents a detected shelf row."""
    row_number: int = Field(description="1-indexed shelf row index sorted top-to-bottom")
    bbox_xyxy: List[int] = Field(description="Enclosing bounding box [x1, y1, x2, y2]")
    bbox_normalized: List[float] = Field(description="Normalized coordinates [x1_norm, y1_norm, x2_norm, y2_norm]")
    polygon: Optional[List[List[int]]] = Field(default=None, description="Contour polygon points [[x, y], ...]")
    confidence: Optional[float] = Field(default=None, description="Segmentation confidence score if available")
    product_count: int = Field(default=0, description="Number of products detected in this row")
    empty_region_count: int = Field(default=0, description="Number of empty space slots detected in this row")
    empty_area_px: int = Field(default=0, description="Total empty space area in pixels for this row")
    product_area_px: int = Field(default=0, description="Total product area in pixels for this row")
    row_empty_percentage: Optional[float] = Field(
        default=None,
        description="Per-row empty space percentage: (empty_area / (empty_area + product_area)) * 100",
    )


class ImageParsingSummary(BaseModel):
    """High-level summary metrics for a processed shelf image."""
    product_count: int = Field(default=0, description="Total detected products")
    empty_region_count: int = Field(default=0, description="Total detected empty shelf regions")
    shelf_row_count: int = Field(default=0, description="Total detected shelf rows")
    empty_area_percentage: Optional[float] = Field(
        default=None,
        description="Area-based percentage: (empty_area / (empty_area + product_area)) * 100",
    )
    product_area_percentage: Optional[float] = Field(
        default=None,
        description="Area-based percentage: (product_area / (empty_area + product_area)) * 100",
    )
    total_empty_area_px: int = Field(default=0, description="Total accumulated empty pixel area")
    total_product_area_px: int = Field(default=0, description="Total accumulated product pixel area")
    excluded_product_count: int = Field(default=0, description="Product-class boxes excluded by the product confidence floor")
    product_confidence_threshold: float = Field(default=0.60, description="Minimum confidence required for a product box to enter matching")


class ImageParsingResult(BaseModel):
    """Top-level machine-readable output for a processed shelf image."""
    source_image: str = Field(description="Original filename or path of the input photograph")
    image_width: int = Field(description="Original image pixel width")
    image_height: int = Field(description="Original image pixel height")
    model_status: str = Field(
        default="completed",
        description="Execution status: 'completed', 'partial', 'no_detections', 'mocked', or 'failed'",
    )
    summary: ImageParsingSummary
    products: List[DetectionItem] = Field(default_factory=list)
    excluded_products: List[DetectionItem] = Field(
        default_factory=list,
        description="Low-confidence product boxes retained for uncertainty diagnostics only; never cropped or matched.",
    )
    empty_regions: List[DetectionItem] = Field(default_factory=list)
    shelf_rows: List[ShelfRowItem] = Field(default_factory=list)
    calibration: Optional[dict] = Field(
        default=None,
        description="Optional four-corner ArUco calibration anchors in source-image pixel coordinates.",
    )
    annotated_image: Optional[str] = Field(default=None, description="Filename of combined annotated image")
    errors: Optional[List[str]] = Field(default=None, description="Any warnings or error details encountered")
