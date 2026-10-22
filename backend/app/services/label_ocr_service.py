"""Shelf-label crop geometry, local OCR, price parsing, and provisional association."""

from __future__ import annotations

import re
import threading
from pathlib import Path
from typing import Any, Optional

from PIL import Image, ImageOps

from app.core.config import settings

OCR_CONFIDENCE_THRESHOLD = 0.70
LABEL_BAND_FRACTION = 0.22
MIN_LABEL_BAND_PX = 18
PRICE_TOLERANCE = 0.01

_reader_lock = threading.Lock()
_reader: Any = None


def _easyocr_reader() -> Any:
    """Load EasyOCR once in CPU mode; the first call may download model weights."""
    global _reader
    if _reader is None:
        with _reader_lock:
            if _reader is None:
                import easyocr
                _reader = easyocr.Reader(["en"], gpu=False, verbose=False)
    return _reader


def _valid_bbox(value: Any) -> Optional[tuple[int, int, int, int]]:
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        return None
    try:
        x1, y1, x2, y2 = (int(round(float(part))) for part in value)
    except (TypeError, ValueError):
        return None
    if x2 <= x1 or y2 <= y1:
        return None
    return x1, y1, x2, y2


def _inverse_homography(corners: Any) -> Optional[list[float]]:
    """Return normalized-shelf-to-image projection for TL/TR/BR/BL anchors."""
    if not isinstance(corners, list) or len(corners) != 4:
        return None
    try:
        points = [(float(point[0]), float(point[1])) for point in corners]
    except (TypeError, ValueError, IndexError):
        return None
    try:
        from app.services.position_calibration import _make_homography
        forward = _make_homography(points)
    except (ValueError, ZeroDivisionError):
        return None
    a, b, c, d, e, f, g, h, i = forward
    determinant = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    if abs(determinant) < 1e-10:
        return None
    inverse = [
        (e * i - f * h) / determinant, (c * h - b * i) / determinant, (b * f - c * e) / determinant,
        (f * g - d * i) / determinant, (a * i - c * g) / determinant, (c * d - a * f) / determinant,
        (d * h - e * g) / determinant, (b * g - a * h) / determinant, (a * e - b * d) / determinant,
    ]
    return inverse


def _project(matrix: list[float], x: float, y: float) -> Optional[tuple[float, float]]:
    denominator = matrix[6] * x + matrix[7] * y + matrix[8]
    if abs(denominator) < 1e-10:
        return None
    return ((matrix[0] * x + matrix[1] * y + matrix[2]) / denominator,
            (matrix[3] * x + matrix[4] * y + matrix[5]) / denominator)


