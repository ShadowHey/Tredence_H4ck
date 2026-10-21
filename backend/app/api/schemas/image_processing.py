from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


ImageStatus = Literal["ready", "queued", "processing", "processed", "failed"]


class ShelfSnapshot(BaseModel):
    id: int
    name: str
    width_cm: float
    total_height_cm: float
    depth_cm: float
    row_count: int


class InputImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    storage_path: str
    content_type: str
    size_bytes: int
    status: ImageStatus
    planogram_id: Optional[int]
    shelf_id: Optional[int]
    shelf_snapshot: Optional[ShelfSnapshot]
    created_at: datetime
    updated_at: datetime
    job_id: Optional[int] = None
    error_message: Optional[str] = None
    output_id: Optional[int] = None


class ProcessImageRequest(BaseModel):
    planogram_id: int = Field(gt=0)
    shelf_id: int = Field(gt=0)


class ProcessedOutputResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    input_image_id: int
    job_id: int
    annotated_image_path: str
    result_json_path: str
    metrics: dict[str, Any]
    created_at: datetime
    source_filename: str
    planogram_id: Optional[int]
    planogram_name: Optional[str]
    shelf_id: Optional[int]
    shelf_snapshot: Optional[ShelfSnapshot]


class ExportRequest(BaseModel):
    output_ids: list[int] = Field(min_length=1)


class CutoutItem(BaseModel):
    id: str
    category: str
    crop_path: str
    bbox_xyxy: list[int]
    confidence: float
    row_number: Optional[int] = None
    cluster_id: Optional[int] = None
    area_px: Optional[int] = None


class CutoutsResponse(BaseModel):
    output_id: int
    source_filename: str
    total_count: int
    products: list[CutoutItem]
    shelves: list[CutoutItem]
    empty_spaces: list[CutoutItem]


class CatalogMatchedProduct(BaseModel):
    id: int
    sku: str
    name: str
    category: str
    image_path: str
    price: float
    currency: str


class ClusterRow(BaseModel):
    cluster_id: int
    item_count: int
    similar_objects: list[CutoutItem]
    similarity_percentage: float
    is_catalog_match: bool
    catalog_confidence: float
    catalog_product: Optional[CatalogMatchedProduct] = None


class OutputAnalysisResponse(BaseModel):
    output_id: int
    source_filename: str
    planogram_name: Optional[str] = None
    shelf_name: Optional[str] = None
    shelf_dimensions: Optional[str] = None
    total_detections: int
    total_clusters: int
    matched_clusters_count: int
    catalog_confidence_threshold: float = 0.95
    clusters: list[ClusterRow]
