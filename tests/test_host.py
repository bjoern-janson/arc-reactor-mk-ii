from arc_mkii.domain import Menu
from arc_mkii.host import execute_query, initial_state, terminal_repair


def test_query_filters_candidates_without_exposing_hidden_fault_to_selector_state():
    state = initial_state(Menu((15, 23, 51, 85)), fault=6, budget=3)
    next_state = execute_query(state, 0)
    assert next_state.candidate_mask != 0xFF
    assert 6 in next_state.candidates
    assert next_state.remaining_budget == 2


def test_terminal_repair_is_singleton_or_lowest_remaining_fault():
    state = initial_state(Menu((15, 23, 51, 85)), fault=6, budget=0)
    assert terminal_repair(state) == 0


def test_selector_view_contains_no_hidden_fault():
    state = initial_state(Menu((15, 23, 51, 85)), fault=6, budget=3)
    view = state.selector_view()
    assert not hasattr(view, "fault")
    assert view.candidate_mask == 0xFF
