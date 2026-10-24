"""Class-specific YOLO confidence filtering tests."""

from types import SimpleNamespace

import numpy as np

from shelf_image_parsing.detector import ProductEmptySpaceDetector


class Tensor:
    def __init__(self, value):
        self.value = value

    def __getitem__(self, index):
        return Tensor(self.value[index])

    def item(self):
        return float(self.value)

    def cpu(self):
        return self

    def numpy(self):
        return np.asarray(self.value)


class Box:
    def __init__(self, cls_id, confidence, coords):
        self.cls = Tensor([cls_id])
        self.conf = Tensor([confidence])
        self.xyxy = Tensor([coords])


class Model:
    def __init__(self, boxes):
        self.boxes = boxes
        self.kwargs = None

    def __call__(self, _image, **kwargs):
        self.kwargs = kwargs
        return [SimpleNamespace(boxes=self.boxes)]


def test_product_cutoff_is_inclusive_at_sixty_percent_and_empty_boxes_are_untouched():
    model = Model([
        Box(1, 0.599, [10, 10, 30, 70]),
        Box(1, 0.600, [35, 10, 55, 70]),
        Box(1, 0.91, [60, 10, 80, 70]),
        Box(0, 0.25, [100, 10, 140, 70]),
    ])
    detector = ProductEmptySpaceDetector(
        confidence=0.20,
        product_confidence_threshold=0.60,
        model=model,
    )

    products, empty_regions = detector.detect(np.zeros((100, 160, 3), dtype=np.uint8))

    assert [product.confidence for product in products] == [0.6, 0.91]
    assert [product.confidence for product in detector.excluded_products] == [0.599]
    assert [region.confidence for region in empty_regions] == [0.25]
    # Keep the proposal floor low so empty-space proposals are not lost to the
    # stricter product-only acceptance threshold.
    assert model.kwargs["conf"] == 0.20


def test_product_cutoff_rejects_invalid_values():
    try:
        ProductEmptySpaceDetector(product_confidence_threshold=1.01, model=Model([]))
    except ValueError as error:
        assert "between 0 and 1" in str(error)
    else:
        raise AssertionError("out-of-range cutoff should be rejected")
