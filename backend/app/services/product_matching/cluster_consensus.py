"""Conservative row-scoped catalogue consensus for visual crop clusters."""

from __future__ import annotations

from collections import Counter, defaultdict
from math import ceil
from typing import Any


CONSENSUS_RATIO = 0.60
MIN_CONSENSUS_VOTES = 2


def _row_key(item: dict[str, Any]) -> tuple[str, Any] | None:
    """Return a stable shelf-row key; never merge clusters without row evidence."""
    position = item.get("planogram_position")
    if isinstance(position, dict) and position.get("row_index") is not None:
        return ("row_index", position["row_index"])
    row_number = item.get("row_number")
    if row_number is not None:
        return ("row_number", row_number)
    return None


def _candidate_vote(item: dict[str, Any]) -> tuple[int, dict[str, Any]] | None:
    # A suspicious detector crop is evidence for review, not a catalogue vote.
    if item.get("quality_status") == "review":
        return None
    match = item.get("catalog_match")
    candidate = match.get("top_candidate") if isinstance(match, dict) else None
    if not isinstance(candidate, dict) or candidate.get("id") is None:
        return None
    return int(candidate["id"]), candidate


def merge_clusters_by_catalog_consensus(
    clusters: list[dict[str, Any]], items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge fragmented visual clusters only when same-row catalogue votes agree.

    The merge is intentionally identity-led and only acts on clusters with at least
    two usable votes and a 60% leading candidate. Uncertain clusters and detections
    without row calibration remain separate. All member indices are retained.
    """
    # A visual leader cluster may span rows, so split it before any catalogue vote.
    row_scoped: list[dict[str, Any]] = []
    for cluster in clusters:
        partitions: dict[tuple[str, Any] | None, list[int]] = defaultdict(list)
        for index in cluster["member_indices"]:
            partitions[_row_key(items[index])].append(index)
        for indices in partitions.values():
            scoped = dict(cluster)
            scoped["member_indices"] = indices
            scoped["cluster_id"] = len(row_scoped) + 1
            row_scoped.append(scoped)

    row_votes: dict[tuple[str, Any], Counter[int]] = defaultdict(Counter)
    cluster_evidence: dict[int, tuple[tuple[str, Any] | None, Counter[int], int]] = {}
    for cluster in row_scoped:
        members = [items[index] for index in cluster["member_indices"]]
        rows = {_row_key(item) for item in members}
        row = next(iter(rows)) if len(rows) == 1 else None
        votes = [vote for item in members if (vote := _candidate_vote(item)) is not None]
        counts = Counter(candidate_id for candidate_id, _ in votes)
        if row is not None:
            row_votes[row].update(candidate_id for candidate_id, _ in votes)
        cluster_evidence[cluster["cluster_id"]] = (row, counts, len(votes))

    row_leaders: dict[tuple[str, Any], int] = {}
    for row, counts in row_votes.items():
        total = sum(counts.values())
        if total < MIN_CONSENSUS_VOTES:
            continue
        leader_id, leader_count = counts.most_common(1)[0]
        if total >= MIN_CONSENSUS_VOTES and leader_count >= max(MIN_CONSENSUS_VOTES, ceil(total * CONSENSUS_RATIO)):
            row_leaders[row] = leader_id

    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for cluster in row_scoped:
        row, _counts, _vote_count = cluster_evidence[cluster["cluster_id"]]
        row_leader = row_leaders.get(row) if row is not None else None
        if row_leader is None:
            groups[("unmerged", cluster["cluster_id"])].append(cluster)
            continue

        # Split dissenting top-candidate crops out before merging the row's majority
        # identity. This keeps a misplaced/visually distinct item from being absorbed
        # merely because it shared a noisy visual leader cluster with many products.
        candidate_buckets: dict[int | None, list[int]] = defaultdict(list)
        for index in cluster["member_indices"]:
            vote = _candidate_vote(items[index])
            candidate_buckets[vote[0] if vote is not None else None].append(index)
        for candidate_id, indices in candidate_buckets.items():
            fragment = dict(cluster)
            fragment["member_indices"] = indices
            key = ((row, row_leader) if candidate_id == row_leader
                   else ("dissent", cluster["cluster_id"], candidate_id))
            groups[key].append(fragment)

    merged: list[dict[str, Any]] = []
    for group in groups.values():
        base = dict(group[0])
        indices = sorted(index for cluster in group for index in cluster["member_indices"])
        base["member_indices"] = indices
        merged.append(base)
    merged.sort(key=lambda cluster: min(cluster["member_indices"]) if cluster["member_indices"] else 0)
    for cluster_id, cluster in enumerate(merged, start=1):
        cluster["cluster_id"] = cluster_id
        for index in cluster["member_indices"]:
            items[index]["cluster_id"] = cluster_id
    return merged


def catalogue_consensus(members: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize crop-level predictions without overwriting their individual states."""
    votes = [vote for item in members if (vote := _candidate_vote(item)) is not None]
    counts = Counter(candidate_id for candidate_id, _ in votes)
    if not votes:
        return {"status": "needs_review", "reason": "no_usable_crop_votes", "support_count": 0,
                "considered_count": 0, "support_ratio": 0.0, "candidate": None}

    candidate_id, support = counts.most_common(1)[0]
    candidate = next(product for voted_id, product in votes if voted_id == candidate_id)
    ratio = support / len(votes)
    supported = support >= max(MIN_CONSENSUS_VOTES, ceil(len(votes) * CONSENSUS_RATIO))
    confirmed_votes = sum(
        1 for item in members
        if isinstance(item.get("catalog_match"), dict)
        and item["catalog_match"].get("status") == "matched"
        and isinstance(item["catalog_match"].get("top_candidate"), dict)
        and item["catalog_match"]["top_candidate"].get("id") == candidate_id
        and item.get("quality_status") != "review"
    )
    confirmed = supported and confirmed_votes >= max(MIN_CONSENSUS_VOTES, ceil(len(members) * CONSENSUS_RATIO))
    return {
        "status": "matched" if confirmed else "needs_review",
        "reason": "majority_catalogue_match" if confirmed else "insufficient_confirmed_consensus",
        "support_count": support,
        "considered_count": len(votes),
        "support_ratio": round(ratio, 4),
        "candidate": candidate,
    }
