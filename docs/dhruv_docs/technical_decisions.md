# Dhruv's Architecture Decision Records (ADRs)

### [2026-10-22 06:19 IST] Normalized Row/Position Layout Comparison

- **Decision**: Keep current shelf calibration and physical-coordinate assignment as the source of compliance decisions, and add a versioned normalized representation (x/shelf-width in [0,1]) for transparent side-by-side row sequence inspection.
- **Representation**: Rows are zero-based internally and top-to-bottom; items carry one-based ordinals from left/right. Planogram expected facings, observed product cutouts, detected empty-space regions, and uncovered intervals remain distinct evidence types.
- **Safety**: Incomplete calibration makes comparison review-only. The UI presents counts/order/interval summaries; pixel-equivalent or exact-image comparison is not attempted. Audit version increments to force stale stored records to rebuild.
- **Alignment**: Each normalized row also gets a monotonic dynamic-programming sequence alignment with explicit paired, missing-expected, and unexpected-observed steps. This remains diagnostic; the existing physical nearest-slot assignment and catalogue verification remain the compliance decision path pending labeled fixture validation.

### [2026-10-22 04:48 IST] Color-First Catalogue Candidate Gate

- **Decision**: Replace soft CLIP/color/shape fusion with a two-stage decision path: (1) remove shelf-catalogue products below a provisional HSV color-histogram intersection threshold of 0.30; (2) rank only survivors by raw CLIP cosine similarity and return the maximum as the closest candidate.
- **Fallback**: If no packshot candidates clear the gate, retain only the best color-compatible candidate(s) within a 0.05 score margin and mark `needs_review`. If catalogue packshot evidence is wholly unavailable, fall back to the full shelf catalogue but also force review. A color fallback can never be confirmed even if CLIP is high.
- **Threshold and limits**: The 0.30 threshold is selected to reject the orange-juice candidate observed at 0.20 color similarity in the reported screenshot. It is a starting cutoff, not a universal calibrated value; illumination, package revisions, crop/background contamination, and missing packshots require validation against labeled shelf images.
- **Cache/API/UI**: Increment analysis version to 6; return color score, before/after candidate counts, threshold, fallback state/reason, and matching method. UI states how many candidates passed the color gate and separately displays the raw CLIP score. Keep the existing 0.90 raw-CLIP match threshold and ambiguity margin.
- **Simplification**: Remove weighted candidate fusion and package-shape ranking modules because they allow non-color signals to override the explicitly requested color-first gate. Existing CLIP model and embedding service remain unchanged.

### [2026-10-22 04:36 IST] Explainable Product Appearance Reranking

- **Decision**: Keep CLIP as the primary shelf-catalogue identity signal and use color histogram intersection (HSV hue, saturation-weighted) plus coarse package aspect ratio only to rerank eligible candidates. Appearance scores are supporting evidence, not standalone identity or probability estimates.
- **Ranking and review policy**: Initial weights are provisional (80% CLIP, 15% color, 5% shape). Preserve raw CLIP score for the existing 0.90 confirmation threshold, and use the fused-score lead to detect ambiguity. Missing/unreadable packshots fall back to CLIP-only ranking. Catalogue scope remains the frozen shelf snapshot.
- **Cache/API**: Bump analysis cache version so existing per-crop rankings are recomputed. Return raw CLIP score, rerank score, color score, shape score, and whether appearance evidence was available; Product Match labels raw similarity separately and states the rerank score is not a probability.
- **Trade-off / pending calibration**: Hand-weighted contributions are not a measured accuracy improvement. Real precision/recall comparison requires labeled held-out shelf crops and packshots across lighting, orientation, and occlusion conditions. Existing optional shelf-label OCR is for shelf labels, not a reliable substitute for package OCR.

### [2026-10-22 04:22 IST] Individual Product Match View

- **Decision**: Keep the existing cluster filters at cluster granularity and implement Product Match as a separate per-cutout view. Flatten each cluster’s `similar_objects` in the client because every item already carries its own CLIP `catalog_match` result from the API.
- **Presentation**: Show the top candidate even when it is below threshold or ambiguous, but mark only backend-confirmed matches as Confirmed; otherwise use Needs review. Display the candidate similarity separately from cluster cohesion. Use the frozen shelf catalogue results already stored with the output.
- **Trade-off**: No ranking recomputation or API contract change is introduced. This keeps the view aligned with the original output/shelf snapshot and avoids silently searching the global product database.

### [2026-10-22 03:22 IST] Analysis Matching Calibration for Pipeline Verification Shelf

