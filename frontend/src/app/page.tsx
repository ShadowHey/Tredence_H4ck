"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Layers,
  Package,
  Grid,
  Plus,
  ArrowRight,
  Clock,
  Sparkles,
  RefreshCw,
  FolderOpen,
  AlertCircle,
  TrendingUp,
} from "lucide-react";
import { api } from "@/lib/api";
import { DashboardMetrics } from "@/types";

export default function DashboardPage() {
  const router = useRouter();
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [seeding, setSeeding] = useState(false);
  const [seedMessage, setSeedMessage] = useState<string | null>(null);

  // New Planogram Modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newPlanogramName, setNewPlanogramName] = useState("");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getDashboardMetrics();
      setMetrics(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg || "Failed to load dashboard metrics.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let ignore = false;
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await api.getDashboardMetrics();
        if (!ignore) {
          setMetrics(data);
        }
      } catch (err: unknown) {
        if (!ignore) {
          const msg = err instanceof Error ? err.message : String(err);
          setError(msg || "Failed to load dashboard metrics.");
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    };
    void fetchData();
    return () => {
      ignore = true;
    };
  }, []);

  const handleSeed = async () => {
    try {
      setSeeding(true);
      setSeedMessage(null);
      const res = await api.seedCatalogue();
      setSeedMessage(res.message);
      await loadData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg || "Failed to seed sample catalogue.");
    } finally {
      setSeeding(false);
    }
  };

  const handleCreatePlanogram = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPlanogramName.trim()) {
      setCreateError("Planogram name is required.");
      return;
    }
    try {
      setCreating(true);
      setCreateError(null);
      const newPlanogram = await api.createPlanogram({ name: newPlanogramName.trim() });
      setShowCreateModal(false);
      setNewPlanogramName("");
      router.push(`/designer?id=${newPlanogram.id}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setCreateError(msg || "Failed to create planogram.");
      setCreating(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-y-auto bg-[#0d0f12]" data-testid="dashboard-page">
      {/* Top Header */}
      <header className="h-16 px-6 border-b border-[#262b36] flex items-center justify-between bg-[#13161c] shrink-0">
        <div>
          <h1 className="text-lg font-semibold text-gray-100 flex items-center gap-2">
            Dashboard
            <span className="text-xs px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium">
              Live SQLite Data
            </span>
          </h1>
          <p className="text-xs text-gray-400">Overview of saved retail planograms and catalogue inventory</p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadData}
            disabled={loading}
            className="p-2 rounded-lg bg-[#1a1e26] border border-[#262b36] text-gray-400 hover:text-gray-200 transition-colors"
            title="Refresh dashboard"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-amber-400" : ""}`} />
          </button>

          <button
            onClick={() => setShowCreateModal(true)}
            data-testid="create-planogram-btn"
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-amber-500 hover:bg-amber-600 text-gray-950 font-semibold text-sm transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>Create Planogram</span>
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="p-6 max-w-7xl mx-auto w-full space-y-6">
        {/* Error Banner */}
        {error && (
          <div className="p-4 rounded-xl bg-red-950/40 border border-red-800/50 flex items-start gap-3 text-red-300 text-sm">
            <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
            <div className="flex-1">
              <span className="font-semibold">Backend Connection Issue: </span>
              {error}
            </div>
            <button
              onClick={loadData}
              className="px-2.5 py-1 rounded bg-red-900/50 hover:bg-red-900 text-red-200 text-xs font-medium"
            >
              Retry
            </button>
          </div>
        )}

        {/* Seed Confirmation Toast */}
        {seedMessage && (
          <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-800/50 flex items-center justify-between text-emerald-300 text-sm">
            <span>{seedMessage}</span>
            <button onClick={() => setSeedMessage(null)} className="text-xs text-emerald-400 underline">
              Dismiss
            </button>
          </div>
        )}

        {/* KPI Cards Row (MoEngage inspired) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: Saved Planograms */}
          <div className="p-5 rounded-xl bg-[#1a1e26] border border-[#262b36] flex flex-col justify-between hover:border-[#3b4252] transition-colors">
            <div className="flex items-center justify-between text-gray-400 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider">Saved Planograms</span>
              <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400">
                <Layers className="w-4 h-4" />
              </div>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-gray-100" data-testid="kpi-planograms">
                {metrics ? metrics.total_planograms : "—"}
              </span>
              <span className="text-xs text-gray-400">layouts</span>
            </div>
            <div className="mt-3 pt-3 border-t border-[#262b36]/60 text-[11px] text-gray-400 flex items-center gap-1">
              <span>Saved in SQLite database</span>
            </div>
          </div>

          {/* Card 2: Catalogue Products */}
          <div className="p-5 rounded-xl bg-[#1a1e26] border border-[#262b36] flex flex-col justify-between hover:border-[#3b4252] transition-colors">
            <div className="flex items-center justify-between text-gray-400 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider">Catalogue Items</span>
              <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400">
                <Package className="w-4 h-4" />
              </div>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-gray-100" data-testid="kpi-products">
                {metrics ? metrics.total_products : "—"}
              </span>
              <span className="text-xs text-gray-400">SKUs</span>
            </div>
            <div className="mt-3 pt-3 border-t border-[#262b36]/60 text-[11px] text-gray-400 flex items-center justify-between">
              <span>Ready for placement</span>
              {metrics && metrics.total_products === 0 && (
                <button
                  onClick={handleSeed}
                  disabled={seeding}
                  className="text-amber-400 hover:text-amber-300 font-medium"
                >
                  {seeding ? "Seeding..." : "Load 6 Samples"}
                </button>
              )}
            </div>
          </div>

          {/* Card 3: Total Shelves Designed */}
          <div className="p-5 rounded-xl bg-[#1a1e26] border border-[#262b36] flex flex-col justify-between hover:border-[#3b4252] transition-colors">
            <div className="flex items-center justify-between text-gray-400 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider">Total Shelves</span>
              <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
                <Grid className="w-4 h-4" />
              </div>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-gray-100" data-testid="kpi-shelves">
                {metrics ? metrics.total_shelves : "—"}
              </span>
              <span className="text-xs text-gray-400">gondolas / fixtures</span>
            </div>
            <div className="mt-3 pt-3 border-t border-[#262b36]/60 text-[11px] text-gray-400">
              <span>Across all planograms</span>
            </div>
          </div>

          {/* Card 4: Product Facings Placed */}
          <div className="p-5 rounded-xl bg-[#1a1e26] border border-[#262b36] flex flex-col justify-between hover:border-[#3b4252] transition-colors">
            <div className="flex items-center justify-between text-gray-400 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider">Total Placements</span>
              <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400">
                <TrendingUp className="w-4 h-4" />
              </div>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-gray-100" data-testid="kpi-placements">
                {metrics ? metrics.total_placements : "—"}
              </span>
              <span className="text-xs text-gray-400">product facings</span>
            </div>
            <div className="mt-3 pt-3 border-t border-[#262b36]/60 text-[11px] text-gray-400">
              <span>Physical coordinates in cm</span>
            </div>
          </div>
        </div>

        {/* Recent Planograms Section */}
        <div className="rounded-xl bg-[#1a1e26] border border-[#262b36] overflow-hidden">
          <div className="p-5 border-b border-[#262b36] flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold text-gray-100">Recent Planograms</h2>
              <p className="text-xs text-gray-400">Open or manage your reference shelf arrangements</p>
            </div>
            <Link
              href="/designer"
              className="text-xs text-amber-400 hover:text-amber-300 font-medium flex items-center gap-1"
            >
              <span>Open Designer Canvas</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {/* Content / Empty State */}
          {loading ? (
            <div className="p-12 text-center text-gray-400 text-sm">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-amber-400" />
              <span>Loading saved planograms from SQLite...</span>
            </div>
          ) : metrics && metrics.recent_planograms.length > 0 ? (
            <div className="divide-y divide-[#262b36]/60">
              {metrics.recent_planograms.map((planogram) => (
                <div
                  key={planogram.id}
                  className="p-4 px-5 flex items-center justify-between hover:bg-[#222733]/50 transition-colors"
                  data-testid={`planogram-row-${planogram.id}`}
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
                      <Layers className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-gray-100">{planogram.name}</h3>
                      <div className="flex items-center gap-3 text-xs text-gray-400 mt-0.5">
                        <span className="flex items-center gap-1">
                          <Grid className="w-3.5 h-3.5" />
                          {planogram.shelf_count} {planogram.shelf_count === 1 ? "shelf" : "shelves"}
                        </span>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          <Package className="w-3.5 h-3.5" />
                          {planogram.placement_count} placements
                        </span>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5" />
                          Updated {new Date(planogram.updated_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Link
                      href={`/designer?id=${planogram.id}`}
                      className="px-3.5 py-1.5 rounded-lg bg-[#262b36] hover:bg-amber-500 hover:text-gray-950 text-gray-200 text-xs font-semibold transition-all flex items-center gap-1.5"
                    >
                      <FolderOpen className="w-3.5 h-3.5" />
                      <span>Open Planogram</span>
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            /* Helpful Empty State (Never fake metrics) */
            <div className="p-12 text-center max-w-md mx-auto space-y-4" data-testid="empty-dashboard">
              <div className="w-14 h-14 rounded-2xl bg-[#262b36]/60 border border-[#262b36] flex items-center justify-center mx-auto text-amber-400">
                <Layers className="w-7 h-7" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-gray-200">No saved planograms yet</h3>
                <p className="text-xs text-gray-400 mt-1 leading-relaxed">
                  Get started by creating your first reference shelf layout. Define real-world shelf dimensions in cm,
                  arrange products, and export visual and JSON planograms.
                </p>
              </div>
              <div className="flex items-center justify-center gap-3 pt-2">
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-600 text-gray-950 font-semibold text-xs transition-colors flex items-center gap-1.5"
                >
                  <Plus className="w-4 h-4" />
                  <span>Create First Planogram</span>
                </button>
                {metrics && metrics.total_products === 0 && (
                  <button
                    onClick={handleSeed}
                    disabled={seeding}
                    className="px-4 py-2 rounded-lg bg-[#262b36] hover:bg-[#323947] text-gray-200 font-medium text-xs transition-colors flex items-center gap-1.5"
                  >
                    <Sparkles className="w-4 h-4 text-amber-400" />
                    <span>{seeding ? "Loading..." : "Seed 6 Sample SKUs"}</span>
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Create Planogram Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-[#1a1e26] border border-[#262b36] rounded-xl w-full max-w-md overflow-hidden shadow-2xl">
            <div className="p-5 border-b border-[#262b36] flex items-center justify-between">
              <h2 className="text-base font-semibold text-gray-100 flex items-center gap-2">
                <Layers className="w-4 h-4 text-amber-400" />
                Create New Planogram
              </h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-gray-400 hover:text-gray-200 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreatePlanogram} className="p-5 space-y-4">
              {createError && (
                <div className="p-3 rounded-lg bg-red-950/50 border border-red-800 text-red-300 text-xs">
                  {createError}
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1.5">
                  Planogram Title <span className="text-amber-400">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Beverages Gondola Bay 1"
                  value={newPlanogramName}
                  onChange={(e) => setNewPlanogramName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-[#13161c] border border-[#262b36] text-gray-100 text-sm focus:outline-none focus:border-amber-500"
                  autoFocus
                />
                <p className="text-[11px] text-gray-400 mt-1">
                  You will be able to add shelves, configure dimensions, and place products on the canvas.
                </p>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#262b36]">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-lg bg-[#262b36] text-gray-300 hover:text-gray-100 text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-600 text-gray-950 font-semibold text-xs transition-colors flex items-center gap-1.5"
                >
                  {creating ? "Creating..." : "Start Designing"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
