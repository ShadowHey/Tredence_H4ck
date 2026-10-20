# ShelfSense AI — Stage 1 Product Specification

**Version:** 0.1 · **Stage:** First usable Planogram Designer MVP · **Audience:** Antigravity coding agent, project owner, teammate

## 1. Product purpose

ShelfSense AI will help retail teams design a reference planogram directly in the software. Users create a shelf, define its real-world measurements and rows, add product records with images and dimensions, drag products onto rows, save the arrangement locally, and export both a visual planogram and machine-readable layout data. This saved planogram will become an input to a later shelf-image compliance system.

**Important boundary:** this stage is a planogram editor and inventory/catalogue foundation. It does not perform computer vision, compare live shelf photos, detect out-of-stocks, read real price labels, or calculate AI compliance scores yet.

## 2. Visual direction from the supplied references

Use the four user-supplied screenshots as design references, not as content to reproduce pixel-for-pixel:

1. **Retail Shelf Planner screenshot:** reference for seeing products arranged across several horizontal shelf rows.
2. **Formal planogram page:** reference for showing physical measurements, rows/shelves, product positions, and an exportable planogram layout.
3. **MoEngage dark dashboard:** reference for the polished analytics-app shell: dark charcoal background, restrained accent color, sidebar navigation, clear cards, strong hierarchy and generous spacing. Do not copy its analytics subject matter or claim to reproduce its exact design.
4. **Blender Outliner screenshot:** reference for a scene/object hierarchy panel in which a planogram contains shelves, shelves contain rows, and rows contain placements.

The main shelf work area must be bright and easy to read against the dark application shell. Draw shelves as white/light-grey structures with clear, dark measurement annotations. Product artwork must retain its aspect ratio and be scaled using declared dimensions, not stretched to fill arbitrary boxes.

## 3. Scope: only two pages

### Page A — Dashboard

- A dark-themed app shell with clear navigation to **Dashboard** and **Design Your Own Planogram**.
- Show useful KPIs derived from saved local data: number of saved planograms, products in catalogue, and shelves in saved planograms.
- Show a recent-planograms list with name, updated date/time, shelf count and an Open action.
- Provide an obvious **Create Planogram** action.
- Show a helpful empty state when there are no saved plans or products. Do not invent demo activity, charts or metrics to make the dashboard look populated.
- Clicking a plan opens it in the designer. The dashboard must use actual API/database data.

### Page B — Design Your Own Planogram

Use a professional dark outer shell and a three-area editor workspace:

- **Left: Scene / Outliner.** A Blender-inspired tree of `Planogram > Shelves > Shelf > Rows > Product placements`. The user can select objects, rename shelves, expand/collapse groups, and remove a selected shelf or placement after confirmation where destructive.
- **Center: Shelf canvas.** A bright, uncluttered, scaled visual editor. Initially there are no shelf objects; show an empty-state message and **Add Shelf** button. When a shelf is created, show a white/light shelf rack with horizontal rows and product packshots. Render width, height, depth and row measurements clearly with cm units. Show empty rows and highlight a valid drop target.
- **Right: Context panel.** Tabs or clearly divided sections for **Properties** and **Product Library**. Provide the plus/add actions for creating shelves and products. When a shelf is selected, show shelf properties; when a product or placement is selected, show its corresponding product/placement properties. Keep essential actions easy to find rather than hidden in menus.

The editor must work with one or multiple shelf objects. A user can create two or three products quickly from seed items or use Add Product to create their own.

## 4. Product catalogue requirements

Each product record includes:

- Stable internal ID.
- SKU (required and unique).
- Product name (required).
- Category (optional).
- Image path (required for a newly created product; allow a bundled sample image to prefill seeded products).
- Width, height and depth in centimetres (positive numeric values).
- Price as a non-negative decimal number and currency (default display currency INR / ₹; make currency handling explicit).
- Created/updated timestamps.

Required behavior:

- **Add Product** opens a validated form with image upload/preview and all fields above.
- Support common raster uploads (JPEG, PNG, WebP) and enforce a reasonable upload size limit. Do not trust file extensions alone; validate MIME/content where practicable.
- On save, the product appears in Product Library and remains after page refresh, browser restart, and backend restart.
- Product Library supports search by name/SKU and category filtering if simple to implement.
- User can edit and delete catalogue items; prevent accidental deletion if a product is used in saved plans, or clearly explain the effect.
- Seed at least three sample products from `sample_assets/catalogue.sample.json` and the included image assets. Prefer all six. Their dimensions/prices are fictional and must be labeled sample data.

