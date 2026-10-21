"use client";

import { useState } from "react";
import { CheckCircle2, XCircle, Search, HelpCircle, Layers, ZoomIn, Eye } from "lucide-react";
import { getImageUrl } from "@/lib/api";
import { ClusterRow, CutoutItem } from "@/types";

interface AnalysisTableProps {
  clusters: ClusterRow[];
  threshold?: number;
  onInspectItem?: (item: CutoutItem) => void;
  loading?: boolean;
}

export function AnalysisTable({
  clusters,
  threshold = 0.95,
  onInspectItem,
  loading = false,
}: AnalysisTableProps) {
  const [filter, setFilter] = useState<"all" | "matched" | "unmatched">("all");
  const [search, setSearch] = useState("");

  const filteredClusters = clusters.filter((c) => {
    if (filter === "matched" && !c.is_catalog_match) return false;
    if (filter === "unmatched" && c.is_catalog_match) return false;

    if (search.trim()) {
      const q = search.toLowerCase();
      const matchName = c.catalog_product?.name.toLowerCase().includes(q) ?? false;
      const matchSku = c.catalog_product?.sku.toLowerCase().includes(q) ?? false;
      const matchCat = c.catalog_product?.category?.toLowerCase().includes(q) ?? false;
      const matchId = `cluster ${c.cluster_id}`.toLowerCase().includes(q);
      return matchName || matchSku || matchCat || matchId;
    }
    return true;
  });

  const matchedCount = clusters.filter((c) => c.is_catalog_match).length;
  const unmatchedCount = clusters.length - matchedCount;

  return (
    <div className="bg-[#13161c] border border-[#262b36] rounded-2xl overflow-hidden flex flex-col shadow-xl" data-testid="analysis-table-container">
      {/* Controls & Filter Bar */}
      <div className="p-4 border-b border-[#262b36] bg-[#1a1e26] flex flex-wrap items-center justify-between gap-3">
        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 bg-[#13161c] p-1 rounded-xl border border-[#262b36]">
          <button
            onClick={() => setFilter("all")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              filter === "all"
                ? "bg-amber-500 text-gray-950 shadow"
                : "text-gray-400 hover:text-gray-200"
            }`}
            data-testid="filter-all-btn"
          >
            All Clusters ({clusters.length})
          </button>
          <button
            onClick={() => setFilter("matched")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
              filter === "matched"
                ? "bg-emerald-500 text-gray-950 shadow"
                : "text-gray-400 hover:text-emerald-400"
            }`}
            data-testid="filter-matched-btn"
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            Matched Catalog ({matchedCount})
          </button>
          <button
            onClick={() => setFilter("unmatched")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
              filter === "unmatched"
                ? "bg-red-500/80 text-white shadow"
                : "text-gray-400 hover:text-gray-200"
            }`}
            data-testid="filter-unmatched-btn"
          >
            <XCircle className="w-3.5 h-3.5" />
            Unmatched ({unmatchedCount})
          </button>
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search SKU, name, cluster..."
            className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-[#13161c] border border-[#262b36] text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-amber-400 transition-colors"
          />
        </div>
      </div>

      {/* 4-Column Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse" data-testid="analysis-4-col-table">
          <thead>
            <tr className="border-b border-[#262b36] bg-[#161a22] text-xs font-semibold text-gray-400 uppercase tracking-wider">
              {/* Column 1 */}
              <th className="py-3.5 px-5 w-[42%] min-w-[340px]">
                <div className="flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-amber-400" />
                  <span>Similar Objects</span>
                </div>
              </th>

              {/* Column 2 */}
              <th className="py-3.5 px-4 w-[16%] min-w-[150px]">
                <span>Similarity Percentage</span>
              </th>

              {/* Column 3 */}
              <th className="py-3.5 px-4 w-[20%] min-w-[190px]">
                <span>Is object similar to someone in the product catalog?</span>
              </th>

              {/* Column 4 */}
              <th className="py-3.5 px-5 w-[22%] min-w-[220px]">
                <span>Similar Product</span>
              </th>
            </tr>
          </thead>

          <tbody className="divide-y divide-[#262b36] text-xs">
            {filteredClusters.length === 0 ? (
              <tr>
                <td colSpan={4} className="py-12 text-center text-gray-500">
                  <HelpCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="font-medium">No visual clusters match current criteria.</p>
                </td>
              </tr>
            ) : (
              filteredClusters.map((row) => (
                <tr
                  key={row.cluster_id}
                  className="hover:bg-[#1a1e26]/60 transition-colors group"
                  data-testid={`cluster-row-${row.cluster_id}`}
                >
                  {/* Column 1: Similar Objects (Horizontal cropped thumbnail cluster) */}
                  <td className="py-3 px-5 align-middle">
                    <div className="flex flex-col gap-1.5">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[11px] font-bold text-gray-400">
                          Cluster #{row.cluster_id}
                        </span>
                        <span className="px-1.5 py-0.5 rounded text-[10px] bg-[#262b36] text-gray-300 font-semibold">
                          {row.item_count} {row.item_count === 1 ? "crop" : "crops"}
                        </span>
                      </div>

                      {/* Horizontal Scrolling Thumbnails */}
                      <div className="flex items-center gap-2 overflow-x-auto pb-1 max-w-xl scrollbar-thin">
                        {row.similar_objects.map((item, idx) => (
                          <div
                            key={item.id}
                            onClick={() => onInspectItem?.(item)}
                            className="relative group/thumb shrink-0 rounded-lg overflow-hidden border border-[#2b313d] bg-[#0d0f12] hover:border-amber-400 cursor-pointer transition-all shadow-sm"
                            title={`Click to inspect crop ${item.id} (Row ${item.row_number ?? "?"}, ${(item.confidence * 100).toFixed(0)}% detection conf)`}
                          >
                            <div className="w-14 h-16 flex items-center justify-center p-1">
                              <img
                                src={getImageUrl(item.crop_path)}
                                alt={item.id}
                                className="max-h-full max-w-full object-contain transition-transform group-hover/thumb:scale-110"
                                loading="lazy"
                              />
                            </div>
                            <div className="absolute inset-0 bg-black/50 opacity-0 group-hover/thumb:opacity-100 flex items-center justify-center transition-opacity">
                              <ZoomIn className="w-3.5 h-3.5 text-white" />
                            </div>
                            <span className="absolute bottom-0 left-0 right-0 bg-black/70 text-[9px] font-mono text-gray-300 text-center py-0.2">
                              #{idx + 1}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </td>

                  {/* Column 2: Similarity Percentage */}
                  <td className="py-3 px-4 align-middle">
                    <div className="flex flex-col gap-1.5">
                      <div className="flex items-baseline gap-1.5">
                        <span
                          className={`text-sm font-bold font-mono px-2 py-0.5 rounded-md border ${
                            row.similarity_percentage >= 95
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                              : row.similarity_percentage >= 85
                              ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                              : "bg-blue-500/10 text-blue-400 border-blue-500/30"
                          }`}
                        >
                          {row.similarity_percentage.toFixed(1)}%
                        </span>
                        <span className="text-[10px] text-gray-500 font-medium">cohesion</span>
                      </div>

                      {/* Mini visual meter */}
                      <div className="w-24 h-1.5 bg-[#262b36] rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${
                            row.similarity_percentage >= 95
                              ? "bg-emerald-500"
                              : row.similarity_percentage >= 85
                              ? "bg-amber-500"
                              : "bg-blue-500"
                          }`}
                          style={{ width: `${Math.min(100, row.similarity_percentage)}%` }}
                        />
                      </div>
                    </div>
                  </td>

                  {/* Column 3: Is object similar to someone in the product catalog? (Strictly Yes / No) */}
                  <td className="py-3 px-4 align-middle">
                    <div className="flex flex-col gap-1">
                      {row.is_catalog_match ? (
                        <div className="flex items-center gap-1.5">
                          <span
                            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/15 border border-emerald-500/40 text-emerald-400 shadow-sm"
                            data-testid="catalog-match-yes"
                          >
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                            Yes
                          </span>
                        </div>
                      ) : (
                        <div className="flex items-center gap-1.5">
                          <span
                            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-gray-500/10 border border-gray-600/30 text-gray-400"
                            data-testid="catalog-match-no"
                          >
                            <XCircle className="w-3.5 h-3.5 text-gray-500 shrink-0" />
                            No
                          </span>
                        </div>
                      )}

                      <span className="text-[10px] text-gray-500">
                        {row.is_catalog_match
                          ? `Match score: ${(row.catalog_confidence * 100).toFixed(1)}% (≥ ${(threshold * 100).toFixed(0)}%)`
                          : `Score ${(row.catalog_confidence * 100).toFixed(1)}% < ${(threshold * 100).toFixed(0)}% cutoff`}
                      </span>
                    </div>
                  </td>

                  {/* Column 4: Similar Product (If Yes, show image & details; If No, show NO image) */}
                  <td className="py-3 px-5 align-middle">
                    {row.is_catalog_match && row.catalog_product ? (
                      <div className="flex items-center gap-3" data-testid="catalog-product-matched">
                        {/* Packshot Image */}
                        <div className="w-13 h-13 rounded-lg bg-white p-1 border border-gray-300 shadow-md shrink-0 flex items-center justify-center overflow-hidden">
                          <img
                            src={getImageUrl(row.catalog_product.image_path)}
                            alt={row.catalog_product.name}
                            className="max-h-full max-w-full object-contain"
                            loading="lazy"
                          />
                        </div>

                        {/* Product Metadata */}
                        <div className="min-w-0 flex flex-col">
                          <h4 className="font-semibold text-gray-100 text-xs truncate max-w-[180px]" title={row.catalog_product.name}>
                            {row.catalog_product.name}
                          </h4>
                          <span className="font-mono text-[11px] text-amber-400 mt-0.5">
                            {row.catalog_product.sku}
                          </span>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className="text-[10px] text-gray-400 capitalize truncate max-w-[90px]">
                              {row.catalog_product.category || "General"}
                            </span>
                            <span className="text-[10px] font-semibold text-emerald-400">
                              {row.catalog_product.currency} {row.catalog_product.price}
                            </span>
                          </div>
                        </div>
                      </div>
                    ) : (
                      /* Strictly NO product image rendered when match is No */
                      <div className="text-gray-500 text-xs italic flex items-center gap-2 py-1" data-testid="catalog-product-none">
                        <span className="inline-block w-2 h-2 rounded-full bg-gray-600" />
                        <span>No catalog product matched</span>
                      </div>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Footer Summary */}
      <div className="p-3.5 border-t border-[#262b36] bg-[#161a22] flex items-center justify-between text-xs text-gray-400">
        <span>
          Showing <strong className="text-gray-200">{filteredClusters.length}</strong> of{" "}
          <strong className="text-gray-200">{clusters.length}</strong> visual clusters
        </span>
        <span className="text-[11px] text-gray-500">
          Strict catalog confidence threshold: <strong className="text-amber-400">{(threshold * 100).toFixed(0)}%</strong>
        </span>
      </div>
    </div>
  );
}
