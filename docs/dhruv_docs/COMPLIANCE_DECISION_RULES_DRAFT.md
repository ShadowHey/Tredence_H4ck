# Shelf Compliance Decision Rules — Operator-Labeled Draft

**Status:** Draft for product review; documentation only. Nothing in this document has been implemented by this session.
**Prepared:** 2026-10-22 19:43 IST; updated 2026-10-22 19:57 IST
**Evidence source:** User-reviewed screenshot showing annotated `bc_image2.png` and its current Analysis/report page. The screenshot does not expose an output ID, so it is recorded by filename only.

## Purpose

Preserve operator-provided ground truth and turn it into a clear, testable basis for later compliance rules. The operator's visual interpretation is the intended outcome for this example. The current detector and report are observations to compare against that truth—not authority to overrule it.

## Operator-labeled expected result for `bc_image2.png`

Rows are interpreted by the human as four product rows, top to bottom. Positions below are qualitative left-to-right order because no manually measured pixel or centimetre coordinates were supplied.

| Row | Intended product row | Operator says is actually visible (left to right) | Desired actionable outcome |
|---|---|---|---|
| 1 (top) | Amul Milk Chocolate | Chocolate; one empty facing; one Yellow Lays packet in the chocolate row; one more empty facing; remaining visible row products | Three localized conditions: one confirmed empty facing, one misplaced Yellow Lays (recommend moving it to Row 2 and refilling its source facing with chocolate), and a second confirmed empty facing. Do not emit repeated per-crop warnings for these same physical conditions. |
| 2 | Yellow Lays | Lays with one empty facing between products | One localized empty-facing alert. Do not infer a wider stock failure from this single gap. |
| 3 | Orange Juice | Orange Juice, two empty facings, and one unknown/non-catalogue product | Two localized empty-facing alerts and one unknown/unrecognized product alert. Do not label the unknown item as Fresh Laundry Liquid unless its identity is actually supported. |
| 4 (bottom) | Fresh Laundry Liquid | Laundry liquid with one empty facing | One localized empty-facing alert. |

The operator therefore expects **six empty facings**, **one misplaced known product**, and **one unknown product**. The screenshot's annotation header says `Products: 36`, `Empty Slots: 7`, and `Rows: 3`; this differs from the operator's four visible merchandise rows and six empty spaces. Treat that as an unresolved detector/report discrepancy, not as a reason to silently change the operator-labeled result. Verify whether the seventh empty-space detection is a duplicate/fragment or an additional real gap before using raw detector counts as ground truth.

The screenshot's report counters show **66 findings** and **57 review-needed**. The visible cards repeat a Row 3 Fresh Laundry misplacement recommendation. The operator does not expect those repeated relocation warnings: only the one misplaced Lays in Row 1 should drive that relocation recommendation. This document does not infer the unseen breakdown of the other findings.

## Second operator-labeled example: `a9d73188d33e41b289a3824eec438306.png`

This is a separate four-row shelf photo. The screenshot does not show an output ID or report panel; the image overlay header reads `Products: 32`, `Empty Slots: 4`, `Rows: 4`, and `Empty Area: 15.5%`. Those are detector/annotation diagnostics, not manually verified truth. The operator reports that the current report has improved substantially (roughly five or six review-quality suggestions remain); this is qualitative feedback, not a count verified from the screenshot.

| Row | Operator-labeled scene, left to right | What current result got right / missed | Desired outcome |
|---|---|---|---|
| 1 (top; Amul Milk Chocolate expected) | One empty facing; one Yellow Lays packet among the chocolates; then two more empty facings | One empty and the misplaced Lays are detected; two empty facings are missed | Three distinct empty-facing conditions and one misplaced known-product condition. Recommend moving the Lays to its expected Row 2 position and restoring chocolate at its Row 1 source position. |
| 2 (Yellow Lays expected) | One empty facing | Empty facing missed | One localized empty-facing condition. |
| 3 (Orange Juice expected) | One empty facing; another empty facing; one wrong/unknown product (visually a pale-yellow `DAILY CLEAN SPRAY` bottle); another empty facing; one more empty facing | Two empties are detected; two empties are missed; the wrong product receives no action/recommendation | Four distinct empty-facing conditions and one wrong-product condition with an actionable recommendation to replace/remove the non-catalogue item and restore the expected Orange Juice, subject to identity/localization evidence. |
| 4 (Fresh Laundry Liquid expected) | One empty facing | Empty facing detected | One localized empty-facing condition. |

