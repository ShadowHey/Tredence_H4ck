# ShelfSense AI — Technical Decisions & Architecture Rationale (Stage 1 MVP)

This document records the foundational technical and architectural decisions made during the design and implementation of the **ShelfSense AI Planogram Designer (Stage 1 MVP)**, structured stage-by-stage with the context, options considered, decisions made, and underlying reasoning.

---

## Stage 1: Repository Architecture & Service Boundary

### Decision 1.1: Modular Monolith vs. Distributed Microservices
- **Context**: The product specification required a local-first system with a frontend editor, backend persistence, and asset storage.
- **Decision**: Implemented a **modular monolith** structured as `frontend/` (Next.js), `backend/` (FastAPI), and `e2e/` (Playwright) in the same repository.
- **Reasoning**:
  - Eliminates network overhead, distributed failure modes, and deployment complexity during early prototyping.
  - Keeps data contracts strictly synchronized between frontend TypeScript types (`frontend/src/types/index.ts`) and backend Pydantic models (`backend/app/api/schemas/`).
  - Allows single-command orchestration via a root `Makefile` (`make backend`, `make frontend`, `make test`).

### Decision 1.2: Tech Stack Selection
- **Frontend**: Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4, `@dnd-kit`, `lucide-react`, `html-to-image`.
- **Backend**: Python 3.9+, FastAPI, Pydantic v2, SQLAlchemy 2.0, SQLite.
- **Reasoning**:
  - **FastAPI + Pydantic v2**: Provides high-performance async endpoints, automatic OpenAPI documentation (`/docs`), and compile-time request validation.
  - **Next.js App Router**: Provides modern layout routing, fast Turbopack compilation (1.8s build), and clean separation between `/` (Dashboard) and `/designer` (Planogram Studio).
  - **Tailwind CSS v4**: Zero-runtime stylesheet generation with instant design token customization for the dark charcoal theme.

---

## Stage 2: Physical Dimension Model over Screen Pixels

### Decision 2.1: Centimetres (`cm`) as the Canonical Unit of Truth
- **Context**: Conventional visual editors store element coordinates in pixels (`px`).
- **Decision**: All database entities (`Shelf`, `Product`, `Placement`), API payloads, collision checks, capacity gauges, and JSON exports strictly operate in physical centimetres (`cm`).
- **Reasoning**:
  - Screen pixel density and viewport sizes vary across displays (e.g., 1080p, 4K, retina laptops). Storing pixel coordinates would make planograms non-reproducible across different screen sizes.
  - Future compliance stages (Stage 2+) require real-world fixture measurements to compare against store camera imagery.
  - Frontend canvas rendering scales physical dimensions dynamically:
    $$\text{item\_width\_pct} = \frac{\text{product.width\_cm} \times \text{facing\_count}}{\text{shelf.width\_cm}} \times 100\%$$
    $$\text{left\_offset\_pct} = \frac{\text{placement.x\_offset\_cm}}{\text{shelf.width\_cm}} \times 100\%$$

---

## Stage 3: Persistence & Image Storage Architecture

### Decision 3.1: SQLite Database with Foreign Key Enforcement
- **Context**: Avoiding mock state or volatile `localStorage`.
- **Decision**: Relational database persistence using SQLite (`backend/shelfsense.db`) with SQLAlchemy declarative models, check constraints, and cascading deletes.
- **Reasoning**:
  - Zero-configuration local database requiring no cloud credentials or daemon services.
  - Fully transactional: changes made in the designer survive browser reloads, network disconnects, and backend process restarts.
  - Check constraints enforce positive widths, heights, depths, and row count ranges ($1 \le \text{row\_count} \le 12$) at the database layer.

### Decision 3.2: Disk-Based Upload Storage (`backend/uploads/`) with Relative DB Paths
- **Context**: Handling user-uploaded product images (JPEG, PNG, WebP, SVG).
- **Decision**: Files are streamed to disk in `backend/uploads/products/` with UUID-based collision-resistant filenames. The database stores clean relative paths (e.g. `uploads/products/a1b2c3d4.png`).
- **Reasoning**:
  - Storing multi-megabyte binary blobs inside SQLite causes database bloat and slow backup/query performance.
  - Fast static serving via FastAPI's `StaticFiles(directory=settings.UPLOADS_DIR)` mounted at `/uploads`.
  - Enforces 5MB size limit and validates MIME types (`image/jpeg`, `image/png`, `image/webp`, `image/svg+xml`).

---

## Stage 4: Collision Detection & Placement Fit Rules

