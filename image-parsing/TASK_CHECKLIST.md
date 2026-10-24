# ShelfSense AI — Image Parsing Task Checklist & Recovery Roadmap

**Repository Root**: `image-parsing/`  
**Pipeline Objective**: Combine (1) Product/Object Bounding Boxes (Neon Cyan `#00E5FF`), (2) Empty Shelf-Space Bounding Boxes (Royal Blue `#1739B7`, translucent fill), and (3) Shelf-Row Segmentation & Boundaries (Amber `#FFB000`, sorted top-to-bottom as `ROW 1`, `ROW 2`, ...) into **ONE unified annotated image**, typed **JSON**, and **CSV** for every input photograph.

**Status as of Current Checkpoint**:
- Core codebase: **100% Implemented** (10/10 modules in `src/shelf_image_parsing/`)
- Unit & Integration Test Suites: **100% Passed** (28/28 tests passed in 0.31s)
- Model Calibration: Calibrated detection threshold (`0.20`) and segmentation threshold (`0.15`) + product-bounded shelf vertical filtering.
- Re-evaluated Benchmarks:
  - `test_987.jpg`: **5 rows** (up from 2), **6 empty spaces** (up from 2, empty area **11.11%** vs 2.05%), large center empty void now captured!
  - `test_999 (1).jpg`: **7 rows**, **147 products**, **1 empty slot**, **0.64% empty**.
  - `test_image.jpg`: **90 products**, **4 empty voids** (5.43% empty space).
- Newly Uploaded Images Evaluated:
  - `new_01_pharmacy_pegboard.jpg`: **102 products**, **2 empty spaces**, **3 rows** (1.74% empty).
  - `new_02_coffee_pods.jpg`: **155 products**, **2 empty spaces**, **8 rows** (1.91% empty).
  - `new_03_dove_bodywash.jpg`: **127 products**, **2 empty spaces**, **9 rows** (1.85% empty).
  - `new_04_packaged_hygiene.jpg`: **187 products**, **3 empty spaces**, **12 rows** (1.39% empty).
  - `new_05_medicines_aisle.jpg`: **155 products**, **3 empty spaces**, **8 rows** (2.46% empty).
- Output Validation: All 8 output images open, retain 100% native resolution, and have matching JSON detections and aggregated CSV summary.

---

## Shelf Compliance Accuracy Work — Phases A and B (2026-10-22)

This is the current handoff checklist for the requested accuracy work. Phase A and B
are scoped to fixture truth and detection/crop geometry quality; no model retraining or
guessed bounding-box repair is claimed.

### Phase A — Reproducible ground-truth fixture
- [x] Preserve the exact original Output #7 shelf image under `tests/fixtures/compliance/pipeline-verification/`.
- [x] Record SHA-256, dimensions, frozen planogram rows/SKUs/facings, and expected issue policy in `manifest.json`.
- [x] Mark that counts/outcomes are operator-reviewed scenario truth, not manually labeled pixel boxes or detector benchmark truth.
- [x] Add tests for image integrity, four-row planogram mapping, and expected alert policy.
- [x] Document the fixture's scope and limits for future agents.

### Phase B — Conservative detection and crop-quality safeguards
- [x] Remove only near-contained, same-class duplicate predictions after YOLO NMS; preserve adjacent facings and original coordinates.
- [x] Add row-relative narrow/short geometry flags without silently resizing or merging detections.
- [x] Persist quality status/flags in cutout metadata and typed API/frontend contracts for downstream review.
- [x] Show a separate geometry warning on Product Match cards when a crop's box is flagged; retain the independent CLIP identity state.
- [x] Version-bump cutout analysis cache so existing outputs are recalculated with the new metadata.
- [x] Add unit regression tests for duplicate containment, adjacency, class boundaries, and suspicious geometry.
- [x] Run full image-parser, backend, and frontend unit/type suites; perform a model-backed Output #7 rerun.

**Verification result:** Image-parser tests: 38 passed; backend tests: 65 passed (the runner emitted 65 passing dots); frontend TypeScript and Vitest: passed (21 tests). Model-backed fixture smoke run completed with 70 products, 1 empty-space region, 4 shelf rows, and 2 narrow-box review flags. It is a baseline, not evidence that localization accuracy improved.

