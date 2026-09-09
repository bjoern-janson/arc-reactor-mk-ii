from arc_mkii.corpus import build_training_rows
from arc_mkii.domain import Menu


def test_corpus_uses_every_ordered_distinct_query_sequence_for_each_budget_and_fault():
    rows = build_training_rows([Menu((15, 23, 51, 85))])
    assert {row.budget for row in rows} == {2, 3}
    assert {row.fault for row in rows} == set(range(8))
    assert all(row.feedback in (0, 1) for row in rows)
    assert all(len(row.features) == 8 for row in rows)


def test_training_rows_have_unique_reconstructible_ids_for_one_menu():
    rows = build_training_rows([Menu((15, 23, 51, 85))])
    assert len({row.row_id for row in rows}) == len(rows)


def test_corpus_can_account_feature_and_query_work():
    from arc_mkii.resources import ResourceCounter

    resources = ResourceCounter()
    rows = build_training_rows([Menu((15, 23, 51, 85))], resources=resources)
    assert rows
    assert resources.feature_vectors_computed > 0
    assert resources.primitive_query_executions > 0
    assert resources.public_truth_table_bit_inspections > 0
    assert resources.terminal_actions > 0
