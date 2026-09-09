from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from .domain import FULL_MASK, QuerySet, candidate_child
from .resources import ResourceCounter


@dataclass(frozen=True)
class PlannerResult:
    success_count: int
    states_expanded: int


def planner_state_reference(
    menu: QuerySet,
    candidate_mask: int,
    remaining_query_ids: tuple[int, ...],
    budget: int,
    resources: ResourceCounter | None = None,
) -> PlannerResult:
    if budget < 0:
        raise ValueError("budget must be nonnegative")
    states_expanded = 0

    @lru_cache(maxsize=None)
    def solve(mask: int, remaining: tuple[int, ...], remaining_budget: int) -> int:
        nonlocal states_expanded
        states_expanded += 1
        if mask == 0:
            return 0
        if mask.bit_count() == 1 or remaining_budget <= 0 or not remaining:
            return 1
        best = 1
        for query_id in remaining:
            query_mask = menu.queries[query_id]
            if resources is not None:
                resources.public_truth_table_bit_inspections += 2 * mask.bit_count()
            child0 = candidate_child(mask, query_mask, 0)
            child1 = candidate_child(mask, query_mask, 1)
            if child0 == 0 or child1 == 0:
                continue
            next_queries = tuple(q for q in remaining if q != query_id)
            value = solve(child0, next_queries, remaining_budget - 1) + solve(
                child1, next_queries, remaining_budget - 1
            )
            best = max(best, value)
        return best

    success_count = solve(candidate_mask, tuple(remaining_query_ids), budget)
    if resources is not None:
        resources.planner_states_expanded += states_expanded
    return PlannerResult(success_count=success_count, states_expanded=states_expanded)


def planner_reference(
    menu: QuerySet,
    budget: int,
    resources: ResourceCounter | None = None,
) -> PlannerResult:
    return planner_state_reference(
        menu,
        FULL_MASK,
        tuple(range(len(menu.queries))),
        budget,
        resources=resources,
    )


def planner_success_count(menu: QuerySet, budget: int) -> int:
    return planner_reference(menu, budget).success_count
