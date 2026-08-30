import numpy as np


class SimulatedAnnealing:
    """
    Continuous Simulated Annealing optimizer.

    Minimizes the supplied objective function.
    """

    def __init__(
        self,
        objective_function,
        dimensions,
        bounds,
        iterations=1000,
        initial_temperature=10.0,
        cooling_rate=0.995,
        step_size=0.1,
    ):
        self.objective_function = objective_function
        self.dimensions = dimensions
        self.bounds = np.asarray(bounds, dtype=float)

        self.iterations = iterations
        self.initial_temperature = initial_temperature
        self.cooling_rate = cooling_rate
        self.step_size = step_size

        self.history = []

    def optimize(self):

        lower = self.bounds[:, 0]
        upper = self.bounds[:, 1]

        # Initial solution
        current_position = np.random.uniform(
            lower,
            upper,
            self.dimensions,
        )

        current_score = self.objective_function(current_position)

        best_position = current_position.copy()
        best_score = float(current_score)

        temperature = self.initial_temperature

        self.history.append(best_score)

        for _ in range(self.iterations):

            # Generate neighboring solution
            candidate = current_position + np.random.normal(
                0,
                self.step_size * (upper - lower),
                self.dimensions,
            )

            candidate = np.clip(
                candidate,
                lower,
                upper,
            )

            candidate_score = self.objective_function(candidate)

            delta = candidate_score - current_score

            # Accept better solution
            if delta < 0:

                accept = True

            else:
                # Occasionally accept worse solutions
                # to escape local minima.
                probability = np.exp(
                    -delta / max(temperature, 1e-12)
                )

                accept = np.random.random() < probability

            if accept:

                current_position = candidate
                current_score = candidate_score

            # Update global best
            if current_score < best_score:

                best_score = float(current_score)
                best_position = current_position.copy()

            self.history.append(best_score)

            # Cool temperature
            temperature *= self.cooling_rate

        return {
            "best_position": best_position,
            "best_score": best_score,
            "history": self.history.copy(),
            "algorithm": "Simulated Annealing",
        }