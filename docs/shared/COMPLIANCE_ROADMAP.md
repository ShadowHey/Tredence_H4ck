# ShelfSense Shelf Compliance Pipeline — Handoff Checklist

### Product confidence cutoff — 2026-10-22
- [x] Add an independent 0.60 acceptance threshold for product detections. Product boxes with confidence `< 0.60` are excluded from crops, CLIP/color matching, clusters, and product quantities; boxes at `0.60` are retained.
- [x] Keep the lower shared YOLO proposal floor for empty-space candidates and shelf structures; product filtering does not disable empty-space/row detection.
- [x] Preserve low-confidence product boxes as uncertainty-only geometry. If one overlaps an expected facing, mark that facing uncertain/review rather than deriving empty/missing/shortage solely from the filter.
- [x] Apply the gate during initial parsing and saved-output reprocessing; expose effective threshold and excluded-box counts.
- [x] Add threshold-boundary, empty-space independence, and compliance uncertainty tests; run backend/parser/frontend/build/Playwright checks.
- [ ] Evaluate precision/recall and false-negative impact against pixel-level labeled shelf images before treating 60% as calibrated.

**Boundary and current fixture:** This is a product acceptance threshold, not the shared model proposal threshold. Reprocessing saved Output #8 produced 60 accepted product crops and 10 excluded low-confidence boxes (9 overlap/map to expected facings). The actionable findings remain one misplaced Yellow Lays in Row 1 and one empty Lays facing in Row 2. Mapped exclusions keep the audit status review-required but do not add empty/missing/shortage issues. OCR accuracy is unchanged.

This checklist tracks implementation of the shelf-photo compliance pipeline. The first phase freezes the planogram ground truth at queue time. Future phases should build on that snapshot and preserve raw CV artifacts.

## Phase 1 — Freeze audit ground truth at queue time

- [x] Store a versioned, immutable snapshot on each processing job so a retry captures a new snapshot while completed work keeps its original one.
- [x] Capture the planogram identity, description, and update timestamp.
- [x] Capture shelf dimensions, configured and resolved row heights, row elevations, plinth dimensions, and the established row convention (`row_index` 0 is top; rows proceed top-to-bottom).
- [x] Capture every placement with product identity, expected row, physical x-range in centimetres, and facing count.
- [x] Expand placements into individually addressable expected facing slots with physical x-ranges.
- [x] Capture a deduplicated shelf-specific product catalogue, including prices, packshot paths, dimensions, and any existing CLIP embedding.
- [x] Capture provisional expected label zones and expected price/currency for each placement. Mark their image geometry as requiring later calibration.
- [x] Add an idempotent SQLite migration for existing `processing_jobs` tables.
- [x] Expose the snapshot through staged-input and processed-output API responses and include it in output ZIP exports.
- [ ] Review snapshot schema with downstream compliance implementation before changing its version or semantics.

## Phase 2 — Shelf-scoped individual product matching

- [x] Match each detected product cutout only against `audit_snapshot.shelf_catalogue`.
- [x] Persist top candidate, runner-up, similarity, confidence margin, and recognition/review state for every cutout.
- [x] Keep cutout identity and per-item match data even when repeated products are visually clustered for display.
- [ ] Calibrate match thresholds and ambiguity rules against the controlled fixture set.

**Phase 2 implementation note (2026-10-22):** Matching is performed per crop against the immutable job snapshot, and results are retained in `cutouts.json`/the cutouts API as `catalog_match`. Existing clusters remain a presentation grouping only; a cluster is called matched only when every member independently matches the same shelf-catalogue product. The 0.95 score and 0.03 ambiguity-margin values are named provisional thresholds, not calibrated production values. Legacy/global-catalogue caches are invalidated by analysis version and snapshot fingerprint.

## Phase 3 — Map photo coordinates to planogram coordinates

