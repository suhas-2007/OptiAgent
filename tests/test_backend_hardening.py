import sys
import os
import math
import pytest

# Ensure root directory is on sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.api import app
from backend.function_parser import SafeFunction
from backend.agent import OptimizationAgent
from backend.nelder_mead import NelderMeadOptimizer
from backend.cma_es import CMAES
from backend.genetic_algorithm import GeneticAlgorithm
from backend.simulated_annealing import SimulatedAnnealing
from backend.hill_climbing import HillClimbing
from backend.optimizer import ParticleSwarmOptimizer
from backend.differential_evolution import DifferentialEvolution
from backend.ai_planner import AIPlanner
from backend.monitor import ConvergenceMonitor


# ----------------------------------------------------------------------
# 1. Root & Package Import Robustness
# ----------------------------------------------------------------------

def test_package_imports_from_root():
    """Verify backend modules can be imported directly from repository root."""
    import backend
    import backend.api
    import backend.agent
    import backend.function_parser
    import backend.monitor
    import backend.ai_planner
    assert hasattr(backend.api, "app")
    assert hasattr(backend.agent, "OptimizationAgent")


# ----------------------------------------------------------------------
# 2. SafeFunction Hardening & Domain Safety
# ----------------------------------------------------------------------

def test_safe_function_syntax_error_handling():
    """Invalid syntax should raise ValueError with helpful message, not crash raw AST."""
    with pytest.raises(ValueError) as excinfo:
        SafeFunction("x1 +++ * 2")
    assert "syntax" in str(excinfo.value).lower()


def test_safe_function_division_by_zero():
    """Division by zero should safely return float('inf') rather than raising ZeroDivisionError."""
    f = SafeFunction("1.0 / x1")
    val = f([0.0])
    assert math.isinf(val) or val > 1e12


def test_safe_function_domain_error():
    """Negative square roots or invalid logs should return float('inf') instead of crashing."""
    f_sqrt = SafeFunction("sqrt(x1)")
    val_sqrt = f_sqrt([-4.0])
    assert math.isinf(val_sqrt) or val_sqrt > 1e12

    f_log = SafeFunction("log(x1)")
    val_log = f_log([0.0])
    assert math.isinf(val_log) or val_log > 1e12


def test_safe_function_accepts_scalar_and_arrays():
    """SafeFunction handles both 1D list, numpy array, and scalar inputs."""
    f = SafeFunction("x1**2 + 5")
    assert f(3.0) == 14.0
    assert f([3.0]) == 14.0


# ----------------------------------------------------------------------
# 3. API Input Validation & Error Handling (/optimize)
# ----------------------------------------------------------------------

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_optimize_empty_body(client):
    res = client.post("/optimize", json=None)
    assert res.status_code == 400
    assert res.get_json()["success"] is False


def test_optimize_missing_objective(client):
    res = client.post("/optimize", json={"dimensions": 2, "bounds": [[-5, 5], [-5, 5]]})
    assert res.status_code == 400
    assert "objective" in res.get_json()["error"].lower()


def test_optimize_invalid_objective_syntax(client):
    res = client.post("/optimize", json={
        "objective": "x1 +++ * 2",
        "dimensions": 2,
        "bounds": [[-5, 5], [-5, 5]]
    })
    assert res.status_code == 400
    assert res.get_json()["success"] is False


def test_optimize_dimensions_out_of_range(client):
    # dimensions <= 0
    res0 = client.post("/optimize", json={
        "objective": "x1**2",
        "dimensions": 0,
        "bounds": []
    })
    assert res0.status_code == 400

    # dimensions > 50
    res_large = client.post("/optimize", json={
        "objective": "x1**2",
        "dimensions": 100,
        "bounds": [[-1, 1]] * 100
    })
    assert res_large.status_code == 400


def test_optimize_bounds_mismatch(client):
    res = client.post("/optimize", json={
        "objective": "x1**2 + x2**2",
        "dimensions": 2,
        "bounds": [[-5, 5]]  # only 1 bound for 2 dimensions
    })
    assert res.status_code == 400
    assert "match dimensions" in res.get_json()["error"].lower()


def test_optimize_inverted_bounds(client):
    res = client.post("/optimize", json={
        "objective": "x1**2 + x2**2",
        "dimensions": 2,
        "bounds": [[5, -5], [-5, 5]]  # lower > upper
    })
    assert res.status_code == 400
    assert "less than upper" in res.get_json()["error"].lower()


def test_optimize_infinite_bounds(client):
    res = client.post("/optimize", json={
        "objective": "x1**2 + x2**2",
        "dimensions": 2,
        "bounds": [[float("-inf"), 5], [-5, 5]]
    })
    assert res.status_code == 400
    assert "finite" in res.get_json()["error"].lower()


