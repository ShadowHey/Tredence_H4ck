"""
Unit and integration tests for Bounding Box Cutout Extraction, Clustering, and Catalog Matching.
"""

from __future__ import annotations

import math
from PIL import Image
import pytest
from app.services.cutout_service import (
    CATALOG_MATCH_THRESHOLD,
    INTRA_CLUSTER_SIMILARITY_THRESHOLD,
    _safe_clamp,
    _normalize_vector,
)
from app.services.embedding_service import embedding_service


def test_safe_clamp():
    assert _safe_clamp(-10, 100) == 0
    assert _safe_clamp(50, 100) == 50
    assert _safe_clamp(150, 100) == 100
    assert _safe_clamp(0, 100) == 0
    assert _safe_clamp(100, 100) == 100


def test_normalize_vector():
    vec = [3.0, 4.0]
    normed = _normalize_vector(vec)
    length = math.sqrt(sum(x * x for x in normed))
    assert math.isclose(length, 1.0, rel_tol=1e-5)


def test_catalog_match_threshold_rule():
    """Verify that catalog match requires confidence >= 90% (0.900)."""
    assert CATALOG_MATCH_THRESHOLD == 0.90

    # Test cases below and at/above threshold
    below_score = 0.899
    exact_score = 0.900
    above_score = 0.978

    assert (below_score >= CATALOG_MATCH_THRESHOLD) is False
    assert (exact_score >= CATALOG_MATCH_THRESHOLD) is True
    assert (above_score >= CATALOG_MATCH_THRESHOLD) is True


def test_batch_embedding_computation():
    """Verify compute_image_embeddings_batch produces expected 512-dim normalized vectors."""
    # Create 3 tiny in-memory images
    imgs = [
        Image.new("RGB", (32, 32), color=(255, 0, 0)),
        Image.new("RGB", (32, 32), color=(0, 255, 0)),
        Image.new("RGB", (32, 32), color=(0, 0, 255)),
    ]

    vecs = embedding_service.compute_image_embeddings_batch(imgs, batch_size=2)
    assert len(vecs) == 3
    for v in vecs:
        assert len(v) == 512
        # Check L2 unit length
        length = math.sqrt(sum(x * x for x in v))
        assert math.isclose(length, 1.0, rel_tol=1e-4)


def test_batch_embedding_empty():
    assert embedding_service.compute_image_embeddings_batch([]) == []
