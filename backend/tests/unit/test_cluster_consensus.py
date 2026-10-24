from app.services.product_matching.cluster_consensus import (
    catalogue_consensus,
    merge_clusters_by_catalog_consensus,
)


def _item(index, candidate_id, *, row=0, status="matched", quality="usable"):
    return {
        "id": f"prod_{index}",
        "row_number": row + 1,
        "quality_status": quality,
        "catalog_match": {
            "status": status,
            "similarity": 0.93 if status == "matched" else 0.82,
            "top_candidate": {"id": candidate_id, "sku": f"SKU-{candidate_id}", "name": f"Product {candidate_id}"},
        },
    }


def test_same_row_majority_merges_fragmented_clusters_but_preserves_other_product():
    items = [_item(1, 200), _item(2, 200), _item(3, 200), _item(4, 201)]
    clusters = [
        {"cluster_id": 1, "member_indices": [0], "similarity_percentage": 100.0},
        {"cluster_id": 2, "member_indices": [1], "similarity_percentage": 100.0},
        {"cluster_id": 3, "member_indices": [2], "similarity_percentage": 100.0},
        {"cluster_id": 4, "member_indices": [3], "similarity_percentage": 100.0},
    ]

    merged = merge_clusters_by_catalog_consensus(clusters, items)

    assert len(merged) == 2
    chocolate = next(cluster for cluster in merged if len(cluster["member_indices"]) == 3)
    assert chocolate["member_indices"] == [0, 1, 2]
    assert {items[index]["cluster_id"] for index in [0, 1, 2]} == {chocolate["cluster_id"]}
    assert items[3]["cluster_id"] != chocolate["cluster_id"]
    assert catalogue_consensus([items[index] for index in chocolate["member_indices"]])["status"] == "matched"


def test_clusters_are_never_merged_across_rows():
    items = [_item(1, 200, row=0), _item(2, 200, row=1)]
    clusters = [
        {"cluster_id": 1, "member_indices": [0], "similarity_percentage": 100.0},
        {"cluster_id": 2, "member_indices": [1], "similarity_percentage": 100.0},
    ]

    assert len(merge_clusters_by_catalog_consensus(clusters, items)) == 2


def test_row_with_no_usable_catalogue_votes_is_left_unmerged():
    items = [
        _item(1, 200, status="needs_review", quality="review"),
        _item(2, 201, status="needs_review", quality="review"),
    ]
    clusters = [
        {"cluster_id": 1, "member_indices": [0], "similarity_percentage": 100.0},
        {"cluster_id": 2, "member_indices": [1], "similarity_percentage": 100.0},
    ]

    merged = merge_clusters_by_catalog_consensus(clusters, items)

    assert len(merged) == 2
    assert sorted(cluster["member_indices"] for cluster in merged) == [[0], [1]]


def test_visual_cluster_spanning_rows_is_split_before_catalogue_consensus():
    items = [_item(1, 200, row=0), _item(2, 200, row=1)]
    clusters = [{"cluster_id": 1, "member_indices": [0, 1], "similarity_percentage": 98.0}]

    split = merge_clusters_by_catalog_consensus(clusters, items)

    assert len(split) == 2
    assert sorted(cluster["member_indices"] for cluster in split) == [[0], [1]]


def test_dissenting_candidate_is_not_absorbed_from_a_mixed_visual_cluster():
    items = [_item(1, 200), _item(2, 200), _item(3, 201)]
    clusters = [{"cluster_id": 1, "member_indices": [0, 2], "similarity_percentage": 89.0}]
    clusters.extend([
        {"cluster_id": 2, "member_indices": [1], "similarity_percentage": 100.0},
    ])

    merged = merge_clusters_by_catalog_consensus(clusters, items)

    assert any(cluster["member_indices"] == [0, 1] for cluster in merged)
    assert any(cluster["member_indices"] == [2] for cluster in merged)


def test_low_quality_and_unconfirmed_crop_votes_cannot_confirm_cluster_identity():
    members = [
        _item(1, 200, status="matched"),
        _item(2, 200, status="needs_review", quality="review"),
        _item(3, 201, status="needs_review"),
    ]

    result = catalogue_consensus(members)

    assert result["status"] == "needs_review"
    assert result["candidate"]["id"] == 200
    assert result["support_count"] == 1
    assert result["considered_count"] == 2


def test_singleton_cluster_is_not_confirmed_by_consensus():
    result = catalogue_consensus([_item(1, 200)])

    assert result["status"] == "needs_review"
    assert result["reason"] == "insufficient_confirmed_consensus"
