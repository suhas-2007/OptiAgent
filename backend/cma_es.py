import numpy as np


class CMAES:
    """
    Simplified Covariance Matrix Adaptation Evolution Strategy.

    Continuous, derivative-free optimization.
    Compatible with OptiAgent's registry and multi-stage seeding system.
    """

    def __init__(
        self,
        objective_function,
        dimensions,
        bounds,
        population_size=20,
        generations=100,
        max_iterations=None,
        sigma=0.5,
        initial_position=None,
        seed=None,
    ):
        self.objective_function = objective_function
        self.dimensions = dimensions
        self.bounds = np.asarray(bounds, dtype=float)

        if max_iterations is not None:
            self.max_iterations = max_iterations
        else:
            self.max_iterations = generations

        self.generations = self.max_iterations
        self.population_size = max(4, int(population_size))
        self.sigma = float(sigma)
        self.initial_sigma = self.sigma

        self.initial_position = initial_position
        self.rng = np.random.default_rng(seed)

        self.mean = (
            self.bounds[:, 0]
            + 0.5 * (self.bounds[:, 1] - self.bounds[:, 0])
        )
        self.covariance = np.eye(self.dimensions)
        self.history = []

    def _clip(self, population):
        return np.clip(
            population,
            self.bounds[:, 0],
            self.bounds[:, 1],
        )

    def _initialize(self):
        self.sigma = self.initial_sigma
        if self.initial_position is not None:
            try:
                self.mean = self._clip(
                    np.asarray(self.initial_position, dtype=float)
                )
            except Exception:
                self.mean = (
                    self.bounds[:, 0]
                    + 0.5 * (self.bounds[:, 1] - self.bounds[:, 0])
                )
        else:
            self.mean = (
                self.bounds[:, 0]
                + 0.5 * (self.bounds[:, 1] - self.bounds[:, 0])
            )

        self.covariance = np.eye(self.dimensions)
        self.history = []

    def optimize(self):
        self._initialize()
        if self.dimensions > 20:
            return self._optimize_diagonal()

        mean = self.mean.copy()
        covariance = self.covariance.copy()
        best_position = mean.copy()
        best_score = float(self.objective_function(best_position))

        for iteration in range(self.max_iterations):
            # Generate candidate population with covariance
            try:
                population = self.rng.multivariate_normal(
                    mean,
                    (self.sigma ** 2) * covariance,
                    size=self.population_size,
                )
            except (np.linalg.LinAlgError, ValueError):
                # Numerical safety fallback to identity covariance
                covariance = np.eye(self.dimensions)
                population = self.rng.multivariate_normal(
                    mean,
                    (self.sigma ** 2) * covariance,
                    size=self.population_size,
                )

            # Keep candidates inside bounds
            population = self._clip(population)

            # Evaluate candidates
            scores = np.array(
                [
                    self.objective_function(individual)
                    for individual in population
                ],
                dtype=float,
            )

            # Sort population
            order = np.argsort(scores)
            population = population[order]
            scores = scores[order]

            generation_best_position = population[0].copy()
            generation_best_score = float(scores[0])

            if generation_best_score < best_score:
                best_score = generation_best_score
                best_position = generation_best_position.copy()

            self.history.append(float(best_score))

            # Select elite sub-population
            elite_count = max(2, self.population_size // 2)
            elite = population[:elite_count]

            # Update distribution mean
            new_mean = np.mean(elite, axis=0)
            centered = elite - new_mean

            if elite_count > 1:
                new_covariance = np.cov(centered, rowvar=False)

                if self.dimensions == 1:
                    new_covariance = np.array([[float(new_covariance)]])

                if new_covariance.shape != covariance.shape:
                    new_covariance = np.eye(self.dimensions)

                covariance = 0.8 * covariance + 0.2 * new_covariance

            # Numerical diagonal regularization
            covariance += np.eye(self.dimensions) * 1e-8
            mean = new_mean

            # Step-size adaptation
            if len(self.history) >= 10:
                recent = self.history[-10:]
                improvement = recent[0] - recent[-1]
                if improvement > 1e-8:
                    self.sigma *= 0.98
                else:
                    self.sigma *= 1.05

                self.sigma = float(np.clip(self.sigma, 1e-5, 1.0))

        return {
            "best_position": best_position,
            "best_score": float(best_score),
            "history": self.history,
        }

    def _optimize_diagonal(self):
        """Linear-memory diagonal evolution for large dimensions (not full CMA-ES)."""
        mean = self.mean.copy()
        variance = ((self.bounds[:, 1]-self.bounds[:, 0])*0.2)**2
        best_position = mean.copy()
        best_score = float(self.objective_function(mean))
        for _ in range(self.max_iterations):
            population = self._clip(mean + self.rng.normal(size=(self.population_size, self.dimensions))*np.sqrt(variance))
            scores = np.array([self.objective_function(point) for point in population])
            order = np.argsort(scores)
            if scores[order[0]] < best_score:
                best_position, best_score = population[order[0]].copy(), float(scores[order[0]])
            elite = population[order[:max(2, self.population_size//2)]]
            mean = elite.mean(axis=0)
            variance = np.maximum(0.8*variance+0.2*elite.var(axis=0), 1e-12)
            self.history.append(best_score)
        return {'best_position':best_position, 'best_score':best_score, 'history':self.history}
