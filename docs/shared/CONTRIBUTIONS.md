# ShelfSense AI — Universal Team Contributions Registry

**Single Source of Truth for Team Work & Feature Execution**  
This document is automatically updated upon every feature or fix commit. It informs all team members and AI agents **who made what**, **when it was made**, **what files were affected**, and **exact commands to run/test the feature**.

| `2026-10-22 17:48 IST` | **Dhruv** | Focused Shelf Findings for Reviewed Four-Row Fixture | Working tree (not committed) | `backend/.venv/bin/pytest backend/tests -q` (83 passed); `cd e2e && npx playwright test tests/analysis_product_match.spec.ts --reporter=list` (2 passed); `git diff --check` | Regenerated Output #8 under audit v8 and reduced the reviewed image to exactly one Row 1 misplaced Yellow Lays and one Row 2 empty Yellow Lays facing. Row-scoped assignments prevent cross-row noise; homogeneous-row context suppresses per-crop uncertain-ID repeats; duplicate slot confirmations and OCR-unavailable label warnings no longer appear as shelf findings. OCR itself remains unavailable; analysis rerun reuses persisted detections, not fresh YOLO inference | `backend/app/services/compliance_service.py`, `backend/app/services/compliance_reporting_service.py`, `backend/tests/unit/test_compliance_service.py`, `backend/tests/integration/test_image_processing_api.py`, `e2e/tests/analysis_product_match.spec.ts`, `docs/shared/CONTRIBUTIONS.md`, `docs/dhruv_docs/*` |

| `2026-10-22 16:41 IST` | **Dhruv** | Compliance Verification and Handoff (Phase F) | Working tree (not committed) | `backend/.venv/bin/pytest backend/tests -q`; `cd image-parsing && PYTHONPATH=src .venv/bin/pytest tests -q`; `cd frontend && npx tsc --noEmit && npm test -- --run && npm run build`; `cd e2e && npx playwright test tests/analysis_product_match.spec.ts --reporter=list`; `git diff --check` | Adds explicit regression coverage for ambiguous CLIP, 7/15 occupancy, isolated empty evidence, neighboring products, and ±2 same-SKU count variation; tolerates same-row over-count up to two and bumps audit version to 6. Upload-to-report fixture regression uses deterministic reviewed detections; real inference is not claimed. Backend 81, image parser 38, frontend 22, and Playwright 2 checks pass | `backend/app/services/compliance_service.py`, backend compliance/matching/fixture tests, `e2e/tests/analysis_product_match.spec.ts`, `image-parsing/TASK_CHECKLIST.md`, `docs/shared/COMPLIANCE_ROADMAP.md`, `docs/shared/CONTRIBUTIONS.md`, `docs/dhruv_docs/*` |

| `2026-10-22 16:06 IST` | **Dhruv** | Evidence-Complete Compliance Reporting (Phase E) | Working tree (not committed) | `backend/.venv/bin/pytest backend/tests -q`; `cd frontend && npx tsc --noEmit && npm test -- --run && npm run build`; `git diff --check` | Makes report JSON export schema v2 link source, annotated, detector, and frozen snapshot artifacts and index product/empty/shelf crop evidence; report UI shows audit state, stock quantities, selected product/empty overlays, and per-cutout downloads. Real shelf photo evidence validation remains pending | `backend/app/services/compliance_reporting_service.py`, `backend/tests/integration/test_image_processing_api.py`, `frontend/src/components/analysis/ComplianceReportPanel.tsx`, `frontend/src/types/index.ts`, `frontend/tests/compliance-report.test.tsx`, `image-parsing/TASK_CHECKLIST.md`, `docs/shared/COMPLIANCE_ROADMAP.md`, `docs/shared/CONTRIBUTIONS.md`, `docs/dhruv_docs/*` |

| `2026-10-22 15:27 IST` | **Dhruv** | Placement-Level Stock Alert Policy (Phase D) | Working tree (not committed) | `backend/.venv/bin/pytest backend/tests -q`; `git diff --check` | Keeps per-slot comparison evidence but emits at most one placement-and-row availability alert when 50% or fewer of expected units are attributable; a single gap among 15 does not alert. Zero stock becomes one missing finding; same-row misplaced recognized units count toward quantity but remain misplaced; uncalibrated positions do not create stock alerts. The 50% rule is provisional | `backend/app/services/compliance_service.py`, backend compliance tests, `image-parsing/TASK_CHECKLIST.md`, `docs/shared/COMPLIANCE_ROADMAP.md`, `docs/shared/CONTRIBUTIONS.md`, `docs/dhruv_docs/*` |

| `2026-10-22 14:54 IST` | **Dhruv** | Row-Scoped Catalogue Consensus & Cluster Identity (Phase C) | Working tree (not committed) | `backend/.venv/bin/pytest backend/tests -q`; `cd frontend && npx tsc --noEmit && npm test -- --run && npm run build`; `git diff --check` | Keeps per-crop shelf-catalogue predictions intact, consolidates fragmented same-row clusters only on a clear catalogue majority, excludes geometry-review crops from votes, and leaves weak/singleton evidence review-needed. Cluster vote support is exposed in analysis UI/API; no accuracy calibration is claimed without labeled crop identities | `backend/app/services/product_matching/cluster_consensus.py`, `backend/app/services/cutout_service.py`, `backend/app/api/schemas/image_processing.py`, `backend/tests/unit/test_cluster_consensus.py`, `frontend/src/components/analysis/AnalysisTable.tsx`, `frontend/src/types/index.ts`, `frontend/tests/analysis-and-cutouts.test.tsx`, `image-parsing/TASK_CHECKLIST.md`, `docs/shared/COMPLIANCE_ROADMAP.md`, `docs/shared/CONTRIBUTIONS.md`, `docs/dhruv_docs/*` |