def test_optimize_invalid_stages_or_patience(client):
    res_stages = client.post("/optimize", json={
        "objective": "x1**2 + x2**2",
        "dimensions": 2,
        "bounds": [[-5, 5], [-5, 5]],
        "max_stages": 0
    })
    assert res_stages.status_code == 400

    res_patience = client.post("/optimize", json={
        "objective": "x1**2 + x2**2",
        "dimensions": 2,
        "bounds": [[-5, 5], [-5, 5]],
        "patience": 100
    })
    assert res_patience.status_code == 400


def test_optimize_success_contract(client):
    """Verify successful end-to-end optimization response contains expected schema."""
    res = client.post("/optimize", json={
        "objective": "x1**2 + x2**2",
        "dimensions": 2,
        "bounds": [[-5.0, 5.0], [-5.0, 5.0]],
        "max_stages": 2,
        "patience": 2
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert isinstance(data["best_position"], list)
    assert len(data["best_position"]) == 2
    assert isinstance(data["best_score"], (int, float))
    assert data["best_score"] < 1.0  # sphere function converges close to 0
    assert isinstance(data["strategy_history"], list)
    assert isinstance(data["stage_history"], list)
    assert isinstance(data["convergence_history"], list)
    assert len(data["convergence_history"]) > 0


# ----------------------------------------------------------------------
# 4. API /api/extract-problem and /api/ask-info edge cases
# ----------------------------------------------------------------------

def test_extract_problem_empty(client):
    res = client.post("/api/extract-problem", json={})
    assert res.status_code == 400
    assert res.get_json()["success"] is False


def test_ask_info_empty(client):
    res = client.post("/api/ask-info", json={})
    assert res.status_code == 400
    assert "missing" in res.get_json()["error"].lower()


def test_ask_info_fallback_responses(client):
    for topic in ["pso", "cma", "genetic", "annealing", "hill", "rosenbrock", "ackley"]:
        res = client.post("/api/ask-info", json={"question": f"tell me about {topic}"})
        assert res.status_code == 200
        assert res.get_json()["success"] is True
        assert len(res.get_json()["answer"]) > 10


# ----------------------------------------------------------------------
# 5. Optimizer Seeding Across All Supported Algorithms
# ----------------------------------------------------------------------

def test_optimizer_initial_position_seeding():
    """All 7 optimizers must accept initial_position and run properly."""
    f = SafeFunction("x1**2 + x2**2")
    bounds = [(-5.0, 5.0), (-5.0, 5.0)]
    seed = [1.5, 1.5]

    optimizers = [
        NelderMeadOptimizer(f, 2, bounds, initial_position=seed, max_iterations=20),
        CMAES(f, 2, bounds, initial_position=seed, max_iterations=20),
        GeneticAlgorithm(f, 2, bounds, initial_position=seed, generations=5, population_size=10),
        SimulatedAnnealing(f, 2, bounds, initial_position=seed, max_iterations=20),
        HillClimbing(f, 2, bounds, initial_position=seed, max_iterations=20),
        ParticleSwarmOptimizer(f, 2, bounds, initial_position=seed, max_iterations=10, num_particles=10),
        DifferentialEvolution(f, 2, bounds, initial_position=seed, population_size=10),
    ]

    for opt in optimizers:
        res = opt.optimize()
        assert isinstance(res, dict)
        assert "best_position" in res
        assert "best_score" in res
        assert len(res["best_position"]) == 2


# ----------------------------------------------------------------------
# 6. AI Planner Resiliency
# ----------------------------------------------------------------------

def test_ai_planner_avoid_all_fallback():
    """If avoid_strategy filters all algorithms, AIPlanner falls back to full pool gracefully."""
    planner = AIPlanner(algorithms=["Nelder-Mead"])
    rec = planner._local_fallback(
        problem_description="x1**2 + x2**2",
        dimensions=2,
        bounds=[(-5, 5), (-5, 5)],
        current_strategy="Nelder-Mead",
        optimization_status="stagnating",
        avoid_strategy="Nelder-Mead"
    )
    assert rec["success"] is True
    assert rec["recommended_strategy"] == "Nelder-Mead"
    assert isinstance(rec["reason"], str)


# ----------------------------------------------------------------------
# 7. Monitor Edge Cases
# ----------------------------------------------------------------------

def test_monitor_empty_or_non_finite_history():
    monitor = ConvergenceMonitor(patience=3, min_improvement=1e-4)
    # Empty
    res_empty = monitor.analyze_history([])
    assert res_empty["stagnating"] is False
    assert res_empty["best_score"] is None

    # Incomplete history (less than patience)
    res_short = monitor.analyze_history([1.0, 0.9])
    assert res_short["stagnating"] is False

    # Stagnant with flat history
    res_flat = monitor.analyze_history([1.0, 1.0, 1.0, 1.0])
    assert res_flat["stagnating"] is True
    assert res_flat["trend"] == "flat"

    # Non-finite and string values filtered safely
    res_non_finite = monitor.analyze_history([1.0, float("inf"), float("nan"), "invalid", 1.0, 1.0, 1.0])
    assert res_non_finite["best_score"] == 1.0
    assert res_non_finite["stagnating"] is True
