# ShelfSense AI — Acceptance and Regression Testing Guide

This document describes the automated test suites, test isolation architecture, and execution procedures for ShelfSense AI.

---

## 1. Test Architecture Overview

| Test Layer | Framework | Target Scope | Isolation Strategy |
| :--- | :--- | :--- | :--- |
| **Backend Unit** | `pytest` | Product/Shelf schema validation, collision math, row capacity calculation, export schema. | In-memory objects, no database IO. |
| **Backend Integration** | `pytest` + `httpx` / `TestClient` | Full REST API lifecycle, multipart uploads, foreign-key cascade, collision 422 errors, persistence. | Isolated temporary SQLite database (`test_*.db`) and isolated temporary uploads directory. Never mutates local development DB. |
| **Frontend Unit** | `vitest` + React Testing Library | Initial empty canvas, Add Shelf modal, Product form validation, Dimension labels in cm, Context panel tabs. | `jsdom` simulated browser environment with mocked API fixtures. |
| **End-to-End** | `playwright` | Full user journey: open app -> create planogram -> add shelf & rows -> place product -> save -> reload -> assert persistence -> export visual & JSON. | Headless browser running against live dev servers. |

---

## 2. Test Execution Commands

### Run All Backend Tests
```bash
make test-backend
# Or directly:
backend/.venv/bin/pytest backend/tests -v
```

### Run Frontend Component Tests
```bash
make test-frontend
# Or directly:
cd frontend && npm test
```

### Run Frontend Lint & Type Checks
```bash
make lint
# Or directly:
cd frontend && npm run lint && npx tsc --noEmit
```

### Run Frontend Production Build
```bash
make build
# Or directly:
cd frontend && npm run build
```

### Run Playwright End-to-End Tests
Ensure both backend and frontend servers are running:
- Terminal 1: `make backend` (port 8000)
- Terminal 2: `make frontend` (port 3000)

Then run:
```bash
make test-e2e
# Or directly:
cd e2e && npx playwright test
```

---

## 3. Verified Acceptance Criteria

- [x] **Initial Empty State**: Canvas begins without shelves; displays Add Shelf prompt.
- [x] **Shelf Creation**: Configures name, width cm, height cm, depth cm, rows (1-12), and optional base plinth.
- [x] **Product Form**: Enforces unique SKU, non-empty name, positive dimensions in cm, price, and image artwork.
- [x] **Zero Overlap**: Rejects overlapping product placements on the same row with actionable error.
- [x] **Capacity Calculation**: Real-time deterministic check using cm values; warns when product exceeds remaining width.
- [x] **Safe Row Reduction**: Blocks reducing shelf row count when populated rows would be deleted.
- [x] **Persistence**: Planogram, shelves, and placements persist across reloads and backend restarts in SQLite.
- [x] **Visual Export**: High-resolution PNG rendering with white shelf background, packshots, and cm dimension ruler.
- [x] **JSON Export**: Versioned schema with `format_version: "1.0"`, `unit: "cm"`, physical coordinates, and dimensions.
