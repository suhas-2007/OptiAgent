import sys
import os

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

from backend.function_parser import SafeFunction
from backend.nelder_mead import NelderMeadOptimizer


def test_nelder_mead_returns_result():

    objective = SafeFunction(
        "x1**2 + x2**2"
    )

    optimizer = NelderMeadOptimizer(
        objective_function=objective,
        dimensions=2,
        bounds=[
            (-10, 10),
            (-10, 10),
        ],
    )

    result = optimizer.optimize()

    assert isinstance(result, dict)

    assert "best_position" in result
    assert "best_score" in result
    assert "history" in result
    assert "iterations" in result


def test_nelder_mead_finds_good_solution():

    objective = SafeFunction(
        "x1**2 + x2**2"
    )

    optimizer = NelderMeadOptimizer(
        objective_function=objective,
        dimensions=2,
        bounds=[
            (-10, 10),
            (-10, 10),
        ],
    )

    result = optimizer.optimize()

    assert result["best_score"] < 1.0


def test_solution_stays_inside_bounds():

    objective = SafeFunction(
        "x1**2 + x2**2"
    )

    bounds = [
        (-10, 10),
        (-10, 10),
    ]

    optimizer = NelderMeadOptimizer(
        objective_function=objective,
        dimensions=2,
        bounds=bounds,
    )

    result = optimizer.optimize()

    position = result["best_position"]

    for i in range(2):

        assert bounds[i][0] <= position[i] <= bounds[i][1]