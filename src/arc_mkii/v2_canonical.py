from __future__ import annotations

import hashlib
import itertools

from .domain import SixQueryArena

FAMILY_PREFIX = b"arc-mkii-v2-six-query-gladiator-family\0"
_QUERY_PERMS = tuple(itertools.permutations(range(6)))


def _permute_row(row: int, perm: tuple[int, ...]) -> int:
    out = 0
    for out_col, source_col in enumerate(perm):
        out |= ((row >> source_col) & 1) << out_col
    return out


_PERM_TABLE = tuple(
    tuple(_permute_row(row, perm) for row in range(64))
    for perm in _QUERY_PERMS
)


def _rows(arena: SixQueryArena) -> tuple[int, ...]:
    return tuple(
        sum(((query >> fault) & 1) << column for column, query in enumerate(arena.queries))
        for fault in range(8)
    )


def canonical_bytes(arena: SixQueryArena) -> bytes:
    rows = _rows(arena)
    best: bytes | None = None
    for anchor in set(rows):
        translated = tuple(row ^ anchor for row in rows)
        for table in _PERM_TABLE:
            candidate = bytes(sorted(table[row] for row in translated))
            if best is None or candidate < best:
                best = candidate
    if best is None:
        raise RuntimeError("V2 arena contained no fault rows")
    return best


def family_id(arena: SixQueryArena) -> str:
    return hashlib.sha256(FAMILY_PREFIX + canonical_bytes(arena)).hexdigest()
