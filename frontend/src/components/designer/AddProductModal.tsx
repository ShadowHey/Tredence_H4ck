"use client";

import { useState, useRef } from "react";
import { Package, Upload, AlertCircle, Image as ImageIcon } from "lucide-react";
import { api } from "@/lib/api";
import { Product } from "@/types";

interface AddProductModalProps {
  isOpen: boolean;
  onClose: () => void;
  onProductCreated: (product: Product) => void;
}

export function AddProductModal({
  isOpen,
  onClose,
  onProductCreated,
}: AddProductModalProps) {
  const [sku, setSku] = useState("");
  const [name, setName] = useState("");
  const [category, setCategory] = useState("Beverages");
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
    if (!imageFile) {
      setError("Please upload a front-facing product packshot image.");
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
      const formData = new FormData();
      formData.append("sku", sku.trim().toUpperCase());
      formData.append("name", name.trim());
      formData.append("category", category);
      formData.append("description", description.trim());
      formData.append("price", price.toString());
      formData.append("currency", currency);
      formData.append("width_cm", widthCm.toString());
      formData.append("height_cm", heightCm.toString());
      formData.append("depth_cm", depthCm.toString());
      formData.append("image", imageFile);

      const created = await api.createProductMultipart(formData);
      onProductCreated(created);
      onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg || "Failed to create product.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-[#1a1e26] border border-[#262b36] rounded-xl w-full max-w-xl overflow-hidden shadow-2xl max-h-[90vh] flex flex-col">
        <div className="p-5 border-b border-[#262b36] flex items-center justify-between shrink-0">
          <h2 className="text-base font-semibold text-gray-100 flex items-center gap-2">
            <Package className="w-4 h-4 text-amber-400" />
            Add Catalogue Product
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-200 text-sm font-bold">
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4 overflow-y-auto flex-1">
          {error && (
            <div className="p-3 rounded-lg bg-red-950/50 border border-red-800 text-red-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Image Upload & Live Packshot Preview */}
          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1.5">
              Product Packshot Artwork <span className="text-amber-400">*</span>
            </label>
            <div className="flex gap-4 items-center">
              <div
                onClick={() => fileInputRef.current?.click()}
                className="flex-1 border-2 border-dashed border-[#262b36] hover:border-amber-500/50 rounded-xl p-4 text-center cursor-pointer bg-[#13161c] transition-colors"
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp,image/svg+xml"
                  className="hidden"
                  onChange={(e) => e.target.files?.[0] && handleFileChange(e.target.files[0])}
                />
                <Upload className="w-6 h-6 text-amber-400 mx-auto mb-1.5" />
                <span className="text-xs font-medium text-gray-200">
                  {imageFile ? imageFile.name : "Click or drag front image"}
                </span>
                <p className="text-[10px] text-gray-400 mt-0.5">PNG, JPG, WebP, SVG (max 5MB)</p>
              </div>

              {/* Preview Thumbnail */}
              <div className="w-24 h-24 rounded-xl bg-white border border-[#262b36] flex flex-col items-center justify-center p-2 shrink-0 overflow-hidden relative shadow-inner">
                {imagePreview ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={imagePreview}
                    alt="Preview"
                    className="max-h-full max-w-full object-contain"
                  />
                ) : (
                  <div className="text-center text-gray-400">
                    <ImageIcon className="w-5 h-5 mx-auto opacity-40 mb-1" />
                    <span className="text-[9px] uppercase tracking-wider font-semibold">Preview</span>
                  </div>
                )}
                {widthCm > 0 && heightCm > 0 && (
                  <div className="absolute bottom-0 inset-x-0 bg-black/60 text-white text-[8px] text-center py-0.5 font-mono">
                    {widthCm}×{heightCm}cm
                  </div>
                )}
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

          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">Description (Optional)</label>
            <input
              type="text"
              placeholder="e.g. Front-facing aluminium beverage can"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-1.5 rounded-lg bg-[#13161c] border border-[#262b36] text-gray-100 text-xs focus:outline-none focus:border-amber-500"
            />
          </div>

          {/* Category & Price */}
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1">Category</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-[#13161c] border border-[#262b36] text-gray-100 text-sm focus:outline-none focus:border-amber-500"
              >
                <option value="Beverages">Beverages</option>
                <option value="Snacks">Snacks</option>
                <option value="Breakfast">Breakfast</option>
                <option value="Home Care">Home Care</option>
                <option value="General">General</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1">Price (₹)</label>
              <input
                type="number"
                step="0.5"
                min="0"
                required
                value={price}
                onChange={(e) => setPrice(parseFloat(e.target.value) || 0)}
                className="w-full px-3 py-2 rounded-lg bg-[#13161c] border border-[#262b36] text-gray-100 text-sm focus:outline-none focus:border-amber-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1">Currency</label>
              <input
                type="text"
                value={currency}
                onChange={(e) => setCurrency(e.target.value.toUpperCase())}
                className="w-full px-3 py-2 rounded-lg bg-[#13161c] border border-[#262b36] text-gray-100 text-sm focus:outline-none focus:border-amber-500"
              />
            </div>
          </div>

          {/* Physical Dimensions in cm */}
          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">
              Physical Dimensions (cm) <span className="text-amber-400">*</span>
            </label>
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
                  className="w-full px-3 py-1.5 rounded-lg bg-[#13161c] border border-[#262b36] text-gray-100 text-sm focus:outline-none focus:border-amber-500"
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
                  className="w-full px-3 py-1.5 rounded-lg bg-[#13161c] border border-[#262b36] text-gray-100 text-sm focus:outline-none focus:border-amber-500"
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
                  className="w-full px-3 py-1.5 rounded-lg bg-[#13161c] border border-[#262b36] text-gray-100 text-sm focus:outline-none focus:border-amber-500"
                />
              </div>
            </div>
            <p className="text-[11px] text-gray-400 mt-1">
              Shelf placement coordinates, collision checks, and row capacity strictly use these physical centimetres.
            </p>
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#262b36] shrink-0">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-[#262b36] text-gray-300 hover:text-gray-100 text-xs font-semibold"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-600 text-gray-950 font-semibold text-xs transition-colors"
            >
              {submitting ? "Saving Product..." : "Save to Product Library"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