- **Decision**: Use a 0.90 minimum cosine similarity for the current four-product controlled shelf fixture. This is a fixture-specific baseline, not a general production accuracy claim. Keep the existing 0.03 runner-up margin so near-ties remain `needs_review`.
- **Evidence and behavior**: Output #7's 20 orange juice, 15 Yellow Lays, and 14 laundry-liquid detections each scored at least 0.90 against the frozen shelf catalogue. The prior 0.95 threshold rejected every one. Below-threshold scores indicate insufficient identity evidence, not evidence that the product is absent; map them to review-needed rather than an unrecognised-product error.
- **Cache/UI**: Bump analysis and audit versions to force re-evaluation of old cached scores/findings. Show the active threshold from the API and label the visual percentage as cluster cohesion, distinct from CLIP catalogue confidence.
- **Trade-off / open validation**: Amul Chocolate remains review-needed because its individual crops score below 0.90 and/or disagree. More labeled examples are required before extrapolating this threshold; OCR findings remain provisional and out of scope.

### [2026-10-22 02:11 IST] Phase 5 — Shelf-Label OCR

- **Decision**: Use EasyOCR locally in CPU mode behind a separate lazy-loaded adapter and optional `backend/requirements-ocr.txt`; do not add cloud OCR or a runtime API key. Reader construction and inference are serialized/cached per backend process.
- **Label geometry**: Project snapshotted physical x spans through detected row bounds, using inverse four-corner homography when available. Until actual label height is calibrated, crop the bottom 22% of the detected row and mark geometry provisional.
- **Association and evidence**: Persist per-zone OCR strings/confidences, parsed amounts/currency, explicit catalogue SKU/name references, image-space bbox/polygon, and crop path into `label_audit` in the version-2 compliance report.
- **Alert policy**: `wrong_product_label`, `price_mismatch`, `missing_label`, and `unreadable_label` are provisional warnings and require fixture validation. Missing package/model and invalid geometry fail closed as `needs_review`.
- **Unresolved validation**: Repository assets have no labelled shelf-price photos/ground truth. Unit tests use a deterministic fake OCR reader and validate logic only; no real-world accuracy claim or definitive alert is made.

### [2026-10-22 02:02 IST] Phase 4 — Planogram Compliance Engine

- **Decision**: Evaluate individual cutouts against the immutable `expected_facing_slots` from the job snapshot, assigning in detected top-to-bottom row and left-to-right order using physical overlap/distance. Keep per-slot state/evidence separate from alerts, and expose the audit independently from the visual-cluster analysis.
- **Conservative policy**: Correct requires both an unambiguous individual shelf-catalogue match and calibrated physical row/x agreement. A recognized product on an unassigned/incorrect slot is misplaced or unexpected; unknown identity is unrecognised; ambiguous identity or unavailable position is needs-review. Empty-space crops are supporting evidence. Missing/short facings derive from slots not correctly occupied, but are downgraded to needs-review when the position frame is unavailable.
- **Persistence**: Store the versioned report in `processed_outputs.compliance_audit` and an output-local `compliance_audit.json`; report includes output/job IDs and snapshot SHA. The API serves it directly and output ZIPs include it.
- **Trade-offs / pending**: A new nullable JSON column requires an idempotent SQLite migration. Audit `complete` only means evaluation completed. Phase 2 similarity thresholds and Phase 3 spatial tolerance remain provisional pending controlled fixtures.

### [2026-10-22 01:56 IST] Phase 3 — Photo-to-Planogram Position Mapping

- **Decision**: Preserve detector pixel boxes, and attach a separate optional physical position derived from the frozen shelf dimensions/row geometry. Straight-on images use per-row horizontal bounds; controlled perspective fixtures may use four OpenCV ArUco marker centres.
- **Marker contract**: `DICT_4X4_50`, IDs 0/1/2/3 at usable shelf TL/TR/BR/BL; project those pixel anchors into a normalized rectangular frame with a homography. This rectifies coordinate measurement, not source image files or saved cutouts.
- **Row convention**: CV parser row numbers are 1-based top-to-bottom; mapped planogram row indices are 0-based top-to-bottom. Row-count mismatch, missing row extents, invalid quadrilaterals, or unavailable physical dimensions are exposed as review conditions.
- **Tolerance**: `max(1 cm, 1% of shelf width)` is an initial position comparison tolerance, not a measured accuracy bound. It requires real fixture validation.

---

### [2026-10-22 01:42 IST] Phase 1 — Immutable Planogram Audit Snapshot
- **Commit**: Working tree (not committed)
- **Status**: Implemented; verification commands documented for handoff