The operator's counts sum to **nine actual empty facings**: Row 1 = 3, Row 2 = 1, Row 3 = 4, Row 4 = 1. The current image overlay marks **four** empty regions (Row 1 = 1, Row 3 = 2, Row 4 = 1), leaving **five missed** (Row 1 = 2, Row 2 = 1, Row 3 = 2). In addition, there is one correctly detected misplaced Lays and one Row 3 wrong product without an action. These are semantic/operator counts from the message and visual review; exact pixel boundaries, facing alignment, and whether each visible interval equals one planogram facing still need annotation. Do not substitute the overlay's `Empty Slots: 4` for the operator-labeled total.

## What the example teaches

1. **Row segmentation is a prerequisite, not a detail.** The selected shelf/planogram has four merchandise rows according to the operator, while the current annotated image header says three. If detected row count does not reconcile with the selected shelf, row-dependent identity/position conclusions can shift an entire row and generate convincing but wrong relocation advice.
2. **Detection boxes are evidence, not alerts.** Multiple boxes, fragments, adjacent boxes, or repeated uncertain crops must not each become a separate operator finding. Findings should represent distinct physical anomalies after association and deduplication.
3. **An empty region is not the same thing as a confirmed missing facing.** A localized empty-space box should be associated with an expected facing, with adjacent/fragmented empty boxes consolidated where they refer to the same physical gap. A low-confidence rejected product box must leave uncertainty, not automatically become a confirmed empty.
4. **Identity must precede relocation advice.** A known catalogue item in the wrong row can support a misplaced-product recommendation. A product-like object with insufficient identity evidence should be `unknown/unrecognized` or review-needed; the system must not assign it the expected SKU just because that row is homogeneous.
5. **Separate location, quantity, and identity.** One empty facing, a misplaced known SKU, and an unknown product are different facts. Report each once, with its row, position, evidence and recommended action. Do not multiply one cause into repeated warnings plus a duplicate stock alert.
6. **Keep the operator's expected outcome machine-readable.** Future fixtures need explicit image dimensions, row boundaries, per-product boxes/identity, empty intervals, and expected findings. This screenshot supplies semantic row-level labels, not precise box coordinates, so it is not yet pixel-level detector ground truth.
7. **Measure empty-space recall separately from product detection.** This second case shows a clear gap between four marked regions and nine operator-labeled empty facings. Validate whether each missed gap was never proposed, was merged/suppressed, or failed association to an expected facing; do not “fix” the result by lowering confidence globally without measuring false positives.
8. **A wrong-product observation needs an action path.** A localized product that is confidently not the expected row SKU should produce one wrong-row/product finding and a correction recommendation. If identity is uncertain, say “unrecognized product in Orange Juice row; verify/replace with expected Orange Juice” rather than inventing an exact SKU. It must not disappear merely because CLIP or cluster consensus abstains.

## Proposed decision flow for a later implementation

These are candidate rules to review; they are not approved production policy yet.

1. **Validate the audit context.** Confirm the job's frozen planogram/shelf snapshot, expected number/order of rows, usable shelf width, and catalogue. If the snapshot is missing, do not issue confident placement findings.
2. **Validate row mapping before comparing products.** Compare detected shelf rows with expected rows and check their top-to-bottom ordering and coverage. If count/order/geometry is inconsistent (as the screenshot header suggests), suppress row-based “misplaced” and row-based expected-product recommendations; expose one row-mapping review condition and retain raw detections for inspection.
3. **Build one normalized row layout for each source.** From the snapshot, represent each expected facing by row, SKU, physical x interval, and normalized `[0,1]` x interval. From the image, represent each product box and empty region by detected row, normalized interval, confidence, and provenance. Preserve pixel boxes and calibration method so every output is traceable.
4. **Resolve product identity conservatively.** Apply the product confidence gate and catalogue match logic. Treat a confident catalogue identity as known; treat no-candidate/weak/ambiguous evidence as unknown or review. Row consensus may support an identity only when the detection-quality and row-mapping checks pass; row membership alone must not manufacture identity.
5. **Associate observations to expected facings within a validated row.** Use overlap/centre and sequence order with tolerance, while ensuring one observed product or empty region cannot satisfy multiple facings. Maintain explicit unassigned and uncertain evidence.
6. **Form physical anomaly groups.** Merge duplicate/fragmented product boxes and connected/overlapping empty regions before producing findings. Emit at most one finding for one physical anomaly/facing (or one well-defined contiguous gap), with all contributing detection IDs attached as evidence.
7. **Classify in a stable order.** (a) known product matching expected SKU and position → correct; (b) known expected-SKU product in a different validated row/slot → misplaced, with a target recommendation; (c) confirmed unknown identity → unrecognized/unknown; (d) explicit empty-region overlap with an unoccupied expected facing → empty facing; (e) residual under-occupancy → aggregate availability rule only after the agreed threshold; (f) ambiguous geometry/identity → review, not a guessed error.
8. **Deduplicate causes and recommendations.** A misplaced product should produce one source-to-target action. Do not separately report the vacated source as an additional empty if the product is physically there and the recommendation already instructs refilling it, unless the operator explicitly wants both facts. Empty intervals elsewhere remain separate findings.
9. **Return a compact report plus full evidence.** Summary counts should count distinct findings, not crop count. Each finding should link row, normalized/physical interval, input-image box(es), source cutout IDs, confidence/identity evidence, expected SKU, observed SKU/unknown, reason, and recommended action. Keep a separate evidence-coverage/review status; do not inflate alert totals with diagnostic uncertainty.

