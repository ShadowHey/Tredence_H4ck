# Test Fixtures

This directory contains lightweight synthetic images, bounding box fixtures, and mocked model responses for offline unit and integration testing.

Tests in `tests/` do not require network access, GPU hardware, or heavy weights. Real inference smoke tests are isolated from unit tests.
# Four-corner position calibration photos

The optional projective calibration path uses OpenCV ArUco `DICT_4X4_50` markers. Print markers with IDs `0`, `1`, `2`, and `3` at the same scale, and place their centres at the usable shelf-area corners (exclude the plinth): ID 0 = top-left, ID 1 = top-right, ID 2 = bottom-right, ID 3 = bottom-left. Keep all four markers visible and on the same plane as the shelf front. The image parser emits these source-image pixel centres as `calibration.shelf_corners_xy`; if any marker is missing or duplicated, the pipeline falls back to detected-row linear calibration and records that it assumes a straight-on view.

The homography corrects image coordinates for mapping; product image crops remain from the original photo. Do not use the marker centres as product/shelf boundaries for compliance ground truth—the planogram's known shelf width and saved row heights define the physical frame.
