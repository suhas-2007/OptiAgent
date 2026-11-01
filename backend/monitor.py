import math


class ConvergenceMonitor:
    """
    Monitors optimization progress and detects stagnation.
    """

    def __init__(
        self,
        patience=3,
        min_improvement=1e-6,
    ):
        self.patience = max(1, int(patience))
        self.min_improvement = float(min_improvement)

        self.best_score = float("inf")
        self.stagnation_count = 0
        self.history = []

    def analyze_history(self, history):
        if not history:
            return {
                "best_score": None,
                "recent_improvement": 0.0,
                "stagnating": False,
                "trend": "unknown",
            }

        values = []
        for val in history:
            try:
                num = float(val)
                if math.isfinite(num):
                    values.append(num)
            except (TypeError, ValueError):
                continue

        if not values:
            return {
                "best_score": None,
                "recent_improvement": 0.0,
                "stagnating": False,
                "trend": "unknown",
            }

        best_score = min(values)
        window_size = min(len(values), self.patience + 1)
        recent = values[-window_size:]

        if len(recent) >= 2:
            recent_improvement = recent[0] - min(recent)
        else:
            recent_improvement = 0.0

        stagnating = (
            len(recent) >= self.patience
            and recent_improvement <= self.min_improvement
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

    def reset(self, best_score=float("inf")):
        try:
            self.best_score = float(best_score)
        except (TypeError, ValueError):
            self.best_score = float("inf")
        self.stagnation_count = 0
        self.history = []