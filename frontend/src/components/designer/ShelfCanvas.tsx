"use client";

import React, { useState } from "react";
import {
  Plus,
  Trash2,
  Box,
  Layers,
  AlertTriangle,
} from "lucide-react";
import { Shelf, Placement, Product } from "@/types";
import { getImageUrl } from "@/lib/api";

interface ShelfCanvasProps {
  shelves: Shelf[];
  selectedShelfId: number | null;
  selectedPlacementId: number | null;
  onSelectShelf: (shelfId: number) => void;
  onSelectPlacement: (placementId: number | null) => void;
  onOpenAddShelf: () => void;
  onDropProductOnRow: (shelfId: number, rowIndex: number, product: Product, clientX?: number) => void;
  onMovePlacement: (placementId: number, newRowIndex: number, newXOffsetCm: number) => void;
  onDeletePlacement: (placementId: number) => void;
  onUpdateShelf?: (shelfId: number, data: Partial<Shelf>) => void;
  collisionWarning: string | null;
}

export function ShelfCanvas({
  shelves,
  selectedShelfId,
  selectedPlacementId,
  onSelectShelf,
  onSelectPlacement,
  onOpenAddShelf,
  onDropProductOnRow,
  onMovePlacement,
  onDeletePlacement,
  onUpdateShelf,
  collisionWarning,
}: ShelfCanvasProps) {
  const [hoveredRow, setHoveredRow] = useState<{ shelfId: number; rowIndex: number } | null>(null);

  // Active shelf to display
  const activeShelf = shelves.find((s) => s.id === selectedShelfId) || shelves[0];

  // Drag over handler
  const handleDragOver = (e: React.DragEvent, shelfId: number, rowIndex: number) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "copy";
    if (hoveredRow?.shelfId !== shelfId || hoveredRow?.rowIndex !== rowIndex) {
      setHoveredRow({ shelfId, rowIndex });
    }
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setHoveredRow(null);
  };

  const handleDrop = (e: React.DragEvent, shelfId: number, rowIndex: number) => {
    e.preventDefault();
    setHoveredRow(null);
    try {
      const rawData = e.dataTransfer.getData("application/json");
      if (!rawData) return;
      const parsed = JSON.parse(rawData);

      if (parsed.type === "new_product") {
        onDropProductOnRow(shelfId, rowIndex, parsed.product, e.clientX);
      } else if (parsed.type === "existing_placement") {
        const placement = parsed.placement as Placement;
        onMovePlacement(placement.id, rowIndex, placement.x_offset_cm);
      }
    } catch (err) {
      console.error("Drop failed:", err);
    }
  };

  // If no shelves exist in the planogram: empty state
  if (!shelves || shelves.length === 0) {
    return (
      <div
        className="flex-1 flex flex-col items-center justify-center p-8 bg-white border border-[#262b36] m-4 rounded-xl shadow-lg select-none"
        data-testid="shelf-canvas-empty"
      >
        <div className="w-16 h-16 rounded-2xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-600 mb-4 shadow-sm">
          <Layers className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-gray-900">Shelf Canvas is Empty</h2>
        <p className="text-sm text-gray-500 max-w-md text-center mt-1.5 leading-relaxed">
          There are no shelf objects in this planogram yet. Add a shelf unit with real physical dimensions in cm to begin
          placing products.
        </p>
        <button
          onClick={onOpenAddShelf}
          data-testid="canvas-add-shelf-btn"
          className="mt-6 px-5 py-2.5 rounded-lg bg-amber-500 hover:bg-amber-600 text-gray-950 font-bold text-sm transition-colors flex items-center gap-2 shadow-sm"
        >
          <Plus className="w-4 h-4" />
          <span>Add Shelf to Canvas</span>
        </button>
      </div>
    );
  }

  // Calculate usable height and effective heights per row
  const usableHeightCm = activeShelf.total_height_cm - (activeShelf.has_plinth ? activeShelf.plinth_height_cm : 0);
  const defaultEqualHeight = Math.max(10, usableHeightCm / activeShelf.row_count);

  // Maximum product height per row (each row must be at least this height)
  const maxProductHeights: number[] = Array.from({ length: activeShelf.row_count }).map((_, rIdx) => {
    const rowPlacements = (activeShelf.placements || []).filter((p) => p.row_index === rIdx);
    if (rowPlacements.length === 0) return 0;
    return Math.max(...rowPlacements.map((p) => p.product.height_cm));
  });

  // Minimum allowed height for each row: at least max product height in that row, and at least 10cm physical minimum
  const minRowHeights: number[] = Array.from({ length: activeShelf.row_count }).map((_, rIdx) => {
    return Math.max(10, Number(maxProductHeights[rIdx].toFixed(1)));
  });

  // Effective row heights array (index 0 is top row, index row_count - 1 is bottom row)
  // RULE: The height of each row must be AT LEAST the maximum of all products in that row
  const effectiveRowHeights: number[] = Array.from({ length: activeShelf.row_count }).map((_, idx) => {
    let h = defaultEqualHeight;
    if (activeShelf.row_heights && activeShelf.row_heights.length === activeShelf.row_count) {
      const val = activeShelf.row_heights[idx];
      if (typeof val === "number" && val > 0) h = val;
    }
    return Math.max(minRowHeights[idx], h);
  });

  // Base elevation above floor / plinth for each row index (0 is top row, row_count-1 is bottom row)
  const plinthCm = activeShelf.has_plinth ? activeShelf.plinth_height_cm : 0;
  const rowElevations: number[] = Array.from({ length: activeShelf.row_count }).map((_, rIdx) => {
    let elev = plinthCm;
    for (let j = rIdx + 1; j < activeShelf.row_count; j++) {
      elev += effectiveRowHeights[j];
    }
    return elev;
  });

  // Adjust row height by deltaCm
  // RULE: when adjusting, row height cannot reduce below minRowHeights[rIdx]
  const changeRowHeight = (rIdx: number, deltaCm: number) => {
    const minCurrent = minRowHeights[rIdx];
    const newHeights = [...effectiveRowHeights];

    if (rIdx < activeShelf.row_count - 1) {
      const minNext = minRowHeights[rIdx + 1];
      const available = newHeights[rIdx] + newHeights[rIdx + 1];
      const maxAllowed = available - minNext;
      if (minCurrent > maxAllowed) return;
      const target = Math.max(minCurrent, Math.min(maxAllowed, newHeights[rIdx] + deltaCm));
      newHeights[rIdx] = Number(target.toFixed(1));
      newHeights[rIdx + 1] = Number((available - target).toFixed(1));
    } else if (rIdx > 0) {
      const minPrev = minRowHeights[rIdx - 1];
      const available = newHeights[rIdx - 1] + newHeights[rIdx];
      const maxAllowed = available - minPrev;
      if (minCurrent > maxAllowed) return;
      const target = Math.max(minCurrent, Math.min(maxAllowed, newHeights[rIdx] + deltaCm));
      newHeights[rIdx] = Number(target.toFixed(1));
      newHeights[rIdx - 1] = Number((available - target).toFixed(1));
    } else {
      newHeights[rIdx] = Math.max(minCurrent, Number((newHeights[rIdx] + deltaCm).toFixed(1)));
    }
    onUpdateShelf?.(activeShelf.id, { row_heights: newHeights });
  };

  // Set specific row height
  // RULE: when adjusting, row height cannot reduce below minRowHeights[rIdx]
  const setSpecificRowHeight = (rIdx: number, targetHeight: number) => {
    const minCurrent = minRowHeights[rIdx];
    const newHeights = [...effectiveRowHeights];

    if (rIdx < activeShelf.row_count - 1) {
      const minNext = minRowHeights[rIdx + 1];
      const available = newHeights[rIdx] + newHeights[rIdx + 1];
      const maxAllowed = available - minNext;
      const target = Math.max(minCurrent, Math.min(maxAllowed, targetHeight));
      newHeights[rIdx] = Number(target.toFixed(1));
      newHeights[rIdx + 1] = Number((available - target).toFixed(1));
    } else if (rIdx > 0) {
      const minPrev = minRowHeights[rIdx - 1];
      const available = newHeights[rIdx - 1] + newHeights[rIdx];
      const maxAllowed = available - minPrev;
      const target = Math.max(minCurrent, Math.min(maxAllowed, targetHeight));
      newHeights[rIdx] = Number(target.toFixed(1));
      newHeights[rIdx - 1] = Number((available - target).toFixed(1));
    } else {
      newHeights[rIdx] = Math.max(minCurrent, Number(targetHeight.toFixed(1)));
    }
    onUpdateShelf?.(activeShelf.id, { row_heights: newHeights });
  };

  // Equalize all row heights
  const handleEqualizeRows = () => {
    onUpdateShelf?.(activeShelf.id, { row_heights: null });
  };

  // Draggable divider handle between adjacent rows
  const handleStartDragDivider = (topRowIdx: number, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const startTopHeight = effectiveRowHeights[topRowIdx];
    const startBottomHeight = effectiveRowHeights[topRowIdx + 1];
    const startY = e.clientY;
    const availableTotal = startTopHeight + startBottomHeight;
    const pxPerCm = 3.2;

    const minTop = minRowHeights[topRowIdx];
    const minBottom = minRowHeights[topRowIdx + 1];

    const onMouseMove = (moveEvent: MouseEvent) => {
      const deltaPx = moveEvent.clientY - startY;
      const deltaCm = deltaPx / pxPerCm;
      let newTop = startTopHeight + deltaCm;
      newTop = Math.max(minTop, Math.min(availableTotal - minBottom, newTop));
      const newBottom = availableTotal - newTop;

      const newHeights = [...effectiveRowHeights];
      newHeights[topRowIdx] = Number(newTop.toFixed(1));
      newHeights[topRowIdx + 1] = Number(newBottom.toFixed(1));

      onUpdateShelf?.(activeShelf.id, { row_heights: newHeights });
    };

    const onMouseUp = () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };

    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
  };

  return (
    <div
      className="flex-1 min-w-[500px] flex flex-col bg-[#0d0f12] overflow-hidden p-3 md:p-4 select-none relative"
      data-testid="shelf-canvas"
    >
      {/* Selected Shelf Header Bar: shows ONLY the selected shelf */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-3 px-1">
        <div className="flex items-center gap-2">
          {/* Active Shelf Indicator */}
          <div
            className="px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-2 bg-amber-500 text-gray-950 shadow-sm"
            data-testid="selected-shelf-badge"
          >
            <Box className="w-3.5 h-3.5" />
            <span>
              Shelf: <strong className="font-bold">{activeShelf.name}</strong>
            </span>
            <span className="text-[10px] font-mono opacity-80">({activeShelf.width_cm}cm)</span>
          </div>

          {/* Quick switcher dropdown when multiple shelves exist */}
          {shelves.length > 1 && (
            <select
              value={activeShelf.id}
              onChange={(e) => {
                onSelectShelf(Number(e.target.value));
                onSelectPlacement(null);
              }}
              className="bg-[#1a1e26] border border-[#262b36] hover:border-amber-500 text-gray-300 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none cursor-pointer transition-colors"
              title="Switch selected shelf"
            >
              {shelves.map((s, idx) => (
                <option key={s.id} value={s.id} className="bg-[#1a1e26] text-gray-200">
                  Bay #{idx + 1}: {s.name} ({s.width_cm}cm)
                </option>
              ))}
            </select>
          )}

          <button
            onClick={onOpenAddShelf}
            className="px-2.5 py-1.5 rounded-lg bg-[#1a1e26] hover:bg-[#222733] text-amber-400 hover:text-amber-300 border border-[#262b36] text-xs font-semibold flex items-center gap-1 transition-colors"
            title="Add another shelf bay"
          >
            <Plus className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Add Shelf</span>
          </button>
        </div>

        <div className="text-[11px] font-mono text-gray-400 flex items-center gap-3 shrink-0">
          <span>Width: {activeShelf.width_cm}cm</span>
          <span>Height: {activeShelf.total_height_cm}cm</span>
          <span>Depth: {activeShelf.depth_cm}cm</span>
        </div>
      </div>

      {/* Collision Warning Floating Toast */}
      {collisionWarning && (
        <div className="absolute top-16 left-1/2 -translate-x-1/2 z-40 bg-red-900/90 border border-red-700 text-red-100 text-xs px-4 py-2 rounded-lg shadow-xl flex items-center gap-2 animate-bounce">
          <AlertTriangle className="w-4 h-4 text-amber-300 shrink-0" />
          <span>{collisionWarning}</span>
        </div>
      )}

      {/* Center Bright Canvas Card */}
      <div
        id="planogram-render-target"
        className="flex-1 bg-white rounded-xl border border-gray-300 p-4 sm:p-6 overflow-auto shadow-inner flex flex-col"
      >
        {/* Formal Planogram Header Annotation */}
        <div className="flex items-center justify-between pb-3 border-b border-gray-200 mb-3 text-gray-900 shrink-0">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-gray-700">
              Bay Reference Elevation: {activeShelf.name}
            </span>
            <div className="text-[11px] text-gray-500 font-mono">
              Physical Dimensions: {activeShelf.width_cm} cm (W) x {activeShelf.total_height_cm} cm (H) x {activeShelf.depth_cm} cm (D) â€¢ {activeShelf.row_count} Rows
            </div>
          </div>
          <div className="text-right">
            <span className="text-[11px] font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-800 border border-blue-200 font-mono whitespace-nowrap">
              Scale: Physical cm Grid
            </span>
          </div>
        </div>

        {/* Shelf Elevation Drawing with Formal Dimension Brackets */}
        <div className="flex flex-col border-2 border-gray-400 bg-gray-50 rounded-lg p-3 shadow-sm relative min-h-fit">
          {/* Top Measurement Headers */}
          <div className="flex items-center gap-3 mb-2">
            {/* Left Elevation Header with Equalize button */}
            <div className="w-36 shrink-0 h-6 border border-blue-200 bg-blue-100/70 rounded flex items-center justify-between px-2 text-[10px] font-mono font-bold text-blue-900 shadow-2xs whitespace-nowrap">
              <div className="flex items-center gap-1">
                <span>Elevation</span>
                <button
                  type="button"
                  onClick={handleEqualizeRows}
                  className="px-1 py-0.5 rounded bg-white/90 hover:bg-white text-[8px] font-semibold text-blue-800 border border-blue-200 shadow-2xs transition-all"
                  title="Reset all rows to equal heights"
                >
                  Equalize
                </button>
              </div>
              <span>Total {activeShelf.total_height_cm}cm</span>
            </div>

            {/* Right Usable Width Ruler */}
            <div className="flex-1 h-6 border border-gray-300 flex items-center justify-between px-2 text-[10px] font-mono font-bold text-gray-700 bg-gray-200/70 rounded shadow-2xs whitespace-nowrap">
              <span>0 cm</span>
              <span className="px-2 py-0.5 bg-white border border-gray-300 rounded text-gray-800 shadow-2xs">
                Total Usable Width: {activeShelf.width_cm} cm
              </span>
              <span>{activeShelf.width_cm} cm</span>
            </div>
          </div>

          {/* Synchronized Rows Container (Rendered Top Row down to Bottom Row) */}
          <div className="flex flex-col gap-1.5">
            {Array.from({ length: activeShelf.row_count }).map((_, rIdx) => {
              const rowHeightCm = effectiveRowHeights[rIdx];
              const minRowH = minRowHeights[rIdx];
              const maxProdH = maxProductHeights[rIdx];
              const baseElevationCm = rowElevations[rIdx];
              const isAtMin = rowHeightCm <= minRowH + 0.1;
              const isHovered = hoveredRow?.shelfId === activeShelf.id && hoveredRow?.rowIndex === rIdx;
              const rowPlacements = (activeShelf.placements || []).filter(
                (p) => p.row_index === rIdx
              );
              const usedWidth = rowPlacements.reduce(
                (acc, p) => acc + p.product.width_cm * p.facing_count,
                0
              );
              const percentUsed = Math.min(
                100,
                (usedWidth / activeShelf.width_cm) * 100
              );

              return (
                <React.Fragment key={`shelf-${activeShelf.id}-row-pair-${rIdx}`}>
                  <div
                    className="flex items-stretch gap-3 transition-all"
                    style={{ minHeight: `${Math.max(75, rowHeightCm * 3.2)}px` }}
                  >
                    {/* Left Elevation Dimension Bracket (Adjustable Row Height) */}
                    <div
                      className={`w-36 shrink-0 rounded-lg border-2 flex flex-col justify-between p-2 select-none font-mono text-[10px] transition-all ${
                        isHovered
                          ? "border-amber-500 bg-amber-50/90 text-amber-950 shadow-xs"
                          : "border-blue-200 bg-blue-50/50 text-blue-900 hover:border-blue-300"
                      }`}
                    >
                      {/* Row Tag & Min Badge */}
                      <div className="flex items-center justify-between font-bold">
                        <span className="px-1.5 py-0.5 rounded bg-blue-200/80 text-blue-950 text-[10px]">
                          R{rIdx + 1}
                        </span>
                        {maxProdH > 0 ? (
                          <span
                            className="text-[9px] font-semibold text-amber-700 bg-amber-100/90 px-1 rounded"
                            title={`Minimum allowed height based on tallest product (${maxProdH}cm)`}
                          >
                            Min {maxProdH}cm
                          </span>
                        ) : (
                          <span className="text-gray-500 text-[9px] font-semibold">
                            Row {rIdx + 1}
                          </span>
                        )}
                      </div>

                      {/* Height Clearance Bracket with Interactive Controls */}
                      <div className="my-auto py-1 flex items-center justify-center gap-1 font-bold text-blue-900">
                        <button
                          type="button"
                          disabled={isAtMin}
                          onClick={() => changeRowHeight(rIdx, -1)}
                          className={`w-4 h-4 rounded font-bold flex items-center justify-center text-[10px] transition-colors ${
                            isAtMin
                              ? "bg-gray-200 text-gray-400 cursor-not-allowed"
                              : "bg-blue-100 hover:bg-blue-300 text-blue-900 cursor-pointer"
                          }`}
                          title={isAtMin ? `Cannot reduce below max product height (${minRowH}cm)` : "Decrease height (-1cm)"}
                        >
                          -
                        </button>
                        <div className="flex items-center gap-0.5 px-1 py-0.5 rounded bg-white border border-blue-200 shadow-2xs">
                          <span className="text-blue-500 text-[10px]">â†•</span>
                          <input
                            type="number"
                            step="0.5"
                            min={minRowH}
                            max="300"
                            value={Number(rowHeightCm.toFixed(1))}
                            onChange={(e) => setSpecificRowHeight(rIdx, parseFloat(e.target.value) || minRowH)}
                            className="w-10 text-center font-mono font-bold text-[10px] text-blue-950 focus:outline-none"
                            title={`Row height in cm (min: ${minRowH}cm)`}
                          />
                          <span className="text-[9px] text-blue-700">cm</span>
                        </div>
                        <button
                          type="button"
                          onClick={() => changeRowHeight(rIdx, 1)}
                          className="w-4 h-4 rounded bg-blue-100 hover:bg-blue-300 text-blue-900 font-bold flex items-center justify-center text-[10px] transition-colors"
                          title="Increase height (+1cm)"
                        >
                          +
                        </button>
                      </div>

                      {/* Base Elevation from Floor */}
                      <div className="flex items-center justify-between text-[9px] text-gray-500 border-t border-blue-200/70 pt-1 font-mono">
                        <span>Elev:</span>
                        <span className="font-bold text-gray-700">
                          {baseElevationCm.toFixed(1)} cm
                        </span>
                      </div>
                    </div>

                    {/* Center Shelf Bay Row Drop Zone */}
                    <div
                      onDragOver={(e) => handleDragOver(e, activeShelf.id, rIdx)}
                      onDragLeave={handleDragLeave}
                      onDrop={(e) => handleDrop(e, activeShelf.id, rIdx)}
                      className={`flex-1 border-2 rounded-lg flex flex-col justify-between transition-colors relative ${
                        isHovered
                          ? "border-amber-500 bg-amber-50/70"
                          : "border-gray-300 bg-white hover:border-gray-400"
                      }`}
                      data-testid={`shelf-row-${rIdx}`}
                    >
                      {/* Row Capacity & Index Header Bar */}
                      <div className="h-5 px-2 bg-gray-100 border-b border-gray-200 flex items-center justify-between text-[10px] text-gray-700 select-none">
                        <span className="font-bold text-gray-800 font-mono">Row {rIdx + 1}</span>
                        
                        {/* Capacity Indicator (used cm / total cm) */}
                        <div className="flex items-center gap-2">
                          <div className="w-24 bg-gray-300 h-2 rounded-full overflow-hidden">
                            <div
                              className={`h-full transition-all ${
                                percentUsed > 100
                                  ? "bg-red-600"
                                  : percentUsed > 80
                                  ? "bg-amber-500"
                                  : "bg-emerald-500"
                              }`}
                              style={{ width: `${percentUsed}%` }}
                            />
                          </div>
                          <span className="font-mono text-[9px] font-semibold">
                            {usedWidth.toFixed(1)} / {activeShelf.width_cm} cm ({percentUsed.toFixed(0)}%)
                          </span>
                        </div>
                      </div>

                      {/* Placed Products Area */}
                      <div className="flex-1 relative w-full h-full flex items-end px-1 pb-1 overflow-hidden">
                        {rowPlacements.map((placement) => {
                          const isSelected = selectedPlacementId === placement.id;
                          const product = placement.product;
                          const itemWidthPct = (product.width_cm * placement.facing_count / activeShelf.width_cm) * 100;
                          const leftOffsetPct = (placement.x_offset_cm / activeShelf.width_cm) * 100;

                          // Height proportional to row height so outline hugs product physical height
                          const itemHeightPct = Math.min(100, Math.max(15, (product.height_cm / rowHeightCm) * 100));

                          return (
                            <div
                              key={placement.id}
                              draggable
                              onDragStart={(e) => {
                                e.dataTransfer.setData(
                                  "application/json",
                                  JSON.stringify({
                                    type: "existing_placement",
                                    placement,
                                  })
                                );
                              }}
                              onClick={(e) => {
                                e.stopPropagation();
                                onSelectShelf(activeShelf.id);
                                onSelectPlacement(placement.id);
                              }}
                              style={{
                                left: `${leftOffsetPct}%`,
                                width: `${itemWidthPct}%`,
                                height: `${itemHeightPct}%`,
                              }}
                              className={`absolute bottom-0 flex flex-col items-center justify-end group cursor-pointer transition-all ${
                                isSelected
                                  ? "z-20 ring-2 ring-amber-500 bg-amber-500/10 rounded-t shadow-md"
                                  : "z-10 hover:z-20 hover:ring-1 hover:ring-blue-400 rounded-t"
                              }`}
                              data-testid={`placement-${placement.id}`}
                              title={`${product.name} (${product.width_cm}cm x ${product.height_cm}cm) - At ${placement.x_offset_cm}cm`}
                            >
                              {/* Facings row: flex-1 so packshot scales within proportional product height */}
                              <div className="w-full flex-1 min-h-0 flex items-end justify-center">
                                {Array.from({ length: placement.facing_count }).map((_, fIdx) => (
                                  <div
                                    key={`facing-${fIdx}`}
                                    className="flex-1 flex flex-col items-center justify-end h-full px-0.5"
                                  >
                                    {/* Packshot Image preserving aspect ratio */}
                                    <div className="w-full h-full flex items-end justify-center overflow-hidden">
                                      {/* eslint-disable-next-line @next/next/no-img-element */}
                                      <img
                                        src={getImageUrl(product.image_path)}
                                        alt={product.name}
                                        className="max-h-full max-w-full object-contain drop-shadow-sm filter transition-transform group-hover:scale-105"
                                      />
                                    </div>
                                  </div>
                                ))}
                              </div>

                              {/* SKU / Width Label Badge */}
                              <div className="w-full text-center bg-gray-900/80 text-white rounded text-[8px] font-mono py-0.5 px-1 truncate shadow-xs">
                                {product.sku} â€¢ {placement.x_offset_cm}cm
                              </div>

                              {/* Delete placement button on hover */}
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onDeletePlacement(placement.id);
                                }}
                                className="absolute -top-2 -right-1 p-0.5 rounded-full bg-red-600 text-white opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-700 shadow"
                                title="Delete placement"
                              >
                                <Trash2 className="w-2.5 h-2.5" />
                              </button>
                            </div>
                          );
                        })}

                        {rowPlacements.length === 0 && (
                          <div className="w-full h-full flex items-center justify-center text-gray-400 text-xs italic font-mono pointer-events-none">
                            Drop products here
                          </div>
                        )}
                      </div>

                      {/* Shelf Horizontal Slat (Visual Shelf Bar) */}
                      <div className="h-2.5 bg-gradient-to-r from-gray-300 via-gray-400 to-gray-300 border-t border-gray-400 shadow-inner rounded-b" />
                    </div>
                  </div>

                  {/* Interactive Draggable Splitter Divider between adjacent rows */}
                  {rIdx < activeShelf.row_count - 1 && (
                    <div
                      onMouseDown={(e) => handleStartDragDivider(rIdx, e)}
                      className="group flex items-center gap-3 cursor-ns-resize select-none py-1 -my-0.5 z-30"
                      title={`Drag up or down to adjust height between Row ${rIdx + 1} and Row ${rIdx + 2}`}
                    >
                      {/* Left elevation divider handle */}
                      <div className="w-36 shrink-0 flex items-center justify-center">
                        <div className="w-full h-1 bg-blue-200 group-hover:bg-amber-400 rounded-full flex items-center justify-center transition-all group-hover:h-2 shadow-xs">
                          <span className="text-[8px] text-amber-950 font-bold opacity-0 group-hover:opacity-100 font-mono tracking-tighter">
                            â†• RESIZE R{rIdx + 1}/R{rIdx + 2}
                          </span>
                        </div>
                      </div>

                      {/* Right divider line across shelf */}
                      <div className="flex-1 h-1 bg-gray-300 group-hover:bg-amber-400 rounded-full transition-all group-hover:h-1.5" />
                    </div>
                  )}
                </React.Fragment>
              );
            })}
          </div>

          {/* Bottom Plinth / Base Fixture Row */}
          <div className="flex items-center gap-3 mt-2">
            {/* Left Plinth Bracket */}
            <div
              className={`w-36 shrink-0 h-8 rounded border flex items-center justify-between px-2.5 text-[10px] font-mono font-bold ${
                activeShelf.has_plinth
                  ? "border-blue-300 bg-blue-100/60 text-blue-950 shadow-2xs"
                  : "border-dashed border-gray-300 text-gray-400"
              }`}
            >
              <span>{activeShelf.has_plinth ? "Plinth" : "No Plinth"}</span>
              <span>{activeShelf.has_plinth ? `${activeShelf.plinth_height_cm} cm` : "0 cm"}</span>
            </div>

            {/* Right Plinth Fixture or Floor Base */}
            {activeShelf.has_plinth ? (
              <div
                className="flex-1 h-8 rounded border border-gray-400 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 flex items-center justify-center text-[10px] font-mono text-gray-600 font-bold shadow-inner"
              >
                Base Plinth Fixture ({activeShelf.plinth_height_cm} cm)
              </div>
            ) : (
              <div className="flex-1 h-2 border-b-2 border-dashed border-gray-300" />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
