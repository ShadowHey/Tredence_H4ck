# ShelfSense AI — Image Parsing, Product Detection, Shelf Rows & Empty Space

A computer-vision pipeline for retail shelf compliance, product detection, empty-space localization, and shelf-row segmentation.

---

## 1. Overview & Capabilities

The pipeline analyzes raw supermarket shelf photographs and produces **ONE combined visual annotation** along with structured **JSON** and **CSV** telemetry:

1. **Product Bounding Boxes**: Tight neon-cyan outlines (`#00E5FF`) surrounding every detected SKU.
2. **Empty Shelf-Space Bounding Boxes**: Dark royal-blue bounding boxes (`#1739B7`) with translucent fills surrounding out-of-stock shelf gaps.
3. **Shelf-Row Segmentation**: Amber polygon boundaries (`#FFB000`) and semi-transparent tier highlights, ordered from top (`ROW 1`) to bottom.
4. **Utilization & Empty Space Analytics**:
   - Area-based metric following the reference standard:
     $$\text{Empty Area \%} = \frac{\text{Total Empty Area}}{\text{Total Empty Area} + \text{Total Product Area}} \times 100$$
   - Per-row empty slot counts and fill ratios.
5. **Exact Resolution Preservation**: The annotated photograph matches 100% of the input image's width and height.

---

## 2. Directory Structure

```text
image-parsing/
├── README.md               # User & architecture documentation
├── MODEL_SETUP.md          # Model weights, class mappings & licensing
├── TASK_CHECKLIST.md       # Granular task checklist & recovery tracking
├── requirements.txt        # Isolated Python dependencies
├── config/
│   └── default.yaml        # Thresholds, colors, and pipeline configuration
├── models/
│   ├── detect_product_empty_space.pt  # YOLO11 detection weights
│   ├── segment_shelf_rows.pt          # YOLO11 segmentation weights
│   └── README.md
├── sample_inputs/          # Raw supermarket shelf photographs
│   ├── test_987.jpg        # Coffee & breakfast aisle
│   ├── test_999 (1).jpg    # Pharmacy & digestive health aisle
│   ├── test_image.jpg      # 7-tier reference shelf
│   └── README.md
├── outputs/                # Generated annotations, JSON, and CSVs
│   ├── test_987_annotated.jpg
│   ├── test_987_detections.json
│   ├── test_999_annotated.jpg
│   ├── test_999_detections.json
│   └── shelf_summary.csv
├── src/
│   └── shelf_image_parsing/
│       ├── __init__.py
│       ├── config.py       # Configuration loading and overrides
│       ├── schemas.py      # Pydantic data schemas
│       ├── geometry.py     # Box math, clipping, IoU, and NMS
│       ├── detector.py     # YOLO product & empty-space detector
│       ├── detection_refinement.py # Conservative nested-duplicate suppression and geometry warnings
│       ├── row_segmenter.py# YOLO-seg shelf-row segmenter
│       ├── empty_space.py  # Empty-space refiner & row-band assignment
│       ├── visualization.py# Multi-layer OpenCV drawing engine
│       ├── pipeline.py     # End-to-end pipeline orchestrator
│       └── cli.py          # Command-line interface
├── scripts/
│   └── run_batch.py        # Convenience batch processing script
├── tests/
│   ├── unit/
│   │   ├── test_geometry.py
│   │   ├── test_empty_space.py
│   │   ├── test_row_assignment.py
│   │   └── test_visualization.py
│   └── integration/
│       └── test_pipeline.py
└── fixtures/
    └── README.md
```

---

## 3. Installation & Setup

The module operates in an isolated virtual environment to prevent dependency conflicts:

```bash
cd image-parsing
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Verify the environment:
```bash
python -c "import ultralytics, cv2, numpy, pydantic, yaml; print('Environment OK!')"
```

---

## 4. Execution Commands

### Batch Processing (Default on `sample_inputs/`)
```bash
cd image-parsing
source .venv/bin/activate
python -m shelf_image_parsing.cli --input sample_inputs --output outputs --save-json --save-csv
```
Or via the helper script:
```bash
python scripts/run_batch.py
```

### Single Image Processing
```bash
python -m shelf_image_parsing.cli --input sample_inputs/test_987.jpg --output outputs --confidence 0.25
```

### CLI Options
- `-i, --input`: Path to an image file or directory of images.
- `-o, --output`: Target directory for artifacts (default: `outputs`).
- `-c, --confidence`: Confidence threshold (overrides config, e.g. `0.25`).
- `-d, --device`: Device to use (`cpu`, `mps`, `cuda`).
- `--save-json / --no-save-json`: Enable or disable JSON export.
- `--save-csv / --no-save-csv`: Enable or disable CSV summary.
- `--save-annotated / --no-save-annotated`: Enable or disable image rendering.

---

## 5. Output Specifications

### A. Annotated Image (`*_annotated.jpg`)
Rendered in strict layered order:
1. Base image (identical dimensions).
2. Shelf rows: Amber (`#FFB000`) translucent fill (`alpha=0.15`), solid boundary lines, and `ROW N` badges.
3. Empty shelf spaces: Dark royal blue (`#1739B7`) translucent fill (`alpha=0.25`), solid boundary, and `EMPTY SPACE <conf>` badges.
4. Product boxes: Neon cyan (`#00E5FF`) tight border, solid background label with cyan text `PRODUCT <conf>`.
5. Telemetry banner: Semi-transparent header displaying total products, empty slots, shelf rows, and calculated empty area percentage.

### B. Machine-Readable JSON (`*_detections.json`)
```json
{
  "source_image": "test_987.jpg",
  "image_width": 1024,
  "image_height": 768,
  "model_status": "completed",
  "summary": {
    "product_count": 86,
    "empty_region_count": 4,
    "shelf_row_count": 7,
    "empty_area_percentage": 11.45,
    "product_area_percentage": 88.55,
    "total_empty_area_px": 54200,
    "total_product_area_px": 419200
  },
  "products": [...],
  "empty_regions": [...],
  "shelf_rows": [...],
  "annotated_image": "test_987_annotated.jpg"
}
```

### C. Summary CSV (`shelf_summary.csv`)
Logs row-level and image-level metrics:
- `source_image`, `model_status`, `image_width`, `image_height`
- `row_number`, `row_product_count`, `row_empty_count`, `row_empty_percentage`
- `total_products`, `total_empty_slots`, `total_shelf_rows`, `overall_empty_percentage`

---

## 6. Running Tests

Unit and integration test suites require **no GPU** and **no network**:

```bash
cd image-parsing
source .venv/bin/activate
PYTHONPATH=src pytest tests/ -v
```

---

## 7. Known Limitations & Troubleshooting

1. **Extreme Angled Perspective**: Highly oblique photographs may produce overlapping row vertical bands. Straight-on or slightly angled photographs produce the cleanest row assignment.
2. **Apple Silicon Acceleration**: Use `--device mps` on Apple Silicon for faster inference if PyTorch MPS backend is configured. Default is `--device cpu` for maximum stability across platforms.
3. **Empty Space vs Dark Shadow**: Deep empty slots with dark shadowing are captured accurately by the dual-class YOLO model; however, severe lighting glare may degrade detection confidence. Adjust `--confidence 0.20` for low-light scenes.
