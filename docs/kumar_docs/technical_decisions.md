# Kumar Saurav's Architecture Decision Records (ADRs)

---

### [2026-10-21 03:45 IST] Manual Product Addition Modal with Full Database Fields
- **Commit**: [`9c3118a`](https://github.com/ShadowHey/Tredence_H4ck/commit/9c3118a)
- **Status**: Implemented & Verified in Production

#### 1. Context & Problem Statement
Users in the planogram designer needed to add custom catalog items on the fly without having to use external CLI scripts or seed endpoints. Creating a product requires complete physical dimensions (width, height, depth in `cm`) and packshot images to calculate row capacities and collision geometry accurately.

#### 2. Options Considered
- **Option 1**: A minimal modal requiring only Name and Price.
  - *Cons*: Causes backend 422 errors because physical dimensions (`width_cm`, `height_cm`, `depth_cm`) are mandatory invariants for planogram collision detection.
- **Option 2 (Chosen)**: A comprehensive modal (`AddProductModal.tsx`) with full validation of all physical dimensions, category presets, and an automated SVG packshot fallback.

#### 3. Final Technical Decision & Rationale
- **Dynamic SVG Packshot Fallback**: If the user does not upload a custom packshot file, client-side vector synthesis creates a crisp, category-colored SVG packshot encoding the product SKU and dimensions directly into the graphic.
- **Instant Shelf Availability**: When `api.createProductMultipart` returns the created product from SQLite, it is immediately prepended to the catalog state, allowing the user to drag-and-drop it onto a shelf immediately.

---

### [2026-10-20 22:30 IST] Shelf Row Headroom Padding & Planogram Deletion
- **Commit**: [`b9172cd`](https://github.com/ShadowHey/Tredence_H4ck/commit/b9172cd)
- **Status**: Implemented & Verified in Production

#### 1. Context & Problem Statement
In real-world retail shelves, products require physical clearance (headroom) above their top edge so shoppers can reach in and grab them. Displaying products flush against the upper shelf plank created an unrealistic representation. Additionally, users needed an explicit delete action for obsolete planograms.

#### 2. Final Technical Decision & Rationale
- **Headroom Calculation**: Implemented minimum row headroom padding (`+ 2.0cm` clearance above the tallest placed item) in `ShelfCanvas.tsx` to ensure realistic spacing.
- **Planogram Deletion**: Added a delete button with double-confirmation dialog on both the main dashboard cards and the designer top bar.
