import {
  Product,
  Planogram,
  PlanogramSummary,
  DashboardMetrics,
  Shelf,
  Placement,
  RowCapacity,
  PlanogramExportJSON,
  InputImage,
  ProcessedOutput,
  CutoutsResponse,
  OutputAnalysisResponse,
} from "@/types";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function getImageUrl(imagePath?: string | null): string {
  if (!imagePath) return "/placeholder-product.svg";
  if (imagePath.startsWith("http://") || imagePath.startsWith("https://")) {
    return imagePath;
  }
  const cleanPath = imagePath.startsWith("/") ? imagePath.slice(1) : imagePath;
  return `${API_BASE_URL}/${cleanPath}`;
}

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        Accept: "application/json",
        ...(options?.headers || {}),
      },
    });

    if (!res.ok) {
      let errorMessage = `API request failed: ${res.status} ${res.statusText}`;
      try {
        const errorData = await res.json();
        if (errorData.detail) {
          if (typeof errorData.detail === "string") {
            errorMessage = errorData.detail;
          } else if (Array.isArray(errorData.detail)) {
            errorMessage = errorData.detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join(", ");
          }
        }
      } catch {
        // Fallback to text status
      }
      throw new Error(errorMessage);
    }

    return await res.json();
  } catch (err: unknown) {
    if (err instanceof TypeError && err.message.includes("Failed to fetch")) {
      throw new Error(`Cannot connect to backend server at ${API_BASE_URL}. Ensure FastAPI is running on port 8000.`);
    }
    throw err;
  }
}