## Candidate acceptance criteria for this example

- [ ] The vision/row layer reconciles the four operator-visible product rows with the selected shelf. If it cannot, row-dependent recommendations are withheld and the audit says review is required.
- [ ] The report has six unique localized empty-facing findings: two in Row 1, one in Row 2, two in Row 3, and one in Row 4.
- [ ] The Row 1 Yellow Lays is one known misplaced-product finding, targeting Row 2; the recommendation identifies chocolate as the product expected in its source facing.
- [ ] The Row 3 non-catalogue object is reported once as unknown/unrecognized only if there is a product detection with sufficient localization; it is not mislabeled as laundry liquid due to row consensus.
- [ ] No duplicated per-box or per-fragment alert is generated for a single physical facing/gap.
- [ ] One empty facing does not become a low-stock alert unless the separately agreed placement-level stock rule is met.
- [ ] Filtering a low-confidence product box cannot alone prove an empty shelf location; mark that location uncertain unless independent empty-space evidence confirms it.
- [ ] The UI can show a concise distinct-finding count while allowing evidence expansion to inspect all contributing detections.

## Candidate acceptance criteria for the second example

- [ ] Preserve the four visible merchandise rows and their top-to-bottom expected identities; do not let the image header's `Products: 32` or `Empty Slots: 4` override the operator annotations.
- [ ] Represent the nine operator-labeled empty facings as Row 1: 3, Row 2: 1, Row 3: 4, Row 4: 1. Match detections to these only after adding pixel-level interval labels and a reviewed planogram alignment.
- [ ] Track the current empty-region recall gap explicitly: four overlay regions currently detected versus nine operator-labeled empty facings (five missed). Tests should identify proposal, merge, association, and reporting stages responsible for each miss.
- [ ] Keep the single Row 1 Yellow Lays as one misplaced-product issue with a move-to-Row-2 recommendation; identify Amul Milk Chocolate as the expected product at its source only when the selected planogram confirms that SKU/slot.
- [ ] Emit one actionable Row 3 wrong-product finding for the `DAILY CLEAN SPRAY`-looking object when supported by localization and identity evidence; otherwise emit a localized unknown-product review with explicit expected Orange Juice correction guidance, not no action and not a fabricated identity.
- [ ] Deduplicate fragments/overlapping boxes so each physical empty facing or wrong product yields one finding, while preserving all contributing detector IDs as evidence.
- [ ] Keep this example's expected findings separate from `bc_image2.png`; the latter has six empties, while this example has nine by the operator's current left-to-right account.

## Inputs needed to promote this draft into implementation rules

- A pixel-level annotation for this exact image: row boundary polygons/boxes, all product boxes and identities (including the unknown item), and each true empty interval.
- Confirmation whether the two Row 1 empty gaps should be two independent findings if each spans one facing, and whether the misplaced Lays's source-facing correction is part of that finding or a separate empty/missing finding.
- A decision on when an “unknown product” is actionable versus `needs_review` (detection confidence, catalogue-match evidence, and minimum visible area).
- Agreement on row-count mismatch behavior, empty-region merging tolerance, position tolerance, and low-stock/quantity aggregation.
- At least one compliant image and controlled variants (move one item, remove facing(s), add unknown item) to regression-test both correct alerts and false-alert suppression.

## Handoff checklist

- [ ] Obtain product-owner review of the operator-labeled outcomes and candidate rules.
- [ ] Add pixel annotations and a versioned expected-findings manifest; keep the screenshot-level labels explicitly marked as coarse until coordinates exist.
- [ ] Quantify current YOLO row/product/empty detection precision and recall against the annotations.
- [ ] Implement row-map validation and alert suppression before tuning scoring or recommendation wording.
- [ ] Implement anomaly grouping/deduplication and one-finding-per-physical-condition semantics.
- [ ] Implement conservative unknown-product identity handling and validate row-consensus abstention.
- [ ] Add unit, backend integration, and Playwright regressions using this exact fixture and its selected planogram.
- [ ] Compare generated findings against each fixture's expected conditions independently (`bc_image2.png`: eight; this second example: eleven) and document any deliberate policy deviations.
- [ ] Only after review, move approved rules to shared product/compliance specifications and mark this draft superseded or approved.
