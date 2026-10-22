import React from "react";
import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { CutoutViewerModal } from "@/components/outputs/CutoutViewerModal";
import { AnalysisTable } from "@/components/analysis/AnalysisTable";
import { ClusterRow, CutoutItem } from "@/types";

const { mockCutoutItemProduct, mockCutoutItemShelf, mockCutoutItemEmpty, mockClusters } = vi.hoisted(() => {
  const prod: CutoutItem = {
    id: "prod_001",
    category: "product",
    crop_path: "uploads/cutouts/crop_1.jpg",
    bbox_xyxy: [100, 200, 150, 300],
    confidence: 0.94,
    row_number: 1,
    cluster_id: 1,
    area_px: 5000,
    catalog_match: {
      status: "matched",
      reason: "above_threshold_and_unambiguous",
      top_candidate: {
        id: 42,
        sku: "SKU-COLGATE-150G",
        name: "Colgate Total 150g",
        category: "Oral Care",
        image_path: "uploads/products/colgate.jpg",
        price: 130,
        currency: "INR",
      },
      similarity: 0.965,
      runner_up_similarity: 0.71,
      confidence_margin: 0.255,
      similarity_threshold: 0.9,
      margin_threshold: 0.03,
      color_similarity: 0.81,
      color_filter_candidate_count_before: 4,
      color_filter_candidate_count_after: 2,
      color_filter_threshold: 0.3,
      matching_method: "color_filter_then_clip",
    },
  };

  const shelf: CutoutItem = {
    id: "shelf_001",
    category: "shelf",
    crop_path: "uploads/cutouts/shelf_1.jpg",
    bbox_xyxy: [0, 180, 1000, 220],
    confidence: 0.88,
    row_number: 1,
    cluster_id: null,
    area_px: 40000,
  };

  const empty: CutoutItem = {
    id: "void_001",
    category: "empty_space",
    crop_path: "uploads/cutouts/void_1.jpg",
    bbox_xyxy: [500, 200, 600, 300],
    confidence: 0.91,
    row_number: 1,
    cluster_id: null,
    area_px: 10000,
  };

  const clusters: ClusterRow[] = [
    {
      cluster_id: 1,
      item_count: 2,
      similar_objects: [prod],
      similarity_percentage: 97.5,
      is_catalog_match: true,
      catalog_confidence: 0.965,
      catalog_product: {
        id: 42,
        sku: "SKU-COLGATE-150G",
        name: "Colgate Total 150g",
        category: "Oral Care",
        image_path: "uploads/products/colgate.jpg",
        price: 130,
        currency: "INR",
      },
    },
    {
      cluster_id: 2,
      item_count: 2,
      similar_objects: [
        {
          ...prod,
          id: "prod_002",
          crop_path: "uploads/cutouts/crop_2.jpg",
          cluster_id: 2,
          catalog_match: {
            status: "needs_review",
            reason: "below_similarity_threshold",
            top_candidate: {
              id: 43,
              sku: "SKU-AMUL-CHOCO",
              name: "Amul Milk Chocolate",
              category: "Chocolate",
              image_path: "uploads/products/amul.jpg",
              price: 50,
              currency: "INR",
            },
            similarity: 0.72,
            runner_up_similarity: 0.58,
            confidence_margin: 0.14,
            similarity_threshold: 0.9,
            margin_threshold: 0.03,
          },
        },
        {
          ...prod,
          id: "prod_003",
          crop_path: "uploads/cutouts/crop_3.jpg",
          cluster_id: 2,
          catalog_match: null,
        },
      ],
      similarity_percentage: 84.0,
      is_catalog_match: false,
      catalog_confidence: 0.72,
      catalog_product: null,
    },
  ];

  return {
    mockCutoutItemProduct: prod,
    mockCutoutItemShelf: shelf,
    mockCutoutItemEmpty: empty,
    mockClusters: clusters,
  };
});

vi.mock("@/lib/api", () => ({
  API_BASE_URL: "http://localhost:8000",
  api: {
    getOutputCutouts: vi.fn().mockResolvedValue({
      output_id: 1,
      source_filename: "shelf_test.jpg",
      total_count: 3,
      products: [mockCutoutItemProduct],
      shelves: [mockCutoutItemShelf],
      empty_spaces: [mockCutoutItemEmpty],
    }),
    getOutputAnalysis: vi.fn().mockResolvedValue({
      output_id: 1,
      source_filename: "shelf_test.jpg",
      planogram_name: "Test Planogram",
      shelf_name: "Shelf 1",
      shelf_dimensions: "120 cm x 180 cm",
      total_detections: 3,
      total_clusters: 2,
      matched_clusters_count: 1,
      catalog_confidence_threshold: 0.9,
      clusters: mockClusters,
    }),
    analyzeOutput: vi.fn(),
  },
  getImageUrl: vi.fn((path: string) => `http://localhost:8000/${path}`),
}));

