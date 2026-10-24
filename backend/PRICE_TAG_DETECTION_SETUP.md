# Price-tag detection setup

The optional Roboflow detector runs only in the backend. Configure `ROBOFLOW_API_KEY` in `backend/.env` (never in frontend variables or source control), then install `backend/requirements-roboflow.txt`. The key is sent as an authorization header by `inference-sdk`; it is not placed in the URL.

Model: `price-tag-detection-kjttf/16`. Images are sent to Roboflow Serverless for inference. Do not process images that may not be sent to that service. A missing key, SDK, OCR engine, or unavailable service must not interrupt product analysis; the compliance payload reports detection/OCR availability.

Detected tag crops and normalized results are cached under each output directory. A tag gets `Label Fetched Price` only when local EasyOCR returns a single unambiguous parsed price with a confident token; otherwise the UI says **Not clearly visible**. Detection boxes use a purple overlay. The current projected planogram label-zone OCR remains in the audit during this integration.

Install OCR separately with `backend/.venv/bin/pip install -r backend/requirements-ocr.txt`. Run backend tests from the repository root with `backend/.venv/bin/pytest backend/tests -q`.