export const api = {
  // Health
  getHealth: () => request<{ status: string; database: string }>("/health"),

  // Products
  getProducts: (search?: string, category?: string) => {
    const params = new URLSearchParams();
    if (search) params.append("search", search);
    if (category) params.append("category", category);
    const qs = params.toString() ? `?${params.toString()}` : "";
    return request<Product[]>(`/api/v1/products${qs}`);
  },

  getProduct: (id: number) => request<Product>(`/api/v1/products/${id}`),

  createProductMultipart: (formData: FormData) =>
    request<Product>("/api/v1/products", {
      method: "POST",
      body: formData,
    }),

  createProductDirect: (data: Partial<Product>) =>
    request<Product>("/api/v1/products/direct", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),

  updateProduct: (id: number, data: Partial<Product>) =>
    request<Product>(`/api/v1/products/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),

  deleteProduct: (id: number) =>
    request<{ message: string }>(`/api/v1/products/${id}`, {
      method: "DELETE",
    }),

  // Planograms
  getPlanograms: () => request<PlanogramSummary[]>("/api/v1/planograms"),

  getDashboardMetrics: () => request<DashboardMetrics>("/api/v1/planograms/metrics"),

  getPlanogram: (id: number) => request<Planogram>(`/api/v1/planograms/${id}`),

  createPlanogram: (data: { name: string; description?: string }) =>
    request<Planogram>("/api/v1/planograms", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),

  updatePlanogram: (id: number, data: { name?: string; description?: string }) =>
    request<Planogram>(`/api/v1/planograms/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),

  deletePlanogram: (id: number) =>
    request<{ message: string }>(`/api/v1/planograms/${id}`, {
      method: "DELETE",
    }),

  clonePlanogram: (id: number, name?: string) =>
    request<Planogram>(`/api/v1/planograms/${id}/clone`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(name ? { name } : {}),
    }),

  // Shelves
  createShelf: (planogramId: number, data: Partial<Shelf>) =>
    request<Shelf>(`/api/v1/planograms/${planogramId}/shelves`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),

  updateShelf: (shelfId: number, data: Partial<Shelf>) =>
    request<Shelf>(`/api/v1/shelves/${shelfId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),

  deleteShelf: (shelfId: number) =>
    request<{ message: string }>(`/api/v1/shelves/${shelfId}`, {
      method: "DELETE",
    }),

  getRowCapacity: (shelfId: number, rowIndex: number) =>
    request<RowCapacity>(`/api/v1/shelves/${shelfId}/capacity/${rowIndex}`),

  // Placements
  createPlacement: (shelfId: number, data: { product_id: number; row_index: number; x_offset_cm: number; facing_count?: number }) =>
    request<Placement>(`/api/v1/shelves/${shelfId}/placements`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),

  autoPackPlacement: (shelfId: number, data: { product_id: number; row_index: number; facing_count?: number }) =>
    request<Placement>(`/api/v1/shelves/${shelfId}/placements/auto-pack`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),

  suggestSlot: (shelfId: number, data: { product_id: number; row_index: number; facing_count?: number }) =>
    request<{ shelf_id: number; product_id: number; row_index: number; x_offset_cm: number; facing_count: number }>(
      `/api/v1/shelves/${shelfId}/placements/suggest-slot`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      }
    ),

  autoArrangeRow: (shelfId: number, rowIndex: number) =>
    request<{ shelf_id: number; row_index: number; rearranged_count: number; placements: Placement[] }>(
      `/api/v1/shelves/${shelfId}/rows/${rowIndex}/auto-arrange`,
      {
        method: "POST",
      }
    ),

  batchCreatePlacements: (
    shelfId: number,
    placements: Array<{ product_id: number; row_index: number; x_offset_cm: number; facing_count?: number }>
  ) =>
    request<Placement[]>(`/api/v1/shelves/${shelfId}/placements/batch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ placements }),
    }),

  updatePlacement: (placementId: number, data: { row_index?: number; x_offset_cm?: number; facing_count?: number }) =>
    request<Placement>(`/api/v1/placements/${placementId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),

  deletePlacement: (placementId: number) =>
    request<{ message: string }>(`/api/v1/placements/${placementId}`, {
      method: "DELETE",
    }),

  // Categories & CSV
  getCategories: () =>
    request<Array<{ category: string; count: number }>>("/api/v1/products/categories"),

  getExportProductsCSVUrl: () => `${API_BASE_URL}/api/v1/products/export/csv`,

  importProductsCSV: (formData: FormData) =>
    request<{ total_rows: number; created: number; updated: number; errors: string[] }>(
      "/api/v1/products/import/csv",
      {
        method: "POST",
        body: formData,
      }
    ),

  // Export
  exportPlanogramJSON: (planogramId: number) =>
    request<PlanogramExportJSON>(`/api/v1/planograms/${planogramId}/export.json`),

  // Seed
  seedCatalogue: () =>
    request<{ status: string; message: string; seeded_count: number }>("/api/v1/seed", {
      method: "POST",
    }),

  // Shelf image processing
  getInputImages: () => request<InputImage[]>("/api/v1/input-images"),

  uploadInputImages: (files: File[]) => {
    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));
    return request<InputImage[]>("/api/v1/input-images", { method: "POST", body: formData });
  },

  processInputImage: (id: number, target: { planogram_id: number; shelf_id: number }) =>
    request<InputImage>(`/api/v1/input-images/${id}/process`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(target),
    }),

  deleteInputImage: (id: number) =>
    request<{ message: string }>(`/api/v1/input-images/${id}`, { method: "DELETE" }),

  getProcessedOutputs: () => request<ProcessedOutput[]>("/api/v1/outputs"),

  deleteProcessedOutputs: (outputIds: number[]) =>
    request<{ message: string }>("/api/v1/outputs", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ output_ids: outputIds }),
    }),

  getOutputCutouts: (outputId: number) =>
    request<CutoutsResponse>(`/api/v1/outputs/${outputId}/cutouts`),

  getOutputAnalysis: (outputId: number) =>
    request<OutputAnalysisResponse>(`/api/v1/outputs/${outputId}/analysis`),

  analyzeOutput: (outputId: number) =>
    request<OutputAnalysisResponse>(`/api/v1/outputs/${outputId}/analyze`, {
      method: "POST",
    }),
};

export async function downloadProcessedOutputs(outputIds: number[]): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/outputs/export`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ output_ids: outputIds }),
  });
  if (!response.ok) throw new Error("Unable to export the selected outputs.");
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "shelfsense-outputs.zip";
  anchor.click();
  URL.revokeObjectURL(url);
}
