export interface Product {
  id: number;
  sku: string;
  name: string;
  category: string;
  description?: string | null;
  price: number;
  currency: string;
  width_cm: number;
  height_cm: number;
  depth_cm: number;
  image_path: string;
  is_sample: boolean;
  created_at: string;
  updated_at: string;
}

export interface Placement {
  id: number;
  shelf_id: number;
  product_id: number;
  row_index: number;
  x_offset_cm: number;
  facing_count: number;
  product: Product;
  created_at: string;
  updated_at: string;
}

export interface Shelf {
  id: number;
  planogram_id: number;
  name: string;
  width_cm: number;
  total_height_cm: number;
  depth_cm: number;
  row_count: number;
  has_plinth: boolean;
  plinth_height_cm: number;
  row_heights?: number[] | null;
  order_index: number;
  placements: Placement[];
  created_at: string;
  updated_at: string;
}

export interface Planogram {
  id: number;
  name: string;
  description?: string | null;
  shelves: Shelf[];
  created_at: string;
  updated_at: string;
}

export interface PlanogramSummary {
  id: number;
  name: string;
  description?: string | null;
  shelf_count: number;
  placement_count: number;
  created_at: string;
  updated_at: string;
}

export interface DashboardMetrics {
  total_planograms: number;
  total_products: number;
  total_shelves: number;
  total_placements: number;
  recent_planograms: PlanogramSummary[];
}

export interface ComplianceDashboardData {
  summary: { audits: number; issues: number; open: number; acknowledged: number; resolved: number; needs_review: number };
  history: Array<{
    output_id: number; source_filename: string; planogram_name?: string | null; shelf_name?: string | null;
    created_at: string; audit_status: string; issue_count: number; open_count: number;
    acknowledged_count: number; resolved_count: number; needs_review_count: number;
  }>;
}

export interface ComplianceIssue {
  issue_id: string;
  type: string;
  severity?: string;
  status: "open" | "acknowledged" | "resolved";
  reason?: string;
  message?: string;
  recommended_action: string;
  row_index?: number | null;
  x_start_cm?: number | null;
  x_end_cm?: number | null;
  normalized_start?: number | null;
  normalized_end?: number | null;
  ordinal_from_left?: number | null;
  ordinal_from_right?: number | null;
  expected_ordinal_from_left?: number | null;
  sku?: string | null;
  expected_sku?: string | null;
  expected_quantity?: number | null;
  observed_quantity?: number | null;
  occupancy_ratio?: number | null;
  placement_id?: number | null;
  product_id?: number | null;
  cutout_id?: string | null;
  slot_id?: string | null;
  bbox_xyxy?: [number, number, number, number] | null;
  label_zone_id?: string | null;
  evidence_crop_path?: string | null;
  evidence?: { empty_space_cutout_ids?: string[]; product_cutout_ids?: string[]; placement_id?: number | null; row_index?: number | null; x_start_cm?: number | null; x_end_cm?: number | null };
  resolution_note?: string | null;
}

export interface ComplianceReport {
  schema_version: number; audit_version: number; output_id: number; job_id: number;
  source_filename: string; status: "complete" | "needs_review"; summary: Record<string, number>;
  issues: ComplianceIssue[]; assignments: Array<Record<string, unknown>>;
  slot_results: Array<Record<string, unknown>>; label_audit: Record<string, unknown>;
  layout_comparison?: {
    coordinate_system: string; row_order: string; shelf_width_cm?: number | null;
    calibration_status: string; comparison_status: string;
    rows: Array<{ row_index: number; row_number: number; alignment_status: string;
      expected_facings: Array<{ slot_id: string; sku: string; status: string; ordinal_from_left: number; ordinal_from_right: number; normalized_start: number; normalized_end: number }>;
      observed_products: Array<{ cutout_id: string; ordinal_from_left: number; ordinal_from_right: number; normalized_start: number; normalized_end: number }>;
      observed_empty_regions: Array<{ cutout_id: string; normalized_start: number; normalized_end: number }>;
      sequence_alignment: Array<{ status: "paired" | "missing_expected" | "unexpected_observed"; slot_id?: string | null; cutout_id?: string | null; position_cost?: number }>;
      expected_free_intervals: Array<{ normalized_start: number; normalized_end: number }>;
      observed_free_intervals: Array<{ normalized_start: number; normalized_end: number }>;
    }>;
  };
  created_at: string; audit_snapshot_sha256?: string | null;
}

