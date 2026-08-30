import numpy as np


class RandomSearch:
    """
    Random Search optimizer.

    Continuously samples random points inside the search space
    and keeps the best solution found.
    """

    def __init__(
        self,
        objective_function,
        dimensions,
        bounds,
        iterations=1000,
    ):
        self.objective_function = objective_function
        self.dimensions = dimensions
        self.bounds = np.asarray(bounds, dtype=float)
        self.iterations = iterations

        self.history = []

    def optimize(self):

        lower = self.bounds[:, 0]
        upper = self.bounds[:, 1]

        best_position = None
        best_score = float("inf")

        self.history = []

        for _ in range(self.iterations):

            # Generate a completely random candidate
            candidate = np.random.uniform(
                lower,
                upper,
                self.dimensions,
            )

            score = self.objective_function(candidate)

            # Keep the best candidate
            if score < best_score:

                best_score = float(score)
                best_position = candidate.copy()

            self.history.append(best_score)

        return {
            "best_position": best_position,
            "best_score": best_score,
            "history": self.history.copy(),
            "algorithm": "Random Search",
        }