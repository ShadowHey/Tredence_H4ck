"use client";

import { CheckCircle2, HelpCircle, Search, XCircle } from "lucide-react";
import { getImageUrl } from "@/lib/api";
import { CutoutItem } from "@/types";

interface ProductMatchViewProps {
  products: CutoutItem[];
  search: string;
  threshold: number;
  onInspectItem?: (item: CutoutItem) => void;
}

function positionLabel(item: CutoutItem): string | null {
  const position = item.planogram_position;
  if (position?.status === "calibrated") {
    return `Row ${position.row_index + 1} · ${position.x_start_cm.toFixed(1)}–${position.x_end_cm.toFixed(1)} cm from left`;
  }
  return item.row_number ? `Detected row ${item.row_number}` : null;
}

export function ProductMatchView({ products, search, threshold, onInspectItem }: ProductMatchViewProps) {
  const query = search.trim().toLocaleLowerCase();
  const filteredProducts = products.filter((item) => {
    if (!query) return true;
    const match = item.catalog_match;
    return [
      item.id,
      match?.top_candidate?.name,
      match?.top_candidate?.sku,
      match?.runner_up?.name,
      match?.runner_up?.sku,
      `cluster ${item.cluster_id ?? ""}`,
    ].some((value) => value?.toLocaleLowerCase().includes(query));
  });
  const confirmedCount = products.filter((item) => item.catalog_match?.status === "matched").length;

  return (
    <section className="flex flex-col" data-testid="product-match-view" aria-label="Individual product matches">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#262b36] bg-[#161a22] px-4 py-3 text-xs text-gray-400">
        <span>
          Showing <strong className="text-gray-200">{filteredProducts.length}</strong> of {products.length} product crops
        </span>
        <span>
          <strong className="text-emerald-400">{confirmedCount}</strong> confirmed · threshold {(threshold * 100).toFixed(0)}%
        </span>
      </div>

      {filteredProducts.length === 0 ? (
        <div className="flex min-h-48 flex-col items-center justify-center px-6 py-10 text-center text-gray-500" data-testid="product-match-empty">
          <Search className="mb-2 h-7 w-7 opacity-60" />
          <p className="text-sm font-medium text-gray-300">No product crops match this search.</p>
          <p className="mt-1 text-xs">Try a crop ID, catalogue product name, or SKU.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-3 p-4 md:grid-cols-2 xl:grid-cols-3">
          {filteredProducts.map((item) => {
            const match = item.catalog_match;
            const candidate = match?.top_candidate;
            const score = match?.similarity;
            const confirmed = match?.status === "matched";
            const location = positionLabel(item);

            return (
              <article
                key={item.id}
                className="min-w-0 rounded-xl border border-[#2b313d] bg-[#13161c] p-3"
                data-testid="product-match-item"
                data-cutout-id={item.id}
              >
                <div className="mb-3 flex items-center justify-between gap-2">
                  <div className="min-w-0">
                    <h3 className="truncate font-mono text-xs font-semibold text-gray-200">{item.id}</h3>
                    <p className="mt-0.5 text-[11px] text-gray-500">
                      {location ?? `Cluster #${item.cluster_id ?? "—"}`}
                    </p>
                  </div>
                  <span
                    className={`inline-flex shrink-0 items-center gap-1 rounded-full border px-2 py-1 text-[10px] font-semibold ${
                      confirmed
                        ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
                        : "border-amber-500/30 bg-amber-500/10 text-amber-300"
                    }`}
                    data-testid="product-match-status"
                  >
                    {confirmed ? <CheckCircle2 className="h-3 w-3" /> : <HelpCircle className="h-3 w-3" />}
                    {confirmed ? "Confirmed" : "Needs review"}
                  </span>
                </div>

                <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2">
                  <button
                    type="button"
                    className="flex h-28 min-w-0 items-center justify-center rounded-lg border border-[#262b36] bg-[#0d0f12] p-2 hover:border-amber-400 focus:outline-none focus:ring-2 focus:ring-amber-400"
                    onClick={() => onInspectItem?.(item)}
                    aria-label={`Inspect input crop ${item.id}`}
                  >
                    <img src={getImageUrl(item.crop_path)} alt={`Input crop ${item.id}`} className="max-h-full max-w-full object-contain" loading="lazy" />
                  </button>
                  <span aria-hidden="true" className="px-1 text-lg text-gray-500">→</span>
                  {candidate ? (
                    <div className="flex h-28 min-w-0 flex-col items-center justify-center rounded-lg border border-[#262b36] bg-[#0d0f12] p-2 text-center">
                      <div className="flex min-h-14 w-full items-center justify-center rounded bg-white p-1">
                        <img src={getImageUrl(candidate.image_path)} alt={`${candidate.name} catalogue image`} className="max-h-14 max-w-full object-contain" loading="lazy" />
                      </div>
                      <p className="mt-1 w-full truncate text-[11px] font-semibold text-gray-100" title={candidate.name}>{candidate.name}</p>
                      <p className="w-full truncate font-mono text-[10px] text-amber-300" title={candidate.sku}>{candidate.sku}</p>
                    </div>
                  ) : (
                    <div className="flex h-28 min-w-0 flex-col items-center justify-center rounded-lg border border-dashed border-[#363d4b] p-2 text-center text-gray-500">
                      <XCircle className="mb-1 h-4 w-4" />
                      <span className="text-[10px]">No catalogue candidate</span>
                    </div>
                  )}
                </div>

                <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-[11px]">
                  <span className="text-gray-400">Raw CLIP similarity</span>
                  <span className={confirmed ? "font-mono font-semibold text-emerald-300" : "font-mono font-semibold text-amber-300"}>
                    {typeof score === "number" ? `${(score * 100).toFixed(1)}%` : "Score unavailable"}
                  </span>
                </div>
                {match?.matching_method?.startsWith("color_filter") && (
                  <p className="mt-1 text-[10px] leading-4 text-gray-500">
                    Color gate kept {match.color_filter_candidate_count_after ?? "—"}/{match.color_filter_candidate_count_before ?? "—"} candidates
                    {" · "}candidate color match {typeof match.color_similarity === "number" ? `${(match.color_similarity * 100).toFixed(0)}%` : "unavailable"}
                  </p>
                )}
                {!confirmed && (
                  <p className="mt-1 text-[10px] leading-4 text-gray-500">
                    {match?.reason === "color_filter_fallback"
                      ? "Color filter could not safely narrow the catalogue; this result needs review."
                      : match?.reason === "ambiguous_candidates"
                      ? "Top catalogue candidates are too close to confirm."
                      : typeof score === "number"
                        ? `Closest candidate only; confirmation requires ≥ ${(threshold * 100).toFixed(0)}% and an unambiguous lead.`
                        : "No usable CLIP match is available for this crop."}
                  </p>
                )}
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
