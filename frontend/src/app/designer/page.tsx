"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  Save,
  Download,
  Plus,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  ArrowLeft,
} from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Planogram, Shelf, Placement, Product } from "@/types";
import { Outliner } from "@/components/designer/Outliner";
import { ShelfCanvas } from "@/components/designer/ShelfCanvas";
import { ContextPanel } from "@/components/designer/ContextPanel";
import { AddShelfModal } from "@/components/designer/AddShelfModal";
import { AddProductModal } from "@/components/designer/AddProductModal";
import { ExportModal } from "@/components/designer/ExportModal";

function DesignerContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const planogramIdParam = searchParams.get("id");

  // Core Data State
  const [planogram, setPlanogram] = useState<Planogram | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState<string | null>(null);

  // Selection State
  const [selectedShelfId, setSelectedShelfId] = useState<number | null>(null);
  const [selectedPlacementId, setSelectedPlacementId] = useState<number | null>(null);

  // Save State (clear feedback: Saved / Unsaved changes / Saving / Save failed)
  const [saveStatus, setSaveStatus] = useState<"saved" | "unsaved" | "saving" | "error">("saved");

  // Modals
  const [showAddShelfModal, setShowAddShelfModal] = useState(false);
  const [showAddProductModal, setShowAddProductModal] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);

  // Collision Warning Floating Banner
  const [collisionWarning, setCollisionWarning] = useState<string | null>(null);

  useEffect(() => {
    let ignore = false;
    const initData = async () => {
      try {
        setPageError(null);

        // Load products
        let prodList = await api.getProducts();
        if (prodList.length === 0) {
          try {
            await api.seedCatalogue();
            prodList = await api.getProducts();
          } catch {
            // Non-blocking
          }
        }
        if (!ignore) {
          setProducts(prodList);
        }

        let activeId = planogramIdParam ? parseInt(planogramIdParam) : null;
        if (!activeId) {
          const summaries = await api.getPlanograms();
          if (summaries.length > 0) {
            activeId = summaries[0].id;
          } else {
            const newP = await api.createPlanogram({ name: "Primary Retail Bay" });
            activeId = newP.id;
          }
          router.replace(`/designer?id=${activeId}`);
        }

        const pData = await api.getPlanogram(activeId);
        if (!ignore) {
          setPlanogram(pData);
          if (pData.shelves && pData.shelves.length > 0) {
            setSelectedShelfId(pData.shelves[0].id);
          }
          setSaveStatus("saved");
        }
      } catch (err: unknown) {
        if (!ignore) {
          const msg = err instanceof Error ? err.message : String(err);
          setPageError(msg || "Failed to load planogram workspace.");
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    };

    void initData();
    return () => {
      ignore = true;
    };
  }, [planogramIdParam, router]);

  // Refresh planogram from server (source of truth)
  const refreshPlanogram = async () => {
    if (!planogram) return;
    try {
      const refreshed = await api.getPlanogram(planogram.id);
      setPlanogram(refreshed);
      setSaveStatus("saved");
    } catch (err: unknown) {
      console.error("Refresh error:", err);
    }
  };

  // Add Shelf
  const handleAddShelf = async (shelfData: Partial<Shelf>) => {
    if (!planogram) return;
    try {
      const created = await api.createShelf(planogram.id, shelfData);
      const updatedShelves = [...(planogram.shelves || []), created];
      setPlanogram({ ...planogram, shelves: updatedShelves });
      setSelectedShelfId(created.id);
      setSelectedPlacementId(null);
      setSaveStatus("saved");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      alert(`Error creating shelf: ${msg}`);
    }
  };

  // Update Shelf Properties
  const handleUpdateShelf = async (shelfId: number, data: Partial<Shelf>) => {
    if (!planogram) return;
    try {
      setSaveStatus("saving");
      const updated = await api.updateShelf(shelfId, data);
      const updatedShelves = planogram.shelves.map((s) => (s.id === shelfId ? updated : s));
      setPlanogram({ ...planogram, shelves: updatedShelves });
      setSaveStatus("saved");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setSaveStatus("error");
      alert(`Shelf update rejected: ${msg}`);
      await refreshPlanogram();
    }
  };

  // Delete Shelf
  const handleDeleteShelf = async (shelfId: number) => {
    if (!planogram) return;
    try {
      await api.deleteShelf(shelfId);
      const remaining = planogram.shelves.filter((s) => s.id !== shelfId);
      setPlanogram({ ...planogram, shelves: remaining });
      setSelectedShelfId(remaining[0]?.id || null);
      setSelectedPlacementId(null);
      setSaveStatus("saved");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      alert(`Error deleting shelf: ${msg}`);
    }
  };

  // Drop Product on Row (Drag from catalogue or quick add)
  const handleDropProductOnRow = async (
    shelfId: number,
    rowIndex: number,
    product: Product
  ) => {
    if (!planogram) return;
    const shelf = planogram.shelves.find((s) => s.id === shelfId);
    if (!shelf) return;

    // Calculate next available x offset in cm
    const rowPlacements = (shelf.placements || []).filter((p) => p.row_index === rowIndex);
    const usedWidth = rowPlacements.reduce((acc, p) => acc + p.product.width_cm * p.facing_count, 0);
    const nextX = Math.round(usedWidth * 10) / 10;

    try {
      // Ensure row height is at least product.height_cm
      const usableH = shelf.total_height_cm - (shelf.has_plinth ? shelf.plinth_height_cm : 0);
      const defaultEqualH = Math.max(10, usableH / shelf.row_count);
      const currentHeights = shelf.row_heights && shelf.row_heights.length === shelf.row_count
        ? [...shelf.row_heights]
        : Array(shelf.row_count).fill(defaultEqualH);

      if (currentHeights[rowIndex] < product.height_cm) {
        currentHeights[rowIndex] = Number(product.height_cm.toFixed(1));
        await api.updateShelf(shelfId, { row_heights: currentHeights });
      }
      setCollisionWarning(null);
      setSaveStatus("saving");
      const newPlacement = await api.createPlacement(shelfId, {
        product_id: product.id,
        row_index: rowIndex,
        x_offset_cm: nextX,
        facing_count: 1,
      });

      // Update local state and source of truth
      await refreshPlanogram();
      setSelectedShelfId(shelfId);
      setSelectedPlacementId(newPlacement.id);
      setSaveStatus("saved");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setSaveStatus("error");
      setCollisionWarning(msg || "Cannot place product: collision or exceeds width.");
      setTimeout(() => setCollisionWarning(null), 5000);
    }
  };

  // Move or update Placement
  const handleMovePlacement = async (
    placementId: number,
    newRowIndex: number,
    newXOffsetCm: number
  ) => {
    try {
      setCollisionWarning(null);
      setSaveStatus("saving");
      await api.updatePlacement(placementId, {
        row_index: newRowIndex,
        x_offset_cm: newXOffsetCm,
      });
      await refreshPlanogram();
      setSaveStatus("saved");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setSaveStatus("error");
      setCollisionWarning(msg || "Invalid placement coordinates.");
      setTimeout(() => setCollisionWarning(null), 5000);
    }
  };

  // Update Placement Properties
  const handleUpdatePlacement = async (placementId: number, data: Partial<Placement>) => {
    try {
      setCollisionWarning(null);
      setSaveStatus("saving");
      await api.updatePlacement(placementId, data);
      await refreshPlanogram();
      setSaveStatus("saved");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setSaveStatus("error");
      setCollisionWarning(msg || "Failed to update placement.");
      setTimeout(() => setCollisionWarning(null), 5000);
    }
  };

  // Delete Placement: deletes product and adjusts row height automatically
  const handleDeletePlacement = async (placementId: number) => {
    try {
      // Find placement and shelf before deletion
      let targetPlacement: Placement | null = null;
      let targetShelf: Shelf | null = null;
      for (const shelf of planogram?.shelves || []) {
        const found = (shelf.placements || []).find((p) => p.id === placementId);
        if (found) {
          targetPlacement = found;
          targetShelf = shelf;
          break;
        }
      }

      await api.deletePlacement(placementId);

      // Adjust the row height automatically when product is deleted
      if (targetShelf && targetPlacement) {
        const rowIndex = targetPlacement.row_index;
        const remainingOnRow = (targetShelf.placements || []).filter(
          (p) => p.id !== placementId && p.row_index === rowIndex
        );
        const newMaxHeight = remainingOnRow.length > 0
          ? Math.max(...remainingOnRow.map((p) => p.product.height_cm))
          : 0;

        const usableH = targetShelf.total_height_cm - (targetShelf.has_plinth ? targetShelf.plinth_height_cm : 0);
        const defaultEqualH = Math.max(10, usableH / targetShelf.row_count);

        const currentHeights = targetShelf.row_heights && targetShelf.row_heights.length === targetShelf.row_count
          ? [...targetShelf.row_heights]
          : Array(targetShelf.row_count).fill(defaultEqualH);

        // Adjust row height based on remaining products
        const targetRowH = newMaxHeight > 0
          ? Math.max(newMaxHeight, Math.min(currentHeights[rowIndex], defaultEqualH))
          : defaultEqualH;

        if (currentHeights[rowIndex] > targetRowH + 0.2) {
          const releasedSpace = currentHeights[rowIndex] - targetRowH;
          currentHeights[rowIndex] = Number(targetRowH.toFixed(1));

          // Redistribute released space to other rows
          const otherIndices = Array.from({ length: targetShelf.row_count }, (_, i) => i).filter(i => i !== rowIndex);
          if (otherIndices.length > 0) {
            const addPer = releasedSpace / otherIndices.length;
            for (const oIdx of otherIndices) {
              currentHeights[oIdx] = Number((currentHeights[oIdx] + addPer).toFixed(1));
            }
          }

          await api.updateShelf(targetShelf.id, { row_heights: currentHeights });
        }
      }

      await refreshPlanogram();
      if (selectedPlacementId === placementId) {
        setSelectedPlacementId(null);
      }
      setSaveStatus("saved");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      alert(`Error deleting placement: ${msg}`);
    }
  };

  // Explicit Save Planogram Name
  const handleSavePlanogramName = async (newName: string) => {
    if (!planogram || !newName.trim()) return;
    try {
      setSaveStatus("saving");
      const updated = await api.updatePlanogram(planogram.id, { name: newName.trim() });
      setPlanogram({ ...planogram, name: updated.name });
      setSaveStatus("saved");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setSaveStatus("error");
      alert(`Failed to save planogram: ${msg}`);
    }
  };

  // Get selected objects
  const activeShelf = planogram?.shelves.find((s) => s.id === selectedShelfId) || planogram?.shelves[0] || null;
  const activePlacement =
    activeShelf?.placements.find((p) => p.id === selectedPlacementId) || null;

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-[#0d0f12] text-gray-400">
        <RefreshCw className="w-8 h-8 animate-spin text-amber-400 mb-3" />
        <span className="text-sm font-semibold">Loading Planogram Studio...</span>
      </div>
    );
  }

  if (pageError || !planogram) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-[#0d0f12] text-gray-300 p-6">
        <div className="p-4 rounded-xl bg-red-950/50 border border-red-800 text-center max-w-md">
          <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-2" />
          <h3 className="font-bold text-red-200">Failed to load planogram</h3>
          <p className="text-xs text-red-300 mt-1">{pageError}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-red-800 hover:bg-red-700 text-white rounded-lg text-xs font-semibold"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-[#0d0f12]" data-testid="designer-page">
      {/* Top Header Bar */}
      <header className="h-14 px-4 border-b border-[#262b36] flex items-center justify-between bg-[#13161c] shrink-0 select-none">
        {/* Left: Back & Planogram Title */}
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="p-1.5 rounded-lg bg-[#1a1e26] border border-[#262b36] text-gray-400 hover:text-gray-100 transition-colors"
            title="Return to Dashboard"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>

          <div className="flex items-center gap-2">
            <input
              type="text"
              value={planogram.name}
              onChange={(e) => setPlanogram({ ...planogram, name: e.target.value })}
              onBlur={(e) => handleSavePlanogramName(e.target.value)}
              className="text-sm font-bold text-gray-100 bg-transparent hover:bg-[#1a1e26] focus:bg-[#1a1e26] px-2 py-1 rounded border border-transparent focus:border-amber-500 transition-colors focus:outline-none"
              title="Click to rename planogram"
            />
            <span className="text-[10px] text-gray-400 font-mono">ID: #{planogram.id}</span>
          </div>
        </div>

        {/* Center: Save State Indicator */}
        <div className="flex items-center gap-2">
          {saveStatus === "saving" && (
            <span className="flex items-center gap-1.5 text-xs text-amber-400 font-medium" data-testid="save-status">
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              <span>Saving to SQLite...</span>
            </span>
          )}
          {saveStatus === "saved" && (
            <span className="flex items-center gap-1.5 text-xs text-emerald-400 font-medium" data-testid="save-status">
              <CheckCircle className="w-3.5 h-3.5" />
              <span>Saved</span>
            </span>
          )}
          {saveStatus === "error" && (
            <span className="flex items-center gap-1.5 text-xs text-red-400 font-medium" data-testid="save-status">
              <AlertCircle className="w-3.5 h-3.5" />
              <span>Save failed</span>
            </span>
          )}
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={() => setShowAddShelfModal(true)}
            data-testid="header-add-shelf-btn"
            className="px-3 py-1.5 rounded-lg bg-[#1a1e26] hover:bg-[#222733] border border-[#262b36] text-gray-200 text-xs font-semibold flex items-center gap-1.5 transition-colors"
          >
            <Plus className="w-3.5 h-3.5 text-amber-400" />
            <span>Add Shelf</span>
          </button>

          <button
            onClick={() => setShowExportModal(true)}
            data-testid="export-btn"
            className="px-3 py-1.5 rounded-lg bg-[#1a1e26] hover:bg-[#222733] border border-[#262b36] text-gray-200 text-xs font-semibold flex items-center gap-1.5 transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-blue-400" />
            <span>Export</span>
          </button>

          <button
            onClick={() => handleSavePlanogramName(planogram.name)}
            data-testid="manual-save-btn"
            className="px-3.5 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-600 text-gray-950 text-xs font-bold flex items-center gap-1.5 shadow-sm transition-colors"
          >
            <Save className="w-3.5 h-3.5" />
            <span>Save</span>
          </button>
        </div>
      </header>

      {/* Main 3-Area Designer Layout: Left Outliner, Center Canvas, Right Context */}
      <div className="flex-1 flex min-h-0 overflow-x-auto">
        {/* Left: Blender Outliner Hierarchy */}
        <Outliner
          planogram={planogram}
          selectedShelfId={selectedShelfId}
          selectedPlacementId={selectedPlacementId}
          onSelectShelf={(id) => {
            setSelectedShelfId(id);
            setSelectedPlacementId(null);
          }}
          onSelectPlacement={(id) => setSelectedPlacementId(id)}
          onDeleteShelf={handleDeleteShelf}
          onDeletePlacement={handleDeletePlacement}
          onOpenAddShelf={() => setShowAddShelfModal(true)}
        />

        {/* Center: Bright Shelf Canvas with formal dimension lines */}
        <ShelfCanvas
          shelves={planogram.shelves}
          selectedShelfId={selectedShelfId}
          selectedPlacementId={selectedPlacementId}
          onSelectShelf={(id) => {
            setSelectedShelfId(id);
            setSelectedPlacementId(null);
          }}
          onSelectPlacement={(id) => setSelectedPlacementId(id)}
          onOpenAddShelf={() => setShowAddShelfModal(true)}
          onDropProductOnRow={handleDropProductOnRow}
          onMovePlacement={handleMovePlacement}
          onDeletePlacement={handleDeletePlacement}
          collisionWarning={collisionWarning}
          onUpdateShelf={handleUpdateShelf}
        />

        {/* Right: Context Panel (Properties & Product Library) */}
        <ContextPanel
          planogram={planogram}
          selectedShelf={activeShelf}
          selectedPlacement={activePlacement}
          products={products}
          onUpdateShelf={handleUpdateShelf}
          onDeleteShelf={handleDeleteShelf}
          onUpdatePlacement={handleUpdatePlacement}
          onDeletePlacement={handleDeletePlacement}
          onOpenAddProduct={() => setShowAddProductModal(true)}
          onSeedCatalogue={async () => {
            await api.seedCatalogue();
            const refreshed = await api.getProducts();
            setProducts(refreshed);
          }}
          onAddProductToRow={(shelfId, rowIndex, prod) =>
            handleDropProductOnRow(shelfId, rowIndex, prod)
          }
        />
      </div>

      {/* Add Shelf Modal */}
      <AddShelfModal
        isOpen={showAddShelfModal}
        onClose={() => setShowAddShelfModal(false)}
        onAdd={handleAddShelf}
        defaultIndex={(planogram.shelves?.length || 0) + 1}
      />

      {/* Add Product Modal */}
      <AddProductModal
        isOpen={showAddProductModal}
        onClose={() => setShowAddProductModal(false)}
        onProductCreated={(prod) => {
          setProducts((prev) => [prod, ...prev]);
        }}
      />

      {/* Export Modal */}
      <ExportModal
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
        planogram={planogram}
      />
    </div>
  );
}

export default function DesignerPage() {
  return (
    <Suspense
      fallback={
        <div className="flex-1 flex flex-col items-center justify-center bg-[#0d0f12] text-gray-400">
          <RefreshCw className="w-8 h-8 animate-spin text-amber-400 mb-3" />
          <span className="text-sm font-semibold">Loading Planogram Studio...</span>
        </div>
      }
    >
      <DesignerContent />
    </Suspense>
  );
}
