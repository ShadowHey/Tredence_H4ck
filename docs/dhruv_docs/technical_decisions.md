# Dhruv's Architecture Decision Records (ADRs)

---

### [2026-10-21 22:45 IST] YOLO Cutout Extraction, Semantic Clustering & 4-Column Analysis Table
- **Commit**: [`8a0b94e`](https://github.com/ShadowHey/Tredence_H4ck/commit/8a0b94e)
- **Status**: Implemented & Verified in Production

#### 1. Context & Problem Statement
From the YOLO shelf detection pipeline, bounding box coordinates are produced for products, shelf structures, and void spaces. Operators need to:
1. Visually inspect the individual cropped images categorized into three distinct buckets: `products`, `shelves`, and `empty_spaces`.
2. Group repeated identical product faces on a shelf (visual clustering).
3. Semantically match detected visual clusters against the product catalog using dense vector embeddings.
4. Enforce a strict $\ge 95\%$ confidence cutoff for catalog matches, presenting a clean 4-column compliance view where non-matches strictly omit any catalog packshot image.

#### 2. Options Considered
- **Option 1**: Compute CLIP vectors sequentially on each cropped bounding box on HTTP request.
  - *Cons*: Sequential CLIP processing takes ~360ms per crop. A shelf with 150+ products would take >50 seconds to respond, blocking the UI thread.
- **Option 2 (Chosen)**: Fast batched PyTorch CLIP inference (`compute_image_embeddings_batch`, batch size 32) coupled with asynchronous precomputation upon job completion.
  - *Pros*: Cuts inference time to **15.6ms per crop**. 150+ crops are embedded in <2.5 seconds. Results are persisted to disk (`cutouts.json`, `analysis.json`) for instant sub-10ms UI reads.

#### 3. Key Architectural Decisions
- **Disk Cutout Organization**:
  Stored in `uploads/image_processing/outputs/{job_id}/cutouts/` with separate subdirectories for `products/`, `shelves/`, and `empty_spaces/`.
- **Intra-Shelf Clustering**:
  Uses a leader-clustering algorithm with a strict visual similarity threshold $\tau = 0.88$. Items above $\tau$ are grouped into the same cluster.
- **Catalog Matching Rule**:
  Cluster centroid vectors are compared against SQLite `products.embedding` vectors via cosine similarity. If $\max(\text{similarity}) \ge 0.95$, `is_catalog_match = True`, and the catalog product details and packshot image are linked. If $< 0.95$, `is_catalog_match = False` and no catalog product is displayed.
- **The 4-Column Table Specification**:
  Implemented in `frontend/src/components/analysis/AnalysisTable.tsx`:
  1. `Similar Objects`: Horizontal scrollable thumbnails of crops belonging to this cluster.
  2. `Similarity Percentage`: Cluster visual cohesion percentage with color-coded meter.
  3. `Is object similar to someone in the product catalog?`: Strictly `Yes` (green check) or `No` (gray cross).
  4. `Similar Product`: Catalog packshot image and details if `Yes`; strictly NO product image rendered if `No`.

---

### [2026-10-21 15:05 IST] Image Intake, Shelf Assignment & Annotated Outputs
- **Commit**: [`30474fc`](https://github.com/ShadowHey/Tredence_H4ck/commit/30474fc)
- **Status**: Implemented and verified.
- **Decision**: Persist each uploaded shelf photo with one explicitly selected planogram and shelf before queueing it. The selected shelf dimensions are snapshotted at queue time, and a single-concurrency worker calls the isolated `image-parsing` environment to create an annotated image and detection JSON.
- **Rationale**: This keeps every output auditable even if the source shelf is later changed, prevents parallel heavyweight model runs, and preserves queued work across restarts through SQLite job records.
- **Trade-off**: Users process one image at a time by design; batch upload remains available for staging photographs.

### [2026-10-21 07:00 IST] Unified Root Logging & Real-Time Job Streamer
- **Commit**: [`19710ad`](https://github.com/ShadowHey/Tredence_H4ck/commit/19710ad)
- **Status**: Implemented & Verified in Production

#### 1. Context & Problem Statement
With background jobs (such as CLIP vector embedding generation) and dynamic frontend actions running concurrently, developers lacked visibility into what was executing under the hood. When a user created a product or shelf in the UI, there was no continuous centralized stream showing:
1. The frontend action intent.
2. The backend REST route handling with latency.
3. The background worker job execution time and status.

#### 2. Options Considered
- **Option 1**: Rely only on browser console and terminal uvicorn stdout.
  - *Cons*: Logs are fragmented across separate windows; impossible to inspect background worker execution history after the fact; no unified timeline.
- **Option 2**: Full ELK or external telemetry stack (Datadog/Sentry).
  - *Cons*: Overkill for local dev and hackathon environment; introduces heavy network/service dependencies.
- **Option 3 (Chosen)**: A unified root `logs/` directory with `logs.txt` as a single file sink, coupled with a lightweight, color-coded Python streamer CLI (`logs/log_collector.py`).

#### 3. Final Technical Decision & Rationale
- **Thread-Safe File Sink**: Implemented `backend/app/core/logging_config.py` using standard library threading locks and immediate line flushing (`f.flush()`). This guarantees zero delay between event occurrence and file persistence.
- **Client Ingestion Route**: Added `POST /api/v1/logs/event` and a non-blocking `frontend/src/lib/logger.ts` helper (`keepalive: true`) so frontend UI actions (`ACTION:SHELF_ADD`, `ACTION:PRODUCT_ADD`) reach `logs.txt` without blocking the browser thread.
- **Request Middleware**: Attached HTTP logging middleware to FastAPI to log all incoming requests with duration in ms, while specifically excluding `/logs/event` to prevent infinite logging loops.
- **Background Worker Instrumentation**: Wrapped CLIP generation in `product_service.py` with `time.perf_counter()` to log `[JOB-START:CLIP]`, `[JOB-DONE:CLIP]`, and `[JOB-ERROR:CLIP]` with precise duration in milliseconds.
- **Standalone CLI**: Built `logs/log_collector.py` using standard Python only (`argparse`, `sys`, `time`). Supports `--follow`, `--jobs`, `--frontend`, `--backend`, and `--summary`.

---

### [2026-10-21 06:18 IST] CLIP ViT-B/32 Vector Embeddings for Product Catalog
- **Commit**: [`38b2583`](https://github.com/ShadowHey/Tredence_H4ck/commit/38b2583)
- **Status**: Implemented & Verified in Production

#### 1. Context & Problem Statement
To enable visual planogram merchandising compliance and product grouping, catalog items needed to be converted into dense semantic vector representations. Multiple packshots of similar products (e.g., various flavours or packet sizes of Lays chips) must project closely in vector space, while distinct product categories (e.g., chips vs chocolate) must separate cleanly.

#### 2. Options Considered
- **Option 1**: External cloud embedding API (OpenAI / Cohere).
  - *Cons*: Network latency, API costs, dependency on external internet connectivity during offline development.
- **Option 2**: ResNet-50 / generic ImageNet feature extraction.
  - *Cons*: Lacks multimodal semantic grounding; fails to capture packaging typography and visual category nuances.
- **Option 3 (Chosen)**: Local OpenCLIP `ViT-B/32` with OpenAI pretrained weights (`quickgelu`).
  - *Pros*: Runs completely locally on CPU in ~40ms per packshot; multimodal vision-language understanding; zero external API keys required.

#### 3. Final Technical Decision & Rationale
- **Model Architecture**: OpenCLIP `ViT-B-32-quickgelu` (`pretrained="openai"`). Loaded as a singleton in `backend/app/services/embedding_service.py` with HuggingFace hub caching.
- **$L_2$ Normalization**: Every 512-dimensional output vector is unit-normalized ($\|\mathbf{v}\|_2 = 1.0$), ensuring that cosine similarity is directly computed via dot product ($\mathbf{a} \cdot \mathbf{b}$).
- **Database Architecture**: SQLite JSON column (`embedding JSON`) added to the `products` table. Auto-migration checks `PRAGMA table_info(products)` on startup and adds the column without manual migration scripts.
- **Deterministic Identity Requirement**: Ensured identical packshots produce identical embeddings. Verified on Product #7 ("Yellow Lays") vs duplicate copy: Cosine Similarity = **1.000000** (100.00% exact match).
- **No Unwanted HTTP Endpoints**: Per user direction, avoided public vector comparison routes and instead built `backend/scripts/inspect_embeddings.py` for direct SQLite CLI inspection (`--list`, `--compare`, `--test-copy`, `--backfill`).
