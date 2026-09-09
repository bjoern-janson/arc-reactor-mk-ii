from __future__ import annotations

import hashlib
import itertools

from .domain import Menu, answer


def canonical_bytes(menu: Menu) -> bytes:
    best: bytes | None = None
    for perm in itertools.permutations(range(4)):
        for complement_bits in range(16):
            rows: list[int] = []
            for fault in range(8):
                row = 0
                for out_col, source_col in enumerate(perm):
                    bit = answer(menu.queries[source_col], fault)
                    if (complement_bits >> out_col) & 1:
                        bit ^= 1
                    row |= bit << out_col
                rows.append(row)
            candidate = bytes(sorted(rows))
            if best is None or candidate < best:
                best = candidate
    if best is None:
        raise RuntimeError("canonicalization produced no candidate")
    return best


def canonical_id(menu: Menu) -> str:
    return hashlib.sha256(b"arc-mkii-task-v0\0" + canonical_bytes(menu)).hexdigest()