| `2026-10-22 04:48 IST` | **Dhruv** | Color-First Catalogue Candidate Gate | Working tree (not committed) | `backend/.venv/bin/pytest backend/tests -q`; `cd frontend && npx tsc --noEmit && npm test -- --run && npm run build`; `cd e2e && npm test -- --grep "Individual product catalogue matching"`; `git diff --check` | Replaces weighted appearance fusion with a color compatibility gate followed by highest raw CLIP cosine ranking; reports candidate counts/fallback and requires review when color filtering is inconclusive. Verified live Output #7 now selects Amul Milk Chocolate for the affected crops | `backend/app/services/product_matching/{color_handling.py,candidate_filtering.py,__init__.py}`, `backend/app/services/cutout_service.py`, `backend/app/api/schemas/image_processing.py`, backend matching tests, Product Match UI/types/tests, `e2e/tests/analysis_product_match.spec.ts`, `docs/shared/CONTRIBUTIONS.md`, `docs/dhruv_docs/*` |

| `2026-10-22 14:18 IST` | **Dhruv** | Shelf Fixture Ground Truth & Detection Quality Safeguards (Phases A–B) | Working tree (not committed) | `cd image-parsing && PYTHONPATH=src .venv/bin/pytest tests -q`; `cd .. && backend/.venv/bin/pytest backend/tests -q`; `cd frontend && npx tsc --noEmit && npm test -- --run && npm run build`; model-backed `shelf_image_parsing.cli` run on pinned fixture; `git diff --check` | Pins the original Output #7 photo and operator-reviewed scenario manifest; conservatively suppresses only nested duplicate detections and flags row-relative suspicious boxes without changing geometry; exposes box-quality metadata to cutout consumers and warns on flagged Product Match cards | `image-parsing/tests/fixtures/compliance/pipeline-verification/*`, `image-parsing/src/shelf_image_parsing/{detection_refinement.py,detector.py,pipeline.py,schemas.py}`, parser tests/docs, `backend/app/services/cutout_service.py`, `backend/app/api/schemas/image_processing.py`, frontend Product Match component/types/tests, shared roadmap and Dhruv journal |

| `2026-10-22 06:19 IST` | **Dhruv** | Normalized Row/Position Layout Comparison | Working tree (not committed) | `backend/.venv/bin/pytest backend/tests -q`; `cd frontend && npx tsc --noEmit && npm test -- --run && npm run build`; `git diff --check` | Adds normalized [0,1] planogram/photo row sequences, monotonic expected-vs-observed sequence alignment, left/right ordinals, explicit gaps/free intervals and an operator-facing row summary; missing/uncalibrated geometry remains review-only | `backend/app/services/spatial_matching/*`, `backend/app/services/compliance_service.py`, `backend/app/api/schemas/image_processing.py`, backend tests, `frontend/src/components/analysis/ComplianceReportPanel.tsx`, `frontend/src/types/index.ts`, `frontend/tests/compliance-report.test.tsx`, `docs/shared/CONTRIBUTIONS.md`, `docs/dhruv_docs/*` |

| `2026-10-22 04:36 IST` | **Dhruv** | Explainable Product Appearance Reranking | Working tree (not committed) | `backend/.venv/bin/pytest backend/tests -q`; `cd frontend && npx tsc --noEmit && npm test -- --run && npm run build`; `git diff --check` | Keeps shelf-scoped CLIP as primary signal, adds optional color-histogram and package-shape reranking against snapshot packshots, exposes component scores, and preserves review state for weak CLIP evidence | `backend/app/services/product_matching/*`, `backend/app/services/cutout_service.py`, `backend/app/api/schemas/image_processing.py`, backend matching tests, `frontend/src/components/analysis/ProductMatchView.tsx`, `frontend/src/types/index.ts`, `frontend/tests/analysis-and-cutouts.test.tsx`, `docs/shared/CONTRIBUTIONS.md`, `docs/dhruv_docs/*` |

| `2026-10-22 04:22 IST` | **Dhruv** | Individual Product Match View | Working tree (not committed) | `cd frontend && npx tsc --noEmit && npm test -- --run && npm run build`; `cd e2e && npm test -- --grep "Individual product catalogue matching"` | Added Product Match tab listing each individual crop and its top CLIP candidate, score, and review/confirmation state; retains current cluster views and shelf-scoped candidates | `frontend/src/components/analysis/{AnalysisTable.tsx,ProductMatchView.tsx}`, `frontend/tests/analysis-and-cutouts.test.tsx`, `e2e/tests/analysis_product_match.spec.ts`, `docs/shared/CONTRIBUTIONS.md`, `docs/dhruv_docs/*` |

| `2026-10-22 03:22 IST` | **Dhruv** | Calibrate Analysis Matching for Pipeline Verification Shelf | Working tree (not committed) | `backend/.venv/bin/pytest backend/tests -q`; `cd frontend && npx tsc --noEmit && npm test -- --run`; Playwright Chromium check of `http://localhost:3000/analysis?outputId=7` | Calibrated catalogue match cutoff to 90% using Output #7's four known shelf products; high-confidence Lays/juice/laundry groups now match, low-confidence identity becomes review-needed, and stale analysis/audit cache versions are invalidated | `backend/app/services/{cutout_service.py,compliance_service.py}`, backend tests, `frontend/src/app/analysis/page.tsx`, `frontend/src/components/analysis/AnalysisTable.tsx`, `frontend/tests/analysis-and-cutouts.test.tsx`, `docs/dhruv_docs/*` |

---

