# Local shelf-label OCR setup

Shelf-label OCR is an optional backend capability implemented with EasyOCR in CPU mode. The OCR adapter is separate from the image-parsing/YOLO environment so the detector package and OCR stack can be installed, tested, and upgraded independently.

## Install

From the repository root, install the optional engine in the backend environment:

```bash
backend/.venv/bin/pip install -r backend/requirements-ocr.txt
```

The backend application and API do not need to be restarted just to install the Python package; restart the backend before testing it. On first OCR use, EasyOCR initializes its English recognition/detection models and may download model weights. The official EasyOCR API documents `Reader(['en'], gpu=False)` for CPU mode and its `readtext` results include text boxes, text, and confidence. See the [EasyOCR project documentation](https://github.com/JaidedAI/EasyOCR#usage).

For offline setup, download the English model files using EasyOCR's documented model hub procedure and place them in the configured EasyOCR model directory before processing. The backend loads the reader lazily and caches one reader per process; set up the model cache for the same OS user that runs the backend.

## Output and safety policy

For every frozen expected label zone, OCR stores the row/centimetre-derived pixel region, crop evidence, text tokens, confidence, parsed amount/currency, and any catalogue product reference in the versioned compliance audit. X projection uses the detected row bounds and frozen shelf width. Since the snapshot has no image-space vertical label coordinates, the current crop uses the bottom 22% of the detected row as a provisional band. Product/price/missing/unreadable findings are always marked provisional until evaluated against labelled physical shelf photos; they are not definitive operator alerts yet.

If EasyOCR or its model weights are unavailable, the audit records `needs_review` with `ocr_engine_unavailable` instead of treating the label as correct or crashing the compliance endpoint. No external OCR service or API key is used.

## Verification

```bash
backend/.venv/bin/pytest backend/tests/unit/test_label_ocr_service.py backend/tests/unit/test_compliance_service.py -q
backend/.venv/bin/pytest backend/tests/integration/test_image_processing_api.py -q
```

The unit tests use a deterministic fake recognizer; they validate region projection, text/price parsing, association, evidence storage, and conservative failure handling. They do not establish real-world OCR accuracy. That requires the controlled labelled fixture photos listed in `docs/shared/COMPLIANCE_ROADMAP.md`.
