"""
ShelfSense AI — Bounding Box Cutout Extraction, Semantic Clustering & Catalog Matching Engine
=============================================================================================
1. Crops product, shelf-row, and empty-space bounding boxes from YOLO detection output.
2. Computes normalized 512-dim CLIP vectors for product cutouts in fast batches.
3. Performs intra-shelf clustering to group identical/similar visual faces.
4. Matches visual clusters against SQLite product catalog with strict >= 95% confidence threshold.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image

import torch
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging_config import log_backend, log_job_start, log_job_done, log_job_error
from app.db.models import ProcessedOutput, Product
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)

CATALOG_MATCH_THRESHOLD = 0.95
INTRA_CLUSTER_SIMILARITY_THRESHOLD = 0.88


def _disk_path(storage_path: str) -> Path:
    """Resolve a public uploads path against the configured uploads root."""
    relative = Path(storage_path)
    if relative.parts and relative.parts[0] == "uploads":
        relative = Path(*relative.parts[1:])
    return settings.UPLOADS_DIR / relative


def _safe_clamp(val: float, max_val: int) -> int:
    return max(0, min(int(round(val)), max_val))


def _normalize_vector(vec: List[float]) -> List[float]:
    t = torch.tensor(vec, dtype=torch.float32)
    norm = torch.norm(t)
    if norm > 1e-6:
        t = t / norm
    return t.tolist()


def extract_cutouts_and_analyze(db: Session, output_id: int, force_recompute: bool = False) -> Dict[str, Any]:
    """
    Extract all YOLO bounding box cutouts, compute embeddings, cluster similar items,
    and match against catalog products.
    """
    output = db.query(ProcessedOutput).filter(ProcessedOutput.id == output_id).first()
    if not output:
        raise HTTPException(status_code=404, detail=f"ProcessedOutput with ID {output_id} not found.")

    output_dir = settings.UPLOADS_DIR / "image_processing" / "outputs" / str(output.job_id)
    analysis_file = output_dir / "analysis.json"
    cutouts_file = output_dir / "cutouts.json"

    # If already computed and not forced, return cached analysis
    if not force_recompute and analysis_file.is_file() and cutouts_file.is_file():
        try:
            with open(analysis_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
                return cached_data
        except Exception:
            logger.warning(f"Failed to read cached analysis for output {output_id}, recomputing...")

    task_id = f"job_cutouts_{output.id}"
    log_job_start("ANALYSIS", task_id, f"Cutout extraction & clustering for Output #{output.id} (Job #{output.job_id})")

    try:
        source_image_path = _disk_path(output.input_image.storage_path)
        if not source_image_path.is_file():
            raise FileNotFoundError(f"Source input image not found at {source_image_path}")

        detections_json_path = _disk_path(output.result_json_path)
        if not detections_json_path.is_file():
            raise FileNotFoundError(f"Detections JSON not found at {detections_json_path}")

        with open(detections_json_path, "r", encoding="utf-8") as f:
            detections_data = json.load(f)

        # Open source image
        with Image.open(source_image_path) as full_img:
            full_img_rgb = full_img.convert("RGB")
            img_w, img_h = full_img_rgb.size

            # Prepare cutouts directories
            cutouts_base = output_dir / "cutouts"
            prod_dir = cutouts_base / "products"
            shelf_dir = cutouts_base / "shelves"
            void_dir = cutouts_base / "empty_spaces"

            prod_dir.mkdir(parents=True, exist_ok=True)
            shelf_dir.mkdir(parents=True, exist_ok=True)
            void_dir.mkdir(parents=True, exist_ok=True)

            # 1. Extract Product Cutouts
            product_crops_pil: List[Image.Image] = []
            product_cutouts_meta: List[Dict[str, Any]] = []

            for idx, prod in enumerate(detections_data.get("products", [])):
                bbox = prod.get("bbox_xyxy", [])
                if len(bbox) != 4:
                    continue
                x1 = _safe_clamp(bbox[0], img_w - 1)
                y1 = _safe_clamp(bbox[1], img_h - 1)
                x2 = _safe_clamp(bbox[2], img_w)
                y2 = _safe_clamp(bbox[3], img_h)

                if x2 <= x1 or y2 <= y1:
                    continue

                crop = full_img_rgb.crop((x1, y1, x2, y2))
                crop_filename = f"crop_{idx + 1:04d}.jpg"
                crop_disk_path = prod_dir / crop_filename
                crop.save(crop_disk_path, "JPEG", quality=92)

                rel_crop_path = f"uploads/image_processing/outputs/{output.job_id}/cutouts/products/{crop_filename}"
                product_crops_pil.append(crop)
                product_cutouts_meta.append({
                    "id": f"prod_{idx + 1:04d}",
                    "category": "product",
                    "crop_path": rel_crop_path,
                    "bbox_xyxy": [x1, y1, x2, y2],
                    "confidence": round(float(prod.get("confidence", 0.0)), 4),
                    "row_number": prod.get("row_number"),
                    "area_px": prod.get("area_px"),
                })

            # 2. Extract Empty Spaces Cutouts
            empty_cutouts_meta: List[Dict[str, Any]] = []
            for idx, void in enumerate(detections_data.get("empty_regions", [])):
                bbox = void.get("bbox_xyxy", [])
                if len(bbox) != 4:
                    continue
                x1 = _safe_clamp(bbox[0], img_w - 1)
                y1 = _safe_clamp(bbox[1], img_h - 1)
                x2 = _safe_clamp(bbox[2], img_w)
                y2 = _safe_clamp(bbox[3], img_h)

                if x2 <= x1 or y2 <= y1:
                    continue

                crop = full_img_rgb.crop((x1, y1, x2, y2))
                crop_filename = f"void_{idx + 1:04d}.jpg"
                crop_disk_path = void_dir / crop_filename
                crop.save(crop_disk_path, "JPEG", quality=90)

                rel_crop_path = f"uploads/image_processing/outputs/{output.job_id}/cutouts/empty_spaces/{crop_filename}"
                empty_cutouts_meta.append({
                    "id": f"void_{idx + 1:04d}",
                    "category": "empty_space",
                    "crop_path": rel_crop_path,
                    "bbox_xyxy": [x1, y1, x2, y2],
                    "confidence": round(float(void.get("confidence", 0.0)), 4),
                    "row_number": void.get("row_number"),
                })

            # 3. Extract Shelf Rows Cutouts
            shelf_cutouts_meta: List[Dict[str, Any]] = []
            for idx, row in enumerate(detections_data.get("shelf_rows", [])):
                bbox = row.get("bbox_xyxy", [])
                if len(bbox) != 4:
                    continue
                x1 = _safe_clamp(bbox[0], img_w - 1)
                y1 = _safe_clamp(bbox[1], img_h - 1)
                x2 = _safe_clamp(bbox[2], img_w)
                y2 = _safe_clamp(bbox[3], img_h)

                if x2 <= x1 or y2 <= y1:
                    continue

                crop = full_img_rgb.crop((x1, y1, x2, y2))
                crop_filename = f"row_{idx + 1:04d}.jpg"
                crop_disk_path = shelf_dir / crop_filename
                crop.save(crop_disk_path, "JPEG", quality=90)

                rel_crop_path = f"uploads/image_processing/outputs/{output.job_id}/cutouts/shelves/{crop_filename}"
                shelf_cutouts_meta.append({
                    "id": f"row_{idx + 1:04d}",
                    "category": "shelf",
                    "crop_path": rel_crop_path,
                    "bbox_xyxy": [x1, y1, x2, y2],
                    "confidence": round(float(row.get("confidence", 0.0)), 4),
                    "row_number": row.get("row_number", idx + 1),
                })

        # 4. Compute CLIP Embeddings in Batch for all Product Cutouts
        product_vectors: List[List[float]] = []
        if product_crops_pil:
            product_vectors = embedding_service.compute_image_embeddings_batch(product_crops_pil, batch_size=32)

        # 5. Intra-Shelf Clustering
        clusters_raw: List[Dict[str, Any]] = []
        num_products = len(product_vectors)

        if num_products > 0:
            # Pairwise cosine similarity matrix
            tensor_vecs = torch.tensor(product_vectors, dtype=torch.float32)
            sim_matrix = (tensor_vecs @ tensor_vecs.T).tolist()

            # Deterministic leader clustering
            assigned_cluster = [-1] * num_products
            cluster_id_counter = 1

            for i in range(num_products):
                if assigned_cluster[i] != -1:
                    continue

                # Start new cluster with i as leader
                current_cluster_members = [i]
                assigned_cluster[i] = cluster_id_counter

                for j in range(i + 1, num_products):
                    if assigned_cluster[j] == -1:
                        # Check similarity with leader and current members
                        sim = sim_matrix[i][j]
                        if sim >= INTRA_CLUSTER_SIMILARITY_THRESHOLD:
                            current_cluster_members.append(j)
                            assigned_cluster[j] = cluster_id_counter

                # Compute cluster internal cohesion similarity percentage
                if len(current_cluster_members) > 1:
                    pairwise_sims = [
                        sim_matrix[a][b]
                        for a in current_cluster_members
                        for b in current_cluster_members
                        if a != b
                    ]
                    avg_sim = (sum(pairwise_sims) / len(pairwise_sims)) * 100.0
                else:
                    avg_sim = 100.0

                # Cluster centroid vector
                member_vectors = [product_vectors[m] for m in current_cluster_members]
                centroid_raw = [
                    sum(v[dim] for v in member_vectors) / len(member_vectors)
                    for dim in range(512)
                ]
                centroid_norm = _normalize_vector(centroid_raw)

                # Attach cluster_id to cutout items
                for m in current_cluster_members:
                    product_cutouts_meta[m]["cluster_id"] = cluster_id_counter

                clusters_raw.append({
                    "cluster_id": cluster_id_counter,
                    "member_indices": current_cluster_members,
                    "similarity_percentage": round(min(100.0, max(0.0, avg_sim)), 1),
                    "centroid_vector": centroid_norm,
                })
                cluster_id_counter += 1

        # 6. Catalog Matching against SQLite Products (Threshold >= 0.95)
        catalog_products = (
            db.query(Product)
            .filter(Product.embedding.isnot(None))
            .all()
        )

        cluster_rows: List[Dict[str, Any]] = []
        matched_count = 0

        for cl in clusters_raw:
            cl_id = cl["cluster_id"]
            centroid = cl["centroid_vector"]
            cohesion_pct = cl["similarity_percentage"]
            members = [product_cutouts_meta[m] for m in cl["member_indices"]]

            best_match_prod: Optional[Product] = None
            best_sim = 0.0

            for prod in catalog_products:
                if prod.embedding and isinstance(prod.embedding, list):
                    sim = embedding_service.cosine_similarity(centroid, prod.embedding)
                    if sim > best_sim:
                        best_sim = sim
                        best_match_prod = prod

            is_match = best_sim >= CATALOG_MATCH_THRESHOLD
            catalog_confidence = round(best_sim * 100.0, 1)

            if is_match and best_match_prod:
                matched_count += 1
                matched_prod_dict = {
                    "id": best_match_prod.id,
                    "sku": best_match_prod.sku,
                    "name": best_match_prod.name,
                    "category": best_match_prod.category or "General",
                    "image_path": best_match_prod.image_path,
                    "price": float(best_match_prod.price),
                    "currency": best_match_prod.currency or "INR",
                }
            else:
                matched_prod_dict = None

            cluster_rows.append({
                "cluster_id": cl_id,
                "item_count": len(members),
                "similar_objects": members,          # Column 1
                "similarity_percentage": cohesion_pct, # Column 2
                "is_catalog_match": is_match,          # Column 3
                "catalog_confidence": catalog_confidence,
                "catalog_product": matched_prod_dict,  # Column 4
            })

        # Sort clusters: matched clusters first, then by item_count descending
        cluster_rows.sort(
            key=lambda c: (1 if c["is_catalog_match"] else 0, c["item_count"], c["similarity_percentage"]),
            reverse=True,
        )

        # Build analysis response payload
        shelf_snap = output.input_image.shelf_snapshot or {}
        shelf_dims_str = (
            f"{shelf_snap.get('width_cm', '')} cm × {shelf_snap.get('total_height_cm', '')} cm · {shelf_snap.get('row_count', '')} rows"
            if shelf_snap else "Shelf dimensions unavailable"
        )

        analysis_payload = {
            "output_id": output.id,
            "source_filename": output.input_image.original_filename,
            "planogram_name": output.input_image.planogram.name if output.input_image.planogram else None,
            "shelf_name": shelf_snap.get("name", "Shelf"),
            "shelf_dimensions": shelf_dims_str,
            "total_detections": len(product_cutouts_meta) + len(shelf_cutouts_meta) + len(empty_cutouts_meta),
            "total_clusters": len(cluster_rows),
            "matched_clusters_count": matched_count,
            "catalog_confidence_threshold": CATALOG_MATCH_THRESHOLD,
            "clusters": cluster_rows,
        }

        cutouts_payload = {
            "output_id": output.id,
            "source_filename": output.input_image.original_filename,
            "total_count": len(product_cutouts_meta) + len(shelf_cutouts_meta) + len(empty_cutouts_meta),
            "products": product_cutouts_meta,
            "shelves": shelf_cutouts_meta,
            "empty_spaces": empty_cutouts_meta,
        }

        # Save to disk
        with open(analysis_file, "w", encoding="utf-8") as f:
            json.dump(analysis_payload, f, indent=2)

        with open(cutouts_file, "w", encoding="utf-8") as f:
            json.dump(cutouts_payload, f, indent=2)

        # Update metrics summary on output record
        if isinstance(output.metrics, dict):
            output.metrics["analysis_summary"] = {
                "clusters_count": len(cluster_rows),
                "matched_clusters_count": matched_count,
                "products_cutouts": len(product_cutouts_meta),
                "empty_cutouts": len(empty_cutouts_meta),
                "shelf_cutouts": len(shelf_cutouts_meta),
            }
            db.commit()

        log_job_done(
            "ANALYSIS",
            task_id,
            0.0,
            f"Extracted {len(product_cutouts_meta)} products, {len(cluster_rows)} clusters ({matched_count} catalog matches >= 95%)",
        )
        return analysis_payload

    except Exception as exc:
        log_job_error("ANALYSIS", task_id, str(exc))
        logger.error(f"Failed to extract cutouts and analyze output {output_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Cutout analysis failed: {exc}") from exc


def get_output_cutouts(db: Session, output_id: int) -> Dict[str, Any]:
    """Retrieve categorized cutouts (products, shelves, empty spaces) for an output."""
    output = db.query(ProcessedOutput).filter(ProcessedOutput.id == output_id).first()
    if not output:
        raise HTTPException(status_code=404, detail=f"ProcessedOutput with ID {output_id} not found.")

    cutouts_file = settings.UPLOADS_DIR / "image_processing" / "outputs" / str(output.job_id) / "cutouts.json"
    if not cutouts_file.is_file():
        # Compute on the fly if missing
        extract_cutouts_and_analyze(db, output_id)

    if cutouts_file.is_file():
        with open(cutouts_file, "r", encoding="utf-8") as f:
            return json.load(f)

    return {
        "output_id": output.id,
        "source_filename": output.input_image.original_filename,
        "total_count": 0,
        "products": [],
        "shelves": [],
        "empty_spaces": [],
    }


def get_output_analysis(db: Session, output_id: int) -> Dict[str, Any]:
    """Retrieve 4-column cluster analysis and catalog matches for an output."""
    output = db.query(ProcessedOutput).filter(ProcessedOutput.id == output_id).first()
    if not output:
        raise HTTPException(status_code=404, detail=f"ProcessedOutput with ID {output_id} not found.")

    analysis_file = settings.UPLOADS_DIR / "image_processing" / "outputs" / str(output.job_id) / "analysis.json"
    if not analysis_file.is_file():
        return extract_cutouts_and_analyze(db, output_id)

    with open(analysis_file, "r", encoding="utf-8") as f:
        return json.load(f)
