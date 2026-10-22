import io
import json
import shutil
from pathlib import Path

from PIL import Image
from sqlalchemy.orm import sessionmaker

from app.services import image_processing_service as service
from app.db.models import ProcessedOutput


def _sample_jpeg() -> io.BytesIO:
    image = Image.new("RGB", (8, 8), "white")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)
    return buffer


def _create_target(client, name: str = "Image Audit Planogram") -> tuple[int, int]:
    planogram = client.post("/api/v1/planograms", json={"name": name}).json()
    shelf = client.post(f"/api/v1/planograms/{planogram['id']}/shelves", json={
        "name": "Reference Bay", "width_cm": 120, "total_height_cm": 180,
        "depth_cm": 40, "row_count": 4,
    }).json()
    return planogram["id"], shelf["id"]


def test_input_image_requires_its_own_valid_planogram_and_shelf(client):
    planogram_id, shelf_id = _create_target(client)
    files = [("files", ("retail-shelf.jpg", _sample_jpeg(), "image/jpeg"))]
    upload = client.post("/api/v1/input-images", files=files)
    assert upload.status_code == 201
    image = upload.json()[0]
    assert image["status"] == "ready"

    wrong_planogram_id, _ = _create_target(client, "Different planogram")
    invalid = client.post(f"/api/v1/input-images/{image['id']}/process", json={"planogram_id": wrong_planogram_id, "shelf_id": shelf_id})
    assert invalid.status_code == 422
    assert "does not belong" in invalid.json()["detail"]


def test_one_image_generates_traceable_output_and_zip(client, db_session, monkeypatch, temp_uploads_dir):
    planogram_id, shelf_id = _create_target(client)
    files = [("files", ("shelf-a.jpg", _sample_jpeg(), "image/jpeg"))]
    image = client.post("/api/v1/input-images", files=files).json()[0]
    queued = client.post(f"/api/v1/input-images/{image['id']}/process", json={"planogram_id": planogram_id, "shelf_id": shelf_id})
    assert queued.status_code == 200
    assert queued.json()["status"] == "queued"

    def fake_pipeline(source_path: Path, output_dir: Path):
        output_dir.mkdir(parents=True, exist_ok=True)
        annotated = output_dir / f"{source_path.stem}_annotated.jpg"
        result = output_dir / f"{source_path.stem}_detections.json"
        shutil.copyfile(source_path, annotated)
        payload = {"summary": {"product_count": 3, "empty_region_count": 1, "shelf_row_count": 4, "empty_area_percentage": 12.5}}
        result.write_text(json.dumps(payload), encoding="utf-8")
        return annotated, result, payload

    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=db_session.bind)
    monkeypatch.setattr(service, "SessionLocal", TestingSession)
    monkeypatch.setattr(service, "_run_pipeline", fake_pipeline)
    service.process_pending_jobs()

    outputs = client.get("/api/v1/outputs")
    assert outputs.status_code == 200
    output = outputs.json()[0]
    assert output["source_filename"] == "shelf-a.jpg"
    assert output["planogram_id"] == planogram_id
    assert output["shelf_id"] == shelf_id
    assert output["shelf_snapshot"]["name"] == "Reference Bay"
    assert output["metrics"]["product_count"] == 3
    compliance = client.get(f"/api/v1/outputs/{output['id']}/compliance")
    assert compliance.status_code == 200
    audit = compliance.json()
    assert audit["output_id"] == output["id"]
    assert audit["job_id"] == output["job_id"]
    assert audit["audit_snapshot_sha256"] == output["audit_snapshot"]["snapshot_sha256"]
    assert audit["schema_version"] == 1
    assert audit["audit_version"] == 4
    assert audit["label_audit"]["status"] == "no_expected_label_zones"

    # Exercise a report issue and its durable operator workflow without depending on CV model output.
    stored_output = db_session.query(ProcessedOutput).filter_by(id=output["id"]).one()
    test_issue = {"type": "missing_product", "severity": "error", "sku": "TEST-1",
                  "row_index": 0, "x_start_cm": 2.0, "x_end_cm": 12.0,
                  "reason": "expected_slot_not_confirmed"}
    stored_output.compliance_audit = {**audit, "issues": [test_issue]}
    db_session.commit()
    report = client.get(f"/api/v1/outputs/{output['id']}/compliance").json()
    assert report["issues"][0]["status"] == "open"
    assert report["issues"][0]["recommended_action"]
    issue_id = report["issues"][0]["issue_id"]
    resolved = client.patch(f"/api/v1/outputs/{output['id']}/compliance/issues/{issue_id}",
                            json={"status": "resolved", "note": "Restocked during audit."})
    assert resolved.status_code == 200
    assert client.get(f"/api/v1/outputs/{output['id']}/compliance").json()["issues"][0]["status"] == "resolved"
    assert client.get(f"/api/v1/compliance/summary").json()["summary"]["resolved"] == 1
    compliance_export = client.get(f"/api/v1/outputs/{output['id']}/compliance/export.json")
    assert compliance_export.status_code == 200
    assert compliance_export.json()["report"]["issues"][0]["resolution_note"] == "Restocked during audit."
    invalid_issue = client.patch(f"/api/v1/outputs/{output['id']}/compliance/issues/{'f' * 64}",
                                 json={"status": "resolved"})
    assert invalid_issue.status_code == 404
    artifact_path = temp_uploads_dir / "/".join(output["annotated_image_path"].split("/")[1:])
    json_path = temp_uploads_dir / "/".join(output["result_json_path"].split("/")[1:])
    assert artifact_path.exists()
    assert json_path.exists()

    exported = client.post("/api/v1/outputs/export", json={"output_ids": [output["id"]]})
    assert exported.status_code == 200
    assert exported.headers["content-type"].startswith("application/zip")
    import zipfile
    from io import BytesIO
    with zipfile.ZipFile(BytesIO(exported.content)) as archive:
        assert f"output-{output['id']}/compliance_audit.json" in archive.namelist()

    removed = client.request("DELETE", "/api/v1/outputs", json={"output_ids": [output["id"]]})
    assert removed.status_code == 200
    assert client.get("/api/v1/input-images").json()[0]["status"] == "ready"
