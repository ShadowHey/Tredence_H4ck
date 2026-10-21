"use client";

import { useState } from "react";
import { Grid, AlertCircle } from "lucide-react";
import { Shelf } from "@/types";
import { logFrontendAction } from "@/lib/logger";

interface AddShelfModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (shelfData: Partial<Shelf>) => Promise<void>;
  defaultIndex?: number;
}

export function AddShelfModal({
  isOpen,
  onClose,
  onAdd,
  defaultIndex = 1,
}: AddShelfModalProps) {
  const [name, setName] = useState(`Shelf 0${defaultIndex}`);
  const [widthCm, setWidthCm] = useState<number>(120.0);
  const [totalHeightCm, setTotalHeightCm] = useState<number>(180.0);
  const [depthCm, setDepthCm] = useState<number>(40.0);
  const [rowCount, setRowCount] = useState<number>(4);
  const [hasPlinth, setHasPlinth] = useState<boolean>(true);
  const [plinthHeightCm, setPlinthHeightCm] = useState<number>(15.0);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Shelf name is required.");
      return;
    }
    if (widthCm <= 0 || totalHeightCm <= 0 || depthCm <= 0) {
      setError("Shelf dimensions must be greater than zero.");
      return;
    }
    if (rowCount < 1 || rowCount > 12) {
      setError("Row count must be between 1 and 12.");
      return;
    }
    if (hasPlinth && (plinthHeightCm < 0 || plinthHeightCm >= totalHeightCm)) {
      setError(`Plinth height must be less than total shelf height (${totalHeightCm}cm).`);
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      await onAdd({
        name: name.trim(),
        width_cm: Number(widthCm),
        total_height_cm: Number(totalHeightCm),
        depth_cm: Number(depthCm),
        row_count: Number(rowCount),
        has_plinth: hasPlinth,
        plinth_height_cm: hasPlinth ? Number(plinthHeightCm) : 0.0,
      });
      logFrontendAction(
        "ACTION:SHELF_ADD",
        `Created shelf "${name.trim()}" (${widthCm}x${totalHeightCm}cm, ${rowCount} rows)`
      );
      onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg || "Failed to add shelf.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-[#1a1e26] border border-[#262b36] rounded-xl w-full max-w-lg overflow-hidden shadow-2xl" data-testid="modal-add-shelf">
        <div className="p-5 border-b border-[#262b36] flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-100 flex items-center gap-2">
            <Grid className="w-4 h-4 text-amber-400" />
            Add New Shelf Unit
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-200 text-sm font-bold">
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-950/50 border border-red-800 text-red-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">
              Shelf Name <span className="text-amber-400">*</span>
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-[#13161c] border border-[#262b36] text-gray-100 text-sm focus:outline-none focus:border-amber-500"
              placeholder="e.g. Shelf 01"
            />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1">
                Width (cm) <span className="text-amber-400">*</span>
              </label>
              <input
                type="number"
                step="0.5"
                min="10"
                max="500"
                required
                value={widthCm}
                onChange={(e) => setWidthCm(parseFloat(e.target.value) || 0)}
                className="w-full px-3 py-2 rounded-lg bg-[#13161c] border border-[#262b36] text-gray-100 text-sm focus:outline-none focus:border-amber-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1">
                Total Height (cm) <span className="text-amber-400">*</span>
              </label>
              <input
                type="number"
                step="0.5"
                min="20"
                max="500"
                required
                value={totalHeightCm}
                onChange={(e) => setTotalHeightCm(parseFloat(e.target.value) || 0)}
                className="w-full px-3 py-2 rounded-lg bg-[#13161c] border border-[#262b36] text-gray-100 text-sm focus:outline-none focus:border-amber-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1">
                Depth (cm) <span className="text-amber-400">*</span>
              </label>
              <input
                type="number"
                step="0.5"
                min="5"
                max="200"
                required
                value={depthCm}
                onChange={(e) => setDepthCm(parseFloat(e.target.value) || 0)}
                className="w-full px-3 py-2 rounded-lg bg-[#13161c] border border-[#262b36] text-gray-100 text-sm focus:outline-none focus:border-amber-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">
              Number of Rows (1 to 12) <span className="text-amber-400">*</span>
            </label>
            <div className="flex items-center gap-3">
              <input
                type="range"
                min="1"
                max="12"
                data-testid="input-modal-shelf-row-count"
                value={rowCount}
                onChange={(e) => setRowCount(parseInt(e.target.value) || 1)}
                className="flex-1 accent-amber-500"
              />
              <input
                type="number"
                min="1"
                max="12"
                data-testid="input-modal-shelf-row-count-number"
                value={rowCount}
                onChange={(e) => setRowCount(Math.min(12, Math.max(1, parseInt(e.target.value) || 1)))}
                className="w-14 text-center text-sm font-bold text-amber-400 bg-[#13161c] px-2 py-1 rounded border border-[#262b36] focus:outline-none focus:border-amber-500 font-mono"
              />
            </div>
            <p className="text-[11px] text-gray-400 mt-1">
              Equal vertical spacing will be allocated automatically across {rowCount} rows.
            </p>
          </div>

          <div className="p-3.5 rounded-lg bg-[#13161c] border border-[#262b36] space-y-2">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-semibold text-gray-200">Bottom Plinth / Base Header</span>
                <p className="text-[11px] text-gray-400">Ground elevation fixture at shelf bottom</p>
              </div>
              <input
                type="checkbox"
                checked={hasPlinth}
                onChange={(e) => setHasPlinth(e.target.checked)}
                className="w-4 h-4 rounded accent-amber-500 cursor-pointer"
              />
            </div>

            {hasPlinth && (
              <div className="pt-2 border-t border-[#262b36] flex items-center justify-between">
                <label className="text-xs text-gray-300">Plinth Height (cm):</label>
                <input
                  type="number"
                  step="0.5"
                  min="1"
                  max={totalHeightCm - 10}
                  value={plinthHeightCm}
                  onChange={(e) => setPlinthHeightCm(parseFloat(e.target.value) || 0)}
                  className="w-24 px-2 py-1 rounded bg-[#1a1e26] border border-[#262b36] text-gray-100 text-xs focus:outline-none focus:border-amber-500"
                />
              </div>
            )}
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#262b36]">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-[#262b36] text-gray-300 hover:text-gray-100 text-xs font-semibold"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              data-testid="modal-add-shelf-submit"
              className="px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-600 text-gray-950 font-semibold text-xs transition-colors"
            >
              {submitting ? "Adding..." : "Add Shelf to Canvas"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
