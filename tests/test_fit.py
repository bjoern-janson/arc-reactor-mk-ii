from fractions import Fraction
from types import SimpleNamespace

from arc_mkii.fit import fit_theta, solve_linear_system
from arc_mkii.selector import THETA0


def test_fraction_solver_returns_exact_solution():
    a = [
        [Fraction(2), Fraction(1)],
        [Fraction(1), Fraction(3)],
    ]
    b = [Fraction(1), Fraction(2)]
    assert solve_linear_system(a, b) == [Fraction(1, 5), Fraction(3, 5)]


def test_ridge_fit_is_exact_fraction_vector():
    row = SimpleNamespace(features=(Fraction(1),) + (Fraction(0),) * 7, feedback=1)
    theta = fit_theta([row])
    assert len(theta) == 8
    assert all(isinstance(value, Fraction) for value in theta)
    assert theta[0] == Fraction(100, 101)
    assert theta[3] == THETA0[3]
