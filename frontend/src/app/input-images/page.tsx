"use client";

import { ChangeEvent, useEffect, useMemo, useState } from "react";
import { CheckCircle2, ChevronRight, ImagePlus, Loader2, Play, Trash2, UploadCloud, XCircle } from "lucide-react";
import { api, getImageUrl } from "@/lib/api";
import { InputImage, Planogram, PlanogramSummary } from "@/types";

const statusClasses: Record<InputImage["status"], string> = {
  ready: "bg-slate-500/15 text-slate-300 border-slate-400/20",
  queued: "bg-amber-500/15 text-amber-300 border-amber-400/30",
  processing: "bg-blue-500/15 text-blue-300 border-blue-400/30",
  processed: "bg-emerald-500/15 text-emerald-300 border-emerald-400/30",
  failed: "bg-red-500/15 text-red-300 border-red-400/30",
};

export default function InputImagesPage() {
  const [images, setImages] = useState<InputImage[]>([]);
  const [planograms, setPlanograms] = useState<PlanogramSummary[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [activePlanogram, setActivePlanogram] = useState<Planogram | null>(null);
  const [planogramId, setPlanogramId] = useState("");
  const [shelfId, setShelfId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const active = useMemo(() => images.find((image) => image.id === activeId) ?? null, [images, activeId]);
  const load = async () => {
    try {
      const [inputRows, planogramRows] = await Promise.all([api.getInputImages(), api.getPlanograms()]);
      setImages(inputRows);
      setPlanograms(planogramRows);
      setActiveId((current) => current && inputRows.some((row) => row.id === current) ? current : inputRows[0]?.id ?? null);
    } catch (err) { setError(err instanceof Error ? err.message : "Unable to load input images."); }
  };

  useEffect(() => { void load(); }, []);
  useEffect(() => {
    const hasActiveJob = images.some((image) => image.status === "queued" || image.status === "processing");
    if (!hasActiveJob) return;
    const timer = window.setInterval(() => void load(), 3000);
    return () => window.clearInterval(timer);
  }, [images]);

  useEffect(() => {
    if (!active) return;
    setPlanogramId(active.planogram_id ? String(active.planogram_id) : "");
    setShelfId(active.shelf_id ? String(active.shelf_id) : "");
    if (active.planogram_id) void api.getPlanogram(active.planogram_id).then(setActivePlanogram).catch(() => setActivePlanogram(null));
    else setActivePlanogram(null);
  }, [activeId]); // selection deliberately owns the target form

  const onUpload = async (event: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files ?? []);
    event.target.value = "";
    if (!files.length) return;
    try {
      setBusy(true); setError(null);
      const rows = await api.uploadInputImages(files);
      await load();
      setActiveId(rows[0]?.id ?? null);
    } catch (err) { setError(err instanceof Error ? err.message : "Upload failed."); }
    finally { setBusy(false); }
  };

  const onPlanogramChange = async (value: string) => {
    setPlanogramId(value); setShelfId(""); setActivePlanogram(null);
    if (!value) return;
    try { setActivePlanogram(await api.getPlanogram(Number(value))); }
    catch (err) { setError(err instanceof Error ? err.message : "Unable to load shelves."); }
  };

  const processActive = async () => {
    if (!active || !planogramId || !shelfId) return;
    try {
      setBusy(true); setError(null);
      await api.processInputImage(active.id, { planogram_id: Number(planogramId), shelf_id: Number(shelfId) });
      await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Unable to queue this image."); }
    finally { setBusy(false); }
  };

  const deleteImage = async (image: InputImage) => {
    if (!window.confirm(`Delete "${image.original_filename}"${image.status === "processed" ? " and its derived output" : ""}?`)) return;
    try { setBusy(true); await api.deleteInputImage(image.id); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : "Unable to delete image."); }
    finally { setBusy(false); }
  };

  const clearSlate = async () => {
    const removable = images.filter((image) => image.status === "ready" || image.status === "failed");
    if (!removable.length || !window.confirm(`Remove ${removable.length} ready or failed image(s)?`)) return;
    try { setBusy(true); await Promise.all(removable.map((image) => api.deleteInputImage(image.id))); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : "Unable to clear the input slate."); }
    finally { setBusy(false); }
  };

  const canProcess = Boolean(active && ["ready", "failed"].includes(active.status) && planogramId && shelfId);
  return <div className="flex-1 overflow-y-auto bg-[#0d0f12]" data-testid="input-images-page">
    <header className="min-h-16 px-6 py-3 border-b border-[#262b36] flex flex-wrap gap-3 items-center justify-between bg-[#13161c]">
      <div><h1 className="text-lg font-semibold">Input Images</h1><p className="text-xs text-gray-400">Assign one shelf photo to one saved planogram shelf, then process it.</p></div>
      <div className="flex gap-2">
        <label className="cursor-pointer inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-amber-500 text-gray-950 font-semibold text-sm"><UploadCloud className="w-4 h-4" /> Upload images<input className="hidden" type="file" accept="image/jpeg,image/png,image/webp,image/bmp" multiple onChange={onUpload} disabled={busy} /></label>
        <button onClick={clearSlate} disabled={busy || !images.some((image) => image.status === "ready" || image.status === "failed")} className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-[#353b48] text-gray-300 text-sm disabled:opacity-40"><Trash2 className="w-4 h-4" /> Clear slate</button>
      </div>
    </header>
    {error && <div role="alert" className="mx-6 mt-4 p-3 text-sm rounded-lg bg-red-500/10 border border-red-500/30 text-red-300">{error}</div>}
    <div className="p-6 grid grid-cols-1 xl:grid-cols-[minmax(320px,0.85fr)_minmax(460px,1.4fr)] gap-6">
      <section className="rounded-xl border border-[#262b36] bg-[#13161c] overflow-hidden">
        <div className="p-4 border-b border-[#262b36] flex justify-between"><div><h2 className="font-semibold">Staged images</h2><p className="text-xs text-gray-400 mt-1">Choose one image to assign and process.</p></div><span className="text-sm text-amber-400">{images.length}</span></div>
        {!images.length ? <div className="p-10 text-center text-gray-400"><ImagePlus className="mx-auto w-8 h-8 mb-3 text-gray-500" /><p className="font-medium text-gray-300">No images yet</p><p className="text-xs mt-1">Upload shelf photographs to start.</p></div> : <div className="p-3 space-y-2">{images.map((image) => <button key={image.id} onClick={() => setActiveId(image.id)} className={`w-full text-left p-3 rounded-lg border transition-colors ${activeId === image.id ? "border-amber-400/50 bg-amber-500/10" : "border-[#2a2f39] bg-[#1a1e26] hover:bg-[#202530]"}`}>
          <div className="flex gap-3"><img src={getImageUrl(image.storage_path)} alt="" className="w-14 h-12 rounded object-cover bg-[#0d0f12]" /><div className="min-w-0 flex-1"><div className="font-medium text-sm truncate">{image.original_filename}</div><div className="mt-1 flex items-center justify-between"><span className={`text-[11px] border px-1.5 py-0.5 rounded-full capitalize ${statusClasses[image.status]}`}>{image.status}</span><span className="text-[11px] text-gray-500">{(image.size_bytes / 1024 / 1024).toFixed(1)} MB</span></div></div><ChevronRight className="w-4 h-4 text-gray-500 self-center" /></div>
        </button>)}</div>}
      </section>
      <section className="rounded-xl border border-[#262b36] bg-[#13161c] min-h-[520px]">
        {!active ? <div className="h-full min-h-[520px] flex items-center justify-center text-gray-500">Select an input image to continue.</div> : <div className="p-5">
          <div className="flex justify-between gap-3 mb-5"><div><h2 className="font-semibold text-lg truncate">{active.original_filename}</h2><p className="text-xs text-gray-400 mt-1">One input image → one planogram shelf.</p></div><button onClick={() => void deleteImage(active)} disabled={busy || active.status === "processing"} title="Delete image" className="p-2 h-fit rounded-lg text-red-300 border border-red-500/25 hover:bg-red-500/10 disabled:opacity-40"><Trash2 className="w-4 h-4" /></button></div>
          <img src={getImageUrl(active.storage_path)} alt={active.original_filename} className="w-full max-h-72 object-contain rounded-lg bg-[#0d0f12] border border-[#262b36]" />
          <div className="mt-5 grid md:grid-cols-2 gap-4"><label className="text-sm text-gray-300">Planogram<select aria-label="Planogram" value={planogramId} onChange={(e) => void onPlanogramChange(e.target.value)} disabled={busy || active.status !== "ready" && active.status !== "failed"} className="mt-1.5 w-full bg-[#0d0f12] border border-[#353b48] rounded-lg p-2.5 text-sm"><option value="">Select a planogram</option>{planograms.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}</select></label>
            <label className="text-sm text-gray-300">Shelf<select aria-label="Shelf" value={shelfId} onChange={(e) => setShelfId(e.target.value)} disabled={!activePlanogram || busy || active.status !== "ready" && active.status !== "failed"} className="mt-1.5 w-full bg-[#0d0f12] border border-[#353b48] rounded-lg p-2.5 text-sm"><option value="">Select a shelf</option>{activePlanogram?.shelves.map((shelf) => <option key={shelf.id} value={shelf.id}>{shelf.name}</option>)}</select></label></div>
          {activePlanogram?.shelves.find((shelf) => shelf.id === Number(shelfId)) && (() => { const shelf = activePlanogram.shelves.find((s) => s.id === Number(shelfId))!; return <div className="mt-3 p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 text-sm text-blue-200">{shelf.name}: {shelf.width_cm} cm × {shelf.total_height_cm} cm · {shelf.row_count} rows</div>; })()}
          {active.error_message && <div className="mt-3 text-sm text-red-300 flex gap-2"><XCircle className="w-4 h-4 shrink-0" />{active.error_message}</div>}
          {active.status === "processed" && <div className="mt-4 p-3 rounded-lg bg-emerald-500/10 border border-emerald-400/25 text-sm text-emerald-200 flex gap-2"><CheckCircle2 className="w-4 h-4" />Processed successfully. Open Outputs to review the annotation.</div>}
          <button onClick={() => void processActive()} disabled={!canProcess || busy} className="mt-5 inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-amber-500 text-gray-950 font-semibold text-sm disabled:opacity-40"><Play className="w-4 h-4" />{busy ? <Loader2 className="w-4 h-4 animate-spin" /> : null} Process this image</button>
        </div>}
      </section>
    </div>
  </div>;
}