describe("CutoutViewerModal Component", () => {
  it("renders the 3 required tabs: Products, Shelves, Empty Spaces", async () => {
    render(<CutoutViewerModal outputId={1} onClose={vi.fn()} />);

    expect(await screen.findByText("YOLO Bounding Box Cutouts Inspector")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Products/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Shelves \/ Rows/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Empty Spaces/i })).toBeInTheDocument();
  });

  it("switches to empty spaces tab and displays cutout counts", async () => {
    render(<CutoutViewerModal outputId={1} onClose={vi.fn()} />);

    const emptyTab = await screen.findByRole("button", { name: /Empty Spaces/i });
    fireEvent.click(emptyTab);

    expect(screen.getByText(/Showing/)).toBeInTheDocument();
    expect(screen.getByText(/empty spaces/)).toBeInTheDocument();
  });

  it("provides an individual download control for each visible cutout", async () => {
    render(<CutoutViewerModal outputId={1} onClose={vi.fn()} />);

    expect(await screen.findByRole("link", { name: "Download cutout #1" })).toBeInTheDocument();
  });
});

describe("AnalysisTable Component (4-Column Specification)", () => {
  it("renders exact 4 column headers", () => {
    render(<AnalysisTable clusters={mockClusters} threshold={0.9} />);

    expect(screen.getByText("Similar Objects")).toBeInTheDocument();
    expect(screen.getByText("Cluster Cohesion")).toBeInTheDocument();
    expect(
      screen.getByText("Is object similar to someone in the product catalog?")
    ).toBeInTheDocument();
    expect(screen.getByText("Similar Product")).toBeInTheDocument();
  });

  it("displays 'Yes' and product packshot image when match is >= 90%", () => {
    render(<AnalysisTable clusters={mockClusters} threshold={0.9} />);

    // Row 1 is a match
    const yesBadge = screen.getByTestId("catalog-match-yes");
    expect(yesBadge).toHaveTextContent("Yes");
    expect(screen.getByText("Colgate Total 150g")).toBeInTheDocument();
    expect(screen.getByText("SKU-COLGATE-150G")).toBeInTheDocument();
    expect(screen.getByTestId("catalog-product-matched")).toBeInTheDocument();
  });

  it("shows review state and no product image when a cluster is below 90%", () => {
    render(<AnalysisTable clusters={mockClusters} threshold={0.9} />);

    // Row 2 is not a match
    const noBadge = screen.getByTestId("catalog-match-no");
    expect(noBadge).toHaveTextContent("No");
    expect(screen.getByTestId("catalog-product-none")).toHaveTextContent(
      "No confirmed catalog product"
    );
  });

  it("filters table rows by Matched and Unmatched pills", () => {
    render(<AnalysisTable clusters={mockClusters} threshold={0.9} />);

    // Click Matched Catalog button
    fireEvent.click(screen.getByTestId("filter-matched-btn"));
    expect(screen.getByTestId("cluster-row-1")).toBeInTheDocument();
    expect(screen.queryByTestId("cluster-row-2")).not.toBeInTheDocument();

    // Click Unmatched button
    fireEvent.click(screen.getByTestId("filter-unmatched-btn"));
    expect(screen.queryByTestId("cluster-row-1")).not.toBeInTheDocument();
    expect(screen.getByTestId("cluster-row-2")).toBeInTheDocument();
  });

  it("shows every individual crop's nearest catalogue candidate in Product Match", () => {
    render(<AnalysisTable clusters={mockClusters} threshold={0.9} />);

    fireEvent.click(screen.getByTestId("filter-product-match-btn"));

    expect(screen.getByTestId("product-match-view")).toBeInTheDocument();
    expect(screen.getAllByTestId("product-match-item")).toHaveLength(3);
    expect(screen.getByText("Colgate Total 150g")).toBeInTheDocument();
    expect(screen.getByText("Amul Milk Chocolate")).toBeInTheDocument();
    expect(screen.getByText("96.5%")).toBeInTheDocument();
    expect(screen.getAllByText("Raw CLIP similarity")).toHaveLength(3);
    expect(screen.getByText("Color gate kept 2/4 candidates · candidate color match 81%")).toBeInTheDocument();
    expect(screen.getByText("72.0%")).toBeInTheDocument();
    expect(screen.getByText("No catalogue candidate")).toBeInTheDocument();
    expect(screen.getAllByTestId("product-match-status").map((badge) => badge.textContent)).toEqual([
      expect.stringContaining("Confirmed"),
      expect.stringContaining("Needs review"),
      expect.stringContaining("Needs review"),
    ]);
  });

  it("searches Product Match items by candidate SKU and returns to the unchanged cluster view", () => {
    render(<AnalysisTable clusters={mockClusters} threshold={0.9} />);

    fireEvent.click(screen.getByTestId("filter-product-match-btn"));
    fireEvent.change(screen.getByPlaceholderText("Search crop, product, SKU..."), {
      target: { value: "SKU-AMUL-CHOCO" },
    });
    expect(screen.getAllByTestId("product-match-item")).toHaveLength(1);
    expect(screen.getByText("Amul Milk Chocolate")).toBeInTheDocument();
    expect(screen.queryByText("Colgate Total 150g")).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId("filter-all-btn"));
    expect(screen.getByTestId("cluster-row-1")).toBeInTheDocument();
    expect(screen.getByTestId("cluster-row-2")).toBeInTheDocument();
  });
});
