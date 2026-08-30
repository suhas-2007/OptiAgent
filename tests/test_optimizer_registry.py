import sys
import os

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

from backend.function_parser import SafeFunction
from backend.optimizer_registry import OptimizerRegistry


def test_registry_has_algorithms():

    registry = OptimizerRegistry()

    algorithms = registry.available_algorithms()

    assert isinstance(
        algorithms,
        list
    )

    assert len(algorithms) > 0


def test_nelder_mead_is_registered():

    registry = OptimizerRegistry()

    algorithms = registry.available_algorithms()

    assert "Nelder-Mead" in algorithms


def test_registry_can_create_nelder_mead():

    objective = SafeFunction(
        "x1**2 + x2**2"
    )

    registry = OptimizerRegistry()

    optimizer = registry.create(
        name="Nelder-Mead",
        objective_function=objective,
        dimensions=2,
        bounds=[
            (-10, 10),
            (-10, 10),
        ],
    )

    assert optimizer is not None


def test_created_optimizer_can_run():

    objective = SafeFunction(
        "x1**2 + x2**2"
    )

    registry = OptimizerRegistry()

    optimizer = registry.create(
        name="Nelder-Mead",
        objective_function=objective,
        dimensions=2,
        bounds=[
            (-10, 10),
            (-10, 10),
        ],
    )

    result = optimizer.optimize()

    assert isinstance(
        result,
        dict
    )

    assert "best_score" in result
    assert "best_position" in result