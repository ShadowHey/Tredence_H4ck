"""Validate the checked-in scenario-level ground truth fixture and its source image."""

import hashlib
import json
from pathlib import Path

import cv2


FIXTURE_DIR = Path(__file__).parents[1] / "fixtures" / "compliance" / "pipeline-verification"


def test_pipeline_verification_manifest_matches_fixture_image():
    manifest = json.loads((FIXTURE_DIR / "manifest.json").read_text(encoding="utf-8"))
    image_path = FIXTURE_DIR / manifest["source_image"]["file"]
    image_bytes = image_path.read_bytes()
    image = cv2.imread(str(image_path))

    assert hashlib.sha256(image_bytes).hexdigest() == manifest["source_image"]["sha256"]
    assert image is not None
    assert image.shape[:2] == (
        manifest["source_image"]["height_px"],
        manifest["source_image"]["width_px"],
    )


def test_pipeline_verification_planogram_and_expected_policy_are_explicit():
    manifest = json.loads((FIXTURE_DIR / "manifest.json").read_text(encoding="utf-8"))
    rows = manifest["planogram"]["rows"]
    observed = {entry["row"]: entry for entry in manifest["observations"]}

    assert [row["row"] for row in rows] == [1, 2, 3, 4]
    assert all(row["facing_count"] == 15 for row in rows)
    assert [row["sku"] for row in rows] == ["BEV-200", "BEV-201", "BEV-202", "BEV-203"]
    assert observed[1]["expected_findings"] == ["misplaced_product:BEV-201"]
    assert observed[2]["expected_findings"] == []
    assert "low_stock" in observed[2]["must_not_report"]
    assert observed[3]["expected_findings"] == []
    assert observed[4]["expected_findings"] == []