**Phase B limitation:** Quality flags are advisory and do not improve the underlying YOLO localization by themselves. Accurate AP/precision/recall and model retraining require a separately reviewed pixel-box annotation set. No products are merged or auto-expanded because those operations can hide adjacent items or fabricate geometry.

### Phase C — Catalogue consensus and fragmented cluster identity
- [x] Keep individual crop-to-shelf-catalogue CLIP/color-first results as the source evidence; do not replace crop states with a cluster guess.
- [x] Use row-scoped catalogue voting to merge fragmented visual clusters only when the same candidate has a clear majority; retain mixed/uncalibrated groups separately.
- [x] Exclude geometry-review crops from catalogue votes while preserving them as visible cluster members.
- [x] Require at least two supporting crops and a 60% candidate majority; require the same ratio of individually confirmed votes before a cluster is marked matched.
- [x] Expose cluster vote support and review status in the analysis response/UI; invalidate old cached grouping with analysis version 8.
- [x] Add regression tests for same-row majority consolidation, product dissent, row isolation, low-quality crop exclusion, and singleton abstention.
- [ ] Validate cluster thresholds and product identity on a manually reviewed crop-level fixture before treating the cutoffs as calibrated.

**Phase C limitation:** Consensus is an explainable aggregation of existing per-crop catalogue matches, not new visual evidence. It can consolidate fragmented same-row groups but cannot repair bad YOLO boxes or guarantee correct SKU identity. Individual crop results remain visible and unchanged; weak or suspicious evidence stays review-needed.

### Phase D — Planogram comparison and actionable alert policy
- [x] Evaluate stock quantity per planogram placement and row, rather than raising a separate shortage alert for every empty facing or aggregating the SKU across unrelated rows.
- [x] Preserve slot-level comparison results as evidence while suppressing low-stock alerts when more than 50% of expected facings are present.
- [x] Emit one placement-level low-stock warning at exactly 50% or lower; emit one missing-product issue when no correctly attributable stock is detected.
- [x] Do not infer stock shortage when position calibration is unavailable; preserve review-needed results.
- [x] Keep misplaced-product identity/position issues distinct from stock shortage, including when the expected SKU is present but misplaced within its row.
- [x] Add boundary tests (14/15, 5/10, zero stock), placement isolation, and audit-version regression coverage.
- [ ] Validate alert thresholds on the controlled physical shelf scenarios and labeled per-facing/photo evidence before calling them calibrated.

**Phase D limitation:** The 50% cutoff is the requested provisional policy, not an empirically validated retail threshold. Alert correctness remains constrained by detection and catalogue identity quality; missing or uncalibrated geometry fails safely to review.

---

## Master Task Checklist

### Phase 1: Reference Inspection & Asset Verification
- [x] **1.1 Inspect Reference Repository (`K-saif/Empty-Shelf-Alert-System`)**
  - Identified dual-model approach: YOLO detection for products & empty spaces, YOLO-seg for shelf row contours.
- [x] **1.2 Verify Model Weights Availability & Paths**
  - `image-parsing/models/detect_product_empty_space.pt` (5.2 MB, YOLO11 detection) verified.
  - `image-parsing/models/segment_shelf_rows.pt` (5.7 MB, YOLO11-seg) verified.
- [x] **1.3 Locate and Copy Raw Supermarket Inputs**
  - Initial benchmarks: `test_987.jpg`, `test_999 (1).jpg`, `test_image.jpg`.
  - Newly uploaded inputs: `new_01_pharmacy_pegboard.jpg`, `new_02_coffee_pods.jpg`, `new_03_dove_bodywash.jpg`, `new_04_packaged_hygiene.jpg`, `new_05_medicines_aisle.jpg`.
- [x] **1.4 Directory Skeleton Creation**
  - Created: `config/`, `models/`, `sample_inputs/`, `outputs/`, `src/shelf_image_parsing/`, `scripts/`, `tests/`.
