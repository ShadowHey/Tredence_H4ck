# ShelfSense AI — Universal Team Contributions Registry

**Single Source of Truth for Team Work & Feature Execution**  
This document is automatically updated upon every feature or fix commit. It informs all team members and AI agents **who made what**, **when it was made**, **what files were affected**, and **exact commands to run/test the feature**.

---

## 1. Quick Overview Ledger

| Date & Time | Contributor | Feature / Fix | Commit | How to Run / Test | Summary of What Was Done | Files Affected |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `2026-10-21 22:45 IST` | **Dhruv** | YOLO Cutout Extraction, Visual Clustering & 4-Col Analysis | `8a0b94e` | `backend/.venv/bin/pytest backend/tests/ -v && npm test --prefix frontend` | Cutout extraction into products/shelves/empty_spaces, batched CLIP embeddings, intra-shelf clustering, strict >= 95% catalog matching, Cutouts modal, and 4-column Analysis Table | 13 files (`backend/*`, `frontend/*`) |
| `2026-10-21 15:05 IST` | **Dhruv** | Shelf-Linked Image Intake & Annotated Outputs | `30474fc` | `backend/.venv/bin/pytest backend/tests -v` | Added persistent one-image-at-a-time shelf-photo intake, serial CV processing, annotated outputs, ZIP export, and UI/E2E coverage | 15 files (`backend/*`, `frontend/*`, `e2e/*`) |
| `2026-10-21 14:55 IST` | **Dhruv** | Canonical Demo Asset Cleanup | `c104bb2` | `diff -qr sample_assets shelfsense_antigravity_handoff/sample_assets` | Removed the duplicate handoff catalogue and made root `sample_assets/` the only canonical demo asset source | 16 files (`shelfsense_antigravity_handoff/*`) |
| `2026-10-21 07:00 IST` | **Dhruv** | Unified Root Logging & Real-Time Job Streamer | `19710ad` | `python logs/log_collector.py --follow` | Root `logs/logs.txt`, background job timing, HTTP middleware & frontend log ingestion | 10 files (`logs/*`, `backend/*`, `frontend/src/lib/logger.ts`, modals) |
| `2026-10-21 06:18 IST` | **Dhruv** | CLIP ViT-B/32 Vector Embeddings & Inspection CLI | `38b2583` | `backend/.venv/bin/python backend/scripts/inspect_embeddings.py --list` | Automated 512-dim normalized CLIP vector generation on product creation, backfill, & CLI | 8 files (`models.py`, `database.py`, `embedding_service.py`, `inspect_embeddings.py`, unit tests) |
| `2026-10-21 03:45 IST` | **Kumar Saurav** | Manual Product Addition Modal with Full Database Fields | `9c3118a` | Open UI $\rightarrow$ Products Library $\rightarrow$ Click **"+ Add Product"** | Full physical dimension form (cm), SVG auto-generation fallback, instant shelf placement availability | `frontend/src/components/designer/AddProductModal.tsx`, `ContextPanel.tsx`, `ShelfCanvas.tsx` |
| `2026-10-20 22:30 IST` | **Kumar Saurav** | Shelf Headroom Padding & Planogram Deletion | `b9172cd` | Open Designer $\rightarrow$ Place product $\rightarrow$ Observe row padding; Delete planogram button | Enforces row minimum height with headroom padding and auto-shifts subsequent items on delete | `ShelfCanvas.tsx`, `Dashboard.tsx`, `Outliner.tsx` |

---

## 2. Detailed Contribution Records
 