def build_label_regions(
    snapshot: Optional[dict[str, Any]], shelf_rows: list[dict[str, Any]],
    image_size: tuple[int, int], position_calibration: Optional[dict[str, Any]],
    shelf_corners_xy: Any = None,
) -> list[dict[str, Any]]:
    """Project frozen cm label spans into provisional pixel crops on detected rows.

    X uses the calibrated row bounds and frozen usable shelf width. Y is a documented
    provisional band at the bottom of that detected row; this vertical heuristic must
    be validated on the physical fixture before findings are considered definitive.
    """
    if not isinstance(snapshot, dict):
        return []
    shelf = snapshot.get("shelf") if isinstance(snapshot.get("shelf"), dict) else {}
    try:
        shelf_width = float(shelf.get("width_cm"))
    except (TypeError, ValueError):
        shelf_width = 0.0
    image_width, image_height = image_size
    calibrated = isinstance(position_calibration, dict) and position_calibration.get("status") == "calibrated"
    corners_method = isinstance(position_calibration, dict) and position_calibration.get("method") == "four_corner_homography"
    inverse_h = _inverse_homography(shelf_corners_xy) if corners_method else None
    resolved_heights = shelf.get("resolved_row_heights_cm")
    if not isinstance(resolved_heights, list):
        resolved_heights = [1.0] * int(shelf.get("row_count") or 0)
    try:
        row_height_sum = sum(float(value) for value in resolved_heights)
        row_heights = [float(value) for value in resolved_heights]
    except (TypeError, ValueError):
        row_height_sum, row_heights = 0.0, []
    rows: dict[int, dict[str, Any]] = {}
    for row in shelf_rows:
        bbox = _valid_bbox(row.get("bbox_xyxy"))
        try:
            row_number = int(row.get("row_number"))
        except (TypeError, ValueError):
            continue
        if bbox and row_number > 0:
            rows[row_number - 1] = {"bbox": bbox, "row_number": row_number}

    regions = []
    zones = snapshot.get("expected_label_zones", [])
    for zone in zones if isinstance(zones, list) else []:
        if not isinstance(zone, dict):
            continue
        try:
            row_index = int(zone.get("row_index"))
            start_cm, end_cm = float(zone.get("x_start_cm")), float(zone.get("x_end_cm"))
        except (TypeError, ValueError):
            continue
        row = rows.get(row_index)
        if not calibrated or shelf_width <= 0 or not row or (corners_method and inverse_h is None):
            regions.append({"label_zone_id": zone.get("label_zone_id"), "placement_id": zone.get("placement_id"),
                            "product_id": zone.get("product_id"), "sku": zone.get("sku"),
                            "expected_price": zone.get("expected_price"), "expected_currency": zone.get("expected_currency"),
                            "row_index": row_index, "status": "needs_review", "reason": "label_zone_geometry_unavailable",
                            "bbox_xyxy": None, "geometry_method": None})
            continue
        rx1, ry1, rx2, ry2 = row["bbox"]
        row_width, row_height = rx2 - rx1, ry2 - ry1
        tolerance_cm = max(1.0, shelf_width * 0.01)
        polygon = None
        geometry_method = "row_bounds_cm_plus_provisional_bottom_band"
        if inverse_h is not None and row_height_sum > 0 and row_index < len(row_heights):
            row_top = sum(row_heights[:row_index]) / row_height_sum
            row_bottom = row_top + row_heights[row_index] / row_height_sum
            y_top = row_bottom - (row_bottom - row_top) * LABEL_BAND_FRACTION
            x_start = max(0.0, start_cm - tolerance_cm) / shelf_width
            x_end = min(shelf_width, end_cm + tolerance_cm) / shelf_width
            points = [_project(inverse_h, x_start, y_top), _project(inverse_h, x_end, y_top),
                      _project(inverse_h, x_end, row_bottom), _project(inverse_h, x_start, row_bottom)]
            if all(point is not None for point in points):
                polygon = [[round(point[0], 2), round(point[1], 2)] for point in points]
                x1 = max(0, min(image_width, int(min(point[0] for point in points))))
                x2 = max(0, min(image_width, int(max(point[0] for point in points)) + 1))
                y1 = max(0, min(image_height, int(min(point[1] for point in points))))
                y2 = max(0, min(image_height, int(max(point[1] for point in points)) + 1))
                geometry_method = "four_corner_homography_plus_provisional_row_band"
            else:
                x1 = x2 = y1 = y2 = 0
        else:
            x1 = max(0, min(image_width, int(round(rx1 + row_width * max(0, start_cm - tolerance_cm) / shelf_width))))
            x2 = max(0, min(image_width, int(round(rx1 + row_width * min(shelf_width, end_cm + tolerance_cm) / shelf_width))))
            band_height = max(MIN_LABEL_BAND_PX, int(round(row_height * LABEL_BAND_FRACTION)))
            y2 = max(0, min(image_height, ry2))
            y1 = max(0, min(image_height, y2 - band_height))
        bbox = [x1, y1, x2, y2] if x2 > x1 and y2 > y1 else None
        regions.append({"label_zone_id": zone.get("label_zone_id"), "placement_id": zone.get("placement_id"),
                        "product_id": zone.get("product_id"), "sku": zone.get("sku"),
                        "expected_price": zone.get("expected_price"), "expected_currency": zone.get("expected_currency"),
                        "row_index": row_index, "status": "ready" if bbox else "needs_review",
                        "reason": None if bbox else "empty_projected_label_zone", "bbox_xyxy": bbox,
                        "geometry_method": geometry_method, "polygon_xy": polygon,
                        "geometry_confidence": "provisional_requires_fixture_validation"})
    return regions


def _parse_price(text: str) -> Optional[dict[str, Any]]:
    currency = None
    upper = text.upper()
    if "₹" in text or re.search(r"\bRS\.?\b|\bINR\b", upper):
        currency = "INR"
    elif "$" in text:
        currency = "USD"
    elif "€" in text:
        currency = "EUR"
    elif "£" in text:
        currency = "GBP"
    pattern = re.compile(r"(?<![A-Z0-9])(?:₹|RS\.?\s*|INR\s*|\$|€|£)?\s*(\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)(?![A-Z0-9])", re.IGNORECASE)
    values = []
    for match in pattern.finditer(text):
        raw = match.group(1)
        try:
            value = float(raw.replace(",", ""))
        except ValueError:
            continue
        values.append({"value": value, "text": match.group(0).strip(), "currency": currency})
    return values[0] if values else None


