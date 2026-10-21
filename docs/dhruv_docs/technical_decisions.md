# Dhruv's Architecture Decision Records (ADRs)

---

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
