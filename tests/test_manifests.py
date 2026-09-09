import inspect

from arc_mkii.canonical import canonical_id
from arc_mkii.manifests import generate_protocol_menus, protocol_record


def test_protocol_split_is_exact_disjoint_and_deterministic():
    train_a, eval_a = generate_protocol_menus()
    train_b, eval_b = generate_protocol_menus()
    assert train_a == train_b
    assert eval_a == eval_b
    assert len(train_a) == 256
    assert len(eval_a) == 64
    train_ids = {canonical_id(m) for m in train_a}
    eval_ids = {canonical_id(m) for m in eval_a}
    assert len(train_ids) == 256
    assert len(eval_ids) == 64
    assert train_ids.isdisjoint(eval_ids)


def test_manifest_generator_has_no_outcome_or_learner_input():
    assert list(inspect.signature(generate_protocol_menus).parameters) == []


def test_protocol_record_pins_scientific_constants_and_scope():
    record = protocol_record()
    assert record["schema"] == "arc-reactor-mkii-protocol/v0"
    assert record["fault_count"] == 8
    assert record["query_count"] == 4
    assert record["budgets"] == [2, 3]
    assert record["train_count"] == 256
    assert record["eval_count"] == 64
    assert record["feature_count"] == 8
    assert record["ridge_lambda"] == {"n": 1, "d": 100}
    assert "same eight-fault universe" in record["scope"]
