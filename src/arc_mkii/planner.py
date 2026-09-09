from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from .domain import FULL_MASK, Menu, candidate_child
from .resources import ResourceCounter


@dataclass(frozen=True)
class PlannerResult:
    success_count: int
    states_expanded: int


def planner_reference(
    menu: Menu,
    budget: int,
    resources: ResourceCounter | None = None,
) -> PlannerResult:
    if budget < 0:
        raise ValueError("budget must be nonnegative")
    states_expanded = 0

    @lru_cache(maxsize=None)
    def solve(candidate_mask: int, remaining_query_ids: tuple[int, ...], remaining_budget: int) -> int:
        nonlocal states_expanded
        states_expanded += 1
        if candidate_mask == 0:
            return 0
        if candidate_mask.bit_count() == 1 or remaining_budget <= 0 or not remaining_query_ids:
            return 1
        best = 1
        for query_id in remaining_query_ids:
            query_mask = menu.queries[query_id]
            if resources is not None:
                resources.public_truth_table_bit_inspections += 2 * candidate_mask.bit_count()
            child0 = candidate_child(candidate_mask, query_mask, 0)
            child1 = candidate_child(candidate_mask, query_mask, 1)
            if child0 == 0 or child1 == 0:
                continue
            next_queries = tuple(q for q in remaining_query_ids if q != query_id)
            value = solve(child0, next_queries, remaining_budget - 1) + solve(
                child1, next_queries, remaining_budget - 1
            )
            if value > best:
                best = value
        return best

    success_count = solve(FULL_MASK, tuple(range(4)), budget)
    if resources is not None:
        resources.planner_states_expanded += states_expanded
    return PlannerResult(success_count=success_count, states_expanded=states_expanded)


def planner_success_count(menu: Menu, budget: int) -> int:
    return planner_reference(menu, budget).success_count
