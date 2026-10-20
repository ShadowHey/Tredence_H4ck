# ShelfSense AI - Model Directory

This directory stores the trained YOLO weights for the image-parsing pipeline.

## Model Files
1. `detect_product_empty_space.pt` (5.2 MB):
   - Architecture: Ultralytics YOLO11 (nano detection)
   - Task: Detects products and empty shelf regions
   - Classes:
     - `0`: `empty_space` (Empty Shelf Space)
     - `1`: `product` (Product)
   - Source: `K-saif/Empty-Shelf-Alert-System` (trained on Roboflow Supermarket Empty Shelf Dataset + Relabeled SKU Product Detections).

2. `segment_shelf_rows.pt` (5.7 MB):
   - Architecture: Ultralytics YOLO11-seg (nano segmentation)
   - Task: Segments shelf rows with polygon masks
   - Classes:
     - `0`: `shelf_row` (Row boundary polygon)
   - Source: `K-saif/Empty-Shelf-Alert-System` (trained on shelf row annotations).

See `MODEL_SETUP.md` in the root of `image-parsing/` for full setup, verification, and licensing details.
