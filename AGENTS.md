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

## Multi-Collaborator Documentation Protocol
ShelfSense AI employs a structured, multi-collaborator documentation architecture in `docs/` to provide persistent memory for AI agents across context resets:
- **Global Specifications (`docs/shared/`)**:
  - `docs/shared/ARCHITECTURE.md`, `API_CONTRACT.md`, `PRODUCT_SPEC.md`, `USER_GUIDE.md`.
  - `docs/shared/CONTRIBUTIONS.md`: The universal ledger of all features and fixes. Every commit MUST be recorded here with: Date & Time, Contributor, Commit Hash, Quick Summary, Files Affected, and exact "How to Run / Test" commands.
- **Collaborator Workspace Journals**:
  - `docs/dhruv_docs/` (Dhruv)
  - `docs/kumar_docs/` (Kumar Saurav)
  - `docs/gyan_docs/` (Gyan)
  Each folder contains 4 standardized files stamped with Date and Time:
  1. `README.md`: Master timeline table and session index.
  2. `technical_decisions.md`: Architecture Decision Records (ADRs) with rationale and trade-offs.
  3. `conversation_history.md`: Human <-> Agent prompts, requirements, and turning points.
  4. `files_affected.md`: Blast radius map listing files created, modified, deleted, and schema changes.

### AI Agent Rules for Documentation:
1. **Context Discovery**: When an agent begins a task or needs to understand past work by a teammate, it MUST first check `docs/shared/CONTRIBUTIONS.md` and the relevant collaborator's folder (`docs/<name>_docs/`).
2. **Auto-Updating on Completion**: When a feature, fix, or session is completed, the agent MUST:
   - Append an entry to `docs/shared/CONTRIBUTIONS.md` with exact instructions on how other teammates can run and test it.
   - Append the date-and-time-stamped entry across the 4 files in `docs/<current_collaborator>_docs/`.
3. **Zero Merge Conflicts**: Agents must never edit another collaborator's journal folder (`kumar_docs` vs `dhruv_docs` vs `gyan_docs`). Shared specs in `docs/shared/` require mutual consensus.

