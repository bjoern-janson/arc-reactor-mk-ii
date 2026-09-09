from arc_mkii.domain import Menu, SixQueryArena


def test_six_query_arena_preserves_public_slot_order():
    arena = SixQueryArena((16, 46, 89, 4, 45, 1))
    assert arena.queries == (16, 46, 89, 4, 45, 1)


def test_six_query_arena_requires_six_distinct_queries():
    try:
        SixQueryArena((1, 2, 3, 4, 5, 5))
    except ValueError as exc:
        assert "six distinct" in str(exc)
    else:
        raise AssertionError("duplicate V2 query was accepted")


def test_legacy_v0_menu_still_sorts_exactly_four_queries():
    assert Menu((85, 15, 51, 23)).queries == (15, 23, 51, 85)
