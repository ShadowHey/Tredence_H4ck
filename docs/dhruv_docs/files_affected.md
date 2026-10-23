# Dhruv's Files & Folders Affected Log (Blast Radius)

### [2026-10-23 05:27 IST] Designer Loopback Loading Fix

#### Files modified
- `frontend/next.config.ts`: Allows the local `127.0.0.1` development origin so Next HMR can establish and client pages hydrate when using the loopback-IP URL.

#### Runtime / verification impact
- Restarted the frontend development server on port 3000. The backend remains on port 8000 and required no source or data change.

### [2026-10-23 03:43 IST] Per-Image Compliance Score

#### Files modified
- `backend/app/services/compliance_service.py`: Adds formula v1, score/evidence/reliability calculation, and advances audit version to 11.
- `backend/app/api/schemas/image_processing.py`: Exposes the typed compliance-score audit contract.
- `backend/app/services/compliance_reporting_service.py`: Includes each persisted score in dashboard audit history.
- `frontend/src/types/index.ts`: Adds score/dashboard TypeScript models.
- `frontend/src/components/analysis/ComplianceReportPanel.tsx`: Renders the selected image’s score, reliability, evidence coverage, and score-supporting summary cards.
- `frontend/src/app/page.tsx`: Renders compact score/state pills in recent audit history.
- `backend/tests/unit/test_compliance_service.py`, `backend/tests/integration/test_image_processing_api.py`, `frontend/tests/compliance-report.test.tsx`: Cover score calculation, provisional/not-scored safety states, API schema output, and score UI rendering.

#### No schema migration
- Score data is persisted inside the existing versioned `processed_outputs.compliance_audit` JSON; audit-version invalidation rebuilds old audits on access.

### [2026-10-23 00:33 IST] Backend Restart and Output #13 Re-analysis

#### Files created/modified
- No source code changed. Updated this session's journal and `docs/shared/CONTRIBUTIONS.md` only.

#### Runtime artifacts / impact
- Recomputed Output #13 from saved detections. Runtime files are under `backend/uploads/image_processing/outputs/14/`, including the refreshed annotated image and price-tag crops/JSON.
- Backend: `http://localhost:8000`; frontend analysis page: `http://localhost:3000/analysis?outputId=13`.

### [2026-10-23 00:25 IST] Roboflow Price Tags and EasyOCR Runtime Verification

#### Files created/modified
- `backend/requirements-roboflow.txt`, `backend/requirements-ocr.txt`: Pin optional Roboflow SDK and EasyOCR requirements for backend setup.
- `backend/PRICE_TAG_DETECTION_SETUP.md`: Document environment configuration and feature setup.
- `backend/app/core/config.py`: Read the optional Roboflow key/model configuration server-side.
- `backend/app/services/price_tag_detection_service.py`: Detect tags, save crops, use header-only fallback for SDK versions lacking header transport, and OCR/parse prices.
- `backend/app/services/cutout_service.py`, `backend/app/services/compliance_service.py`: Include price-tag artifacts in pipeline output and version the derived audit.
- `backend/tests/unit/test_price_tag_detection_service.py`: Cover tag geometry/cache, secure old-SDK fallback, price parsing, and ambiguous OCR.
- `frontend/src/components/analysis/ComplianceReportPanel.tsx`: Display label OCR evidence and “Label Fetched Price”.
- `backend/tests/integration/test_image_processing_api.py`, `backend/tests/unit/test_compliance_service.py`: Update audit-version expectations.
- `docs/shared/CONTRIBUTIONS.md` and the Dhruv journal files: Record results and handoff.

#### Runtime artifacts / impact
- No database schema migration. Live inference used an existing shelf input and wrote tag crops/JSON plus `shelf_tag_overlay.jpg` under `backend/uploads/image_processing/outputs/14/roboflow_smoke_sdk_abs/` (generated uploads, not source files).
- EasyOCR model files are cached under the user's `~/.EasyOCR/model`; they are not repository assets and contain no API secrets.

### [2026-10-22 19:57 IST] Operator-Labeled Compliance Rules Update — second shelf photo

#### Files modified
- `docs/dhruv_docs/COMPLIANCE_DECISION_RULES_DRAFT.md`: Adds a second isolated operator-labeled photo case, row-by-row detected/missed gaps, the un-actioned wrong product, candidate acceptance criteria, and a reminder to keep the case separate from the earlier six-empty example.
- `docs/shared/CONTRIBUTIONS.md`: Records this documentation-only update and its verification command.
- `docs/dhruv_docs/README.md`, `technical_decisions.md`, `conversation_history.md`, `files_affected.md`: Adds this timestamped journal entry and cross-links.

#### Runtime/source impact
- No application code, tests, API, database, saved analysis, report, generated output, or running process was changed. Existing unrelated working-tree edits were preserved.

### [2026-10-22 19:43 IST] Operator-Labeled Compliance Rules Draft — `bc_image2.png`

#### Files created
- `docs/dhruv_docs/COMPLIANCE_DECISION_RULES_DRAFT.md`: Captures the operator-labeled expected issues for `bc_image2.png`, distinguishes them from the visible current detector/report output, proposes reviewable future decision logic, lists acceptance criteria and open policy questions, and provides a next-agent checklist. Explicitly marked draft/unimplemented.

#### Files modified
- `docs/shared/CONTRIBUTIONS.md`: Adds this documentation-only work and notes that no tests or pipeline execution were required.
- `docs/dhruv_docs/README.md`: Adds a journal timeline link to the draft.
- `docs/dhruv_docs/technical_decisions.md`: Records the design boundary and observed discrepancy.
- `docs/dhruv_docs/conversation_history.md`: Records the request, operator labels, and no-code scope.

