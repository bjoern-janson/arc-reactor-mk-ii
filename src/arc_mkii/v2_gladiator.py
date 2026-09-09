from __future__ import annotations

import hashlib
from dataclasses import dataclass
from fractions import Fraction

from .domain import FULL_MASK, SixQueryArena, candidate_child
from .features import feature_vector
from .host import SelectorView
from .planner import planner_state_reference
from .selector import THETA0, choose_query

RAW_COUNTERS = 1 << 20
CANONICAL_THRESHOLD = 320
SEED = b"arc-reactor-mk-ii/v2-six-query/confirmatory/menu-seed/2026-09-09/fresh-001"


@dataclass(frozen=True)
class ArenaAnalysis:
    root_matched_tie: bool
    tied_queries: tuple[int, ...]
    frozen_query: int | None
    continuation_values: tuple[tuple[int, int], ...]
    planner_gap: bool
    optimal_tied_queries: tuple[int, ...]
    feature_pairs: tuple[tuple[int, tuple[Fraction, Fraction]], ...]
    feature_representable: bool

    @property
    def admitted(self) -> bool:
        return self.root_matched_tie and self.planner_gap and self.feature_representable


def _partition_from(counter: int, slot: int) -> int:
    if not 0 <= counter < RAW_COUNTERS:
        raise ValueError("counter outside frozen V2 raw universe")
    if not 0 <= slot < 6:
        raise ValueError("slot must be in 0..5")
    payload = SEED + counter.to_bytes(8, "big") + slot.to_bytes(1, "big")
    digest = hashlib.sha256(payload).digest()
    return 1 + (int.from_bytes(digest[:8], "big") % 127)


def arena_from_counter(counter: int) -> SixQueryArena | None:
    queries = tuple(_partition_from(counter, slot) for slot in range(6))
    if len(set(queries)) != 6:
        return None
    return SixQueryArena(queries)


def _root_view(arena: SixQueryArena) -> SelectorView:
    return SelectorView(
        menu=arena,
        candidate_mask=FULL_MASK,
        remaining_query_ids=(0, 1, 2, 3, 4, 5),
        remaining_budget=3,
        observations=(),
    )


def _balance(arena: SixQueryArena, query_id: int) -> Fraction:
    query_mask = arena.queries[query_id]
    child0 = candidate_child(FULL_MASK, query_mask, 0)
    child1 = candidate_child(FULL_MASK, query_mask, 1)
    return Fraction(min(child0.bit_count(), child1.bit_count()), 8)


def _continuation_value(arena: SixQueryArena, query_id: int) -> int:
    remaining = tuple(q for q in range(6) if q != query_id)
    query_mask = arena.queries[query_id]
    return sum(
        planner_state_reference(
            arena,
            candidate_child(FULL_MASK, query_mask, bit),
            remaining,
            2,
        ).success_count
        for bit in (0, 1)
    )


def analyze_arena(arena: SixQueryArena) -> ArenaAnalysis:
    view = _root_view(arena)
    balances = tuple((q, _balance(arena, q)) for q in range(6))
    best_balance = max(value for _, value in balances)
    tied = tuple(q for q, value in balances if value == best_balance)
    root_matched_tie = best_balance == Fraction(1, 2) and len(tied) >= 2

    if not root_matched_tie:
        return ArenaAnalysis(
            root_matched_tie=False,
            tied_queries=tied,
            frozen_query=None,
            continuation_values=(),
            planner_gap=False,
            optimal_tied_queries=(),
            feature_pairs=(),
            feature_representable=False,
        )

    frozen_query = choose_query(THETA0, view)
    if frozen_query not in tied:
        raise RuntimeError("THETA0 root choice escaped the maximum-balance tie")

    continuation_values = tuple((q, _continuation_value(arena, q)) for q in tied)
    continuation = dict(continuation_values)
    best_continuation = max(continuation.values())
    planner_gap = best_continuation - continuation[frozen_query] >= 2
    optimal_tied_queries = tuple(q for q in tied if continuation[q] == best_continuation)

    feature_pairs = tuple(
        (q, (features[6], features[7]))
        for q in tied
        for features in (feature_vector(view, q),)
    )

    feature_representable = False
    if planner_gap:
        pairs = dict(feature_pairs)
        frozen_weighted, frozen_worst = pairs[frozen_query]
        for query_id in optimal_tied_queries:
            weighted, worst = pairs[query_id]
            if worst > frozen_worst or (worst == frozen_worst and weighted > frozen_weighted):
                feature_representable = True
                break

    return ArenaAnalysis(
        root_matched_tie=True,
        tied_queries=tied,
        frozen_query=frozen_query,
        continuation_values=continuation_values,
        planner_gap=planner_gap,
        optimal_tied_queries=optimal_tied_queries,
        feature_pairs=feature_pairs,
        feature_representable=feature_representable,
    )