## 5. Shelf and planogram requirements

### Shelf object

Each shelf has a stable ID and at least:

- Name (e.g. Shelf 01).
- Width in cm.
- Total height in cm.
- Depth in cm.
- Row count.
- Optional bottom plinth/base-header enabled flag.
- Plinth height in cm when enabled.
- Ordered row metadata; allow equal row spacing as the default. Per-row height editing is optional if it does not destabilize the MVP.
- Created/updated timestamps.

Validation rules:

- Width, height and depth must be greater than zero.
- Row count must be an integer from 1 to 12 for this MVP.
- Plinth height cannot be negative and cannot exceed total shelf height.
- Adding, deleting, or changing row count must not silently lose placements. If a row containing products is to be removed, ask for confirmation or prevent the change until items are moved.

### Create and edit a shelf

- Initial canvas is empty; do not create a shelf automatically.
- **Add Shelf** creates a new selectable shelf object in the Outliner and renders it on the canvas.
- Selecting a shelf exposes its dimensions, row count and optional plinth in the properties panel.
- Support multiple separate shelves, each configurable independently.
- Use one consistent physical unit (cm) in the MVP.
- Show the visual scale / dimension annotations consistently. The shelf may scale to fit the canvas, but physical dimensions shown must remain tied to the saved numerical dimensions.

### Product placement / drag-and-drop

- A product in the Product Library can be dragged onto a shelf row; clicking a product and using an **Add to Shelf** action may be provided as an accessible alternative.
- Dragging a product again creates another placement (a new facing), unless an explicit quantity control is used; behavior must be consistent and documented.
- Product width determines horizontal space consumed and height determines its displayed physical height. Keep product aspect ratio. Depth is stored and included in the export even though the editor is front-facing 2D.
- Snap placements to their shelf row. Store their row index and horizontal offset in cm (not only pixel coordinates) so the exported planogram is independent of screen size.
- Show visible dimensions for the shelf and, when selected, the product/placement. The properties panel must display product width/height/depth.
- Prevent a placement from exceeding shelf usable width or overlapping another placement on the same row. Show a clear message if the product will not fit. Do not silently shrink physical dimensions to force a fit.
- Allow moving a placement between rows and reordering it horizontally. Keep positions deterministic after resize/refresh.
- Show a basic capacity indicator per row (used width / available width) and clearly indicate remaining width. This is a deterministic calculation, not an AI prediction.
- Keep placements associated with a specific shelf and row, and support deleting a placement without deleting the catalogue product.

### Save/load behavior

- User can create a named planogram, save changes, reopen it from Dashboard, and continue editing.
- Persist planograms, shelves, rows, product records, and placements in a local SQLite database via the backend. Store uploaded images as local files; keep relative file paths/metadata in the DB rather than storing large image binaries in SQLite.
- The SQLite database and uploads directory must be configurable and ignored by Git. Provide safe initial setup/migration/create-table logic.
- Save state must survive browser refresh and application restart. Do not rely on React component state or localStorage as the system of record. LocalStorage can be used only for minor UI preferences/drafts if there is an explicit reason.
- Make save state clear to the user (Saved / Unsaved changes / Saving / Save failed). Avoid claiming a save succeeded until the API confirms success.

## 6. Export requirements

The user must be able to export a saved planogram in two required formats:

1. **Visual export (PNG required; SVG acceptable as an additional or fallback format):** white shelf background, products, planogram title, shelf name, measurements in cm, row labels, SKU/name labels where legible, and the chosen physical dimensions. Export should be suitable for a report or mentor review.
2. **Structured JSON:** versioned schema with planogram ID/name, units, shelves, each shelf dimensions/row count/plinth settings, product catalogue identity and dimensions, and placements containing shelf ID, row index, SKU, x offset in cm and relevant product dimensions. Include `format_version`.

The JSON export must be stable and machine-readable, with a test confirming its required fields. Export must reflect saved/current data and handle an empty planogram with a helpful message or valid empty export.

A browser print view or PDF export is a bonus only if the two required exports and tests are solid.

## 7. Backend and persistence architecture

Recommended stack (use unless an existing repository already has a deliberate compatible choice):

- Frontend: Next.js + React + TypeScript + Tailwind CSS.
- Drag/drop: a maintained React drag-and-drop library such as `@dnd-kit`.
- Backend: Python + FastAPI + Pydantic + SQLAlchemy.
- Local database: SQLite.
- Backend tests: pytest and FastAPI TestClient / HTTPX.
- Frontend tests: Vitest + React Testing Library.
- Browser end-to-end tests: Playwright for the critical user journey.