- [x] **1.5 Python Isolated Virtual Environment & Dependencies**
  - Python 3.11 virtualenv with PyTorch 2.14.1, torchvision 0.29.1, Ultralytics 8.4.183, OpenCV 4.11.0, NumPy 1.26.4.

---

### Phase 2: Core Domain Logic & Calibration
- [x] **2.1 Configuration Management (`config.py` & `config/default.yaml`)**
  - Calibrated defaults: detection confidence 0.20, segmentation confidence 0.15.
- [x] **2.2 Typed Schemas (`schemas.py`)**
  - Pydantic models with serialization and per-row flat CSV mappings.
- [x] **2.3 Spatial & Geometric Utilities (`geometry.py`)**
  - Box clipping, normalization, IoU, center point, polygon bbox, and NMS.
- [x] **2.4 Product & Empty-Space Detector (`detector.py`)**
  - Multi-class YOLO inference (Class 0: empty space, Class 1: product).
- [x] **2.5 Shelf-Row Segmenter (`row_segmenter.py`)**
  - YOLO-seg inference, mask resizing, polygon extraction, and top-to-bottom sorting.
- [x] **2.6 Empty-Space Refinement & Row Assignment (`empty_space.py`)**
  - Updated vertical filtering: incorporates both shelf rows and products to prevent false pruning of empty gaps between products.
- [x] **2.7 Unified Visualizer (`visualization.py`)**
  - Multi-layered composite: Base -> Amber rows -> Royal Blue empty spaces -> Cyan products -> Telemetry banner.
- [x] **2.8 Pipeline Orchestrator (`pipeline.py`)**
  - Multi-stage pipeline with batch error recovery.
- [x] **2.9 CLI (`cli.py`) & Batch Script (`scripts/run_batch.py`)**
  - Added independent `--row-confidence` control.

---

### Phase 3: Comprehensive Test Suite (`tests/`)
- [x] **3.1 Unit Tests: Geometry (`tests/unit/test_geometry.py`)** (10 tests)
- [x] **3.2 Unit Tests: Empty Space (`tests/unit/test_empty_space.py`)** (4 tests)
- [x] **3.3 Unit Tests: Row Assignment (`tests/unit/test_row_assignment.py`)** (4 tests)
- [x] **3.4 Unit Tests: Visualization (`tests/unit/test_visualization.py`)** (4 tests)
- [x] **3.5 Integration Tests (`tests/integration/test_pipeline.py`)** (2 tests)
- [x] **3.6 Test Execution**: All 28 tests passing (`28 passed in 0.31s`).

---

### Phase 4: Model Inference on Initial & Newly Uploaded Images
- [x] **4.1 Re-run Inference on `test_987.jpg`**: 173 products, 6 empty spaces, 5 shelf rows (11.11% empty).
- [x] **4.2 Re-run Inference on `test_999 (1).jpg`**: 147 products, 1 empty space, 7 shelf rows (0.64% empty).
- [x] **4.3 Re-run Inference on `test_image.jpg`**: 90 products, 4 empty spaces, 1 shelf row (5.43% empty).
- [x] **4.4 Run Inference on 5 Newly Uploaded Images**:
  - `new_01_pharmacy_pegboard.jpg`: 102 products, 2 empty spaces, 3 rows.
  - `new_02_coffee_pods.jpg`: 155 products, 2 empty spaces, 8 rows.
  - `new_03_dove_bodywash.jpg`: 127 products, 2 empty spaces, 9 rows.
  - `new_04_packaged_hygiene.jpg`: 187 products, 3 empty spaces, 12 rows.
  - `new_05_medicines_aisle.jpg`: 155 products, 3 empty spaces, 8 rows.
- [x] **4.5 Aggregated CSV Summary**: Generated `outputs/shelf_summary.csv` across all 8 images.
- [x] **4.6 Verification & Integrity Check**: 100% resolution preserved across all outputs.

---

### Phase 5: Documentation & Visual Verification
- [x] **5.1 Comprehensive Documentation (`image-parsing/README.md`)**
- [x] **5.2 Model Setup & Attribution Guide (`image-parsing/MODEL_SETUP.md`)**
- [x] **5.3 Visual Verification Report**: Formatted in `image_parsing_completion_report.md`.

