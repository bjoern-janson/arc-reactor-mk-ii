from __future__ import annotations

from dataclasses import dataclass

from .domain import FAULTS, FULL_MASK, Menu, answer, candidate_child
from .resources import ResourceCounter


@dataclass(frozen=True)
class SelectorView:
    menu: Menu
    candidate_mask: int
    remaining_query_ids: tuple[int, ...]
    remaining_budget: int
    observations: tuple[tuple[int, int], ...]

    @property
    def candidates(self) -> tuple[int, ...]:
        return tuple(f for f in FAULTS if (self.candidate_mask >> f) & 1)


@dataclass(frozen=True)
class HostState:
    menu: Menu
    fault: int
    candidate_mask: int
    remaining_query_ids: tuple[int, ...]
    remaining_budget: int
    observations: tuple[tuple[int, int], ...] = ()

    @property
    def candidates(self) -> tuple[int, ...]:
        return tuple(f for f in FAULTS if (self.candidate_mask >> f) & 1)

    def selector_view(self) -> SelectorView:
        return SelectorView(
            menu=self.menu,
            candidate_mask=self.candidate_mask,
            remaining_query_ids=self.remaining_query_ids,
            remaining_budget=self.remaining_budget,
            observations=self.observations,
        )


def initial_state(menu: Menu, fault: int, budget: int) -> HostState:
    if fault not in FAULTS:
        raise ValueError("fault must be in 0..7")
    if budget < 0:
        raise ValueError("budget must be nonnegative")
    return HostState(
        menu=menu,
        fault=fault,
        candidate_mask=FULL_MASK,
        remaining_query_ids=tuple(range(4)),
        remaining_budget=budget,
        observations=(),
    )


def execute_query(
    state: HostState,
    query_id: int,
    resources: ResourceCounter | None = None,
) -> HostState:
    if query_id not in state.remaining_query_ids:
        raise ValueError("query is not available")
    if state.remaining_budget <= 0:
        raise ValueError("query budget exhausted")
    qmask = state.menu.queries[query_id]
    observed = answer(qmask, state.fault)
    if resources is not None:
        resources.primitive_query_executions += 1
        resources.public_truth_table_bit_inspections += state.candidate_mask.bit_count()
    kept = candidate_child(state.candidate_mask, qmask, observed)
    if kept == 0:
        raise RuntimeError("truth-consistent query removed every candidate")
    return HostState(
        menu=state.menu,
        fault=state.fault,
        candidate_mask=kept,
        remaining_query_ids=tuple(q for q in state.remaining_query_ids if q != query_id),
        remaining_budget=state.remaining_budget - 1,
        observations=state.observations + ((query_id, observed),),
    )


def terminal_repair(
    state: HostState | SelectorView,
    resources: ResourceCounter | None = None,
) -> int:
    if resources is not None:
        resources.terminal_actions += 1
    mask = state.candidate_mask
    if mask == 0:
        raise ValueError("cannot repair from an empty candidate set")
    for fault in FAULTS:
        if (mask >> fault) & 1:
            return fault
    raise RuntimeError("nonempty candidate mask contained no declared fault")