export interface RowCapacity {
  row_index: number;
  total_width_cm: number;
  used_width_cm: number;
  remaining_width_cm: number;
  percent_used: number;
  placement_count: number;
}

export interface ExportPlacement {
  id: number;
  shelf_id: number;
  product_sku: string;
  product_name: string;
  row_index: number;
  x_offset_cm: number;
  facing_count: number;
  product_width_cm: number;
  product_height_cm: number;
  product_depth_cm: number;
}

export interface ExportShelf {
  id: number;
  name: string;
  width_cm: number;
  total_height_cm: number;
  depth_cm: number;
  row_count: number;
  has_plinth: boolean;
  plinth_height_cm: number;
  row_heights?: number[] | null;
  placements: ExportPlacement[];
}

export interface PlanogramExportJSON {
  format_version: string;
  unit: string;
  planogram_id: number;
  planogram_name: string;
  description?: string | null;
  shelves: ExportShelf[];
  products: {
    id: number;
    sku: string;
    name: string;
    category?: string | null;
    width_cm: number;
    height_cm: number;
    depth_cm: number;
    price: number;
    currency: string;
  }[];
  exported_at: string;
}

export type InputImageStatus = "ready" | "queued" | "processing" | "processed" | "failed";

export interface ShelfSnapshot {
  id: number;
  name: string;
  width_cm: number;
  total_height_cm: number;
  depth_cm: number;
  row_count: number;
}

export interface InputImage {
  id: number;
  original_filename: string;
  storage_path: string;
  content_type: string;
  size_bytes: number;
  status: InputImageStatus;
  planogram_id?: number | null;
  shelf_id?: number | null;
  shelf_snapshot?: ShelfSnapshot | null;
  created_at: string;
  updated_at: string;
  job_id?: number | null;
  error_message?: string | null;
  output_id?: number | null;
  audit_snapshot?: PlanogramAuditSnapshot | null;
}

export interface AuditCatalogueProduct {
  id: number;
  sku: string;
  name: string;
  category: string;
  description?: string | null;
  image_path: string;
  price: number;
  currency: string;
  width_cm: number;
  height_cm: number;
  depth_cm: number;
  embedding: number[] | null;
}

export interface PlanogramAuditSnapshot {
  schema_version: number;
  captured_at: string;
  snapshot_sha256: string;
  planogram: { id: number; name: string; description?: string | null; updated_at?: string | null };
  shelf: {
    id: number;
    name: string;
    width_cm: number;
    total_height_cm: number;
    depth_cm: number;
    row_count: number;
    row_heights_cm: number[] | null;
    resolved_row_heights_cm: number[];
    row_elevations_from_floor_cm: number[];
    row_index_origin: 0;
    row_order: "top_to_bottom";
    has_plinth: boolean;
    plinth_height_cm: number;
  };
  expected_placements: Array<{
    placement_id: number;
    product_id: number;
    row_index: number;
    x_offset_cm: number;
    x_end_cm: number;
    facing_count: number;
    sku: string;
    product_name: string;
  }>;
  expected_facing_slots: Array<{
    slot_id: string;
    placement_id: number;
    facing_index: number;
    product_id: number;
    sku: string;
    row_index: number;
    x_start_cm: number;
    x_end_cm: number;
  }>;
  shelf_catalogue: AuditCatalogueProduct[];
  expected_label_zones: Array<{
    label_zone_id: string;
    placement_id: number;
    product_id: number;
    sku: string;
    row_index: number;
    x_start_cm: number;
    x_end_cm: number;
    anchor: "below_placement";
    expected_price: number;
    expected_currency: string;
    geometry_status: "provisional_requires_image_calibration";
  }>;
  limitations: string[];
}

