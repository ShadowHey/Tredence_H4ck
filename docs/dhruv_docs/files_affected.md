# Dhruv's Files & Folders Affected Log (Blast Radius)

---

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
