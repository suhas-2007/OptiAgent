try:
    # Package imports — used by pytest/API/package execution
    from backend.optimizer import ParticleSwarmOptimizer
    from backend.differential_evolution import DifferentialEvolution
    from backend.genetic_algorithm import GeneticAlgorithm
    from backend.simulated_annealing import SimulatedAnnealing
    from backend.hill_climbing import HillClimbing
    from backend.cma_es import CMAES
    from backend.nelder_mead import NelderMeadOptimizer

except ModuleNotFoundError:
    # Direct execution — used when running backend/main.py
    from optimizer import ParticleSwarmOptimizer
    from differential_evolution import DifferentialEvolution
    from genetic_algorithm import GeneticAlgorithm
    from simulated_annealing import SimulatedAnnealing
    from hill_climbing import HillClimbing
    from cma_es import CMAES
    from nelder_mead import NelderMeadOptimizer


class OptimizerRegistry:
    """
    Central registry for all optimization strategies.

    The agent can request an optimizer by name without knowing
    the implementation details of each algorithm.
    """

    def __init__(self):

        self.algorithms = {
            "PSO": self._create_pso,
            "Differential Evolution": self._create_de,
            "Genetic Algorithm": self._create_ga,
            "Simulated Annealing": self._create_sa,
            "Hill Climbing": self._create_hill_climbing,
            "CMA-ES": self._create_cma_es,
            "Nelder-Mead": self._create_nelder_mead,
        }

    def available_algorithms(self):
        """Return all registered algorithm names."""

        return list(self.algorithms.keys())

    def create(
        self,
        name,
        objective_function,
        dimensions,
        bounds,
    ):
        """Create an optimizer by name."""

        if name not in self.algorithms:

            raise ValueError(
                f"Unknown optimizer: {name}. "
                f"Available: {self.available_algorithms()}"
            )

        return self.algorithms[name](
            objective_function,
            dimensions,
            bounds,
        )

    # ==================================================
    # OPTIMIZER FACTORIES
    # ==================================================

    def _create_pso(
        self,
        objective_function,
        dimensions,
        bounds,
    ):

        return ParticleSwarmOptimizer(
            objective_function=objective_function,
            dimensions=dimensions,
            bounds=bounds,
            num_particles=50,
            max_iterations=200,
        )

    def _create_de(
        self,
        objective_function,
        dimensions,
        bounds,
    ):

        return DifferentialEvolution(
            objective_function=objective_function,
            dimensions=dimensions,
            bounds=bounds,
            population_size=50,
        )

    def _create_ga(
        self,
        objective_function,
        dimensions,
        bounds,
    ):

        return GeneticAlgorithm(
            objective_function=objective_function,
            dimensions=dimensions,
            bounds=bounds,
            population_size=50,
            generations=100,
        )

    def _create_sa(
        self,
        objective_function,
        dimensions,
        bounds,
    ):

        return SimulatedAnnealing(
            objective_function=objective_function,
            dimensions=dimensions,
            bounds=bounds,
            iterations=1000,
        )

    def _create_hill_climbing(
        self,
        objective_function,
        dimensions,
        bounds,
    ):

        return HillClimbing(
            objective_function=objective_function,
            dimensions=dimensions,
            bounds=bounds,
            iterations=500,
            restarts=10,
        )

    def _create_cma_es(
        self,
        objective_function,
        dimensions,
        bounds,
    ):

        return CMAES(
            objective_function=objective_function,
            dimensions=dimensions,
            bounds=bounds,
            generations=150,
        )

    def _create_nelder_mead(
        self,
        objective_function,
        dimensions,
        bounds,
    ):

        return NelderMeadOptimizer(
            objective_function=objective_function,
            dimensions=dimensions,
            bounds=bounds,
            max_iterations=1000,
        )