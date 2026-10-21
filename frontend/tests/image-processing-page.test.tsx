import React from "react";
import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

vi.mock("@/lib/api", () => ({
  api: {
    getInputImages: vi.fn().mockResolvedValue([]),
    getPlanograms: vi.fn().mockResolvedValue([]),
    getProcessedOutputs: vi.fn().mockResolvedValue([]),
  },
  getImageUrl: vi.fn((path: string) => path),
  downloadProcessedOutputs: vi.fn(),
}));

import InputImagesPage from "@/app/input-images/page";
import OutputsPage from "@/app/outputs/page";

describe("Image processing pages", () => {
  it("renders the one-image-at-a-time input empty state", async () => {
    render(<InputImagesPage />);
    expect(await screen.findByText("No images yet")).toBeInTheDocument();
    expect(screen.getByText(/Assign one shelf photo to one saved planogram shelf/i)).toBeInTheDocument();
    expect(screen.getByText("Select an input image to continue.")).toBeInTheDocument();
  });

  it("renders the output empty state", async () => {
    render(<OutputsPage />);
    expect(await screen.findByText("No processed outputs")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Export" })).toBeDisabled();
  });
});
