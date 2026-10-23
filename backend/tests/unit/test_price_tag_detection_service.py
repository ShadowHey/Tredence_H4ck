import json
import sys
import types

from PIL import Image

from app.core.config import settings
from app.services import price_tag_detection_service as service


def test_box_conversion_clamps_and_rejects_degenerate_predictions():
    assert service._xyxy({"x": 5, "y": 5, "width": 20, "height": 8}, 10, 10) == [0, 1, 10, 9]
    assert service._xyxy({"x": 5, "y": 5, "width": 0, "height": 8}, 10, 10) is None


def test_no_key_is_reported_without_calling_roboflow(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "ROBOFLOW_API_KEY", None)
    result = service.detect_price_tags(tmp_path / "missing.jpg", tmp_path / "out")
    assert result["status"] == "not_configured"
    assert result["detections"] == []


def test_detector_filters_classes_saves_crop_and_caches(tmp_path, monkeypatch):
    image_path = tmp_path / "shelf.jpg"
    Image.new("RGB", (100, 80), "white").save(image_path)
    monkeypatch.setattr(settings, "UPLOADS_DIR", tmp_path)
    monkeypatch.setattr(settings, "ROBOFLOW_API_KEY", "test-key")

    class Client:
        def __init__(self, **kwargs):
            assert kwargs["api_key"] == "test-key"

        def configure(self, _):
            return self

        def infer(self, *_args, **_kwargs):
            return {"predictions": [
                {"class": "objects", "x": 20, "y": 20, "width": 10, "height": 10, "confidence": .9},
                {"class": "price_tag", "x": 50, "y": 40, "width": 20, "height": 10, "confidence": .8},
            ]}

    fake_sdk = types.ModuleType("inference_sdk")
    fake_sdk.InferenceHTTPClient = Client
    fake_sdk.InferenceConfiguration = lambda **kwargs: kwargs
    monkeypatch.setitem(sys.modules, "inference_sdk", fake_sdk)
    result = service.detect_price_tags(image_path, tmp_path / "out")
    assert result["status"] == "complete"
    assert len(result["detections"]) == 1
    assert result["detections"][0]["bbox_xyxy"] == [40, 35, 60, 45]
    assert (tmp_path / "out" / "price_tags" / "tag_0001.jpg").is_file()
    assert json.loads((tmp_path / "out" / "price_tag_detections.json").read_text())["status"] == "complete"


def test_older_sdk_uses_bearer_header_fallback(tmp_path, monkeypatch):
    image_path = tmp_path / "shelf.jpg"
    Image.new("RGB", (100, 80), "white").save(image_path)
    monkeypatch.setattr(settings, "UPLOADS_DIR", tmp_path)
    monkeypatch.setattr(settings, "ROBOFLOW_API_KEY", "test-key")
    monkeypatch.setattr(settings, "ROBOFLOW_PRICE_TAG_MODEL_ID", "price-tag-detection-kjttf/16")

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"predictions": [
                {"class": "price_tag", "x": 50, "y": 40, "width": 20, "height": 10, "confidence": .8},
            ]}

    def post(url, *, headers, files, timeout):
        assert url == "https://serverless.roboflow.com/price-tag-detection-kjttf/16"
        assert headers == {"Authorization": "Bearer test-key"}
        assert "api_key" not in url
        assert files["file"].read(1)
        assert timeout == 90
        return Response()

    monkeypatch.setattr("httpx.post", post)
    fake_sdk = types.ModuleType("inference_sdk")
    fake_sdk.InferenceConfiguration = lambda **kwargs: (_ for _ in ()).throw(
        TypeError("api_key_transport unsupported")
    )
    fake_sdk.InferenceHTTPClient = object
    monkeypatch.setitem(sys.modules, "inference_sdk", fake_sdk)

    result = service.detect_price_tags(image_path, tmp_path / "out")
    assert result["status"] == "complete"
    assert len(result["detections"]) == 1


def test_tag_ocr_accepts_one_confident_price_and_rejects_ambiguous_prices(tmp_path, monkeypatch):
    crop_path = tmp_path / "price-tag.jpg"
    Image.new("RGB", (80, 40), "white").save(crop_path)
    monkeypatch.setattr(settings, "UPLOADS_DIR", tmp_path)
    monkeypatch.setattr("app.services.label_ocr_service._easyocr_reader", lambda: object())

    tokens = [{"text": "4.99", "confidence": .92}]
    monkeypatch.setattr("app.services.label_ocr_service._read_text", lambda *_: tokens)
    result = {"detections": [{"id": "tag_0001", "crop_path": "uploads/price-tag.jpg"}]}
    service.read_tag_prices(result)
    assert result["detections"][0]["ocr_status"] == "read"
    assert result["detections"][0]["label_fetched_price"] == "4.99"

    tokens[:] = [{"text": "$4.99", "confidence": .92}, {"text": "$5.99", "confidence": .91}]
    result = {"detections": [{"id": "tag_0001", "crop_path": "uploads/price-tag.jpg"}]}
    service.read_tag_prices(result)
    assert result["detections"][0]["ocr_status"] == "unclear"
    assert result["detections"][0]["label_fetched_price"] == "Not clearly visible"

    tokens[:] = [{"text": "499", "confidence": .95}]
    result = {"detections": [{"id": "tag_0001", "crop_path": "uploads/price-tag.jpg"}]}
    service.read_tag_prices(result)
    assert result["detections"][0]["ocr_status"] == "unclear"
    assert result["detections"][0]["label_fetched_price"] == "Not clearly visible"
