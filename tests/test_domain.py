from arc_mkii.domain import Menu, answer, normalize_partition


def test_partition_normalization_identifies_answer_complements():
    assert normalize_partition(0b11110000) == 0b00001111
    assert normalize_partition(0b00001111) == 0b00001111


def test_menu_requires_four_distinct_nonconstant_partitions():
    menu = Menu((15, 23, 51, 85))
    assert menu.queries == (15, 23, 51, 85)


def test_query_answer_reads_fault_bit_from_truth_mask():
    assert answer(0b00001000, 3) == 1
    assert answer(0b00001000, 2) == 0
