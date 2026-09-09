from __future__ import annotations

from fractions import Fraction
from typing import TypeAlias

from .domain import candidate_child
from .features import FEATURE_NAMES, feature_vector
from .host import SelectorView
from .resources import ResourceCounter

Theta: TypeAlias = tuple[Fraction, ...]
THETA0: Theta = tuple(Fraction(1 if i == 3 else 0) for i in range(len(FEATURE_NAMES)))


def _useful(view: SelectorView, query_id: int) -> bool:
    query_mask = view.menu.queries[query_id]
    child0 = candidate_child(view.candidate_mask, query_mask, 0)
    child1 = candidate_child(view.candidate_mask, query_mask, 1)
    return child0 != 0 and child1 != 0


def score_query(
    theta: tuple[Fraction, ...],
    view: SelectorView,
    query_id: int,
    resources: ResourceCounter | None = None,
) -> Fraction:
    if len(theta) != len(FEATURE_NAMES):
        raise ValueError("theta must contain eight coefficients")
    features = feature_vector(view, query_id, resources=resources)
    return sum((weight * value for weight, value in zip(theta, features)), Fraction(0))


def query_scores(
    theta: tuple[Fraction, ...],
    view: SelectorView,
    resources: ResourceCounter | None = None,
) -> tuple[tuple[int, Fraction], ...]:
    if view.candidate_mask.bit_count() <= 1:
        return ()
    if view.remaining_budget <= 0 or not view.remaining_query_ids:
        return ()
    useful = [query_id for query_id in view.remaining_query_ids if _useful(view, query_id)]
    return tuple((query_id, score_query(theta, view, query_id, resources)) for query_id in useful)


def choose_from_scores(scores: tuple[tuple[int, Fraction], ...]) -> int | None:
    if not scores:
        return None
    best_score = max(score for _, score in scores)
    return min(query_id for query_id, score in scores if score == best_score)


def choose_query(
    theta: tuple[Fraction, ...],
    view: SelectorView,
    resources: ResourceCounter | None = None,
) -> int | None:
    return choose_from_scores(query_scores(theta, view, resources=resources))
