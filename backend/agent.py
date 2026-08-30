from monitor import ConvergenceMonitor
from adaptation import AdaptationEngine
from optimizer_registry import OptimizerRegistry
from ai_planner import AIPlanner
from solution_validator import SolutionValidator


class OptimizationAgent:
    """
    Autonomous Agentic Optimization System.

    Observe
        ↓
    Reason
        ↓
    Decide
        ↓
    Act
        ↓
    Validate
        ↓
    Monitor
        ↓
    Adapt
        ↓
    Repeat

    The AI planner selects the optimization strategy.
    If a strategy stagnates, the next AI decision is explicitly
    told to avoid the previous strategy.
    """

    def __init__(
        self,
        objective_function,
        dimensions,
        bounds,
        expression,
        max_stages=5,
        patience=3,
    ):

        # ==================================================
        # BASIC CONFIGURATION
        # ==================================================

        self.objective_function = (
            objective_function
        )

        self.dimensions = dimensions
        self.bounds = bounds
        self.expression = expression

        self.max_stages = max_stages
        self.patience = patience

        # ==================================================
        # REGISTRY
        # ==================================================

        self.registry = (
            OptimizerRegistry()
        )

        self.algorithms = (
            self.registry.available_algorithms()
        )

        if not self.algorithms:
            raise RuntimeError(
                "No optimization algorithms are registered."
            )

        # ==================================================
        # AI BRAIN
        # ==================================================

        self.planner = AIPlanner(
            self.algorithms
        )

        # ==================================================
        # MONITOR
        # ==================================================

        self.monitor = (
            ConvergenceMonitor(
                patience=self.patience
            )
        )

        # ==================================================
        # VALIDATOR
        # ==================================================

        self.validator = (
            SolutionValidator(
                objective_function=(
                    self.objective_function
                ),
                dimensions=self.dimensions,
                bounds=self.bounds,
            )
        )

        # ==================================================
        # ADAPTATION
        # ==================================================

        self.adaptation = (
            AdaptationEngine()
        )

        # ==================================================
        # STATE
        # ==================================================

        self.current_strategy = None

        self.best_position = None
        self.best_score = float("inf")

        self.strategy_history = []
        self.stage_history = []
        self.convergence_history = []

        # ==================================================
        # LAST GEMINI DECISION
        # ==================================================

        self.last_recommendation = None

    # ======================================================
    # GLOBAL BEST
    # ======================================================

    def _update_global_best(
        self,
        result,
    ):

        score = float(
            result["best_score"]
        )

        if score < self.best_score:

            self.best_score = score

            position = result[
                "best_position"
            ]

            if hasattr(
                position,
                "copy",
            ):

                self.best_position = (
                    position.copy()
                )

            else:

                self.best_position = position

            return True

        return False

    # ======================================================
    # GEMINI DECISION
    # ======================================================

    def _ask_gemini(
        self,
        status,
        validation=None,
        avoid_strategy=None,
    ):
        """
        Ask Gemini to select the next optimizer.

        avoid_strategy:
            Previous strategy that must not be selected
            again after stagnation.
        """

        recommendation = (
            self.planner.recommend_strategy(
                problem_description=(
                    "Minimize the user-defined "
                    "objective function:\n"
                    f"{self.expression}"
                ),

                dimensions=self.dimensions,

                bounds=self.bounds,

                current_strategy=(
                    self.current_strategy
                ),

                optimization_status=(
                    status
                ),

                best_score=(
                    self.best_score
                ),

                validation=(
                    validation
                ),

                avoid_strategy=(
                    avoid_strategy
                ),
            )
        )

        # ==================================================
        # SAVE EXACT GEMINI DECISION
        # ==================================================

        self.last_recommendation = (
            recommendation
        )

        # ==================================================
        # UPDATE CURRENT STRATEGY
        # ==================================================

        selected_strategy = (
            recommendation.get(
                "recommended_strategy"
            )
        )

        if not selected_strategy:

            raise RuntimeError(
                "Gemini did not return a "
                "recommended optimization strategy."
            )

        # ==================================================
        # SAFETY CHECK
        # ==================================================

        if (
            selected_strategy
            not in self.algorithms
        ):

            raise RuntimeError(
                "Gemini selected an unavailable "
                f"algorithm: {selected_strategy}"
            )

        # ==================================================
        # ENFORCE STRATEGY EXCLUSION
        # ==================================================

        if (
            avoid_strategy is not None
            and
            selected_strategy.strip().lower()
            ==
            avoid_strategy.strip().lower()
        ):

            raise RuntimeError(
                "Gemini selected the same strategy "
                f"'{selected_strategy}' even though "
                f"'{avoid_strategy}' was explicitly "
                "excluded after stagnation."
            )

        self.current_strategy = (
            selected_strategy
        )

        return recommendation

    # ======================================================
    # RUN OPTIMIZER
    # ======================================================

    def _run_optimizer(self):

        optimizer = (
            self.registry.create(
                name=self.current_strategy,

                objective_function=(
                    self.objective_function
                ),

                dimensions=(
                    self.dimensions
                ),

                bounds=(
                    self.bounds
                ),
            )
        )

        # ==================================================
        # GLOBAL BEST SEED
        # ==================================================

        if self.best_position is not None:

            try:

                optimizer.initial_position = (
                    self.best_position.copy()
                )

                print()
                print(
                    ">>> Seeding optimizer with previous global best:"
                )

                print(
                    f">>> {self.best_position}"
                )

            except Exception:

                optimizer.initial_position = (
                    self.best_position
                )

        result = optimizer.optimize()

        # ==================================================
        # RESULT CHECK
        # ==================================================

        if not isinstance(
            result,
            dict,
        ):

            raise RuntimeError(
                f"{self.current_strategy} returned "
                "an invalid result."
            )

        # ==================================================
        # HISTORY CHECK
        # ==================================================

        if "history" not in result:

            result["history"] = []

        # ==================================================
        # INDEPENDENT VALIDATION
        # ==================================================

        validation = (
            self.validator.validate_result(
                result
            )
        )

        result["validation"] = (
            validation
        )

        if not validation["valid"]:

            raise RuntimeError(
                "Optimizer returned an invalid solution: "
                + validation["reason"]
            )

        return optimizer, result

    # ======================================================
    # SAVE CONVERGENCE
    # ======================================================

    def _save_history(
        self,
        stage,
        history,
    ):

        for iteration, score in enumerate(
            history,
            start=1,
        ):

            self.convergence_history.append(
                {
                    "stage": stage,

                    "algorithm": (
                        self.current_strategy
                    ),

                    "iteration": iteration,

                    "score": float(
                        score
                    ),
                }
            )

    # ======================================================
    # MAIN OPTIMIZATION LOOP
    # ======================================================

    def optimize(self):

        print()
        print("=" * 60)
        print(
            "                    OPTIAGENT"
        )
        print("=" * 60)

        print()

        print(
            f"Function: "
            f"{self.expression}"
        )

        print()

        print(
            "Available algorithms:"
        )

        for algorithm in self.algorithms:

            print(
                f"    - {algorithm}"
            )

        # ==================================================
        # INITIAL AI DECISION
        # ==================================================

        print()

        print(
            ">>> Asking Gemini for initial strategy..."
        )

        recommendation = (
            self._ask_gemini(
                status="initial",
                validation=None,
                avoid_strategy=None,
            )
        )

        print()

        print(
            f">>> Initial strategy: "
            f"{self.current_strategy}"
        )

        print(
            f">>> Confidence: "
            f"{recommendation.get('confidence', 0.0):.2f}"
        )

        print(
            f">>> Exploration: "
            f"{recommendation.get('exploration_level', 'medium')}"
        )

        print(
            f">>> Reason: "
            f"{recommendation.get('reason', '')}"
        )

        # ==================================================
        # OPTIMIZATION STAGES
        # ==================================================

        for stage in range(
            1,
            self.max_stages + 1,
        ):

            print()

            print(
                "-" * 60
            )

            print(
                f"STAGE "
                f"{stage}/{self.max_stages}"
            )

            print(
                f"Algorithm: "
                f"{self.current_strategy}"
            )

            print(
                "-" * 60
            )

            # ==================================================
            # RUN OPTIMIZER
            # ==================================================

            optimizer, result = (
                self._run_optimizer()
            )

            # ==================================================
            # SAVE CONVERGENCE
            # ==================================================

            history = result.get(
                "history",
                [],
            )

            self._save_history(
                stage,
                history,
            )

            # ==================================================
            # GLOBAL BEST
            # ==================================================

            improved = (
                self._update_global_best(
                    result
                )
            )

            # ==================================================
            # GLOBAL PROGRESS CHECK
            # ==================================================

            global_stagnating = not improved

            if global_stagnating:

                print()
                print(
                    ">>> Global best was NOT improved."
                )

                print(
                    f">>> Current global best: "
                    f"{self.best_score}"
                )

                print(
                    f">>> Stage result: "
                    f"{result['best_score']}"
                )

            else:

                print()
                print(
                    ">>> Global best IMPROVED."
                )

                print(
                    f">>> New global best: "
                    f"{self.best_score}"
                )

            # ==================================================
            # VALIDATION
            # ==================================================

            validation = (
                result["validation"]
            )

            print()

            print(
                ">>> Solution validation"
            )

            print(
                f">>> Valid: "
                f"{validation['valid']}"
            )

            print(
                f">>> Reliable: "
                f"{validation['reliable']}"
            )

            print(
                f">>> Verified score: "
                f"{validation['actual_score']}"
            )

            # ==================================================
            # MONITOR
            # ==================================================

            monitor_result = (
                self.monitor.analyze_history(
                    history
                )
            )

            # ==================================================
            # STRATEGY HISTORY
            # ==================================================

            self.strategy_history.append(
                self.current_strategy
            )

            # ==================================================
            # STAGE HISTORY
            # ==================================================

            self.stage_history.append(
                {
                    "stage": stage,

                    "strategy": (
                        self.current_strategy
                    ),

                    "stage_best_score": float(
                        result["best_score"]
                    ),

                    "verified_score": float(
                        validation[
                            "actual_score"
                        ]
                    ),

                    "global_best_score": float(
                        self.best_score
                    ),

                    "improved": improved,

                    "trend": (
                        monitor_result[
                            "trend"
                        ]
                    ),

                    "stagnating": (
                        monitor_result[
                            "stagnating"
                        ]
                    ),

                    "reliable": (
                        validation[
                            "reliable"
                        ]
                    ),
                }
            )

            # ==================================================
            # DISPLAY
            # ==================================================

            print()

            print(
                f"Stage best : "
                f"{result['best_score']}"
            )

            print(
                f"Global best: "
                f"{self.best_score}"
            )

            print(
                f"Trend      : "
                f"{monitor_result['trend']}"
            )

            print(
                f"Stagnating : "
                f"{monitor_result['stagnating']}"
            )

            # ==================================================
            # EXACT OPTIMUM FOUND
            # ==================================================

            if self.best_score <= 1e-10:

                print()

                print(
                    ">>> Near-exact optimum found."
                )

                break

            # ==================================================
            # MAX STAGES
            # ==================================================

            if stage == self.max_stages:

                print()

                print(
                    ">>> Maximum stages reached."
                )

                break

            # ==================================================
            # STILL IMPROVING
            # ==================================================

            if (
                not monitor_result["stagnating"]
                and not global_stagnating
            ):

                print()

                print(
                    ">>> Optimization is improving."
                )

                print(
                    ">>> Continuing current strategy."
                )

                continue

            # ==================================================
            # STAGNATION DETECTED
            # ==================================================

            print()

            print(
                ">>> STAGNATION DETECTED"
            )

            # ==================================================
            # SAVE OLD STRATEGY
            # ==================================================

            old_strategy = (
                self.current_strategy
            )

            # ==================================================
            # OPTIMIZER-SPECIFIC ADAPTATION
            # ==================================================

            adaptation_result = (
                self.adaptation.adapt(
                    optimizer,
                    monitor_result,
                    global_stagnating=global_stagnating,
                )
            )

            print(
                f">>> Adaptation: "
                f"{adaptation_result['action']}"
            )

            print(
                f">>> Adaptation reason: "
                f"{adaptation_result['reason']}"
            )

            # ==================================================
            # ASK GEMINI FOR A DIFFERENT STRATEGY
            # ==================================================

            print()

            print(
                ">>> Agent is asking Gemini "
                "to choose a different strategy..."
            )

            recommendation = (
                self._ask_gemini(
                    status="stagnating",

                    validation=(
                        validation
                    ),

                    avoid_strategy=(
                        old_strategy
                    ),
                )
            )

            new_strategy = (
                recommendation[
                    "recommended_strategy"
                ]
            )

            print()

            print(
                f">>> Previous strategy: "
                f"{old_strategy}"
            )

            print(
                f">>> New strategy: "
                f"{new_strategy}"
            )

            print(
                f">>> Confidence: "
                f"{recommendation.get('confidence', 0.0):.2f}"
            )

            print(
                f">>> Exploration: "
                f"{recommendation.get('exploration_level', 'medium')}"
            )

            print(
                f">>> Reason: "
                f"{recommendation.get('reason', '')}"
            )

            # ==================================================
            # RESET MONITOR
            # ==================================================

            self.monitor.reset(
                best_score=self.best_score
            )

        # ======================================================
        # FINAL RESULT
        # ======================================================
        print()

        print(
            "=" * 60
        )

        print(
            "                 FINAL RESULT"
        )

        print(
            "=" * 60
        )

        print()

        print(
            f"Function: "
            f"{self.expression}"
        )

        print(
            f"Best position: "
            f"{self.best_position}"
        )

        print(
            f"Best score: "
            f"{self.best_score}"
        )

        print()

        print(
            "Strategies used:"
        )

        for index, strategy in enumerate(
            self.strategy_history,
            start=1,
        ):

            print(
                f"  Stage {index}: "
                f"{strategy}"
            )

        # ======================================================
        # FINAL RESPONSE
        # ======================================================

        return {
            "best_position": (
                self.best_position
            ),

            "best_score": (
                float(
                    self.best_score
                )
            ),

            "strategy_history": (
                self.strategy_history
            ),

            "stage_history": (
                self.stage_history
            ),

            "convergence_history": (
                self.convergence_history
            ),

            # ==================================================
            # GEMINI DECISION
            # ==================================================

            "recommendation": (
                self.last_recommendation
                if self.last_recommendation
                else {}
            ),
        }