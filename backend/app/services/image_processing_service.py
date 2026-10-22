"""Persistent input-image workflow and a serial bridge to the CV pipeline."""
from __future__ import annotations

import json
import hashlib
import os
import subprocess
import threading
import zipfile
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile
from PIL import UnidentifiedImageError, Image
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.logging_config import log_backend
from app.db.database import SessionLocal
from app.db.models import InputImage, Planogram, ProcessedOutput, ProcessingJob, Shelf
from app.storage.file_storage import save_uploaded_image

PROCESSABLE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp"}
PROCESSABLE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
_worker_lock = threading.Lock()


def _disk_path(storage_path: str) -> Path:
    """Resolve a public uploads path against the configured (testable) uploads root."""
    relative = Path(storage_path)
    if relative.parts and relative.parts[0] == "uploads":
        relative = Path(*relative.parts[1:])
    return settings.UPLOADS_DIR / relative


def _public(item: InputImage) -> dict[str, Any]:
    return {
        "id": item.id,
        "original_filename": item.original_filename,
        "storage_path": item.storage_path,
        "content_type": item.content_type,
        "size_bytes": item.size_bytes,
        "status": item.status,
        "planogram_id": item.planogram_id,
        "shelf_id": item.shelf_id,
        "shelf_snapshot": item.shelf_snapshot,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "job_id": item.job.id if item.job else None,
        "error_message": item.job.error_message if item.job else None,
        "output_id": item.output.id if item.output else None,
        "audit_snapshot": item.job.audit_snapshot if item.job else None,
    }


def list_input_images(db: Session) -> list[dict[str, Any]]:
    rows = (
        db.query(InputImage)
        .options(joinedload(InputImage.job), joinedload(InputImage.output))
        .order_by(InputImage.created_at.desc())
        .all()
    )
    return [_public(row) for row in rows]


def create_input_images(db: Session, files: list[UploadFile]) -> list[dict[str, Any]]:
    if not files:
        raise HTTPException(status_code=422, detail="Select at least one shelf image to upload.")
    created: list[InputImage] = []
    try:
        for file in files:
            if not file.filename:
                raise HTTPException(status_code=400, detail="Each uploaded image needs a filename.")
            suffix = Path(file.filename).suffix.lower()
            if file.content_type not in PROCESSABLE_CONTENT_TYPES or suffix not in PROCESSABLE_EXTENSIONS:
                raise HTTPException(status_code=400, detail="Unsupported shelf-image format. Use JPG, PNG, WebP, or BMP.")
            original_name = Path(file.filename).name
            storage_path = save_uploaded_image(
                file,
                subfolder="image_processing/inputs",
                max_size_bytes=settings.IMAGE_PROCESSING_MAX_UPLOAD_SIZE_BYTES,
            )
            disk_path = _disk_path(storage_path)
            size = disk_path.stat().st_size
            if size > settings.IMAGE_PROCESSING_MAX_UPLOAD_SIZE_BYTES:
                disk_path.unlink(missing_ok=True)
                raise HTTPException(status_code=400, detail="Shelf images must be 15MB or smaller.")
            try:
                with Image.open(disk_path) as image:
                    image.verify()
            except (UnidentifiedImageError, OSError):
                disk_path.unlink(missing_ok=True)
                raise HTTPException(status_code=400, detail="The uploaded file is not a readable image.")
            row = InputImage(
                original_filename=original_name,
                storage_path=storage_path,
                content_type=file.content_type or "application/octet-stream",
                size_bytes=size,
                status="ready",
            )
            db.add(row)
            created.append(row)
        db.commit()
        for row in created:
            db.refresh(row)
        log_backend("INFO", "IMAGE_UPLOAD", f"Stored {len(created)} shelf image(s) for review.")
        return [_public(row) for row in created]
    except Exception:
        db.rollback()
        for row in created:
            path = _disk_path(row.storage_path)
            path.unlink(missing_ok=True)
        raise


