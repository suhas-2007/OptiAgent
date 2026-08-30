class ConvergenceMonitor:
    """
    Monitors optimization progress and detects stagnation.
    """

    def __init__(
        self,
        patience=3,
        min_improvement=1e-6,
    ):

        self.patience = patience
        self.min_improvement = min_improvement

        self.best_score = float("inf")
        self.stagnation_count = 0

        self.history = []

    # ==================================================
    # ANALYZE OPTIMIZER HISTORY
    # ==================================================

    def analyze_history(self, history):

        if not history:

            return {
                "best_score": None,
                "recent_improvement": 0.0,
                "stagnating": False,
                "trend": "unknown",
            }

        values = [
            float(value)
            for value in history
        ]

        best_score = min(values)

        window_size = min(
            len(values),
            self.patience + 1,
        )

        recent = values[-window_size:]

        if len(recent) >= 2:

            recent_improvement = (
                recent[0] - min(recent)
            )

        else:

            recent_improvement = 0.0

        stagnating = (
            len(recent) >= self.patience
            and recent_improvement
            <= self.min_improvement
        )

        if len(recent) < 2:

            trend = "unknown"

        elif recent[-1] < recent[0]:

            trend = "improving"

        elif recent[-1] > recent[0]:

            trend = "worsening"

        else:

            trend = "flat"

        return {
            "best_score": best_score,
            "recent_improvement": recent_improvement,
            "stagnating": stagnating,
            "trend": trend,
        }

    # ==================================================
    # RESET
    # ==================================================

    def reset(self, best_score=float("inf")):

        self.best_score = float(
            best_score
        )

        self.stagnation_count = 0

        self.history = []