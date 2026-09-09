from __future__ import annotations

import hashlib

from .canonical import canonical_id
from .domain import Menu

SEED = b"arc-reactor-mk-ii/v0/menu-seed/2026-09-09"
TRAIN_COUNT = 256
EVAL_COUNT = 64
BUDGETS = (2, 3)


def _partition_from(seed: bytes, counter: int, slot: int) -> int:
    payload = seed + counter.to_bytes(8, "big") + slot.to_bytes(1, "big")
    digest = hashlib.sha256(payload).digest()
    return 1 + (int.from_bytes(digest[:8], "big") % 127)


def generate_protocol_menus() -> tuple[list[Menu], list[Menu]]:
    accepted: list[Menu] = []
    seen: set[str] = set()
    counter = 0
    while len(accepted) < TRAIN_COUNT + EVAL_COUNT:
        parts = tuple(_partition_from(SEED, counter, slot) for slot in range(4))
        counter += 1
        if len(set(parts)) != 4:
            continue
        menu = Menu(parts)
        cid = canonical_id(menu)
        if cid in seen:
            continue
        seen.add(cid)
        accepted.append(menu)
    return accepted[:TRAIN_COUNT], accepted[TRAIN_COUNT:]


def protocol_record() -> dict[str, object]:
    return {
        "schema": "arc-reactor-mkii-protocol/v0",
        "fault_count": 8,
        "query_count": 4,
        "budgets": [2, 3],
        "train_count": TRAIN_COUNT,
        "eval_count": EVAL_COUNT,
        "seed": SEED.decode("ascii"),
        "feature_count": 8,
        "ridge_lambda": {"n": 1, "d": 100},
        "scope": (
            "Evaluation novelty is limited to unseen canonical query "
            "configurations over the same eight-fault universe."
        ),
    }
