"use client";

import { useState } from "react";
import {
  ChevronRight,
  ChevronDown,
  Box,
  Layers,
  Folder,
  Trash2,
  Package,
  Plus,
} from "lucide-react";
import { Planogram } from "@/types";

interface OutlinerProps {
  planogram: Planogram | null;
  selectedShelfId: number | null;
  selectedPlacementId: number | null;
  onSelectShelf: (shelfId: number | null) => void;
  onSelectPlacement: (placementId: number | null) => void;
  onDeleteShelf: (shelfId: number) => void;
  onDeletePlacement: (placementId: number) => void;
  onOpenAddShelf: () => void;
}

export function Outliner({
  planogram,
  selectedShelfId,
  selectedPlacementId,
  onSelectShelf,
  onSelectPlacement,
  onDeleteShelf,
  onDeletePlacement,
  onOpenAddShelf,
}: OutlinerProps) {
  // Collapsed sets
  const [collapsedShelves, setCollapsedShelves] = useState<Set<number>>(new Set());
  const [collapsedRows, setCollapsedRows] = useState<Set<string>>(new Set());

  const toggleShelf = (shelfId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    const next = new Set(collapsedShelves);
    if (next.has(shelfId)) {
      next.delete(shelfId);
    } else {
      next.add(shelfId);
    }
    setCollapsedShelves(next);
  };

  const toggleRow = (rowKey: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const next = new Set(collapsedRows);
    if (next.has(rowKey)) {
      next.delete(rowKey);
    } else {
      next.add(rowKey);
    }
    setCollapsedRows(next);
  };

  const shelves = planogram?.shelves || [];

  return (
    <aside
      className="w-72 bg-[#13161c] border-r border-[#262b36] flex flex-col h-full select-none text-xs"
      data-testid="blender-outliner"
    >
      {/* Header bar inspired by Blender Outliner */}
      <div className="h-10 px-3 border-b border-[#262b36] flex items-center justify-between bg-[#1a1e26] shrink-0">
        <div className="flex items-center gap-1.5 text-gray-200 font-semibold tracking-wide uppercase text-[11px]">
          <Layers className="w-3.5 h-3.5 text-amber-400" />
          <span>Scene Hierarchy</span>
        </div>
        <button
          onClick={onOpenAddShelf}
          className="p-1 rounded hover:bg-[#262b36] text-gray-400 hover:text-amber-400 transition-colors"
          title="Add Shelf"
        >
          <Plus className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Tree Content */}
      <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
        {/* Root Planogram Node */}
        <div
          onClick={() => {
            onSelectShelf(null);
            onSelectPlacement(null);
          }}
          className={`flex items-center justify-between px-2 py-1.5 rounded cursor-pointer transition-colors ${
            selectedShelfId === null && selectedPlacementId === null
              ? "bg-amber-500/15 text-amber-300 font-medium border border-amber-500/30"
              : "text-gray-300 hover:bg-[#1a1e26]"
          }`}
        >
          <div className="flex items-center gap-1.5 truncate">
            <Folder className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            <span className="truncate font-semibold">{planogram?.name || "Untitled Planogram"}</span>
          </div>
          <span className="text-[10px] text-gray-400 font-mono">
            {shelves.length} {shelves.length === 1 ? "shelf" : "shelves"}
          </span>
        </div>

        {/* Shelves List */}
        {shelves.map((shelf) => {
          const isShelfCollapsed = collapsedShelves.has(shelf.id);
          const isShelfSelected = selectedShelfId === shelf.id && selectedPlacementId === null;
          
          return (
            <div key={shelf.id} className="pl-2 space-y-0.5">
              {/* Shelf Item */}
              <div
                onClick={() => {
                  onSelectShelf(shelf.id);
                  onSelectPlacement(null);
                }}
                className={`flex items-center justify-between px-2 py-1 rounded cursor-pointer group transition-colors ${
                  isShelfSelected
                    ? "bg-amber-500/20 text-amber-300 font-medium border border-amber-500/40"
                    : "text-gray-300 hover:bg-[#1a1e26]"
                }`}
                data-testid={`outliner-shelf-${shelf.id}`}
              >
                <div className="flex items-center gap-1.5 truncate flex-1 min-w-0">
                  <button
                    onClick={(e) => toggleShelf(shelf.id, e)}
                    className="p-0.5 text-gray-400 hover:text-gray-200"
                  >
                    {isShelfCollapsed ? (
                      <ChevronRight className="w-3 h-3" />
                    ) : (
                      <ChevronDown className="w-3 h-3" />
                    )}
                  </button>
                  <Box className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                  <span className="truncate">{shelf.name}</span>
                  <span className="text-[10px] text-gray-400 font-mono">
                    ({shelf.width_cm}×{shelf.total_height_cm}cm)
                  </span>
                </div>

                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm(`Delete shelf "${shelf.name}" and its placements?`)) {
                        onDeleteShelf(shelf.id);
                      }
                    }}
                    className="p-1 hover:text-red-400 text-gray-400"
                    title="Delete shelf"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              </div>

              {/* Rows inside shelf */}
              {!isShelfCollapsed && (
                <div className="pl-4 space-y-0.5">
                  {Array.from({ length: shelf.row_count }).map((_, rIdx) => {
                    const rowKey = `${shelf.id}-r${rIdx}`;
                    const isRowCollapsed = collapsedRows.has(rowKey);
                    const rowPlacements = (shelf.placements || []).filter(
                      (p) => p.row_index === rIdx
                    );
                    const usedWidth = rowPlacements.reduce(
                      (acc, p) => acc + p.product.width_cm * p.facing_count,
                      0
                    );

                    return (
                      <div key={rowKey} className="space-y-0.5">
                        {/* Row Node */}
                        <div
                          onClick={(e) => toggleRow(rowKey, e)}
                          className="flex items-center justify-between px-2 py-0.5 rounded text-gray-400 hover:text-gray-200 hover:bg-[#1a1e26]/60 cursor-pointer text-[11px]"
                        >
                          <div className="flex items-center gap-1.5 truncate">
                            {rowPlacements.length > 0 ? (
                              <button className="p-0.5">
                                {isRowCollapsed ? (
                                  <ChevronRight className="w-2.5 h-2.5" />
                                ) : (
                                  <ChevronDown className="w-2.5 h-2.5" />
                                )}
                              </button>
                            ) : (
                              <span className="w-3.5" />
                            )}
                            <span className="font-mono text-gray-400">Row {rIdx + 1}</span>
                          </div>
                          <span
                            className={`text-[9px] font-mono px-1 rounded ${
                              usedWidth > shelf.width_cm
                                ? "bg-red-950 text-red-400"
                                : "text-gray-400"
                            }`}
                          >
                            {usedWidth.toFixed(1)} / {shelf.width_cm}cm
                          </span>
                        </div>

                        {/* Placements inside Row */}
                        {!isRowCollapsed &&
                          rowPlacements.map((placement) => {
                            const isPlSelected = selectedPlacementId === placement.id;
                            return (
                              <div
                                key={placement.id}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onSelectShelf(shelf.id);
                                  onSelectPlacement(placement.id);
                                }}
                                className={`flex items-center justify-between pl-6 pr-2 py-0.5 rounded cursor-pointer group text-[11px] transition-colors ${
                                  isPlSelected
                                    ? "bg-amber-500/25 text-amber-300 font-medium border border-amber-500/50"
                                    : "text-gray-300 hover:bg-[#1a1e26]"
                                }`}
                                data-testid={`outliner-placement-${placement.id}`}
                              >
                                <div className="flex items-center gap-1.5 truncate flex-1 min-w-0">
                                  <Package className="w-3 h-3 text-emerald-400 shrink-0" />
                                  <span className="truncate">{placement.product.name}</span>
                                  <span className="text-[9px] text-gray-400 font-mono">
                                    @{placement.x_offset_cm}cm
                                  </span>
                                  {placement.facing_count > 1 && (
                                    <span className="text-[9px] px-1 rounded bg-amber-500/20 text-amber-300 font-bold">
                                      ×{placement.facing_count}
                                    </span>
                                  )}
                                </div>

                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    onDeletePlacement(placement.id);
                                  }}
                                  className="p-0.5 opacity-0 group-hover:opacity-100 hover:text-red-400 text-gray-400"
                                  title="Remove placement"
                                >
                                  <Trash2 className="w-2.5 h-2.5" />
                                </button>
                              </div>
                            );
                          })}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}

        {shelves.length === 0 && (
          <div className="p-4 text-center text-gray-400 text-xs">
            <p>No shelf units added yet.</p>
            <button
              onClick={onOpenAddShelf}
              className="mt-2 text-amber-400 hover:text-amber-300 font-semibold flex items-center gap-1 mx-auto"
            >
              <Plus className="w-3 h-3" />
              <span>Add Shelf</span>
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}
