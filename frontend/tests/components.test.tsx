import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

import { ShelfCanvas } from "@/components/designer/ShelfCanvas";
import { AddShelfModal } from "@/components/designer/AddShelfModal";
import { AddProductModal } from "@/components/designer/AddProductModal";
import { ContextPanel } from "@/components/designer/ContextPanel";
import { Shelf, Product } from "@/types";

const mockProduct: Product = {
  id: 1,
  sku: "DEMO-DRK-001",
  name: "Citrus Sparkling Drink",
  category: "Beverages",
  description: "Test drink",
  price: 35.0,
  currency: "INR",
  width_cm: 6.5,
  height_cm: 12.2,
  depth_cm: 6.5,
  image_path: "uploads/sample.svg",
  is_sample: true,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

const mockShelf: Shelf = {
  id: 1,
  planogram_id: 1,
  name: "Shelf 01",
  width_cm: 120.0,
  total_height_cm: 180.0,
  depth_cm: 40.0,
  row_count: 4,
  has_plinth: true,
  plinth_height_cm: 15.0,
  order_index: 0,
  placements: [],
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

describe("ShelfCanvas Component", () => {
  it("renders empty state with Add Shelf action when there are no shelves", () => {
    const onOpenAddShelf = vi.fn();
    render(
      <ShelfCanvas
        shelves={[]}
        selectedShelfId={null}
        selectedPlacementId={null}
        onSelectShelf={vi.fn()}
        onSelectPlacement={vi.fn()}
        onOpenAddShelf={onOpenAddShelf}
        onDropProductOnRow={vi.fn()}
        onMovePlacement={vi.fn()}
        onDeletePlacement={vi.fn()}
        collisionWarning={null}
      />
    );

    expect(screen.getByTestId("shelf-canvas-empty")).toBeInTheDocument();
    expect(screen.getByText("Shelf Canvas is Empty")).toBeInTheDocument();
    const addBtn = screen.getByTestId("canvas-add-shelf-btn");
    expect(addBtn).toBeInTheDocument();
    fireEvent.click(addBtn);
    expect(onOpenAddShelf).toHaveBeenCalledTimes(1);
  });

  it("renders shelf with physical cm dimensions and formal brackets when shelf exists", () => {
    render(
      <ShelfCanvas
        shelves={[mockShelf]}
        selectedShelfId={mockShelf.id}
        selectedPlacementId={null}
        onSelectShelf={vi.fn()}
        onSelectPlacement={vi.fn()}
        onOpenAddShelf={vi.fn()}
        onDropProductOnRow={vi.fn()}
        onMovePlacement={vi.fn()}
        onDeletePlacement={vi.fn()}
        collisionWarning={null}
      />
    );

    expect(screen.getByTestId("shelf-canvas")).toBeInTheDocument();
    expect(screen.getByText(/Total Usable Width: 120 cm/i)).toBeInTheDocument();
    expect(screen.getByText(/Total 180cm/i)).toBeInTheDocument();
    expect(screen.getByText(/Base Plinth Fixture \(15 cm\)/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Row 1/i).length).toBeGreaterThan(0);
  });

  it("enforces row minimum height based on placed products and displays Min badge", () => {
    const shelfWithPlacement: Shelf = {
      ...mockShelf,
      placements: [
        {
          id: 101,
          shelf_id: mockShelf.id,
          product_id: mockProduct.id,
          row_index: 0,
          x_offset_cm: 0,
          facing_count: 1,
          product: mockProduct, // height_cm: 12.2
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
    };

    render(
      <ShelfCanvas
        shelves={[shelfWithPlacement]}
        selectedShelfId={shelfWithPlacement.id}
        selectedPlacementId={null}
        onSelectShelf={vi.fn()}
        onSelectPlacement={vi.fn()}
        onOpenAddShelf={vi.fn()}
        onDropProductOnRow={vi.fn()}
        onMovePlacement={vi.fn()}
        onDeletePlacement={vi.fn()}
        collisionWarning={null}
      />
    );

    // Checks that the Min badge is displayed for the placed product (12.2cm + 3.0cm headroom = 15.2cm)
    expect(screen.getByText(/Min 15.2cm/i)).toBeInTheDocument();
  });
  it("clicking shelf row in ShelfCanvas triggers onSelectRow callback", () => {
    const onSelectRow = vi.fn();
    render(
      <ShelfCanvas
        shelves={[mockShelf]}
        selectedShelfId={mockShelf.id}
        selectedPlacementId={null}
        selectedRowIndex={0}
        onSelectShelf={vi.fn()}
        onSelectPlacement={vi.fn()}
        onSelectRow={onSelectRow}
        onOpenAddShelf={vi.fn()}
        onDropProductOnRow={vi.fn()}
        onMovePlacement={vi.fn()}
        onDeletePlacement={vi.fn()}
        collisionWarning={null}
      />
    );

    const row2 = screen.getByTestId("shelf-row-1");
    fireEvent.click(row2);
    expect(onSelectRow).toHaveBeenCalledWith(1);
  });
});

describe("AddShelfModal Component", () => {
  it("validates shelf name and positive dimensions", async () => {
    const onAdd = vi.fn().mockResolvedValue(undefined);
    render(
      <AddShelfModal
        isOpen={true}
        onClose={vi.fn()}
        onAdd={onAdd}
        defaultIndex={1}
      />
    );

    expect(screen.getByText("Add New Shelf Unit")).toBeInTheDocument();
    const submitBtn = screen.getByText("Add Shelf to Canvas");
    
    await fireEvent.click(submitBtn);

    expect(onAdd).toHaveBeenCalledWith(
      expect.objectContaining({
        name: "Shelf 01",
        width_cm: 120,
        total_height_cm: 180,
        row_count: 4,
      })
    );
  });
});

describe("AddProductModal Component", () => {
  it("renders product input fields with cm units", () => {
    render(
      <AddProductModal
        isOpen={true}
        onClose={vi.fn()}
        onProductCreated={vi.fn()}
      />
    );

    expect(screen.getByText("Add Catalogue Product")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("e.g. BEV-001")).toBeInTheDocument();
    expect(screen.getByText("Physical Dimensions (cm)")).toBeInTheDocument();
  });
});

describe("ContextPanel Component", () => {
  it("displays shelf properties and cm dimensions when shelf is selected", () => {
    render(
      <ContextPanel
        planogram={{ id: 1, name: "Test Planogram", shelves: [mockShelf], created_at: "", updated_at: "" }}
        selectedShelf={mockShelf}
        selectedPlacement={null}
        products={[mockProduct]}
        onUpdateShelf={vi.fn()}
        onDeleteShelf={vi.fn()}
        onUpdatePlacement={vi.fn()}
        onDeletePlacement={vi.fn()}
        onOpenAddProduct={vi.fn()}
        onSeedCatalogue={vi.fn()}
        onAddProductToRow={vi.fn()}
      />
    );

    expect(screen.getByTestId("shelf-width-label")).toHaveTextContent("120 cm");
    expect(screen.getByTestId("shelf-rows-label")).toHaveTextContent("4 rows");
  });

  it("switches to product library tab and lists products", () => {
    render(
      <ContextPanel
        planogram={{ id: 1, name: "Test Planogram", shelves: [mockShelf], created_at: "", updated_at: "" }}
        selectedShelf={mockShelf}
        selectedPlacement={null}
        products={[mockProduct]}
        onUpdateShelf={vi.fn()}
        onDeleteShelf={vi.fn()}
        onUpdatePlacement={vi.fn()}
        onDeletePlacement={vi.fn()}
        onOpenAddProduct={vi.fn()}
        onSeedCatalogue={vi.fn()}
        onAddProductToRow={vi.fn()}
      />
    );

    const libTab = screen.getByTestId("tab-library");
    fireEvent.click(libTab);

    expect(screen.getByTestId(`catalogue-product-${mockProduct.sku}`)).toBeInTheDocument();
    expect(screen.getByText("Citrus Sparkling Drink")).toBeInTheDocument();
    expect(screen.getByText("6.5 × 12.2 cm")).toBeInTheDocument();
  });
});