def _get_target(db: Session, planogram_id: int, shelf_id: int) -> tuple[Planogram, Shelf, dict[str, Any]]:
    planogram = db.query(Planogram).filter(Planogram.id == planogram_id).first()
    if not planogram:
        raise HTTPException(status_code=404, detail=f"Planogram with ID {planogram_id} was not found.")
    shelf = db.query(Shelf).filter(Shelf.id == shelf_id).first()
    if not shelf:
        raise HTTPException(status_code=404, detail=f"Shelf with ID {shelf_id} was not found.")
    if shelf.planogram_id != planogram.id:
        raise HTTPException(status_code=422, detail="The selected shelf does not belong to the selected planogram.")
    snapshot = {
        "id": shelf.id,
        "name": shelf.name,
        "width_cm": shelf.width_cm,
        "total_height_cm": shelf.total_height_cm,
        "depth_cm": shelf.depth_cm,
        "row_count": shelf.row_count,
    }
    return planogram, shelf, snapshot


def _product_snapshot(product: Any) -> dict[str, Any]:
    return {
        "id": int(product.id),
        "sku": product.sku,
        "name": product.name,
        "category": product.category or "General",
        "description": product.description,
        "image_path": product.image_path,
        "price": float(product.price),
        "currency": product.currency or "INR",
        "width_cm": float(product.width_cm),
        "height_cm": float(product.height_cm),
        "depth_cm": float(product.depth_cm),
        "embedding": list(product.embedding) if isinstance(product.embedding, list) else None,
    }


