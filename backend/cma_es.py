import numpy as np


class CMAES:
    """
    Simplified Covariance Matrix Adaptation Evolution Strategy.

    Continuous, derivative-free optimization.
    Compatible with OptiAgent's registry and benchmark system.
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
    ):

        # basic configuration

        self.objective_function = objective_function
        self.dimensions = dimensions
        self.bounds = np.asarray(
            bounds,
            dtype=float
        )

        # iteration compatibility

        if max_iterations is not None:
            self.max_iterations = max_iterations
        else:
            self.max_iterations = generations

        # Registry/benchmark may look for generations
        self.generations = self.max_iterations

        # population

        self.population_size = max(
            4,
            int(population_size)
        )

        # search step size

        self.sigma = float(sigma)

        # Used by AdaptationEngine detection
        self.initial_sigma = self.sigma

        # initial mean

        self.mean = (
            self.bounds[:, 0]
            + 0.5
            * (
                self.bounds[:, 1]
                - self.bounds[:, 0]
            )
        )

        # covariance

        self.covariance = np.eye(
            self.dimensions
        )

        # history

        self.history = []

    # clip to bounds

    def _clip(self, population):

        return np.clip(
            population,
            self.bounds[:, 0],
            self.bounds[:, 1],
        )

    # initialize

    def _initialize(self):

        self.mean = (
            self.bounds[:, 0]
            + 0.5
            * (
                self.bounds[:, 1]
                - self.bounds[:, 0]
            )
        )

        self.covariance = np.eye(
            self.dimensions
        )

        self.history = []

    # optimization

    def optimize(self):

        self._initialize()

        mean = self.mean.copy()

        covariance = self.covariance.copy()

        best_position = mean.copy()

        best_score = float(
            self.objective_function(
                best_position
            )
        )

        # main loop

        for iteration in range(
            self.max_iterations
        ):

            # generate candidate solutions

            try:

                population = (
                    np.random.multivariate_normal(
                        mean,
                        (
                            self.sigma ** 2
                        ) * covariance,
                        size=self.population_size,
                    )
                )

            except np.linalg.LinAlgError:

                # Numerical safety
                covariance = (
                    np.eye(
                        self.dimensions
                    )
                )

                population = (
                    np.random.multivariate_normal(
                        mean,
                        (
                            self.sigma ** 2
                        ) * covariance,
                        size=self.population_size,
                    )
                )

            # keep candidates inside bounds

            population = self._clip(
                population
            )

            # evaluate candidates

            scores = np.array(
                [
                    self.objective_function(
                        individual
                    )
                    for individual in population
                ],
                dtype=float,
            )

            # sort population

            order = np.argsort(
                scores
            )

            population = population[
                order
            ]

            scores = scores[
                order
            ]

            # current generation best

            generation_best_position = (
                population[0].copy()
            )

            generation_best_score = float(
                scores[0]
            )

            # global best

            if (
                generation_best_score
                < best_score
            ):

                best_score = (
                    generation_best_score
                )

                best_position = (
                    generation_best_position.copy()
                )

            # save convergence history

            self.history.append(
                float(best_score)
            )

            # select elite population

            elite_count = max(
                2,
                self.population_size // 2,
            )

            elite = population[
                :elite_count
            ]

            # update mean

            new_mean = np.mean(
                elite,
                axis=0,
            )

            # update covariance

            centered = (
                elite - new_mean
            )

            if elite_count > 1:

                new_covariance = (
                    np.cov(
                        centered,
                        rowvar=False,
                    )
                )

                # One-dimensional safety
                if (
                    self.dimensions == 1
                ):

                    new_covariance = np.array(
                        [[
                            float(
                                new_covariance
                            )
                        ]]
                    )

                # Numerical safety
                if (
                    new_covariance.shape
                    != covariance.shape
                ):

                    new_covariance = (
                        np.eye(
                            self.dimensions
                        )
                    )

                covariance = (
                    0.8 * covariance
                    + 0.2 * new_covariance
                )

            # numerical stabilization

            covariance += (
                np.eye(
                    self.dimensions
                ) * 1e-8
            )

            mean = new_mean

            # adaptive sigma

            if len(self.history) >= 10:

                recent = (
                    self.history[-10:]
                )

                improvement = (
                    recent[0]
                    - recent[-1]
                )

                if improvement > 1e-8:

                    self.sigma *= 0.98

                else:

                    self.sigma *= 1.05

                self.sigma = float(
                    np.clip(
                        self.sigma,
                        1e-5,
                        1.0,
                    )
                )

        # final result

        return {
            "best_position": best_position,
            "best_score": float(
                best_score
            ),
            "history": self.history,
        }