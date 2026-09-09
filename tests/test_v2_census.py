from arc_mkii.domain import SixQueryArena
from arc_mkii.v2_census import merge_parts, scan_records

ADMITTED = SixQueryArena((16, 46, 89, 4, 45, 1))
ADMITTED_ALIAS = SixQueryArena((16, 46, 89, 4, 1, 45))
REJECTED = SixQueryArena((1, 2, 4, 8, 16, 32))


def test_first_admitted_counter_is_retained_for_family():
    part = scan_records([(9, ADMITTED), (12, ADMITTED_ALIAS)])
    assert part.raw_counters == 2
    assert part.grammar_valid == 2
    assert part.admitted_presentations == 2
    assert len(part.first_families) == 1
    record = next(iter(part.first_families.values()))
    assert record.first_counter == 9
    assert record.queries == ADMITTED.queries


def test_shard_merge_is_order_independent_and_keeps_global_first_counter():
    left = scan_records([(12, ADMITTED_ALIAS)])
    right = scan_records([(9, ADMITTED)])
    merged_a = merge_parts([left, right])
    merged_b = merge_parts([right, left])
    assert merged_a == merged_b
    record = next(iter(merged_a.first_families.values()))
    assert record.first_counter == 9


def test_rejected_synthetic_arena_stops_before_admission():
    part = scan_records([(3, REJECTED)])
    assert part.raw_counters == 1
    assert part.grammar_valid == 1
    assert part.root_matched_tie == 0
    assert part.planner_gap == 0
    assert part.feature_representable == 0
    assert part.admitted_presentations == 0
    assert part.first_families == {}


def test_grammar_invalid_record_counts_raw_only():
    part = scan_records([(4, None)])
    assert part.raw_counters == 1
    assert part.grammar_valid == 0
    assert part.admitted_presentations == 0


def test_manual_shards_merge_exactly_like_single_pass():
    records = [(9, ADMITTED), (12, ADMITTED_ALIAS), (13, REJECTED), (14, None)]
    whole = scan_records(records)
    split = merge_parts([
        scan_records(records[:1]),
        scan_records(records[1:3]),
        scan_records(records[3:]),
    ])
    assert split == whole
