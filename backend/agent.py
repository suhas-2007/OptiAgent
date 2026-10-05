from monitor import ConvergenceMonitor
from adaptation import AdaptationEngine
from optimizer_registry import OptimizerRegistry
from ai_planner import AIPlanner
from solution_validator import SolutionValidator


class OptimizationAgent:
    """
    Multi-stage optimization agent.
    Runs optimization in stages and adapts strategies when stagnating.
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

        # basic configuration

        self.objective_function = (
            objective_function
        )

        self.dimensions = dimensions
        self.bounds = bounds
        self.expression = expression

        self.max_stages = max_stages
        self.patience = patience

        # registry

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

        # ai brain

        self.planner = AIPlanner(
            self.algorithms
        )

        # monitor

        self.monitor = (
            ConvergenceMonitor(
                patience=self.patience
            )
        )

        # validator

        self.validator = (
            SolutionValidator(
                objective_function=(
                    self.objective_function
                ),
                dimensions=self.dimensions,
                bounds=self.bounds,
            )
        )

        # adaptation

        self.adaptation = (
            AdaptationEngine()
        )

        # state

        self.current_strategy = None

        self.best_position = None
        self.best_score = float("inf")

        self.strategy_history = []
        self.stage_history = []
        self.convergence_history = []

        # last gemini decision

        self.last_recommendation = None

    # global best

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

    # gemini decision

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

        # save exact gemini decision

        self.last_recommendation = (
            recommendation
        )

        # update current strategy

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

        # safety check

        if (
            selected_strategy
            not in self.algorithms
        ):

            raise RuntimeError(
                "Gemini selected an unavailable "
                f"algorithm: {selected_strategy}"
            )

        # enforce strategy exclusion

        if (
            avoid_strategy is not None
            and
            selected_strategy.strip().lower()
            ==
            avoid_strategy.strip().lower()
        ):

            alternatives = [
                alg for alg in self.algorithms
                if alg.strip().lower() != avoid_strategy.strip().lower()
            ]
            selected_strategy = alternatives[0] if alternatives else self.algorithms[0]
            recommendation["recommended_strategy"] = selected_strategy
            recommendation["reason"] = (
                f"Switched from {avoid_strategy} to {selected_strategy} to escape stagnation."
            )

        self.current_strategy = (
            selected_strategy
        )

        return recommendation

    # run optimizer

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

        # global best seed

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

        # result check

        if not isinstance(
            result,
            dict,
        ):

            raise RuntimeError(
                f"{self.current_strategy} returned "
                "an invalid result."
            )

        # history check

        if "history" not in result:

            result["history"] = []

        # independent validation

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

    # save convergence

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

    # main optimization loop

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

        # initial ai decision

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

        # optimization stages

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

            # run optimizer

            optimizer, result = (
                self._run_optimizer()
            )

            # save convergence

            history = result.get(
                "history",
                [],
            )

            self._save_history(
                stage,
                history,
            )

            # global best

            improved = (
                self._update_global_best(
                    result
                )
            )

            # global progress check

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

            # validation

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

            # monitor

            monitor_result = (
                self.monitor.analyze_history(
                    history
                )
            )

            # strategy history

            self.strategy_history.append(
                self.current_strategy
            )

            # stage history

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

            # display

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

            # exact optimum found

            if self.best_score <= 1e-10:

                print()

                print(
                    ">>> Near-exact optimum found."
                )

                break

            # max stages

            if stage == self.max_stages:

                print()

                print(
                    ">>> Maximum stages reached."
                )

                break

            # still improving

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

            # stagnation detected

            print()

            print(
                ">>> STAGNATION DETECTED"
            )

            # save old strategy

            old_strategy = (
                self.current_strategy
            )

            # optimizer-specific adaptation

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

            # ask gemini for a different strategy

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

            # reset monitor

            self.monitor.reset(
                best_score=self.best_score
            )

        # final result
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

        # final response

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

            # gemini decision

            "recommendation": (
                self.last_recommendation
                if self.last_recommendation
                else {}
            ),
        }