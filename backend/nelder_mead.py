import numpy as np


class NelderMeadOptimizer:
    """
    Nelder-Mead simplex optimization.

    Minimizes the supplied objective function without using gradients.
    """

    def __init__(
        self,
        objective_function,
        dimensions,
        bounds,
        max_iterations=1000,
        tolerance=1e-8,
    ):
        self.objective_function = objective_function
        self.dimensions = dimensions
        self.bounds = np.asarray(bounds, dtype=float)
        self.max_iterations = max_iterations
        self.tolerance = tolerance

        # Nelder-Mead coefficients
        self.alpha = 1.0      # reflection
        self.gamma = 2.0      # expansion
        self.rho = 0.5        # contraction
        self.sigma = 0.5      # shrink

        self.global_best_position = None
        self.global_best_score = float("inf")
        self.history = []

    def _clip(self, x):
        """Keep a point inside the search bounds."""
        return np.clip(x, self.bounds[:, 0], self.bounds[:, 1])

    def _evaluate(self, x):
        return float(self.objective_function(x))

    def optimize(self):
        # Create initial simplex
        center = np.mean(self.bounds, axis=1)

        simplex = [center.copy()]

        for i in range(self.dimensions):
            point = center.copy()

            step = 0.05 * (self.bounds[i, 1] - self.bounds[i, 0])

            if step == 0:
                step = 0.1

            point[i] += step
            point = self._clip(point)

            simplex.append(point)

        simplex = np.array(simplex)

        scores = np.array([
            self._evaluate(point)
            for point in simplex
        ])

        for iteration in range(self.max_iterations):

            # Sort by objective score
            order = np.argsort(scores)

            simplex = simplex[order]
            scores = scores[order]

            best = simplex[0]
            best_score = scores[0]

            # Store best result
            if best_score < self.global_best_score:
                self.global_best_score = best_score
                self.global_best_position = best.copy()

            self.history.append(self.global_best_score)

            # Convergence check
            if np.std(scores) < self.tolerance:
                break

            # Centroid excluding worst point
            centroid = np.mean(simplex[:-1], axis=0)

            worst = simplex[-1]

            # Reflection
            reflected = centroid + self.alpha * (centroid - worst)
            reflected = self._clip(reflected)

            reflected_score = self._evaluate(reflected)

            if scores[0] <= reflected_score < scores[-2]:
                simplex[-1] = reflected
                scores[-1] = reflected_score

            elif reflected_score < scores[0]:

                # Expansion
                expanded = centroid + self.gamma * (reflected - centroid)
                expanded = self._clip(expanded)

                expanded_score = self._evaluate(expanded)

                if expanded_score < reflected_score:
                    simplex[-1] = expanded
                    scores[-1] = expanded_score
                else:
                    simplex[-1] = reflected
                    scores[-1] = reflected_score

            else:

                # Contraction
                contracted = centroid + self.rho * (worst - centroid)
                contracted = self._clip(contracted)

                contracted_score = self._evaluate(contracted)

                if contracted_score < scores[-1]:
                    simplex[-1] = contracted
                    scores[-1] = contracted_score

                else:
                    # Shrink
                    best_point = simplex[0].copy()

                    for i in range(1, len(simplex)):
                        simplex[i] = (
                            best_point
                            + self.sigma
                            * (simplex[i] - best_point)
                        )

                        simplex[i] = self._clip(simplex[i])
                        scores[i] = self._evaluate(simplex[i])

        # Final sorting
        order = np.argsort(scores)
        simplex = simplex[order]
        scores = scores[order]

        if scores[0] < self.global_best_score:
            self.global_best_score = scores[0]
            self.global_best_position = simplex[0].copy()

        return {
            "best_position": self.global_best_position,
            "best_score": self.global_best_score,
            "history": self.history,
            "iterations": len(self.history),
        }