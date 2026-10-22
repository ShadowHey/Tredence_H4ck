"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { X, Loader2, Sparkles, AlertCircle, Maximize2, Tag, Layers, CheckCircle2, Download } from "lucide-react";
import { API_BASE_URL, api, getImageUrl } from "@/lib/api";
import { CutoutsResponse, CutoutItem } from "@/types";

interface CutoutViewerModalProps {
  outputId: number | null;
  onClose: () => void;
}

export function CutoutViewerModal({ outputId, onClose }: CutoutViewerModalProps) {
  const [data, setData] = useState<CutoutsResponse | null>(null);
  const [activeTab, setActiveTab] = useState<"products" | "shelves" | "empty_spaces">("products");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCrop, setSelectedCrop] = useState<CutoutItem | null>(null);
  const cutoutDownloadUrl = (item: CutoutItem) =>
    `${API_BASE_URL}/api/v1/outputs/${outputId}/cutouts/${encodeURIComponent(item.id)}/download`;

  useEffect(() => {
    if (!outputId) return;

    let isMounted = true;
    setLoading(true);
    setError(null);

    api
      .getOutputCutouts(outputId)
      .then((res) => {
        if (isMounted) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load cutouts.");
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [outputId]);

  if (!outputId) return null;

  const currentItems: CutoutItem[] = data ? data[activeTab] : [];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 overflow-hidden"
      data-testid="cutout-viewer-modal"
      onClick={onClose}
    >
      <div
        className="bg-[#13161c] border border-[#262b36] rounded-2xl w-full max-w-5xl h-[88vh] flex flex-col shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <header className="px-6 py-4 border-b border-[#262b36] bg-[#1a1e26] flex items-center justify-between shrink-0">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-semibold text-gray-100 flex items-center gap-2">
                <Tag className="w-4 h-4 text-amber-400" />
                YOLO Bounding Box Cutouts Inspector
              </h2>
              {data && (
                <span className="px-2 py-0.5 text-xs font-semibold rounded bg-amber-500/10 border border-amber-500/30 text-amber-400">
                  {data.total_count} total cutouts
                </span>
              )}
            </div>
            <p className="text-xs text-gray-400 mt-0.5 truncate max-w-xl">
              Source: <span className="text-gray-200">{data?.source_filename || `Output #${outputId}`}</span>
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href={`/analysis?outputId=${outputId}`}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-gray-950 font-semibold text-xs transition-colors"
            >
              <Sparkles className="w-3.5 h-3.5" />
              Open Analysis ➔
            </Link>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-gray-400 hover:text-gray-200 hover:bg-[#262b36] transition-colors"
              title="Close modal"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </header>

        {/* Tab Buttons */}
        <div className="px-6 pt-3 pb-2 border-b border-[#262b36] bg-[#161a22] flex items-center gap-2 shrink-0">
          <button
            onClick={() => setActiveTab("products")}
            className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all flex items-center gap-2 ${
              activeTab === "products"
                ? "bg-amber-500 text-gray-950 shadow"
                : "text-gray-400 hover:text-gray-200 hover:bg-[#1a1e26]"
            }`}
          >
            <span>Products</span>
            <span
              className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                activeTab === "products" ? "bg-amber-600/40 text-gray-950" : "bg-[#262b36] text-gray-400"
              }`}
            >
              {data?.products.length ?? 0}
            </span>
          </button>

          <button
            onClick={() => setActiveTab("shelves")}
            className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all flex items-center gap-2 ${
              activeTab === "shelves"
                ? "bg-amber-500 text-gray-950 shadow"
                : "text-gray-400 hover:text-gray-200 hover:bg-[#1a1e26]"
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Shelves / Rows</span>
            <span
              className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                activeTab === "shelves" ? "bg-amber-600/40 text-gray-950" : "bg-[#262b36] text-gray-400"
              }`}
            >
              {data?.shelves.length ?? 0}
            </span>
          </button>

          <button
            onClick={() => setActiveTab("empty_spaces")}
            className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all flex items-center gap-2 ${
              activeTab === "empty_spaces"
                ? "bg-amber-500 text-gray-950 shadow"
                : "text-gray-400 hover:text-gray-200 hover:bg-[#1a1e26]"
            }`}
          >
            <span>Empty Spaces</span>
            <span
              className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                activeTab === "empty_spaces" ? "bg-amber-600/40 text-gray-950" : "bg-[#262b36] text-gray-400"
              }`}
            >
              {data?.empty_spaces.length ?? 0}
            </span>
          </button>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-6 bg-[#0d0f12]">
          {loading && (
            <div className="h-64 flex flex-col items-center justify-center text-center">
              <Loader2 className="w-8 h-8 text-amber-400 animate-spin mb-3" />
              <p className="text-sm text-gray-300">Extracting cutouts and computing embeddings...</p>
              <p className="text-xs text-gray-500 mt-1">This will only take a moment.</p>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-xl bg-red-950/40 border border-red-800 text-red-300 text-sm flex items-center gap-3">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {!loading && !error && currentItems.length === 0 && (
            <div className="h-64 flex flex-col items-center justify-center text-center text-gray-500">
              <p className="text-sm font-medium">No cutouts detected in this category.</p>
            </div>
          )}

          {!loading && !error && currentItems.length > 0 && (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3.5">
              {currentItems.map((item, idx) => (
                <div
                  key={item.id}
                  onClick={() => setSelectedCrop(item)}
                  className="group relative rounded-xl border border-[#262b36] bg-[#161a22] hover:border-amber-500/60 transition-all p-2 flex flex-col items-center cursor-pointer shadow-sm hover:shadow-md"
                >
                  <div className="w-full h-28 bg-[#0d0f12] rounded-lg overflow-hidden flex items-center justify-center relative">
                    <img
                      src={getImageUrl(item.crop_path)}
                      alt={item.id}
                      className="max-h-full max-w-full object-contain transition-transform group-hover:scale-105"
                      loading="lazy"
                    />
                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                      <Maximize2 className="w-4 h-4 text-white" />
                    </div>
                  </div>

                  <div className="w-full mt-2 flex items-center justify-between text-[11px]">
                    <span className="font-mono text-gray-300 font-semibold truncate">#{idx + 1}</span>
                    <div className="flex items-center gap-1">
                      <span className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                        {(item.confidence * 100).toFixed(0)}%
                      </span>
                      <a
                        aria-label={`Download cutout #${idx + 1}`}
                        title="Download this cutout"
                        href={cutoutDownloadUrl(item)}
                        className="p-1 rounded text-gray-400 hover:text-amber-400 hover:bg-amber-500/10 transition-colors"
                      >
                        <Download className="w-3.5 h-3.5" />
                      </a>
                    </div>
                  </div>

                  {item.row_number && (
                    <div className="w-full text-left mt-0.5">
                      <span className="text-[10px] text-gray-400">Row {item.row_number}</span>
                    </div>
                  )}
                  {item.category === "product" && item.catalog_match && (
                    <div className={`w-full mt-1 text-[10px] font-semibold ${item.catalog_match.status === "matched" ? "text-emerald-400" : item.catalog_match.status === "needs_review" ? "text-amber-300" : "text-gray-400"}`}>
                      {item.catalog_match.status === "matched" ? `Matched · ${item.catalog_match.top_candidate?.sku ?? "SKU"}` : item.catalog_match.status === "needs_review" ? "Needs review" : "Unmatched"}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <footer className="px-6 py-3 border-t border-[#262b36] bg-[#1a1e26] flex items-center justify-between shrink-0 text-xs text-gray-400">
          <span>
            Showing <strong className="text-gray-200">{currentItems.length}</strong> {activeTab.replace("_", " ")} cutouts
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg border border-[#353b48] hover:bg-[#262b36] text-gray-300 font-medium transition-colors"
          >
            Close
          </button>
        </footer>
      </div>

      {/* Enlarged Crop Detail Sub-Modal */}
      {selectedCrop && (
        <div
          className="fixed inset-0 z-60 flex items-center justify-center bg-black/85 p-4"
          onClick={() => setSelectedCrop(null)}
        >
          <div
            className="bg-[#1a1e26] border border-[#353b48] rounded-xl max-w-md w-full p-5 shadow-2xl space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-[#262b36] pb-3">
              <h3 className="text-sm font-semibold text-gray-200 font-mono">Cutout {selectedCrop.id}</h3>
              <button
                onClick={() => setSelectedCrop(null)}
                className="text-gray-400 hover:text-gray-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="w-full h-64 bg-[#0d0f12] rounded-lg flex items-center justify-center overflow-hidden p-2">
              <img
                src={getImageUrl(selectedCrop.crop_path)}
                alt={selectedCrop.id}
                className="max-h-full max-w-full object-contain"
              />
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="p-2.5 rounded bg-[#13161c] border border-[#262b36]">
                <span className="text-gray-400 block text-[10px] uppercase font-semibold">Category</span>
                <span className="text-gray-200 font-medium capitalize">{selectedCrop.category.replace("_", " ")}</span>
              </div>
              <div className="p-2.5 rounded bg-[#13161c] border border-[#262b36]">
                <span className="text-gray-400 block text-[10px] uppercase font-semibold">Detection Confidence</span>
                <span className="text-emerald-400 font-medium">{(selectedCrop.confidence * 100).toFixed(1)}%</span>
              </div>
              <div className="p-2.5 rounded bg-[#13161c] border border-[#262b36] col-span-2">
                <span className="text-gray-400 block text-[10px] uppercase font-semibold">Bounding Box (XYXY px)</span>
                <span className="text-gray-200 font-mono text-[11px]">
                  [{selectedCrop.bbox_xyxy.join(", ")}]
                </span>
              </div>
            </div>

            {selectedCrop.category === "product" && selectedCrop.catalog_match && (
              <section className="rounded-lg border border-[#353b48] bg-[#13161c] p-3 space-y-2 text-xs" aria-label="Shelf catalogue match">
                <div className="flex items-center justify-between">
                  <span className="text-gray-400 uppercase text-[10px] font-semibold">Shelf catalogue match</span>
                  <span className={`font-semibold capitalize ${selectedCrop.catalog_match.status === "matched" ? "text-emerald-400" : selectedCrop.catalog_match.status === "needs_review" ? "text-amber-300" : "text-gray-300"}`}>
                    {selectedCrop.catalog_match.status.replace("_", " ")}
                  </span>
                </div>
                <p className="text-gray-400">{selectedCrop.catalog_match.reason.replaceAll("_", " ")}</p>
                {selectedCrop.catalog_match.top_candidate && (
                  <p className="text-gray-200">Top: <span className="font-semibold">{selectedCrop.catalog_match.top_candidate.name}</span> ({selectedCrop.catalog_match.top_candidate.sku}) · {selectedCrop.catalog_match.similarity == null ? "—" : `${(selectedCrop.catalog_match.similarity * 100).toFixed(1)}%`}</p>
                )}
                {selectedCrop.catalog_match.runner_up && (
                  <p className="text-gray-400">Runner-up: {selectedCrop.catalog_match.runner_up.name} ({selectedCrop.catalog_match.runner_up.sku}) · {selectedCrop.catalog_match.runner_up_similarity == null ? "—" : `${(selectedCrop.catalog_match.runner_up_similarity * 100).toFixed(1)}%`}</p>
                )}
                {selectedCrop.catalog_match.confidence_margin != null && (
                  <p className="text-gray-400">Score margin: {(selectedCrop.catalog_match.confidence_margin * 100).toFixed(1)} percentage points</p>
                )}
              </section>
            )}

            {selectedCrop.planogram_position && (
              <section className="rounded-lg border border-[#353b48] bg-[#13161c] p-3 space-y-1 text-xs" aria-label="Planogram position">
                <span className="text-gray-400 uppercase text-[10px] font-semibold">Planogram position</span>
                <p className="text-gray-200">
                  Row {selectedCrop.planogram_position.row_index + 1} · {selectedCrop.planogram_position.x_start_cm.toFixed(1)}–{selectedCrop.planogram_position.x_end_cm.toFixed(1)} cm from left
                </p>
                <p className="text-gray-500">
                  {selectedCrop.planogram_position.method.replaceAll("_", " ")} · ±{selectedCrop.planogram_position.position_tolerance_cm.toFixed(1)} cm tolerance
                </p>
              </section>
            )}

            <a
              href={cutoutDownloadUrl(selectedCrop)}
              className="w-full py-2 rounded-lg border border-[#4a5262] hover:border-amber-500/60 text-gray-200 hover:text-amber-300 font-semibold text-xs transition-colors inline-flex items-center justify-center gap-2"
            >
              <Download className="w-3.5 h-3.5" />
              Download cutout
            </a>

            <button
              onClick={() => setSelectedCrop(null)}
              className="w-full py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-gray-950 font-semibold text-xs transition-colors"
            >
              Back to Cutouts
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
