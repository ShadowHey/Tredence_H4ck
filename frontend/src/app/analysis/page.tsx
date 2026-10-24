"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Sparkles,
  Layers,
  CheckCircle2,
  XCircle,
  Loader2,
  RefreshCw,
  Crop,
  ArrowLeft,
  Store,
  ChevronRight,
  FileQuestion,
  Tag,
  ZoomIn,
  X,
  ExternalLink,
} from "lucide-react";
import { api, getImageUrl } from "@/lib/api";
import { ProcessedOutput, OutputAnalysisResponse, CutoutItem } from "@/types";
import { AnalysisTable } from "@/components/analysis/AnalysisTable";
import { CutoutViewerModal } from "@/components/outputs/CutoutViewerModal";
import { ComplianceReportPanel } from "@/components/analysis/ComplianceReportPanel";

function AnalysisContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const queryOutputId = searchParams.get("outputId");
  const parsedOutputId = queryOutputId ? parseInt(queryOutputId, 10) : null;

  const [outputs, setOutputs] = useState<ProcessedOutput[]>([]);
  const [selectedOutputId, setSelectedOutputId] = useState<number | null>(parsedOutputId);
  const [analysisData, setAnalysisData] = useState<OutputAnalysisResponse | null>(null);
  const [loadingOutputs, setLoadingOutputs] = useState<boolean>(true);
  const [loadingAnalysis, setLoadingAnalysis] = useState<boolean>(false);
  const [reanalyzing, setReanalyzing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Modals state
  const [activeCutoutModalId, setActiveCutoutModalId] = useState<number | null>(null);
  const [enlargedCrop, setEnlargedCrop] = useState<CutoutItem | null>(null);

  // 1. Fetch available outputs
  useEffect(() => {
    let isMounted = true;
    setLoadingOutputs(true);
    api
      .getProcessedOutputs()
      .then((data) => {
        if (!isMounted) return;
        setOutputs(data);
        setLoadingOutputs(false);

        // If no explicit output was in the query param and we have outputs, default to the first
        if (!selectedOutputId && data.length > 0) {
          setSelectedOutputId(data[0].id);
        }
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err instanceof Error ? err.message : "Failed to load outputs.");
        setLoadingOutputs(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  // Sync selectedOutputId with query param
  useEffect(() => {
    if (parsedOutputId && parsedOutputId !== selectedOutputId) {
      setSelectedOutputId(parsedOutputId);
    }
  }, [parsedOutputId]);

  // 2. Fetch analysis for selected output
  useEffect(() => {
    if (!selectedOutputId) {
      setAnalysisData(null);
      return;
    }

    let isMounted = true;
    setLoadingAnalysis(true);
    setError(null);

    api
      .getOutputAnalysis(selectedOutputId)
      .then((data) => {
        if (!isMounted) return;
        setAnalysisData(data);
        setLoadingAnalysis(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err instanceof Error ? err.message : "Failed to load analysis for this output.");
        setLoadingAnalysis(false);
      });

    return () => {
      isMounted = false;
    };
  }, [selectedOutputId]);

  const handleSelectOutput = (id: number) => {
    setSelectedOutputId(id);
    router.push(`/analysis?outputId=${id}`);
  };

  const handleReanalyze = async () => {
    if (!selectedOutputId) return;
    try {
      setReanalyzing(true);
      setError(null);
      const updated = await api.analyzeOutput(selectedOutputId);
      setAnalysisData(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Re-analysis failed.");
    } finally {
      setReanalyzing(false);
    }
  };

  const currentOutputMeta = outputs.find((o) => o.id === selectedOutputId);

  return (
    <div className="flex-1 overflow-y-auto bg-[#0d0f12] text-gray-100 flex flex-col" data-testid="analysis-page">
      {/* Header */}
      <header className="px-6 py-4 border-b border-[#262b36] bg-[#13161c] flex flex-wrap items-center justify-between gap-4 shrink-0">
        <div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-amber-400" />
            </div>
            <h1 className="text-lg font-bold text-gray-100">
              Planogram Product Analysis & Catalog Matching
            </h1>
          </div>
          <p className="text-xs text-gray-400 mt-1">
            Intra-shelf visual grouping and CLIP matching against this shelf’s catalogue (90% minimum; ambiguous or lower-confidence results need review).
          </p>
        </div>

        {/* Top actions & Output Switcher */}
        <div className="flex items-center gap-3">
          {outputs.length > 0 && (
            <div className="flex items-center gap-2 bg-[#1a1e26] border border-[#262b36] rounded-xl px-3 py-1.5 text-xs">
              <span className="text-gray-400 font-medium">Shelf Image:</span>
              <select
                value={selectedOutputId ?? ""}
                onChange={(e) => handleSelectOutput(Number(e.target.value))}
                className="bg-transparent text-gray-200 font-semibold focus:outline-none cursor-pointer"
                data-testid="output-selector-dropdown"
              >
                {outputs.map((out) => (
                  <option key={out.id} value={out.id} className="bg-[#13161c] text-gray-200">
                    Output #{out.id} — {out.source_filename}
                  </option>
                ))}
              </select>
            </div>
          )}

          {selectedOutputId && (
            <>
              <button
                onClick={() => setActiveCutoutModalId(selectedOutputId)}
                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl border border-amber-500/40 bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 text-xs font-semibold transition-all shadow-sm"
                data-testid="open-cutouts-btn"
              >
                <Crop className="w-3.5 h-3.5 text-amber-400" />
                Inspect Cutouts
              </button>

              <button
                onClick={handleReanalyze}
                disabled={reanalyzing || loadingAnalysis}
                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-gray-950 text-xs font-bold transition-all shadow-sm disabled:opacity-50"
                data-testid="reanalyze-btn"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${reanalyzing ? "animate-spin" : ""}`} />
                {reanalyzing ? "Re-running YOLO..." : "Re-run YOLO Analysis"}
              </button>
            </>
          )}
        </div>
      </header>

      {/* Main Body */}
      <main className="p-6 flex-1 space-y-6">
        {selectedOutputId && currentOutputMeta && <ComplianceReportPanel key={selectedOutputId} output={currentOutputMeta} />}
        {error && (
          <div className="p-4 rounded-xl bg-red-950/40 border border-red-800 text-red-300 text-sm flex items-center gap-3">
            <XCircle className="w-5 h-5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Empty State when no outputs exist */}
        {!loadingOutputs && outputs.length === 0 && (
          <div className="h-[60vh] flex flex-col items-center justify-center text-center p-8 bg-[#13161c] border border-[#262b36] rounded-2xl">
            <FileQuestion className="w-12 h-12 text-gray-600 mb-3" />
            <h2 className="text-base font-semibold text-gray-200">No Processed Shelf Outputs</h2>
            <p className="text-xs text-gray-400 mt-1 max-w-md">
              Please stage and process shelf images from the Input Images dashboard to generate bounding boxes and semantic analysis.
            </p>
            <Link
              href="/input-images"
              className="mt-4 px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-gray-950 text-xs font-bold transition-colors"
            >
              Go to Input Images ➔
            </Link>
          </div>
        )}

        {/* Selected Output Metadata & Metric Cards */}
        {selectedOutputId && currentOutputMeta && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Shelf Info Hero Card */}
            <div className="p-4 rounded-2xl bg-[#13161c] border border-[#262b36] flex items-center gap-4 shadow-sm md:col-span-1">
              <div
                className="w-16 h-16 rounded-xl bg-[#0d0f12] overflow-hidden shrink-0 border border-[#262b36] cursor-pointer relative group"
                onClick={() => setActiveCutoutModalId(selectedOutputId)}
                title="Click to view cutouts"
              >
                <img
                  src={getImageUrl(currentOutputMeta.annotated_image_path)}
                  alt={currentOutputMeta.source_filename}
                  className="w-full h-full object-cover transition-transform group-hover:scale-105"
                />
                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                  <ZoomIn className="w-4 h-4 text-white" />
                </div>
              </div>

              <div className="min-w-0">
                <span className="text-[10px] text-amber-400 font-bold uppercase tracking-wider block">
                  Active Shelf
                </span>
                <h3 className="text-sm font-semibold text-gray-100 truncate" title={currentOutputMeta.source_filename}>
                  {currentOutputMeta.source_filename}
                </h3>
                <p className="text-xs text-gray-400 mt-0.5 truncate">
                  {currentOutputMeta.planogram_name ?? "Planogram"} · {currentOutputMeta.shelf_snapshot?.name ?? "Shelf"}
                </p>
                <p className="text-[11px] text-blue-300 mt-0.5">
                  {currentOutputMeta.shelf_snapshot
                    ? `${currentOutputMeta.shelf_snapshot.width_cm} cm × ${currentOutputMeta.shelf_snapshot.total_height_cm} cm`
                    : "Dimensions unavailable"}
                </p>
              </div>
            </div>

            {/* Total Clusters */}
            <div className="p-4 rounded-2xl bg-[#13161c] border border-[#262b36] flex flex-col justify-between shadow-sm">
              <span className="text-xs text-gray-400 font-medium flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-amber-400" />
                Total Visual Clusters
              </span>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold font-mono text-gray-100" data-testid="stat-total-clusters">
                  {analysisData ? analysisData.total_clusters : "—"}
                </span>
                <span className="text-[11px] text-gray-500">intra-shelf groups</span>
              </div>
              <span className="text-[10px] text-gray-500 mt-1">
                {analysisData?.total_product_crops ?? analysisData?.total_detections ?? 0} product crops retained
                {(analysisData?.excluded_low_confidence_product_count ?? 0) > 0 && (
                  <> · {analysisData?.excluded_low_confidence_product_count} excluded below {Math.round((analysisData?.product_confidence_threshold ?? 0.6) * 100)}% confidence</>
                )}
              </span>
            </div>

            {/* Matches above the calibrated catalogue threshold */}
            <div className="p-4 rounded-2xl bg-[#13161c] border border-[#262b36] flex flex-col justify-between shadow-sm">
              <span className="text-xs text-emerald-400 font-semibold flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                Catalog Matched (≥ {(analysisData?.catalog_confidence_threshold ?? 0.9) * 100}%)
              </span>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold font-mono text-emerald-400" data-testid="stat-matched-clusters">
                  {analysisData ? analysisData.matched_clusters_count : "—"}
                </span>
                <span className="text-[11px] text-emerald-500/80 font-medium">clusters verified</span>
              </div>
              <span className="text-[10px] text-emerald-500/70 mt-1">
                Strict semantic cutoff passed
              </span>
            </div>

            {/* Unmatched Clusters */}
            <div className="p-4 rounded-2xl bg-[#13161c] border border-[#262b36] flex flex-col justify-between shadow-sm">
              <span className="text-xs text-gray-400 font-medium flex items-center gap-1.5">
                <XCircle className="w-3.5 h-3.5 text-gray-500" />
                Unmatched Shelf Faces
              </span>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold font-mono text-gray-300" data-testid="stat-unmatched-clusters">
                  {analysisData
                    ? analysisData.total_clusters - analysisData.matched_clusters_count
                    : "—"}
                </span>
                <span className="text-[11px] text-gray-500">below threshold / review</span>
              </div>
              <span className="text-[10px] text-gray-500 mt-1">
                Threshold: {(analysisData?.catalog_confidence_threshold ?? 0.9) * 100}%
              </span>
            </div>
          </div>
        )}

        {/* 4-Column Table Container */}
        {loadingAnalysis ? (
          <div className="h-64 flex flex-col items-center justify-center text-center bg-[#13161c] border border-[#262b36] rounded-2xl p-8">
            <Loader2 className="w-8 h-8 text-amber-400 animate-spin mb-3" />
            <p className="text-sm font-semibold text-gray-200">
              Generating embeddings and computing 4-column cluster analysis...
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Extracting bounding box crops and matching against SQLite catalog
            </p>
          </div>
        ) : analysisData ? (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-gray-200 flex items-center gap-2">
                <span>Cluster Breakdown &amp; Catalog Matching</span>
                <span className="px-2 py-0.5 rounded text-[11px] bg-[#1a1e26] border border-[#262b36] text-amber-400 font-mono">
                  {analysisData.clusters.length} rows
                </span>
              </h2>
            </div>
            <div className={`rounded-lg border px-3 py-2 text-xs ${analysisData.position_calibration?.status === "calibrated" ? "border-emerald-500/20 bg-emerald-500/5 text-emerald-300" : "border-amber-500/20 bg-amber-500/5 text-amber-300"}`} data-testid="position-calibration-status">
              Position mapping: {analysisData.position_calibration?.status === "calibrated"
                ? `${analysisData.position_calibration.method.replaceAll("_", " ")} · ±${analysisData.position_calibration.position_tolerance_cm?.toFixed(1)} cm · ${analysisData.detections_with_calibrated_positions} detections mapped${analysisData.position_calibration.row_count_match === false ? ` · row detector ${analysisData.position_calibration.detected_row_count}/${analysisData.position_calibration.expected_row_count}` : ""}`
                : `Needs review${analysisData.position_calibration?.reason ? ` · ${analysisData.position_calibration.reason.replaceAll("_", " ")}` : " · no usable shelf calibration"}`}
            </div>

            {/* Render the strict 4-column Table */}
            <AnalysisTable
              clusters={analysisData.clusters}
              threshold={analysisData.catalog_confidence_threshold}
              onInspectItem={(item) => setEnlargedCrop(item)}
            />
          </div>
        ) : null}
      </main>

      {/* YOLO Bounding Box Cutout Viewer Modal */}
      <CutoutViewerModal
        outputId={activeCutoutModalId}
        onClose={() => setActiveCutoutModalId(null)}
      />

      {/* Enlarged Crop Detail Sub-Modal */}
      {enlargedCrop && (
        <div
          className="fixed inset-0 z-60 flex items-center justify-center bg-black/85 p-4"
          onClick={() => setEnlargedCrop(null)}
          data-testid="enlarged-crop-modal"
        >
          <div
            className="bg-[#1a1e26] border border-[#353b48] rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-[#262b36] pb-3">
              <div className="flex items-center gap-2">
                <Tag className="w-4 h-4 text-amber-400" />
                <h3 className="text-sm font-bold text-gray-200 font-mono">
                  Crop #{enlargedCrop.id}
                </h3>
              </div>
              <button
                onClick={() => setEnlargedCrop(null)}
                className="text-gray-400 hover:text-gray-200 p-1 rounded-lg hover:bg-[#262b36] transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="w-full h-64 bg-[#0d0f12] rounded-xl flex items-center justify-center overflow-hidden p-2 border border-[#262b36]">
              <img
                src={getImageUrl(enlargedCrop.crop_path)}
                alt={enlargedCrop.id}
                className="max-h-full max-w-full object-contain"
              />
            </div>

            <div className="grid grid-cols-2 gap-2.5 text-xs">
              <div className="p-2.5 rounded-xl bg-[#13161c] border border-[#262b36]">
                <span className="text-gray-400 block text-[10px] uppercase font-semibold">Category</span>
                <span className="text-gray-200 font-medium capitalize">{enlargedCrop.category.replace("_", " ")}</span>
              </div>
              <div className="p-2.5 rounded-xl bg-[#13161c] border border-[#262b36]">
                <span className="text-gray-400 block text-[10px] uppercase font-semibold">Detection Conf</span>
                <span className="text-emerald-400 font-semibold">{(enlargedCrop.confidence * 100).toFixed(1)}%</span>
              </div>
              {enlargedCrop.row_number && (
                <div className="p-2.5 rounded-xl bg-[#13161c] border border-[#262b36]">
                  <span className="text-gray-400 block text-[10px] uppercase font-semibold">Shelf Row</span>
                  <span className="text-blue-400 font-semibold">Row #{enlargedCrop.row_number}</span>
                </div>
              )}
              {enlargedCrop.cluster_id && (
                <div className="p-2.5 rounded-xl bg-[#13161c] border border-[#262b36]">
                  <span className="text-gray-400 block text-[10px] uppercase font-semibold">Assigned Cluster</span>
                  <span className="text-amber-400 font-semibold font-mono">Cluster #{enlargedCrop.cluster_id}</span>
                </div>
              )}
              <div className="p-2.5 rounded-xl bg-[#13161c] border border-[#262b36] col-span-2">
                <span className="text-gray-400 block text-[10px] uppercase font-semibold">Bounding Box (XYXY px)</span>
                <span className="text-gray-300 font-mono text-[11px]">
                  [{enlargedCrop.bbox_xyxy.join(", ")}]
                </span>
              </div>
              {enlargedCrop.planogram_position && (
                <div className="p-2.5 rounded-xl bg-[#13161c] border border-[#262b36] col-span-2">
                  <span className="text-gray-400 block text-[10px] uppercase font-semibold">Planogram Position</span>
                  <span className="text-gray-200 font-medium">
                    Row {enlargedCrop.planogram_position.row_index + 1} · {enlargedCrop.planogram_position.x_start_cm.toFixed(1)}–{enlargedCrop.planogram_position.x_end_cm.toFixed(1)} cm from left
                  </span>
                  <span className="text-gray-500 block text-[10px] mt-1">
                    {enlargedCrop.planogram_position.method.replaceAll("_", " ")} · ±{enlargedCrop.planogram_position.position_tolerance_cm.toFixed(1)} cm tolerance
                  </span>
                </div>
              )}
            </div>

            <button
              onClick={() => setEnlargedCrop(null)}
              className="w-full py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-gray-950 font-bold text-xs transition-colors shadow-sm"
            >
              Close Crop Inspector
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function AnalysisPage() {
  return (
    <Suspense
      fallback={
        <div className="flex-1 bg-[#0d0f12] flex items-center justify-center p-8">
          <Loader2 className="w-8 h-8 text-amber-400 animate-spin" />
        </div>
      }
    >
      <AnalysisContent />
    </Suspense>
  );
}
