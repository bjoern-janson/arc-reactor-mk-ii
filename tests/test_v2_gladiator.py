from fractions import Fraction

from arc_mkii.domain import SixQueryArena
from arc_mkii.v2_gladiator import (
    CANONICAL_THRESHOLD,
    RAW_COUNTERS,
    SEED,
    analyze_arena,
    arena_from_counter,
)

WITNESS = SixQueryArena((16, 46, 89, 4, 45, 1))


def test_v2_raw_universe_constants_are_exactly_frozen():
    assert RAW_COUNTERS == 1_048_576
    assert CANONICAL_THRESHOLD == 320
    assert SEED == b"arc-reactor-mk-ii/v2-six-query/confirmatory/menu-seed/2026-09-09/fresh-001"


def test_counter_zero_derivation_checks_generator_only():
    arena = arena_from_counter(0)
    assert arena is not None
    assert arena.queries == (20, 8, 17, 13, 117, 61)


def test_hand_witness_has_same_six_to_eight_route_preservation_conflict():
    analysis = analyze_arena(WITNESS)
    assert analysis.root_matched_tie
    assert analysis.tied_queries == (1, 2, 4)
    assert analysis.frozen_query == 1
    assert dict(analysis.continuation_values) == {1: 6, 2: 8, 4: 8}
    assert analysis.optimal_tied_queries == (2, 4)
    assert dict(analysis.feature_pairs)[1] == (Fraction(1, 4), Fraction(1, 4))
    assert dict(analysis.feature_pairs)[2] == (Fraction(1, 2), Fraction(1, 2))
    assert analysis.planner_gap
    assert analysis.feature_representable
    assert analysis.admitted
