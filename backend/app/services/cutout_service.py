"""Crop, map, embed, cluster, and shelf-catalogue-match CV detections."""

from __future__ import annotations

import io
import hashlib
import json
import logging
import math
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image

import torch
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging_config import log_backend, log_job_start, log_job_done, log_job_error
from app.db.models import ProcessedOutput
from app.services.embedding_service import embedding_service
from app.services.position_calibration import map_detections_to_planogram
from app.services.compliance_service import AUDIT_VERSION, build_compliance_audit
from app.services.label_ocr_service import analyze_shelf_labels
from app.services.price_tag_detection_service import detect_price_tags, draw_price_tag_boxes, read_tag_prices
from app.services.product_matching import filter_candidates_by_color
from app.services.product_matching.cluster_consensus import catalogue_consensus, merge_clusters_by_catalog_consensus

logger = logging.getLogger(__name__)

ANALYSIS_VERSION = 9
PRODUCT_BOX_CONFIDENCE_THRESHOLD = 0.60
CATALOG_MATCH_THRESHOLD = 0.90  # Calibrated against the four-product Pipeline Verification shelf.
CATALOG_MATCH_MARGIN_THRESHOLD = 0.03  # Provisional ambiguity margin.
INTRA_CLUSTER_SIMILARITY_THRESHOLD = 0.88


def _disk_path(storage_path: str) -> Path:
    """Resolve a public uploads path against the configured uploads root."""
    relative = Path(storage_path)
    if relative.parts and relative.parts[0] == "uploads":
        relative = Path(*relative.parts[1:])
    return settings.UPLOADS_DIR / relative


def _safe_clamp(val: float, max_val: int) -> int:
    return max(0, min(int(round(val)), max_val))


def _count_calibrated_positions(detections: List[Dict[str, Any]]) -> int:
    """Count mapped detections while treating an explicit null position as uncalibrated."""
    return sum(
        1 for item in detections
        if isinstance(item, dict)
        and isinstance(item.get("planogram_position"), dict)
        and item["planogram_position"].get("status") == "calibrated"
    )


def _normalize_vector(vec: List[float]) -> List[float]:
    t = torch.tensor(vec, dtype=torch.float32)
    norm = torch.norm(t)
    if norm > 1e-6:
        t = t / norm
    return t.tolist()


