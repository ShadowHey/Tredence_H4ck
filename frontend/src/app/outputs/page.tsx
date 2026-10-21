"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Download, FileJson, Loader2, Trash2, Crop, Sparkles, ZoomIn } from "lucide-react";
import { api, downloadProcessedOutputs, getImageUrl } from "@/lib/api";
import { ProcessedOutput } from "@/types";
import { CutoutViewerModal } from "@/components/outputs/CutoutViewerModal";

export default function OutputsPage() {
  const [outputs, setOutputs] = useState<ProcessedOutput[]>([]);
  const [selected, setSelected] = useState<number[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeCutoutOutputId, setActiveCutoutOutputId] = useState<number | null>(null);

  const load = async () => {
    try {
      setOutputs(await api.getProcessedOutputs());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load outputs.");
    }
  };

  useEffect(() => {
    void load();
    const timer = window.setInterval(() => void load(), 5000);
    return () => window.clearInterval(timer);
  }, []);

  const toggle = (id: number) =>
    setSelected((ids) => (ids.includes(id) ? ids.filter((val) => val !== id) : [...ids, id]));

  const exportSelected = async () => {
    try {
      setBusy(true);
      await downloadProcessedOutputs(selected);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed.");
    } finally {
      setBusy(false);
    }
  };

  const deleteSelected = async () => {
    if (
      !selected.length ||
      !window.confirm(`Delete ${selected.length} selected output(s)? Original input images will remain staged.`)
    )
      return;
    try {
      setBusy(true);
      await api.deleteProcessedOutputs(selected);
      setSelected([]);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Deletion failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto bg-[#0d0f12]" data-testid="outputs-page">
      <header className="min-h-16 px-6 py-3 border-b border-[#262b36] flex flex-wrap gap-3 items-center justify-between bg-[#13161c]">
        <div>
          <h1 className="text-lg font-semibold text-gray-100">Outputs</h1>
          <p className="text-xs text-gray-400">
            Annotated shelf images with YOLO bounding box cutouts and planogram traceability.
          </p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => setSelected(selected.length === outputs.length ? [] : outputs.map((o) => o.id))}
            disabled={!outputs.length || busy}
            className="px-3 py-2 rounded-lg border border-[#353b48] text-sm text-gray-300 disabled:opacity-40 hover:bg-[#1a1e26] transition-colors"
          >
            {selected.length === outputs.length ? "Clear selection" : "Select all"}
          </button>
          <button
            onClick={() => void exportSelected()}
            disabled={!selected.length || busy}
            className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-gray-950 text-sm font-semibold disabled:opacity-40 transition-colors shadow-sm"
          >
            <Download className="w-4 h-4" />
            Export
          </button>
          <button
            onClick={() => void deleteSelected()}
            disabled={!selected.length || busy}
            className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-red-500/35 hover:bg-red-500/10 text-red-300 text-sm disabled:opacity-40 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            Delete
          </button>
        </div>
      </header>

      {error && (
        <div role="alert" className="mx-6 mt-4 p-3 text-sm rounded-lg bg-red-500/10 border border-red-500/30 text-red-300">
          {error}
        </div>
      )}

      {!outputs.length ? (
        <div className="h-[60vh] flex flex-col items-center justify-center text-center">
          <FileJson className="w-10 h-10 text-gray-600 mb-3" />
          <h2 className="font-semibold text-gray-300">No processed outputs</h2>
          <p className="text-sm text-gray-500 mt-1">
            Process an assigned shelf image from Input Images to see annotations here.
          </p>
        </div>
      ) : (
        <div className="p-6 grid grid-cols-1 md:grid-cols-2 2xl:grid-cols-3 gap-5">
          {outputs.map((output) => (
            <article
              key={output.id}
              className={`rounded-xl overflow-hidden border bg-[#13161c] transition-all hover:border-[#3a4252] ${
                selected.includes(output.id) ? "border-amber-400/70" : "border-[#262b36]"
              }`}
            >
              {/* Image Preview with Click-to-Inspect Overlay */}
              <div
                className="relative bg-[#0d0f12] cursor-pointer group"
                onClick={() => setActiveCutoutOutputId(output.id)}
                title="Click to inspect YOLO bounding box cutouts"
              >
                <img
                  src={getImageUrl(output.annotated_image_path)}
                  alt={`Annotated ${output.source_filename}`}
                  className="w-full h-60 object-contain transition-transform group-hover:scale-[1.02]"
                />

                {/* Hover Overlay */}
                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center gap-2 transition-opacity">
                  <div className="px-3 py-1.5 rounded-lg bg-black/80 border border-amber-500/50 text-amber-300 text-xs font-semibold flex items-center gap-1.5 shadow-lg">
                    <Crop className="w-3.5 h-3.5" />
                    Inspect Cutouts
                  </div>
                </div>

                <label
                  className="absolute top-3 left-3 p-2 rounded bg-[#0d0f12]/85 border border-[#444b58] cursor-pointer"
                  onClick={(e) => e.stopPropagation()}
                >
                  <input
                    aria-label={`Select ${output.source_filename}`}
                    type="checkbox"
                    checked={selected.includes(output.id)}
                    onChange={() => toggle(output.id)}
                  />
                </label>
              </div>

              {/* Card Metadata & Actions */}
              <div className="p-4">
                <h2 className="font-semibold text-sm truncate text-gray-100">{output.source_filename}</h2>
                <p className="text-xs text-gray-400 mt-1">
                  {output.planogram_name ?? "Deleted planogram"} · {output.shelf_snapshot?.name ?? "Deleted shelf"}
                </p>
                <p className="text-xs text-blue-300 mt-1">
                  {output.shelf_snapshot
                    ? `${output.shelf_snapshot.width_cm} cm × ${output.shelf_snapshot.total_height_cm} cm · ${output.shelf_snapshot.row_count} rows`
                    : "Shelf snapshot unavailable"}
                </p>

                {/* Metrics Grid */}
                <div className="mt-3 grid grid-cols-3 gap-2 text-center text-xs">
                  <div className="p-2 rounded bg-[#1a1e26] border border-[#262b36]">
                    <strong className="text-gray-100">{output.metrics.product_count ?? 0}</strong>
                    <br />
                    <span className="text-gray-400">Products</span>
                  </div>
                  <div className="p-2 rounded bg-[#1a1e26] border border-[#262b36]">
                    <strong className="text-gray-100">{output.metrics.shelf_row_count ?? 0}</strong>
                    <br />
                    <span className="text-gray-400">Rows</span>
                  </div>
                  <div className="p-2 rounded bg-[#1a1e26] border border-[#262b36]">
                    <strong className="text-gray-100">{output.metrics.empty_area_percentage?.toFixed(1) ?? "—"}%</strong>
                    <br />
                    <span className="text-gray-400">Empty</span>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="mt-4 pt-3 border-t border-[#262b36] flex items-center justify-between">
                  <button
                    onClick={() => setActiveCutoutOutputId(output.id)}
                    className="inline-flex items-center gap-1.5 text-xs text-amber-400 hover:text-amber-300 font-medium"
                  >
                    <Crop className="w-3.5 h-3.5" />
                    Inspect Cutouts
                  </button>

                  <Link
                    href={`/analysis?outputId=${output.id}`}
                    className="inline-flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300 font-semibold"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    Analysis Insights ➔
                  </Link>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}

      {busy && (
        <div className="fixed bottom-5 right-5 p-3 rounded-lg bg-[#1a1e26] border border-[#353b48] text-sm flex gap-2 shadow-xl">
          <Loader2 className="w-4 h-4 animate-spin text-amber-400" />
          Working…
        </div>
      )}

      {/* YOLO Bounding Box Cutout Viewer Modal */}
      <CutoutViewerModal
        outputId={activeCutoutOutputId}
        onClose={() => setActiveCutoutOutputId(null)}
      />
    </div>
  );
}
