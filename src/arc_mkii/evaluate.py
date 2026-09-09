from __future__ import annotations

import time
import tracemalloc
from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable

from .canonical import canonical_id
from .domain import Menu
from .host import execute_query, initial_state, terminal_repair
from .resources import ResourceCounter, ResourceReport
from .selector import choose_from_scores, query_scores


@dataclass(frozen=True)
class DecisionTrace:
    candidate_mask: int
    remaining_budget: int
    scores: tuple[tuple[int, Fraction], ...]
    chosen_query: int | None


@dataclass(frozen=True)
class CaseTrace:
    canonical_task_id: str
    budget: int
    fault: int
    selected_query_ids: tuple[int, ...]
    observed_bits: tuple[int, ...]
    candidate_masks_after_queries: tuple[int, ...]
    decisions: tuple[DecisionTrace, ...]
    repair: int
    success: int
    query_count: int


@dataclass(frozen=True)
class EvaluationResult:
    name: str
    case_traces: tuple[CaseTrace, ...]
    success_by_budget: dict[int, int]
    resources: ResourceReport


def evaluate_theta(
    name: str,
    theta: tuple[Fraction, ...],
    menus: Iterable[Menu],
    *,
    artifact_bytes: int = 0,
) -> EvaluationResult:
    menus = tuple(menus)
    resources = ResourceCounter()
    tracemalloc.start()
    started = time.perf_counter_ns()
    traces: list[CaseTrace] = []
    success_by_budget = {2: 0, 3: 0}
    for menu in menus:
        task_id = canonical_id(menu)
        for budget in (2, 3):
            for fault in range(8):
                state = initial_state(menu, fault=fault, budget=budget)
                decisions: list[DecisionTrace] = []
                selected: list[int] = []
                masks: list[int] = []
                while True:
                    view = state.selector_view()
                    scores = query_scores(theta, view, resources=resources)
                    chosen = choose_from_scores(scores)
                    decisions.append(
                        DecisionTrace(
                            candidate_mask=view.candidate_mask,
                            remaining_budget=view.remaining_budget,
                            scores=scores,
                            chosen_query=chosen,
                        )
                    )
                    if chosen is None:
                        break
                    selected.append(chosen)
                    state = execute_query(state, chosen, resources=resources)
                    masks.append(state.candidate_mask)
                repair = terminal_repair(state, resources=resources)
                success = int(repair == fault)
                success_by_budget[budget] += success
                traces.append(
                    CaseTrace(
                        canonical_task_id=task_id,
                        budget=budget,
                        fault=fault,
                        selected_query_ids=tuple(selected),
                        observed_bits=tuple(bit for _, bit in state.observations),
                        candidate_masks_after_queries=tuple(masks),
                        decisions=tuple(decisions),
                        repair=repair,
                        success=success,
                        query_count=len(selected),
                    )
                )
    wall_time_ns = time.perf_counter_ns() - started
    _, peak_python_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return EvaluationResult(
        name=name,
        case_traces=tuple(traces),
        success_by_budget=success_by_budget,
        resources=resources.report(
            artifact_bytes=artifact_bytes,
            peak_python_bytes=peak_python_bytes,
            wall_time_ns=wall_time_ns,
        ),
    )


def transplant_equivalent(
    source_theta: tuple[Fraction, ...],
    transplanted_theta: tuple[Fraction, ...],
    menus: Iterable[Menu],
) -> bool:
    menus = tuple(menus)
    source = evaluate_theta("source", source_theta, menus)
    transplanted = evaluate_theta("transplanted", transplanted_theta, menus)
    return (
        source.case_traces == transplanted.case_traces
        and source.success_by_budget == transplanted.success_by_budget
    )


def ignition_pass(learn, scrambled, frozen, transplant_ok: bool) -> bool:
    if not transplant_ok:
        return False
    strict_budget = any(
        learn.success_by_budget[b] > scrambled.success_by_budget[b]
        and learn.success_by_budget[b] > frozen.success_by_budget[b]
        for b in (2, 3)
    )
    no_loss = all(
        learn.success_by_budget[b] >= scrambled.success_by_budget[b]
        and learn.success_by_budget[b] >= frozen.success_by_budget[b]
        for b in (2, 3)
    )
    return strict_budget and no_loss