def _build_audit_snapshot(planogram: Planogram, shelf: Shelf) -> dict[str, Any]:
    """Freeze all shelf ground truth required to reproduce a later compliance audit."""
    placements = sorted(
        shelf.placements,
        key=lambda placement: (int(placement.row_index), float(placement.x_offset_cm), int(placement.id)),
    )
    products_by_id: dict[int, dict[str, Any]] = {}
    placement_snapshots: list[dict[str, Any]] = []
    expected_facing_slots: list[dict[str, Any]] = []
    expected_label_zones: list[dict[str, Any]] = []

    for placement in placements:
        product = placement.product
        product_id = int(product.id)
        product_data = products_by_id.setdefault(product_id, _product_snapshot(product))
        x_start = float(placement.x_offset_cm)
        facing_width = float(product.width_cm)
        x_end = x_start + facing_width * int(placement.facing_count)
        placement_snapshots.append({
            "placement_id": int(placement.id),
            "product_id": product_id,
            "row_index": int(placement.row_index),
            "x_offset_cm": x_start,
            "x_end_cm": x_end,
            "facing_count": int(placement.facing_count),
            "sku": product_data["sku"],
            "product_name": product_data["name"],
        })

        for facing_index in range(1, int(placement.facing_count) + 1):
            slot_start = x_start + facing_width * (facing_index - 1)
            expected_facing_slots.append({
                "slot_id": f"placement-{placement.id}-facing-{facing_index}",
                "placement_id": int(placement.id),
                "facing_index": facing_index,
                "product_id": product_id,
                "sku": product.sku,
                "row_index": int(placement.row_index),
                "x_start_cm": slot_start,
                "x_end_cm": slot_start + facing_width,
            })

        expected_label_zones.append({
            "label_zone_id": f"placement-{placement.id}-label",
            "placement_id": int(placement.id),
            "product_id": product_id,
            "sku": product.sku,
            "row_index": int(placement.row_index),
            "x_start_cm": x_start,
            "x_end_cm": x_end,
            "anchor": "below_placement",
            "expected_price": float(product.price),
            "expected_currency": product.currency or "INR",
            "geometry_status": "provisional_requires_image_calibration",
        })

    usable_height = max(0.0, float(shelf.total_height_cm) - (float(shelf.plinth_height_cm) if shelf.has_plinth else 0.0))
    default_row_height = max(10.0, usable_height / int(shelf.row_count))
    configured_heights = shelf.row_heights if isinstance(shelf.row_heights, list) and len(shelf.row_heights) == int(shelf.row_count) else None
    resolved_row_heights = []
    for row_index in range(int(shelf.row_count)):
        tallest_product = max(
            (float(p.product.height_cm) for p in placements if p.row_index == row_index),
            default=0.0,
        )
        min_row_height = max(10.0, tallest_product + 3.0)
        configured_height = configured_heights[row_index] if configured_heights and configured_heights[row_index] > 0 else default_row_height
        resolved_row_heights.append(max(min_row_height, float(configured_height)))
    plinth_cm = float(shelf.plinth_height_cm) if shelf.has_plinth else 0.0
    row_elevations_from_floor = [
        plinth_cm + sum(resolved_row_heights[row_index + 1 :])
        for row_index in range(int(shelf.row_count))
    ]

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    snapshot: dict[str, Any] = {
        "schema_version": 1,
        "captured_at": now,
        "planogram": {
            "id": int(planogram.id),
            "name": planogram.name,
            "description": planogram.description,
            "updated_at": planogram.updated_at.isoformat() if planogram.updated_at else None,
        },
        "shelf": {
            "id": int(shelf.id),
            "name": shelf.name,
            "width_cm": float(shelf.width_cm),
            "total_height_cm": float(shelf.total_height_cm),
            "depth_cm": float(shelf.depth_cm),
            "row_count": int(shelf.row_count),
            "row_heights_cm": list(shelf.row_heights) if isinstance(shelf.row_heights, list) else None,
            "resolved_row_heights_cm": resolved_row_heights,
            "row_elevations_from_floor_cm": row_elevations_from_floor,
            "row_index_origin": 0,
            "row_order": "top_to_bottom",
            "has_plinth": bool(shelf.has_plinth),
            "plinth_height_cm": float(shelf.plinth_height_cm),
        },
        "expected_placements": placement_snapshots,
        "expected_facing_slots": expected_facing_slots,
        "shelf_catalogue": sorted(products_by_id.values(), key=lambda product: product["id"]),
        "expected_label_zones": expected_label_zones,
        "limitations": [
            "Label zones are provisional horizontal spans derived from placements; image-space label geometry requires later calibration.",
        ],
    }
    canonical = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    snapshot["snapshot_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return snapshot


def queue_input_image(db: Session, input_image_id: int, planogram_id: int, shelf_id: int) -> dict[str, Any]:
    item = db.query(InputImage).options(joinedload(InputImage.job), joinedload(InputImage.output)).filter(InputImage.id == input_image_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Input image with ID {input_image_id} was not found.")
    if item.status not in {"ready", "failed"}:
        raise HTTPException(status_code=409, detail=f"This image is already {item.status} and cannot be queued again.")
    planogram, shelf, snapshot = _get_target(db, planogram_id, shelf_id)
    audit_snapshot = _build_audit_snapshot(planogram, shelf)
    if item.job:
        db.delete(item.job)
        db.flush()
        item.job = None
    item.planogram_id = planogram_id
    item.shelf_id = shelf_id
    item.shelf_snapshot = snapshot
    item.status = "queued"
    job = ProcessingJob(input_image_id=item.id, status="queued", audit_snapshot=audit_snapshot)
    item.job = job
    db.add(job)
    db.commit()
    db.refresh(item)
    log_backend("INFO", "IMAGE_QUEUED", f"Job {job.id}: input {item.id} assigned to planogram {planogram_id}, shelf {shelf_id}.")
    return _public(item)


def _run_pipeline(source_path: Path, output_dir: Path) -> tuple[Path, Path, dict[str, Any]]:
    """Run the isolated CV environment so its heavy dependencies stay out of FastAPI."""
    cv_root = settings.IMAGE_PARSING_DIR
    python = cv_root / ".venv" / "bin" / "python"
    if not python.exists():
        raise RuntimeError("Image-parsing environment is unavailable. Create image-parsing/.venv and install its requirements.")
    output_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(cv_root / "src")
    result = subprocess.run(
        [str(python), "-m", "shelf_image_parsing.cli", "--input", str(source_path), "--output", str(output_dir), "--save-json", "--no-save-csv"],
        cwd=cv_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=settings.IMAGE_PROCESSING_TIMEOUT_SECONDS,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Image-parsing pipeline failed.")
    stem = source_path.stem
    json_path = output_dir / f"{stem}_detections.json"
    annotated_path = output_dir / f"{stem}_annotated.jpg"
    if not json_path.exists() or not annotated_path.exists():
        raise RuntimeError("Image-parsing pipeline completed without required annotated image and JSON artifacts.")
    with json_path.open(encoding="utf-8") as handle:
        result_json = json.load(handle)
    return annotated_path, json_path, result_json


def process_pending_jobs() -> None:
    """Drain the durable queue serially. Safe to call from a background task or worker loop."""
    if not _worker_lock.acquire(blocking=False):
        return
    try:
        while True:
            db = SessionLocal()
            try:
                job = (
                    db.query(ProcessingJob)
                    .options(joinedload(ProcessingJob.input_image))
                    .filter(ProcessingJob.status == "queued")
                    .order_by(ProcessingJob.created_at.asc())
                    .first()
                )
                if not job:
                    return
                item = job.input_image
                job.status = "processing"
                job.started_at = datetime.utcnow()
                item.status = "processing"
                db.commit()
                job_id, input_id, source_path = job.id, item.id, _disk_path(item.storage_path)
            finally:
                db.close()

            try:
                target_dir = settings.UPLOADS_DIR / "image_processing" / "outputs" / str(job_id)
                annotated, result_json, payload = _run_pipeline(source_path, target_dir)
                db = SessionLocal()
                try:
                    job = db.query(ProcessingJob).options(joinedload(ProcessingJob.input_image)).filter(ProcessingJob.id == job_id).one()
                    item = job.input_image
                    metrics = payload.get("summary", {})
                    output = ProcessedOutput(
                        input_image_id=input_id,
                        job_id=job_id,
                        annotated_image_path=f"uploads/image_processing/outputs/{job_id}/{annotated.name}",
                        result_json_path=f"uploads/image_processing/outputs/{job_id}/{result_json.name}",
                        metrics=metrics,
                    )
                    db.add(output)
                    item.status = "processed"
                    job.status = "completed"
                    job.completed_at = datetime.utcnow()
                    db.commit()
                    db.refresh(output)

                    try:
                        from app.services.cutout_service import extract_cutouts_and_analyze
                        extract_cutouts_and_analyze(db, output.id)
                    except Exception as err:
                        log_backend("WARN", "ANALYSIS_DEFERRED", f"Job {job_id}: cutout analysis deferred: {err}")

                    log_backend("INFO", "IMAGE_DONE", f"Job {job_id}: input {input_id} processed successfully.")
                finally:
                    db.close()
            except Exception as exc:
                db = SessionLocal()
                try:
                    job = db.query(ProcessingJob).options(joinedload(ProcessingJob.input_image)).filter(ProcessingJob.id == job_id).first()
                    if job:
                        job.status = "failed"
                        job.error_message = str(exc)[:2000]
                        job.completed_at = datetime.utcnow()
                        job.input_image.status = "failed"
                        db.commit()
                    log_backend("ERROR", "IMAGE_FAILED", f"Job {job_id}: {exc}")
                finally:
                    db.close()
    finally:
        _worker_lock.release()


def recover_interrupted_jobs() -> None:
    """Return work interrupted by a server restart to the durable queue."""
    db = SessionLocal()
    try:
        interrupted = db.query(ProcessingJob).options(joinedload(ProcessingJob.input_image)).filter(ProcessingJob.status == "processing").all()
        for job in interrupted:
            job.status = "queued"
            job.started_at = None
            job.input_image.status = "queued"
        if interrupted:
            db.commit()
            log_backend("INFO", "IMAGE_RECOVERED", f"Returned {len(interrupted)} interrupted image job(s) to the queue.")
    finally:
        db.close()


def list_outputs(db: Session) -> list[dict[str, Any]]:
    outputs = (
        db.query(ProcessedOutput)
        .options(
            joinedload(ProcessedOutput.input_image).joinedload(InputImage.planogram),
            joinedload(ProcessedOutput.job),
        )
        .order_by(ProcessedOutput.created_at.desc())
        .all()
    )
    return [
        {
            "id": output.id,
            "input_image_id": output.input_image_id,
            "job_id": output.job_id,
            "annotated_image_path": output.annotated_image_path,
            "result_json_path": output.result_json_path,
            "metrics": output.metrics,
            "created_at": output.created_at,
            "source_filename": output.input_image.original_filename,
            "planogram_id": output.input_image.planogram_id,
            "planogram_name": output.input_image.planogram.name if output.input_image.planogram else None,
            "shelf_id": output.input_image.shelf_id,
            "shelf_snapshot": output.input_image.shelf_snapshot,
            "audit_snapshot": output.job.audit_snapshot if output.job else None,
            "compliance_audit": output.compliance_audit,
        }
        for output in outputs
    ]


def delete_input_image(db: Session, input_image_id: int) -> None:
    item = db.query(InputImage).filter(InputImage.id == input_image_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Input image not found.")
    if item.status == "processing":
        raise HTTPException(status_code=409, detail="Cannot delete an image while it is being processed.")
    paths = [_disk_path(item.storage_path)]
    if item.output:
        paths.extend([_disk_path(item.output.annotated_image_path), _disk_path(item.output.result_json_path)])
    db.delete(item)
    db.commit()
    for path in paths:
        path.unlink(missing_ok=True)
    output_dir = settings.UPLOADS_DIR / "image_processing" / "outputs"
    if output_dir.exists():
        for child in output_dir.iterdir():
            if child.is_dir() and not any(child.iterdir()):
                child.rmdir()


def delete_outputs(db: Session, output_ids: list[int]) -> int:
    outputs = db.query(ProcessedOutput).filter(ProcessedOutput.id.in_(output_ids)).all()
    if len(outputs) != len(set(output_ids)):
        raise HTTPException(status_code=404, detail="One or more selected outputs were not found.")
    paths: list[Path] = []
    for output in outputs:
        paths.extend([_disk_path(output.annotated_image_path), _disk_path(output.result_json_path)])
        output.input_image.status = "ready"
        db.delete(output)
    db.commit()
    for path in paths:
        path.unlink(missing_ok=True)
    return len(outputs)


def build_export_zip(db: Session, output_ids: list[int]) -> BytesIO:
    outputs = db.query(ProcessedOutput).options(joinedload(ProcessedOutput.input_image)).filter(ProcessedOutput.id.in_(output_ids)).all()
    if len(outputs) != len(set(output_ids)):
        raise HTTPException(status_code=404, detail="One or more selected outputs were not found.")
    manifest: list[dict[str, Any]] = []
    archive = BytesIO()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for output in outputs:
            annotated = _disk_path(output.annotated_image_path)
            result = _disk_path(output.result_json_path)
            if not annotated.exists() or not result.exists():
                raise HTTPException(status_code=409, detail=f"Artifacts for output {output.id} are unavailable.")
            prefix = f"output-{output.id}"
            zf.write(annotated, f"{prefix}/{annotated.name}")
            zf.write(result, f"{prefix}/{result.name}")
            audit_snapshot = output.job.audit_snapshot if output.job else None
            if audit_snapshot is not None:
                zf.writestr(f"{prefix}/audit_snapshot.json", json.dumps(audit_snapshot, indent=2))
            compliance_audit = output.compliance_audit
            compliance_path = None
            if isinstance(compliance_audit, dict):
                compliance_path = f"{prefix}/compliance_audit.json"
                zf.writestr(compliance_path, json.dumps(compliance_audit, indent=2))
                label_zones = compliance_audit.get("label_audit", {}).get("zones", [])
                output_dir = settings.UPLOADS_DIR / "image_processing" / "outputs" / str(output.job_id)
                for zone in label_zones if isinstance(label_zones, list) else []:
                    evidence_path = zone.get("evidence_image_path") if isinstance(zone, dict) else None
                    if not isinstance(evidence_path, str) or not evidence_path.startswith("uploads/"):
                        continue
                    disk_path = _disk_path(evidence_path)
                    try:
                        disk_path.resolve().relative_to(output_dir.resolve())
                    except ValueError:
                        continue
                    if disk_path.is_file():
                        zf.write(disk_path, f"{prefix}/label_evidence/{disk_path.name}")
            manifest.append({"output_id": output.id, "source_filename": output.input_image.original_filename, "planogram_id": output.input_image.planogram_id, "shelf_id": output.input_image.shelf_id, "metrics": output.metrics, "audit_snapshot_path": f"{prefix}/audit_snapshot.json" if audit_snapshot is not None else None, "compliance_audit_path": compliance_path})
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))
    archive.seek(0)
    return archive