Keep a small monorepo with separate `frontend/` and `backend/`. Use a modular monolith. Do not add authentication, cloud services, a queue, vector database, YOLO/CLIP/OCR, or microservices in this stage.

Recommended conceptual entities:

- `Product`: SKU, name, image_path, dimensions, price/currency.
- `Planogram`: name and timestamps.
- `Shelf`: planogram_id, name, dimensions, rows, plinth settings.
- `ShelfRow`: shelf_id, ordered/indexed row metadata (could be normalized or derived if carefully handled).
- `Placement`: shelf_id, row index, product_id, x_offset_cm and order/position data.

Use database constraints and service-level validation for unique SKU, foreign keys, positive dimensions, valid row index and non-overlapping placement. Keep business logic separate from API route functions. Do not treat pixel coordinates as saved physical coordinates.

## 8. Suggested API surface

The backend may adapt endpoint naming to an existing repository, but provide equivalent tested operations:

- `GET /health`
- `GET /api/v1/products`
- `POST /api/v1/products` (multipart image upload)
- `GET /api/v1/products/{id}`
- `PATCH /api/v1/products/{id}`
- `DELETE /api/v1/products/{id}`
- `GET /api/v1/planograms`
- `POST /api/v1/planograms`
- `GET /api/v1/planograms/{id}`
- `PATCH /api/v1/planograms/{id}`
- `DELETE /api/v1/planograms/{id}`
- `POST /api/v1/planograms/{id}/shelves`
- `PATCH /api/v1/shelves/{id}`
- `DELETE /api/v1/shelves/{id}`
- `POST /api/v1/shelves/{id}/placements`
- `PATCH /api/v1/placements/{id}`
- `DELETE /api/v1/placements/{id}`
- `GET /api/v1/planograms/{id}/export.json`

You may choose more cohesive nested routes. Document the final route list and schemas in the repository. Return clear validation errors for duplicate SKUs, invalid measurements, and out-of-bounds/overlapping placements.

## 9. Minimum folder structure

Keep structure proportionate to the first stage; do not create empty architectural layers without use:

```text
Tredence_H4ck/
├── AGENTS.md
├── README.md
├── .gitignore
├── docs/
│   ├── PRODUCT_SPEC.md
│   ├── USER_GUIDE.md
│   ├── API_CONTRACT.md
│   └── TESTING.md
├── sample_assets/
│   ├── catalogue.sample.json
│   ├── catalogue.sample.csv
│   ├── README.md
│   └── images/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/          # routes + schemas
│   │   ├── core/         # config, logging
│   │   ├── db/           # engine, session, models
│   │   ├── services/     # product, planogram, placement logic
│   │   └── storage/      # safe upload helpers
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── conftest.py
│   ├── pyproject.toml
│   └── .gitkeep # only if needed before package initialization
├── frontend/
│   ├── src/
│   │   ├── app/          # dashboard + planogram designer pages
│   │   ├── components/   # shared UI, shelf canvas, outliner
│   │   ├── features/     # products, planograms, placements
│   │   ├── lib/          # typed API client and validators
│   │   └── types/
│   ├── tests/
│   └── package.json
├── e2e/                  # Playwright critical flow
└── scripts/              # seed sample catalogue / dev helpers if needed
```

Adjust if the repository already has an established structure. Avoid duplicate config files or unnecessary placeholders. Keep sample assets in the repo; ignore runtime SQLite databases and user uploads.

## 10. Quality and testing requirements

Tests are part of the task, not a later optional task. Do not stop after producing a visually plausible frontend.

### Backend unit tests

- Product schema rejects empty name/SKU, duplicate SKU, negative price, zero/negative dimensions, unsupported image type and over-limit file.
- Shelf schema rejects zero/negative dimensions, invalid row counts and invalid plinth dimensions.
- Placement logic accepts a product that fits and rejects a placement that exceeds row width.
- Placement logic rejects overlapping placements and allows deterministic reorder/move between rows.
- Capacity calculation uses physical product width and shelf usable width, not CSS pixels.
- JSON export contains format version, cm units, shelf measurements, product SKU/dimensions, row index and horizontal offset.
- If rows are deleted/reduced, existing placements are handled safely and predictably.

### Backend integration tests

Use a temporary test SQLite database and temporary upload directory; never run integration tests against the developer's persistent local database.