- [x] Define and implement image calibration using detected shelf rows and known shelf width for straight-on images.
- [x] Add optional four-corner ArUco calibration markers and projective coordinate correction for controlled test photos.
- [x] Convert product and empty-space pixel boxes to planogram row and physical x-ranges in centimetres.
- [x] Verify top-to-bottom row indexing against the snapshot convention and define a provisional position tolerance.
- [ ] Validate the provisional tolerance and marker-placement repeatability against a measured physical shelf fixture.

**Phase 3 implementation note (2026-10-22):** Straight-on mapping scales each detection's x-span against its detected shelf-row bounds and the frozen shelf width. Optional OpenCV `DICT_4X4_50` markers use IDs 0/1/2/3 at usable-area TL/TR/BR/BL; their centres produce an image-to-rectified-frame homography for perspective-corrected coordinates. All cutouts retain original-image crops. Results expose 0-based top-to-bottom `row_index`, `x_start_cm`, `x_end_cm`, mapping method, and tolerance `max(1 cm, 1% of shelf width)`. The tolerance is provisional and requires physical fixture validation; missing/invalid calibration remains explicitly `needs_review`.

## Phase 4 — Planogram compliance engine

- [x] Assign individual cutouts deterministically to expected facing slots in top-to-bottom row and left-to-right order, preferring physical overlap and the detected row.
- [x] Report correct, misplaced, missing, insufficient quantity, unexpected product, unrecognised product, and needs-review results with row/cm locations and reasons.
- [x] Attach overlapping detected empty-space cutouts as evidence; derive missing/insufficient facings from expected slots not correctly occupied.
- [x] Persist a versioned audit in SQLite and `compliance_audit.json`, linked to output/job IDs and the frozen snapshot SHA; expose it by API and include it in output exports.

**Phase 4 implementation note (2026-10-22):** Compliance is conservative. A detection is “correct” only when its individual identity and calibrated physical position agree with its assigned snapshotted facing slot. Unknown identities and uncalibrated positions remain review/unrecognized findings. No missing-stock claim is made when the run has no calibrated position frame. “complete” means the audit ran, not that the shelf passed. Similarity thresholds and coordinate tolerance still require fixture calibration (Phases 2–3).

## Phase 5 — Shelf-label OCR

- [x] Select and isolate an OCR engine and document local setup/runtime requirements.
- [x] Define image-space label-zone extraction using calibrated shelf coordinates.
- [x] Extract text, price, currency, and OCR confidence with evidence references.
- [x] Associate labels with expected products and report wrong product, wrong price, missing label, and unreadable label issues.
- [ ] Evaluate OCR accuracy on labelled test photos before surfacing definitive alerts.

**Phase 5 implementation note (2026-10-22):** Added optional EasyOCR CPU inference in its own backend requirements file and lazy service module. Expected label x-spans project from frozen centimetre geometry through detected row bounds; four-corner calibration uses the inverse homography. The vertical band is currently the bottom 22% of a detected row because Phase 1 snapshots do not encode label height. Each zone stores its crop, OCR text/confidences, parsed amount/currency, and any explicit catalogue reference; provisional price/product/missing/unreadable findings are appended to the versioned compliance audit and exported with evidence. If the package/model is absent, the audit records `needs_review`. Accuracy evaluation remains open: `sample_assets/` contains catalogue packshots but no labelled shelf/price-tag photos, so this implementation does not emit definitive OCR alerts.

## Phase 6 — Reports and operator workflow

- [x] Extend the per-output analysis view into a compliance report with issue locations and evidence.
- [x] Add annotated issue overlays for findings with detection evidence, severity/status filters, status controls, and recommended actions.
- [x] Add dashboard compliance summaries and per-output planogram/shelf audit history.
- [x] Add machine-readable JSON compliance export and persistent issue-resolution workflow.

**Phase 6 implementation note:** Resolution states (`open`, `acknowledged`, `resolved`) and optional notes are stored in SQLite separately from the generated audit. Finding identifiers are deterministic within a persisted output audit; reports retain the original audit evidence and expose the current operator disposition. Image overlays highlight referenced product cutouts; findings without pixel-level cutout evidence retain their calibrated shelf row and centimetre span instead of drawing an inferred box. Dashboard history includes outputs whose compliance audit has been generated. Synthetic API/UI coverage validates this workflow; real-world position, catalogue, and OCR thresholds still require the controlled fixture set below.

