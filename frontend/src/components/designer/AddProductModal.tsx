"use client";

import { useState, useRef, useMemo, useEffect } from "react";
import { Package, Upload, AlertCircle, Image as ImageIcon, Sparkles, Check, X } from "lucide-react";
import { api } from "@/lib/api";
import { Product } from "@/types";

interface AddProductModalProps {
  isOpen: boolean;
  onClose: () => void;
  onProductCreated: (product: Product) => void;
}

const CATEGORY_PRESETS = [
  "Beverages",
  "Snacks",
  "Breakfast",
  "Dairy",
  "Bakery",
  "Home Care",
  "Personal Care",
  "General",
];

const CATEGORY_COLORS: Record<string, { bg1: string; bg2: string; accent: string; badge: string }> = {
  Beverages: { bg1: "#0284c7", bg2: "#0369a1", accent: "#38bdf8", badge: "DRK" },
  Snacks: { bg1: "#d97706", bg2: "#b45309", accent: "#fbbf24", badge: "SNK" },
  Breakfast: { bg1: "#ea580c", bg2: "#c2410c", accent: "#fdba74", badge: "BF" },
  Dairy: { bg1: "#059669", bg2: "#047857", accent: "#6ee7b7", badge: "DRY" },
  Bakery: { bg1: "#b45309", bg2: "#78350f", accent: "#fde68a", badge: "BKY" },
  "Home Care": { bg1: "#4f46e5", bg2: "#3730a3", accent: "#a5b4fc", badge: "HC" },
  "Personal Care": { bg1: "#9333ea", bg2: "#7e22ce", accent: "#d8b4fe", badge: "PC" },
  General: { bg1: "#475569", bg2: "#334155", accent: "#cbd5e1", badge: "GEN" },
};

function escapeXml(unsafe: string): string {
  return unsafe.replace(/[<>&'"]/g, (c) => {
    switch (c) {
      case "<": return "&lt;";
      case ">": return "&gt;";
      case "&": return "&amp;";
      case "\'": return "&apos;";
      case "\"": return "&quot;";
      default: return c;
    }
  });
}