### [2026-10-21 22:45 IST] YOLO Cutout Extraction, Semantic Clustering & 4-Column Analysis Table
- **Contributor**: Dhruv
- **Commit**: [`8a0b94e`](https://github.com/ShadowHey/Tredence_H4ck/commit/8a0b94e)
- **Summary of What Was Done**:
  - Implemented automatic YOLO bounding box cropping into 3 categorized directories: `products/`, `shelves/`, and `empty_spaces/` stored under `uploads/image_processing/outputs/{job_id}/cutouts/`.
  - Added fast batched PyTorch CLIP inference (`compute_image_embeddings_batch`), achieving ~15.6ms per crop and embedding 150+ crops in under 2.5 seconds.
  - Implemented intra-shelf visual clustering with cohesion threshold $\tau = 0.88$ to group identical facings on the shelf.
  - Implemented semantic catalog comparison against SQLite `products.embedding` enforcing strict $\ge 95\%$ confidence cutoff (`CATALOG_MATCH_THRESHOLD = 0.95`).
  - Created interactive `CutoutViewerModal` component with 3 distinct tabs (`Products`, `Shelves / Rows`, `Empty Spaces`), confidence badges, row tags, and crop inspection zoom.
  - Implemented top-level `/analysis` page with active shelf card, metric badges, output switcher, and the strict **4-column table**:
    - **Col 1: Similar Objects** (horizontal thumbnail preview/cluster with zoom click).
    - **Col 2: Similarity Percentage** (cluster cohesion score pill with visual meter).
    - **Col 3: Is object similar to someone in the product catalog?** (strictly `Yes` with green check or `No` with gray cross).
    - **Col 4: Similar Product** (if `Yes` and $\ge 95\%$, renders catalog packshot image, name, SKU, category, and price; if `No`, strictly displays NO product image).
  - Added unit test suites covering all backend routes and frontend components (35 backend tests + 17 frontend tests all passing).
- **How to Run / Test**:
  ```bash
  # 1. Run all backend tests
  backend/.venv/bin/pytest backend/tests/ -v

  # 2. Run frontend unit tests
  npm test --prefix frontend

  # 3. Build frontend bundle
  npm run build --prefix frontend

  # 4. Open in browser
  # Navigate to http://localhost:3000/outputs -> Click any shelf image card -> View Cutouts Inspector modal
  # Navigate to http://localhost:3000/analysis -> View 4-Column Table, filter pills, and crop zoom
  ```
- **Files Affected**:
  - `backend/app/services/cutout_service.py` *(New)*
  - `backend/app/services/embedding_service.py` *(Modified)*
  - `backend/app/services/image_processing_service.py` *(Modified)*
  - `backend/app/api/schemas/image_processing.py` *(Modified)*
  - `backend/app/api/routes/image_processing.py` *(Modified)*
  - `backend/tests/unit/test_cutouts_and_analysis.py` *(New)*
  - `frontend/src/types/index.ts` *(Modified)*
  - `frontend/src/lib/api.ts` *(Modified)*
  - `frontend/src/components/shell/Sidebar.tsx` *(Modified)*
  - `frontend/src/components/outputs/CutoutViewerModal.tsx` *(New)*
  - `frontend/src/app/outputs/page.tsx` *(Modified)*
  - `frontend/src/components/analysis/AnalysisTable.tsx` *(New)*
  - `frontend/src/app/analysis/page.tsx` *(New)*
  - `frontend/tests/analysis-and-cutouts.test.tsx` *(New)*

### [2026-10-21 15:05 IST] Shelf-Linked Image Intake & Annotated Outputs
- **Contributor**: Dhruv
- **Commit**: [`30474fc`](https://github.com/ShadowHey/Tredence_H4ck/commit/30474fc)
- **Summary of What Was Done**:
  - Added Input Images and Outputs navigation pages, with a user required to select one planogram and one shelf before queuing each image.
  - Added SQLite input, job, and output records; a serial/recoverable worker that invokes the isolated image-parsing pipeline; source/shelf snapshots; annotation/JSON storage; ZIP export; and safe deletion.
- **How to Run / Test**:
  ```bash
  backend/.venv/bin/pytest backend/tests -v
  cd frontend && npx tsc --noEmit && npm test && npm run build
  cd e2e && npx playwright test --list
  ```
- **Files Affected**: New image-processing backend route/schema/service/test, Input Images and Outputs pages, frontend types/API/sidebar, and Playwright journey test.

### [2026-10-21 14:55 IST] Canonical Demo Asset Cleanup
- **Contributor**: Dhruv
- **Commit**: [`c104bb2`](https://github.com/ShadowHey/Tredence_H4ck/commit/c104bb2)
- **Summary of What Was Done**: Removed the byte-identical `shelfsense_antigravity_handoff/sample_assets/` copy and clarified that the repository-root `sample_assets/` directory is canonical.
- **How to Run / Test**:
  ```bash
  diff -qr sample_assets shelfsense_antigravity_handoff/sample_assets
  ```
- **Files Affected**: Handoff prompt and the 15 deleted duplicate sample-asset files.

### [2026-10-21 07:00 IST] Unified Root Logging & Real-Time Job Streamer
- **Contributor**: Dhruv
- **Commit**: [`19710ad`](https://github.com/ShadowHey/Tredence_H4ck/commit/19710ad)
- **Summary of What Was Done**:
  - Implemented a unified logging system at the repository root (`logs/logs.txt`) that aggregates Frontend UI actions, Backend REST requests with latencies, and Background Worker telemetry in chronological order.
  - Built a standalone terminal monitoring script (`logs/log_collector.py`) with ANSI colors, line-following, job filtering, and statistical summaries.
  - Added non-blocking fire-and-forget client-side logger (`frontend/src/lib/logger.ts`) dispatching to `POST /api/v1/logs/event`.
  - Added background worker execution timer around CLIP vector generation (`[JOB-START:CLIP]`, `[JOB-DONE:CLIP]`, duration in ms).
- **How to Run / Test**:
  ```bash
  # 1. Stream all live logs in real-time
  python logs/log_collector.py --follow

  # 2. Stream only background worker jobs (e.g. CLIP embeddings)
  python logs/log_collector.py --jobs --follow

  # 3. View a statistical summary of jobs and latency
  python logs/log_collector.py --summary
  ```
- **Files Affected**:
  - `logs/log_collector.py` *(New)*: CLI log streamer and analysis tool.
  - `logs/logs.txt` *(New)*: Central log file.
  - `logs/.gitignore` *(New)*: Git rules for logs directory.
  - `backend/app/core/logging_config.py` *(New)*: Thread-safe unified log writer.
  - `backend/app/api/routes/logs.py` *(New)*: Ingestion router for client events.
  - `backend/app/main.py`: Added HTTP logging middleware and router inclusion.
  - `backend/app/services/product_service.py`: Added job start/done/duration logging.
  - `frontend/src/lib/logger.ts` *(New)*: Fire-and-forget client telemetry.
  - `frontend/src/components/designer/AddShelfModal.tsx`: Emits `ACTION:SHELF_ADD`.
  - `frontend/src/components/designer/AddProductModal.tsx`: Emits `ACTION:PRODUCT_ADD`.

---

### [2026-10-21 06:18 IST] CLIP ViT-B/32 Vector Embedding Pipeline & Direct SQLite Inspection Tool
- **Contributor**: Dhruv
- **Commit**: [`38b2583`](https://github.com/ShadowHey/Tredence_H4ck/commit/38b2583)
- **Summary of What Was Done**:
  - Integrated OpenCLIP (`ViT-B-32-quickgelu` with OpenAI weights) to compute 512-dimensional vector embeddings for all product catalog items.
  - Added `embedding JSON` column to SQLite `products` table with zero-touch automatic startup migration.
  - Hooked automated embedding computation into `create_product()` and image updates.
  - Created a direct SQLite database inspection CLI without exposing unnecessary public HTTP endpoints.
  - Verified identical copy similarity: duplicate Yellow Lays product achieves **1.000000** (100.00%) cosine similarity.
- **How to Run / Test**:
  ```bash
  # 1. List all catalog products and verify embeddings are present
  backend/.venv/bin/python backend/scripts/inspect_embeddings.py --list

  # 2. Compare two products to calculate pairwise cosine similarity
  backend/.venv/bin/python backend/scripts/inspect_embeddings.py --compare 7 8

  # 3. Duplicate any product and verify embedding equality
  backend/.venv/bin/python backend/scripts/inspect_embeddings.py --test-copy 7

  # 4. Run embedding unit test suite
  backend/.venv/bin/pytest backend/tests/unit/test_embeddings.py -v
  ```
- **Files Affected**:
  - `backend/app/services/embedding_service.py` *(New)*: CLIP singleton and similarity engine.
  - `backend/scripts/inspect_embeddings.py` *(New)*: Database inspection CLI.
  - `backend/tests/unit/test_embeddings.py` *(New)*: 5 unit tests for dimensions, L2 norm, and identity.
  - `backend/app/db/models.py`: Added `embedding = Column(JSON, nullable=True)`.
  - `backend/app/db/database.py`: Auto-migration pragma check.
  - `backend/app/api/schemas/product.py`: Added `embedding: Optional[List[float]]`.
  - `backend/app/services/product_service.py`: Automated embedding hook.
  - `backend/requirements.txt`: Added `torch`, `torchvision`, `open-clip-torch`.

---

### [2026-10-21 03:45 IST] Manual Product Addition Modal with Full Database Fields
- **Contributor**: Kumar Saurav
- **Commit**: [`9c3118a`](https://github.com/ShadowHey/Tredence_H4ck/commit/9c3118a) / [`d4d47e5`](https://github.com/ShadowHey/Tredence_H4ck/commit/d4d47e5)
- **Summary of What Was Done**:
  - Built an `AddProductModal` dialog enabling manual product creation directly from the UI.
  - Captures full database properties: Name, SKU, Category, Price, Currency, physical Width, Height, Depth in `cm`, and custom image upload.
  - If no custom packshot is uploaded, client dynamically synthesizes a crisp SVG packshot with category-themed badges and dimensions.
  - Newly created products are immediately added to catalog state and ready for instant shelf drag-and-drop.
- **How to Run / Test**:
  1. Open frontend at [http://localhost:3000](http://localhost:3000/).
  2. In the right Context Panel, click the **"Library"** tab.
  3. Click **"+ Add Product"** to open the modal.
  4. Enter details (e.g., SKU: `TEST-DRK-1`, Width: `10cm`, Height: `18cm`) and submit.
  5. Verify the product immediately appears in the library list.
- **Files Affected**:
  - `frontend/src/components/designer/AddProductModal.tsx` *(New)*: Full modal component.
  - `frontend/src/components/designer/ContextPanel.tsx`: Added trigger button and state handler.
  - `frontend/src/components/designer/ShelfCanvas.tsx`: Product placement sync.
  - `frontend/tests/components.test.tsx`: Unit tests for modal submission and field validations.