def _snapshot_fingerprint(snapshot: Optional[Dict[str, Any]]) -> Optional[str]:
    if not isinstance(snapshot, dict):
        return None
    existing = snapshot.get("snapshot_sha256")
    if isinstance(existing, str) and existing:
        return existing
    canonical = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _catalogue_match(
    vector: Optional[List[float]], catalogue: List[Dict[str, Any]], snapshot_available: bool,
    source_crop: Optional[Image.Image] = None,
) -> Dict[str, Any]:
    """Rank only the immutable shelf catalogue; never fall back to the live product table."""
    result: Dict[str, Any] = {
        "status": "needs_review",
        "reason": "missing_audit_snapshot" if not snapshot_available else "no_shelf_catalogue",
        "top_candidate": None,
        "runner_up": None,
        "similarity": None,
        "runner_up_similarity": None,
        "confidence_margin": None,
        "similarity_threshold": CATALOG_MATCH_THRESHOLD,
        "margin_threshold": CATALOG_MATCH_MARGIN_THRESHOLD,
        "color_similarity": None,
        "color_filter_candidate_count_before": 0,
        "color_filter_candidate_count_after": 0,
        "color_filter_threshold": 0.30,
        "color_filter_fallback": False,
        "color_filter_fallback_reason": None,
        "matching_method": "clip_only",
    }
    if not snapshot_available or not catalogue:
        return result
    if not vector or len(vector) != 512 or not all(math.isfinite(float(value)) for value in vector):
        result["reason"] = "missing_or_invalid_cutout_embedding"
        return result

    valid_products: List[Dict[str, Any]] = []
    for product in catalogue:
        candidate_vector = product.get("embedding")
        if not isinstance(candidate_vector, list) or len(candidate_vector) != 512:
            continue
        try:
            if not all(math.isfinite(float(value)) for value in candidate_vector):
                continue
            if not all(math.isfinite(float(value)) for value in candidate_vector):
                continue
        except (TypeError, ValueError, RuntimeError):
            continue
        valid_products.append(product)

    image_cache: Dict[str, Optional[Image.Image]] = {}

    def load_packshot(image_path: str) -> Optional[Image.Image]:
        if image_path not in image_cache:
            try:
                path = embedding_service.resolve_image_path(image_path)
                if path is None:
                    image_cache[image_path] = None
                else:
                    with Image.open(path) as image:
                        image_cache[image_path] = image.convert("RGB").copy()
            except (OSError, ValueError):
                image_cache[image_path] = None
        return image_cache[image_path]

    if source_crop is not None and valid_products:
        color_filter = filter_candidates_by_color(source_crop, valid_products, load_packshot)
        matching_products = color_filter["candidates"]
        result.update({
            "color_filter_candidate_count_before": color_filter["candidate_count_before"],
            "color_filter_candidate_count_after": color_filter["candidate_count_after"],
            "color_filter_threshold": color_filter["threshold"],
            "color_filter_fallback": color_filter["fallback"],
            "color_filter_fallback_reason": color_filter["fallback_reason"],
            "matching_method": "color_filter_then_clip",
        })
    else:
        matching_products = valid_products
        result["color_filter_candidate_count_before"] = len(valid_products)
        result["color_filter_candidate_count_after"] = len(valid_products)
        result["color_filter_fallback"] = source_crop is not None
        result["color_filter_fallback_reason"] = "no_valid_catalogue_embeddings" if source_crop is not None else None
        result["matching_method"] = "clip_only_fallback" if source_crop is not None else "clip_only"

    # Stage 2: compute candidate cosine scores only after color has filtered the list.
    ranked: List[Tuple[float, Dict[str, Any]]] = []
    clip_scores: Dict[int, float] = {}
    for product in matching_products:
        candidate_vector = product["embedding"]
        try:
            score = float(embedding_service.cosine_similarity(vector, candidate_vector))
        except (TypeError, ValueError, RuntimeError):
            continue
        if math.isfinite(score):
            product_id = int(product.get("id", 0))
            clip_scores[product_id] = score
            ranked.append((score, product))
    ranked.sort(key=lambda entry: (-entry[0], str(entry[1].get("sku", "")), int(entry[1].get("id", 0))))
    if not ranked:
        result["reason"] = "no_catalogue_embeddings"
        return result

    top_score, top_product = ranked[0]
    runner_score, runner_product = ranked[1] if len(ranked) > 1 else (None, None)
    margin = top_score - runner_score if runner_score is not None else top_score

    def public_candidate(product: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": int(product["id"]),
            "sku": str(product.get("sku", "")),
            "name": str(product.get("name", "")),
            "category": str(product.get("category") or "General"),
            "image_path": str(product.get("image_path", "")),
            "price": float(product.get("price") or 0),
            "currency": str(product.get("currency") or "INR"),
        }

    result.update({
        "top_candidate": public_candidate(top_product),
        "runner_up": public_candidate(runner_product) if runner_product else None,
        "similarity": round(top_score, 6),
        "runner_up_similarity": round(runner_score, 6) if runner_score is not None else None,
        "confidence_margin": round(margin, 6),
        "color_similarity": round(color_filter["scores"].get(int(top_product["id"])), 6)
        if source_crop is not None and not color_filter["fallback"] and color_filter["scores"].get(int(top_product["id"])) is not None
        else None,
    })
    if result["color_filter_fallback"]:
        result.update(status="needs_review", reason="color_filter_fallback")
    elif top_score < CATALOG_MATCH_THRESHOLD:
        # A low CLIP score is insufficient evidence of identity, not proof that the
        # item is absent from the shelf catalogue. Keep it reviewable, not an error.
        result.update(status="needs_review", reason="below_similarity_threshold")
    elif runner_score is not None and margin < CATALOG_MATCH_MARGIN_THRESHOLD:
        result.update(status="needs_review", reason="ambiguous_candidates")
    else:
        result.update(status="matched", reason="above_threshold_and_unambiguous")
    return result


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

    snapshot = output.job.audit_snapshot if output.job else None
    snapshot_hash = _snapshot_fingerprint(snapshot)
    # Cached results are valid only for this matching version and frozen shelf snapshot.
    if not force_recompute and analysis_file.is_file() and cutouts_file.is_file():
        try:
            with open(analysis_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
            with open(cutouts_file, "r", encoding="utf-8") as f:
                cached_cutouts = json.load(f)
            if (
                cached_data.get("analysis_version") == ANALYSIS_VERSION
                and cached_cutouts.get("analysis_version") == ANALYSIS_VERSION
                and cached_data.get("audit_snapshot_sha256") == snapshot_hash
                and cached_cutouts.get("audit_snapshot_sha256") == snapshot_hash
            ):
                audit = _persist_compliance_audit(db, output, cached_cutouts, snapshot_hash)
                cached_data["compliance_summary"] = audit["summary"]
                with analysis_file.open("w", encoding="utf-8") as f:
                    json.dump(cached_data, f, indent=2)
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
            detection_summary = detections_data.get("summary") if isinstance(detections_data.get("summary"), dict) else {}
            product_confidence_threshold = float(
                detection_summary.get("product_confidence_threshold", PRODUCT_BOX_CONFIDENCE_THRESHOLD)
            )
            excluded_products_raw = list(detections_data.get("excluded_products", []))
            eligible_products = []
            for prod in detections_data.get("products", []):
                try:
                    confidence = float(prod.get("confidence", 0.0))
                except (TypeError, ValueError):
                    confidence = 0.0
                if confidence < product_confidence_threshold:
                    # Also filter historical detection JSON that predates this
                    # product-specific cutoff, so cached output analysis upgrades.
                    excluded_products_raw.append(prod)
                else:
                    eligible_products.append(prod)

            for idx, prod in enumerate(eligible_products):
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
                    "quality_status": prod.get("quality_status", "unchecked"),
                    "quality_flags": list(prod.get("quality_flags") or []),
                    "catalog_match": None,
                })

            # These boxes are not product detections for matching/counting. Keep
            # only their coordinates as uncertainty evidence for compliance.
            excluded_products_meta: List[Dict[str, Any]] = []
            for idx, prod in enumerate(excluded_products_raw):
                bbox = prod.get("bbox_xyxy", [])
                if len(bbox) != 4:
                    continue
                x1 = _safe_clamp(bbox[0], img_w - 1)
                y1 = _safe_clamp(bbox[1], img_h - 1)
                x2 = _safe_clamp(bbox[2], img_w)
                y2 = _safe_clamp(bbox[3], img_h)
                if x2 <= x1 or y2 <= y1:
                    continue
                excluded_products_meta.append({
                    "id": f"excluded_prod_{idx + 1:04d}",
                    "bbox_xyxy": [x1, y1, x2, y2],
                    "confidence": round(float(prod.get("confidence", 0.0)), 4),
                    "row_number": prod.get("row_number"),
                    "planogram_position": None,
                    "excluded_reason": "below_product_confidence_threshold",
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

        calibration_data = detections_data.get("calibration") or {}
        shelf_geometry = snapshot.get("shelf") if isinstance(snapshot, dict) else None
        product_cutouts_meta, position_calibration = map_detections_to_planogram(
            product_cutouts_meta,
            shelf_cutouts_meta,
            shelf_geometry,
            img_w,
            img_h,
            calibration_data.get("shelf_corners_xy") if isinstance(calibration_data, dict) else None,
        )
        excluded_products_meta, _ = map_detections_to_planogram(
            excluded_products_meta,
            shelf_cutouts_meta,
            shelf_geometry,
            img_w,
            img_h,
            calibration_data.get("shelf_corners_xy") if isinstance(calibration_data, dict) else None,
        )
        empty_cutouts_meta, _ = map_detections_to_planogram(
            empty_cutouts_meta,
            shelf_cutouts_meta,
            shelf_geometry,
            img_w,
            img_h,
            calibration_data.get("shelf_corners_xy") if isinstance(calibration_data, dict) else None,
        )

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

        # 6. Match every individual crop against the job's frozen shelf catalogue.
        catalogue = snapshot.get("shelf_catalogue", []) if isinstance(snapshot, dict) else []
        if not isinstance(catalogue, list):
            catalogue = []
        vector_by_member = {index: product_vectors[index] for index in range(min(len(product_vectors), len(product_cutouts_meta)))}
        snapshot_available = isinstance(snapshot, dict)
        for index, item in enumerate(product_cutouts_meta):
            item["catalog_match"] = _catalogue_match(
                vector_by_member.get(index), catalogue, snapshot_available,
                source_crop=product_crops_pil[index] if index < len(product_crops_pil) else None,
            )

        # Consolidate visually fragmented clusters only when same-row catalogue
        # evidence agrees; individual crop identities and review states stay intact.
        clusters_raw = merge_clusters_by_catalog_consensus(clusters_raw, product_cutouts_meta)
        for cluster in clusters_raw:
            indices = cluster["member_indices"]
            pairwise_sims = [sim_matrix[a][b] for a in indices for b in indices if a != b]
            cluster["similarity_percentage"] = round(
                min(100.0, max(0.0, (sum(pairwise_sims) / len(pairwise_sims)) * 100.0))
                if pairwise_sims else 0.0,
                1,
            )
            vectors = [product_vectors[index] for index in indices]
            centroid_raw = [sum(vector[dim] for vector in vectors) / len(vectors) for dim in range(512)]
            cluster["centroid_vector"] = _normalize_vector(centroid_raw)

        cluster_rows: List[Dict[str, Any]] = []
        matched_count = 0

        for cl in clusters_raw:
            cl_id = cl["cluster_id"]
            centroid = cl["centroid_vector"]
            cohesion_pct = cl["similarity_percentage"]
            members = [product_cutouts_meta[m] for m in cl["member_indices"]]

            member_matches = [member.get("catalog_match", {}) for member in members]
            consensus = catalogue_consensus(members)
            is_match = consensus["status"] == "matched"
            consensus_candidate_id = (consensus["candidate"] or {}).get("id")
            scores = [
                match["similarity"] for match in member_matches
                if isinstance(match.get("similarity"), (int, float))
                and isinstance(match.get("top_candidate"), dict)
                and match["top_candidate"].get("id") == consensus_candidate_id
            ]
            catalog_confidence = round((sum(scores) / len(scores)) if scores else 0.0, 6)
            matched_prod_dict = consensus["candidate"]
            if is_match and matched_prod_dict:
                matched_count += 1

            cluster_rows.append({
                "cluster_id": cl_id,
                "item_count": len(members),
                "similar_objects": members,          # Column 1
                "similarity_percentage": cohesion_pct, # Column 2
                "is_catalog_match": is_match,          # Column 3
                "catalog_confidence": catalog_confidence,
                "catalog_product": matched_prod_dict,  # Column 4
                "catalog_consensus": {
                    "status": consensus["status"],
                    "reason": consensus["reason"],
                    "support_count": consensus["support_count"],
                    "considered_count": consensus["considered_count"],
                    "support_ratio": consensus["support_ratio"],
                },
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
            "total_product_crops": len(product_cutouts_meta),
            "total_clusters": len(cluster_rows),
            "matched_clusters_count": matched_count,
            "catalog_confidence_threshold": CATALOG_MATCH_THRESHOLD,
            "catalog_match_margin_threshold": CATALOG_MATCH_MARGIN_THRESHOLD,
            "product_confidence_threshold": product_confidence_threshold,
            "excluded_low_confidence_product_count": len(excluded_products_meta),
            "analysis_version": ANALYSIS_VERSION,
            "catalog_scope": "job_audit_snapshot.shelf_catalogue",
            "audit_snapshot_sha256": snapshot_hash,
            "products_needing_review": sum(1 for item in product_cutouts_meta if item["catalog_match"]["status"] == "needs_review"),
            "position_calibration": position_calibration,
            "detections_with_calibrated_positions": _count_calibrated_positions(product_cutouts_meta + empty_cutouts_meta),
            "clusters": cluster_rows,
        }

        cutouts_payload = {
            "output_id": output.id,
            "source_filename": output.input_image.original_filename,
            "total_count": len(product_cutouts_meta) + len(shelf_cutouts_meta) + len(empty_cutouts_meta),
            "analysis_version": ANALYSIS_VERSION,
            "audit_snapshot_sha256": snapshot_hash,
            "position_calibration": position_calibration,
            "calibration_corners_xy": calibration_data.get("shelf_corners_xy") if isinstance(calibration_data, dict) else None,
            "products": product_cutouts_meta,
            "excluded_products": excluded_products_meta,
            "shelves": shelf_cutouts_meta,
            "empty_spaces": empty_cutouts_meta,
        }

        # Save to disk
        with open(analysis_file, "w", encoding="utf-8") as f:
            json.dump(analysis_payload, f, indent=2)

        with open(cutouts_file, "w", encoding="utf-8") as f:
            json.dump(cutouts_payload, f, indent=2)

        compliance_audit = _persist_compliance_audit(
            db, output, cutouts_payload, snapshot_hash, force_recompute=force_recompute,
        )
        analysis_payload["compliance_summary"] = compliance_audit["summary"]
        with analysis_file.open("w", encoding="utf-8") as f:
            json.dump(analysis_payload, f, indent=2)

        # Update metrics summary on output record
        if isinstance(output.metrics, dict):
            output.metrics["analysis_summary"] = {
                "clusters_count": len(cluster_rows),
                "matched_clusters_count": matched_count,
                "products_cutouts": len(product_cutouts_meta),
                "empty_cutouts": len(empty_cutouts_meta),
                "shelf_cutouts": len(shelf_cutouts_meta),
                "position_calibrated_count": _count_calibrated_positions(product_cutouts_meta + empty_cutouts_meta),
            }
            db.commit()

        log_job_done(
            "ANALYSIS",
            task_id,
            0.0,
            f"Extracted {len(product_cutouts_meta)} products, {len(cluster_rows)} clusters ({matched_count} shelf-catalogue matches)",
        )
        return analysis_payload

    except Exception as exc:
        log_job_error("ANALYSIS", task_id, str(exc))
        logger.error(f"Failed to extract cutouts and analyze output {output_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Cutout analysis failed: {exc}") from exc


def _persist_compliance_audit(
    db: Session,
    output: ProcessedOutput,
    cutouts: Dict[str, Any],
    snapshot_hash: Optional[str],
    force_recompute: bool = False,
) -> Dict[str, Any]:
    """Persist the current audit in SQLite and beside its immutable CV artifacts."""
    output_dir = settings.UPLOADS_DIR / "image_processing" / "outputs" / str(output.job_id)
    audit_path = output_dir / "compliance_audit.json"
    snapshot = output.job.audit_snapshot if output.job else None
    current = output.compliance_audit if isinstance(output.compliance_audit, dict) else None
    if (not force_recompute and current and current.get("audit_version") == AUDIT_VERSION
            and current.get("audit_snapshot_sha256") == snapshot_hash
            and current.get("output_id") == output.id and audit_path.is_file()):
        return current
    input_path = _disk_path(output.input_image.storage_path)
    try:
        with Image.open(input_path) as source_image:
            image_size = source_image.size
    except (OSError, ValueError):
        image_size = (0, 0)
    label_audit = analyze_shelf_labels(
        image_path=input_path,
        output_dir=output_dir / "label_zones",
        snapshot=snapshot,
        shelf_rows=cutouts.get("shelves", []),
        image_size=image_size,
        position_calibration=cutouts.get("position_calibration"),
        shelf_corners_xy=cutouts.get("calibration_corners_xy"),
    )
    # Actual tag boxes are independent of product detections and planogram slots.
    # Cached Roboflow predictions prevent report refreshes from making cloud calls.
    price_tags = detect_price_tags(input_path, output_dir)
    price_tags = read_tag_prices(price_tags)
    shelf_width = (snapshot.get("shelf", {}).get("width_cm")
                   if isinstance(snapshot, dict) and isinstance(snapshot.get("shelf"), dict) else None)
    for tag in price_tags.get("detections", []):
        box = tag.get("bbox_xyxy")
        if not isinstance(box, list) or len(box) != 4:
            continue
        center_x, center_y = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        for shelf_row in cutouts.get("shelves", []):
            row_box = shelf_row.get("bbox_xyxy")
            if (isinstance(row_box, list) and len(row_box) == 4
                    and row_box[1] <= center_y <= row_box[3]):
                tag["row_number"] = shelf_row.get("row_number")
                if isinstance(shelf_width, (int, float)) and row_box[2] > row_box[0]:
                    scale = float(shelf_width) / (row_box[2] - row_box[0])
                    tag["x_center_cm"] = round((center_x - row_box[0]) * scale, 2)
                break
    label_audit["price_tag_detection"] = price_tags
    try:
        draw_price_tag_boxes(_disk_path(output.annotated_image_path), price_tags.get("detections", []))
    except Exception as exc:
        logger.warning("Could not draw price-tag overlay (%s)", type(exc).__name__)
    audit = build_compliance_audit(
        output_id=output.id,
        job_id=output.job_id,
        source_filename=output.input_image.original_filename,
        snapshot=snapshot,
        snapshot_sha256=snapshot_hash,
        products=cutouts.get("products", []),
        empty_spaces=cutouts.get("empty_spaces", []),
        excluded_products=cutouts.get("excluded_products", []),
        position_calibration=cutouts.get("position_calibration"),
        label_audit=label_audit,
    )
    output.compliance_audit = audit
    output.metrics = {**(output.metrics or {}), "compliance_summary": audit["summary"],
                      "compliance_audit_version": AUDIT_VERSION}
    output_dir.mkdir(parents=True, exist_ok=True)
    with audit_path.open("w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2)
    db.commit()
    return audit


def get_output_compliance_audit(db: Session, output_id: int) -> Dict[str, Any]:
    """Return a persisted audit, rebuilding stale/missing artifacts from saved cutouts."""
    output = db.query(ProcessedOutput).filter(ProcessedOutput.id == output_id).first()
    if not output:
        raise HTTPException(status_code=404, detail=f"ProcessedOutput with ID {output_id} not found.")
    cutouts = get_output_cutouts(db, output_id)
    snapshot = output.job.audit_snapshot if output.job else None
    snapshot_hash = _snapshot_fingerprint(snapshot)
    audit_path = settings.UPLOADS_DIR / "image_processing" / "outputs" / str(output.job_id) / "compliance_audit.json"
    audit = output.compliance_audit if isinstance(output.compliance_audit, dict) else None
    if (not audit or audit.get("audit_version") != AUDIT_VERSION
            or audit.get("audit_snapshot_sha256") != snapshot_hash
            or audit.get("output_id") != output.id):
        return _persist_compliance_audit(db, output, cutouts, snapshot_hash)
    if not audit_path.is_file():
        with audit_path.open("w", encoding="utf-8") as f:
            json.dump(audit, f, indent=2)
    return audit


def get_output_cutouts(db: Session, output_id: int) -> Dict[str, Any]:
    """Retrieve categorized cutouts (products, shelves, empty spaces) for an output."""
    output = db.query(ProcessedOutput).filter(ProcessedOutput.id == output_id).first()
    if not output:
        raise HTTPException(status_code=404, detail=f"ProcessedOutput with ID {output_id} not found.")

    cutouts_file = settings.UPLOADS_DIR / "image_processing" / "outputs" / str(output.job_id) / "cutouts.json"
    snapshot = output.job.audit_snapshot if output.job else None
    snapshot_hash = _snapshot_fingerprint(snapshot)
    cached_is_current = False
    if cutouts_file.is_file():
        try:
            with open(cutouts_file, "r", encoding="utf-8") as f:
                payload = json.load(f)
            cached_is_current = payload.get("analysis_version") == ANALYSIS_VERSION and payload.get("audit_snapshot_sha256") == snapshot_hash
        except (OSError, json.JSONDecodeError):
            cached_is_current = False
    if not cached_is_current:
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
    snapshot = output.job.audit_snapshot if output.job else None
    snapshot_hash = _snapshot_fingerprint(snapshot)
    try:
        with open(analysis_file, "r", encoding="utf-8") as f:
            payload = json.load(f)
        cache_is_current = payload.get("analysis_version") == ANALYSIS_VERSION and payload.get("audit_snapshot_sha256") == snapshot_hash
    except (OSError, json.JSONDecodeError):
        cache_is_current = False
    if not cache_is_current:
        return extract_cutouts_and_analyze(db, output_id)
    return payload


def get_cutout_download_path(db: Session, output_id: int, cutout_id: str) -> Path:
    """Resolve one cutout from its persisted metadata without accepting a client file path."""
    output = db.query(ProcessedOutput).filter(ProcessedOutput.id == output_id).first()
    if not output:
        raise HTTPException(status_code=404, detail=f"ProcessedOutput with ID {output_id} not found.")

    payload = get_output_cutouts(db, output_id)
    item = next(
        (candidate for group in ("products", "shelves", "empty_spaces") for candidate in payload.get(group, []) if candidate.get("id") == cutout_id),
        None,
    )
    if not item:
        raise HTTPException(status_code=404, detail=f"Cutout {cutout_id} was not found for output {output_id}.")

    crop_name = Path(item["crop_path"]).name
    category_directory = {
        "product": "products",
        "shelf": "shelves",
        "empty_space": "empty_spaces",
    }.get(item["category"])
    if not category_directory:
        raise HTTPException(status_code=404, detail="The cutout category is invalid.")
    crop_path = settings.UPLOADS_DIR / "image_processing" / "outputs" / str(output.job_id) / "cutouts" / category_directory / crop_name
    if not crop_path.is_file():
        raise HTTPException(status_code=404, detail="The cutout image file is unavailable.")
    return crop_path


def build_cutouts_zip(db: Session, output_id: int, category: Optional[str] = None) -> io.BytesIO:
    """Build a zip archive containing cutouts for an output, optionally filtered by category."""
    output = db.query(ProcessedOutput).filter(ProcessedOutput.id == output_id).first()
    if not output:
        raise HTTPException(status_code=404, detail=f"ProcessedOutput with ID {output_id} not found.")

    output_dir = settings.UPLOADS_DIR / "image_processing" / "outputs" / str(output.job_id)
    cutouts_dir = output_dir / "cutouts"

    if not cutouts_dir.exists():
        extract_cutouts_and_analyze(db, output_id)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        if category and category in ("products", "shelves", "empty_spaces"):
            cat_dir = cutouts_dir / category
            if cat_dir.exists():
                for file_path in sorted(cat_dir.glob("*.jpg")):
                    zf.write(file_path, arcname=f"{category}/{file_path.name}")
        else:
            for file_path in sorted(cutouts_dir.rglob("*.jpg")):
                rel_path = file_path.relative_to(cutouts_dir)
                zf.write(file_path, arcname=str(rel_path))

    buf.seek(0)
    return buf
