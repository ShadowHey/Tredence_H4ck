# ShelfSense AI — Model Setup & Architecture Guide

This document describes the trained computer-vision models used by the ShelfSense AI Image Parsing pipeline, their origin, class mappings, licensing terms, and verification procedures.

---

## 1. Overview of Model Assets

The pipeline utilizes two complementary YOLO11 deep-learning models derived from the reference architecture:

| Asset | File Name | Size | Architecture | Primary Task |
| :--- | :--- | :--- | :--- | :--- |
| **Object Detector** | `detect_product_empty_space.pt` | ~5.2 MB | Ultralytics YOLO11n | Product presence & empty shelf slot bounding boxes |
| **Row Segmenter** | `segment_shelf_rows.pt` | ~5.7 MB | Ultralytics YOLO11n-seg | Shelf-row polygon segmentation & visible boundaries |

Both model weight files are stored in `image-parsing/models/`.

---

## 2. Dataset Strategy & Class Mappings

### A. Detection Model (`detect_product_empty_space.pt`)
- **Dataset Construction**: Trained using a weakly-supervised relabeling strategy combining:
  1. Roboflow Supermarket Empty Shelf Detector dataset (providing empty shelf gap annotations).
  2. Pretrained SKU product detector generating bounding boxes on occupied shelf regions.
- **Class Mapping**:
  - `class_id = 0` $\to$ **`empty_space`** (Empty Shelf Region / Out-of-stock slot)
  - `class_id = 1` $\to$ **`product`** (Retail product / SKU packaging)

### B. Row Segmentation Model (`segment_shelf_rows.pt`)
- **Dataset Construction**: Trained on shelf fixture images annotated with polygon boundaries for each horizontal tier/slat.
- **Class Mapping**:
  - `class_id = 0` $\to$ **`shelf_row`** (Shelf tier contour)

---

## 3. Licensing, Attribution & Provenance

- **Reference Repository**: [`K-saif/Empty-Shelf-Alert-System`](https://github.com/K-saif/Empty-Shelf-Alert-System)
- **Author**: K-saif (Saif Khan)
- **Licensing Status**: The original repository is published publicly on GitHub without an explicit OSI license file (`UNLICENSE` / No License specified). Under GitHub Terms of Service, public repositories are viewable and forkable for evaluation and research.
- **Attribution**: All architectural concepts, relabeling strategies, and trained weights are credited to the original author.
- **Commercial Deployment Recommendation**: For production store deployments, train proprietary YOLO11 weights on store-specific planogram photography and synthetic renders to guarantee commercial license compliance.

---

## 4. Model Verification & Smoke Test

To verify that the weights are present, valid, and loadable by Ultralytics:

```bash
cd image-parsing
source .venv/bin/activate
python -c "
from ultralytics import YOLO
import sys

print('1. Checking Detection Model...')
det = YOLO('models/detect_product_empty_space.pt')
print('   ✔ Detection Classes:', det.names)

print('2. Checking Segmentation Model...')
seg = YOLO('models/segment_shelf_rows.pt')
print('   ✔ Segmentation Classes:', seg.names)
print('✅ Both models successfully verified!')
"
```

Expected output:
```text
1. Checking Detection Model...
   ✔ Detection Classes: {0: 'empty', 1: 'product'}
2. Checking Segmentation Model...
   ✔ Segmentation Classes: {0: 'row'}
✅ Both models successfully verified!
```

---

## 5. Mock Testing Fallback

The test suite in `tests/integration/test_pipeline.py` implements complete dependency injection via `MockDetector` and `MockSegmenter`. This ensures the full pipeline logic, geometry clipping, IoU math, NMS deduplication, row-band assignment, and JSON/CSV exporters can be verified independently without GPU hardware or external network access.