#### Runtime/source impact
- No code, API, database, saved analysis, report, output artifact, or running process was changed.

### [2026-10-22 19:12 IST] Product Detection Confidence Gate (60%)

#### Files modified/added
- `image-parsing/src/shelf_image_parsing/config.py`, `detector.py`, `pipeline.py`, `schemas.py`, `cli.py`, `image-parsing/config/default.yaml`: Add configurable product-only 0.60 threshold; isolate it from empty-space proposal generation; retain excluded boxes as diagnostics; report threshold/count.
- `image-parsing/tests/unit/test_detector_confidence.py` *(new)* and `image-parsing/tests/integration/test_pipeline.py`: Verify below/equal/above cutoff, empty-region independence, validation, and diagnostics.
- `backend/app/services/cutout_service.py`, `compliance_service.py`, `image_processing_service.py`; `backend/app/api/routes/image_processing.py`, `backend/app/api/schemas/image_processing.py`: Filter legacy saved detections, prevent excluded boxes becoming product evidence, map overlaps as uncertainty, and support fresh source-image reprocessing with versioned results.
- `backend/tests/unit/test_compliance_service.py`, `backend/tests/integration/test_image_processing_api.py`: Cover uncertainty behavior and reprocessing API.
- `frontend/src/app/analysis/page.tsx`, `frontend/src/components/analysis/ComplianceReportPanel.tsx`, `frontend/src/lib/api.ts`, `frontend/src/types/index.ts`: Trigger fresh YOLO reprocessing and show accepted/excluded counts and uncertainty note.
- `image-parsing/TASK_CHECKLIST.md`, `docs/shared/COMPLIANCE_ROADMAP.md`, `docs/shared/CONTRIBUTIONS.md`, and Dhruv journal files: Record scope, verification, result, and calibration caveat.

#### Runtime/data effects
- No database migration. Analysis cache and compliance audit versions advanced; Output #8 generated artifacts and derived report were regenerated locally from the saved source photo.
- Output #8: 60 accepted products, 10 below-threshold excluded boxes, 9 mapped uncertainty geometries; two actionable findings remain (misplaced Row 1 Lays; empty Row 2 Lays facing). Review-required audit status reflects uncertainty, not additional discrepancy findings.

### [2026-10-22 16:57 IST] Backend Restart and Saved Analysis Refresh

#### Files modified
- `backend/app/services/product_matching/cluster_consensus.py`: Guard against empty per-row catalogue vote counters; no-vote clusters remain separate.
- `backend/app/services/cutout_service.py`: Propagate forced recompute into compliance audit persistence, so explicit reruns refresh derived warnings.
- `backend/tests/unit/test_cluster_consensus.py`: Add regression for rows containing only unusable/review-needed crop votes.
- `docs/shared/CONTRIBUTIONS.md`, `docs/dhruv_docs/{README.md,technical_decisions.md,conversation_history.md,files_affected.md}`: Record rerun outcomes, tests, and follow-up limits.

#### Runtime effects
- Restarted backend process on port 8000; frontend process was left running.
- Recomputed analysis/audit artifacts for saved Outputs #1–#8 using their existing persisted detections. No original inputs or source uploads were modified.
- All outputs returned HTTP 200 after the edge-case fix. Output #8 audit summary remains 16 correct, 9 tolerated, 24 misplaced, 15 missing, 101 review-needed, 60 label issues; warnings did not materially reduce.

#### Verification
- `backend/.venv/bin/pytest backend/tests -q` — 82 passed.
- Live `POST /api/v1/outputs/{1..8}/analyze` — HTTP 200 each; `GET /api/v1/outputs/8/compliance` — audit version 6.

### [2026-10-22 06:19 IST] Normalized Row/Position Layout Comparison

#### Files created
- `backend/app/services/spatial_matching/__init__.py`: Package facade for layout comparison.
- `backend/app/services/spatial_matching/planogram_layout.py`: Normalizes expected facing slots by shelf width and assigns row ordinals.
- `backend/app/services/spatial_matching/image_layout.py`: Normalizes calibrated product and empty-space evidence per photo row.
- `backend/app/services/spatial_matching/sequence_alignment.py`: Monotonically aligns expected/observed row sequences with explicit missing/extra gaps and computes uncovered intervals.
- `backend/app/services/spatial_matching/layout_comparison.py`: Combines normalized planogram and image row evidence into the audit payload.
- `backend/tests/unit/test_spatial_layout_comparison.py`: Validates normalized coordinates, ordinals, intervals, and review-only calibration behavior.

#### Files modified
- `backend/app/services/compliance_service.py`: Adds normalized assignment/slot fields, embeds layout comparison, and bumps audit version to 4.
- `backend/app/api/schemas/image_processing.py`: Adds typed response slot for layout-comparison data.
- `backend/tests/unit/test_compliance_service.py`, `backend/tests/integration/test_image_processing_api.py`: Verify audit v4 and layout fields.
- `frontend/src/components/analysis/ComplianceReportPanel.tsx`, `frontend/src/types/index.ts`: Show normalized row summary and ordinal position.
- `frontend/tests/compliance-report.test.tsx`: Covers layout summary rendering.
- `docs/shared/CONTRIBUTIONS.md` and the Dhruv journal files: Record implementation and test commands.

#### Database changes
- None. Existing persisted compliance audit JSON is rebuilt through the audit-version check.