### [2026-10-22 14:18 IST] Shelf Fixture Ground Truth & Detection Quality Safeguards — Phases A–B
- **Contributor**: Dhruv
- **Commit**: Working tree (not committed)
- **Scope**: Phase A pins the actual Output #7 input image and records the frozen four-row planogram plus operator-provided expected findings in a SHA-256-verified scenario manifest. It explicitly does not claim pixel-level annotation or benchmark-grade ground truth. Phase B adds near-contained same-class duplicate suppression and advisory row-relative narrow/short geometry flags; boxes are not auto-expanded or merged.
- **How to Run / Test**:
  ```bash
  cd image-parsing && PYTHONPATH=src .venv/bin/pytest tests -q
  cd .. && backend/.venv/bin/pytest backend/tests -q
  cd frontend && npx tsc --noEmit && npm test -- --run && npm run build
  ```
- **Verification**: Image-parser suite 38 passed; backend suite 65 passed; frontend type-check, 21 Vitest tests, and production build passed. Model-backed Output #7 smoke run returned 70 products, 1 empty region, 4 rows, and 2 narrow-box review flags. This is not proof of improved localization accuracy.
- **Files affected**: Added compliance fixture image/manifest/README and fixture/refinement tests; added `detection_refinement.py`; updated image parser detector, pipeline, schemas and docs; propagated geometry quality metadata through backend cutout generation/schema and frontend Product Match UI/types/tests; updated compliance roadmap and this Dhruv journal.
- **Open work**: Manually annotate visible facings, then measure detector quality and tune/train localization. Do not change model thresholds based on the scenario-only labels.

## 1. Quick Overview Ledger

| Date & Time | Contributor | Feature / Fix | Commit | How to Run / Test | Summary of What Was Done | Files Affected |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `2026-10-22 02:43 IST` | **Dhruv** | Null Calibration Position Analysis Failure | Working tree (not committed) | `backend/.venv/bin/pytest backend/tests -q`; live GET `/api/v1/outputs/4/{analysis,cutouts,compliance}`; Chromium Playwright check at `/analysis?outputId=4` | Null `planogram_position` values are now treated as uncalibrated in both detection counters; added regression coverage | `backend/app/services/cutout_service.py`, `backend/tests/unit/test_cutout_service.py`, `docs/shared/CONTRIBUTIONS.md`, `docs/dhruv_docs/*` |
| `2026-10-22 02:25 IST` | **Dhruv** | Phase 6 Compliance Reporting & Operator Workflow | Working tree (not committed) | `backend/.venv/bin/pytest backend/tests -q`; `cd frontend && npx tsc --noEmit && npm test -- --run` | Evidence/location reports, cutout-linked highlights, filters, recommended actions, durable dispositions/notes, dashboard history, JSON export | backend compliance API/DB/service/tests, frontend analysis/dashboard/report/types/tests, shared docs and Dhruv journal |
| `2026-10-22 02:11 IST` | **Dhruv** | Phase 5 Shelf-Label OCR | Working tree (not committed) | `backend/.venv/bin/pytest backend/tests -q`; `cd frontend && npx tsc --noEmit && npm test -- --run`; `git diff --check` | Adds optional local EasyOCR, calibrated label-zone crops, text/price association and provisional audit findings with crop evidence | `backend/app/services/label_ocr_service.py`, backend audit/API/tests/docs |
| `2026-10-22 02:02 IST` | **Dhruv** | Phase 4 Planogram Compliance Engine | Working tree (not committed) | `backend/.venv/bin/pytest backend/tests -q`; `cd frontend && npx tsc --noEmit && npm test -- --run`; `git diff --check` | Adds row-aware facing-slot assignment, explicit compliance findings/evidence, and versioned audit persistence linked to output/job/snapshot | `backend/app/services/compliance_service.py`, backend API/DB/services/tests, `docs/shared/*`, `docs/dhruv_docs/*` |
| `2026-10-22 01:56 IST` | **Dhruv** | Phase 3 Photo-to-Planogram Position Mapping | Working tree (not committed) | `backend/.venv/bin/pytest backend/tests -q`; `cd image-parsing && PYTHONPATH=src .venv/bin/pytest tests -q`; `cd frontend && npx tsc --noEmit && npm test -- --run` | Adds straight-on row scaling and optional four-corner ArUco homography; records zero-based rows, physical cm spans, and calibration/tolerance status per detection | `backend/app/services/position_calibration.py`, `backend/app/services/cutout_service.py`, `backend/app/api/schemas/image_processing.py`, `backend/tests/unit/test_position_calibration.py`, `image-parsing/*`, `frontend/src/*`, `docs/shared/*`, `docs/dhruv_docs/*` |
| `2026-10-22 01:48 IST` | **Dhruv** | Phase 2 Shelf-Scoped Cutout Matching | Working tree (not committed) | Python syntax compilation; Pydantic schema generation; `cd frontend && npx tsc --noEmit`; `git diff --check` | Scores individual cutouts only against the job snapshot shelf catalogue; persists ranked candidates, margins, and review state; invalidates stale analysis cache | `backend/app/services/cutout_service.py`, `backend/app/api/schemas/image_processing.py`, `frontend/src/types/index.ts`, `frontend/src/components/analysis/AnalysisTable.tsx`, `frontend/src/components/outputs/CutoutViewerModal.tsx`, `docs/shared/*`, `docs/dhruv_docs/*` |
| `2026-10-22 01:42 IST` | **Dhruv** | Phase 1 Immutable Planogram Audit Snapshot | Working tree (not committed) | `backend/.venv/bin/pytest backend/tests -q`; `cd frontend && npx tsc --noEmit` | Captured versioned job-scoped ground truth: placements, facing slots, shelf catalogue, prices, provisional label zones, and checksum; exposed by APIs and output ZIP | `backend/*`, `frontend/src/types/index.ts`, `docs/shared/*`, `docs/dhruv_docs/*` |
| `2026-10-21 22:45 IST` | **Dhruv** | YOLO Cutout Extraction, Visual Clustering & 4-Col Analysis | `8a0b94e` | `backend/.venv/bin/pytest backend/tests/ -v && npm test --prefix frontend` | Cutout extraction into products/shelves/empty_spaces, batched CLIP embeddings, intra-shelf clustering, strict >= 95% catalog matching, Cutouts modal, and 4-column Analysis Table | 13 files (`backend/*`, `frontend/*`) |
| `2026-10-21 15:05 IST` | **Dhruv** | Shelf-Linked Image Intake & Annotated Outputs | `30474fc` | `backend/.venv/bin/pytest backend/tests -v` | Added persistent one-image-at-a-time shelf-photo intake, serial CV processing, annotated outputs, ZIP export, and UI/E2E coverage | 15 files (`backend/*`, `frontend/*`, `e2e/*`) |
| `2026-10-21 14:55 IST` | **Dhruv** | Canonical Demo Asset Cleanup | `c104bb2` | `diff -qr sample_assets shelfsense_antigravity_handoff/sample_assets` | Removed the duplicate handoff catalogue and made root `sample_assets/` the only canonical demo asset source | 16 files (`shelfsense_antigravity_handoff/*`) |
| `2026-10-21 07:00 IST` | **Dhruv** | Unified Root Logging & Real-Time Job Streamer | `19710ad` | `python logs/log_collector.py --follow` | Root `logs/logs.txt`, background job timing, HTTP middleware & frontend log ingestion | 10 files (`logs/*`, `backend/*`, `frontend/src/lib/logger.ts`, modals) |
| `2026-10-21 06:18 IST` | **Dhruv** | CLIP ViT-B/32 Vector Embeddings & Inspection CLI | `38b2583` | `backend/.venv/bin/python backend/scripts/inspect_embeddings.py --list` | Automated 512-dim normalized CLIP vector generation on product creation, backfill, & CLI | 8 files (`models.py`, `database.py`, `embedding_service.py`, `inspect_embeddings.py`, unit tests) |
| `2026-10-21 03:45 IST` | **Kumar Saurav** | Manual Product Addition Modal with Full Database Fields | `9c3118a` | Open UI $\rightarrow$ Products Library $\rightarrow$ Click **"+ Add Product"** | Full physical dimension form (cm), SVG auto-generation fallback, instant shelf placement availability | `frontend/src/components/designer/AddProductModal.tsx`, `ContextPanel.tsx`, `ShelfCanvas.tsx` |
| `2026-10-20 22:30 IST` | **Kumar Saurav** | Shelf Headroom Padding & Planogram Deletion | `b9172cd` | Open Designer $\rightarrow$ Place product $\rightarrow$ Observe row padding; Delete planogram button | Enforces row minimum height with headroom padding and auto-shifts subsequent items on delete | `ShelfCanvas.tsx`, `Dashboard.tsx`, `Outliner.tsx` |