### Phase E — Evidence-complete operator report (implemented)
- [x] Export a versioned JSON manifest linking the report to its original input image, annotated image, raw detection JSON, and frozen planogram snapshot.
- [x] Index product, empty-space, and shelf crop assets with category, crop path, source-image bounding box, confidence, crop-quality flags, and mapped planogram position.
- [x] Show audit completion/review state and expected-versus-observed facing counts in the report UI.
- [x] When a finding is selected, overlay its product and empty-space crop detections on the annotated shelf image and show downloadable crop evidence.
- [x] Add backend and frontend regressions for export provenance, low-stock quantity evidence, selected crop overlays, and direct evidence downloads.
- [ ] Validate the exported evidence package and issue-to-crop links against manually reviewed physical shelf photos; keep geometry, recognition, OCR, and stock thresholds provisional until then.

**Phase E boundary:** The export is an evidence index, not a self-contained archive: paths resolve through the local application's existing artifact/download endpoints. It does not change detection, matching, comparison, or alert policy. `needs_review` remains a visible audit status rather than being presented as a passing shelf.

### Phase F — Verification and handoff (implemented)
- [x] Verify nested duplicate suppression and neighboring product preservation; verify fragmented same-row clusters can consolidate without absorbing dissenting or cross-row products.
- [x] Verify ambiguous CLIP candidates remain `needs_review`, including top and runner-up scores above threshold but within the ambiguity margin.
- [x] Verify misplaced products, 14/15 no-alert stock, 7/15 low-stock alert, isolated empty-space evidence, and uncalibrated review-only behavior.
- [x] Verify same-row/same-SKU count variation of up to two either below or above expected quantity is tolerated; retain slot-level evidence and flag larger overages. Bump compliance audit version to 6.
- [x] Add a backend integration regression that uploads the SHA-pinned labeled shelf photo, selects a planogram built from the manifest, processes the queued job, and checks the snapshot-bound compliance report against deterministic operator-reviewed detections.
- [x] Add a Chromium Playwright regression for the saved labeled shelf output, selected planogram snapshot, normalized four-row report, and audit status.
- [x] Run backend tests, image-parser tests, frontend tests, TypeScript check, production build, targeted Playwright, and `git diff --check`; record exact commands/outcomes in the Dhruv journal and contribution ledger.
- [ ] Run actual model inference and manually compare every crop, row/position, and issue against pixel-level labels; the fixture is scenario-labeled only, so this remains the next validation task.

**Phase F boundary:** The upload-to-report integration uses a deterministic test detector/audit adapter after selecting the real fixture-derived planogram; it proves the queue, frozen snapshot, report, and policy contract, but is not a live YOLO/CLIP accuracy benchmark. The ±2 same-SKU count tolerance is a provisional rule from the operator-reviewed fixture, not a generally calibrated retail policy.

### Product Box Confidence Gate — 2026-10-22 (implemented)
- [x] Add a product-only confidence cutoff of 60%; detections at exactly 60% are retained and detections below 60% are excluded from product crops, embeddings, clusters, and product counts.
- [x] Keep the shared YOLO proposal threshold unchanged so empty-space and shelf-row detection remain independent of the product cutoff.
- [x] Preserve excluded product boxes as diagnostics-only uncertainty geometry; overlapping expected facings become review/uncertain instead of being declared empty or missing solely because a low-confidence product box was filtered.
- [x] Apply the same filter when reprocessing saved outputs and expose effective threshold and excluded count in analysis/report responses.
- [x] Cover threshold boundaries and independent empty-space proposals; run backend, parser, frontend, build, and Playwright checks.
- [ ] Calibrate the 60% cutoff against manually labeled product boxes and review excluded geometry on additional shelf photos.

**Confidence-gate boundary:** 60% is the requested initial operating cutoff, not a universally calibrated detector threshold. Empty-space proposal handling is deliberately unaffected. Excluded boxes are never counted as products or used as identity evidence.
