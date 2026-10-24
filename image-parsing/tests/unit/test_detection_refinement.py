"""Regression tests for conservative duplicate removal and box-quality warnings."""

import pytest

from shelf_image_parsing.detection_refinement import assess_row_box_quality, suppress_nested_duplicates
from shelf_image_parsing.schemas import DetectionItem


def detection(box, confidence=0.8, row=1, class_id=1):
    return DetectionItem(
        class_name="product" if class_id else "empty_space",
        class_id=class_id,
        confidence=confidence,
        bbox_xyxy=box,
        bbox_normalized=[0.0, 0.0, 1.0, 1.0],
        row_number=row,
    )


def test_nested_duplicate_is_removed_but_adjacent_facings_are_preserved():
    first = detection([10, 10, 50, 100], confidence=0.9)
    nested_lower_confidence = detection([12, 12, 48, 98], confidence=0.6)
    adjacent = detection([51, 10, 90, 100], confidence=0.8)

    kept = suppress_nested_duplicates([first, nested_lower_confidence, adjacent])

    assert kept == [first, adjacent]
    assert first.bbox_xyxy == [10, 10, 50, 100]
    assert adjacent.bbox_xyxy == [51, 10, 90, 100]


def test_deduplication_is_class_aware():
    product = detection([10, 10, 50, 100], class_id=1)
    empty = detection([10, 10, 50, 100], class_id=0)

    assert suppress_nested_duplicates([product, empty]) == [product, empty]


def test_quality_assessment_flags_narrow_box_without_changing_geometry():
    typical_a = detection([0, 0, 40, 100])
    narrow = detection([42, 0, 60, 100])
    typical_b = detection([62, 0, 102, 100])

    assessed = assess_row_box_quality([typical_a, narrow, typical_b])

    assert assessed[0].quality_status == "usable"
    assert assessed[1].quality_status == "review"
    assert assessed[1].quality_flags == ["narrow_vs_row_median"]
    assert assessed[1].bbox_xyxy == [42, 0, 60, 100]


def test_quality_assessment_leaves_items_unchecked_when_row_unknown():
    item = detection([0, 0, 40, 100], row=None)

    assessed = assess_row_box_quality([item])

    assert assessed[0].quality_status == "unchecked"
    assert assessed[0].quality_flags == []


def test_invalid_duplicate_threshold_is_rejected():
    with pytest.raises(ValueError):
        suppress_nested_duplicates([], containment_threshold=0)