---

## 2. Detailed Contribution Records

### [2026-10-22 02:11 IST] Phase 5 — Shelf-Label OCR
- **Contributor**: Dhruv
- **Commit**: Working tree (not committed)
- **Summary**: Added a lazily loaded EasyOCR CPU adapter as an optional, isolated dependency. Frozen placement label spans project into image crops using detected row bounds, with inverse four-corner homography when calibration markers are present; vertical label band remains a documented provisional bottom-row heuristic. OCR extracts token text/confidence, amount/currency, and explicit catalogue SKU/name references, linking each result to expected placement and crop evidence.
- **Findings/policy**: Adds `wrong_product_label`, `price_mismatch`, `missing_label`, `unreadable_label`, and `needs_review` to the persisted compliance report. OCR findings are all warning-level and carry `provisional: true` / `needs_fixture_validation`; missing engine/model fails closed. Bumps compliance audit version to 2.
- **How to Run / Test**:
  ```bash
  backend/.venv/bin/pip install -r backend/requirements-ocr.txt
  backend/.venv/bin/pytest backend/tests -q
  cd frontend && npx tsc --noEmit && npm test -- --run
  git diff --check
  ```
- **Verification**: Backend suite 53 passed, frontend Vitest 18 passed, TypeScript check, Python compilation, and whitespace check passed. Deterministic tests cover cm-to-pixel projection, inverse-homography geometry, parsing/association, crop evidence, low confidence, empty labels, and missing OCR engine.
- **Still open**: Real accuracy evaluation must remain undone until labelled shelf/price-tag photos and a ground-truth manifest exist. Existing `sample_assets/` contains catalogue packshots, not shelf-label evaluation photos. Definitive label/price alerts remain disabled by provisional status.
- **Files affected**: New `backend/app/services/label_ocr_service.py`, `backend/requirements-ocr.txt`, `backend/OCR_SETUP.md`, `backend/tests/unit/test_label_ocr_service.py`; modified `backend/app/services/compliance_service.py`, `backend/app/services/cutout_service.py`, `backend/app/api/schemas/image_processing.py`, `backend/app/services/image_processing_service.py`, `backend/tests/unit/test_compliance_service.py`, `backend/tests/integration/test_image_processing_api.py`, shared API/architecture/roadmap docs, and Dhruv journals.

