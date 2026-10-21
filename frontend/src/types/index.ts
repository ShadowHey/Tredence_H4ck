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
  };
  created_at: string;
  source_filename: string;
  planogram_id?: number | null;
  planogram_name?: string | null;
  shelf_id?: number | null;
  shelf_snapshot?: ShelfSnapshot | null;
}
