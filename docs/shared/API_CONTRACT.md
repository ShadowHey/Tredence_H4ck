# ShelfSense AI — API Contract (v1)

This document specifies the REST API contract for the ShelfSense AI Planogram Designer backend.

## Base URL
- Default local server: `http://localhost:8000`
- API Prefix: `/api/v1`
- Static Uploads: `/uploads/`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`

---

## 1. System & Health

### `GET /health`
Returns system health, database connectivity, and uploads storage accessibility.

**Response: `200 OK`**
```json
{
  "status": "ok",
  "database": "healthy",
  "uploads_dir": "/Users/.../backend/uploads",
  "uploads_accessible": true
}
```

---

## 2. Product Catalogue

### `GET /api/v1/products`
Lists products in the catalogue.

**Query Parameters:**
- `search` (optional string): Case-insensitive match on product name or SKU.
- `category` (optional string): Exact match on category (or "all" for all categories).

**Response: `200 OK`** (Array of Product objects)
```json
[
  {
    "id": 1,
    "sku": "DEMO-DRK-001",
    "name": "Citrus Sparkling Drink",
    "category": "Beverages",
    "description": "Unbranded sample can; illustration only.",
    "price": 35.0,
    "currency": "INR",
    "width_cm": 6.5,
    "height_cm": 12.2,
    "depth_cm": 6.5,
    "image_path": "uploads/sample_products/citrus_drink_can.svg",
    "is_sample": true,
    "created_at": "2026-10-20T00:00:00Z",
    "updated_at": "2026-10-20T00:00:00Z"
  }
]
```

### `POST /api/v1/products` (Multipart Upload)
Creates a new product with an uploaded image file.

**Content-Type:** `multipart/form-data`
**Form Fields:**
- `sku` (string, required, unique)
- `name` (string, required)
- `category` (string, optional, default "General")
- `description` (string, optional)
- `price` (float, required >= 0)
- `currency` (string, required, default "INR")
- `width_cm` (float, required > 0)
- `height_cm` (float, required > 0)
- `depth_cm` (float, required > 0)
- `image` (file, binary, allowed MIME types: jpeg, png, webp, svg+xml; max 5MB)
- `image_path` (string, alternative if image is already stored)

**Responses:**
- `201 Created`: Returns created Product object.
- `400 Bad Request`: Missing image or unsupported MIME type / size limit exceeded.
- `409 Conflict`: SKU already exists in database.
- `422 Unprocessable Entity`: Invalid dimensions or negative price.

### `GET /api/v1/products/{id}`
Retrieves a single product by ID.
- `200 OK`: Product object.
- `404 Not Found`: Product does not exist.

### `PATCH /api/v1/products/{id}`
Updates editable product fields.

### `DELETE /api/v1/products/{id}`
Deletes a product from the catalogue.
- `200 OK`: `{"message": "Product deleted successfully."}`
- `409 Conflict`: Product cannot be deleted if placed on saved planogram shelves.

---

## 3. Planograms & Dashboard

### `GET /api/v1/planograms`
Lists saved planograms with shelf and placement counts, sorted by most recently updated.

**Response: `200 OK`**
```json
[
  {
    "id": 1,
    "name": "Beverages Gondola A",
    "description": "Front aisle reference",
    "shelf_count": 2,
    "placement_count": 8,
    "created_at": "2026-10-20T01:00:00Z",
    "updated_at": "2026-10-20T01:15:00Z"
  }
]
```

### `GET /api/v1/planograms/metrics`
Returns verified SQLite database totals for the MoEngage-style Dashboard KPIs.

**Response: `200 OK`**
```json
{
  "total_planograms": 3,
  "total_products": 6,
  "total_shelves": 4,
  "total_placements": 14,
  "recent_planograms": [...]
}
```

### `POST /api/v1/planograms`
Creates a new named planogram.

**Payload:**
```json
{
  "name": "Snack Bay 2026",
  "description": "Optional notes"
}
```

### `GET /api/v1/planograms/{id}`
Retrieves full planogram including all nested shelves and placements.

### `PATCH /api/v1/planograms/{id}`
Updates planogram name and description.

### `DELETE /api/v1/planograms/{id}`
Deletes planogram and its associated shelves/placements via cascade delete.

---

## 4. Shelves

### `POST /api/v1/planograms/{planogram_id}/shelves`
Adds a shelf to a planogram.

**Payload:**
```json
{
  "name": "Shelf 01",
  "width_cm": 120.0,
  "total_height_cm": 180.0,
  "depth_cm": 40.0,
  "row_count": 4,
  "has_plinth": true,
  "plinth_height_cm": 15.0,
  "order_index": 0
}
```

**Validation Rules:**
- `width_cm > 0`, `total_height_cm > 0`, `depth_cm > 0`
- `row_count` integer in `[1..12]`
- `plinth_height_cm >= 0` and `< total_height_cm`

### `PATCH /api/v1/shelves/{shelf_id}`
Updates shelf dimensions, name, or row count.
- **Safety check**: If reducing `row_count` or `width_cm` would orphan or truncate existing product placements, returns `422 Unprocessable Entity` detailing the collision.

### `DELETE /api/v1/shelves/{shelf_id}`
Deletes a shelf and its placements.

### `GET /api/v1/shelves/{shelf_id}/capacity/{row_index}`
Calculates deterministic row capacity in centimetres.

**Response: `200 OK`**
```json
{
  "row_index": 0,
  "total_width_cm": 120.0,
  "used_width_cm": 45.5,
  "remaining_width_cm": 74.5,
  "percent_used": 37.9,
  "placement_count": 4
}
```

---

## 5. Placements (Physical Coordinates & Collision)

### `POST /api/v1/shelves/{shelf_id}/placements`
Places a product on a shelf row.

**Payload:**
```json
{
  "product_id": 1,
  "row_index": 0,
  "x_offset_cm": 0.0,
  "facing_count": 1
}
```

**Responses:**
- `201 Created`: Placement created with ID.
- `422 Unprocessable Entity`:
  - `x_offset_cm + (product.width_cm * facing_count) > shelf.width_cm` (exceeds shelf width).
  - Interval $[x, x + w]$ overlaps an existing placement on the same row.
  - Invalid row index.

### `PATCH /api/v1/placements/{placement_id}`
Moves placement to another row, changes horizontal $x$ offset in cm, or updates facing count. Validates zero-overlap and shelf width before applying.

### `DELETE /api/v1/placements/{placement_id}`
Removes a placement without deleting the catalogue product.

---

## 6. Two-Way Exports

### `GET /api/v1/planograms/{id}/export.json`
Returns machine-readable, versioned JSON with physical measurements in cm.

**Response Schema (`PlanogramExportJSON`):**
```json
{
  "format_version": "1.0",
  "unit": "cm",
  "planogram_id": 1,
  "planogram_name": "Beverages Gondola A",
  "description": "Front aisle reference",
  "shelves": [
    {
      "id": 1,
      "name": "Shelf 01",
      "width_cm": 120.0,
      "total_height_cm": 180.0,
      "depth_cm": 40.0,
      "row_count": 4,
      "has_plinth": true,
      "plinth_height_cm": 15.0,
      "placements": [
        {
          "id": 10,
          "shelf_id": 1,
          "product_sku": "DEMO-DRK-001",
          "product_name": "Citrus Sparkling Drink",
          "row_index": 0,
          "x_offset_cm": 0.0,
          "facing_count": 2,
          "product_width_cm": 6.5,
          "product_height_cm": 12.2,
          "product_depth_cm": 6.5
        }
      ]
    }
  ],
  "products": [
    {
      "id": 1,
      "sku": "DEMO-DRK-001",
      "name": "Citrus Sparkling Drink",
      "category": "Beverages",
      "width_cm": 6.5,
      "height_cm": 12.2,
      "depth_cm": 6.5,
      "price": 35.0,
      "currency": "INR"
    }
  ],
  "exported_at": "2026-10-20T02:00:00Z"
}
```

---

## 7. Sample Seeding

### `POST /api/v1/seed`
Loads the 6 unbranded sample products from `sample_assets/catalogue.sample.json` and copies SVG/PNG packshots into `uploads/sample_products/`.
- `200 OK`: `{"status": "success", "seeded_count": 6, ...}`

---

## 8. Shelf Image Processing Ground Truth

When `POST /api/v1/input-images/{input_image_id}/process` accepts a valid planogram and shelf, it freezes audit ground truth on that processing job. The `audit_snapshot` field is returned by `GET /api/v1/input-images` and `GET /api/v1/outputs`.

Version 1 includes planogram identity, selected shelf dimensions, configured and resolved row heights/elevations, the row convention (`row_index` 0 is the top row and indices increase top-to-bottom), each expected placement and physical x-range in centimetres, an individually addressable record for every facing, and the deduplicated shelf-specific catalogue with prices, packshot paths, dimensions, and available CLIP embeddings. It also captures provisional per-placement label zones with expected price/currency; image-space x spans are projected through detected row bounds, while the vertical label band remains provisional and requires fixture calibration. The snapshot contains a UTC capture time, schema version, and SHA-256 checksum.

The snapshot belongs to the processing job attempt. Retrying a failed image creates a new job and snapshot. Completed outputs retain their original job snapshot if the planogram or catalogue later changes. Output ZIPs contain `audit_snapshot.json` per output, and `manifest.json` references its path. Legacy jobs may not have a snapshot.

### Shelf-scoped cutout matching

`GET /api/v1/outputs/{output_id}/cutouts` returns each product cutout with a `catalog_match` object. Its `status` is `matched`, `unmatched`, or `needs_review`; it includes the top candidate, runner-up, cosine similarities, confidence margin, provisional thresholds, and an explicit reason. Candidates are drawn exclusively from the job's `audit_snapshot.shelf_catalogue`. Jobs without a snapshot or usable catalogue embeddings do not fall back to the current global product catalogue and are marked for review.

`GET /api/v1/outputs/{output_id}/analysis` keeps the visual-cluster summary and adds `analysis_version`, `catalog_scope`, `audit_snapshot_sha256`, the provisional score/margin thresholds, and `products_needing_review`. A cluster is considered matched only when all its individual cutouts match the same catalogue product. Results are cached per analysis version and snapshot fingerprint. Thresholds are provisional pending calibration against controlled fixtures.

### Planogram compliance audit

`GET /api/v1/outputs/{output_id}/compliance` returns a versioned audit bound to the processed output, its processing job, and `audit_snapshot_sha256`. `assignments` records each product cutout's selected facing slot and state; `slot_results` records each expected facing's state and empty-space/product evidence; `issues` contains non-correct findings with type, reason, and row/centimetre location where available. Finding types are `misplaced_product`, `missing_product`, `insufficient_quantity`, `unexpected_product`, `unrecognised_product`, and `needs_review`. Correct placements are recorded in assignments and slot results, not duplicated as alerts.

The result is persisted in `processed_outputs.compliance_audit` and beside the CV artifacts as `compliance_audit.json`; output ZIPs include the audit when present. An audit status of `complete` means the comparison ran, not that the shelf passed. If position calibration is unavailable, expected slots are marked `needs_review` rather than producing definitive empty-stock claims.

The same audit includes `label_audit`: EasyOCR tokens/confidences, parsed price/currency, per-zone OCR state, evidence crop paths, and provisional label findings (`wrong_product_label`, `price_mismatch`, `missing_label`, `unreadable_label`, or `needs_review`). The local engine is optional and can be installed with `backend/.venv/bin/pip install -r backend/requirements-ocr.txt`; see `backend/OCR_SETUP.md`. Every OCR finding carries `provisional: true` and `confidence_status: needs_fixture_validation`; no definitive price/label alerts should be exposed until the labelled fixture evaluation is completed.

### Phase 6 operator reporting

- `GET /api/v1/outputs/{output_id}/compliance` augments each computed finding with a stable `issue_id`, `status` (`open`, `acknowledged`, `resolved`), optional `resolution_note`, and a recommended action. Finding location/evidence remains sourced from the output's immutable audit; cutout-backed findings can be highlighted on the annotated image.
- `PATCH /api/v1/outputs/{output_id}/compliance/issues/{issue_id}` accepts `{ "status": "open|acknowledged|resolved", "note": "optional operator note" }`. Resolutions are stored in `compliance_issue_resolutions`, independently of the computed audit, and cascade-delete with their output.
- `GET /api/v1/compliance/summary` returns persisted audit counts and the 20 most recent audit entries by planogram/shelf, including issue disposition counts. It does not trigger CV/OCR processing for outputs which have not yet had an audit generated.
- `GET /api/v1/outputs/{output_id}/compliance/export.json` exports the complete report, disposition state, source linkage, annotated artifact path, and originating audit snapshot as JSON.

### Photo-to-planogram positions

Each product/empty-space cutout may include `planogram_position`: the zero-based top-to-bottom `row_index`, `x_start_cm`, `x_end_cm`, and centre measured from the usable shelf's left edge. `position_calibration` reports the method, detected/expected row counts, and provisional tolerance `max(1 cm, 1% of shelf width)`. Row-based scaling assumes a straight-on view and uses detected row extents plus the immutable snapshot shelf width; incomplete row coverage is reported as `needs_review`.

The image parser optionally detects OpenCV `DICT_4X4_50` ArUco IDs 0–3. Place marker centres at usable-shelf TL, TR, BR, BL corners in that order; their image-coordinate homography rectifies detection coordinates for mapping. It does not alter the original photo or saved crops. Missing, duplicated, degenerate, or out-of-image markers fall back to row-based mapping. This option is intended for controlled fixtures, not as a substitute for validating camera and marker placement.
