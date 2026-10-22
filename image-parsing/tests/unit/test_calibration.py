import cv2
import numpy as np

from shelf_image_parsing.calibration import detect_shelf_corner_markers


def _place_marker(image, marker_id, center, size=80):
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    marker = cv2.aruco.generateImageMarker(dictionary, marker_id, size)
    x = center[0] - size // 2
    y = center[1] - size // 2
    image[y:y + size, x:x + size] = cv2.cvtColor(marker, cv2.COLOR_GRAY2BGR)


def test_detects_four_ordered_shelf_corner_markers():
    image = np.full((600, 800, 3), 255, dtype=np.uint8)
    _place_marker(image, 0, (100, 100))
    _place_marker(image, 1, (700, 100))
    _place_marker(image, 2, (700, 500))
    _place_marker(image, 3, (100, 500))

    result = detect_shelf_corner_markers(image)

    assert result["status"] == "detected"
    np.testing.assert_allclose(
        result["shelf_corners_xy"],
        [[100.0, 100.0], [700.0, 100.0], [700.0, 500.0], [100.0, 500.0]],
        atol=0.5,
    )
    assert result["marker_ids"] == {
        "top_left": 0,
        "top_right": 1,
        "bottom_right": 2,
        "bottom_left": 3,
    }


def test_missing_corner_marker_is_a_nonfatal_fallback_signal():
    image = np.full((400, 500, 3), 255, dtype=np.uint8)
    _place_marker(image, 0, (70, 70))
    _place_marker(image, 1, (430, 70))
    _place_marker(image, 2, (430, 330))

    result = detect_shelf_corner_markers(image)

    assert result["status"] == "not_detected"
    assert result["shelf_corners_xy"] is None


def test_duplicate_corner_marker_is_rejected():
    image = np.full((600, 800, 3), 255, dtype=np.uint8)
    _place_marker(image, 0, (100, 100))
    _place_marker(image, 0, (180, 100))
    _place_marker(image, 1, (700, 100))
    _place_marker(image, 2, (700, 500))
    _place_marker(image, 3, (100, 500))

    result = detect_shelf_corner_markers(image)

    assert result["status"] == "not_detected"
    assert result["shelf_corners_xy"] is None
