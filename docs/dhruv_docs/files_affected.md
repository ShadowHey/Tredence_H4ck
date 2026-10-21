# Dhruv's Files & Folders Affected Log (Blast Radius)

---

### [2026-10-21 22:45 IST] YOLO Cutout Extraction, Semantic Clustering & 4-Column Analysis Table
- **Commit**: [`8a0b94e`](https://github.com/ShadowHey/Tredence_H4ck/commit/8a0b94e)
- **Author**: Dhruv
- **Branch**: `feature/dhruv`

#### Files Created
| File Path | Description / Role |
| :--- | :--- |
| `backend/app/services/cutout_service.py` | Core engine for bounding box cutout extraction, fast batch CLIP embeddings, intra-shelf clustering ($\tau = 0.88$), and strict catalog matching ($\ge 95\%$). |
| `backend/tests/unit/test_cutouts_and_analysis.py` | 5 unit tests for cutout disk saving, batch CLIP speed, clustering, and >= 95% threshold verification. |
| `frontend/src/components/outputs/CutoutViewerModal.tsx` | Cutout inspector dialog with 3 tabs (`Products`, `Shelves / Rows`, `Empty Spaces`), confidence badges, and zoom sub-modal. |
| `frontend/src/components/analysis/AnalysisTable.tsx` | Strict 4-column analysis table: Similar Objects, Similarity Percentage, Is object similar to someone in the product catalog (Yes/No), and Similar Product. |
| `frontend/src/app/analysis/page.tsx` | Top-level `/analysis` route with Suspense wrapper, active shelf card, metric badges, output switcher, and crop inspector. |
| `frontend/tests/analysis-and-cutouts.test.tsx` | 6 frontend unit tests validating modal tabs and 4-column table rendering behavior. |

#### Files Modified
| File Path | Changes Made |
| :--- | :--- |
| `backend/app/services/embedding_service.py` | Added `compute_image_embeddings_batch(images, batch_size=32)` for accelerated vector calculation (~15.6ms/crop). |
| `backend/app/services/image_processing_service.py` | Integrated `extract_cutouts_and_analyze()` automatically on image inference job completion. |
| `backend/app/api/schemas/image_processing.py` | Added Pydantic schemas: `CutoutItem`, `CutoutsResponse`, `CatalogMatchedProduct`, `ClusterRow`, `OutputAnalysisResponse`. |
| `backend/app/api/routes/image_processing.py` | Registered `GET /outputs/{id}/cutouts`, `GET /outputs/{id}/analysis`, and `POST /outputs/{id}/analyze`. |
| `frontend/src/types/index.ts` | Added TypeScript interfaces matching backend analysis schemas. |
| `frontend/src/lib/api.ts` | Added `getOutputCutouts`, `getOutputAnalysis`, and `analyzeOutput` API client methods. |
| `frontend/src/components/shell/Sidebar.tsx` | Added `/analysis` top-level navigation item with `ScanSearch` icon. |
| `frontend/src/app/outputs/page.tsx` | Integrated `CutoutViewerModal` triggered on image card click or Inspect button; linked to `/analysis`. |

#### How to test
```bash
backend/.venv/bin/pytest backend/tests/ -v
npm test --prefix frontend
npm run build --prefix frontend
```

---

### [2026-10-21 15:05 IST] Image Intake, Shelf Assignment & Annotated Outputs
- **Commit**: [`30474fc`](https://github.com/ShadowHey/Tredence_H4ck/commit/30474fc)
- **Status**: Implemented and verified.
- **Created**: `backend/app/api/routes/image_processing.py`, `backend/app/api/schemas/image_processing.py`, `backend/app/services/image_processing_service.py`, `backend/tests/integration/test_image_processing_api.py`, `frontend/src/app/input-images/page.tsx`, `frontend/src/app/outputs/page.tsx`, `frontend/tests/image-processing-page.test.tsx`, and `e2e/tests/image_processing_journey.spec.ts`.
- **Modified**: database models/configuration, FastAPI startup/router registration, upload storage, sidebar navigation, frontend API client, and shared TypeScript types.
- **Schema impact**: Adds `input_images`, `processing_jobs`, and `processed_outputs` SQLite tables.
- **How to test**:
  ```bash
  backend/.venv/bin/pytest backend/tests -v
  cd frontend && npx tsc --noEmit && npm test && npm run build
  ```

### [2026-10-21 07:00 IST] Unified Root Logging & Real-Time Job Streamer
- **Commit**: [`19710ad`](https://github.com/ShadowHey/Tredence_H4ck/commit/19710ad)
- **Author**: Dhruv
- **Branch**: `feature/dhruv`

#### Files Created
| File Path | Description / Role |
| :--- | :--- |
| `logs/logs.txt` | Master log sink file aggregating Frontend UI, Backend API, and Worker telemetry. |
| `logs/log_collector.py` | Standalone CLI log streamer with ANSI colors, line-following, and summary metrics. |
| `logs/.gitignore` | Ignores temporary and rotated files while keeping `logs.txt` tracked. |
| `backend/app/core/logging_config.py` | Thread-safe logging handler with immediate line flush and job tracking helpers. |
| `backend/app/api/routes/logs.py` | FastAPI route `POST /api/v1/logs/event` to ingest client-side action events. |
| `frontend/src/lib/logger.ts` | Non-blocking, fire-and-forget `logFrontendAction()` utility (`keepalive: true`). |

#### Files Modified
| File Path | Changes Made |
| :--- | :--- |
| `backend/app/main.py` | Mounted `setup_unified_logging()` in lifespan; added HTTP request logging middleware with latency tracking; mounted `logs.router`. |
| `backend/app/services/product_service.py` | Wrapped CLIP embedding execution in `log_job_start()`, `log_job_done()`, and `log_job_error()` with duration in ms. |
| `frontend/src/components/designer/AddShelfModal.tsx` | Dispatches `ACTION:SHELF_ADD` upon successful shelf unit creation. |
| `frontend/src/components/designer/AddProductModal.tsx` | Dispatches `ACTION:PRODUCT_ADD` upon successful product creation. |

#### Database & Dependency Changes
- None (pure logging & telemetry infrastructure).

---

### [2026-10-21 06:18 IST] CLIP ViT-B/32 Vector Embeddings for Product Catalog
- **Commit**: [`38b2583`](https://github.com/ShadowHey/Tredence_H4ck/commit/38b2583)
- **Author**: Dhruv
- **Branch**: `feature/dhruv`

#### Files Created
| File Path | Description / Role |
| :--- | :--- |
| `backend/app/services/embedding_service.py` | Singleton CLIP service (`ViT-B-32-quickgelu`), image path resolver, L2 unit normalizer. |
| `backend/scripts/inspect_embeddings.py` | Direct SQLite inspection CLI tool (`--list`, `--compare`, `--test-copy`, `--backfill`). |
| `backend/tests/unit/test_embeddings.py` | 5 unit tests covering dimensionality (512), L2 normalization, duplicate copy identity, and separation. |

#### Files Modified
| File Path | Changes Made |
| :--- | :--- |
| `backend/app/db/models.py` | Added `embedding = Column(JSON, nullable=True)` to `Product` SQLAlchemy model. |
| `backend/app/db/database.py` | Updated `init_db()` with dynamic `PRAGMA table_info(products)` check and `ALTER TABLE products ADD COLUMN embedding JSON;`. |
| `backend/app/api/schemas/product.py` | Added `embedding: Optional[List[float]] = None` to `ProductResponse` Pydantic model. |
| `backend/app/services/product_service.py` | Automatically computes and attaches embedding vector on `create_product()` and image update. |
| `backend/requirements.txt` | Added `torch>=2.0.0`, `torchvision>=0.23.0`, and `open-clip-torch>=3.3.0`. |

#### Database Changes
- **Table**: `products`
  - **New Column**: `embedding` (Type: `JSON`, Nullable: `True`, Content: 512-dim float list).

#### External Dependencies Added
- `torch 2.8.0`
- `torchvision 0.23.0`
- `open-clip-torch 3.3.0`
- Pretrained weights: `models--timm--vit_base_patch32_clip_224.openai` cached locally in `~/.cache/huggingface/`.
