"""Optional Roboflow price-tag detection with local evidence and OCR artifacts."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from app.core.config import settings

logger = logging.getLogger(__name__)
MODEL_ID = "price-tag-detection-kjttf/16"
TAG_CLASSES = {"price_tag", "price_label"}


def _infer_with_bearer_header(image_path: Path, model_id: str, api_key: str) -> dict[str, Any]:
    """Call Roboflow without putting the secret in the URL query string."""
    import httpx

    with image_path.open("rb") as image_file:
        reply = httpx.post(
            f"https://serverless.roboflow.com/{model_id}",
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": image_file},
            timeout=90,
        )
    reply.raise_for_status()
    return reply.json()


def _xyxy(prediction: dict[str, Any], width: int, height: int) -> list[int] | None:
    try:
        cx, cy = float(prediction["x"]), float(prediction["y"])
        w, h = float(prediction["width"]), float(prediction["height"])
    except (KeyError, TypeError, ValueError):
        return None
    box = [max(0, round(cx - w / 2)), max(0, round(cy - h / 2)),
           min(width, round(cx + w / 2)), min(height, round(cy + h / 2))]
    return box if box[2] > box[0] and box[3] > box[1] else None


def detect_price_tags(image_path: Path, output_dir: Path) -> dict[str, Any]:
    """Infer once per output, cache normalized tag boxes, and save distinct crops."""
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_path = output_dir / "price_tag_detections.json"
    if cache_path.is_file():
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            logger.warning("Ignoring invalid cached price-tag results")
    api_key = (settings.ROBOFLOW_API_KEY or "").strip()
    if not api_key:
        return {"status": "not_configured", "model_id": settings.ROBOFLOW_PRICE_TAG_MODEL_ID,
                "detections": [], "message": "ROBOFLOW_API_KEY is not configured."}
    try:
        model_id = settings.ROBOFLOW_PRICE_TAG_MODEL_ID or MODEL_ID
        try:
            from inference_sdk import InferenceConfiguration, InferenceHTTPClient
            try:
                configuration = InferenceConfiguration(api_key_transport="header")
            except TypeError:
                # Older SDK releases do not support header transport. Use the
                # direct header-auth request; never fall back to query auth.
                response = _infer_with_bearer_header(image_path, model_id, api_key)
            else:
                client = InferenceHTTPClient(api_url="https://serverless.roboflow.com", api_key=api_key).configure(
                    configuration)
                response = client.infer(str(image_path), model_id=model_id)
        except ImportError:
            # Keep inference usable in lean environments without the optional SDK.
            response = _infer_with_bearer_header(image_path, model_id, api_key)
        with Image.open(image_path) as source:
            image = source.convert("RGB")
        width, height = image.size
        detections = []
        for prediction in response.get("predictions", []) if isinstance(response, dict) else []:
            if not isinstance(prediction, dict) or str(prediction.get("class", "")).lower() not in TAG_CLASSES:
                continue
            box = _xyxy(prediction, width, height)
            if box is None:
                continue
            index = len(detections) + 1
            tag_id = f"tag_{index:04d}"
            crop_path = output_dir / "price_tags" / f"{tag_id}.jpg"
            crop_path.parent.mkdir(parents=True, exist_ok=True)
            image.crop(tuple(box)).save(crop_path, "JPEG", quality=95)
            detections.append({"id": tag_id, "class": str(prediction.get("class")),
                "confidence": round(float(prediction.get("confidence", 0)), 4), "bbox_xyxy": box,
                "crop_path": f"uploads/{crop_path.relative_to(settings.UPLOADS_DIR).as_posix()}",
                "label_fetched_price": "Not clearly visible", "ocr_status": "unavailable"})
        result = {"status": "complete", "model_id": settings.ROBOFLOW_PRICE_TAG_MODEL_ID or MODEL_ID,
                  "detections": detections}
        cache_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result
    except Exception as exc:
        # Optional external inference must not break product detection/compliance.
        logger.warning("Price-tag inference unavailable (%s)", type(exc).__name__)
        return {"status": "unavailable", "model_id": settings.ROBOFLOW_PRICE_TAG_MODEL_ID or MODEL_ID,
                "detections": [], "message": "Price-tag detection is temporarily unavailable."}


def read_tag_prices(result: dict[str, Any]) -> dict[str, Any]:
    """Reuse the existing local EasyOCR reader/parser for detected-tag crops."""
    detections = result.get("detections", [])
    if not detections:
        return result
    try:
        from app.services.label_ocr_service import _easyocr_reader, _parse_price, _read_text
        reader = _easyocr_reader()
    except Exception as exc:
        logger.info("Shelf-label OCR unavailable (%s)", type(exc).__name__)
        for detection in detections:
            detection["ocr_status"] = "unavailable"
        return result
    for detection in detections:
        try:
            detection.setdefault("label_fetched_price", "Not clearly visible")
            crop_path = settings.UPLOADS_DIR / detection["crop_path"].removeprefix("uploads/")
            with Image.open(crop_path) as crop:
                tokens = _read_text(reader, crop)
            confident = [token for token in tokens if token["confidence"] >= 0.70]
            text = " ".join(token["text"] for token in tokens)
            # Parse each confident OCR token independently so separate amounts
            # remain ambiguous instead of silently selecting the first one.
            prices = [price for token in confident if (price := _parse_price(token["text"]))]
            price = prices[0] if len(prices) == 1 else None
            price_text = str(price.get("text", "")) if price else ""
            # A bare integer like "499" can be a lost decimal ("4.99").
            # Without an explicit currency marker, require the decimal to be
            # visible before presenting it as a fetched shelf price.
            if price and (price.get("currency") or "." in price_text):
                amount = f"{price['value']:g}"
                detection["label_fetched_price"] = f"₹{amount}" if price.get("currency") == "INR" else amount
                detection["extracted_price"] = price
                detection["ocr_status"] = "read"
            else:
                detection["ocr_status"] = "unclear"
            detection["tokens"] = tokens
            detection["text"] = text
            detection["ocr_confidence"] = round(sum(t["confidence"] for t in tokens) / len(tokens), 4) if tokens else None
        except Exception as exc:
            logger.info("OCR failed for %s (%s)", detection.get("id"), type(exc).__name__)
            detection["ocr_status"] = "unavailable"
    return result


def draw_price_tag_boxes(image_path: Path, detections: list[dict[str, Any]]) -> None:
    """Add a purple tag-only layer without changing detector output or product boxes."""
    if not detections or not image_path.is_file():
        return
    with Image.open(image_path) as source:
        image = source.convert("RGB")
    draw = ImageDraw.Draw(image)
    for detection in detections:
        box = detection.get("bbox_xyxy")
        if isinstance(box, list) and len(box) == 4:
            draw.rectangle(box, outline="#c084fc", width=max(2, round(min(image.size) / 500)))
            draw.text((box[0], max(0, box[1] - 14)), f"PRICE TAG {detection.get('confidence', 0):.0%}", fill="#c084fc")
    image.save(image_path)