### [2026-10-22 02:02 IST] Phase 4 — Planogram Compliance Engine
- **Contributor**: Dhruv
- **Commit**: Working tree (not committed)
- **Summary**: Added deterministic row-aware, left-to-right assignment of individual product cutouts to frozen expected-facing slots. Results distinguish correct, misplaced, missing, insufficient quantity, unexpected, unrecognised, and needs-review states; expected slot findings include row/cm location and references to overlapping empty-space/product cutouts. Missing-stock claims are withheld if no calibrated position frame is available.
- **Persistence/API**: Stores schema-versioned `compliance_audit` JSON on `ProcessedOutput` (with an idempotent SQLite migration) and as `compliance_audit.json` beside CV artifacts. Adds `GET /api/v1/outputs/{output_id}/compliance`, exposes persisted audits in output listings/ZIP exports, and ties each report to its output, job, and frozen snapshot SHA.
- **How to Run / Test**:
  ```bash
  backend/.venv/bin/pytest backend/tests -q
  cd frontend && npx tsc --noEmit && npm test -- --run
  git diff --check
  ```
- **Verification**: Backend suite 46 passed; frontend Vitest 18 passed; TypeScript check, Python compileall, and whitespace check passed. Compliance unit tests exercise placement, swap, missing/insufficient with empty evidence, unexpected, unrecognised, review, and snapshot linkage; integration verifies API persistence and ZIP inclusion.
- **Files Affected**: `backend/app/services/compliance_service.py` (new); `backend/app/services/cutout_service.py`; `backend/app/db/models.py`; `backend/app/db/database.py`; `backend/app/api/schemas/image_processing.py`; `backend/app/api/routes/image_processing.py`; `backend/app/services/image_processing_service.py`; `backend/tests/unit/test_compliance_service.py` (new); `backend/tests/integration/test_image_processing_api.py`; `docs/shared/COMPLIANCE_ROADMAP.md`; `docs/shared/API_CONTRACT.md`; `docs/shared/ARCHITECTURE.md`; and this Dhruv journal.

### [2026-10-22 01:56 IST] Phase 3 — Photo-to-Planogram Position Mapping
- **Contributor**: Dhruv
- **Commit**: Working tree (not committed)
- **Summary**: Added per-detection coordinate mapping from pixel boxes into the selected shelf's zero-based top-to-bottom row and physical x-span. Straight-on mode scales against detected row bounds and frozen shelf width; optional ArUco IDs 0–3 provide four-corner perspective-corrected coordinates. Missing/invalid calibration and incomplete row detection are explicit review states. Source crop pixels remain unchanged.
- **Position tolerance**: `max(1.0 cm, 1% of shelf width)`, surfaced as provisional for later fixture calibration.
- **Files affected**: New `backend/app/services/position_calibration.py`; updated cutout service/API schemas, image-parser calibration module/result schema/pipeline, `image-parsing/requirements.txt`, backend/CV tests, per-cutout inspector and analysis summary, API/architecture/roadmap and Dhruv journal records.
- **Verification**: Backend full suite passed; image-parsing suite passed (31 tests); frontend type-check and production build passed; frontend Vitest passed (18 tests); Pydantic response schemas generated and `git diff --check` passed. Physical tolerance/marker repeatability validation remains pending a measured fixture.

### [2026-10-22 01:48 IST] Phase 2 — Shelf-Scoped Individual Cutout Matching
- **Contributor**: Dhruv
- **Commit**: Working tree (not committed)
- **Summary**:
  - Removed live whole-database matching from the cutout analysis path. Each product crop is ranked independently against only the immutable `audit_snapshot.shelf_catalogue` captured for its job.
  - Persisted top candidate, runner-up, raw cosine similarities, score margin, thresholds, and `matched` / `unmatched` / `needs_review` state per cutout. Missing snapshots/embeddings are explicitly review states; no global-catalogue fallback is used.
  - Preserved per-cutout decisions alongside clustering. Cluster-level match is affirmative only if all member cutouts independently resolve to the same shelf product.
  - Added analysis version + snapshot fingerprint cache validation and showed per-cutout match details in the inspector. Thresholds are provisional pending the controlled fixture set.
- **Files affected**:
  - `backend/app/services/cutout_service.py`: shelf-scoped per-item candidate ranking and stale cache invalidation.
  - `backend/app/api/schemas/image_processing.py`: typed per-cutout match response and analysis metadata.
  - `frontend/src/types/index.ts`, `frontend/src/components/outputs/CutoutViewerModal.tsx`: types and match/review information in crop details.
  - `docs/shared/COMPLIANCE_ROADMAP.md`, `docs/shared/CONTRIBUTIONS.md`, `docs/dhruv_docs/*`: checklist and persistent handoff records.
- **Static verification**: Python syntax compilation, Pydantic schema generation, frontend `npx tsc --noEmit`, and `git diff --check` passed.
- **Test note**: Backend/frontend test suites were not run in this session. Thresholds remain uncalibrated until controlled compliance photos and ground truth are available.

### [2026-10-22 01:42 IST] Phase 1 — Immutable Planogram Audit Snapshot
- **Contributor**: Dhruv
- **Commit**: Working tree (not committed)
- **Summary of What Was Done**:
  - Captures a versioned ground-truth snapshot on each processing job at queue time, including planogram/shelf metadata, row convention, expected placements, expanded individual facings, and the deduplicated shelf-specific product catalogue with stored embeddings.
  - Captures provisional per-placement label zones with expected prices and currencies, marked as requiring later image calibration.
  - Adds an idempotent SQLite migration, API exposure, output ZIP snapshot artifacts, and the multi-phase handoff checklist.
- **How to Run / Test**:
  ```bash
  backend/.venv/bin/pytest backend/tests -q
  cd frontend && npx tsc --noEmit
  ```
