from fractions import Fraction

from arc_mkii.domain import Menu
from arc_mkii.features import FEATURE_NAMES, feature_vector
from arc_mkii.host import initial_state


def test_feature_schema_is_exact_and_public_only():
    assert FEATURE_NAMES == (
        "intercept",
        "remaining_budget_over_3",
        "candidate_count_over_8",
        "smaller_child_fraction",
        "child_fraction_product",
        "singleton_child_candidate_fraction",
        "weighted_best_next_split",
        "worst_child_best_next_split",
    )
    view = initial_state(Menu((15, 23, 51, 85)), fault=0, budget=3).selector_view()
    f = feature_vector(view, 0)
    assert len(f) == 8
    assert all(isinstance(value, Fraction) for value in f)
    assert f[0] == Fraction(1, 1)
    assert f[1] == Fraction(1, 1)
    assert f[2] == Fraction(1, 1)
    assert f[3] == Fraction(1, 2)