### [2026-10-22 04:48 IST] Color-First Catalogue Candidate Gate

#### Files created
- `backend/app/services/product_matching/candidate_filtering.py`: Hard color compatibility gate, candidate counts, and safe fallback selection.
- `backend/tests/unit/test_product_matching.py`: Color gate rejection/retention, no-pass fallback, missing-packshot fallback, and color-similarity tests.

#### Files modified
- `backend/app/services/product_matching/color_handling.py`, `backend/app/services/product_matching/__init__.py`: Expose color evidence and make filtering the package entry point.
- `backend/app/services/cutout_service.py`: Filter candidates by color before computing candidate CLIP similarities, select maximum CLIP survivor, preserve existing confidence safeguards, and bump analysis cache to version 6.
- `backend/app/api/schemas/image_processing.py`: Expose color score, filter threshold, before/after candidate counts, fallback/reason, and method.
- `frontend/src/types/index.ts`, `frontend/src/components/analysis/ProductMatchView.tsx`, `frontend/tests/analysis-and-cutouts.test.tsx`: Type and display the color gate evidence and test the UI.
- `backend/tests/unit/test_cutout_service.py`, `e2e/tests/analysis_product_match.spec.ts`: Integration-level regression for a color-filtered CLIP misranking/review-only fallback; update Playwright to assert the raw CLIP label.
- `docs/shared/CONTRIBUTIONS.md` and all four Dhruv journal files: Decision, handoff, file map, and checks.

#### Files deleted
- `backend/app/services/product_matching/candidate_fusion.py`: Removed soft score blending that could let CLIP override color incompatibility.
- `backend/app/services/product_matching/package_shape.py`: Removed package shape from ranking because the requested second stage is CLIP-only.

### [2026-10-22 04:36 IST] Explainable Product Appearance Reranking

#### Files created
- `backend/app/services/product_matching/__init__.py`: Public package entry point for candidate reranking.
- `backend/app/services/product_matching/crop_preprocessing.py`: EXIF-safe normalization and packshot foreground aspect estimation.
- `backend/app/services/product_matching/color_handling.py`: Saturation-weighted HSV hue histogram intersection.
- `backend/app/services/product_matching/package_shape.py`: Coarse aspect-ratio similarity.
- `backend/app/services/product_matching/candidate_fusion.py`: CLIP-primary fusion and candidate ordering with component scores.
- `backend/tests/unit/test_product_matching.py`: Tests color-based reranking for a close CLIP error, bounded scores, shape consistency, and missing-packshot fallback.

#### Files modified
- `backend/app/services/cutout_service.py`: Apply reranking per crop against the immutable shelf catalogue; preserve CLIP score/threshold semantics; bump analysis cache version.
- `backend/app/api/schemas/image_processing.py`: Add optional rerank/color/shape scores and appearance-availability field.
- `frontend/src/types/index.ts`, `frontend/src/components/analysis/ProductMatchView.tsx`, `frontend/tests/analysis-and-cutouts.test.tsx`: Type and display the scores, distinguish CLIP-only from CLIP-plus-appearance ranking, and assert the explainable score labels.
- `docs/shared/CONTRIBUTIONS.md` and the four Dhruv journal files: Record decisions, limitations, file map, and verification.

#### Not changed
- No database/schema migration or new dependency. Existing `embedding_service.py` remains the CLIP implementation, and no global-catalogue matching fallback was introduced.

### [2026-10-22 04:22 IST] Individual Product Match View

#### Files created
- `frontend/src/components/analysis/ProductMatchView.tsx`: Individual crop-to-top-catalogue-candidate cards, confidence/status, and review explanations.
- `e2e/tests/analysis_product_match.spec.ts`: Playwright coverage for Product Match and return to cluster mode.

#### Files modified
- `frontend/src/components/analysis/AnalysisTable.tsx`: Fourth tab/count, stable individual cutout ordering, search handoff, and mode switching; existing cluster filters preserved.
- `frontend/tests/analysis-and-cutouts.test.tsx`: Candidate, confidence, review/no-candidate, SKU search, and tab-return tests.
- `docs/shared/CONTRIBUTIONS.md` and all four Dhruv journal files: Session record and test instructions.

#### Backend / API
- No backend/API/schema changes. Existing `similar_objects[].catalog_match` already carries each crop's top candidate, runner-up, score, confidence threshold, and resolution status.

### [2026-10-22 03:22 IST] Analysis Matching Calibration for Pipeline Verification Shelf

#### Files modified
- `backend/app/services/cutout_service.py`: Calibrated threshold to 0.90, changed below-threshold classification to review-needed, and bumped analysis cache version.
- `backend/app/services/compliance_service.py`: Bumped persisted audit version to invalidate findings from obsolete match rules.
- `backend/tests/unit/test_cutout_service.py`, `backend/tests/unit/test_cutouts_and_analysis.py`, `backend/tests/unit/test_compliance_service.py`, `backend/tests/integration/test_image_processing_api.py`: Covered 90% matching, low-score review state, and revised schema versions.
- `frontend/src/app/analysis/page.tsx`, `frontend/src/components/analysis/AnalysisTable.tsx`, `frontend/tests/analysis-and-cutouts.test.tsx`: Display active API threshold, clarify cohesion vs catalogue score, and update tests/labels.
- `docs/shared/CONTRIBUTIONS.md` and this four-file Dhruv journal entry: Record evidence, behavior, verification, and limitations.

#### Database / runtime data
- No schema changes. Recomputed the existing local Output #7 analysis/audit once to verify regenerated matching and report.

