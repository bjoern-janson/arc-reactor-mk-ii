from arc_mkii.canonical import canonical_bytes, canonical_id
from arc_mkii.domain import Menu


def permute_faults(mask: int, permutation: tuple[int, ...]) -> int:
    out = 0
    for old_fault, new_fault in enumerate(permutation):
        if (mask >> old_fault) & 1:
            out |= 1 << new_fault
    return out


def test_identity_ignores_fault_renaming_query_order_and_answer_complement():
    base = Menu((15, 23, 51, 85))
    renamed = Menu(tuple(permute_faults(q, (7, 6, 5, 4, 3, 2, 1, 0)) for q in reversed(base.queries)))
    complemented = Menu(tuple(q ^ 0xFF for q in base.queries))
    assert canonical_bytes(base) == canonical_bytes(renamed)
    assert canonical_bytes(base) == canonical_bytes(complemented)
    assert canonical_id(base) == canonical_id(renamed)


def test_canonical_bytes_are_exactly_eight_row_bytes():
    assert len(canonical_bytes(Menu((15, 23, 51, 85)))) == 8


def test_structurally_different_menus_can_have_different_ids():
    assert canonical_id(Menu((15, 23, 51, 85))) != canonical_id(Menu((1, 2, 4, 8)))
