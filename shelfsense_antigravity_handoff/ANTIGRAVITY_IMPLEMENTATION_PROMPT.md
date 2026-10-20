# Antigravity Implementation Prompt — ShelfSense AI Planogram Designer MVP

You are working in the existing `Tredence_H4ck` repository. Implement the **first usable version** of ShelfSense AI described in `PRODUCT_SPEC.md`. The user will also attach four screenshots in Antigravity:

1. Retail Shelf Planner: use for product arrangement across shelf rows.
2. A formal planogram page: use for dimension lines, shelf labels and exportable layout conventions.
3. MoEngage analytics dashboard: use for the dark premium SaaS shell, sidebar, cards, hierarchy and restrained color palette.
4. Blender Outliner: use for the left-side nested scene hierarchy of planogram > shelves > rows > product placements.

Read `AGENTS.md`, `README.md`, `PRODUCT_SPEC.md`, and `sample_assets/README.md` before you start. Treat `PRODUCT_SPEC.md` as the requirements source of truth. Treat the screenshots as visual references, not images to embed as product assets. If the repository already has code, inspect it and preserve unrelated work.

## Desired result

Build a real local full-stack application, not a static mockup. It must have exactly two primary navigation pages for this stage:

- **Dashboard**: actual counts and recently saved planograms from SQLite, plus a create/open planogram path. Include useful empty states; do not fake business analytics.
- **Design Your Own Planogram**: a functional shelf editor with an initially empty canvas, Add Shelf, Add Product, a hierarchy/outliner panel, a bright shelf canvas with physically meaningful dimensions, product drag-and-drop, a context/properties panel, persistence, and exports.

Design direction: dark charcoal outer application shell inspired by the MoEngage screenshot, with clear typography, thoughtful spacing, muted surfaces, and one warm accent. The shelf canvas must be bright/white and visually legible with clear measurement annotations. Use a clean responsive desktop-first layout. Show product names/SKUs and physical measurements in cm. The layout may scale to fit the viewport but saved layout coordinates and capacity calculations must use physical dimensions, not pixel measurements.

## Implementation stack

Unless the repository has an existing deliberate compatible setup, use:
- Frontend: Next.js + React + TypeScript + Tailwind CSS.
- Drag-and-drop: `@dnd-kit` or an equally maintained library.
- Backend: FastAPI + Pydantic + SQLAlchemy.
- Local persistent database: SQLite.
- Product image uploads: local file storage with relative paths in SQLite.
- Backend testing: pytest + FastAPI TestClient/HTTPX.
- Frontend unit/component testing: Vitest + React Testing Library.
- Critical browser flow: Playwright.

Keep a modular monolith in the same repository. Do not add authentication, cloud infrastructure, queues, object detection, CLIP, OCR or AI compliance logic at this stage. Do not install redundant libraries without a reason.

## Must-have functional behavior

1. On first opening the designer, the shelf canvas is empty and asks the user to add a shelf.
2. Add Shelf creates a selectable shelf node in the outliner and a visible shelf in the canvas.
3. A shelf supports name, width cm, total height cm, depth cm, row count (1-12) and optional bottom plinth/base-header with a height. All visible measurements and editor properties must agree with stored dimensions.
4. Product creation supports product image, name, unique SKU, width/height/depth in cm, price and currency. Include preview, validation, friendly errors, and persistent save. Seed at least three sample products, preferably all six from `sample_assets/catalogue.sample.json` and `sample_assets/images/`.
5. Users can drag a catalogue product to a row. Dropping creates a placement; dragging it again creates another facing. Support moving placements between rows and horizontal ordering. Product width controls occupied row width; product height influences its visual display while preserving aspect ratio. Product depth is recorded even though this editor is front-facing 2D.
6. Use snapping/physical coordinates. Reject overlap or a placement beyond available row width; explain why instead of silently shrinking items. Show row capacity/used width in cm.
7. Outliner tree represents Planogram > Shelves > Rows > Product placements, supports selection and expand/collapse, and updates with data changes. Allow adding multiple shelves.
8. Save a named planogram, reopen it from Dashboard, refresh or restart the app, and find products/shelves/placements intact. SQLite is the source of truth; React state/localStorage alone is not persistence. Uploaded image files must persist on disk.
9. Provide visual export (PNG required; SVG may be supported) showing the shelf layout and dimensions, plus a versioned JSON export containing shelf dimensions and placement coordinates in cm.
10. Provide friendly validation, loading/saving states, no-data states and API error messages.
11. Write a user guide with setup, running the two services, sample-data behavior, creating products/shelves, drag/drop, save/reopen, exporting, tests, and known limitations.

## Do not skip tests

Create and execute:
- Backend unit tests for product/shelf validation, capacity calculations, fit/no-fit, overlap prevention, row changes, coordinate stability and JSON export schema.
- Backend integration tests for product/image CRUD, planogram/shelf/placement CRUD, persistence across API requests, invalid/out-of-bounds placement errors and exports. Use a temporary test DB and temporary uploads directory; never test against a developer database.
- Frontend tests for initial empty canvas, add-shelf flow, product form validation/preview, properties measurements, placing a product, and visible API/save errors.
- A Playwright end-to-end scenario: open app > create/open planogram > add shelf and rows > place a sample product > save > reload > verify the placement persisted > export JSON and visual planogram.

Add stable accessible labels or test IDs as needed. Test business rules independently of the browser. Do not make core unit tests download models or call external services.

## Work style: inspect, plan, then implement

1. Inspect the current repository, branch and Git status. Do not reset, switch branches, commit, push, or change branch-protection settings.
2. Summarize the current state and present a staged implementation plan before substantial code changes.
3. Implement in vertical slices in this order: app shell + health/DB; product catalogue + assets; shelf/planogram CRUD; canvas/outliner; drag-drop/fit rules; save/load/dashboard; exports; tests/docs/polish.
4. After each slice, run relevant checks before moving on. Keep the API contract consistent between frontend and backend. Document routes/schema in `docs/API_CONTRACT.md`.
5. If requirements are ambiguous, use the explicit rules in `PRODUCT_SPEC.md`. If a critical ambiguity remains, ask one concise question before making a destructive or architecture-changing decision.
6. Review your own `git diff` for accidental changes, hardcoded paths, unvalidated inputs, swallowed errors, broken types and secrets.
7. If time or context limits prevent full completion, preserve a runnable app and complete the core journey first. Do not pretend unfinished functionality is implemented.

## Required final verification and report

Before presenting the result:
- Run backend lint/format/tests.
- Run frontend lint, TypeScript, tests and production build.
- Run the Playwright critical path if the environment supports it.
- Start the app and check browser/server logs where possible.
- Inspect the actual UI, preferably with a browser screenshot, at desktop width and a narrower viewport.
- Run `git diff --check` and inspect `git diff --stat` plus the full diff.
- Fix failures when possible; list blocked checks separately.

Finish with a concise report containing: implemented features, architecture and folder tree, setup/run commands, test commands and exact pass/fail outcomes, files created/modified, known limitations, and the next recommended task. Never report a command or test as passing unless it actually ran and passed. Do not commit or push changes; leave the working tree for developer review.
