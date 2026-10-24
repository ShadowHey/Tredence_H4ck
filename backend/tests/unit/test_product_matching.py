from PIL import Image

from app.services.product_matching.candidate_filtering import filter_candidates_by_color
from app.services.product_matching.color_handling import color_similarity


def _rgb(color: tuple[int, int, int], size: tuple[int, int] = (48, 96)) -> Image.Image:
    return Image.new("RGB", size, color)


def test_color_filter_removes_visibly_incompatible_candidates_before_clip():
    crop = _rgb((76, 38, 19))
    packshots = {
        "juice.png": _rgb((255, 125, 5)),
        "chocolate.png": _rgb((82, 42, 22)),
    }
    candidates = [
        {"id": 1, "sku": "JUICE", "image_path": "juice.png"},
        {"id": 2, "sku": "CHOC", "image_path": "chocolate.png"},
    ]

    result = filter_candidates_by_color(crop, candidates, packshots.get)

    assert [item["sku"] for item in result["candidates"]] == ["CHOC"]
    assert result["candidate_count_before"] == 2
    assert result["candidate_count_after"] == 1
    assert result["fallback"] is False
    assert result["scores"][1] < 0.30
    assert result["scores"][2] >= 0.30


def test_color_gate_relaxes_to_best_color_candidates_and_marks_fallback():
    crop = _rgb((76, 38, 19))
    candidates = [
        {"id": 1, "sku": "GREEN", "image_path": "green.png"},
        {"id": 2, "sku": "BLUE", "image_path": "blue.png"},
    ]
    packshots = {"green.png": _rgb((0, 255, 0)), "blue.png": _rgb((0, 0, 255))}

    result = filter_candidates_by_color(crop, candidates, packshots.get)

    assert result["fallback"] is True
    assert result["fallback_reason"] == "no_candidates_passed_color_threshold"
    assert result["candidates"]
    assert all(score < result["threshold"] for score in result["scores"].values())


def test_missing_packshots_keep_candidates_but_report_unavailable_color_evidence():
    candidates = [{"id": 1, "sku": "SKU", "image_path": "missing.png"}]

    result = filter_candidates_by_color(_rgb((120, 80, 40)), candidates, lambda _path: None)

    assert result["candidates"] == candidates
    assert result["fallback"] is True
    assert result["fallback_reason"] == "catalogue_packshot_color_unavailable"
    assert result["scores"][1] is None


def test_color_similarity_is_bounded_and_distinguishes_brown_from_orange():
    chocolate = _rgb((76, 38, 19))
    chocolate_packshot = _rgb((82, 42, 22))
    orange = _rgb((255, 125, 5))

    assert 0.0 <= color_similarity(chocolate, orange) <= 1.0
    assert color_similarity(chocolate, chocolate_packshot) > color_similarity(chocolate, orange)