export interface ProcessedOutput {
  id: number;
  input_image_id: number;
  job_id: number;
  annotated_image_path: string;
  result_json_path: string;
  metrics: {
    product_count?: number;
    empty_region_count?: number;
    shelf_row_count?: number;
    empty_area_percentage?: number | null;
    analysis_summary?: {
      clusters_count?: number;
      matched_clusters_count?: number;
      products_cutouts?: number;
      empty_cutouts?: number;
      shelf_cutouts?: number;
    };
  };
  created_at: string;
  source_filename: string;
  planogram_id?: number | null;
  planogram_name?: string | null;
  shelf_id?: number | null;
  shelf_snapshot?: ShelfSnapshot | null;
  audit_snapshot?: PlanogramAuditSnapshot | null;
}

export interface CutoutItem {
  id: string;
  category: "product" | "shelf" | "empty_space";
  crop_path: string;
  bbox_xyxy: number[];
  confidence: number;
  row_number?: number | null;
  cluster_id?: number | null;
  area_px?: number | null;
  quality_status?: "unchecked" | "usable" | "review";
  quality_flags?: string[];
  catalog_match?: CutoutCatalogMatch | null;
  planogram_position?: PlanogramPosition | null;
}

export interface PlanogramPosition {
  status: "calibrated";
  method: "four_corner_homography" | "detected_row_linear";
  row_index: number;
  x_start_cm: number;
  x_end_cm: number;
  center_x_cm: number;
  position_tolerance_cm: number;
  detected_row_number?: number | null;
}

export interface PositionCalibration {
  status: "calibrated" | "needs_review";
  method: "four_corner_homography" | "detected_row_linear" | "unavailable";
  reason?: string | null;
  position_tolerance_cm?: number | null;
  row_index_origin: 0;
  row_order: "top_to_bottom";
  shelf_width_cm?: number | null;
  straight_on_assumption: boolean;
  expected_row_count?: number | null;
  detected_row_count?: number | null;
  row_count_match?: boolean | null;
}

export interface CutoutsResponse {
  output_id: number;
  source_filename: string;
  total_count: number;
  analysis_version: number;
  audit_snapshot_sha256?: string | null;
  position_calibration?: PositionCalibration | null;
  products: CutoutItem[];
  shelves: CutoutItem[];
  empty_spaces: CutoutItem[];
}

export interface CatalogMatchedProduct {
  id: number;
  sku: string;
  name: string;
  category: string;
  image_path: string;
  price: number;
  currency: string;
}

export interface CutoutCatalogMatch {
  status: "matched" | "unmatched" | "needs_review";
  reason: string;
  top_candidate?: CatalogMatchedProduct | null;
  runner_up?: CatalogMatchedProduct | null;
  similarity?: number | null;
  runner_up_similarity?: number | null;
  confidence_margin?: number | null;
  similarity_threshold: number;
  margin_threshold: number;
  color_similarity?: number | null;
  color_filter_candidate_count_before?: number;
  color_filter_candidate_count_after?: number;
  color_filter_threshold?: number;
  color_filter_fallback?: boolean;
  color_filter_fallback_reason?: string | null;
  matching_method?: string;
}

export interface ClusterRow {
  cluster_id: number;
  item_count: number;
  similar_objects: CutoutItem[];
  similarity_percentage: number;
  is_catalog_match: boolean;
  catalog_confidence: number;
  catalog_product?: CatalogMatchedProduct | null;
  catalog_consensus?: {
    status: "matched" | "needs_review";
    reason: string;
    support_count: number;
    considered_count: number;
    support_ratio: number;
  };
}

export interface OutputAnalysisResponse {
  output_id: number;
  source_filename: string;
  planogram_name?: string | null;
  shelf_name?: string | null;
  shelf_dimensions?: string | null;
  total_detections: number;
  total_clusters: number;
  matched_clusters_count: number;
  catalog_confidence_threshold: number;
  catalog_match_margin_threshold: number;
  analysis_version: number;
  catalog_scope: string;
  audit_snapshot_sha256?: string | null;
  products_needing_review: number;
  position_calibration?: PositionCalibration | null;
  detections_with_calibrated_positions: number;
  clusters: ClusterRow[];
}