function generateSvgFile(
  sku: string,
  name: string,
  category: string,
  widthCm: number,
  heightCm: number
): File {
  const theme = CATEGORY_COLORS[category] || CATEGORY_COLORS.General;
  const safeSku = escapeXml(sku.trim().toUpperCase() || "SKU-001");
  const safeName = escapeXml(name.trim() || "Product Packshot");
  const displayTitle = safeName.length > 20 ? safeName.slice(0, 18) + "..." : safeName;

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 240" width="200" height="240">
  <defs>
    <linearGradient id="pGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="${theme.bg1}"/>
      <stop offset="100%" stop-color="${theme.bg2}"/>
    </linearGradient>
  </defs>
  <rect width="200" height="240" rx="16" fill="#ffffff" stroke="#cbd5e1" stroke-width="2"/>
  <rect x="16" y="16" width="168" height="152" rx="12" fill="url(#pGrad)"/>
  <circle cx="100" cy="70" r="28" fill="#ffffff" opacity="0.22"/>
  <text x="100" y="78" font-family="system-ui, -apple-system, sans-serif" font-size="18" font-weight="800" fill="#ffffff" text-anchor="middle" letter-spacing="1">${theme.badge}</text>
  <text x="100" y="122" font-family="monospace" font-size="12" font-weight="700" fill="#ffffff" text-anchor="middle">${safeSku}</text>
  <text x="100" y="142" font-family="system-ui, -apple-system, sans-serif" font-size="10" font-weight="600" fill="#ffffff" opacity="0.95" text-anchor="middle">${displayTitle}</text>
  <rect x="16" y="180" width="168" height="44" rx="8" fill="#f1f5f9"/>
  <text x="100" y="206" font-family="monospace" font-size="11" font-weight="700" fill="#1e293b" text-anchor="middle">${widthCm} \u00D7 ${heightCm} cm</text>
</svg>`;

  const cleanName = (sku.trim().toLowerCase().replace(/[^a-z0-9_-]/g, "_") || "packshot") + ".svg";
  return new File([svg], cleanName, { type: "image/svg+xml" });
}

export function AddProductModal({
  isOpen,
  onClose,
  onProductCreated,
}: AddProductModalProps) {
  const [sku, setSku] = useState("");
  const [name, setName] = useState("");
  const [category, setCategory] = useState("Beverages");
  const [customCategory, setCustomCategory] = useState("");
  const [description, setDescription] = useState("");
  const [price, setPrice] = useState<number>(50.0);
  const [currency, setCurrency] = useState("INR");
  const [widthCm, setWidthCm] = useState<number>(8.0);
  const [heightCm, setHeightCm] = useState<number>(18.0);
  const [depthCm, setDepthCm] = useState<number>(5.0);

  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const effectiveCategory = category === "Custom" ? (customCategory.trim() || "General") : category;

  // Auto-generate SVG preview URL when no custom image is selected
  const generatedSvgPreview = useMemo(() => {
    if (imagePreview) return imagePreview;
    const theme = CATEGORY_COLORS[effectiveCategory] || CATEGORY_COLORS.General;
    const safeSku = escapeXml(sku.trim().toUpperCase() || "SKU-001");
    const safeName = escapeXml(name.trim() || "New Product");
    const displayTitle = safeName.length > 20 ? safeName.slice(0, 18) + "..." : safeName;

    const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 240" width="200" height="240">
  <defs>
    <linearGradient id="pGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="${theme.bg1}"/>
      <stop offset="100%" stop-color="${theme.bg2}"/>
    </linearGradient>
  </defs>
  <rect width="200" height="240" rx="16" fill="#ffffff" stroke="#cbd5e1" stroke-width="2"/>
  <rect x="16" y="16" width="168" height="152" rx="12" fill="url(#pGrad)"/>
  <circle cx="100" cy="70" r="28" fill="#ffffff" opacity="0.22"/>
  <text x="100" y="78" font-family="system-ui, -apple-system, sans-serif" font-size="18" font-weight="800" fill="#ffffff" text-anchor="middle" letter-spacing="1">${theme.badge}</text>
  <text x="100" y="122" font-family="monospace" font-size="12" font-weight="700" fill="#ffffff" text-anchor="middle">${safeSku}</text>
  <text x="100" y="142" font-family="system-ui, -apple-system, sans-serif" font-size="10" font-weight="600" fill="#ffffff" opacity="0.95" text-anchor="middle">${displayTitle}</text>
  <rect x="16" y="180" width="168" height="44" rx="8" fill="#f1f5f9"/>
  <text x="100" y="206" font-family="monospace" font-size="11" font-weight="700" fill="#1e293b" text-anchor="middle">${widthCm || 0} \u00D7 ${heightCm || 0} cm</text>
</svg>`;
    return "data:image/svg+xml;utf8," + encodeURIComponent(svg);
  }, [imagePreview, effectiveCategory, sku, name, widthCm, heightCm]);

  // Clean up object URL when component unmounts or image changes
  useEffect(() => {
    return () => {
      if (imagePreview && imagePreview.startsWith("blob:")) {
        URL.revokeObjectURL(imagePreview);
      }
    };
  }, [imagePreview]);

  if (!isOpen) return null;

  const handleFileChange = (file: File) => {
    if (!file) return;
    const allowedTypes = ["image/jpeg", "image/png", "image/webp", "image/svg+xml"];
    if (!allowedTypes.includes(file.type)) {
      setError(`Invalid file type (${file.type}). Allowed: JPG, PNG, WebP, SVG.`);
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setError("File exceeds maximum allowed size of 5MB.");
      return;
    }
    setError(null);
    setImageFile(file);
    const objectUrl = URL.createObjectURL(file);
    setImagePreview(objectUrl);
  };

  const handleClearImage = () => {
    if (imagePreview && imagePreview.startsWith("blob:")) {
      URL.revokeObjectURL(imagePreview);
    }
    setImageFile(null);
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sku.trim()) {
      setError("Product SKU is required and must be unique.");
      return;
    }
    if (!name.trim()) {
      setError("Product name is required.");
      return;
    }
    if (widthCm <= 0 || heightCm <= 0 || depthCm <= 0) {
      setError("All dimensions (width, height, depth) must be greater than zero.");
      return;
    }
    if (price < 0) {
      setError("Price cannot be negative.");
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      // If no custom image file was selected by user, auto-generate one!
      const finalImageFile =
        imageFile ||
        generateSvgFile(sku, name, effectiveCategory, widthCm, heightCm);

      const formData = new FormData();
      formData.append("sku", sku.trim().toUpperCase());
      formData.append("name", name.trim());
      formData.append("category", effectiveCategory);
      formData.append("description", description.trim());
      formData.append("price", price.toString());
      formData.append("currency", currency.trim().toUpperCase() || "INR");
      formData.append("width_cm", widthCm.toString());
      formData.append("height_cm", heightCm.toString());
      formData.append("depth_cm", depthCm.toString());
      formData.append("image", finalImageFile);

      const created = await api.createProductMultipart(formData);
      onProductCreated(created);
      onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg || "Failed to create product in database.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-[#1a1e26] border border-[#262b36] rounded-xl w-full max-w-xl overflow-hidden shadow-2xl max-h-[92vh] flex flex-col">
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-[#262b36] flex items-center justify-between shrink-0">
          <div>
            <h2 className="text-base font-semibold text-gray-100 flex items-center gap-2">
              <Package className="w-4 h-4 text-amber-400" />
              Add Catalogue Product
            </h2>
            <p className="text-[11px] text-gray-400 mt-0.5">
              Enter all database details to create a new physical product ready for shelf placement.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded text-gray-400 hover:text-gray-200 hover:bg-[#262b36] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 sm:p-5 space-y-4 overflow-y-auto flex-1">
          {error && (
            <div className="p-3 rounded-lg bg-red-950/50 border border-red-800 text-red-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Packshot Artwork Section (Upload OR Auto-Generated) */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-medium text-gray-300">
                Product Packshot Artwork
              </label>
              {imageFile ? (
                <button
                  type="button"
                  onClick={handleClearImage}
                  className="text-[10px] text-red-400 hover:text-red-300 underline"
                >
                  Clear custom upload
                </button>
              ) : (
                <span className="text-[10px] text-amber-400/90 font-medium flex items-center gap-1">
                  <Sparkles className="w-3 h-3" />
                  Auto-generates if not uploaded
                </span>
              )}
            </div>

            <div className="flex gap-4 items-center">
              {/* Drag/Click Upload Box */}
              <div
                onClick={() => fileInputRef.current?.click()}
                className={`flex-1 border-2 border-dashed rounded-xl p-3 text-center cursor-pointer transition-colors ${
                  imageFile
                    ? "border-emerald-500/60 bg-emerald-950/20"
                    : "border-[#262b36] hover:border-amber-500/50 bg-[#13161c]"
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp,image/svg+xml"
                  className="hidden"
                  onChange={(e) => e.target.files?.[0] && handleFileChange(e.target.files[0])}
                />
                <Upload className="w-5 h-5 text-amber-400 mx-auto mb-1" />
                <span className="text-xs font-medium text-gray-200 block truncate">
                  {imageFile ? imageFile.name : "Upload front packshot (optional)"}
                </span>
                <p className="text-[10px] text-gray-400 mt-0.5">PNG, JPG, WebP, SVG (or leave blank to auto-generate)</p>
              </div>

              {/* Live Preview Box */}
              <div className="w-24 h-28 rounded-xl bg-white border border-[#262b36] flex flex-col items-center justify-center p-2 shrink-0 overflow-hidden relative shadow-inner">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={generatedSvgPreview}
                  alt="Live Packshot Preview"
                  className="max-h-full max-w-full object-contain"
                />
                <div className="absolute top-1 right-1 px-1 py-0.2 rounded bg-black/70 text-[8px] font-mono text-white">
                  {imageFile ? "Custom" : "Auto SVG"}
                </div>
              </div>
            </div>
          </div>

          {/* SKU & Name */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1">
                Unique SKU <span className="text-amber-400">*</span>
              </label>
              <input
                type="text"
                required
                placeholder="e.g. BEV-001"
                value={sku}
                onChange={(e) => setSku(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-[#13161c] border border-[#262b36] text-gray-100 text-sm focus:outline-none focus:border-amber-500 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1">
                Product Name <span className="text-amber-400">*</span>
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Citrus Soda Can"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-[#13161c] border border-[#262b36] text-gray-100 text-sm focus:outline-none focus:border-amber-500"
              />
            </div>
          </div>

          {/* Category Selection */}
          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">Category</label>
            <div className="flex flex-wrap gap-1.5 mb-2">
              {CATEGORY_PRESETS.map((cat) => (
                <button
                  key={cat}
                  type="button"
                  onClick={() => setCategory(cat)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                    category === cat
                      ? "bg-amber-500 text-gray-950 font-bold"
                      : "bg-[#13161c] text-gray-300 hover:bg-[#202530] border border-[#262b36]"
                  }`}
                >
                  {cat}
                </button>
              ))}
              <button
                type="button"
                onClick={() => setCategory("Custom")}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                  category === "Custom"
                    ? "bg-amber-500 text-gray-950 font-bold"
                    : "bg-[#13161c] text-gray-300 hover:bg-[#202530] border border-[#262b36]"
                }`}
              >
                Custom...
              </button>
            </div>
            {category === "Custom" && (
              <input
                type="text"
                placeholder="Type custom category name..."
                value={customCategory}
                onChange={(e) => setCustomCategory(e.target.value)}
                className="w-full px-3 py-1.5 rounded-lg bg-[#13161c] border border-[#262b36] text-gray-100 text-xs focus:outline-none focus:border-amber-500"
              />
            )}
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">Description (Optional)</label>
            <input
              type="text"
              placeholder="e.g. Front-facing aluminium beverage can with pull tab"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-1.5 rounded-lg bg-[#13161c] border border-[#262b36] text-gray-100 text-xs focus:outline-none focus:border-amber-500"
            />
          </div>

          {/* Price & Currency */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1">Price</label>
              <div className="relative">
                <input
                  type="number"
                  step="0.5"
                  min="0"
                  required
                  value={price}
                  onChange={(e) => setPrice(parseFloat(e.target.value) || 0)}
                  className="w-full pl-7 pr-3 py-2 rounded-lg bg-[#13161c] border border-[#262b36] text-gray-100 text-sm focus:outline-none focus:border-amber-500"
                />
                <span className="absolute left-2.5 top-2.5 text-xs text-gray-400 font-bold">
                  {currency === "INR" ? "?" : "$"}
                </span>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1">Currency Code</label>
              <input
                type="text"
                value={currency}
                onChange={(e) => setCurrency(e.target.value.toUpperCase())}
                className="w-full px-3 py-2 rounded-lg bg-[#13161c] border border-[#262b36] text-gray-100 text-sm focus:outline-none focus:border-amber-500 font-mono"
              />
            </div>
          </div>

          {/* Physical Dimensions in cm */}
          <div className="p-3 rounded-lg bg-[#141820] border border-[#262b36]">
            <label className="block text-xs font-semibold text-gray-200 mb-1">
              Physical Dimensions (cm) <span className="text-amber-400">*</span>
            </label>
            <p className="text-[10px] text-gray-400 mb-2">
              Shelf placement coordinates, collision checks, and row capacity strictly use these physical centimetres.
            </p>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <span className="text-[10px] text-gray-400 block mb-0.5">Width (cm)</span>
                <input
                  type="number"
                  step="0.1"
                  min="0.5"
                  max="300"
                  required
                  value={widthCm}
                  onChange={(e) => setWidthCm(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-1.5 rounded-lg bg-[#1a1e26] border border-[#262b36] text-gray-100 text-sm focus:outline-none focus:border-amber-500 font-mono"
                />
              </div>

              <div>
                <span className="text-[10px] text-gray-400 block mb-0.5">Height (cm)</span>
                <input
                  type="number"
                  step="0.1"
                  min="0.5"
                  max="300"
                  required
                  value={heightCm}
                  onChange={(e) => setHeightCm(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-1.5 rounded-lg bg-[#1a1e26] border border-[#262b36] text-gray-100 text-sm focus:outline-none focus:border-amber-500 font-mono"
                />
              </div>

              <div>
                <span className="text-[10px] text-gray-400 block mb-0.5">Depth (cm)</span>
                <input
                  type="number"
                  step="0.1"
                  min="0.5"
                  max="200"
                  required
                  value={depthCm}
                  onChange={(e) => setDepthCm(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-1.5 rounded-lg bg-[#1a1e26] border border-[#262b36] text-gray-100 text-sm focus:outline-none focus:border-amber-500 font-mono"
                />
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#262b36] shrink-0">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-[#262b36] text-gray-300 hover:text-gray-100 text-xs font-semibold transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-600 text-gray-950 font-bold text-xs transition-colors flex items-center gap-1.5 shadow-sm"
            >
              {submitting ? "Saving Product..." : "Save to Product Library"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
