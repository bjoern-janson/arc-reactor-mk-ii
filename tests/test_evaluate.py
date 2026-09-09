from fractions import Fraction
from types import SimpleNamespace

from arc_mkii.domain import Menu
from arc_mkii.evaluate import evaluate_theta, ignition_pass, transplant_equivalent
from arc_mkii.selector import THETA0


def test_same_theta_in_fresh_hosts_has_identical_traces_and_scores():
    menus = [Menu((15, 23, 51, 85))]
    theta = tuple(Fraction(x) for x in THETA0)
    left = evaluate_theta("left", theta, menus)
    right = evaluate_theta("right", theta, menus)
    assert left.case_traces == right.case_traces
    assert left.success_by_budget == right.success_by_budget


def test_transplant_equivalence_compares_behavior_not_object_identity():
    menus = [Menu((15, 23, 51, 85))]
    theta = tuple(Fraction(x) for x in THETA0)
    assert transplant_equivalent(tuple(theta), tuple(theta), menus)


def test_ignition_requires_strict_win_somewhere_and_no_loss_elsewhere():
    learn = SimpleNamespace(success_by_budget={2: 10, 3: 20})
    scrambled = SimpleNamespace(success_by_budget={2: 9, 3: 20})
    frozen = SimpleNamespace(success_by_budget={2: 9, 3: 19})
    assert ignition_pass(learn, scrambled, frozen, transplant_ok=True)
    learn_tradeoff = SimpleNamespace(success_by_budget={2: 10, 3: 18})
    assert not ignition_pass(learn_tradeoff, scrambled, frozen, transplant_ok=True)


def test_resource_report_has_raw_vector_fields():
    result = evaluate_theta("frozen", tuple(Fraction(x) for x in THETA0), [Menu((15, 23, 51, 85))])
    report = result.resources
    assert report.primitive_query_executions > 0
    assert report.terminal_actions == 16
    assert report.feature_vectors_computed > 0
    assert report.public_truth_table_bit_inspections > 0
    assert not hasattr(report, "weighted_total")
