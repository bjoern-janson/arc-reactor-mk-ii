from __future__ import annotations

import hashlib
import itertools
import json
from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable

from .canonical import canonical_id
from .domain import Menu
from .features import feature_vector
from .host import execute_query, initial_state, terminal_repair
from .resources import ResourceCounter


def _fraction_record(value: Fraction) -> dict[str, int]:
    return {"n": value.numerator, "d": value.denominator}


@dataclass(frozen=True)
class TrainingRow:
    canonical_task_id: str
    query_masks: tuple[int, int, int, int]
    budget: int
    fault: int
    planned_sequence: tuple[int, ...]
    decision_depth: int
    candidate_mask: int
    remaining_query_ids: tuple[int, ...]
    action_query_id: int
    features: tuple[Fraction, ...]
    terminal_repair: int
    feedback: int

    @property
    def row_id(self) -> str:
        record = {
            "canonical_task_id": self.canonical_task_id,
            "query_masks": list(self.query_masks),
            "budget": self.budget,
            "fault": self.fault,
            "planned_sequence": list(self.planned_sequence),
            "decision_depth": self.decision_depth,
            "candidate_mask": self.candidate_mask,
            "remaining_query_ids": list(self.remaining_query_ids),
            "action_query_id": self.action_query_id,
            "features": [_fraction_record(v) for v in self.features],
            "terminal_repair": self.terminal_repair,
        }
        payload = json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(b"arc-mkii-training-row-v0\0" + payload).hexdigest()


def build_training_rows(
    menus: Iterable[Menu],
    resources: ResourceCounter | None = None,
) -> list[TrainingRow]:
    rows: list[TrainingRow] = []
    ordered_menus = sorted(menus, key=canonical_id)
    for menu in ordered_menus:
        task_id = canonical_id(menu)
        for budget in (2, 3):
            for fault in range(8):
                for sequence in itertools.permutations(range(4), budget):
                    state = initial_state(menu, fault=fault, budget=budget)
                    staged: list[dict[str, object]] = []
                    for decision_depth, query_id in enumerate(sequence):
                        if state.candidate_mask.bit_count() == 1:
                            break
                        view = state.selector_view()
                        staged.append(
                            {
                                "decision_depth": decision_depth,
                                "candidate_mask": state.candidate_mask,
                                "remaining_query_ids": state.remaining_query_ids,
                                "action_query_id": query_id,
                                "features": feature_vector(view, query_id, resources=resources),
                            }
                        )
                        state = execute_query(state, query_id, resources=resources)
                    repair = terminal_repair(state, resources=resources)
                    feedback = int(repair == fault)
                    for item in staged:
                        rows.append(
                            TrainingRow(
                                canonical_task_id=task_id,
                                query_masks=menu.queries,
                                budget=budget,
                                fault=fault,
                                planned_sequence=tuple(sequence),
                                decision_depth=int(item["decision_depth"]),
                                candidate_mask=int(item["candidate_mask"]),
                                remaining_query_ids=tuple(item["remaining_query_ids"]),
                                action_query_id=int(item["action_query_id"]),
                                features=tuple(item["features"]),
                                terminal_repair=repair,
                                feedback=feedback,
                            )
                        )
    return rows
