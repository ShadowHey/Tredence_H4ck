"""Optional ArUco calibration markers for controlled shelf photographs."""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np


CORNER_MARKER_IDS = {0: "top_left", 1: "top_right", 2: "bottom_right", 3: "bottom_left"}


def detect_shelf_corner_markers(image: np.ndarray) -> dict[str, Any]:
    """Return four marker-centre anchors in TL,TR,BR,BL order, if all are visible.

    Markers use OpenCV DICT_4X4_50 IDs 0–3, with each marker centre placed at
    the corresponding usable-shelf boundary corner. Missing/duplicate markers
    are non-fatal; the consumer then uses detected-row straight-on calibration.
    """
    unavailable = {
        "status": "not_detected",
        "source": "aruco_dict_4x4_50_ids_0_to_3",
        "reason": "four_unique_corner_markers_not_found",
        "shelf_corners_xy": None,
    }
    aruco = getattr(cv2, "aruco", None)
    if aruco is None or image is None or image.size == 0:
        return unavailable

    dictionary = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
    if hasattr(aruco, "ArucoDetector"):
        detector = aruco.ArucoDetector(dictionary, aruco.DetectorParameters())
        corners, ids, _ = detector.detectMarkers(image)
    else:  # OpenCV 4.8 API compatibility
        corners, ids, _ = aruco.detectMarkers(image, dictionary)
    if ids is None:
        return unavailable

    centers: dict[int, list[float]] = {}
    duplicate_ids: set[int] = set()
    for marker_corners, marker_id in zip(corners, ids.flatten().tolist()):
        if marker_id not in CORNER_MARKER_IDS:
            continue
        if marker_id in centers:
            duplicate_ids.add(int(marker_id))
            continue
        center = np.asarray(marker_corners, dtype=np.float64).reshape(-1, 2).mean(axis=0)
        centers[int(marker_id)] = [round(float(center[0]), 3), round(float(center[1]), 3)]

    if set(centers) != set(CORNER_MARKER_IDS) or duplicate_ids:
        return unavailable
    return {
        "status": "detected",
        "source": "aruco_dict_4x4_50_ids_0_to_3",
        "reason": None,
        "marker_ids": {name: marker_id for marker_id, name in CORNER_MARKER_IDS.items()},
        "shelf_corners_xy": [centers[marker_id] for marker_id in (0, 1, 2, 3)],
    }
