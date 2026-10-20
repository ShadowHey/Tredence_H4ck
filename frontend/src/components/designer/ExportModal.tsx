"use client";

import { useState } from "react";
import { Download, Image as ImageIcon, FileJson, Check, AlertCircle } from "lucide-react";
import { exportElementAsPng, downloadJsonFile } from "@/lib/export_visual";
import { api } from "@/lib/api";
import { Planogram } from "@/types";

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  planogram: Planogram | null;
}

export function ExportModal({ isOpen, onClose, planogram }: ExportModalProps) {
  const [exportingPng, setExportingPng] = useState(false);
  const [exportingJson, setExportingJson] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  if (!isOpen || !planogram) return null;

  const handleExportPng = async () => {
    try {
      setExportingPng(true);
      setErrorMessage(null);
      setSuccessMessage(null);
      const filename = `${planogram.name.toLowerCase().replace(/[^a-z0-9]+/g, "_")}_planogram.png`;
      await exportElementAsPng("planogram-render-target", filename);
      setSuccessMessage("Visual PNG exported and downloaded successfully!");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setErrorMessage(msg || "Visual export failed.");
    } finally {
      setExportingPng(false);
    }
  };

  const handleExportJson = async () => {
    try {
      setExportingJson(true);
      setErrorMessage(null);
      setSuccessMessage(null);
      const jsonData = await api.exportPlanogramJSON(planogram.id);
      const filename = `${planogram.name.toLowerCase().replace(/[^a-z0-9]+/g, "_")}_export.json`;
      downloadJsonFile(jsonData, filename);
      setSuccessMessage("Structured JSON planogram downloaded successfully!");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setErrorMessage(msg || "JSON export failed.");
    } finally {
      setExportingJson(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-[#1a1e26] border border-[#262b36] rounded-xl w-full max-w-lg overflow-hidden shadow-2xl">
        <div className="p-5 border-b border-[#262b36] flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-100 flex items-center gap-2">
            <Download className="w-4 h-4 text-amber-400" />
            Export Planogram Layout
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-200 text-sm font-bold">
            ✕
          </button>
        </div>

        <div className="p-5 space-y-4">
          {successMessage && (
            <div className="p-3 rounded-lg bg-emerald-950/50 border border-emerald-800 text-emerald-300 text-xs flex items-center gap-2">
              <Check className="w-4 h-4 shrink-0 text-emerald-400" />
              <span>{successMessage}</span>
            </div>
          )}

          {errorMessage && (
            <div className="p-3 rounded-lg bg-red-950/50 border border-red-800 text-red-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          <p className="text-xs text-gray-400 leading-relaxed">
            Export the reference planogram arrangement for compliance review, reporting, or downstream machine processing.
          </p>

          <div className="grid grid-cols-2 gap-4 pt-2">
            {/* Visual PNG Export Card */}
            <div className="p-4 rounded-xl bg-[#13161c] border border-[#262b36] flex flex-col justify-between hover:border-amber-500/40 transition-colors">
              <div>
                <div className="w-10 h-10 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center mb-3">
                  <ImageIcon className="w-5 h-5" />
                </div>
                <h4 className="text-sm font-semibold text-gray-100">Visual PNG Export</h4>
                <p className="text-[11px] text-gray-400 mt-1 leading-relaxed">
                  High-resolution rendered image with white shelf background, packshots, dimension lines in cm, and labels.
                </p>
              </div>

              <button
                onClick={handleExportPng}
                disabled={exportingPng}
                data-testid="export-png-btn"
                className="mt-4 w-full py-2 rounded-lg bg-amber-500 hover:bg-amber-600 text-gray-950 font-bold text-xs transition-colors flex items-center justify-center gap-2 shadow-sm"
              >
                <Download className="w-3.5 h-3.5" />
                <span>{exportingPng ? "Rendering..." : "Download PNG"}</span>
              </button>
            </div>

            {/* Structured JSON Export Card */}
            <div className="p-4 rounded-xl bg-[#13161c] border border-[#262b36] flex flex-col justify-between hover:border-blue-500/40 transition-colors">
              <div>
                <div className="w-10 h-10 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center mb-3">
                  <FileJson className="w-5 h-5" />
                </div>
                <h4 className="text-sm font-semibold text-gray-100">Structured JSON</h4>
                <p className="text-[11px] text-gray-400 mt-1 leading-relaxed">
                  Versioned schema with physical dimensions, shelf properties, and placement coordinates in cm.
                </p>
              </div>

              <button
                onClick={handleExportJson}
                disabled={exportingJson}
                data-testid="export-json-btn"
                className="mt-4 w-full py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs transition-colors flex items-center justify-center gap-2 shadow-sm"
              >
                <Download className="w-3.5 h-3.5" />
                <span>{exportingJson ? "Fetching..." : "Download JSON"}</span>
              </button>
            </div>
          </div>
        </div>

        <div className="p-4 bg-[#13161c] border-t border-[#262b36] flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-[#262b36] text-gray-300 hover:text-gray-100 text-xs font-semibold"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
