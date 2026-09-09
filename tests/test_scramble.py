from collections import Counter

from arc_mkii.corpus import build_training_rows
from arc_mkii.domain import Menu
from arc_mkii.scramble import scramble_descriptor, scramble_feedback


def test_scramble_preserves_feedback_multiset_within_each_budget_depth_stratum():
    rows = build_training_rows([Menu((15, 23, 51, 85)), Menu((1, 2, 4, 8))])
    scrambled_a = scramble_feedback(rows)
    scrambled_b = scramble_feedback(rows)
    assert scrambled_a == scrambled_b
    for key in {(r.budget, r.decision_depth) for r in rows}:
        original = [r.feedback for r in rows if (r.budget, r.decision_depth) == key]
        changed = [s.feedback for s in scrambled_a if (s.budget, s.decision_depth) == key]
        assert Counter(original) == Counter(changed)


def test_scramble_descriptor_is_deterministic_and_reconstructive_metadata():
    rows = build_training_rows([Menu((15, 23, 51, 85))])
    descriptor = scramble_descriptor(rows)
    assert descriptor["schema"] == "arc-reactor-mkii-scramble/v0"
    assert descriptor == scramble_descriptor(rows)
    assert descriptor["strata"]
    assert all(set(item) == {"budget", "decision_depth", "size", "offset", "row_ids_sha256"} for item in descriptor["strata"])
