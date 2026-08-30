import time


class AlgorithmBenchmark:
    """
    Lightweight benchmark for comparing candidate optimizers.

    The benchmark is intentionally small so that it does not
    dominate the total optimization runtime.
    """

    def __init__(
        self,
        registry,
        objective_function,
        dimensions,
        bounds,
        budget=30,
    ):
        self.registry = registry
        self.objective_function = objective_function
        self.dimensions = dimensions
        self.bounds = bounds
        self.budget = budget

    def _set_budget(self, optimizer):
        """
        Apply a small iteration budget when the optimizer
        exposes a recognized iteration attribute.
        """

        attributes = [
            "max_iterations",
            "iterations",
            "n_iterations",
            "num_iterations",
            "max_iter",
        ]

        for attribute in attributes:

            if hasattr(optimizer, attribute):

                try:
                    setattr(
                        optimizer,
                        attribute,
                        self.budget,
                    )
                    return

                except Exception:
                    pass

    def run(self, algorithms):
        """
        Run a quick benchmark on the supplied algorithms.
        """

        results = []

        for algorithm_name in algorithms:

            print(
                f">>> Benchmarking "
                f"{algorithm_name}..."
            )

            start = time.perf_counter()

            try:

                optimizer = self.registry.create(
                    name=algorithm_name,
                    objective_function=self.objective_function,
                    dimensions=self.dimensions,
                    bounds=self.bounds,
                )

                self._set_budget(
                    optimizer
                )

                result = optimizer.optimize()

                elapsed = (
                    time.perf_counter()
                    - start
                )

                results.append(
                    {
                        "algorithm": algorithm_name,
                        "best_score": float(
                            result["best_score"]
                        ),
                        "runtime": round(
                            elapsed,
                            4,
                        ),
                        "status": "success",
                    }
                )

                print(
                    f"    score = "
                    f"{result['best_score']:.8g}"
                )

                print(
                    f"    time  = "
                    f"{elapsed:.4f}s"
                )

            except Exception as error:

                elapsed = (
                    time.perf_counter()
                    - start
                )

                print(
                    f"    FAILED: {error}"
                )

                results.append(
                    {
                        "algorithm": algorithm_name,
                        "best_score": float("inf"),
                        "runtime": round(
                            elapsed,
                            4,
                        ),
                        "status": "failed",
                        "error": str(error),
                    }
                )

        return results

    def rank(self, results):
        """
        Rank successful algorithms by optimization quality.
        """

        successful = [
            result
            for result in results
            if result["status"] == "success"
        ]

        return sorted(
            successful,
            key=lambda result: result[
                "best_score"
            ],
        )