# ShelfSense AI — Backend API

FastAPI backend service powering the ShelfSense AI Planogram Designer Studio.

## Architecture & Features
- **FastAPI + SQLAlchemy 2.0 + SQLite**: High-performance asynchronous API with strict SQLite foreign key constraint enforcement.
- **Physical Centimetre Calculations**: Computes shelf row capacities, collisions, bounds, and spacing directly in centimetres (`cm`).
- **Zero-Overlap Collision Engine**: Validates product placement intervals with sub-millimetre precision.
- **Persistent Asset Storage**: Manages uploads and SVG/PNG product packshots under `uploads/`.

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Seed sample catalogue
python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/seed')"
# Or via Makefile: make seed

# Run server
uvicorn app.main:app --reload --port 8000
```

## Running Tests
```bash
pytest -v
```
