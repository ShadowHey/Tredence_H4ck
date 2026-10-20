# ShelfSense AI — Planogram Designer User Guide (MVP)

ShelfSense AI Stage 1 is a local-first retail planogram designer and catalogue management platform. It allows retail space planners to configure real-world physical shelves in centimetres (`cm`), maintain product catalogues with accurate packshot artwork, arrange items across shelf rows with collision prevention, save arrangements to persistent SQLite storage, and export both visual and machine-readable planograms.

---

## 1. Quick Start & Local Setup

### Prerequisites
- **Python**: 3.9+ (with `venv`)
- **Node.js**: v20+ or v22+
- **npm**: 10+

### Option A: Using the Makefile (Recommended)

1. **Install dependencies**:
   ```bash
   make install
   ```

2. **Seed sample product catalogue** (copies the 6 unbranded packshot assets):
   ```bash
   make seed
   ```

3. **Start the backend server** (FastAPI on `http://localhost:8000`):
   ```bash
   make backend
   ```

4. **In a new terminal, start the frontend** (Next.js on `http://localhost:3000`):
   ```bash
   make frontend
   ```

5. Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 2. Page Navigation & Layout

ShelfSense AI provides two primary navigation pages accessible from the left sidebar:

### A. Dashboard (`/`)
- **Real SQLite KPI Cards**: Displays live counts of saved planograms, catalogue products, total shelves designed, and total product facings.
- **Recent Planograms**: List of previously saved planograms with shelf count, product count, updated timestamp, and an **Open** action.
- **Empty States**: If no planograms or products exist, helpful call-to-actions guide you to create your first planogram or seed the sample SKUs.

### B. Design Your Own Planogram (`/designer`)
The workspace uses a three-panel studio layout:
1. **Left: Blender-inspired Scene Hierarchy (Outliner)**:
   - Nested tree: `Planogram > Shelves > Shelf Unit > Rows > Product Placements`.
   - Node selection, expand/collapse chevrons, and item deletion controls.
2. **Center: Bright Shelf Canvas**:
   - High-contrast white canvas with formal planogram dimension brackets (side elevation ruler for row heights and plinth, top usable width ruler in cm).
   - Horizontal shelf slats, drop zones, packshot graphics with true aspect ratios, and live capacity progress bars.
3. **Right: Context Panel**:
   - **Properties Tab**: Real-time inspection and editing for the selected shelf or placement.
   - **Product Library Tab**: Searchable, categorised catalogue cards ready for dragging onto shelf rows.

---

## 3. Product Catalogue Management

### Creating a Custom Product
1. Open the **Designer** and switch to the **Product Library** tab on the right panel.
2. Click **Add Product** to open the modal.
3. Upload front-facing product artwork (JPEG, PNG, WebP, or SVG, up to 5MB).
4. Enter:
   - **Unique SKU** (e.g. `BEV-COLA-01`)
   - **Product Name**
   - **Category** (Beverages, Snacks, Breakfast, Home Care, etc.)
   - **Price** (in ₹ INR)
   - **Physical Dimensions in cm** (`Width`, `Height`, `Depth`)
5. Review the live packshot preview and click **Save to Product Library**.
6. The product is immediately saved to SQLite and its image file is stored locally in `backend/uploads/products/`.

### Bundled Sample Items
The application includes six unbranded sample products with SVG and PNG packshots:
- `DEMO-DRK-001`: Citrus Sparkling Drink (6.5cm × 12.2cm × 6.5cm)
- `DEMO-DRK-002`: Orange Juice Carton (6.0cm × 19.0cm × 5.0cm)
- `DEMO-FOD-001`: Oat Crunch Cereal (8.0cm × 22.0cm × 4.5cm)
- `DEMO-SNK-001`: Crispy Chips Pouch (14.0cm × 20.0cm × 5.0cm)
- `DEMO-HOM-001`: Fresh Laundry Liquid Bottle (9.0cm × 25.0cm × 6.0cm)
- `DEMO-HOM-002`: Daily Clean Spray Bottle (7.0cm × 24.0cm × 5.0cm)

---

## 4. Shelf Configuration

1. On first opening the designer, the shelf canvas starts empty.
2. Click **Add Shelf to Canvas** or **Add Shelf** in the header.
3. Configure:
   - **Name**: e.g. `Shelf 01` or `Gondola Bay A`
   - **Usable Width (cm)**: e.g. `120.0 cm`
   - **Total Height (cm)**: e.g. `180.0 cm`
   - **Depth (cm)**: e.g. `40.0 cm`
   - **Rows**: 1 to 12 rows (vertical spacing is automatically computed)
   - **Bottom Plinth**: Optional ground fixture elevation (e.g. `15.0 cm`)
4. Click **Add Shelf to Canvas**. The shelf unit is rendered with physical measurement brackets.

---

## 5. Drag-and-Drop Placement & Physical Rules

### Placing Products
- **Drag & Drop**: Click and drag any product card from the **Product Library** onto any shelf row.
- **Accessible Quick Add**: Click the `+` button on a product card to place it on the active shelf.

### Physical Coordinate & Collision Rules
- **Physical Coordinates**: All placements store horizontal offset `x_offset_cm` from the left edge of the shelf.
- **Zero Overlap**: The backend strictly validates that no two placements on the same row collide ($[x_1, x_1 + w_1]$ does not intersect $[x_2, x_2 + w_2]$).
- **Usable Width**: Total placed width cannot exceed `shelf.width_cm`. If an item exceeds remaining space, an informative error explains the overflow.
- **Facings Multiplier**: In the Properties panel, increase the facing count to place multiple adjacent units of the product.
- **Safe Row Reduction**: Decreasing shelf rows will not silently delete products. If a row has items, the change is blocked until items are moved or deleted.

---

## 6. Saving & Reopening (Persistence)

1. The planogram title can be renamed at any time from the top header.
2. Click **Save** in the top header. The save badge updates:
   - `Saving to SQLite...`
   - `Saved` (green checkmark)
3. Return to the **Dashboard** at any time. The saved planogram will appear under **Recent Planograms**.
4. Refreshing the browser or restarting the backend preserves all shelves, dimensions, products, and placements.

---

## 7. Two-Way Exports

Click the **Export** button in the top header to access:

### 1. Visual PNG Export
- Click **Download PNG** to generate a clean, high-resolution rendering of the shelf layout.
- Includes planogram title, shelf name, formal dimension ruler in cm, row labels, and product packshots.

### 2. Structured JSON Export
- Click **Download JSON** to fetch the machine-readable planogram file (`GET /api/v1/planograms/{id}/export.json`).
- Adheres to standard schema:
  - `format_version: "1.0"`
  - `unit: "cm"`
  - Shelf dimensions (`width_cm`, `total_height_cm`, `depth_cm`, `row_count`, `plinth_height_cm`)
  - Product catalogue references with physical dimensions
  - Placements with `x_offset_cm`, `facing_count`, and `row_index`.

---

## 8. Current Stage Boundaries

- **In Scope**: Planogram editor, physical cm layout engine, zero-overlap validation, product catalogue, image file persistence, SQLite database, visual & JSON exports.
- **Out of Scope (Stage 2+)**: Computer vision shelf auditing, live photograph compliance scoring, YOLO/RT-DETR object detection, CLIP product embeddings, OCR price-tag reading.
