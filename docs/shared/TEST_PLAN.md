# ShelfSense AI — Acceptance and Regression Test Plan

## Local verification checklist

### Functional smoke tests
- [ ] First visit to Planogram Designer shows an empty canvas and Add Shelf action.
- [ ] Add Shelf creates an outliner node and a visible shelf with measurement labels.
- [ ] Update width/height/depth/row count; the canvas and API response agree.
- [ ] Add Product with image, name, unique SKU, dimensions and price.
- [ ] Saved Product appears in the library after browser refresh.
- [ ] Duplicate SKU is rejected with a useful error.
- [ ] Drag/drop a product into a row; selected placement shows width/height/depth and row.
- [ ] Repeated drag creates another facing, consistent with documented behavior.
- [ ] A product wider than remaining row space is rejected; no layout corruption occurs.
- [ ] Overlapping placements are rejected or normalized by a documented deterministic rule.
- [ ] Save, navigate away, reopen and refresh: the layout remains intact.
- [ ] Dashboard totals and recent plans reflect real persisted data.
- [ ] Exported JSON is valid and includes format version, units, shelves, dimensions, SKUs and placement offsets in cm.
- [ ] Visual export includes shelf geometry, products, row labels and dimensions.
- [ ] Delete/row reduction cannot silently orphan or drop existing placements.

## Backend unit test ideas

1. Product schema validation: SKU/name required, dimensions > 0, price >= 0.
2. SKU uniqueness service/database constraint.
3. Shelf dimension and row-count validation (1..12).
4. Plinth height cannot exceed shelf height.
5. Capacity calculation uses cm values and accounts for occupied width.
6. Placement accepted when fully inside row.
7. Placement rejected when beyond row width or overlapping another placement.
8. Moving between rows updates coordinates while preserving product identity.
9. JSON export uses consistent units and stable field names.
10. Row deletion/reduction has explicit safe behavior.

## Backend integration test ideas

Use a temporary SQLite database and temporary media directory for each test session.

1. Product upload -> database record -> GET response -> uploaded file exists.
2. Duplicate SKU returns 409 or another documented 4xx response.
3. Create planogram -> create shelf -> add placement -> fetch planogram nested state.
4. Update shelf dimensions, verify valid placements remain within bounds or update is rejected.
5. Out-of-bounds placement returns 422/409 with an actionable validation message.
6. Delete product/shelf/planogram follows documented foreign-key behavior.
7. Export JSON endpoint returns `application/json` with expected schema.
8. Persistence verified across API requests and independent DB sessions.

## Frontend component tests

1. Designer empty state contains Add Shelf; no default shelf is fabricated.
2. Product form required fields, positive dimensions and image preview.
3. Shelf inspector displays actual physical dimensions and row count.
4. Product library renders sample items from API state.
5. Placement success updates the canvas and outliner.
6. Placement error is shown to the user; no false success state.
7. Save state indicates loading/saved/failed correctly.
8. Dashboard KPI counts and recent plans come from API data.

## Playwright end-to-end critical path

Use accessible names or stable `data-testid` hooks. Start frontend and backend with an isolated test database.

1. Navigate to Dashboard and then Design Your Own Planogram.
2. Assert the canvas is empty.
3. Add a shelf, set width/height/depth, and choose at least two rows.
4. Use a seeded product or create one through the form.
5. Place it on row 1 and confirm the product appears.
6. Save under a planogram name.
7. Reload and confirm shelf and placement persistence.
8. Download JSON; parse it and assert the selected SKU, dimensions and placement offset exist.
9. Trigger visual export and assert a non-empty file is downloaded.

## Required reporting from the coding agent

The agent should report the exact commands executed and actual outcomes for backend tests, frontend tests, type checking, lint, production build, and E2E. It must label tests that were not run as **not run** and explain the blocker. It must not replace genuine tests with screenshots alone.