## Controlled test fixture and photo checklist

- [ ] Create one physical two- or three-row shelf with four to six distinct products represented in the catalogue.
- [ ] Arrange exact planogram placements with measured widths, row indices, x-offsets, facing counts, prices, and visible shelf labels.
- [ ] Capture straight-on, in-focus, glare-free baseline image `01_compliant` with the full shelf and labels visible.
- [ ] Capture one controlled perspective image with the four prescribed ArUco markers and measured corner coordinates.
- [ ] Capture `02_misplaced` by swapping two products without changing total quantity.
- [ ] Capture `03_missing` by removing one expected product.
- [ ] Capture `04_insufficient_quantity` by removing one facing from a multi-facing placement.
- [ ] Capture `05_unexpected_product` by adding a product not assigned to this shelf.
- [ ] Capture `06_wrong_label` with a product’s label positioned under another product.
- [ ] Capture `07_wrong_price` with the correct product label showing a deliberately incorrect price.
- [ ] Capture `08_ocr_challenge` with controlled small text, mild blur, or glare; expected outcome is low-confidence review.
- [ ] Store a ground-truth manifest with expected issue types, SKU, row, physical span, and label text/price for every scenario.
- [ ] Keep the existing generic CV sample photographs for detector regression only; they are not compliance truth because their products/layout do not correspond to the project catalogue and a matching saved planogram.

## Suggested fixture layout

```text
sample_assets/compliance-fixtures/v1/
  catalogue/
  planograms/
  photos/
    01_compliant/
    02_misplaced/
    03_missing/
    04_insufficient_quantity/
    05_unexpected_product/
    06_wrong_label/
    07_wrong_price/
    08_ocr_challenge/
  ground-truth/expected-audits.json
```

## Detection Accuracy Follow-up — Phases A and B (2026-10-22)

### Phase A — Ground-truth fixture (implemented, scoped)
- [x] Pin the original Output #7 shelf photo by SHA-256 and dimensions.
- [x] Record the frozen 4-row, 15-facing planogram, row/SKU mapping, operator-described observations, and expected alert policy.
- [x] Label provenance and limitations: this is scenario-level/manual visual truth, not pixel-coordinate annotations or a detector benchmark.
- [x] Add integrity and policy regression tests.
- [ ] Complete manually reviewed per-facing bounding-box coordinates before reporting YOLO precision/recall or tuning thresholds.

### Phase B — Detection/crop safeguards (implemented, conservative)
- [x] Suppress only near-contained same-class duplicates after YOLO's normal NMS; preserve separate adjacent products and original coordinates.
- [x] Mark row-relative narrow/short boxes as `review` in parser JSON; leave their coordinates unchanged.
- [x] Propagate geometry-quality status and flags into cutout analysis metadata and API types; invalidate stale cutout cache.
- [x] Add unit tests and run a model-backed smoke pass on the pinned photo.
- [ ] Train/calibrate localization against reviewed bbox labels, then evaluate the original image and perturbation cases before changing confidence/NMS settings.

The safeguards improve observability and avoid unsafe guessed geometry. They do not claim to repair half-product boxes or improve model localization; that requires labeled data and a measured evaluation loop.

### Phase C — Catalogue consensus and fragmented cluster identity (implemented, conservative)
- [x] Preserve every individual crop's shelf-catalogue match as independent evidence.
- [x] Consolidate fragmented visual clusters only when a clear candidate majority agrees within the same calibrated row.
- [x] Keep mixed-identity, uncalibrated-row, and weak-evidence groups separate; suspicious geometry crops do not vote.
- [x] Confirm a cluster only with at least two supporting detections, a 60% candidate majority, and enough individually confirmed crop matches; otherwise expose the best-supported candidate as review-needed.
- [x] Return vote counts/ratio and render the candidate plus consensus state in Cluster Breakdown; bump analysis cache version.
- [x] Add pure unit coverage for majority merge, dissenting product, row isolation, flagged-crop abstention, and singleton abstention.
- [ ] Calibrate the provisional 60% / two-crop rule using a manually labeled crop-identity fixture across compliant and deliberately mixed rows.

