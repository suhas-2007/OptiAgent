import numpy as np


class DifferentialEvolution:
    """
    Differential Evolution optimizer.

    Uses population-based mutation and crossover to search
    for the minimum of an objective function.

    Supports optional global-best seeding from OptiAgent.
    """

    def __init__(
        self,
        objective_function,
        dimensions,
        bounds,
        population_size=30,
        seed=123,
    ):
        self.objective_function = objective_function
        self.dimensions = dimensions
        self.bounds = np.asarray(
            bounds,
            dtype=float,
        )

        self.population_size = population_size

        self.lower_bounds = self.bounds[:, 0]
        self.upper_bounds = self.bounds[:, 1]

        self.rng = np.random.default_rng(seed)

        # ==================================================
        # OPTIONAL GLOBAL-BEST SEED
        # ==================================================

        self.initial_position = None

        # ==================================================
        # INITIAL POPULATION
        # ==================================================

        self.population = self.rng.uniform(
            self.lower_bounds,
            self.upper_bounds,
            size=(
                population_size,
                dimensions,
            ),
        )

        # ==================================================
        # INITIAL SCORES
        # ==================================================

        self.scores = np.array([
            self.objective_function(x)
            for x in self.population
        ])

        # ==================================================
        # INITIAL GLOBAL BEST
        # ==================================================

        best_index = np.argmin(
            self.scores
        )

        self.global_best_position = (
            self.population[
                best_index
            ].copy()
        )

        self.global_best_score = float(
            self.scores[
                best_index
            ]
        )

        # ==================================================
        # HISTORY
        # ==================================================

        self.history = [
            self.global_best_score
        ]

    # ======================================================
    # APPLY GLOBAL-BEST SEED
    # ======================================================

    def _apply_initial_position(self):

        if self.initial_position is None:
            return

        seed_position = np.asarray(
            self.initial_position,
            dtype=float,
        ).copy()

        # --------------------------------------------------
        # Validate dimensions
        # --------------------------------------------------

        if seed_position.shape != (
            self.dimensions,
        ):
            return

        # --------------------------------------------------
        # Keep inside bounds
        # --------------------------------------------------

        seed_position = np.clip(
            seed_position,
            self.lower_bounds,
            self.upper_bounds,
        )

        # --------------------------------------------------
        # Put previous best into first individual
        # --------------------------------------------------

        self.population[0] = (
            seed_position
        )

        # --------------------------------------------------
        # Recalculate its score
        # --------------------------------------------------

        seed_score = float(
            self.objective_function(
                seed_position
            )
        )

        self.scores[0] = (
            seed_score
        )

        # --------------------------------------------------
        # Recalculate global best
        # --------------------------------------------------

        best_index = np.argmin(
            self.scores
        )

        self.global_best_position = (
            self.population[
                best_index
            ].copy()
        )

        self.global_best_score = float(
            self.scores[
                best_index
            ]
        )

        # --------------------------------------------------
        # Reset history
        # --------------------------------------------------

        self.history = [
            self.global_best_score
        ]

        print()
        print(
            ">>> Differential Evolution "
            "global-best seed applied:"
        )

        print(
            f">>> Position: "
            f"{seed_position}"
        )

        print(
            f">>> Score: "
            f"{seed_score}"
        )

    # ======================================================
    # OPTIMIZE
    # ======================================================

    def optimize(
        self,
        iterations=10,
    ):
        """
        Run Differential Evolution for several generations.
        """

        # ==================================================
        # APPLY PREVIOUS GLOBAL BEST
        # ==================================================

        self._apply_initial_position()

        # ==================================================
        # MAIN DE LOOP
        # ==================================================

        for _ in range(iterations):

            for i in range(
                self.population_size
            ):

                candidates = [
                    j
                    for j in range(
                        self.population_size
                    )
                    if j != i
                ]

                # --------------------------------------------------
                # Select three different individuals
                # --------------------------------------------------

                a, b, c = self.rng.choice(
                    candidates,
                    size=3,
                    replace=False,
                )

                # --------------------------------------------------
                # Mutation
                # --------------------------------------------------

                mutant = (
                    self.population[a]
                    + 0.8
                    * (
                        self.population[b]
                        - self.population[c]
                    )
                )

                mutant = np.clip(
                    mutant,
                    self.lower_bounds,
                    self.upper_bounds,
                )

                # --------------------------------------------------
                # Crossover
                # --------------------------------------------------

                trial = (
                    self.population[i].copy()
                )

                mask = (
                    self.rng.random(
                        self.dimensions
                    )
                    < 0.9
                )

                # Guarantee at least one
                # mutated dimension.
                mask[
                    self.rng.integers(
                        0,
                        self.dimensions,
                    )
                ] = True

                trial[mask] = (
                    mutant[mask]
                )

                # --------------------------------------------------
                # Evaluate trial
                # --------------------------------------------------

                trial_score = float(
                    self.objective_function(
                        trial
                    )
                )

                # --------------------------------------------------
                # Selection
                # --------------------------------------------------

                if (
                    trial_score
                    < self.scores[i]
                ):

                    self.population[i] = (
                        trial
                    )

                    self.scores[i] = (
                        trial_score
                    )

                    # ----------------------------------------------
                    # Update global best
                    # ----------------------------------------------

                    if (
                        trial_score
                        < self.global_best_score
                    ):

                        self.global_best_score = (
                            trial_score
                        )

                        self.global_best_position = (
                            trial.copy()
                        )

            # --------------------------------------------------
            # Record convergence
            # --------------------------------------------------

            self.history.append(
                float(
                    self.global_best_score
                )
            )

        # ==================================================
        # FINAL RESULT
        # ==================================================

        return {
            "best_position": (
                self.global_best_position.copy()
            ),

            "best_score": float(
                self.global_best_score
            ),

            "history": (
                self.history.copy()
            ),
        }