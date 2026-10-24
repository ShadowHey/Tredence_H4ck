from app.services import cutout_service
from app.services.cutout_service import _count_calibrated_positions


def test_count_calibrated_positions_tolerates_unavailable_null_and_valid_positions():
    detections = [
        {"id": "missing-position"},
        {"id": "explicit-null", "planogram_position": None},
        {"id": "needs-review", "planogram_position": {"status": "needs_review"}},
        {"id": "mapped", "planogram_position": {"status": "calibrated"}},
    ]

    assert _count_calibrated_positions(detections) == 1


def test_catalog_match_accepts_clear_match_at_calibrated_90_percent(monkeypatch):
    monkeypatch.setattr(cutout_service.embedding_service, "cosine_similarity", lambda _a, b: b[0])
    catalogue = [
        {"id": 1, "sku": "SKU-A", "name": "Expected product", "embedding": [0.93] + [0.0] * 511},
        {"id": 2, "sku": "SKU-B", "name": "Other product", "embedding": [0.80] + [0.0] * 511},
    ]

    result = cutout_service._catalogue_match([1.0] + [0.0] * 511, catalogue, True)

    assert result["status"] == "matched"
    assert result["top_candidate"]["sku"] == "SKU-A"
    assert result["similarity_threshold"] == 0.90


def test_catalog_match_below_threshold_is_review_not_false_unrecognised_alert(monkeypatch):
    monkeypatch.setattr(cutout_service.embedding_service, "cosine_similarity", lambda _a, b: b[0])
    catalogue = [{"id": 1, "sku": "SKU-A", "name": "Expected product", "embedding": [0.89] + [0.0] * 511}]

    result = cutout_service._catalogue_match([1.0] + [0.0] * 511, catalogue, True)

    assert result["status"] == "needs_review"
    assert result["reason"] == "below_similarity_threshold"


def test_catalog_match_with_ambiguous_clip_margin_remains_review_needed(monkeypatch):
    scores = {0.93: 0.93, 0.92: 0.92}
    monkeypatch.setattr(cutout_service.embedding_service, "cosine_similarity", lambda _a, b: scores[b[0]])
    catalogue = [
        {"id": 1, "sku": "SKU-A", "name": "Candidate A", "embedding": [0.93] + [0.0] * 511},
        {"id": 2, "sku": "SKU-B", "name": "Candidate B", "embedding": [0.92] + [0.0] * 511},
    ]

    result = cutout_service._catalogue_match([1.0] + [0.0] * 511, catalogue, True)

    assert result["top_candidate"]["sku"] == "SKU-A"
    assert result["runner_up"]["sku"] == "SKU-B"
    assert result["confidence_margin"] == 0.01
    assert result["status"] == "needs_review"
    assert result["reason"] == "ambiguous_candidates"


def test_catalogue_match_color_filters_orange_before_clip_ranks_remaining_product(monkeypatch, tmp_path):
    from PIL import Image

    crop = Image.new("RGB", (48, 96), (76, 38, 19))
    juice_path = tmp_path / "juice.png"
    chocolate_path = tmp_path / "chocolate.png"
    Image.new("RGB", (48, 96), (255, 125, 5)).save(juice_path)
    Image.new("RGB", (48, 96), (82, 42, 22)).save(chocolate_path)
    paths = {"juice.png": juice_path, "chocolate.png": chocolate_path}
    monkeypatch.setattr(cutout_service.embedding_service, "resolve_image_path", lambda path: paths.get(path))
    # CLIP alone prefers juice, but that candidate must be removed before cosine ranking.
    monkeypatch.setattr(cutout_service.embedding_service, "cosine_similarity", lambda _a, b: b[0])
    catalogue = [
        {"id": 1, "sku": "JUICE", "name": "Orange Juice", "image_path": "juice.png", "embedding": [0.94] + [0.0] * 511},
        {"id": 2, "sku": "CHOC", "name": "Amul Dark Chocolate", "image_path": "chocolate.png", "embedding": [0.82] + [0.0] * 511},
    ]

    result = cutout_service._catalogue_match([1.0] + [0.0] * 511, catalogue, True, crop)

    assert result["top_candidate"]["sku"] == "CHOC"
    assert result["similarity"] == 0.82
    assert result["status"] == "needs_review"  # Still below the raw-CLIP confirmation threshold.
    assert result["matching_method"] == "color_filter_then_clip"
    assert result["color_filter_candidate_count_before"] == 2
    assert result["color_filter_candidate_count_after"] == 1
    assert result["color_filter_fallback"] is False


def test_catalogue_match_color_fallback_never_confirms_a_match(monkeypatch, tmp_path):
    from PIL import Image

    crop = Image.new("RGB", (48, 96), (76, 38, 19))
    green_path = tmp_path / "green.png"
    Image.new("RGB", (48, 96), (0, 255, 0)).save(green_path)
    monkeypatch.setattr(cutout_service.embedding_service, "resolve_image_path", lambda _path: green_path)
    monkeypatch.setattr(cutout_service.embedding_service, "cosine_similarity", lambda _a, _b: 0.99)
    catalogue = [{"id": 1, "sku": "GREEN", "image_path": "green.png", "embedding": [1.0] + [0.0] * 511}]

    result = cutout_service._catalogue_match([1.0] + [0.0] * 511, catalogue, True, crop)

    assert result["status"] == "needs_review"
    assert result["reason"] == "color_filter_fallback"
    assert result["color_filter_fallback"] is True
