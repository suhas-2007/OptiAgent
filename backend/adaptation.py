class AdaptationEngine:
    """
    Adapts optimizer parameters when convergence stalls.

    Algorithm selection itself is handled by OptimizationAgent.

    This class considers BOTH:
        1. Optimizer-level stagnation
        2. Global-best stagnation

    The global_stagnating flag is supplied by OptimizationAgent.
    """

    def __init__(self):

        self.actions_taken = []

    # ======================================================
    # MAIN ADAPTATION METHOD
    # ======================================================

    def adapt(
        self,
        optimizer,
        monitor_result,
        global_stagnating=False,
    ):
        """
        Adapt the optimizer when progress stalls.

        Parameters
        ----------
        optimizer:
            Current optimizer instance.

        monitor_result:
            Result produced by ConvergenceMonitor.

        global_stagnating:
            True when the current stage failed to improve
            OptiAgent's global best solution.
        """

        # ==================================================
        # CHECK BOTH TYPES OF PROGRESS
        # ==================================================

        optimizer_stagnating = (
            monitor_result.get(
                "stagnating",
                False,
            )
        )

        # ==================================================
        # NO STAGNATION
        # ==================================================

        if (
            not optimizer_stagnating
            and not global_stagnating
        ):

            action = {
                "action": "continue",
                "reason": (
                    "Optimization is still improving "
                    "at both the optimizer and global-best levels."
                ),
            }

            self.actions_taken.append(
                action
            )

            return action

        # ==================================================
        # GLOBAL STAGNATION
        # ==================================================

        if global_stagnating:

            global_reason = (
                "The current stage did not improve "
                "OptiAgent's global best solution."
            )

        else:

            global_reason = (
                "The current stage improved the global best."
            )

        # --------------------------------------------------
        # PSO
        # --------------------------------------------------

        if hasattr(
            optimizer,
            "inertia",
        ):

            old_inertia = (
                optimizer.inertia
            )

            old_social = (
                optimizer.social
            )

            optimizer.inertia = min(
                0.95,
                optimizer.inertia + 0.15,
            )

            optimizer.social = min(
                2.5,
                optimizer.social + 0.2,
            )

            action = {
                "action": "increase_exploration",

                "reason": (
                    "PSO stagnation detected. "
                    "Increasing swarm exploration. "
                    + global_reason
                ),

                "old_inertia": (
                    old_inertia
                ),

                "new_inertia": (
                    optimizer.inertia
                ),

                "old_social": (
                    old_social
                ),

                "new_social": (
                    optimizer.social
                ),
            }

            self.actions_taken.append(
                action
            )

            return action

        # --------------------------------------------------
        # DIFFERENTIAL EVOLUTION
        # --------------------------------------------------

        if (
            hasattr(
                optimizer,
                "population",
            )
            and
            hasattr(
                optimizer,
                "scores",
            )
        ):

            import numpy as np

            population_size = len(
                optimizer.population
            )

            number_to_refresh = max(
                1,
                population_size // 10,
            )

            lower = (
                optimizer.bounds[:, 0]
            )

            upper = (
                optimizer.bounds[:, 1]
            )

            for _ in range(
                number_to_refresh
            ):

                index = (
                    optimizer.rng.integers(
                        0,
                        population_size,
                    )
                    if hasattr(
                        optimizer,
                        "rng",
                    )
                    else
                    np.random.randint(
                        0,
                        population_size,
                    )
                )

                optimizer.population[
                    index
                ] = np.random.uniform(
                    lower,
                    upper,
                    optimizer.dimensions,
                )

                optimizer.scores[
                    index
                ] = (
                    optimizer.objective_function(
                        optimizer.population[
                            index
                        ]
                    )
                )

            # Recalculate population best
            best_index = np.argmin(
                optimizer.scores
            )

            if (
                optimizer.scores[
                    best_index
                ]
                <
                optimizer.global_best_score
            ):

                optimizer.global_best_score = float(
                    optimizer.scores[
                        best_index
                    ]
                )

                optimizer.global_best_position = (
                    optimizer.population[
                        best_index
                    ].copy()
                )

            action = {
                "action": (
                    "increase_population_diversity"
                ),

                "reason": (
                    "Differential Evolution "
                    "stagnated. Refreshing part "
                    "of the population. "
                    + global_reason
                ),
            }

            self.actions_taken.append(
                action
            )

            return action

        # --------------------------------------------------
        # SIMULATED ANNEALING
        # --------------------------------------------------

        if hasattr(
            optimizer,
            "initial_temperature",
        ):

            old_step_size = (
                optimizer.step_size
            )

            optimizer.step_size *= 1.15

            action = {
                "action": (
                    "increase_sa_exploration"
                ),

                "reason": (
                    "Simulated Annealing "
                    "stagnated. Increasing "
                    "neighborhood exploration. "
                    + global_reason
                ),

                "old_step_size": (
                    old_step_size
                ),

                "new_step_size": (
                    optimizer.step_size
                ),
            }

            self.actions_taken.append(
                action
            )

            return action

        # --------------------------------------------------
        # GENETIC ALGORITHM
        # --------------------------------------------------

        if hasattr(
            optimizer,
            "mutation_rate",
        ):

            old_mutation_rate = (
                optimizer.mutation_rate
            )

            optimizer.mutation_rate = min(
                0.5,
                optimizer.mutation_rate + 0.05,
            )

            action = {
                "action": (
                    "increase_mutation"
                ),

                "reason": (
                    "Genetic Algorithm "
                    "stagnated. Increasing "
                    "mutation to restore "
                    "population diversity. "
                    + global_reason
                ),

                "old_mutation_rate": (
                    old_mutation_rate
                ),

                "new_mutation_rate": (
                    optimizer.mutation_rate
                ),
            }

            self.actions_taken.append(
                action
            )

            return action

        # --------------------------------------------------
        # HILL CLIMBING
        # --------------------------------------------------

        if hasattr(
            optimizer,
            "restarts",
        ):

            action = {
                "action": (
                    "restart_local_search"
                ),

                "reason": (
                    "Hill Climbing stagnated. "
                    "Additional restarts can "
                    "escape local minima. "
                    + global_reason
                ),
            }

            self.actions_taken.append(
                action
            )

            return action

        # --------------------------------------------------
        # CMA-ES
        # --------------------------------------------------

        if hasattr(
            optimizer,
            "sigma",
        ):

            old_sigma = (
                optimizer.sigma
            )

            optimizer.sigma = min(
                1.0,
                optimizer.sigma * 1.25,
            )

            action = {
                "action": (
                    "increase_cma_exploration"
                ),

                "reason": (
                    "CMA-ES stagnated. "
                    "Increasing search step "
                    "size. "
                    + global_reason
                ),

                "old_sigma": (
                    old_sigma
                ),

                "new_sigma": (
                    optimizer.sigma
                ),
            }

            self.actions_taken.append(
                action
            )

            return action

        # --------------------------------------------------
        # NELDER-MEAD
        # --------------------------------------------------

        if hasattr(
            optimizer,
            "alpha",
        ):

            action = {
                "action": (
                    "restart_simplex"
                ),

                "reason": (
                    "Nelder-Mead stagnated. "
                    "A simplex restart can "
                    "explore a new region. "
                    + global_reason
                ),
            }

            self.actions_taken.append(
                action
            )

            return action

        # --------------------------------------------------
        # GENERIC FALLBACK
        # --------------------------------------------------

        action = {
            "action": (
                "continue_strategy"
            ),

            "reason": (
                "Stagnation was detected, "
                "but no optimizer-specific "
                "adaptation rule is available. "
                + global_reason
            ),
        }

        self.actions_taken.append(
            action
        )

        return action

    # ======================================================
    # HISTORY
    # ======================================================

    def get_history(self):

        return list(
            self.actions_taken
        )

    # ======================================================
    # RESET
    # ======================================================

    def reset(self):

        self.actions_taken.clear()