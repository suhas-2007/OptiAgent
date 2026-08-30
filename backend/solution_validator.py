import math
import numpy as np


class SolutionValidator:
    """
    Validates and evaluates optimization results.

    The validator does not choose an algorithm.
    It independently checks whether an optimizer's
    solution is valid and reliable.
    """

    def __init__(
        self,
        objective_function,
        dimensions,
        bounds,
        tolerance=1e-8,
    ):

        self.objective_function = objective_function
        self.dimensions = int(dimensions)

        self.bounds = np.asarray(
            bounds,
            dtype=float,
        )

        self.tolerance = float(
            tolerance
        )

        # ==================================================
        # VALIDATE BOUNDS
        # ==================================================

        if self.bounds.shape != (
            self.dimensions,
            2,
        ):

            raise ValueError(
                f"Expected bounds shape "
                f"({self.dimensions}, 2), "
                f"got {self.bounds.shape}."
            )

        if np.any(
            self.bounds[:, 0]
            >= self.bounds[:, 1]
        ):

            raise ValueError(
                "Every lower bound must be "
                "less than its upper bound."
            )

    # ======================================================
    # POSITION VALIDATION
    # ======================================================

    def validate_position(
        self,
        position,
    ):

        if position is None:

            return {
                "valid": False,
                "reason": (
                    "Optimizer returned no position."
                ),
            }

        try:

            position = np.asarray(
                position,
                dtype=float,
            ).flatten()

        except Exception:

            return {
                "valid": False,
                "reason": (
                    "Position contains invalid values."
                ),
            }

        # --------------------------------------------------
        # DIMENSION CHECK
        # --------------------------------------------------

        if len(position) != self.dimensions:

            return {
                "valid": False,
                "reason": (
                    f"Expected {self.dimensions} dimensions, "
                    f"but received {len(position)}."
                ),
            }

        # --------------------------------------------------
        # FINITE CHECK
        # --------------------------------------------------

        if not np.all(
            np.isfinite(position)
        ):

            return {
                "valid": False,
                "reason": (
                    "Position contains NaN or infinity."
                ),
            }

        # --------------------------------------------------
        # BOUND CHECK
        # --------------------------------------------------

        for i, value in enumerate(
            position
        ):

            lower = self.bounds[i, 0]
            upper = self.bounds[i, 1]

            if value < (
                lower - self.tolerance
            ):

                return {
                    "valid": False,
                    "reason": (
                        f"x{i + 1} is below "
                        "its lower bound."
                    ),
                }

            if value > (
                upper + self.tolerance
            ):

                return {
                    "valid": False,
                    "reason": (
                        f"x{i + 1} is above "
                        "its upper bound."
                    ),
                }

        return {
            "valid": True,
            "reason": "Position is valid.",
            "position": position,
        }

    # ======================================================
    # SCORE VALIDATION
    # ======================================================

    def validate_score(
        self,
        score,
    ):

        try:

            score = float(score)

        except (
            TypeError,
            ValueError,
        ):

            return {
                "valid": False,
                "reason": (
                    "Score is not numeric."
                ),
            }

        if not math.isfinite(
            score
        ):

            return {
                "valid": False,
                "reason": (
                    "Score is NaN or infinity."
                ),
            }

        return {
            "valid": True,
            "reason": "Score is valid.",
            "score": score,
        }

    # ======================================================
    # RE-EVALUATE SOLUTION
    # ======================================================

    def reevaluate(
        self,
        position,
    ):

        validation = (
            self.validate_position(
                position
            )
        )

        if not validation["valid"]:

            return {
                "valid": False,
                "reason": (
                    validation["reason"]
                ),
            }

        position = validation[
            "position"
        ]

        try:

            score = (
                self.objective_function(
                    position
                )
            )

            score = float(score)

        except Exception as error:

            return {
                "valid": False,
                "reason": (
                    "Objective function failed "
                    "when re-evaluating the solution."
                ),
                "error": str(error),
            }

        score_validation = (
            self.validate_score(
                score
            )
        )

        if not score_validation["valid"]:

            return score_validation

        return {
            "valid": True,
            "position": position,
            "score": score,
            "reason": (
                "Solution successfully "
                "re-evaluated."
            ),
        }

    # ======================================================
    # HISTORY ANALYSIS
    # ======================================================

    def analyze_history(
        self,
        history,
    ):

        if history is None:

            history = []

        values = []

        for value in history:

            try:

                value = float(value)

                if math.isfinite(
                    value
                ):

                    values.append(
                        value
                    )

            except (
                TypeError,
                ValueError,
            ):

                continue

        if not values:

            return {
                "has_history": False,
                "iterations": 0,
                "improving": False,
                "stagnating": False,
                "best_score": None,
            }

        # --------------------------------------------------
        # BASIC INFORMATION
        # --------------------------------------------------

        best_score = min(
            values
        )

        first_score = values[0]
        last_score = values[-1]

        if len(values) >= 2:

            improvement = (
                first_score
                - last_score
            )

            improving = (
                last_score
                < first_score
            )

        else:

            improvement = 0.0
            improving = False

        # --------------------------------------------------
        # RECENT HISTORY
        # --------------------------------------------------

        recent_count = min(
            5,
            len(values),
        )

        recent = values[
            -recent_count:
        ]

        recent_range = (
            max(recent)
            - min(recent)
        )

        stagnating = (
            len(recent) >= 3
            and
            recent_range
            <= self.tolerance
        )

        return {
            "has_history": True,

            "iterations": len(values),

            "initial_score": (
                first_score
            ),

            "final_score": (
                last_score
            ),

            "best_score": (
                best_score
            ),

            "improvement": (
                improvement
            ),

            "improving": (
                improving
            ),

            "recent_range": (
                recent_range
            ),

            "stagnating": (
                stagnating
            ),
        }

    # ======================================================
    # COMPLETE RESULT VALIDATION
    # ======================================================

    def validate_result(
        self,
        result,
    ):

        # --------------------------------------------------
        # RESULT TYPE
        # --------------------------------------------------

        if not isinstance(
            result,
            dict,
        ):

            return {
                "valid": False,
                "reliable": False,
                "reason": (
                    "Optimizer result must "
                    "be a dictionary."
                ),
            }

        # --------------------------------------------------
        # REQUIRED POSITION
        # --------------------------------------------------

        if "best_position" not in result:

            return {
                "valid": False,
                "reliable": False,
                "reason": (
                    "Optimizer result has "
                    "no best_position."
                ),
            }

        # --------------------------------------------------
        # REQUIRED SCORE
        # --------------------------------------------------

        if "best_score" not in result:

            return {
                "valid": False,
                "reliable": False,
                "reason": (
                    "Optimizer result has "
                    "no best_score."
                ),
            }

        # ==================================================
        # POSITION
        # ==================================================

        position_result = (
            self.validate_position(
                result[
                    "best_position"
                ]
            )
        )

        if not position_result["valid"]:

            return {
                "valid": False,
                "reliable": False,
                "reason": (
                    position_result[
                        "reason"
                    ]
                ),
            }

        # ==================================================
        # REPORTED SCORE
        # ==================================================

        score_result = (
            self.validate_score(
                result[
                    "best_score"
                ]
            )
        )

        if not score_result["valid"]:

            return {
                "valid": False,
                "reliable": False,
                "reason": (
                    score_result[
                        "reason"
                    ]
                ),
            }

        # ==================================================
        # INDEPENDENT RE-EVALUATION
        # ==================================================

        reevaluated = (
            self.reevaluate(
                position_result[
                    "position"
                ]
            )
        )

        if not reevaluated["valid"]:

            return {
                "valid": False,
                "reliable": False,
                "reason": (
                    reevaluated[
                        "reason"
                    ]
                ),
            }

        # ==================================================
        # SCORES
        # ==================================================

        reported_score = (
            score_result["score"]
        )

        actual_score = (
            reevaluated["score"]
        )

        score_difference = abs(
            reported_score
            - actual_score
        )

        # Relative tolerance makes validation
        # safer for large objective values.

        scale = max(
            1.0,
            abs(reported_score),
            abs(actual_score),
        )

        relative_difference = (
            score_difference
            / scale
        )

        score_consistent = (
            score_difference
            <= self.tolerance
            or
            relative_difference
            <= self.tolerance
        )

        # ==================================================
        # HISTORY
        # ==================================================

        history_analysis = (
            self.analyze_history(
                result.get(
                    "history",
                    []
                )
            )
        )

        # ==================================================
        # RELIABILITY
        # ==================================================

        reliable = (
            score_consistent
            and
            history_analysis[
                "has_history"
            ]
            and
            math.isfinite(
                actual_score
            )
        )

        # ==================================================
        # RESULT
        # ==================================================

        return {

            "valid": True,

            "reliable": reliable,

            "position": (
                position_result[
                    "position"
                ]
            ),

            "reported_score": (
                reported_score
            ),

            "actual_score": (
                actual_score
            ),

            "score_difference": (
                score_difference
            ),

            "relative_difference": (
                relative_difference
            ),

            "score_consistent": (
                score_consistent
            ),

            "history": (
                history_analysis
            ),

            "reason": (
                "Solution passed independent "
                "position, bounds, score, and "
                "history validation."
                if reliable
                else
                "Solution is valid, but "
                "additional evaluation may "
                "be required."
            ),
        }