### [2026-10-22 02:11 IST] Phase 5 — Shelf-Label OCR

#### Files created
- `backend/app/services/label_ocr_service.py`: Lazy EasyOCR CPU adapter, calibrated/provisional label-region projection, OCR price/currency parsing, expected-product association, crop evidence, and conservative findings.
- `backend/requirements-ocr.txt`: Optional isolated EasyOCR dependency.
- `backend/OCR_SETUP.md`: Local installation, first-run model/cache, fail-closed behavior, and test instructions.
- `backend/tests/unit/test_label_ocr_service.py`: Geometry, OCR parsing/association, evidence, low-confidence, missing-engine, and review tests.

#### Files modified
- `backend/app/services/cutout_service.py`: Runs label OCR from the saved source/cutout calibration and persists results with the compliance audit.
- `backend/app/services/compliance_service.py`: Merges provisional label findings and bumps audit schema generation version.
- `backend/app/api/schemas/image_processing.py`: Exposes optional corner anchors and label audit contract.
- `backend/app/services/image_processing_service.py`: Adds label crop evidence images to output ZIPs.
- `backend/tests/unit/test_compliance_service.py`, `backend/tests/integration/test_image_processing_api.py`: Updated version and endpoint regression assertions.
- `docs/shared/{COMPLIANCE_ROADMAP.md,API_CONTRACT.md,ARCHITECTURE.md,CONTRIBUTIONS.md}` and all four Dhruv journal files: Phase 5 checklist, constraints, setup, and handoff notes.

#### Runtime behavior
- EasyOCR is imported and initialized on demand. Missing dependency/model weights, uncalibrated label geometry, or inference errors produce `needs_review`; no external OCR service is called.
- Each report contains crop paths relative to `uploads/`; output ZIP includes these label images beside the report.
- OCR findings remain `provisional` pending a labelled physical photo evaluation set.

### [2026-10-22 02:02 IST] Phase 4 — Planogram Compliance Engine

#### Files created
- `backend/app/services/compliance_service.py`: Deterministic slot assignment, audit findings, empty-region evidence, and needs-review policy.
- `backend/tests/unit/test_compliance_service.py`: Tests correct/misplaced/missing/insufficient/unexpected/unrecognised/review outcomes and audit linkage.

#### Files modified
- `backend/app/db/models.py`, `backend/app/db/database.py`: Persist audit JSON on outputs and migrate existing SQLite databases idempotently.
- `backend/app/services/cutout_service.py`: Create/refresh audit with cutout analysis and expose stored audit retrieval.
- `backend/app/services/image_processing_service.py`: Include audit in output API and ZIP manifest/archive.
- `backend/app/api/routes/image_processing.py`, `backend/app/api/schemas/image_processing.py`: Add the compliance endpoint and typed response contract.
- `backend/tests/integration/test_image_processing_api.py`: Verify report linkage, endpoint response, and export artifact.
- `docs/shared/COMPLIANCE_ROADMAP.md`, `API_CONTRACT.md`, `ARCHITECTURE.md`, `CONTRIBUTIONS.md`, and this Dhruv journal: Track completion and API/decision handoff.

#### Database changes
- `processed_outputs.compliance_audit` (`JSON`, nullable); legacy outputs without an audit receive one when the compliance endpoint is requested or current analysis is regenerated.

---

### [2026-10-22 01:42 IST] Phase 1 — Immutable Planogram Audit Snapshot
- **Commit**: Working tree (not committed)
- **Author**: Dhruv
- **Branch**: `feature/dhruv`

#### Files Created
| File Path | Description / Role |
| :--- | :--- |
| `docs/shared/COMPLIANCE_ROADMAP.md` | Handoff checklist for compliance phases and controlled shelf-photo fixtures. |

#### Files Modified
| File Path | Changes Made |
| :--- | :--- |
| `backend/app/db/models.py` | Added nullable JSON `audit_snapshot` to processing jobs. |
| `backend/app/db/database.py` | Added SQLite migration; migration failures are no longer silently swallowed. |
| `backend/app/api/schemas/image_processing.py` | Added snapshots to input-image and processed-output response models. |
| `backend/app/services/image_processing_service.py` | Captures, returns, and exports immutable ground-truth snapshots. |
| `frontend/src/types/index.ts` | Added TypeScript contracts for job snapshots. |
| `docs/shared/API_CONTRACT.md` | Documented snapshot response and archive behavior. |
| `docs/shared/ARCHITECTURE.md` | Documented job-scoped ground-truth storage. |
| `docs/shared/CONTRIBUTIONS.md` | Added implementation summary and handoff commands. |
| `docs/dhruv_docs/README.md` | Added session to the journal timeline. |
| `docs/dhruv_docs/technical_decisions.md` | Recorded snapshot choice and boundaries. |
| `docs/dhruv_docs/conversation_history.md` | Recorded request and implementation outcome. |
| `docs/dhruv_docs/files_affected.md` | Added this blast-radius map. |

#### Database Changes
- `processing_jobs.audit_snapshot` (`JSON`, nullable); existing jobs remain `NULL` and are treated as legacy records.

