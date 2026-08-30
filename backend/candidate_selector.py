class CandidateSelector:
    """
    Selects a small portfolio of suitable optimization
    algorithms based on the objective function and dimension.

    This is a fast local decision. It does NOT run any
    optimization.
    """

    def __init__(self, available_algorithms):
        self.available_algorithms = available_algorithms

    def select(self, expression, dimensions):
        expression_lower = expression.lower()

        # --------------------------------------------------
        # Function characteristics
        # --------------------------------------------------

        multimodal_terms = [
            "sin",
            "cos",
            "tan",
            "exp",
        ]

        local_search_terms = [
            "abs",
            "max",
            "min",
        ]

        is_multimodal = any(
            term in expression_lower
            for term in multimodal_terms
        )

        is_local_search_problem = any(
            term in expression_lower
            for term in local_search_terms
        )

        high_dimension = dimensions >= 10

        # --------------------------------------------------
        # Candidate portfolio
        # --------------------------------------------------

        if is_multimodal:

            preferred = [
                "Differential Evolution",
                "PSO",
                "Genetic Algorithm",
            ]

        elif high_dimension:

            preferred = [
                "Differential Evolution",
                "CMA-ES",
                "PSO",
            ]

        elif is_local_search_problem:

            preferred = [
                "Differential Evolution",
                "Nelder-Mead",
                "Simulated Annealing",
            ]

        else:

            preferred = [
                "CMA-ES",
                "Differential Evolution",
                "PSO",
            ]

        # --------------------------------------------------
        # Keep only registered algorithms
        # --------------------------------------------------

        candidates = [
            algorithm
            for algorithm in preferred
            if algorithm in self.available_algorithms
        ]

        # Safety fallback
        if not candidates:
            candidates = self.available_algorithms[:3]

        return candidates[:3]