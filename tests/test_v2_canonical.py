import itertools

from arc_mkii.domain import SixQueryArena
from arc_mkii.v2_canonical import canonical_bytes, family_id

WITNESS = SixQueryArena((16, 46, 89, 4, 45, 1))


def _rows(arena: SixQueryArena) -> tuple[int, ...]:
    return tuple(
        sum(((query >> fault) & 1) << column for column, query in enumerate(arena.queries))
        for fault in range(8)
    )


def _permute_row(row: int, perm: tuple[int, ...]) -> int:
    out = 0
    for out_col, source_col in enumerate(perm):
        out |= ((row >> source_col) & 1) << out_col
    return out


def _explicit_oracle(arena: SixQueryArena) -> bytes:
    rows = _rows(arena)
    best: bytes | None = None
    for complement in range(1 << 6):
        translated = tuple(row ^ complement for row in rows)
        for perm in itertools.permutations(range(6)):
            candidate = bytes(sorted(_permute_row(row, perm) for row in translated))
            if best is None or candidate < best:
                best = candidate
    assert best is not None
    return best


def _permute_faults(mask: int, perm: tuple[int, ...]) -> int:
    out = 0
    for new_fault, old_fault in enumerate(perm):
        out |= ((mask >> old_fault) & 1) << new_fault
    return out


def test_witness_has_exact_canonical_bytes_and_family_id():
    assert canonical_bytes(WITNESS) == bytes([0, 1, 2, 4, 9, 11, 26, 43])
    assert family_id(WITNESS) == "9444534fc7a1171614925bb2fee464aaf28835bb24dbd1e61454de6891c1b942"


def test_query_permutation_does_not_change_family():
    permuted = SixQueryArena(tuple(WITNESS.queries[i] for i in (5, 2, 0, 4, 1, 3)))
    assert family_id(permuted) == family_id(WITNESS)


def test_fault_permutation_does_not_change_family():
    permutation = (3, 0, 7, 2, 5, 1, 6, 4)
    renamed = SixQueryArena(tuple(_permute_faults(query, permutation) for query in WITNESS.queries))
    assert family_id(renamed) == family_id(WITNESS)


def test_optimized_canonicalization_matches_explicit_quotient():
    fixtures = (
        SixQueryArena((16, 46, 89, 4, 45, 1)),
        SixQueryArena((15, 23, 51, 85, 1, 3)),
        SixQueryArena((7, 11, 13, 19, 37, 73)),
    )
    for arena in fixtures:
        assert canonical_bytes(arena) == _explicit_oracle(arena)
