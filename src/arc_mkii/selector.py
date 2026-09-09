from __future__ import annotations

from fractions import Fraction
from typing import TypeAlias

from .domain import candidate_child
from .features import FEATURE_NAMES, feature_vector
from .host import SelectorView

Theta: TypeAlias = tuple[Fraction, ...]
THETA0: Theta = tuple(Fraction(1 if i == 3 else 0) for i in range(len(FEATURE_NAMES)))


def _useful(view: SelectorView, query_id: int) -> bool:
    query_mask = view.menu.queries[query_id]
    child0 = candidate_child(view.candidate_mask, query_mask, 0)
    child1 = candidate_child(view.candidate_mask, query_mask, 1)
    return child0 != 0 and child1 != 0


def score_query(theta: tuple[Fraction, ...], view: SelectorView, query_id: int) -> Fraction:
    if len(theta) != len(FEATURE_NAMES):
        raise ValueError("theta must contain eight coefficients")
    features = feature_vector(view, query_id)
    return sum((weight * value for weight, value in zip(theta, features)), Fraction(0))


def choose_query(theta: tuple[Fraction, ...], view: SelectorView) -> int | None:
    if view.candidate_mask.bit_count() <= 1:
        return None
    if view.remaining_budget <= 0 or not view.remaining_query_ids:
        return None
    useful = [query_id for query_id in view.remaining_query_ids if _useful(view, query_id)]
    if not useful:
        return None
    scored = [(score_query(theta, view, query_id), query_id) for query_id in useful]
    best_score = max(score for score, _ in scored)
    return min(query_id for score, query_id in scored if score == best_score)
