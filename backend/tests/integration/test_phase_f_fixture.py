"""Fixture-backed selected-planogram regression through image intake and audit APIs."""

import hashlib
import json
import shutil
from pathlib import Path

from sqlalchemy.orm import sessionmaker

from app.db.models import ProcessedOutput
from app.services import cutout_service, image_processing_service as processing_service
from app.services.compliance_service import build_compliance_audit


FIXTURE_DIR = Path(__file__).parents[3] / "image-parsing" / "tests" / "fixtures" / "compliance" / "pipeline-verification"


def _create_selected_planogram(client, manifest):
    planogram = client.post("/api/v1/planograms", json={"name": manifest["planogram"]["name"]}).json()
    shelf = client.post(f"/api/v1/planograms/{planogram['id']}/shelves", json={
        "name": manifest["planogram"]["shelf_name"], "width_cm": manifest["planogram"]["width_cm"],
        "total_height_cm": manifest["planogram"]["height_cm"], "depth_cm": 40, "row_count": 4,
    }).json()
    ids_by_sku = {}
    for row in manifest["planogram"]["rows"]:
        product = client.post("/api/v1/products/direct", json={
            "sku": row["sku"], "name": row["product"], "category": "Fixture",
            "width_cm": manifest["planogram"]["width_cm"] / row["facing_count"],
            "height_cm": 20, "depth_cm": 5, "price": 50, "currency": "INR",
            "image_path": "uploads/fixture-packshot.png",
        })
        assert product.status_code == 201
        ids_by_sku[row["sku"]] = product.json()["id"]
        placement = client.post(f"/api/v1/shelves/{shelf['id']}/placements", json={
            "product_id": ids_by_sku[row["sku"]], "row_index": row["row"] - 1,
            "x_offset_cm": 0, "facing_count": row["facing_count"],
        })
        assert placement.status_code == 201
    return planogram, shelf, ids_by_sku


def _position(row, start, end):
    return {"status": "calibrated", "method": "detected_row_linear", "row_index": row,
            "x_start_cm": start, "x_end_cm": end, "center_x_cm": (start + end) / 2,
            "position_tolerance_cm": 1.0}


def test_labeled_shelf_fixture_runs_through_selected_planogram_to_compliance_report(
    client, db_session, monkeypatch, temp_uploads_dir,
):
    manifest_path = FIXTURE_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    photo_path = FIXTURE_DIR / manifest["source_image"]["file"]
    assert hashlib.sha256(photo_path.read_bytes()).hexdigest() == manifest["source_image"]["sha256"]
    planogram, shelf, ids_by_sku = _create_selected_planogram(client, manifest)

    upload = client.post("/api/v1/input-images", files=[(
        "files", (photo_path.name, photo_path.read_bytes(), "image/png"),
    )])
    assert upload.status_code == 201
    input_image = upload.json()[0]
    queued = client.post(f"/api/v1/input-images/{input_image['id']}/process", json={
        "planogram_id": planogram["id"], "shelf_id": shelf["id"],
    })
    assert queued.status_code == 200
    assert queued.json()["status"] == "queued"

    def fake_pipeline(source_path: Path, output_dir: Path):
        output_dir.mkdir(parents=True, exist_ok=True)
        annotated = output_dir / f"{source_path.stem}_annotated.jpg"
        result = output_dir / f"{source_path.stem}_detections.json"
        shutil.copyfile(source_path, annotated)
        result.write_text(json.dumps({"summary": {"product_count": 58, "empty_region_count": 1,
                                                   "shelf_row_count": 4, "empty_area_percentage": 2.0}}), encoding="utf-8")
        return annotated, result, {"summary": {"product_count": 58, "empty_region_count": 1,
                                                "shelf_row_count": 4, "empty_area_percentage": 2.0}}

    def persist_fixture_audit(db, output_id, force_recompute=False):
        output = db.query(ProcessedOutput).filter_by(id=output_id).one()
        snapshot = output.job.audit_snapshot
        slots = snapshot["expected_facing_slots"]
        slot_by_row = {row: [slot for slot in slots if slot["row_index"] == row] for row in range(4)}
        observed = []
        # One Yellow Lays facing is deliberately placed in the chocolate row.
        for row in range(4):
            for slot in slot_by_row[row]:
                if row == 0 and slot["facing_index"] == 10:
                    sku = "BEV-201"
                elif row == 1 and slot["facing_index"] == 15:
                    continue  # Isolated empty facing: 14/15 remains above low-stock threshold.
                else:
                    sku = next(entry["sku"] for entry in manifest["planogram"]["rows"] if entry["row"] == row + 1)
                start, end = slot["x_start_cm"], slot["x_end_cm"]
                observed.append({"id": f"fixture-{row}-{slot['facing_index']}",
                    "planogram_position": _position(row, start, end),
                    "catalog_match": {"status": "matched", "top_candidate": {
                        "id": ids_by_sku[sku], "sku": sku,
                    }}})
        audit = build_compliance_audit(
            output_id=output.id, job_id=output.job_id, source_filename=photo_path.name,
            snapshot=snapshot, snapshot_sha256=snapshot["snapshot_sha256"], products=observed,
            empty_spaces=[{"id": "fixture-empty-row-2", "planogram_position": _position(1, 112, 120)}],
            position_calibration={"status": "calibrated", "method": "detected_row_linear"},
            label_audit={"status": "no_expected_label_zones", "zones": [], "issues": []},
        )
        output.compliance_audit = audit
        db.commit()
        return {"output_id": output_id, "compliance_summary": audit["summary"]}

    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=db_session.bind)
    monkeypatch.setattr(processing_service, "SessionLocal", TestingSession)
    monkeypatch.setattr(processing_service, "_run_pipeline", fake_pipeline)
    monkeypatch.setattr(cutout_service, "extract_cutouts_and_analyze", persist_fixture_audit)
    processing_service.process_pending_jobs()

    output = client.get("/api/v1/outputs").json()[0]
    assert output["planogram_id"] == planogram["id"]
    assert output["shelf_id"] == shelf["id"]
    report_response = client.get(f"/api/v1/outputs/{output['id']}/compliance")
    assert report_response.status_code == 200
    report = report_response.json()
    assert report["audit_snapshot_sha256"] == output["audit_snapshot"]["snapshot_sha256"]
    assert report["status"] == "complete"
    assert report["summary"]["misplaced_product"] == 1
    assert report["summary"]["missing_product"] == 0
    assert report["summary"]["insufficient_quantity"] == 0
    assert not any(issue["type"] in {"missing_product", "insufficient_quantity"} for issue in report["issues"])
    row_two = next(row for row in report["layout_comparison"]["rows"] if row["row_index"] == 1)
    assert len(row_two["observed_products"]) == 14
    assert len(row_two["observed_empty_regions"]) == 1
