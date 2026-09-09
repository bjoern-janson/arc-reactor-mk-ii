from arc_mkii.domain import FULL_MASK, Menu, SixQueryArena, candidate_child
from arc_mkii.host import initial_state
from arc_mkii.planner import planner_state_reference, planner_success_count

WITNESS = SixQueryArena((16, 46, 89, 4, 45, 1))


def test_v2_host_exposes_all_six_public_query_ids():
    state = initial_state(WITNESS, fault=0, budget=3)
    assert state.remaining_query_ids == (0, 1, 2, 3, 4, 5)


def test_state_planner_certifies_witness_bad_root_value_six():
    q_f = 1
    remaining = (0, 2, 3, 4, 5)
    values = [
        planner_state_reference(
            WITNESS,
            candidate_child(FULL_MASK, WITNESS.queries[q_f], bit),
            remaining,
            2,
        ).success_count
        for bit in (0, 1)
    ]
    assert values == [3, 3]
    assert sum(values) == 6


def test_v0_planner_reference_remains_eight_of_eight():
    assert planner_success_count(Menu((15, 23, 51, 85)), budget=3) == 8
