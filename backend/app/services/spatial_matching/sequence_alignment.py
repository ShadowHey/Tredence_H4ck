"""Describe expected and observed free intervals in normalized shelf coordinates."""

from __future__ import annotations

from typing import Any


def align_sequences(expected: list[dict[str, Any]], actual: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Monotonically align ordered facings and detections using normalized geometry.

    Gap operations are retained explicitly. This is diagnostic evidence; compliance
    identity decisions continue to use the existing catalogue/slot audit policy.
    """
    gap_cost = 0.35
    rows = len(expected) + 1
    cols = len(actual) + 1
    cost = [[0.0] * cols for _ in range(rows)]
    action = [[""] * cols for _ in range(rows)]
    for i in range(1, rows):
        cost[i][0], action[i][0] = i * gap_cost, "missing"
    for j in range(1, cols):
        cost[0][j], action[0][j] = j * gap_cost, "unexpected"
    for i in range(1, rows):
        for j in range(1, cols):
            exp, obs = expected[i - 1], actual[j - 1]
            center_delta = abs(float(exp["normalized_center"]) - float(obs["normalized_center"]))
            width_delta = abs((float(exp["normalized_end"]) - float(exp["normalized_start"]))
                              - (float(obs["normalized_end"]) - float(obs["normalized_start"])))
            pair_cost = min(1.0, center_delta * 2.0 + width_delta * 0.25)
            choices = [(cost[i - 1][j - 1] + pair_cost, "pair"),
                       (cost[i - 1][j] + gap_cost, "missing"),
                       (cost[i][j - 1] + gap_cost, "unexpected")]
            cost[i][j], action[i][j] = min(choices, key=lambda item: (item[0], item[1]))
    aligned = []
    i, j = len(expected), len(actual)
    while i or j:
        step = action[i][j]
        if step == "pair":
            exp, obs = expected[i - 1], actual[j - 1]
            aligned.append({"status": "paired", "slot_id": exp.get("slot_id"),
                            "cutout_id": obs.get("cutout_id"),
                            "position_cost": round(min(1.0, abs(float(exp["normalized_center"])
                                - float(obs["normalized_center"])) * 2.0), 6)})
            i -= 1
            j -= 1
        elif step == "missing":
            aligned.append({"status": "missing_expected", "slot_id": expected[i - 1].get("slot_id"), "cutout_id": None})
            i -= 1
        else:
            aligned.append({"status": "unexpected_observed", "slot_id": None, "cutout_id": actual[j - 1].get("cutout_id")})
            j -= 1
    return list(reversed(aligned))


def free_intervals(items: list[dict[str, Any]], *, start_key: str, end_key: str) -> list[dict[str, float]]:
    """Return uncovered intervals in [0, 1], clipping overlapping detections safely."""
    cursor = 0.0
    gaps: list[dict[str, float]] = []
    for item in sorted(items, key=lambda value: (value[start_key], value[end_key])):
        start = max(0.0, min(1.0, float(item[start_key])))
        end = max(start, min(1.0, float(item[end_key])))
        if start - cursor > 1e-4:
            gaps.append({"normalized_start": round(cursor, 6), "normalized_end": round(start, 6)})
        cursor = max(cursor, end)
    if 1.0 - cursor > 1e-4:
        gaps.append({"normalized_start": round(cursor, 6), "normalized_end": 1.0})
    return gaps
