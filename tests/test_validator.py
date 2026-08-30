import sys
import os

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

from backend.function_parser import SafeFunction
from backend.solution_validator import SolutionValidator


def test_valid_solution():

    objective = SafeFunction(
        "x1**2 + x2**2"
    )

    validator = SolutionValidator(
        objective_function=objective,
        dimensions=2,
        bounds=[
            (-10, 10),
            (-10, 10),
        ],
    )

    result = {
        "best_position": [0, 0],
        "best_score": 0,
        "history": [10, 5, 1, 0],
    }

    validation = validator.validate_result(result)

    assert validation["valid"] is True


def test_solution_inside_bounds():

    objective = SafeFunction(
        "x1**2 + x2**2"
    )

    validator = SolutionValidator(
        objective_function=objective,
        dimensions=2,
        bounds=[
            (-10, 10),
            (-10, 10),
        ],
    )

    result = {
        "best_position": [3, 4],
        "best_score": 25,
        "history": [100, 50, 25],
    }

    validation = validator.validate_result(result)

    assert validation["valid"] is True