"use client";

import { useState } from "react";
import {
  Sliders,
  Package,
  Plus,
  Trash2,
  Search,
  Sparkles,
  Box,
  Layers,
} from "lucide-react";
import { Shelf, Placement, Product, Planogram } from "@/types";
import { getImageUrl } from "@/lib/api";

interface ContextPanelProps {
  planogram: Planogram | null;
  selectedShelf: Shelf | null;
  selectedPlacement: Placement | null;
  products: Product[];
  onUpdateShelf: (shelfId: number, data: Partial<Shelf>) => void;
  onDeleteShelf: (shelfId: number) => void;
  onUpdatePlacement: (placementId: number, data: Partial<Placement>) => void;
  onDeletePlacement: (placementId: number) => void;
  onOpenAddProduct: () => void;
  onSeedCatalogue: () => void;
  onAddProductToRow: (shelfId: number, rowIndex: number, product: Product) => void;
}

export function ContextPanel({
  planogram,
  selectedShelf,
  selectedPlacement,
  products,
  onUpdateShelf,
  onDeleteShelf,
  onUpdatePlacement,
  onDeletePlacement,
  onOpenAddProduct,
  onSeedCatalogue,
  onAddProductToRow,
}: ContextPanelProps) {
  const [activeTab, setActiveTab] = useState<"properties" | "library">("properties");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  // Calculate shelf row heights
  const usableH = selectedShelf
    ? selectedShelf.total_height_cm - (selectedShelf.has_plinth ? selectedShelf.plinth_height_cm : 0)
    : 0;
  const defaultH = selectedShelf ? Math.max(10, usableH / selectedShelf.row_count) : 10;
  const shelfRowHeights = selectedShelf
    ? Array.from({ length: selectedShelf.row_count }).map((_, idx) => {
        if (selectedShelf.row_heights && selectedShelf.row_heights.length === selectedShelf.row_count) {
          const val = selectedShelf.row_heights[idx];
          if (typeof val === "number" && val > 0) return val;
        }
        return defaultH;
      })
    : [];

  // Filter products
  const categories = ["All", ...Array.from(new Set(products.map((p) => p.category || "General")))];
  const filteredProducts = products.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.sku.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === "All" || p.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <aside
      className="w-80 bg-[#13161c] border-l border-[#262b36] flex flex-col h-full select-none text-xs"
      data-testid="designer-context-panel"
    >
      {/* Tabs Header */}
      <div className="h-10 px-2 border-b border-[#262b36] flex items-center bg-[#1a1e26] shrink-0 gap-1">
        <button
          onClick={() => setActiveTab("properties")}
          className={`flex-1 py-1.5 rounded font-semibold text-[11px] uppercase tracking-wider flex items-center justify-center gap-1.5 transition-all ${
            activeTab === "properties"
              ? "bg-[#13161c] text-amber-400 border border-[#262b36] shadow-xs"
              : "text-gray-400 hover:text-gray-200"
          }`}
          data-testid="tab-properties"
        >
          <Sliders className="w-3.5 h-3.5" />
          <span>Properties</span>
        </button>

        <button
          onClick={() => setActiveTab("library")}
          className={`flex-1 py-1.5 rounded font-semibold text-[11px] uppercase tracking-wider flex items-center justify-center gap-1.5 transition-all ${
            activeTab === "library"
              ? "bg-[#13161c] text-amber-400 border border-[#262b36] shadow-xs"
              : "text-gray-400 hover:text-gray-200"
          }`}
          data-testid="tab-library"
        >
          <Package className="w-3.5 h-3.5" />
          <span>Product Library ({products.length})</span>
        </button>
      </div>

      {/* Tab 1: Properties Content */}
      {activeTab === "properties" && (
        <div className="flex-1 overflow-y-auto p-4 space-y-4" data-testid="properties-panel">
          {/* Case A: Placement Selected */}
          {selectedPlacement ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-[#262b36]">
                <div className="flex items-center gap-1.5 font-bold text-gray-200">
                  <Package className="w-4 h-4 text-emerald-400" />
                  <span>Selected Placement</span>
                </div>
                <button
                  onClick={() => onDeletePlacement(selectedPlacement.id)}
                  className="p-1 rounded text-red-400 hover:bg-red-950/40"
                  title="Remove placement"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Product Card Preview */}
              <div className="p-3 rounded-lg bg-[#1a1e26] border border-[#262b36] flex gap-3 items-center">
                <div className="w-14 h-14 rounded bg-white p-1 flex items-center justify-center shrink-0 border border-gray-300">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={getImageUrl(selectedPlacement.product.image_path)}
                    alt={selectedPlacement.product.name}
                    className="max-h-full max-w-full object-contain"
                  />
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="text-sm font-semibold text-gray-100 truncate">
                    {selectedPlacement.product.name}
                  </h4>
                  <div className="text-[10px] text-amber-400 font-mono font-bold">
                    {selectedPlacement.product.sku}
                  </div>
                  <div className="text-[11px] text-gray-400">
                    ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¹{selectedPlacement.product.price.toFixed(2)} Ã¢â‚¬Â¢ {selectedPlacement.product.category}
                  </div>
                </div>
              </div>

              {/* Physical Dimensions */}
              <div className="p-3 rounded-lg bg-[#1a1e26] border border-[#262b36] space-y-2">
                <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wider">
                  Physical Dimensions (cm)
                </span>
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="p-1.5 rounded bg-[#13161c] border border-[#262b36]">
                    <span className="text-[9px] text-gray-400 block">Width</span>
                    <span className="font-mono font-bold text-gray-200" data-testid="prop-width">
                      {selectedPlacement.product.width_cm} cm
                    </span>
                  </div>
                  <div className="p-1.5 rounded bg-[#13161c] border border-[#262b36]">
                    <span className="text-[9px] text-gray-400 block">Height</span>
                    <span className="font-mono font-bold text-gray-200" data-testid="prop-height">
                      {selectedPlacement.product.height_cm} cm
                    </span>
                  </div>
                  <div className="p-1.5 rounded bg-[#13161c] border border-[#262b36]">
                    <span className="text-[9px] text-gray-400 block">Depth</span>
                    <span className="font-mono font-bold text-gray-200" data-testid="prop-depth">
                      {selectedPlacement.product.depth_cm} cm
                    </span>
                  </div>
                </div>
              </div>

              {/* Placement Row & Position Controls */}
              <div className="p-3 rounded-lg bg-[#1a1e26] border border-[#262b36] space-y-3">
                <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wider">
                  Placement Position
                </span>

                <div>
                  <label className="text-gray-300 block mb-1">Target Shelf Row:</label>
                  <select
                    value={selectedPlacement.row_index}
                    onChange={(e) =>
                      onUpdatePlacement(selectedPlacement.id, {
                        row_index: parseInt(e.target.value),
                      })
                    }
                    className="w-full px-2.5 py-1.5 rounded bg-[#13161c] border border-[#262b36] text-gray-100 text-xs focus:border-amber-500 font-mono"
                  >
                    {selectedShelf &&
                      Array.from({ length: selectedShelf.row_count }).map((_, rIdx) => (
                        <option key={rIdx} value={rIdx}>
                          Row {rIdx + 1}
                        </option>
                      ))}
                  </select>
                </div>

                <div>
                  <label className="text-gray-300 block mb-1">Horizontal Offset (cm from left):</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      step="0.5"
                      min="0"
                      value={selectedPlacement.x_offset_cm}
                      onChange={(e) =>
                        onUpdatePlacement(selectedPlacement.id, {
                          x_offset_cm: parseFloat(e.target.value) || 0,
                        })
                      }
                      className="flex-1 px-2.5 py-1.5 rounded bg-[#13161c] border border-[#262b36] text-gray-100 text-xs focus:border-amber-500 font-mono"
                    />
                    <span className="text-gray-400 text-xs font-mono">cm</span>
                  </div>
                </div>

                <div>
                  <label className="text-gray-300 block mb-1">Facing Count (Adjacent Units):</label>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() =>
                        onUpdatePlacement(selectedPlacement.id, {
                          facing_count: Math.max(1, selectedPlacement.facing_count - 1),
                        })
                      }
                      disabled={selectedPlacement.facing_count <= 1}
                      className="w-7 h-7 rounded bg-[#262b36] text-gray-200 hover:bg-[#323947] disabled:opacity-40 font-bold"
                    >
                      -
                    </button>
                    <span className="font-mono text-sm font-bold text-amber-400">
                      {selectedPlacement.facing_count}
                    </span>
                    <button
                      onClick={() =>
                        onUpdatePlacement(selectedPlacement.id, {
                          facing_count: selectedPlacement.facing_count + 1,
                        })
                      }
                      className="w-7 h-7 rounded bg-[#262b36] text-gray-200 hover:bg-[#323947] font-bold"
                    >
                      +
                    </button>
                    <span className="text-gray-400 text-[10px]">
                      Total width: {(selectedPlacement.product.width_cm * selectedPlacement.facing_count).toFixed(1)} cm
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ) : selectedShelf ? (
            /* Case B: Shelf Selected */
            <div className="space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-[#262b36]">
                <div className="flex items-center gap-1.5 font-bold text-gray-200">
                  <Box className="w-4 h-4 text-blue-400" />
                  <span>Shelf Unit Properties</span>
                </div>
                <button
                  onClick={() => onDeleteShelf(selectedShelf.id)}
                  className="p-1 rounded text-red-400 hover:bg-red-950/40"
                  title="Delete shelf"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Shelf Name */}
              <div>
                <label className="text-gray-300 block mb-1 font-semibold">Shelf Unit Name:</label>
                <input
                  type="text"
                  value={selectedShelf.name}
                  onChange={(e) => onUpdateShelf(selectedShelf.id, { name: e.target.value })}
                  className="w-full px-2.5 py-1.5 rounded bg-[#13161c] border border-[#262b36] text-gray-100 text-xs focus:border-amber-500 font-semibold"
                />
              </div>

              {/* Shelf Dimensions in cm */}
              <div className="p-3 rounded-lg bg-[#1a1e26] border border-[#262b36] space-y-3">
                <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wider">
                  Physical Dimensions (cm)
                </span>

                <div>
                  <div className="flex justify-between text-gray-300 mb-1">
                    <span>Usable Width:</span>
                    <span className="font-mono font-bold text-amber-400" data-testid="shelf-width-label">
                      {selectedShelf.width_cm} cm
                    </span>
                  </div>
                  <input
                    type="number"
                    step="1"
                    min="20"
                    max="500"
                    value={selectedShelf.width_cm}
                    onChange={(e) =>
                      onUpdateShelf(selectedShelf.id, {
                        width_cm: parseFloat(e.target.value) || 20,
                      })
                    }
                    className="w-full px-2.5 py-1.5 rounded bg-[#13161c] border border-[#262b36] text-gray-100 text-xs focus:border-amber-500 font-mono"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-gray-300 mb-1">
                    <span>Total Height:</span>
                    <span className="font-mono font-bold text-amber-400">{selectedShelf.total_height_cm} cm</span>
                  </div>
                  <input
                    type="number"
                    step="1"
                    min="30"
                    max="500"
                    value={selectedShelf.total_height_cm}
                    onChange={(e) =>
                      onUpdateShelf(selectedShelf.id, {
                        total_height_cm: parseFloat(e.target.value) || 30,
                      })
                    }
                    className="w-full px-2.5 py-1.5 rounded bg-[#13161c] border border-[#262b36] text-gray-100 text-xs focus:border-amber-500 font-mono"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-gray-300 mb-1">
                    <span>Shelf Depth:</span>
                    <span className="font-mono font-bold text-amber-400">{selectedShelf.depth_cm} cm</span>
                  </div>
                  <input
                    type="number"
                    step="1"
                    min="10"
                    max="200"
                    value={selectedShelf.depth_cm}
                    onChange={(e) =>
                      onUpdateShelf(selectedShelf.id, {
                        depth_cm: parseFloat(e.target.value) || 10,
                      })
                    }
                    className="w-full px-2.5 py-1.5 rounded bg-[#13161c] border border-[#262b36] text-gray-100 text-xs focus:border-amber-500 font-mono"
                  />
                </div>
              </div>

              {/* Row Count (1 to 12) */}
              <div className="p-3 rounded-lg bg-[#1a1e26] border border-[#262b36] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wider">
                    Shelf Rows (1 to 12)
                  </span>
                  <span className="font-mono font-bold text-amber-400" data-testid="shelf-rows-label">
                    {selectedShelf.row_count} rows
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <input
                    type="range"
                    min="1"
                    max="12"
                    data-testid="input-shelf-row-count-slider"
                    value={selectedShelf.row_count}
                    onChange={(e) =>
                      onUpdateShelf(selectedShelf.id, {
                        row_count: parseInt(e.target.value),
                      })
                    }
                    className="flex-1 accent-amber-500"
                  />
                  <input
                    type="number"
                    min="1"
                    max="12"
                    data-testid="input-shelf-row-count-number"
                    value={selectedShelf.row_count}
                    onChange={(e) =>
                      onUpdateShelf(selectedShelf.id, {
                        row_count: Math.min(12, Math.max(1, parseInt(e.target.value) || 1)),
                      })
                    }
                    className="w-12 text-center text-xs font-bold text-amber-400 bg-[#13161c] px-1 py-1 rounded border border-[#262b36] font-mono"
                  />
                </div>
                <p className="text-[10px] text-gray-400">
                  Reducing row count protects populated rows from accidental deletion.
                </p>
              </div>

              {/* Bottom Plinth */}
              <div className="p-3 rounded-lg bg-[#1a1e26] border border-[#262b36] space-y-2">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-gray-200 font-semibold block">Bottom Plinth</span>
                    <span className="text-[10px] text-gray-400">Base elevation fixture</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={selectedShelf.has_plinth}
                    onChange={(e) =>
                      onUpdateShelf(selectedShelf.id, {
                        has_plinth: e.target.checked,
                      })
                    }
                    className="w-4 h-4 rounded accent-amber-500 cursor-pointer"
                  />
                </div>

                {selectedShelf.has_plinth && (
                  <div className="pt-2 border-t border-[#262b36] flex items-center justify-between">
                    <span className="text-gray-300">Plinth Height (cm):</span>
                    <input
                      type="number"
                      step="0.5"
                      min="1"
                      max={selectedShelf.total_height_cm - 10}
                      value={selectedShelf.plinth_height_cm}
                      onChange={(e) =>
                        onUpdateShelf(selectedShelf.id, {
                          plinth_height_cm: parseFloat(e.target.value) || 0,
                        })
                      }
                      className="w-20 px-2 py-1 rounded bg-[#13161c] border border-[#262b36] text-gray-100 text-xs font-mono"
                    />
                  </div>
                )}
              </div>
            </div>
          ) : (
            /* Case C: Planogram Root Selected */
            <div className="space-y-4 text-center py-6">
              <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center mx-auto text-amber-400">
                <Layers className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-bold text-gray-100 text-sm">{planogram?.name}</h3>
                <p className="text-[11px] text-gray-400 mt-1">
                  Select a shelf or a product placement in the scene or canvas to inspect and edit its physical properties.
                </p>
              </div>
              <div className="p-3 rounded-lg bg-[#1a1e26] border border-[#262b36] text-left space-y-1.5 text-[11px]">
                <div className="flex justify-between text-gray-400">
                  <span>Total Shelf Fixtures:</span>
                  <span className="text-gray-200 font-bold">{planogram?.shelves.length || 0}</span>
                </div>
                <div className="flex justify-between text-gray-400">
                  <span>Total Placed Items:</span>
                  <span className="text-gray-200 font-bold">
                    {planogram?.shelves.reduce((acc, s) => acc + (s.placements?.length || 0), 0) || 0}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Product Library Content */}
      {activeTab === "library" && (
        <div className="flex-1 flex flex-col h-full overflow-hidden" data-testid="product-library-panel">
          {/* Search & Actions Bar */}
          <div className="p-3 border-b border-[#262b36] space-y-2 shrink-0">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-gray-400 absolute left-2.5 top-2.5" />
              <input
                type="text"
                placeholder="Search name or SKU..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-[#1a1e26] border border-[#262b36] text-gray-100 text-xs focus:border-amber-500"
              />
            </div>

            {/* Category Filter Pills */}
            <div className="flex gap-1 overflow-x-auto pb-1 text-[10px]">
              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`px-2 py-0.5 rounded-full whitespace-nowrap transition-colors ${
                    selectedCategory === cat
                      ? "bg-amber-500 text-gray-950 font-bold"
                      : "bg-[#1a1e26] text-gray-400 hover:text-gray-200"
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>

            {/* Add Product Button */}
            <div className="flex gap-2">
              <button
                onClick={onOpenAddProduct}
                data-testid="add-product-btn"
                className="flex-1 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-600 text-gray-950 font-bold text-xs flex items-center justify-center gap-1.5 shadow-sm"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Product</span>
              </button>

              {products.length === 0 && (
                <button
                  onClick={onSeedCatalogue}
                  className="px-2.5 py-1.5 rounded-lg bg-[#1a1e26] hover:bg-[#222733] border border-[#262b36] text-amber-400 text-xs font-semibold flex items-center gap-1"
                  title="Seed sample products"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Seed</span>
                </button>
              )}
            </div>
          </div>

          {/* Product Items List */}
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {filteredProducts.map((product) => (
              <div
                key={product.id}
                draggable
                onDragStart={(e) => {
                  e.dataTransfer.setData(
                    "application/json",
                    JSON.stringify({
                      type: "new_product",
                      product,
                    })
                  );
                }}
                className="p-2.5 rounded-lg bg-[#1a1e26] border border-[#262b36] hover:border-amber-500/50 hover:bg-[#222733] transition-all cursor-grab active:cursor-grabbing flex gap-2.5 items-center group"
                data-testid={`catalogue-product-${product.sku}`}
              >
                {/* Thumbnail packshot */}
                <div className="w-12 h-14 rounded bg-white p-1 flex items-center justify-center shrink-0 border border-gray-300 shadow-xs">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={getImageUrl(product.image_path)}
                    alt={product.name}
                    className="max-h-full max-w-full object-contain"
                  />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono text-amber-400 font-bold truncate">
                      {product.sku}
                    </span>
                    <span className="text-[10px] font-mono text-gray-300">
                      ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¹{product.price.toFixed(0)}
                    </span>
                  </div>
                  <h4 className="text-xs font-semibold text-gray-100 truncate mt-0.5">
                    {product.name}
                  </h4>
                  <div className="text-[10px] text-gray-400 font-mono mt-0.5">
                    {product.width_cm}{" \u00D7 "}{product.height_cm} cm
                  </div>
                </div>

                {/* Accessible Quick Add to Selected Shelf Row */}
                {selectedShelf && selectedShelf.row_count > 0 && (
                  <button
                    onClick={() => onAddProductToRow(selectedShelf.id, 0, product)}
                    className="opacity-0 group-hover:opacity-100 p-1.5 rounded bg-amber-500 text-gray-950 font-bold hover:bg-amber-400 transition-opacity"
                    title={`Add ${product.name} to Row 1`}
                  >
                    <Plus className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            ))}

            {filteredProducts.length === 0 && (
              <div className="p-6 text-center text-gray-400 text-xs">
                <p>No catalogue items found.</p>
                <button
                  onClick={onOpenAddProduct}
                  className="mt-2 text-amber-400 hover:text-amber-300 font-semibold flex items-center gap-1 mx-auto"
                >
                  <Plus className="w-3 h-3" />
                  <span>Create Product</span>
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </aside>
  );
}
