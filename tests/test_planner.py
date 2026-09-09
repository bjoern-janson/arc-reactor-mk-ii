from arc_mkii.domain import Menu
from arc_mkii.planner import planner_reference, planner_success_count


def test_exact_planner_solves_coordinate_menu_with_budget_three():
    menu = Menu((15, 23, 51, 85))
    assert planner_success_count(menu, budget=3) == 8


def test_planner_reports_positive_state_work_without_changing_answer():
    result = planner_reference(Menu((15, 23, 51, 85)), budget=3)
    assert result.success_count == 8
    assert result.states_expanded > 0