### [2026-10-21 22:45 IST] YOLO Cutout Extraction, Semantic Clustering & 4-Column Analysis Table
- **Commit**: [`8a0b94e`](https://github.com/ShadowHey/Tredence_H4ck/commit/8a0b94e)
- **Author**: Dhruv
- **Branch**: `feature/dhruv`

#### Files Created
| File Path | Description / Role |
| :--- | :--- |
| `backend/app/services/cutout_service.py` | Core engine for bounding box cutout extraction, fast batch CLIP embeddings, intra-shelf clustering ($\tau = 0.88$), and strict catalog matching ($\ge 95\%$). |
| `backend/tests/unit/test_cutouts_and_analysis.py` | 5 unit tests for cutout disk saving, batch CLIP speed, clustering, and >= 95% threshold verification. |
| `frontend/src/components/outputs/CutoutViewerModal.tsx` | Cutout inspector dialog with 3 tabs (`Products`, `Shelves / Rows`, `Empty Spaces`), confidence badges, and zoom sub-modal. |
| `frontend/src/components/analysis/AnalysisTable.tsx` | Strict 4-column analysis table: Similar Objects, Similarity Percentage, Is object similar to someone in the product catalog (Yes/No), and Similar Product. |
| `frontend/src/app/analysis/page.tsx` | Top-level `/analysis` route with Suspense wrapper, active shelf card, metric badges, output switcher, and crop inspector. |
| `frontend/tests/analysis-and-cutouts.test.tsx` | 6 frontend unit tests validating modal tabs and 4-column table rendering behavior. |

#### Files Modified
| File Path | Changes Made |
| :--- | :--- |
| `backend/app/services/embedding_service.py` | Added `compute_image_embeddings_batch(images, batch_size=32)` for accelerated vector calculation (~15.6ms/crop). |
| `backend/app/services/image_processing_service.py` | Integrated `extract_cutouts_and_analyze()` automatically on image inference job completion. |
| `backend/app/api/schemas/image_processing.py` | Added Pydantic schemas: `CutoutItem`, `CutoutsResponse`, `CatalogMatchedProduct`, `ClusterRow`, `OutputAnalysisResponse`. |
| `backend/app/api/routes/image_processing.py` | Registered `GET /outputs/{id}/cutouts`, `GET /outputs/{id}/analysis`, and `POST /outputs/{id}/analyze`. |
| `frontend/src/types/index.ts` | Added TypeScript interfaces matching backend analysis schemas. |
| `frontend/src/lib/api.ts` | Added `getOutputCutouts`, `getOutputAnalysis`, and `analyzeOutput` API client methods. |
| `frontend/src/components/shell/Sidebar.tsx` | Added `/analysis` top-level navigation item with `ScanSearch` icon. |
| `frontend/src/app/outputs/page.tsx` | Integrated `CutoutViewerModal` triggered on image card click or Inspect button; linked to `/analysis`. |

#### How to test
```bash
backend/.venv/bin/pytest backend/tests/ -v
npm test --prefix frontend
npm run build --prefix frontend
```

---

### [2026-10-21 15:05 IST] Image Intake, Shelf Assignment & Annotated Outputs
- **Commit**: [`30474fc`](https://github.com/ShadowHey/Tredence_H4ck/commit/30474fc)
- **Status**: Implemented and verified.
- **Created**: `backend/app/api/routes/image_processing.py`, `backend/app/api/schemas/image_processing.py`, `backend/app/services/image_processing_service.py`, `backend/tests/integration/test_image_processing_api.py`, `frontend/src/app/input-images/page.tsx`, `frontend/src/app/outputs/page.tsx`, `frontend/tests/image-processing-page.test.tsx`, and `e2e/tests/image_processing_journey.spec.ts`.
- **Modified**: database models/configuration, FastAPI startup/router registration, upload storage, sidebar navigation, frontend API client, and shared TypeScript types.
- **Schema impact**: Adds `input_images`, `processing_jobs`, and `processed_outputs` SQLite tables.
- **How to test**:
  ```bash
  backend/.venv/bin/pytest backend/tests -v
  cd frontend && npx tsc --noEmit && npm test && npm run build
  ```

### [2026-10-21 07:00 IST] Unified Root Logging & Real-Time Job Streamer
- **Commit**: [`19710ad`](https://github.com/ShadowHey/Tredence_H4ck/commit/19710ad)
- **Author**: Dhruv
- **Branch**: `feature/dhruv`

#### Files Created
| File Path | Description / Role |
| :--- | :--- |
| `logs/logs.txt` | Master log sink file aggregating Frontend UI, Backend API, and Worker telemetry. |
| `logs/log_collector.py` | Standalone CLI log streamer with ANSI colors, line-following, and summary metrics. |
| `logs/.gitignore` | Ignores temporary and rotated files while keeping `logs.txt` tracked. |
| `backend/app/core/logging_config.py` | Thread-safe logging handler with immediate line flush and job tracking helpers. |
| `backend/app/api/routes/logs.py` | FastAPI route `POST /api/v1/logs/event` to ingest client-side action events. |
| `frontend/src/lib/logger.ts` | Non-blocking, fire-and-forget `logFrontendAction()` utility (`keepalive: true`). |

#### Files Modified
| File Path | Changes Made |
| :--- | :--- |
| `backend/app/main.py` | Mounted `setup_unified_logging()` in lifespan; added HTTP request logging middleware with latency tracking; mounted `logs.router`. |
| `backend/app/services/product_service.py` | Wrapped CLIP embedding execution in `log_job_start()`, `log_job_done()`, and `log_job_error()` with duration in ms. |
| `frontend/src/components/designer/AddShelfModal.tsx` | Dispatches `ACTION:SHELF_ADD` upon successful shelf unit creation. |
| `frontend/src/components/designer/AddProductModal.tsx` | Dispatches `ACTION:PRODUCT_ADD` upon successful product creation. |

#### Database & Dependency Changes
- None (pure logging & telemetry infrastructure).

---

### [2026-10-21 06:18 IST] CLIP ViT-B/32 Vector Embeddings for Product Catalog
- **Commit**: [`38b2583`](https://github.com/ShadowHey/Tredence_H4ck/commit/38b2583)
- **Author**: Dhruv
- **Branch**: `feature/dhruv`

#### Files Created
| File Path | Description / Role |
| :--- | :--- |
| `backend/app/services/embedding_service.py` | Singleton CLIP service (`ViT-B-32-quickgelu`), image path resolver, L2 unit normalizer. |
| `backend/scripts/inspect_embeddings.py` | Direct SQLite inspection CLI tool (`--list`, `--compare`, `--test-copy`, `--backfill`). |
| `backend/tests/unit/test_embeddings.py` | 5 unit tests covering dimensionality (512), L2 normalization, duplicate copy identity, and separation. |

#### Files Modified
| File Path | Changes Made |
| :--- | :--- |
| `backend/app/db/models.py` | Added `embedding = Column(JSON, nullable=True)` to `Product` SQLAlchemy model. |
| `backend/app/db/database.py` | Updated `init_db()` with dynamic `PRAGMA table_info(products)` check and `ALTER TABLE products ADD COLUMN embedding JSON;`. |
| `backend/app/api/schemas/product.py` | Added `embedding: Optional[List[float]] = None` to `ProductResponse` Pydantic model. |
| `backend/app/services/product_service.py` | Automatically computes and attaches embedding vector on `create_product()` and image update. |
| `backend/requirements.txt` | Added `torch>=2.0.0`, `torchvision>=0.23.0`, and `open-clip-torch>=3.3.0`. |

#### Database Changes
- **Table**: `products`
  - **New Column**: `embedding` (Type: `JSON`, Nullable: `True`, Content: 512-dim float list).

#### External Dependencies Added
- `torch 2.8.0`
- `torchvision 0.23.0`
- `open-clip-torch 3.3.0`
- Pretrained weights: `models--timm--vit_base_patch32_clip_224.openai` cached locally in `~/.cache/huggingface/`.

---

### [2026-10-22 00:54 IST] Individual Cutout Downloads & Fetch Failure Fix
- **Commit**: [`947e73a`](https://github.com/ShadowHey/Tredence_H4ck/commit/947e73a)
- **Author**: Dhruv
- **Branch**: `feature/dhruv`

#### Files Created
| File Path | Description / Role |
| :--- | :--- |
| `e2e/tests/cutout_download.spec.ts` | Chromium regression test for downloading an individual rendered cutout. |

#### Files Modified
| File Path | Changes Made |
| :--- | :--- |
| `backend/app/api/routes/image_processing.py` | Added the single-cutout JPEG attachment route. |
| `backend/app/services/cutout_service.py` | Added safe persisted-cutout path resolution and archive creation support. |
| `frontend/src/components/outputs/CutoutViewerModal.tsx` | Added native individual download links to cards and crop details. |
| `frontend/tests/analysis-and-cutouts.test.tsx` | Added a test for the individual download control and API base URL mock. |

#### Database Changes
- None.
### [2026-10-22 01:48 IST] Phase 2 — Shelf-Scoped Individual Cutout Matching

#### Files modified
- `backend/app/services/cutout_service.py`: Replaced global Product-table matching with individual per-crop matching against frozen shelf catalogue; introduced provisional thresholds and snapshot/version-aware cache invalidation.
- `backend/app/api/schemas/image_processing.py`: Added typed candidate, match-status, margin, and analysis metadata response fields.
- `frontend/src/types/index.ts`: Typed per-cutout match payload and version/scope metadata.
- `frontend/src/components/outputs/CutoutViewerModal.tsx`: Shows match/review state and ranked candidates for each product crop.
- `docs/shared/COMPLIANCE_ROADMAP.md`: Ticked implementation tasks; calibration remains open.
- `docs/shared/CONTRIBUTIONS.md`, `docs/dhruv_docs/{README.md,technical_decisions.md,conversation_history.md,files_affected.md}`: Persistent work log.

#### Database changes
- None. Match records are persisted in the existing per-job `cutouts.json` artifact and served through the existing cutouts endpoint.
### [2026-10-22 01:56 IST] Phase 3 — Photo-to-Planogram Position Mapping

#### Files created
- `backend/app/services/position_calibration.py`: Pure geometry service for linear row mapping, quadrilateral validation, projective homography, row resolution, and per-cutout physical coordinates.
- `backend/tests/unit/test_position_calibration.py`: Tests straight-on row mapping, projective rectification, invalid-corner fallback, unavailable calibration, and row-count mismatch.
- `image-parsing/src/shelf_image_parsing/calibration.py`: Optional ArUco marker detector.
- `image-parsing/tests/unit/test_calibration.py`: Synthetic four-marker, missing-marker, and duplicate-marker tests.

#### Files modified
- `backend/app/services/cutout_service.py`: Applies mapping to product and empty-space crop records; bumps analysis cache version and persists calibration summaries.
- `backend/app/api/schemas/image_processing.py`, `frontend/src/types/index.ts`: Position and calibration response contracts.
- `image-parsing/src/shelf_image_parsing/{pipeline.py,schemas.py}`: Emit optional marker-derived corner coordinates in parser output.
- `image-parsing/requirements.txt`: Use OpenCV contrib headless package for ArUco support.
- `frontend/src/{app/analysis/page.tsx,components/outputs/CutoutViewerModal.tsx}`: Show calibration status and mapped row/centimetre spans.
- `docs/shared/{API_CONTRACT.md,ARCHITECTURE.md,COMPLIANCE_ROADMAP.md,CONTRIBUTIONS.md}`, `image-parsing/tests/fixtures/README.md`, and this Dhruv journal.

#### Database changes
- None. Position results are stored with existing per-job `cutouts.json` and `analysis.json` artifacts.
### [2026-10-22 02:25 IST] Phase 6 — Compliance Reporting & Operator Workflow

#### Files created
- `backend/app/services/compliance_reporting_service.py`: Stable finding IDs, actions, resolution persistence, dashboard summary/history, JSON export.
- `frontend/src/components/analysis/ComplianceReportPanel.tsx`: Finding report, filters, evidence overlays, note/status controls, export.
- `frontend/tests/compliance-report.test.tsx`: Report/filter/evidence/disposition UI regression test.

#### Files modified
- `backend/app/db/models.py`: Added output-cascading `ComplianceIssueResolution` table with unique output/finding identity and valid-state constraints.
- `backend/app/api/routes/image_processing.py`, `backend/app/api/schemas/image_processing.py`: Summary, report, resolution and JSON-export endpoints/contracts.
- `backend/tests/integration/test_image_processing_api.py`: Report enrichment, durable resolution, export and invalid-ID coverage.
- `frontend/src/app/analysis/page.tsx`, `frontend/src/app/page.tsx`: Integrated report and dashboard summary/history.
- `frontend/src/lib/api.ts`, `frontend/src/types/index.ts`: Typed client operations and response contracts.
- `docs/shared/{COMPLIANCE_ROADMAP.md,API_CONTRACT.md,ARCHITECTURE.md,CONTRIBUTIONS.md}` and all four files in `docs/dhruv_docs/`.

#### Database changes
- New `compliance_issue_resolutions` SQLite table; created with SQLAlchemy metadata initialization; keyed by output/finding and cascade deleted with the output.

### [2026-10-22 02:43 IST] Null Calibration Position Analysis Failure

#### Files modified
- `backend/app/services/cutout_service.py`: Added a null-safe calibrated-position counter and used it for both analysis response and output metric calculations.
- `backend/tests/unit/test_cutout_service.py` *(New)*: Regression test for missing, null, needs-review, and calibrated position records.
- `docs/shared/CONTRIBUTIONS.md` and all four Dhruv journal files: Recorded root cause, fix, and live verification.

#### Database changes
- None.
# [2026-10-22 14:18 IST] Shelf Fixture Ground Truth & Detection Quality Safeguards — Phases A–B

#### Files created
- `image-parsing/tests/fixtures/compliance/pipeline-verification/shelf_photo.png`: Copy of the original Output #7 input, pinned by hash in its manifest.
- `image-parsing/tests/fixtures/compliance/pipeline-verification/manifest.json`: Frozen planogram mapping and operator-reviewed scenario outcomes/provenance.
- `image-parsing/tests/fixtures/compliance/pipeline-verification/README.md`: Fixture scope and explicit non-benchmark limitations.
- `image-parsing/src/shelf_image_parsing/detection_refinement.py`: Nested duplicate suppression and row-relative geometry warnings.
- `image-parsing/tests/unit/test_detection_refinement.py`, `test_compliance_fixture.py`: Logic and fixture integrity/policy tests.

#### Files modified
- `image-parsing/src/shelf_image_parsing/{detector.py,pipeline.py,schemas.py}`: Conservative duplicate cleanup and output quality flags.
- `image-parsing/tests/fixtures/README.md`, `image-parsing/README.md`, `image-parsing/TASK_CHECKLIST.md`: Fixture/module documentation and completed A/B checklist.
- `backend/app/services/cutout_service.py`: Propagates detection quality metadata; cache version 7.
- `backend/app/api/schemas/image_processing.py`, `frontend/src/types/index.ts`: Typed quality fields.
- `frontend/src/components/analysis/ProductMatchView.tsx`, `frontend/tests/analysis-and-cutouts.test.tsx`: Display/test a separate geometry warning for flagged crops without changing the product-identity state.
- `docs/shared/COMPLIANCE_ROADMAP.md`, `docs/shared/CONTRIBUTIONS.md`, all four `docs/dhruv_docs/` files: Handoff and contribution record.

#### Database changes
- None.
# [2026-10-22 14:54 IST] Row-Scoped Catalogue Consensus & Cluster Identity — Phase C

#### Files created
- `backend/app/services/product_matching/cluster_consensus.py`: Conservative, row-scoped same-candidate cluster merge and consensus evaluation; geometry-review crops abstain.
- `backend/tests/unit/test_cluster_consensus.py`: Regression tests for majority consolidation, dissenting products, cross-row isolation/splitting, low-quality abstention, and singleton review.

#### Files modified
- `backend/app/services/cutout_service.py`: Runs crop-specific catalogue matching before consensus consolidation, retains individual results, calculates merged cluster metrics/consensus, and bumps analysis cache version to 8.
- `backend/app/api/schemas/image_processing.py`, `frontend/src/types/index.ts`: Expose typed consensus state and support counts.
- `frontend/src/components/analysis/AnalysisTable.tsx`, `frontend/tests/analysis-and-cutouts.test.tsx`: Display leading catalogue candidate and vote support even when cluster confirmation remains review-needed; test this state.
- `image-parsing/TASK_CHECKLIST.md`, `docs/shared/COMPLIANCE_ROADMAP.md`: Tick Phase C implementation tasks and record calibration boundary.
- `docs/shared/CONTRIBUTIONS.md`, all four `docs/dhruv_docs/` files: Record request, decision, affected files, tests, and the pending validation handoff.

#### Database changes
- None. Existing cached analysis files are invalidated by analysis version 8.
# [2026-10-22 15:27 IST] Placement-Level Stock Alert Policy — Phase D

#### Files modified
- `backend/app/services/compliance_service.py`: Aggregate stock findings by planogram placement/row; keep slot results; gate alerts at <=50% expected units; count recognized same-row misplaced units as stock presence; withhold definitive stock issues when calibration is unavailable; bump audit version to 5.
- `backend/tests/unit/test_compliance_service.py`: Add one-of-15 no-alert, exact half, zero-quantity single finding, row/placement isolation, and update the audit version assertion.
- `backend/tests/integration/test_image_processing_api.py`: Update the versioned audit response assertion.
- `image-parsing/TASK_CHECKLIST.md`, `docs/shared/COMPLIANCE_ROADMAP.md`: Tick Phase D implementation tasks and note remaining empirical validation.
- `docs/shared/CONTRIBUTIONS.md`, all four `docs/dhruv_docs/` files: Record the behavior, verification commands, and handoff.

#### Database changes
- None. Existing computed audits are regenerated using audit version 5.

### [2026-10-22 16:06 IST] Evidence-Complete Compliance Reporting — Phase E

#### Files modified
- `backend/app/services/compliance_reporting_service.py`: Upgrade JSON export to schema v2 and enumerate source, annotated, detector, snapshot, and product/empty-space/shelf crop evidence assets.
- `backend/tests/integration/test_image_processing_api.py`: Assert export schema version and provenance fields.
- `frontend/src/components/analysis/ComplianceReportPanel.tsx`: Show audit status and stock quantities; display and overlay selected product/empty-space crops with direct downloads.
- `frontend/src/types/index.ts`: Type quantity and positional evidence fields.
- `frontend/tests/compliance-report.test.tsx`: Verify audit status, quantity display, both crop overlays, and download links.
- `image-parsing/TASK_CHECKLIST.md`, `docs/shared/COMPLIANCE_ROADMAP.md`: Add Phase E deliverables and retain real-photo validation as open.
- `docs/shared/CONTRIBUTIONS.md`, `docs/dhruv_docs/{README.md,technical_decisions.md,conversation_history.md,files_affected.md}`: Record decision, request, scope, tests, and handoff.

#### Database changes
- None. Existing cutout download route and artifact storage are reused; no migration or new persistence model.

### [2026-10-22 16:41 IST] Compliance Verification and Handoff — Phase F

#### Files modified
- `backend/app/services/compliance_service.py`: Add named ±2 same-row/same-SKU count-variation tolerance for overage detections; preserve individual slot statuses; add a separate tolerated assignment state; bump compliance audit version from 5 to 6.
- `backend/tests/unit/test_compliance_service.py`: Cover 7/15 alert, isolated empty-region evidence at 14/15, ±2 count range, neighboring same-SKU facings, and audit v6.
- `backend/tests/unit/test_cutout_service.py`: Cover an above-threshold but low-margin ambiguous CLIP candidate pair remains `needs_review`.
- `backend/tests/integration/test_image_processing_api.py`: Expect audit version 6.
- `backend/tests/integration/test_phase_f_fixture.py` *(new)*: Upload SHA-pinned fixture, construct/select the manifest planogram, process queued input, and assert snapshot-bound compliance outcomes with deterministic reviewed detections.
- `e2e/tests/analysis_product_match.spec.ts`: Verify the saved labeled shelf output links to the correct planogram and renders the normalized four-row compliance report in Chromium.
- `image-parsing/TASK_CHECKLIST.md`, `docs/shared/COMPLIANCE_ROADMAP.md`: Record Phase F checks and the remaining model-backed/pixel-label validation.
- `docs/shared/CONTRIBUTIONS.md`, `docs/dhruv_docs/{README.md,technical_decisions.md,conversation_history.md,files_affected.md}`: Record the change, exact commands/results, and limitations.

#### Database changes
- No migration. Compliance audits are regenerated under version 6; historical resolution records remain keyed to their existing issue IDs.
### [2026-10-22 17:48 IST] Focused Shelf Findings for Reviewed Four-Row Fixture

#### Files modified
- `backend/app/services/compliance_service.py`: Bump audit version to 8; assign slot comparisons row-locally; use homogeneous-row product identity as context for low-confidence crops; emit one misplaced finding rather than duplicated slot-level reports; detect evidence-backed empty facings; suppress unavailable OCR engine placeholders from actionable shelf findings; tolerate same-row expected-SKU count variance under this reviewed policy.
- `backend/app/services/compliance_reporting_service.py`: Make the misplaced-item recommendation describe the source and target rows and the product that should occupy the vacated facing; make empty-facing guidance name its expected product.
- `backend/tests/unit/test_compliance_service.py`: Add a reviewed four-row regression asserting exactly one misplaced Lays and one Row 2 empty-facing finding, and update empty/count-variation expectations.
- `backend/tests/integration/test_image_processing_api.py`: Expect audit version 8.
- `e2e/tests/analysis_product_match.spec.ts`: Assert API and UI show the two intended findings and actionable recommendations.
- `docs/shared/CONTRIBUTIONS.md`, `docs/dhruv_docs/{README.md,technical_decisions.md,conversation_history.md,files_affected.md}`: Record outcome, test commands/results, and limitations.

#### Runtime/data changes
- No schema migration. Saved Output #8 was re-analyzed and its derived compliance audit regenerated at version 8 from persisted detections. No fresh YOLO inference was run; OCR remains unavailable.