#### Decision
Store the full audit ground truth as a versioned JSON value on `ProcessingJob`, captured in the same database transaction that queues the image. Expose that job snapshot through input/output responses and include it as a separate artifact in output ZIPs.

#### Rationale
Planograms, placements, product prices, and embeddings can change after image processing. A job-scoped snapshot gives future compliance matching the exact shelf-specific candidate catalogue and expected facing layout for that processing attempt. A failed retry creates a new job and therefore a new snapshot; a completed output keeps its original job snapshot.

#### Snapshot Contents and Boundaries
- Includes planogram/shelf metadata, top-to-bottom row convention, placement geometry in centimetres, expanded facing slots, deduplicated catalogue products, prices, and provisional label-zone spans.
- Includes UTC capture time, schema version, and SHA-256 checksum.
- Label zones carry expected price/currency and remain provisional until photo calibration defines image-space coordinates.
- This phase does not change the current global CLIP matching, detection, OCR, compliance scoring, or dashboard behavior.

#### Migration
`init_db()` adds nullable `processing_jobs.audit_snapshot JSON` to existing SQLite databases after checking the table columns. Fresh databases receive it through SQLAlchemy metadata creation.

### [2026-10-21 22:45 IST] YOLO Cutout Extraction, Semantic Clustering & 4-Column Analysis Table
- **Commit**: [`8a0b94e`](https://github.com/ShadowHey/Tredence_H4ck/commit/8a0b94e)
- **Status**: Implemented & Verified in Production

#### 1. Context & Problem Statement
From the YOLO shelf detection pipeline, bounding box coordinates are produced for products, shelf structures, and void spaces. Operators need to:
1. Visually inspect the individual cropped images categorized into three distinct buckets: `products`, `shelves`, and `empty_spaces`.
2. Group repeated identical product faces on a shelf (visual clustering).
3. Semantically match detected visual clusters against the product catalog using dense vector embeddings.
4. Enforce a strict $\ge 95\%$ confidence cutoff for catalog matches, presenting a clean 4-column compliance view where non-matches strictly omit any catalog packshot image.

#### 2. Options Considered
- **Option 1**: Compute CLIP vectors sequentially on each cropped bounding box on HTTP request.
  - *Cons*: Sequential CLIP processing takes ~360ms per crop. A shelf with 150+ products would take >50 seconds to respond, blocking the UI thread.
- **Option 2 (Chosen)**: Fast batched PyTorch CLIP inference (`compute_image_embeddings_batch`, batch size 32) coupled with asynchronous precomputation upon job completion.
  - *Pros*: Cuts inference time to **15.6ms per crop**. 150+ crops are embedded in <2.5 seconds. Results are persisted to disk (`cutouts.json`, `analysis.json`) for instant sub-10ms UI reads.

#### 3. Key Architectural Decisions
- **Disk Cutout Organization**:
  Stored in `uploads/image_processing/outputs/{job_id}/cutouts/` with separate subdirectories for `products/`, `shelves/`, and `empty_spaces/`.
- **Intra-Shelf Clustering**:
  Uses a leader-clustering algorithm with a strict visual similarity threshold $\tau = 0.88$. Items above $\tau$ are grouped into the same cluster.
- **Catalog Matching Rule**:
  Cluster centroid vectors are compared against SQLite `products.embedding` vectors via cosine similarity. If $\max(\text{similarity}) \ge 0.95$, `is_catalog_match = True`, and the catalog product details and packshot image are linked. If $< 0.95$, `is_catalog_match = False` and no catalog product is displayed.
- **The 4-Column Table Specification**:
  Implemented in `frontend/src/components/analysis/AnalysisTable.tsx`:
  1. `Similar Objects`: Horizontal scrollable thumbnails of crops belonging to this cluster.
  2. `Similarity Percentage`: Cluster visual cohesion percentage with color-coded meter.
  3. `Is object similar to someone in the product catalog?`: Strictly `Yes` (green check) or `No` (gray cross).
  4. `Similar Product`: Catalog packshot image and details if `Yes`; strictly NO product image rendered if `No`.

---

### [2026-10-21 15:05 IST] Image Intake, Shelf Assignment & Annotated Outputs
- **Commit**: [`30474fc`](https://github.com/ShadowHey/Tredence_H4ck/commit/30474fc)
- **Status**: Implemented and verified.
- **Decision**: Persist each uploaded shelf photo with one explicitly selected planogram and shelf before queueing it. The selected shelf dimensions are snapshotted at queue time, and a single-concurrency worker calls the isolated `image-parsing` environment to create an annotated image and detection JSON.
- **Rationale**: This keeps every output auditable even if the source shelf is later changed, prevents parallel heavyweight model runs, and preserves queued work across restarts through SQLite job records.
- **Trade-off**: Users process one image at a time by design; batch upload remains available for staging photographs.

### [2026-10-21 07:00 IST] Unified Root Logging & Real-Time Job Streamer
- **Commit**: [`19710ad`](https://github.com/ShadowHey/Tredence_H4ck/commit/19710ad)
- **Status**: Implemented & Verified in Production

#### 1. Context & Problem Statement
With background jobs (such as CLIP vector embedding generation) and dynamic frontend actions running concurrently, developers lacked visibility into what was executing under the hood. When a user created a product or shelf in the UI, there was no continuous centralized stream showing:
1. The frontend action intent.
2. The backend REST route handling with latency.
3. The background worker job execution time and status.

#### 2. Options Considered
- **Option 1**: Rely only on browser console and terminal uvicorn stdout.
  - *Cons*: Logs are fragmented across separate windows; impossible to inspect background worker execution history after the fact; no unified timeline.
- **Option 2**: Full ELK or external telemetry stack (Datadog/Sentry).
  - *Cons*: Overkill for local dev and hackathon environment; introduces heavy network/service dependencies.
- **Option 3 (Chosen)**: A unified root `logs/` directory with `logs.txt` as a single file sink, coupled with a lightweight, color-coded Python streamer CLI (`logs/log_collector.py`).

#### 3. Final Technical Decision & Rationale
- **Thread-Safe File Sink**: Implemented `backend/app/core/logging_config.py` using standard library threading locks and immediate line flushing (`f.flush()`). This guarantees zero delay between event occurrence and file persistence.
- **Client Ingestion Route**: Added `POST /api/v1/logs/event` and a non-blocking `frontend/src/lib/logger.ts` helper (`keepalive: true`) so frontend UI actions (`ACTION:SHELF_ADD`, `ACTION:PRODUCT_ADD`) reach `logs.txt` without blocking the browser thread.
- **Request Middleware**: Attached HTTP logging middleware to FastAPI to log all incoming requests with duration in ms, while specifically excluding `/logs/event` to prevent infinite logging loops.
- **Background Worker Instrumentation**: Wrapped CLIP generation in `product_service.py` with `time.perf_counter()` to log `[JOB-START:CLIP]`, `[JOB-DONE:CLIP]`, and `[JOB-ERROR:CLIP]` with precise duration in milliseconds.
- **Standalone CLI**: Built `logs/log_collector.py` using standard Python only (`argparse`, `sys`, `time`). Supports `--follow`, `--jobs`, `--frontend`, `--backend`, and `--summary`.

---

### [2026-10-21 06:18 IST] CLIP ViT-B/32 Vector Embeddings for Product Catalog
- **Commit**: [`38b2583`](https://github.com/ShadowHey/Tredence_H4ck/commit/38b2583)
- **Status**: Implemented & Verified in Production

#### 1. Context & Problem Statement
To enable visual planogram merchandising compliance and product grouping, catalog items needed to be converted into dense semantic vector representations. Multiple packshots of similar products (e.g., various flavours or packet sizes of Lays chips) must project closely in vector space, while distinct product categories (e.g., chips vs chocolate) must separate cleanly.

#### 2. Options Considered
- **Option 1**: External cloud embedding API (OpenAI / Cohere).
  - *Cons*: Network latency, API costs, dependency on external internet connectivity during offline development.
- **Option 2**: ResNet-50 / generic ImageNet feature extraction.
  - *Cons*: Lacks multimodal semantic grounding; fails to capture packaging typography and visual category nuances.
- **Option 3 (Chosen)**: Local OpenCLIP `ViT-B/32` with OpenAI pretrained weights (`quickgelu`).
  - *Pros*: Runs completely locally on CPU in ~40ms per packshot; multimodal vision-language understanding; zero external API keys required.

#### 3. Final Technical Decision & Rationale
- **Model Architecture**: OpenCLIP `ViT-B-32-quickgelu` (`pretrained="openai"`). Loaded as a singleton in `backend/app/services/embedding_service.py` with HuggingFace hub caching.
- **$L_2$ Normalization**: Every 512-dimensional output vector is unit-normalized ($\|\mathbf{v}\|_2 = 1.0$), ensuring that cosine similarity is directly computed via dot product ($\mathbf{a} \cdot \mathbf{b}$).
- **Database Architecture**: SQLite JSON column (`embedding JSON`) added to the `products` table. Auto-migration checks `PRAGMA table_info(products)` on startup and adds the column without manual migration scripts.
- **Deterministic Identity Requirement**: Ensured identical packshots produce identical embeddings. Verified on Product #7 ("Yellow Lays") vs duplicate copy: Cosine Similarity = **1.000000** (100.00% exact match).
- **No Unwanted HTTP Endpoints**: Per user direction, avoided public vector comparison routes and instead built `backend/scripts/inspect_embeddings.py` for direct SQLite CLI inspection (`--list`, `--compare`, `--test-copy`, `--backfill`).

---

### [2026-10-22 00:54 IST] Individual Cutout Downloads & Fetch Failure Fix
- **Commit**: [`947e73a`](https://github.com/ShadowHey/Tredence_H4ck/commit/947e73a)
- **Status**: Implemented and verified

#### Decision
Expose a backend-owned `GET /api/v1/outputs/{output_id}/cutouts/{cutout_id}/download` route that resolves a cutout only from persisted output metadata, then serves it with `Content-Disposition: attachment`.

#### Rationale
The previous client-side blob fetch depended on a separate asset request and surfaced “Failed to fetch” when that request was interrupted. Direct attachment links use the browser download mechanism, while server-side lookup maps semantic categories (`product`, `shelf`, `empty_space`) to their actual pluralized storage directories.

#### Verification
- `backend/.venv/bin/pytest backend/tests -q` — 35 passed.
- Frontend type-check, focused Vitest test, and production build passed.
- Chromium Playwright confirmed a downloaded `.jpg` and no “Failed to fetch” banner.
### [2026-10-22 01:48 IST] Phase 2 — Shelf-Scoped Individual Cutout Matching

- **Status**: Implemented in working tree; score calibration remains pending controlled fixtures.
- **Decision**: Compare each product crop embedding independently with only the frozen `shelf_catalogue` stored on its processing job. Never query/fallback to the mutable global Product table for audit matching.
- **Recognition policy**: A cutout is `matched` only above the provisional 0.95 cosine threshold and by at least the provisional 0.03 margin over runner-up. Below threshold is `unmatched`; ambiguous, missing-snapshot, or unavailable-embedding cases are `needs_review` with explicit reasons.
- **Identity and clustering**: Keep every crop’s match result on its own cutout record. Visual clusters remain presentation summaries and are marked matched only when all members resolve to the same SKU.
- **Cache correctness**: Version results and attach the audit-snapshot fingerprint; recompute caches created by old global matching or for a different snapshot.
- **Trade-off**: Conservative statuses avoid presenting a near-tie as a definitive SKU. The numeric thresholds are provisional; controlled fixture calibration is still required before operational claims.
### [2026-10-22 02:25 IST] Phase 6 — Compliance Reporting & Operator Workflow

- **Status**: Implemented in working tree; backend and frontend verification pass.
- **Decision**: Keep operator disposition separate from generated compliance evidence. `ComplianceIssueResolution` references output ID and deterministic issue ID, stores `open`/`acknowledged`/`resolved` plus optional note, and is removed with its output.
- **Reporting**: Per-output API decorates issues with stable identifiers and recommended actions; dashboard aggregates only persisted audits and recent planogram/shelf audit records. JSON export includes the report and originating immutable snapshot.
- **Evidence display**: Cutout-backed findings can highlight their pixel bounding box on annotated output; slot-only findings show the audited row and physical centimetre range without pretending an uncalibrated mapping exists.
- **Trade-off / remaining validation**: The summary endpoint deliberately does not run CV/OCR as a dashboard side effect. Controlled shelf photos remain necessary to evaluate real detection, position, and OCR accuracy.
- **Verification**: `backend/.venv/bin/pytest backend/tests -q`; `cd frontend && npx tsc --noEmit && npm test -- --run`.

### [2026-10-22 02:43 IST] Null Calibration Position Analysis Failure

- **Cause**: Position mapping intentionally writes `planogram_position: null` when there is no usable calibration. Analysis summary counters used `item.get("planogram_position", {}).get(...)`; the default only handles a missing key, not a present null value, causing a 500 after detections were extracted.
- **Fix**: A shared safe counter now checks that the detection and position are dictionaries before reading `status`. Both the API response count and persisted metrics use it.
- **Verification**: Added null/missing/review/calibrated unit cases. Backend suite passed (54 tests); Output #4 analysis, cutouts, compliance APIs returned 200; Chromium rendered the analysis report with 11 findings and no page errors.
