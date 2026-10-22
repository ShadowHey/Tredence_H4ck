"use client";

import { useEffect, useMemo, useState } from "react";
import { Download, MapPin, RefreshCw } from "lucide-react";
import { API_BASE_URL, api, getImageUrl } from "@/lib/api";
import { ComplianceIssue, ComplianceReport, CutoutItem, ProcessedOutput } from "@/types";

const label = (value: string) => value.replaceAll("_", " ");

export function ComplianceReportPanel({ output }: { output: ProcessedOutput }) {
  const [report, setReport] = useState<ComplianceReport | null>(null);
  const [cutouts, setCutouts] = useState<CutoutItem[]>([]);
  const [imageDimensions, setImageDimensions] = useState({ width: 0, height: 0 });
  const [selectedIssueId, setSelectedIssueId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("all");
  const [severityFilter, setSeverityFilter] = useState("all");
  const [busyIssue, setBusyIssue] = useState<string | null>(null);
  const [notes, setNotes] = useState<Record<string, string>>({});

  const load = async () => {
    try { setError(null); setReport(await api.getOutputCompliance(output.id)); }
    catch (err) { setError(err instanceof Error ? err.message : "Could not load compliance report."); }
  };
  useEffect(() => { void load(); }, [output.id]);
  useEffect(() => { api.getOutputCutouts(output.id).then(data => setCutouts([...data.products, ...data.empty_spaces, ...data.shelves])).catch(() => setCutouts([])); }, [output.id]);

  const visibleIssues = useMemo(() => (report?.issues ?? []).filter((issue) =>
    (statusFilter === "all" || issue.status === statusFilter) &&
    (severityFilter === "all" || (issue.severity ?? "warning") === severityFilter)), [report, statusFilter, severityFilter]);
  const selectedIssue = report?.issues.find(issue => issue.issue_id === selectedIssueId);
  const evidenceIds = new Set([selectedIssue?.cutout_id, ...(selectedIssue?.evidence?.product_cutout_ids ?? []), ...(selectedIssue?.evidence?.empty_space_cutout_ids ?? [])].filter(Boolean));
  const highlightedCutouts = cutouts.filter(cutout => evidenceIds.has(cutout.id));

  const update = async (issue: ComplianceIssue, status: "open" | "acknowledged" | "resolved", note = notes[issue.issue_id] ?? issue.resolution_note ?? "") => {
    try {
      setBusyIssue(issue.issue_id);
      await api.updateComplianceIssue(output.id, issue.issue_id, { status, note: note.trim() || undefined });
      await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Could not update issue status."); }
    finally { setBusyIssue(null); }
  };

  const exportReport = async () => {
    try { setError(null); await api.exportComplianceReport(output.id); }
    catch (err) { setError(err instanceof Error ? err.message : "Could not export compliance report."); }
  };

  return <section className="rounded-2xl border border-[#262b36] bg-[#13161c] overflow-hidden" data-testid="compliance-report">
    <div className="flex flex-wrap items-center justify-between gap-3 p-5 border-b border-[#262b36]">
      <div>
        <div className="flex flex-wrap items-center gap-2"><h2 className="font-semibold text-gray-100">Shelf compliance report</h2>
          {report && <span data-testid="audit-status" className={`rounded px-2 py-1 text-[10px] uppercase ${report.status === "complete" ? "bg-emerald-500/10 text-emerald-300" : "bg-amber-500/10 text-amber-300"}`}>{report.status === "complete" ? "Audit complete" : "Review required"}</span>}
        </div>
        <p className="text-xs text-gray-400 mt-1">Findings are tied to this input image and its frozen planogram/shelf snapshot.</p>
      </div>
      <div className="flex gap-2">
        <button onClick={() => void load()} className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-[#353b48] text-sm text-gray-300"><RefreshCw className="w-4 h-4"/>Refresh</button>
        <button onClick={() => void exportReport()} className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-amber-500 text-gray-950 text-sm font-semibold"><Download className="w-4 h-4"/>Export JSON</button>
      </div>
    </div>
    {error && <div role="alert" className="m-4 p-3 rounded-lg border border-red-500/30 bg-red-500/10 text-sm text-red-300">{error}</div>}
    {report && <>
      {report.layout_comparison && <div className="mx-4 mt-4 rounded-xl border border-[#262b36] bg-[#0d0f12] p-4" data-testid="normalized-layout-comparison">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div><h3 className="text-sm font-semibold text-gray-100">Normalized shelf layout</h3>
            <p className="mt-1 text-xs text-gray-400">Rows run top to bottom; positions and empty intervals are measured from the left across shelf width.</p></div>
          <span className={`rounded px-2 py-1 text-[10px] uppercase ${report.layout_comparison.comparison_status === "ready" ? "bg-emerald-500/10 text-emerald-300" : "bg-amber-500/10 text-amber-300"}`}>
            {report.layout_comparison.comparison_status === "ready" ? "Calibrated" : "Needs review"}
          </span>
        </div>
        {report.layout_comparison.rows.map(row => <div key={row.row_index} className="mt-3 grid grid-cols-[64px_1fr] gap-3 border-t border-[#262b36] pt-3 text-xs">
          <div className="font-medium text-gray-300">Row {row.row_number}</div>
          <div className="space-y-1.5 text-gray-400">
            <div>Expected {row.expected_facings.length} facings · detected {row.observed_products.length} products · {row.observed_empty_regions.length} empty-space regions</div>
            {row.expected_facings.length > 0 && <div className="flex flex-wrap gap-1.5">{row.expected_facings.map(slot => <span key={slot.slot_id} className="rounded border border-[#303642] px-1.5 py-1" title={`${(slot.normalized_start * 100).toFixed(1)}–${(slot.normalized_end * 100).toFixed(1)}% of shelf width`}>
              {slot.ordinal_from_left}. {slot.sku || "Expected item"} · {label(slot.status)}
            </span>)}</div>}
            <div>Expected open width: {row.expected_free_intervals.length} interval(s) · observed open width: {row.observed_free_intervals.length} interval(s)</div>
          </div>
        </div>)}
      </div>}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-2 p-4">
        {[["Findings", report.issues.length], ["Open", report.issues.filter(i => i.status === "open").length], ["Acknowledged", report.issues.filter(i => i.status === "acknowledged").length], ["Resolved", report.issues.filter(i => i.status === "resolved").length], ["Review needed", report.summary.needs_review ?? 0]].map(([name, value]) =>
          <div key={String(name)} className="rounded-lg border border-[#262b36] bg-[#0d0f12] p-3"><div className="text-[10px] uppercase text-gray-500">{name}</div><div className="text-xl font-semibold text-gray-100 mt-1">{value}</div></div>)}
      </div>
      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)] gap-4 p-4 pt-0">
        <div className="rounded-xl border border-[#262b36] bg-[#0d0f12] p-2 self-start">
          <div className="relative w-fit max-w-full mx-auto" data-testid="annotated-issue-overlay">
            <img src={getImageUrl(output.annotated_image_path)} alt={`Annotated evidence for ${output.source_filename}`} onLoad={event => setImageDimensions({ width: event.currentTarget.naturalWidth, height: event.currentTarget.naturalHeight })} className="block max-w-full max-h-[620px] w-auto object-contain" />
            {(highlightedCutouts.length > 0 || selectedIssue?.bbox_xyxy) && imageDimensions.width > 0 && <svg aria-label="Selected issue detection overlay" className="absolute inset-0 w-full h-full pointer-events-none" viewBox={`0 0 ${imageDimensions.width} ${imageDimensions.height}`} preserveAspectRatio="none">
              {highlightedCutouts.map(cutout => <rect key={cutout.id} data-testid={`evidence-overlay-${cutout.id}`} x={cutout.bbox_xyxy[0]} y={cutout.bbox_xyxy[1]} width={cutout.bbox_xyxy[2] - cutout.bbox_xyxy[0]} height={cutout.bbox_xyxy[3] - cutout.bbox_xyxy[1]} fill={cutout.category === "empty_space" ? "rgba(59,130,246,.18)" : "rgba(245,158,11,.15)"} stroke={cutout.category === "empty_space" ? "#3b82f6" : "#f59e0b"} strokeWidth="5" />)}
              {selectedIssue?.bbox_xyxy && <rect x={selectedIssue.bbox_xyxy[0]} y={selectedIssue.bbox_xyxy[1]} width={selectedIssue.bbox_xyxy[2] - selectedIssue.bbox_xyxy[0]} height={selectedIssue.bbox_xyxy[3] - selectedIssue.bbox_xyxy[1]} fill="rgba(239,68,68,.16)" stroke="#ef4444" strokeWidth="5" />}
            </svg>}
          </div>
          <p className="text-xs text-gray-400 p-2">Annotated shelf evidence · {output.source_filename}</p>
        </div>
        <div className="min-w-0">
          <div className="flex gap-2 mb-3">
            <select aria-label="Filter by issue status" value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="bg-[#0d0f12] border border-[#353b48] rounded-lg px-2 py-2 text-xs text-gray-200"><option value="all">All statuses</option><option value="open">Open</option><option value="acknowledged">Acknowledged</option><option value="resolved">Resolved</option></select>
            <select aria-label="Filter by severity" value={severityFilter} onChange={e => setSeverityFilter(e.target.value)} className="bg-[#0d0f12] border border-[#353b48] rounded-lg px-2 py-2 text-xs text-gray-200"><option value="all">All severity</option><option value="error">Errors</option><option value="warning">Warnings / review</option></select>
          </div>
          <div className="space-y-3 max-h-[700px] overflow-y-auto pr-1">
            {visibleIssues.map(issue => <article key={issue.issue_id} onClick={() => setSelectedIssueId(issue.issue_id)} className={`rounded-xl border bg-[#1a1e26] p-4 cursor-pointer ${selectedIssueId === issue.issue_id ? "border-amber-400" : "border-[#303642]"}`} data-testid="compliance-issue">
              <div className="flex justify-between gap-2 items-start">
                <div><h3 className="font-semibold text-sm text-gray-100 capitalize">{label(issue.type)}</h3><p className="text-xs text-gray-400 mt-1">{issue.message || label(issue.reason || "compliance finding")}</p></div>
                <span className={`shrink-0 text-[10px] uppercase rounded px-2 py-1 ${issue.severity === "error" ? "bg-red-500/10 text-red-300" : "bg-amber-500/10 text-amber-300"}`}>{issue.severity || "warning"}</span>
              </div>
              <div className="mt-3 flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-blue-200">
                {issue.row_index != null && <span className="inline-flex items-center gap-1"><MapPin className="w-3 h-3"/>Row {issue.row_index + 1}</span>}
                {issue.x_start_cm != null && issue.x_end_cm != null && <span>{issue.x_start_cm.toFixed(1)}–{issue.x_end_cm.toFixed(1)} cm from left</span>}
                {issue.ordinal_from_left != null && <span>Observed item {issue.ordinal_from_left} from left</span>}
                {issue.expected_ordinal_from_left != null && <span>Expected position {issue.expected_ordinal_from_left} from left</span>}
                {issue.sku && <span>SKU {issue.sku}</span>}{issue.expected_sku && <span>Expected {issue.expected_sku}</span>}
                {issue.expected_quantity != null && issue.observed_quantity != null && <span data-testid="quantity-evidence">Detected {issue.observed_quantity} / {issue.expected_quantity} facings{issue.occupancy_ratio != null ? ` (${Math.round(issue.occupancy_ratio * 100)}%)` : ""}</span>}
                {issue.cutout_id && <span>Detection {issue.cutout_id}</span>}{issue.slot_id && <span>Slot {issue.slot_id}</span>}
                {(issue.evidence?.product_cutout_ids?.length || issue.evidence?.empty_space_cutout_ids?.length) ? <span>Evidence: {[...(issue.evidence?.product_cutout_ids ?? []), ...(issue.evidence?.empty_space_cutout_ids ?? [])].join(", ")}</span> : null}
                {issue.label_zone_id && <span>Label zone {issue.label_zone_id}</span>}
                {issue.evidence_crop_path && <a href={getImageUrl(issue.evidence_crop_path)} target="_blank" rel="noreferrer" className="text-amber-300 underline">View label crop</a>}
              </div>
              {selectedIssueId === issue.issue_id && <div className="mt-3 grid grid-cols-2 gap-2" data-testid="issue-evidence-gallery">
                {highlightedCutouts.map(cutout => <div key={cutout.id} className="rounded-lg border border-[#303642] bg-[#0d0f12] p-2">
                  <img src={getImageUrl(cutout.crop_path)} alt={`${cutout.category === "empty_space" ? "Empty-space" : cutout.category === "product" ? "Product" : "Shelf"} evidence ${cutout.id}`} className="w-full h-24 object-contain rounded" />
                  <div className="mt-1 flex items-center justify-between gap-2 text-[10px] text-gray-400"><span className="capitalize">{label(cutout.category)} evidence</span>
                    <a aria-label={`Download ${label(cutout.category)} cutout ${cutout.id}`} href={`${API_BASE_URL.replace(/\/$/, "")}/api/v1/outputs/${output.id}/cutouts/${encodeURIComponent(cutout.id)}/download`} className="text-amber-300 underline">Download</a></div>
                </div>)}
                {!highlightedCutouts.length && <p className="col-span-2 text-xs text-gray-500">No crop files are available for this finding; use its row and centimetre location as evidence.</p>}
              </div>}
              <p className="text-xs text-gray-300 mt-3"><span className="text-gray-500">Recommended: </span>{issue.recommended_action}</p>
              <label className="block mt-3"><span className="text-[10px] uppercase tracking-wide text-gray-500">Operator note</span><textarea aria-label={`Operator note for ${issue.issue_id}`} value={notes[issue.issue_id] ?? issue.resolution_note ?? ""} onChange={event => setNotes(current => ({ ...current, [issue.issue_id]: event.target.value }))} maxLength={2000} rows={2} className="mt-1 w-full resize-y rounded-lg bg-[#0d0f12] border border-[#353b48] px-2 py-1.5 text-xs text-gray-200" placeholder="Add context for the next audit operator…" /></label>
              <div className="flex items-center justify-between gap-2 mt-3 pt-3 border-t border-[#303642]"><span className="text-xs text-gray-400 capitalize">{label(issue.status)}</span><div className="flex gap-2">
                {(notes[issue.issue_id] ?? issue.resolution_note ?? "") !== (issue.resolution_note ?? "") && <button disabled={busyIssue === issue.issue_id} onClick={() => void update(issue, issue.status)} className="px-2 py-1 rounded border border-blue-500/30 text-xs text-blue-300 disabled:opacity-50">Save note</button>}
                {issue.status !== "acknowledged" && <button disabled={busyIssue === issue.issue_id} onClick={() => void update(issue, "acknowledged")} className="px-2 py-1 rounded border border-[#454d5a] text-xs text-gray-300 disabled:opacity-50">Acknowledge</button>}
                {issue.status !== "resolved" && <button disabled={busyIssue === issue.issue_id} onClick={() => void update(issue, "resolved")} className="px-2 py-1 rounded bg-emerald-600/20 border border-emerald-500/30 text-xs text-emerald-300 disabled:opacity-50">Resolve</button>}
                {issue.status !== "open" && <button disabled={busyIssue === issue.issue_id} onClick={() => void update(issue, "open")} className="px-2 py-1 rounded border border-[#454d5a] text-xs text-gray-300 disabled:opacity-50">Reopen</button>}
              </div></div>
            </article>)}
            {!visibleIssues.length && <div className="p-8 text-center text-sm text-gray-500 rounded-xl border border-dashed border-[#353b48]">No findings match these filters.</div>}
          </div>
        </div>
      </div>
    </>}
  </section>;
}
