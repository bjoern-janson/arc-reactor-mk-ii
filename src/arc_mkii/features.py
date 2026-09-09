from __future__ import annotations

from fractions import Fraction

from .domain import candidate_child
from .host import SelectorView
from .resources import ResourceCounter

FEATURE_NAMES = (
    "intercept",
    "remaining_budget_over_3",
    "candidate_count_over_8",
    "smaller_child_fraction",
    "child_fraction_product",
    "singleton_child_candidate_fraction",
    "weighted_best_next_split",
    "worst_child_best_next_split",
)


def _count(mask: int) -> int:
    return mask.bit_count()


def _child(candidate_mask: int, query_mask: int, bit: int, resources: ResourceCounter | None) -> int:
    if resources is not None:
        resources.public_truth_table_bit_inspections += candidate_mask.bit_count()
    return candidate_child(candidate_mask, query_mask, bit)


def _split_score(
    view: SelectorView,
    child_mask: int,
    excluded_query_id: int,
    resources: ResourceCounter | None,
) -> Fraction:
    size = _count(child_mask)
    if size == 1:
        return Fraction(1, 2)
    best = Fraction(0)
    for query_id in view.remaining_query_ids:
        if query_id == excluded_query_id:
            continue
        query_mask = view.menu.queries[query_id]
        child0 = _child(child_mask, query_mask, 0, resources)
        child1 = _child(child_mask, query_mask, 1, resources)
        n0 = _count(child0)
        n1 = _count(child1)
        score = Fraction(min(n0, n1), size)
        if score > best:
            best = score
    return best


def feature_vector(
    view: SelectorView,
    query_id: int,
    resources: ResourceCounter | None = None,
) -> tuple[Fraction, ...]:
    if query_id not in view.remaining_query_ids:
        raise ValueError("query is not available")
    n = _count(view.candidate_mask)
    if n <= 0:
        raise ValueError("candidate set must be nonempty")
    if resources is not None:
        resources.feature_vectors_computed += 1

    query_mask = view.menu.queries[query_id]
    children = tuple(
        child
        for bit in (0, 1)
        if (child := _child(view.candidate_mask, query_mask, bit, resources)) != 0
    )
    sizes = tuple(_count(child) for child in children)
    if len(sizes) == 1:
        n0, n1 = sizes[0], 0
    else:
        n0, n1 = sizes

    smaller = Fraction(min(n0, n1), n)
    product = Fraction(n0, n) * Fraction(n1, n)
    singleton_fraction = Fraction(sum(size for size in sizes if size == 1), n)

    weighted_next = Fraction(0)
    worst_next = Fraction(0)
    if view.remaining_budget > 1:
        branch_scores = tuple(_split_score(view, child, query_id, resources) for child in children)
        weighted_next = sum(
            (Fraction(size, n) * score for size, score in zip(sizes, branch_scores)),
            Fraction(0),
        )
        worst_next = min(branch_scores) if branch_scores else Fraction(0)

    return (
        Fraction(1),
        Fraction(view.remaining_budget, 3),
        Fraction(n, 8),
        smaller,
        product,
        singleton_fraction,
        weighted_next,
        worst_next,
    )
