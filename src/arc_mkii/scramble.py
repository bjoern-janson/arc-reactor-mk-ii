from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import replace
from typing import Iterable

from .corpus import TrainingRow

SCHEMA = "arc-reactor-mkii-scramble/v0"


def _strata(rows: Iterable[TrainingRow]) -> dict[tuple[int, int], list[TrainingRow]]:
    grouped: dict[tuple[int, int], list[TrainingRow]] = defaultdict(list)
    for row in rows:
        grouped[(row.budget, row.decision_depth)].append(row)
    for key in grouped:
        grouped[key].sort(key=lambda row: row.row_id)
    return dict(grouped)


def _offset(budget: int, depth: int, n: int) -> int:
    if n <= 1:
        return 0
    seed = f"arc-reactor-mk-ii/v0/scramble/{budget}/{depth}".encode()
    return 1 + (int.from_bytes(hashlib.sha256(seed).digest()[:8], "big") % (n - 1))


def _row_ids_sha256(ordered: list[TrainingRow]) -> str:
    payload = b"\n".join(row.row_id.encode("ascii") for row in ordered)
    return hashlib.sha256(b"arc-mkii-row-id-list-v0\0" + payload).hexdigest()


def scramble_descriptor(rows: Iterable[TrainingRow]) -> dict[str, object]:
    grouped = _strata(rows)
    strata = []
    for budget, depth in sorted(grouped):
        ordered = grouped[(budget, depth)]
        strata.append(
            {
                "budget": budget,
                "decision_depth": depth,
                "size": len(ordered),
                "offset": _offset(budget, depth, len(ordered)),
                "row_ids_sha256": _row_ids_sha256(ordered),
            }
        )
    return {"schema": SCHEMA, "strata": strata}


def scramble_feedback(rows: Iterable[TrainingRow]) -> list[TrainingRow]:
    source_rows = list(rows)
    grouped = _strata(source_rows)
    feedback_by_id: dict[str, int] = {}
    for (budget, depth), ordered in grouped.items():
        n = len(ordered)
        offset = _offset(budget, depth, n)
        for i, destination in enumerate(ordered):
            feedback_by_id[destination.row_id] = ordered[(i + offset) % n].feedback
    return [replace(row, feedback=feedback_by_id[row.row_id]) for row in source_rows]
