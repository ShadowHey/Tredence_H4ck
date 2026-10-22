# ShelfSense Shelf Compliance Pipeline — Handoff Checklist

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