- Create a product with image; GET it back and verify persisted metadata and image.
- Create a planogram and shelf, add placements, fetch the complete planogram and verify relationships.
- Update shelf dimensions/row count and verify validation behavior.
- Verify out-of-bounds/overlapping placement returns a documented 4xx error.
- Export JSON and verify schema and coordinates.
- Verify data remains available across separate API requests and database sessions.
- Verify delete behavior and friendly not-found responses.

### Frontend unit/component tests

- Empty designer shows no shelf by default and a working Add Shelf control.
- Add Product form validates fields and displays an image preview.
- Saved products appear in Product Library.
- Shelf properties reflect selected dimensions and row count.
- Product placement triggers the API and updates the visible row.
- API error shows readable feedback; save failure is not shown as success.
- Measurement labels are visible and use cm.

### End-to-end Playwright test

At minimum, automate this core journey against the actual frontend and backend:

1. Open the app and Dashboard.
2. Open Design Your Own Planogram.
3. Confirm the shelf canvas starts empty.
4. Add a shelf, set dimensions and row count.
5. Add or use a sample product and place it on a shelf row.
6. Save the planogram.
7. Reload the page and confirm shelf/product placement persisted.
8. Export structured JSON and assert it has shelf dimensions and placements.
9. Confirm the visual export can be downloaded or rendered through the export path.

The CI/test setup should run headlessly. Add stable `data-testid` or accessible labels where appropriate; avoid brittle selectors based on CSS classes.

### Required scripts and verification

Provide root-level documented commands, preferably via a root `Makefile` or scripts where cross-platform behavior is clear. At minimum document backend lint/test, frontend lint/typecheck/test/build, and E2E commands. Add CI only if it can be made reliable within this implementation stage; the local test commands are mandatory regardless.

After implementation, the agent must actually run the available tests, start the application if possible, execute the core journey, inspect browser/server logs, and report exact pass/fail outcomes. Never state tests pass unless commands actually ran. If a test cannot run, report the blocker and do not imply full verification.

## 11. Acceptance criteria / definition of done

- There are exactly two main navigation pages: Dashboard and Design Your Own Planogram.
- App uses the dark polished dashboard shell while shelf viewport is bright and legible.
- Planogram canvas is initially empty.
- Users can create multiple shelves and configure width/height/depth/rows and optional bottom plinth.
- Users can create products with image, name, unique SKU, dimensions and price; products persist in SQLite and images persist on disk.
- At least three sample products are available, preferably all six supplied sample items.
- Users can drag/drop products onto shelves, move products between rows, and see the fit/capacity feedback.
- Out-of-bounds and overlapping placements cannot be silently saved.
- Scene hierarchy lists planograms, shelves, rows and placements with selection.
- A named planogram can be saved and reopened after refresh/restart.
- Product, shelf and placement measurements are visible and represented in physical centimetres in stored data.
- User can download a visual planogram and a versioned JSON planogram export.
- User guide explains how to run the local stack and use the editor.
- Unit tests, integration tests and one critical end-to-end journey are implemented.
- Type checks, lint/build and test commands are run; failures are either fixed or clearly reported.
- No credentials, runtime DB files, uploaded user images, generated build folders or model weights are committed.

## 12. Out of scope for this stage

- YOLO/RT-DETR object detection.
- CLIP/embedding product recognition.
- OCR and shelf price-tag recognition.
- Comparison of a live shelf photograph to the planogram.
- AI-generated recommendations, compliance scores or out-of-stock inference.
- User accounts, cloud database, multi-user synchronization or cloud deployment.
- 3D shelf rendering or Blender-style 3D manipulation; the Outliner is a hierarchy UI only.
- Multi-store permissions, audit history and analytics beyond actual local dashboard counts.

## 13. Implementation approach

Build this incrementally. First inspect repository state, report a short plan, and create the agreed skeleton. Then implement vertical slices in this order:

1. Local app shell + health API + SQLite setup.
2. Product upload/catalogue CRUD + seeded sample items and tests.
3. Planogram/shelf CRUD + dimension/row editing and tests.
4. Shelf canvas/outliner + physical-unit layout model.
5. Drag-and-drop placements + fit/overlap validation and tests.
6. Save/load + Dashboard real data.
7. JSON and visual export.
8. Integration/E2E tests, usage docs, polish and regression pass.

Keep commits and PRs small, make no direct changes to protected branches, and do not silently change architecture. If time becomes constrained, complete the core save/load/placement/export journey before adding optional features.
