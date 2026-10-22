# Dhruv's Files & Folders Affected Log (Blast Radius)

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