### Decision 4.1: Deterministic 1D Interval Overlap Algorithm
- **Context**: A shelf row is a continuous horizontal span from $0$ to $\text{shelf.width\_cm}$. Products cannot overlap or exceed row boundaries.
- **Decision**: Implemented strict interval intersection validation in `backend/app/services/placement_service.py` with an epsilon tolerance ($\epsilon = 0.01\text{ cm}$):
  $$\text{item\_start} = x, \quad \text{item\_end} = x + (w \times \text{facing\_count})$$
  $$\text{Overlap occurs if } \max(x_A, x_B) < \min(\text{end}_A, \text{end}_B) - \epsilon$$
- **Reasoning**:
  - **Zero Overlap**: Real retail products cannot physically occupy the same shelf volume.
  - Actionable Error Feedback: Returns HTTP `422 Unprocessable Entity` with exact measurements (e.g. *"Cannot place 'Crispy Chips': width 14.0cm exceeds shelf width 100cm by 5.0cm"* or *"Overlaps with 'Oat Crunch Cereal' at 20.0cm - 28.0cm"*).
  - No silent shrinking: The application never shrinks an item to force it into a gap, ensuring physical accuracy.

### Decision 4.2: Safe Row Reduction & Width Reduction
- **Context**: A user may edit shelf properties and reduce rows (e.g., from 4 rows to 2 rows) or decrease shelf width.
- **Decision**: The backend service checks whether existing placements would be orphaned ($p.\text{row\_index} \ge \text{new\_row\_count}$) or truncated ($x + w > \text{new\_width}$). If so, the update is rejected with an actionable HTTP 422 error.
- **Reasoning**:
  - Protects users from accidental data loss during shelf redesigns.

---

## Stage 5: Visual Direction & Design System

### Decision 5.1: Fusion of the Four Design References
1. **MoEngage Dark SaaS Shell**:
   - Deep charcoal background (`#0d0f12`), card surfaces (`#1a1e26`), subtle dividers (`#262b36`), and warm amber accents (`#f59e0b`).
   - Clean vertical sidebar navigation with active pill indicators.
   - Dashboard KPI metric cards deriving real counts from SQLite (`total_planograms`, `total_products`, `total_shelves`, `total_placements`).
2. **Blender Outliner**:
   - Left-side hierarchical scene tree: `Planogram > Shelves > Shelf Unit > Rows > Product Placements`.
   - Node selection bidirectional sync: clicking a placement in the outliner highlights it on the canvas and loads its properties in the context panel.
3. **Formal Planogram Canvas**:
   - Bright, high-contrast white shelf canvas (`#ffffff`) surrounded by the dark shell.
   - Formal side elevation ruler with blue bracket lines indicating per-row heights in cm and bottom plinth fixture height.
   - Top usable width dimension line with left (0 cm) and right ($W$ cm) bounds.
4. **Retail Shelf Planner**:
   - Horizontal shelf slats, clean product packshots preserving natural aspect ratio (`object-contain`), SKU badges, and row capacity progress bars.

---

## Stage 6: Two-Way Export Engine

### Decision 6.1: Client-Side High-Resolution PNG Visual Export
- **Context**: Users need exportable planogram diagrams for store managers, mentors, and compliance reviews.
- **Decision**: Implemented client-side DOM-to-canvas rendering via `html-to-image` at $2\times$ pixel ratio with a clean white background.
- **Reasoning**:
  - Renders the exact visual planogram with high-DPI text, dimension brackets, row slats, and product artwork without server-side headless browser overhead.

### Decision 6.2: Machine-Readable Versioned JSON Schema (`v1.0`)
- **Context**: Future AI compliance systems (Stage 2+) need structured layout coordinates.
- **Decision**: Implemented `GET /api/v1/planograms/{id}/export.json` delivering `PlanogramExportJSON` with `format_version: "1.0"` and `unit: "cm"`.
- **Reasoning**:
  - Stable contract: includes planogram metadata, shelf dimensions, row counts, plinth settings, unique product SKUs, product dimensions, and placement offsets in cm.

---

## Stage 7: Automated Testing & Verification Architecture

### Decision 7.1: Isolated Temporary Databases for Backend Tests
- **Context**: Running backend tests against the developer database corrupts local user data.
- **Decision**: `backend/tests/conftest.py` spins up a fresh temporary SQLite file database (`test_*.db`) and temporary upload directory in `/tmp` for each test session, wiping it upon teardown.
- **Reasoning**:
  - Guarantees 100% test reproducibility with zero side-effects on developer data.

