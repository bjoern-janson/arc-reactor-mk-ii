from __future__ import annotations

from fractions import Fraction
from typing import Sequence

from .corpus import TrainingRow
from .selector import THETA0
from .resources import ResourceCounter

LAMBDA = Fraction(1, 100)


def solve_linear_system(a: Sequence[Sequence[Fraction]], b: Sequence[Fraction]) -> list[Fraction]:
    n = len(b)
    if len(a) != n or any(len(row) != n for row in a):
        raise ValueError("coefficient matrix must be square and match rhs")
    matrix = [[Fraction(value) for value in row] + [Fraction(b[i])] for i, row in enumerate(a)]
    for col in range(n):
        pivot = next((row for row in range(col, n) if matrix[row][col] != 0), None)
        if pivot is None:
            raise ValueError("singular linear system")
        if pivot != col:
            matrix[col], matrix[pivot] = matrix[pivot], matrix[col]
        pivot_value = matrix[col][col]
        matrix[col] = [value / pivot_value for value in matrix[col]]
        for row in range(n):
            if row == col:
                continue
            factor = matrix[row][col]
            if factor == 0:
                continue
            matrix[row] = [
                current - factor * pivot_entry
                for current, pivot_entry in zip(matrix[row], matrix[col])
            ]
    return [matrix[i][-1] for i in range(n)]


def fit_theta(
    rows: Sequence[TrainingRow],
    resources: ResourceCounter | None = None,
) -> tuple[Fraction, ...]:
    p = 8
    a = [[Fraction(0) for _ in range(p)] for _ in range(p)]
    b = [Fraction(0) for _ in range(p)]
    for row in rows:
        if resources is not None:
            resources.training_rows_consumed += 1
        x = row.features
        if len(x) != p:
            raise ValueError("training row must have eight features")
        y = Fraction(row.feedback)
        for i in range(p):
            b[i] += x[i] * y
            for j in range(p):
                a[i][j] += x[i] * x[j]
    for i in range(p):
        a[i][i] += LAMBDA
        b[i] += LAMBDA * THETA0[i]
    return tuple(solve_linear_system(a, b))
