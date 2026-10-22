import React from "react";
import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { ComplianceReportPanel } from "@/components/analysis/ComplianceReportPanel";

const { apiMock } = vi.hoisted(() => ({ apiMock: {
  getOutputCompliance: vi.fn(), getOutputCutouts: vi.fn(), updateComplianceIssue: vi.fn(), exportComplianceReport: vi.fn(),
} }));

vi.mock("@/lib/api", () => ({
  api: apiMock,
  getImageUrl: (path: string) => `http://localhost:8000/${path}`,
}));

const issue = {
  issue_id: "stable-issue-id", type: "missing_product", severity: "error", status: "open" as const,
  reason: "expected_slot_not_confirmed", recommended_action: "Restock the expected product.",
  row_index: 0, x_start_cm: 10, x_end_cm: 20, sku: "SKU-1", cutout_id: "cutout-1",
};

describe("ComplianceReportPanel", () => {
  it("shows location/evidence, filters findings, persists resolution, and exposes JSON export", async () => {
    apiMock.getOutputCompliance.mockResolvedValue({ output_id: 7, source_filename: "shelf.jpg", status: "needs_review", summary: { needs_review: 0 }, issues: [issue],
      layout_comparison: { coordinate_system: "normalized_shelf_width", row_order: "top_to_bottom", shelf_width_cm: 100, calibration_status: "calibrated", comparison_status: "ready", rows: [{ row_index: 0, row_number: 1, alignment_status: "aligned", expected_facings: [{ slot_id: "slot-1", sku: "SKU-1", status: "missing_product", ordinal_from_left: 1, ordinal_from_right: 1, normalized_start: 0, normalized_end: 0.2 }], observed_products: [], observed_empty_regions: [], expected_free_intervals: [{ normalized_start: 0.2, normalized_end: 1 }], observed_free_intervals: [{ normalized_start: 0, normalized_end: 1 }] }] } });
    apiMock.getOutputCutouts.mockResolvedValue({ products: [{ id: "cutout-1", bbox_xyxy: [10, 20, 30, 40] }] });
    apiMock.updateComplianceIssue.mockResolvedValue({ issue_id: issue.issue_id, status: "resolved" });
    render(<ComplianceReportPanel output={{ id: 7, annotated_image_path: "uploads/a.jpg", source_filename: "shelf.jpg" } as never} />);
    const image = await screen.findByAltText("Annotated evidence for shelf.jpg");
    Object.defineProperty(image, "naturalWidth", { configurable: true, value: 100 });
    Object.defineProperty(image, "naturalHeight", { configurable: true, value: 100 });
    fireEvent.load(image);
    expect(await screen.findAllByText("Row 1")).toHaveLength(2);
    expect(screen.getByTestId("normalized-layout-comparison")).toHaveTextContent("Expected 1 facings · detected 0 products");
    expect(screen.getByTestId("normalized-layout-comparison")).toHaveTextContent("1. SKU-1 · missing product");
    expect(screen.getByText("10.0–20.0 cm from left")).toBeInTheDocument();
    expect(screen.getByText("Restock the expected product.")).toBeInTheDocument();
    fireEvent.click(screen.getByTestId("compliance-issue"));
    expect(await screen.findByLabelText("Selected issue detection overlay")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Filter by issue status"), { target: { value: "resolved" } });
    expect(screen.getByText("No findings match these filters.")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Filter by issue status"), { target: { value: "all" } });
    fireEvent.change(screen.getByLabelText(`Operator note for ${issue.issue_id}`), { target: { value: "Restocked on shift." } });
    fireEvent.click(screen.getByRole("button", { name: "Save note" }));
    await waitFor(() => expect(apiMock.updateComplianceIssue).toHaveBeenCalledWith(7, issue.issue_id, { status: "open", note: "Restocked on shift." }));
    fireEvent.click(await screen.findByRole("button", { name: "Resolve" }));
    await waitFor(() => expect(apiMock.updateComplianceIssue).toHaveBeenCalledWith(7, issue.issue_id, { status: "resolved", note: "Restocked on shift." }));
    expect(await screen.findByRole("button", { name: "Export JSON" })).toBeInTheDocument();
  });
});