**Phase C boundary:** This phase changes cluster aggregation and presentation only. It does not rewrite individual CLIP/color-first rankings, change YOLO localization, or change compliance issue/alert policy. Consensus is not a probability; weak evidence remains review-needed.

### Phase D — Planogram comparison and actionable alert policy (implemented, provisional)
- [x] Group expected facing slots by planogram placement and row; avoid treating a single gap among a large facing count as a placement-level low-stock alert.
- [x] Retain individual slot results and evidence in the report while raising one aggregate availability issue only when 50% or fewer of expected facings are detected for that placement.
- [x] Raise one `missing_product` issue for a placement with zero attributable units and one `insufficient_quantity` warning at/below the 50% boundary.
- [x] Count recognized same-row units for stock quantity even if a unit is misplaced within that row; retain the separate misplaced-location finding.
- [x] Suppress definitive shortage issues when position calibration is unavailable; keep rows/slots review-needed.
- [x] Add regression tests for one missing out of 15, exactly-half stock, no stock, placement isolation, and audit versioning.
- [ ] Validate the requested cutoff and alert behavior against manually reviewed physical shelf photos and per-facing ground truth.

**Phase D boundary:** The 50% value is a product-requested provisional rule, not a learned or industry-calibrated threshold. YOLO and CLIP errors can still affect inferred quantities and placements; no certainty is claimed beyond available evidence.

### Phase E — Evidence-complete operator report (implemented)
- [x] Export a versioned JSON evidence manifest linking the report to the original input, annotated image, detector JSON, and frozen audit snapshot.
- [x] Index product, empty-space, and shelf crops with category, image path, source bbox, confidence, crop-quality metadata, and mapped planogram position.
- [x] Display audit state and expected-versus-observed facing quantities in the report.
- [x] Highlight both product and empty-space crop boxes for a selected finding and provide direct downloads of each evidence crop.
- [x] Cover export provenance and report evidence in backend/API and frontend component tests.
- [ ] Validate evidence paths and issue-to-crop correspondence on manually reviewed physical shelf photos.

**Phase E boundary:** The export is a path-based evidence index, not a self-contained ZIP. It reuses existing artifact storage and the cutout download route and does not alter detection, matching, compliance rules, or thresholds. Physical photo validation remains required before relying on the report for real-world decisions.

### Phase F — Verification and handoff (implemented)
- [x] Cover duplicate suppression, adjacent products, fragmented same-row clusters, cross-row separation, dissenting candidates, and ambiguous individual CLIP results.
- [x] Cover misplaced products; 14/15 and 7/15 placement occupancy; isolated empty-space evidence; count variation of ±2 same-SKU items; and uncalibrated inputs.
- [x] Exercise fixture-photo upload, assignment to a fixture-derived planogram/shelf, queue processing, frozen snapshot, and report retrieval with deterministic reviewed detection evidence.
- [x] Exercise the saved labeled output and its selected planogram report in Chromium Playwright.
- [x] Run and record full backend, image-parser, frontend, TypeScript, production-build, and targeted Playwright checks.
- [ ] Run model-backed inference against manually labeled per-item bounding boxes and validate actual detections, matching, physical positions, and report outcomes.

**Phase F implementation note (2026-10-22):** Compliance now tolerates a same-row, same-SKU count delta up to two above or below the planogram count, while still retaining slot-level gap evidence; larger overages remain unexpected. Audit version advanced to 6. This narrow tolerance is provisional and specifically reflects the reviewed fixture scenario. The fixture integration uses deterministic operator-reviewed detection evidence after real upload/selection/queue operations; it does not establish YOLO/CLIP accuracy. Exact commands and results are recorded in Dhruv's journal and the contributions ledger.
