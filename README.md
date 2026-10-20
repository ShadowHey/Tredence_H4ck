# ShelfSense AI — Planogram Designer Studio (MVP)

ShelfSense AI is a modern retail planogram design and inventory management workspace built for retail category managers and shelf planning teams. It combines physical-space planning in centimetres (`cm`) with collision detection, packshot artwork preservation, and automated two-way exports.

---

## 🎨 Visual Aesthetics & Reference Architecture

The design directly reflects four reference architectures:
1. **MoEngage Analytics SaaS Shell**: Dark charcoal theme (`#0d0f12`, `#1a1e26`), vertical navigation sidebar, subtle borders (`#262b36`), and warm amber accents (`#f59e0b`).
2. **Blender Outliner**: Left-side hierarchical scene tree (`Planogram > Shelves > Shelf Unit > Rows > Product Placements`) with node selection, item counts, and expand/collapse.
3. **Formal Planogram Conventions**: High-contrast, bright/white shelf canvas featuring formal side elevation rulers, per-row height brackets, and cm grid dimensioning.
4. **Retail Shelf Planner**: Horizontal shelf slats, drop zones, packshot rendering preserving true aspect ratio, and deterministic capacity progress indicators.

---

## 🚀 Technology Stack

- **Frontend**: Next.js 16 (App Router) + React 19 + TypeScript + Tailwind CSS
- **Backend**: FastAPI + Pydantic v2 + SQLAlchemy 2.0
- **Database**: Persistent local SQLite (`backend/shelfsense.db`)
- **Asset Storage**: Local file storage (`backend/uploads/`) with relative DB paths
- **Testing**:
  - Backend: `pytest` + `httpx` / `TestClient` (isolated temporary databases)
  - Frontend: `vitest` + React Testing Library + `@testing-library/jest-dom`
  - End-to-End: `playwright`

---

## 📦 Quick Start & Local Setup

### 1. Installation
Install backend Python packages and frontend Node dependencies:
```bash
make install
```
*(Or manually create `backend/.venv`, run `pip install -r backend/requirements.txt`, and `npm install` inside `frontend/` and `e2e/`)*.

### 2. Seed Catalogue
Populate the 6 unbranded sample products with SVG/PNG packshots:
```bash
make seed
```

### 3. Run the Development Servers
In two separate terminals:

```bash
# Terminal 1: Backend API (FastAPI)
make backend
# Running on http://localhost:8000 (OpenAPI docs at http://localhost:8000/docs)

# Terminal 2: Frontend Web App (Next.js)
make frontend
# Running on http://localhost:3000
```

Open [http://localhost:3000](http://localhost:3000) to access the studio.

---

## 🧪 Testing Suite

### Run All Tests
```bash
# Backend unit & integration tests
make test-backend

# Frontend component tests
make test-frontend

# Frontend lint & TypeScript verification
make lint

# Frontend production build
make build

# Playwright critical journey E2E test
make test-e2e
```

---

## 📁 Repository Structure

```text
Tredence_H4ck/
├── Makefile                # Root orchestration commands
├── AGENTS.md               # Coding standards and agent pair programming rules
├── README.md               # Repository overview and setup guide
├── docs/
│   ├── PRODUCT_SPEC.md     # Stage 1 product requirements specification
│   ├── USER_GUIDE.md       # Comprehensive user operational guide
│   ├── API_CONTRACT.md     # Complete REST API specification
│   └── TESTING.md          # Acceptance and regression test procedures
├── sample_assets/          # Bundled sample catalogue and packshot SVGs/PNGs
│   ├── catalogue.sample.json
│   ├── catalogue.sample.csv
│   └── images/
├── backend/
│   ├── app/
│   │   ├── main.py         # FastAPI entrypoint, lifespan, and CORS
│   │   ├── core/           # Config, directory paths, and settings
│   │   ├── db/             # SQLAlchemy engine, session, and models
│   │   ├── api/            # Routes (health, products, planograms, seed)
│   │   ├── services/       # Collision engine, shelf logic, and export service
│   │   └── storage/        # Safe image file uploads
│   ├── tests/
│   │   ├── conftest.py     # Isolated temporary test database fixtures
│   │   ├── unit/           # Unit tests (schemas, physical fit, capacity)
│   │   └── integration/    # Integration tests (CRUD, cascade, persistence)
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── app/            # App Router: Dashboard (/) & Designer (/designer)
│   │   ├── components/     # Shell, Outliner, ShelfCanvas, ContextPanel, Modals
│   │   ├── lib/            # Typed API client and visual PNG export
│   │   └── types/          # TypeScript interfaces
│   ├── tests/              # Vitest component tests
│   ├── package.json
│   └── vitest.config.mjs
└── e2e/                    # Playwright end-to-end critical journey
    ├── playwright.config.ts
    └── tests/planogram_journey.spec.ts
```

---

## 📌 Scope Boundaries (Stage 1 MVP)

- **Implemented**: Full-stack planogram designer, physical cm coordinate system, zero-overlap collision validation, Blender-style outliner, MoEngage-style dark dashboard, product catalogue with file uploads, PNG & versioned JSON exports, and full test suites.
- **Future Scope (Stage 2+)**: Computer vision shelf auditing, live photograph compliance scoring, YOLO/RT-DETR object detection, CLIP product embeddings, OCR price-tag reading.
