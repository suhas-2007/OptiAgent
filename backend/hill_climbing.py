import numpy as np


class HillClimbing:
    """
    Continuous Hill Climbing optimizer.

    Minimizes the supplied objective function.
    """

    def __init__(
        self,
        objective_function,
        dimensions,
        bounds,
        iterations=500,
        step_size=0.1,
        restarts=5,
    ):
        self.objective_function = objective_function
        self.dimensions = dimensions
        self.bounds = np.asarray(bounds, dtype=float)

        self.iterations = iterations
        self.step_size = step_size
        self.restarts = restarts

        self.history = []

    def optimize(self):
        lower = self.bounds[:, 0]
        upper = self.bounds[:, 1]

        global_best_position = None
        global_best_score = float("inf")

        self.history = []

        for restart in range(self.restarts):

            # Start from a random position
            current_position = np.random.uniform(
                lower,
                upper,
                self.dimensions,
            )

            current_score = self.objective_function(
                current_position
            )

            for _ in range(self.iterations):

                # Generate a nearby candidate
                candidate = current_position + np.random.normal(
                    0,
                    self.step_size * (upper - lower),
                    self.dimensions,
                )

                # Keep candidate inside bounds
                candidate = np.clip(
                    candidate,
                    lower,
                    upper,
                )

                candidate_score = self.objective_function(candidate)

                # Move only if the candidate is better
                if candidate_score < current_score:

                    current_position = candidate
                    current_score = candidate_score

                # Update global best
                if current_score < global_best_score:

                    global_best_score = float(current_score)
                    global_best_position = current_position.copy()

                self.history.append(global_best_score)

        return {
            "best_position": global_best_position,
            "best_score": global_best_score,
            "history": self.history.copy(),
            "algorithm": "Hill Climbing",
        }