# ShelfSense AI — AGENTS.md

Welcome to the ShelfSense AI repository. This guide sets developer and coding-agent standards for building and maintaining the ShelfSense AI Planogram Designer.

## Architecture Guidelines
- **Modular Monolith**: `backend/` (FastAPI + SQLAlchemy + SQLite) and `frontend/` (Next.js + TypeScript + Tailwind CSS).
- **Physical Coordinates over Pixels**: All database entities, calculations, validations, and exports use real physical dimensions in centimetres (`cm`). Frontend pixels are purely a responsive rendering projection.
- **Strict Collision & Bounds**: Placements cannot exceed shelf usable width or overlap existing placements on the same row. Always return actionable 4xx errors with exact measurements.
- **No Mock Persistence**: SQLite and local disk files (`uploads/`) are the single source of truth. Never rely solely on React state or localStorage for data persistence.
- **Design Aesthetic**:
  - Dark charcoal SaaS shell (`#0d0f12`, `#1a1e26`) inspired by modern analytics dashboards (MoEngage).
  - Clean Blender-inspired scene hierarchy tree for the planogram outliner.
  - Bright, high-contrast white shelf canvas with distinct measurement brackets (formal planogram conventions) and SVG/PNG packshots.

## Testing Standards
- Always run backend tests (`pytest`) against isolated temporary test databases and temporary upload folders. Never mutate the development SQLite database in tests.
- Maintain frontend unit tests (`vitest`) for empty states, form validations, and measurement calculations.
- Maintain end-to-end user journey tests with Playwright (`e2e/`).