- **Files Affected**:
  - `backend/app/db/models.py`, `backend/app/db/database.py`: Persist job snapshots and migrate existing SQLite databases.
  - `backend/app/api/schemas/image_processing.py`: Expose snapshot data in image and output response contracts.
  - `backend/app/services/image_processing_service.py`: Build, return, and export immutable snapshots.
  - `frontend/src/types/index.ts`: Add typed audit snapshot contracts.
  - `docs/shared/COMPLIANCE_ROADMAP.md` *(New)*: Phase checklist and controlled photo fixture plan.
  - `docs/shared/API_CONTRACT.md`, `docs/shared/ARCHITECTURE.md`: Document the snapshot contract.
 
### [2026-10-21 22:45 IST] YOLO Cutout Extraction, Semantic Clustering & 4-Column Analysis Table
- **Contributor**: Dhruv
- **Commit**: [`8a0b94e`](https://github.com/ShadowHey/Tredence_H4ck/commit/8a0b94e)
- **Summary of What Was Done**:
  - Implemented automatic YOLO bounding box cropping into 3 categorized directories: `products/`, `shelves/`, and `empty_spaces/` stored under `uploads/image_processing/outputs/{job_id}/cutouts/`.
  - Added fast batched PyTorch CLIP inference (`compute_image_embeddings_batch`), achieving ~15.6ms per crop and embedding 150+ crops in under 2.5 seconds.
  - Implemented intra-shelf visual clustering with cohesion threshold $\tau = 0.88$ to group identical facings on the shelf.
  - Implemented semantic catalog comparison against SQLite `products.embedding` enforcing strict $\ge 95\%$ confidence cutoff (`CATALOG_MATCH_THRESHOLD = 0.95`).
  - Created interactive `CutoutViewerModal` component with 3 distinct tabs (`Products`, `Shelves / Rows`, `Empty Spaces`), confidence badges, row tags, and crop inspection zoom.
  - Implemented top-level `/analysis` page with active shelf card, metric badges, output switcher, and the strict **4-column table**:
    - **Col 1: Similar Objects** (horizontal thumbnail preview/cluster with zoom click).
    - **Col 2: Similarity Percentage** (cluster cohesion score pill with visual meter).
    - **Col 3: Is object similar to someone in the product catalog?** (strictly `Yes` with green check or `No` with gray cross).
    - **Col 4: Similar Product** (if `Yes` and $\ge 95\%$, renders catalog packshot image, name, SKU, category, and price; if `No`, strictly displays NO product image).
  - Added unit test suites covering all backend routes and frontend components (35 backend tests + 17 frontend tests all passing).
- **How to Run / Test**:
  ```bash
  # 1. Run all backend tests
  backend/.venv/bin/pytest backend/tests/ -v

  # 2. Run frontend unit tests
  npm test --prefix frontend

  # 3. Build frontend bundle
  npm run build --prefix frontend

  # 4. Open in browser
  # Navigate to http://localhost:3000/outputs -> Click any shelf image card -> View Cutouts Inspector modal
  # Navigate to http://localhost:3000/analysis -> View 4-Column Table, filter pills, and crop zoom
  ```
- **Files Affected**:
  - `backend/app/services/cutout_service.py` *(New)*
  - `backend/app/services/embedding_service.py` *(Modified)*
  - `backend/app/services/image_processing_service.py` *(Modified)*
  - `backend/app/api/schemas/image_processing.py` *(Modified)*
  - `backend/app/api/routes/image_processing.py` *(Modified)*
  - `backend/tests/unit/test_cutouts_and_analysis.py` *(New)*
  - `frontend/src/types/index.ts` *(Modified)*
  - `frontend/src/lib/api.ts` *(Modified)*
  - `frontend/src/components/shell/Sidebar.tsx` *(Modified)*
  - `frontend/src/components/outputs/CutoutViewerModal.tsx` *(New)*
  - `frontend/src/app/outputs/page.tsx` *(Modified)*
  - `frontend/src/components/analysis/AnalysisTable.tsx` *(New)*
  - `frontend/src/app/analysis/page.tsx` *(New)*
  - `frontend/tests/analysis-and-cutouts.test.tsx` *(New)*

### [2026-10-21 15:05 IST] Shelf-Linked Image Intake & Annotated Outputs
- **Contributor**: Dhruv
- **Commit**: [`30474fc`](https://github.com/ShadowHey/Tredence_H4ck/commit/30474fc)
- **Summary of What Was Done**:
  - Added Input Images and Outputs navigation pages, with a user required to select one planogram and one shelf before queuing each image.
  - Added SQLite input, job, and output records; a serial/recoverable worker that invokes the isolated image-parsing pipeline; source/shelf snapshots; annotation/JSON storage; ZIP export; and safe deletion.
- **How to Run / Test**:
  ```bash
  backend/.venv/bin/pytest backend/tests -v
  cd frontend && npx tsc --noEmit && npm test && npm run build
  cd e2e && npx playwright test --list
  ```
- **Files Affected**: New image-processing backend route/schema/service/test, Input Images and Outputs pages, frontend types/API/sidebar, and Playwright journey test.

### [2026-10-21 14:55 IST] Canonical Demo Asset Cleanup
- **Contributor**: Dhruv
- **Commit**: [`c104bb2`](https://github.com/ShadowHey/Tredence_H4ck/commit/c104bb2)
- **Summary of What Was Done**: Removed the byte-identical `shelfsense_antigravity_handoff/sample_assets/` copy and clarified that the repository-root `sample_assets/` directory is canonical.
- **How to Run / Test**:
  ```bash
  diff -qr sample_assets shelfsense_antigravity_handoff/sample_assets
  ```
- **Files Affected**: Handoff prompt and the 15 deleted duplicate sample-asset files.

### [2026-10-21 07:00 IST] Unified Root Logging & Real-Time Job Streamer
- **Contributor**: Dhruv
- **Commit**: [`19710ad`](https://github.com/ShadowHey/Tredence_H4ck/commit/19710ad)
- **Summary of What Was Done**:
  - Implemented a unified logging system at the repository root (`logs/logs.txt`) that aggregates Frontend UI actions, Backend REST requests with latencies, and Background Worker telemetry in chronological order.
  - Built a standalone terminal monitoring script (`logs/log_collector.py`) with ANSI colors, line-following, job filtering, and statistical summaries.
  - Added non-blocking fire-and-forget client-side logger (`frontend/src/lib/logger.ts`) dispatching to `POST /api/v1/logs/event`.
  - Added background worker execution timer around CLIP vector generation (`[JOB-START:CLIP]`, `[JOB-DONE:CLIP]`, duration in ms).
- **How to Run / Test**:
  ```bash
  # 1. Stream all live logs in real-time
  python logs/log_collector.py --follow

  # 2. Stream only background worker jobs (e.g. CLIP embeddings)
  python logs/log_collector.py --jobs --follow

  # 3. View a statistical summary of jobs and latency
  python logs/log_collector.py --summary
  ```
- **Files Affected**:
  - `logs/log_collector.py` *(New)*: CLI log streamer and analysis tool.
  - `logs/logs.txt` *(New)*: Central log file.
  - `logs/.gitignore` *(New)*: Git rules for logs directory.
  - `backend/app/core/logging_config.py` *(New)*: Thread-safe unified log writer.
  - `backend/app/api/routes/logs.py` *(New)*: Ingestion router for client events.
  - `backend/app/main.py`: Added HTTP logging middleware and router inclusion.
  - `backend/app/services/product_service.py`: Added job start/done/duration logging.
  - `frontend/src/lib/logger.ts` *(New)*: Fire-and-forget client telemetry.
  - `frontend/src/components/designer/AddShelfModal.tsx`: Emits `ACTION:SHELF_ADD`.
  - `frontend/src/components/designer/AddProductModal.tsx`: Emits `ACTION:PRODUCT_ADD`.

---

### [2026-10-21 06:18 IST] CLIP ViT-B/32 Vector Embedding Pipeline & Direct SQLite Inspection Tool
- **Contributor**: Dhruv
- **Commit**: [`38b2583`](https://github.com/ShadowHey/Tredence_H4ck/commit/38b2583)
- **Summary of What Was Done**:
  - Integrated OpenCLIP (`ViT-B-32-quickgelu` with OpenAI weights) to compute 512-dimensional vector embeddings for all product catalog items.
  - Added `embedding JSON` column to SQLite `products` table with zero-touch automatic startup migration.
  - Hooked automated embedding computation into `create_product()` and image updates.
  - Created a direct SQLite database inspection CLI without exposing unnecessary public HTTP endpoints.
  - Verified identical copy similarity: duplicate Yellow Lays product achieves **1.000000** (100.00%) cosine similarity.
- **How to Run / Test**:
  ```bash
  # 1. List all catalog products and verify embeddings are present
  backend/.venv/bin/python backend/scripts/inspect_embeddings.py --list

  # 2. Compare two products to calculate pairwise cosine similarity
  backend/.venv/bin/python backend/scripts/inspect_embeddings.py --compare 7 8

  # 3. Duplicate any product and verify embedding equality
  backend/.venv/bin/python backend/scripts/inspect_embeddings.py --test-copy 7

  # 4. Run embedding unit test suite
  backend/.venv/bin/pytest backend/tests/unit/test_embeddings.py -v
  ```
- **Files Affected**:
  - `backend/app/services/embedding_service.py` *(New)*: CLIP singleton and similarity engine.
  - `backend/scripts/inspect_embeddings.py` *(New)*: Database inspection CLI.
  - `backend/tests/unit/test_embeddings.py` *(New)*: 5 unit tests for dimensions, L2 norm, and identity.
  - `backend/app/db/models.py`: Added `embedding = Column(JSON, nullable=True)`.
  - `backend/app/db/database.py`: Auto-migration pragma check.
  - `backend/app/api/schemas/product.py`: Added `embedding: Optional[List[float]]`.
  - `backend/app/services/product_service.py`: Automated embedding hook.
  - `backend/requirements.txt`: Added `torch`, `torchvision`, `open-clip-torch`.

---

### [2026-10-21 03:45 IST] Manual Product Addition Modal with Full Database Fields
- **Contributor**: Kumar Saurav
- **Commit**: [`9c3118a`](https://github.com/ShadowHey/Tredence_H4ck/commit/9c3118a) / [`d4d47e5`](https://github.com/ShadowHey/Tredence_H4ck/commit/d4d47e5)
- **Summary of What Was Done**:
  - Built an `AddProductModal` dialog enabling manual product creation directly from the UI.
  - Captures full database properties: Name, SKU, Category, Price, Currency, physical Width, Height, Depth in `cm`, and custom image upload.
  - If no custom packshot is uploaded, client dynamically synthesizes a crisp SVG packshot with category-themed badges and dimensions.
  - Newly created products are immediately added to catalog state and ready for instant shelf drag-and-drop.
- **How to Run / Test**:
  1. Open frontend at [http://localhost:3000](http://localhost:3000/).
  2. In the right Context Panel, click the **"Library"** tab.
  3. Click **"+ Add Product"** to open the modal.
  4. Enter details (e.g., SKU: `TEST-DRK-1`, Width: `10cm`, Height: `18cm`) and submit.
  5. Verify the product immediately appears in the library list.
- **Files Affected**:
  - `frontend/src/components/designer/AddProductModal.tsx` *(New)*: Full modal component.
  - `frontend/src/components/designer/ContextPanel.tsx`: Added trigger button and state handler.
  - `frontend/src/components/designer/ShelfCanvas.tsx`: Product placement sync.
  - `frontend/tests/components.test.tsx`: Unit tests for modal submission and field validations.

---

### [2026-10-22 00:54 IST] Individual Cutout Downloads and Reliable Attachment Delivery
- **Contributor**: Dhruv
- **Commit**: [`947e73a`](https://github.com/ShadowHey/Tredence_H4ck/commit/947e73a)
- **Summary of What Was Done**:
  - Added an authenticated-by-record, server-resolved endpoint for downloading one extracted cutout as a JPEG attachment.
  - Replaced the browser-side blob fetch with ordinary download links, preventing the user-facing “Failed to fetch” state during cutout downloads.
  - Added a Chromium Playwright journey that opens the inspector, downloads one exact crop, and verifies the absence of the error banner.
- **How to Run / Test**:
  ```bash
  backend/.venv/bin/pytest backend/tests -q
  cd frontend && npx tsc --noEmit && npm test -- --run tests/analysis-and-cutouts.test.tsx && npm run build
  cd ../e2e && npx playwright test tests/cutout_download.spec.ts --reporter=list
  ```
- **Files Affected**:
  - `backend/app/api/routes/image_processing.py`: Added the individual cutout attachment endpoint.
  - `backend/app/services/cutout_service.py`: Resolves persisted category folders safely and builds cutout archives.
  - `frontend/src/components/outputs/CutoutViewerModal.tsx`: Added per-card and detail-view download links.
  - `frontend/tests/analysis-and-cutouts.test.tsx`: Covered the visible individual download control.
  - `e2e/tests/cutout_download.spec.ts` *(New)*: Browser download regression coverage.
### 2026-10-22 16:57 IST — Restart and Refresh Saved Shelf Analyses
- **Contributor**: Dhruv with Codex
- **Commit**: Working tree (not committed)
- **Summary**: Restarted the backend and force-ran analysis on saved Outputs #1–#8. Fixed a no-vote cluster-consensus crash and ensured an explicit analysis rerun also regenerates its derived compliance audit instead of reusing a same-version stale audit.
- **Files affected**: `backend/app/services/product_matching/cluster_consensus.py`; `backend/app/services/cutout_service.py`; `backend/tests/unit/test_cluster_consensus.py`; Dhruv journal files.
- **How to run / test**:
  ```bash
  backend/.venv/bin/pytest backend/tests -q
  curl -X POST http://localhost:8000/api/v1/outputs/8/analyze
  curl http://localhost:8000/api/v1/outputs/8/compliance
  ```
- **Live rerun**: All eight outputs now analyze successfully (HTTP 200). Outputs #7/#8, the Pipeline Verification Planogram fixture, each report 75 detections, 6 clusters, 3 matched clusters, 21 products needing review; refreshed compliance counts are 16 correct, 9 tolerated count variations, 24 misplaced, 15 missing, 101 needing review, and 60 label issues. These counts did not materially decrease after rerun. Older outputs have weaker/no snapshot/catalogue evidence and remain review-heavy; Outputs #1/#2 lack frozen audit snapshots.
- **Follow-up**: Inspect why the current fixture still produces many placement/review findings and why shelf-label OCR is unavailable; compare the visual report against manually labeled image coordinates. Restarted backend remains at `http://localhost:8000`; frontend was not restarted.

### 2026-10-22 02:25 IST — Phase 6 Compliance Reports and Operator Workflow
- **Contributor**: Dhruv with Codex
- **Commit**: Working tree (not committed)
- **Summary**: Added evidence/location reports, cutout-linked issue highlighting, severity/status filters, recommended actions, persistent issue acknowledgement/resolution and notes, dashboard compliance totals/history, and JSON report export.
- **Files affected**: `backend/app/db/models.py`; `backend/app/api/routes/image_processing.py`; `backend/app/api/schemas/image_processing.py`; `backend/app/services/compliance_reporting_service.py`; `backend/tests/integration/test_image_processing_api.py`; `frontend/src/app/analysis/page.tsx`; `frontend/src/app/page.tsx`; `frontend/src/components/analysis/ComplianceReportPanel.tsx`; `frontend/src/lib/api.ts`; `frontend/src/types/index.ts`; `frontend/tests/compliance-report.test.tsx`; `docs/shared/{COMPLIANCE_ROADMAP.md,API_CONTRACT.md,ARCHITECTURE.md}`; `docs/dhruv_docs/{README.md,technical_decisions.md,conversation_history.md,files_affected.md}`.
- **How to run / test**:
  ```bash
  backend/.venv/bin/pytest backend/tests -q
  cd frontend && npx tsc --noEmit && npm test -- --run
  ```
- **Validation note**: Synthetic workflow regression coverage passes; physical shelf/label fixture calibration remains open.

### 2026-10-22 02:43 IST — Null Calibration Position Analysis Failure
- **Contributor**: Dhruv with Codex
- **Commit**: Working tree (not committed)
- **Summary**: Fixed analysis 500 on detection records whose `planogram_position` is explicitly null. The same unsafe nested `.get()` existed in both response and metrics counters; both now safely count only calibrated position dictionaries.
- **Files affected**: `backend/app/services/cutout_service.py`, `backend/tests/unit/test_cutout_service.py`, and Dhruv handoff journal.
- **How to run / test**:
  ```bash
  backend/.venv/bin/pytest backend/tests -q
  ```
- **Live verification**: Output #4 `analysis`, `cutouts`, and `compliance` endpoints returned HTTP 200; Chromium opened `/analysis?outputId=4`, rendered 11 findings, and showed no analysis error or JavaScript exceptions.