### Decision 7.2: Three-Tier Testing Pipeline
1. **Backend Tests (pytest)**:
   - Unit tests: Schema constraints, zero/negative validation, placement collision math, capacity calculations, JSON export schema.
   - Integration tests: Product CRUD with multipart image upload, duplicate SKU 409 rejection, planogram/shelf/placement lifecycles, and foreign-key cascading.
2. **Frontend Tests (Vitest + React Testing Library)**:
   - Initial empty canvas state, Add Shelf modal, Product form validation, Dimension labels in cm, Context panel tab switching.
3. **End-to-End Tests (Playwright)**:
   - Critical path: Open Dashboard -> Create planogram -> Add shelf & rows -> Place product -> Save -> Reload -> Assert persistence -> Export JSON & PNG.

---

## Stage 8: Dynamic Elevation Scale & Layout Architecture

### Decision 8.1: Unified Row Pairing Architecture for 1:1 Elevation Scaling
- **Context**: When the number of shelf rows was increased (e.g. from 4 to 8 or 12 rows), the previous design used two disconnected flex columns—one for the side ruler and one for the shelf bay fixture. Because the center bay rows had `min-h-[90px]` and inter-row gaps while the left ruler was an unconstrained flex column, the left elevation brackets compressed into the top third of the canvas, becoming misaligned with their corresponding shelf rows and leaving the plinth bracket floating mid-fixture.
- **Decision**: Re-architected the shelf canvas from disconnected sibling columns to a **Unified Row Pairing Architecture**:
  1. **Top Measurement Header Bar**: A single horizontal row pairing the left Elevation Header (`w-36 shrink-0 h-6`) with the Usable Width Dimension Ruler (`flex-1 h-6`), establishing a unified horizontal reference line.
  2. **Row Pair Wrapper**: Each row iteration (`rIdx` from `0` to `activeShelf.row_count - 1`) renders a synchronized row pair wrapped in `<div className="flex items-stretch gap-3 min-h-[90px]">`:
     - **Left Column (`w-36 shrink-0`)**: Dedicated elevation dimension bracket featuring the row identifier badge (`R{rIdx + 1}`), vertical clearance indicator with arrows (`↕ {rowHeightCm.toFixed(1)} cm`), and cumulative base elevation from the floor/plinth (`Elev: {baseElevationCm.toFixed(1)} cm`).
     - **Right Column (`flex-1`)**: Drop zone, placed product packshots with aspect ratio preservation, SKU badges, and capacity indicators.
  3. **Bottom Plinth Pair**: A synchronized bottom row pairing the left Plinth Bracket (`w-36 shrink-0 h-8`) directly alongside the physical Base Plinth Fixture (`flex-1 h-8`).
  4. **Natural Container Growth**: Removed `justify-between` and 0-basis flex constraints from the canvas fixture container, allowing the fixture to naturally enclose any number of rows (1 to 12) without overflowing or clipping the footer.
- **Reasoning**:
  - **Mathematical Guarantee**: Because CSS `items-stretch` operates on the common row container, the elevation bracket is geometrically constrained to equal the exact pixel height of the shelf row, regardless of viewport size, row count, or packshot heights.
  - **Instant Visual Clarity**: In formal CAD and retail planogramming conventions (e.g. JDA/Spaceman), each shelf level requires immediate visual proximity to its clearance height and base elevation.
  - **Synchronized Interaction**: Hovering over or dragging onto a row highlights both the drop bay and the left elevation bracket simultaneously in amber (`border-amber-500 bg-amber-50`), giving the user immediate visual confirmation of the target row.
  - **Zero Regression**: Verified with automated Playwright bounding-box comparisons (`Math.abs(bracket.y - bay.y) <= 1.5px`) across 8-row shelves and 100% passing test suites across frontend, backend, and E2E.

---

## Summary of Architectural Invariants

| Principle | Invariant |
| :--- | :--- |
| **Units** | All database values, APIs, and exports use **centimetres (`cm`)**, never pixels. |
| **Collision** | Overlapping placements on the same row are **strictly rejected with HTTP 422**. |
| **Persistence** | **SQLite and local disk** are the sole source of truth; no volatile mock state. |
| **Safety** | Destructive actions (reducing rows, deleting products in use) are **guarded and validated**. |
| **Aesthetics** | **Dark MoEngage shell** framing a **bright high-contrast white canvas** with formal dimension lines. |
| **Scale Alignment** | Elevation brackets and shelf rows share a **Unified Row Pairing structure**, guaranteeing 1:1 vertical alignment across any row count (1 to 12). |

