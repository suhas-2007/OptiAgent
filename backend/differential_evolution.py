"""Population search using SciPy's established Differential Evolution solver."""
import numpy as np
from scipy.optimize import differential_evolution
from scipy.stats import qmc


class DifferentialEvolution:
    def __init__(self, objective_function, dimensions, bounds, population_size=None,
                 seed=None, initial_position=None, generations=None):
        self.objective_function = objective_function
        self.dimensions = dimensions
        self.bounds = np.asarray(bounds, dtype=float)
        self.population_size = max(5, int(population_size or min(400, max(40, 10*dimensions))))
        self.max_iterations = generations if generations is not None else min(600, max(150, 10*dimensions))
        self.rng = np.random.default_rng(seed)
        self.initial_position = initial_position
        self.history = []

    def optimize(self, iterations=None):
        sample = qmc.LatinHypercube(d=self.dimensions, seed=int(self.rng.integers(2**31-1)))
        population = qmc.scale(sample.random(self.population_size), self.bounds[:, 0], self.bounds[:, 1])
        x0 = None
        if self.initial_position is not None:
            candidate = np.asarray(self.initial_position, dtype=float)
            if candidate.shape == (self.dimensions,) and np.all(np.isfinite(candidate)):
                x0 = np.clip(candidate, self.bounds[:, 0], self.bounds[:, 1])
        self.history = []
        def record(xk, convergence):
            self.history.append(float(self.objective_function(xk)))
            return False
        result = differential_evolution(self.objective_function, self.bounds,
            maxiter=self.max_iterations if iterations is None else iterations,
            init=population, x0=x0, seed=self.rng, callback=record,
            mutation=(0.5, 1.0), recombination=0.7, tol=1e-8,
            atol=1e-10, polish=True, workers=1)
        self.history.append(float(result.fun))
        return {'best_position':result.x.copy(), 'best_score':float(result.fun),
                'history':self.history.copy(), 'iterations':int(result.nit)}
