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
    audit_snapshot: Optional[dict[str, Any]] = None


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
    audit_snapshot: Optional[dict[str, Any]] = None
    compliance_audit: Optional[dict[str, Any]] = None


class ComplianceAuditResponse(BaseModel):
    schema_version: int
    audit_version: int
    output_id: int
    job_id: int
    source_filename: str
    audit_snapshot_sha256: Optional[str] = None
    status: Literal["complete", "needs_review"]
    summary: dict[str, int]
    assignments: list[dict[str, Any]]
    slot_results: list[dict[str, Any]]
    layout_comparison: dict[str, Any] = Field(default_factory=dict)
    issues: list[dict[str, Any]]
    label_audit: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ComplianceIssueResolutionRequest(BaseModel):
    status: Literal["open", "acknowledged", "resolved"]
    note: Optional[str] = Field(default=None, max_length=2000)


class ExportRequest(BaseModel):
    output_ids: list[int] = Field(min_length=1)


class PlanogramPosition(BaseModel):
    status: Literal["calibrated"]
    method: Literal["four_corner_homography", "detected_row_linear"]
    row_index: int = Field(ge=0)
    x_start_cm: float
    x_end_cm: float
    center_x_cm: float
    position_tolerance_cm: float = Field(gt=0)
    detected_row_number: Optional[int] = None


class PositionCalibration(BaseModel):
    status: Literal["calibrated", "needs_review"]
    method: Literal["four_corner_homography", "detected_row_linear", "unavailable"]
    reason: Optional[str] = None
    position_tolerance_cm: Optional[float] = None
    row_index_origin: Literal[0] = 0
    row_order: Literal["top_to_bottom"] = "top_to_bottom"
    shelf_width_cm: Optional[float] = None
    straight_on_assumption: bool = True
    expected_row_count: Optional[int] = None
    detected_row_count: Optional[int] = None
    row_count_match: Optional[bool] = None


class CutoutItem(BaseModel):
    id: str
    category: str
    crop_path: str
    bbox_xyxy: list[int]
    confidence: float
    row_number: Optional[int] = None
    cluster_id: Optional[int] = None
    area_px: Optional[int] = None
    quality_status: Literal["unchecked", "usable", "review"] = "unchecked"
    quality_flags: list[str] = Field(default_factory=list)
    catalog_match: Optional["CutoutCatalogMatch"] = None
    planogram_position: Optional[PlanogramPosition] = None


class CutoutsResponse(BaseModel):
    output_id: int
    source_filename: str
    total_count: int
    analysis_version: int = 3
    audit_snapshot_sha256: Optional[str] = None
    position_calibration: Optional[PositionCalibration] = None
    calibration_corners_xy: Optional[list[list[float]]] = None
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


class CutoutCatalogMatch(BaseModel):
    status: Literal["matched", "unmatched", "needs_review"]
    reason: str
    top_candidate: Optional[CatalogMatchedProduct] = None
    runner_up: Optional[CatalogMatchedProduct] = None
    similarity: Optional[float] = None
    runner_up_similarity: Optional[float] = None
    confidence_margin: Optional[float] = None
    similarity_threshold: float
    margin_threshold: float
    color_similarity: Optional[float] = None
    color_filter_candidate_count_before: int = 0
    color_filter_candidate_count_after: int = 0
    color_filter_threshold: float = 0.30
    color_filter_fallback: bool = False
    color_filter_fallback_reason: Optional[str] = None
    matching_method: str = "clip_only"


class ClusterRow(BaseModel):
    cluster_id: int
    item_count: int
    similar_objects: list[CutoutItem]
    similarity_percentage: float
    is_catalog_match: bool
    catalog_confidence: float
    catalog_product: Optional[CatalogMatchedProduct] = None
    catalog_consensus: dict[str, Any] = Field(default_factory=dict)


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
    catalog_match_margin_threshold: float = 0.03
    analysis_version: int = 3
    catalog_scope: str = "job_audit_snapshot.shelf_catalogue"
    audit_snapshot_sha256: Optional[str] = None
    products_needing_review: int = 0
    position_calibration: Optional[PositionCalibration] = None
    detections_with_calibrated_positions: int = 0
    compliance_summary: Optional[dict[str, int]] = None
    clusters: list[ClusterRow]
