import numpy as np


class ParticleSwarmOptimizer:
    """
    Particle Swarm Optimization (PSO).

    The swarm searches for the minimum of a given objective function.

    Supports optional global-best seeding from OptiAgent so that
    later optimization stages can refine the best solution found
    by previous stages.
    """

    def __init__(
        self,
        objective_function,
        dimensions,
        bounds,
        num_particles=30,
        max_iterations=100,
        inertia=0.7,
        cognitive=1.5,
        social=1.5,
        seed=42,
    ):
        self.objective_function = objective_function
        self.dimensions = dimensions
        self.bounds = np.asarray(bounds, dtype=float)

        self.num_particles = num_particles
        self.max_iterations = max_iterations

        self.inertia = inertia
        self.cognitive = cognitive
        self.social = social

        self.rng = np.random.default_rng(seed)

        self.lower_bounds = self.bounds[:, 0]
        self.upper_bounds = self.bounds[:, 1]

        # optional global-best seed

        self.initial_position = None

        # initial particle positions

        self.positions = self.rng.uniform(
            self.lower_bounds,
            self.upper_bounds,
            size=(num_particles, dimensions),
        )

        # initial velocities

        self.velocities = np.zeros(
            (num_particles, dimensions)
        )

        # personal best

        self.personal_best_positions = (
            self.positions.copy()
        )

        self.personal_best_scores = np.array([
            self.objective_function(position)
            for position in self.positions
        ])

        # global best

        best_index = np.argmin(
            self.personal_best_scores
        )

        self.global_best_position = (
            self.personal_best_positions[
                best_index
            ].copy()
        )

        self.global_best_score = (
            self.personal_best_scores[
                best_index
            ]
        )

        # history

        self.history = [
            float(self.global_best_score)
        ]

    # apply global-best seed

    def _apply_initial_position(self):

        if self.initial_position is None:
            return

        # make sure the seed is a numpy array

        seed_position = np.asarray(
            self.initial_position,
            dtype=float,
        ).copy()

        # check dimensions

        if seed_position.shape != (
            self.dimensions,
        ):

            return

        # keep seed inside bounds

        seed_position = np.clip(
            seed_position,
            self.lower_bounds,
            self.upper_bounds,
        )

        # put previous global best into particle 0

        self.positions[0] = seed_position

        # start seeded particle with zero velocity

        self.velocities[0] = 0.0

        # recalculate personal best of particle 0

        seed_score = float(
            self.objective_function(
                seed_position
            )
        )

        self.personal_best_positions[0] = (
            seed_position.copy()
        )

        self.personal_best_scores[0] = (
            seed_score
        )

        # recalculate swarm global best

        best_index = np.argmin(
            self.personal_best_scores
        )

        self.global_best_position = (
            self.personal_best_positions[
                best_index
            ].copy()
        )

        self.global_best_score = (
            self.personal_best_scores[
                best_index
            ]
        )

        # reset history for this optimization run

        self.history = [
            float(self.global_best_score)
        ]

        print()
        print(
            ">>> PSO global-best seed applied:"
        )

        print(
            f">>> Position: "
            f"{seed_position}"
        )

        print(
            f">>> Score: "
            f"{seed_score}"
        )

    # optimize

    def optimize(self, iterations=None):
        """
        Continue optimization for a specified number
        of iterations.

        If iterations is not provided, max_iterations
        is used.
        """

        if iterations is None:
            iterations = self.max_iterations

        # apply previous global best

        self._apply_initial_position()

        # main pso loop

        for _ in range(iterations):

            # random coefficients

            r1 = self.rng.random(
                (
                    self.num_particles,
                    self.dimensions,
                )
            )

            r2 = self.rng.random(
                (
                    self.num_particles,
                    self.dimensions,
                )
            )

            # update velocities

            self.velocities = (
                self.inertia
                * self.velocities

                + self.cognitive
                * r1
                * (
                    self.personal_best_positions
                    - self.positions
                )

                + self.social
                * r2
                * (
                    self.global_best_position
                    - self.positions
                )
            )

            # move particles

            self.positions += (
                self.velocities
            )

            # keep particles inside bounds

            self.positions = np.clip(
                self.positions,
                self.lower_bounds,
                self.upper_bounds,
            )

            # evaluate particles

            scores = np.array([
                self.objective_function(
                    position
                )
                for position in self.positions
            ])

            # update personal bests

            improved = (
                scores
                < self.personal_best_scores
            )

            self.personal_best_positions[
                improved
            ] = self.positions[
                improved
            ]

            self.personal_best_scores[
                improved
            ] = scores[
                improved
            ]

            # update global best

            best_index = np.argmin(
                self.personal_best_scores
            )

            if (
                self.personal_best_scores[
                    best_index
                ]
                < self.global_best_score
            ):

                self.global_best_score = (
                    self.personal_best_scores[
                        best_index
                    ]
                )

                self.global_best_position = (
                    self.personal_best_positions[
                        best_index
                    ].copy()
                )

            # record convergence

            self.history.append(
                float(
                    self.global_best_score
                )
            )

        # final result

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