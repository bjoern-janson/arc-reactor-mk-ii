from itertools import permutations

from arc_mkii.domain import Menu
from arc_mkii.host import execute_query, initial_state, terminal_repair
from arc_mkii.selector import THETA0, choose_query


def test_theta0_has_one_balance_weight_and_seven_zero_weights():
    assert tuple(THETA0) == (0, 0, 0, 1, 0, 0, 0, 0)


def test_frozen_control_uses_public_query_order_for_exact_ties():
    view = initial_state(Menu((15, 23, 51, 85)), fault=0, budget=3).selector_view()
    assert choose_query(THETA0, view) == 0


def _success_for_sequence(menu, sequence):
    total = 0
    for fault in range(8):
        state = initial_state(menu, fault=fault, budget=3)
        for query_id in sequence:
            if len(state.candidates) == 1:
                break
            state = execute_query(state, query_id)
        total += terminal_repair(state) == fault
    return total


def test_hand_checkable_menu_query_order_matters():
    menu = Menu((15, 23, 51, 85))
    assert _success_for_sequence(menu, (0, 2, 3)) == 8
    best_after_majority = max(
        _success_for_sequence(menu, (1,) + pair)
        for pair in permutations((0, 2, 3), 2)
    )
    assert best_after_majority == 6
