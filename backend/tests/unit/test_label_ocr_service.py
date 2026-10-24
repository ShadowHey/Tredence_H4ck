from PIL import Image

from app.core.config import settings
from app.services import label_ocr_service as service


def snapshot():
    return {
        "shelf": {"width_cm": 100, "row_count": 1},
        "expected_label_zones": [
            {"label_zone_id": "label-a", "placement_id": 1, "product_id": 1, "sku": "SKU-A",
             "row_index": 0, "x_start_cm": 10, "x_end_cm": 40, "expected_price": 10.0, "expected_currency": "INR"},
            {"label_zone_id": "label-b", "placement_id": 2, "product_id": 2, "sku": "SKU-B",
             "row_index": 0, "x_start_cm": 50, "x_end_cm": 80, "expected_price": 20.0, "expected_currency": "INR"},
        ],
        "shelf_catalogue": [
            {"id": 1, "sku": "SKU-A", "name": "Alpha Biscuit"},
            {"id": 2, "sku": "SKU-B", "name": "Beta Cereal"},
        ],
    }


def output_label_dir(tmp_path, monkeypatch):
    uploads = tmp_path / "uploads"
    uploads.mkdir(exist_ok=True)
    monkeypatch.setattr(settings, "UPLOADS_DIR", uploads)
    label_dir = uploads / "image_processing" / "outputs" / "1" / "label_zones"
    return uploads, label_dir


def test_label_regions_project_snapshot_cm_spans_into_provisional_bottom_band():
    regions = service.build_label_regions(
        snapshot(), [{"row_number": 1, "bbox_xyxy": [10, 20, 210, 120]}],
        (220, 130), {"status": "calibrated", "method": "detected_row_linear"},
    )
    assert regions[0]["bbox_xyxy"] == [28, 98, 92, 120]
    assert regions[0]["geometry_method"] == "row_bounds_cm_plus_provisional_bottom_band"
    assert regions[0]["geometry_confidence"] == "provisional_requires_fixture_validation"


def test_missing_calibration_never_creates_guessed_image_roi():
    regions = service.build_label_regions(snapshot(), [], (220, 130), {"status": "needs_review"})
    assert all(region["status"] == "needs_review" and region["bbox_xyxy"] is None for region in regions)


def test_four_corner_calibration_projects_label_zone_through_perspective():
    snapshot_data = snapshot()
    snapshot_data["shelf"]["resolved_row_heights_cm"] = [50]
    regions = service.build_label_regions(
        snapshot_data, [{"row_number": 1, "bbox_xyxy": [10, 20, 210, 120]}],
        (220, 130), {"status": "calibrated", "method": "four_corner_homography"},
        [[10, 20], [210, 20], [190, 120], [30, 120]],
    )
    assert regions[0]["status"] == "ready"
    assert regions[0]["geometry_method"] == "four_corner_homography_plus_provisional_row_band"
    assert len(regions[0]["polygon_xy"]) == 4


def test_price_parser_handles_currency_and_grouped_amounts():
    assert service._parse_price("₹1,299.00") == {"value": 1299.0, "text": "₹1,299.00", "currency": "INR"}
    assert service._parse_price("Rs. 25.50") == {"value": 25.5, "text": "Rs. 25.50", "currency": "INR"}
    assert service._parse_price("PRICE") is None


def test_ocr_price_and_wrong_label_findings_are_explicitly_provisional(tmp_path, monkeypatch):
    uploads, label_dir = output_label_dir(tmp_path, monkeypatch)
    source = tmp_path / "shelf.jpg"
    Image.new("RGB", (220, 130), "white").save(source)
    monkeypatch.setattr(service, "_read_text", lambda reader, crop: [
        {"text": "SKU-A", "confidence": 0.95}, {"text": "₹12.50", "confidence": 0.91},
    ])
    audit = service.analyze_shelf_labels(
        image_path=source, output_dir=label_dir, snapshot=snapshot(),
        shelf_rows=[{"row_number": 1, "bbox_xyxy": [10, 20, 210, 120]}],
        image_size=(220, 130), position_calibration={"status": "calibrated"}, reader=object(),
    )
    assert audit["engine"] == "EasyOCR"
    assert audit["findings_are_provisional"] is True
    assert any(issue["type"] == "price_mismatch" for issue in audit["issues"])
    assert any(issue["type"] == "wrong_product_label" for issue in audit["issues"])
    assert all(issue["provisional"] and issue["confidence_status"] == "needs_fixture_validation" for issue in audit["issues"])
    assert all((uploads / issue["evidence_image_path"].removeprefix("uploads/")).is_file() for issue in audit["issues"])
    assert len(list(label_dir.glob("*.jpg"))) == 2


def test_low_confidence_and_no_text_are_not_reported_as_success(tmp_path, monkeypatch):
    _, label_dir = output_label_dir(tmp_path, monkeypatch)
    source = tmp_path / "shelf.jpg"
    Image.new("RGB", (220, 130), "white").save(source)
    responses = iter([[{"text": "12?5", "confidence": 0.2}], []])
    monkeypatch.setattr(service, "_read_text", lambda reader, crop: next(responses))
    audit = service.analyze_shelf_labels(
        image_path=source, output_dir=label_dir, snapshot=snapshot(),
        shelf_rows=[{"row_number": 1, "bbox_xyxy": [10, 20, 210, 120]}],
        image_size=(220, 130), position_calibration={"status": "calibrated"}, reader=object(),
    )
    assert [zone["status"] for zone in audit["zones"]] == ["unreadable_label", "missing_label"]
    assert {issue["type"] for issue in audit["issues"]} == {"unreadable_label", "missing_label"}


def test_unavailable_engine_returns_review_not_false_clean_result(tmp_path, monkeypatch):
    _, label_dir = output_label_dir(tmp_path, monkeypatch)
    source = tmp_path / "shelf.jpg"
    Image.new("RGB", (220, 130), "white").save(source)
    monkeypatch.setattr(service, "_easyocr_reader", lambda: (_ for _ in ()).throw(ImportError("not installed")))
    audit = service.analyze_shelf_labels(
        image_path=source, output_dir=label_dir, snapshot=snapshot(),
        shelf_rows=[{"row_number": 1, "bbox_xyxy": [10, 20, 210, 120]}],
        image_size=(220, 130), position_calibration={"status": "calibrated"},
    )
    assert audit["status"] == "unavailable"
    assert all(zone["status"] == "needs_review" for zone in audit["zones"])