def _catalogue_reference(text: str, catalogue: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    compact_text = re.sub(r"[^a-z0-9]", "", text.lower())
    if not compact_text:
        return None
    for product in catalogue:
        sku = re.sub(r"[^a-z0-9]", "", str(product.get("sku", "")).lower())
        name = re.sub(r"[^a-z0-9]", "", str(product.get("name", "")).lower())
        if (len(sku) >= 4 and sku in compact_text) or (len(name) >= 7 and name in compact_text):
            return {"id": product.get("id"), "sku": product.get("sku"), "name": product.get("name")}
    return None


def _read_text(reader: Any, crop: Image.Image) -> list[dict[str, Any]]:
    from numpy import asarray

    gray = ImageOps.autocontrast(crop.convert("L"))
    scale = max(1, min(4, int(160 / max(1, gray.height))))
    if scale > 1:
        gray = gray.resize((gray.width * scale, gray.height * scale), Image.Resampling.LANCZOS)
    rgb = gray.convert("RGB")
    with _reader_lock:
        raw = reader.readtext(asarray(rgb), detail=1, paragraph=False, decoder="beamsearch")
    tokens = []
    for row in raw or []:
        if not isinstance(row, (list, tuple)) or len(row) < 3:
            continue
        text, confidence = str(row[1]).strip(), row[2]
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            continue
        if text and 0 <= confidence <= 1:
            tokens.append({"text": text, "confidence": round(confidence, 4)})
    return tokens


def analyze_shelf_labels(
    *, image_path: Path, output_dir: Path, snapshot: Optional[dict[str, Any]],
    shelf_rows: list[dict[str, Any]], image_size: tuple[int, int],
    position_calibration: Optional[dict[str, Any]], shelf_corners_xy: Any = None, reader: Any = None,
) -> dict[str, Any]:
    """Run local OCR on expected label regions and return explicitly provisional findings."""
    regions = build_label_regions(snapshot, shelf_rows, image_size, position_calibration, shelf_corners_xy)
    catalogue = snapshot.get("shelf_catalogue", []) if isinstance(snapshot, dict) else []
    catalogue = catalogue if isinstance(catalogue, list) else []
    output_dir.mkdir(parents=True, exist_ok=True)
    if not regions:
        return {"engine": "EasyOCR", "engine_version": None, "status": "no_expected_label_zones",
                "confidence_threshold": OCR_CONFIDENCE_THRESHOLD, "price_tolerance": PRICE_TOLERANCE,
                "geometry_policy": "row-bounds x projection in cm; provisional bottom 22% of each detected row",
                "findings_are_provisional": True,
                "note": "No expected shelf-label zones were recorded in the frozen snapshot.",
                "zones": [], "issues": []}
    try:
        image = Image.open(image_path).convert("RGB")
    except (OSError, ValueError):
        image = None
    engine_error = None
    try:
        reader = reader if reader is not None else _easyocr_reader()
    except Exception as exc:  # missing dependency/model/offline download are actionable review states
        engine_error = type(exc).__name__
        reader = None

    results, issues = [], []
    for region in regions:
        result = {**region, "tokens": [], "text": "", "ocr_confidence": None,
                  "extracted_price": None, "detected_product_reference": None}
        if region.get("status") != "ready":
            result["status"] = "needs_review"
            result["reason"] = region.get("reason")
            issues.append(_finding("needs_review", result, region.get("reason", "label_zone_geometry_unavailable")))
            results.append(result)
            continue
        if image is None:
            result["status"], result["reason"] = "needs_review", "source_image_unavailable"
            issues.append(_finding("needs_review", result, result["reason"]))
            results.append(result)
            continue
        x1, y1, x2, y2 = region["bbox_xyxy"]
        evidence_path = output_dir / f"{re.sub(r'[^a-zA-Z0-9_-]', '_', str(region.get('label_zone_id') or 'label'))}.jpg"
        crop = image.crop((x1, y1, x2, y2))
        crop.save(evidence_path, "JPEG", quality=95)
        result["evidence_image_path"] = f"uploads/{evidence_path.relative_to(settings.UPLOADS_DIR).as_posix()}"
        if reader is None:
            result["status"], result["reason"] = "needs_review", "ocr_engine_unavailable"
            result["engine_error"] = engine_error
            issues.append(_finding("needs_review", result, result["reason"]))
            results.append(result)
            continue
        try:
            tokens = _read_text(reader, crop)
        except Exception as exc:
            result["status"], result["reason"] = "needs_review", "ocr_inference_failed"
            result["engine_error"] = type(exc).__name__
            issues.append(_finding("needs_review", result, result["reason"]))
            results.append(result)
            continue
        result["tokens"] = tokens
        result["text"] = " ".join(token["text"] for token in tokens)
        result["ocr_confidence"] = round(sum(token["confidence"] for token in tokens) / len(tokens), 4) if tokens else None
        reference = _catalogue_reference(result["text"], catalogue)
        result["detected_product_reference"] = reference
        prices = [_parse_price(token["text"]) for token in tokens]
        prices = [price for price in prices if price is not None]
        if prices:
            # Price is selected from the OCR token with the best confidence, not proximity to expected value.
            ranked = []
            for token in tokens:
                parsed = _parse_price(token["text"])
                if parsed:
                    ranked.append((token["confidence"], parsed))
            result["extracted_price"] = {**max(ranked, key=lambda pair: pair[0])[1],
                                         "confidence": max(ranked, key=lambda pair: pair[0])[0]}
        if not tokens:
            result["status"], result["reason"] = "missing_label", "no_text_detected_in_expected_label_region"
            issues.append(_finding("missing_label", result, result["reason"]))
        elif result["ocr_confidence"] < OCR_CONFIDENCE_THRESHOLD or not result["extracted_price"]:
            result["status"], result["reason"] = "unreadable_label", "low_confidence_or_no_price_detected"
            issues.append(_finding("unreadable_label", result, result["reason"]))
        else:
            result["status"], result["reason"] = "read", None
            if reference and str(reference.get("id")) != str(region.get("product_id")):
                issues.append(_finding("wrong_product_label", result, "label_text_references_a_different_catalogue_product"))
            price = result["extracted_price"]
            try:
                expected_price = float(region.get("expected_price"))
            except (TypeError, ValueError):
                expected_price = None
            expected_currency = str(region.get("expected_currency") or "").upper()
            actual_currency = str(price.get("currency") or expected_currency).upper()
            result["extracted_price"]["currency"] = actual_currency or None
            result["extracted_price"]["currency_source"] = "ocr_text" if price.get("currency") else "snapshot_assumption"
            if expected_price is not None and (abs(float(price["value"]) - expected_price) > PRICE_TOLERANCE
                    or (actual_currency and expected_currency and actual_currency != expected_currency)):
                issues.append(_finding("price_mismatch", result, "ocr_price_or_currency_differs_from_snapshot"))
        results.append(result)

    unavailable = reader is None
    try:
        from importlib.metadata import version
        engine_version = version("easyocr") if not unavailable else None
    except Exception:
        engine_version = None
    return {"engine": "EasyOCR", "engine_version": engine_version, "status": "unavailable" if unavailable else (
            "needs_review" if any(item["status"] == "needs_review" for item in results) else "completed"),
            "confidence_threshold": OCR_CONFIDENCE_THRESHOLD, "price_tolerance": PRICE_TOLERANCE,
            "geometry_policy": "row-bounds x projection in cm; provisional bottom 22% of each detected row",
            "findings_are_provisional": True,
            "note": "OCR/label geometry must be evaluated on labelled physical shelf fixtures before definitive alerts.",
            "zones": results, "issues": issues}


def _finding(kind: str, result: dict[str, Any], reason: str) -> dict[str, Any]:
    return {"type": kind, "severity": "warning", "provisional": True,
            "confidence_status": "needs_fixture_validation", "label_zone_id": result.get("label_zone_id"),
            "placement_id": result.get("placement_id"), "product_id": result.get("product_id"),
            "sku": result.get("sku"), "row_index": result.get("row_index"),
            "bbox_xyxy": result.get("bbox_xyxy"), "expected_price": result.get("expected_price"),
            "expected_currency": result.get("expected_currency"),
            "observed_text": result.get("text"), "observed_price": result.get("extracted_price"),
            "evidence_image_path": result.get("evidence_image_path"), "reason": reason}
