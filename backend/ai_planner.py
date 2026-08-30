import os
import time
import httpx

from google import genai
from google.genai import types
from google.genai import errors


class AIPlanner:
    """
    Gemini-powered strategic planner for OptiAgent.

    Primary:
        Gemini Function Calling / AFC

    Fallback:
        Local intelligent strategy selection

    Supports:
        - PSO
        - Differential Evolution
        - Genetic Algorithm
        - Simulated Annealing
        - Hill Climbing
        - CMA-ES
        - Nelder-Mead

    If Gemini becomes unavailable or quota is exhausted,
    the planner permanently switches to the local fallback
    for the lifetime of this planner instance.
    """

    # ======================================================
    # INITIALIZATION
    # ======================================================

    def __init__(
        self,
        algorithms,
        model=None,
        api_key=None,
    ):

        if not algorithms:
            raise ValueError(
                "AIPlanner requires at least one "
                "optimization algorithm."
            )

        self.algorithms = list(algorithms)

        # ==================================================
        # API KEY
        # ==================================================

        self.api_key = (
            api_key
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
        )

        # ==================================================
        # MODEL
        # ==================================================

        self.model = (
            model
            or os.getenv(
                "GEMINI_MODEL",
                "gemini-3.6-flash",
            )
        )

        # ==================================================
        # GEMINI CLIENT
        # ==================================================

        self.client = None

        if self.api_key:

            try:

                self.client = genai.Client(
                    api_key=self.api_key,
                    http_options=types.HttpOptions(
                        timeout=120000
                    ),
                )

            except Exception as exc:

                print(
                    f">>> Gemini client initialization failed: {exc}"
                )

                self.client = None

        # ==================================================
        # STATE
        # ==================================================

        self.last_recommendation = None

        self.decision_history = []

        self.gemini_available = (
            self.client is not None
        )

        # Once quota is exhausted, don't make
        # unnecessary Gemini requests again.
        self.gemini_quota_exhausted = False

    # ======================================================
    # GEMINI FUNCTION
    # ======================================================

    def select_optimization_strategy(
        self,
        algorithm: str,
        reason: str,
        exploration_level: str,
        confidence: float,
    ):
        """
        Validate and store Gemini's optimizer decision.
        """

        print()
        print(
            ">>> Function Calling decision received"
        )

        print(
            f">>> Requested algorithm: {algorithm}"
        )

        selected_algorithm = None

        # ==================================================
        # MATCH ALGORITHM
        # ==================================================

        for available in self.algorithms:

            if (
                str(available).strip().lower()
                ==
                str(algorithm).strip().lower()
            ):

                selected_algorithm = available

                break

        # ==================================================
        # INVALID
        # ==================================================

        if selected_algorithm is None:

            raise ValueError(
                "Gemini selected an unavailable "
                f"algorithm: {algorithm}. "
                f"Available algorithms: "
                f"{self.algorithms}"
            )

        # ==================================================
        # EXPLORATION
        # ==================================================

        exploration = (
            str(
                exploration_level
            )
            .strip()
            .lower()
        )

        if exploration not in {
            "low",
            "medium",
            "high",
        }:

            exploration = "medium"

        # ==================================================
        # CONFIDENCE
        # ==================================================

        try:

            confidence_value = float(
                confidence
            )

        except (
            TypeError,
            ValueError,
        ):

            confidence_value = 0.5

        confidence_value = max(
            0.0,
            min(
                1.0,
                confidence_value,
            ),
        )

        # ==================================================
        # RESULT
        # ==================================================

        result = {

            "success": True,

            "recommended_strategy": (
                selected_algorithm
            ),

            "reason": str(
                reason
            ),

            "exploration_level": (
                exploration
            ),

            "confidence": (
                confidence_value
            ),

            "source": "gemini",
        }

        self.last_recommendation = result

        print(
            f">>> Selected: {selected_algorithm}"
        )

        return result

    # ======================================================
    # BUILD PROMPT
    # ======================================================

    def _build_prompt(
        self,
        problem_description,
        dimensions,
        bounds,
        current_strategy,
        optimization_status,
        best_score,
        validation,
        avoid_strategy=None,
    ):

        bounds_text = []

        for index, bound in enumerate(
            bounds,
            start=1,
        ):

            try:

                lower = float(
                    bound[0]
                )

                upper = float(
                    bound[1]
                )

                bounds_text.append(
                    f"x{index}: [{lower}, {upper}]"
                )

            except Exception:

                bounds_text.append(
                    f"x{index}: {bound}"
                )

        bounds_text = "\n".join(
            bounds_text
        )

        # ==================================================
        # CURRENT STRATEGY
        # ==================================================

        current_strategy_text = (
            "None"
            if current_strategy is None
            else str(current_strategy)
        )

        # ==================================================
        # SCORE
        # ==================================================

        score_text = (
            "None"
            if best_score is None
            else str(best_score)
        )

        # ==================================================
        # VALIDATION
        # ==================================================

        if validation is None:

            validation_text = (
                "No validation available. "
                "This is the initial decision."
            )

        else:

            validation_text = (
                f"valid: "
                f"{validation.get('valid')}\n"
                f"reliable: "
                f"{validation.get('reliable')}\n"
                f"actual_score: "
                f"{validation.get('actual_score')}\n"
                f"reason: "
                f"{validation.get('reason')}"
            )

        # ==================================================
        # STRATEGY EXCLUSION
        # ==================================================

        if avoid_strategy:

            strategy_exclusion = f"""

CRITICAL STRATEGY CHANGE RULE
=============================

The previous strategy was:

{avoid_strategy}

The optimization has stagnated.

DO NOT select {avoid_strategy} again.

You MUST select a DIFFERENT optimizer.

This rule has higher priority than the
normal algorithm-selection preference.
"""

        else:

            strategy_exclusion = """

STRATEGY CHANGE RULE
====================

No optimizer is currently excluded.

Select the most appropriate optimizer.
"""

        # ==================================================
        # PROMPT
        # ==================================================

        return f"""
You are the strategic optimization brain
of OptiAgent.

Your job is to select ONE optimization
algorithm for the current stage.

OBJECTIVE
---------
{problem_description}

DIMENSIONS
----------
{dimensions}

BOUNDS
------
{bounds_text}

AVAILABLE ALGORITHMS
--------------------
{", ".join(str(a) for a in self.algorithms)}

CURRENT STRATEGY
----------------
{current_strategy_text}

{strategy_exclusion}

OPTIMIZATION STATUS
-------------------
{optimization_status}

CURRENT GLOBAL BEST SCORE
-------------------------
{score_text}

VALIDATION
----------
{validation_text}

ALGORITHM GUIDANCE
------------------

PSO:
Population-based global optimizer.
Good for continuous multimodal problems.

Differential Evolution:
Strong population-based global optimizer.
Useful for difficult continuous search spaces.

Genetic Algorithm:
Useful when mutation and population diversity
are important.

Simulated Annealing:
Useful for escaping local minima.

Hill Climbing:
Useful mainly for local refinement.

CMA-ES:
Strong continuous optimizer, especially for
smooth numerical functions.

Nelder-Mead:
Derivative-free local optimization.

DECISION RULES
--------------

Consider:

1. Objective-function structure.
2. Multimodality.
3. Dimensionality.
4. Search bounds.
5. Exploration requirements.
6. Exploitation requirements.
7. Current strategy.
8. Stagnation.
9. Validation.
10. Current global best score.

IMPORTANT
---------

You MUST call:

select_optimization_strategy

Call it exactly once.

Select exactly ONE algorithm.

The selected algorithm MUST be one of:

{self.algorithms}

Do not invent an algorithm.

If a strategy is explicitly excluded,
you MUST NOT select it.

The function arguments must contain:

algorithm
reason
exploration_level
confidence
"""

    # ======================================================
    # GEMINI TOOL
    # ======================================================

    def _get_tool(self):

        return types.Tool(

            function_declarations=[

                types.FunctionDeclaration(

                    name=(
                        "select_optimization_strategy"
                    ),

                    description=(
                        "Select exactly one "
                        "optimization algorithm "
                        "for OptiAgent."
                    ),

                    parameters={

                        "type": "OBJECT",

                        "properties": {

                            "algorithm": {

                                "type": "STRING",

                                "description": (
                                    "Exact name of "
                                    "selected optimizer."
                                ),
                            },

                            "reason": {

                                "type": "STRING",

                                "description": (
                                    "Technical reason "
                                    "for selection."
                                ),
                            },

                            "exploration_level": {

                                "type": "STRING",

                                "enum": [
                                    "low",
                                    "medium",
                                    "high",
                                ],
                            },

                            "confidence": {

                                "type": "NUMBER",

                                "description": (
                                    "Confidence from "
                                    "0.0 to 1.0."
                                ),
                            },
                        },

                        "required": [

                            "algorithm",

                            "reason",

                            "exploration_level",

                            "confidence",
                        ],
                    },
                )
            ]
        )

    # ======================================================
    # LOCAL FALLBACK
    # ======================================================

    def _local_fallback(
        self,
        problem_description,
        dimensions,
        bounds,
        current_strategy=None,
        optimization_status="initial",
        best_score=None,
        validation=None,
        avoid_strategy=None,
    ):
        """
        Local intelligent strategy selector.

        Used when Gemini is unavailable,
        quota is exhausted, or the API fails.
        """

        text = str(
            problem_description
        ).lower()

        # ==================================================
        # REMOVE AVOIDED STRATEGY
        # ==================================================

        available = [

            algorithm

            for algorithm in self.algorithms

            if not (
                avoid_strategy
                and
                algorithm.strip().lower()
                ==
                str(
                    avoid_strategy
                ).strip().lower()
            )
        ]

        if not available:

            raise RuntimeError(
                "No optimizer remains after applying "
                "strategy exclusion."
            )

        # ==================================================
        # DETECT FUNCTION TYPE
        # ==================================================

        multimodal = any(
            keyword in text
            for keyword in [
                "schwefel",
                "rastrigin",
                "ackley",
                "griewank",
                "multimodal",
            ]
        )

        trigonometric = any(
            keyword in text
            for keyword in [
                "sin",
                "cos",
                "tan",
            ]
        )

        quadratic = any(
            keyword in text
            for keyword in [
                "sphere",
                "quadratic",
                "x1**2",
                "x2**2",
            ]
        )

        # ==================================================
        # INITIAL CANDIDATE ORDER
        # ==================================================

        if multimodal:

            candidates = [

                "PSO",

                "Differential Evolution",

                "Genetic Algorithm",

                "CMA-ES",

                "Simulated Annealing",

                "Nelder-Mead",

                "Hill Climbing",
            ]

        elif quadratic:

            candidates = [

                "CMA-ES",

                "PSO",

                "Nelder-Mead",

                "Differential Evolution",

                "Hill Climbing",

                "Simulated Annealing",

                "Genetic Algorithm",
            ]

        elif trigonometric:

            candidates = [

                "PSO",

                "CMA-ES",

                "Differential Evolution",

                "Genetic Algorithm",

                "Simulated Annealing",

                "Nelder-Mead",

                "Hill Climbing",
            ]

        else:

            candidates = [

                "PSO",

                "CMA-ES",

                "Differential Evolution",

                "Genetic Algorithm",

                "Simulated Annealing",

                "Nelder-Mead",

                "Hill Climbing",
            ]

        # ==================================================
        # STAGNATION
        # ==================================================

        if (
            optimization_status
            == "stagnating"
        ):

            candidates = [

                "PSO",

                "Differential Evolution",

                "Genetic Algorithm",

                "CMA-ES",

                "Simulated Annealing",

                "Nelder-Mead",

                "Hill Climbing",
            ]

        # ==================================================
        # FILTER
        # ==================================================

        filtered = [

            candidate

            for candidate in candidates

            if candidate in available
        ]

        if not filtered:

            filtered = available

        # ==================================================
        # AVOID SAME STRATEGY
        # ==================================================

        if (
            current_strategy
            and
            optimization_status
            == "stagnating"
        ):

            different = [

                candidate

                for candidate in filtered

                if candidate.strip().lower()
                !=
                str(
                    current_strategy
                ).strip().lower()
            ]

            if different:

                filtered = different

        # ==================================================
        # SELECT
        # ==================================================

        selected = filtered[0]

        # ==================================================
        # EXPLORATION
        # ==================================================

        if (
            optimization_status
            == "stagnating"
        ):

            exploration = "high"

        elif (
            multimodal
            or
            dimensions >= 10
        ):

            exploration = "high"

        elif quadratic:

            exploration = "low"

        else:

            exploration = "medium"

        # ==================================================
        # CONFIDENCE
        # ==================================================

        confidence = 0.70

        # ==================================================
        # REASON
        # ==================================================

        if (
            optimization_status
            == "stagnating"
        ):

            reason = (
                "Gemini is unavailable and the previous "
                "strategy stagnated. The local fallback "
                "selected a different optimizer to "
                "increase search diversity."
            )

        elif multimodal:

            reason = (
                "The objective appears multimodal. "
                "The fallback selected a population-based "
                "global optimizer suitable for exploring "
                "multiple regions of the search space."
            )

        elif quadratic:

            reason = (
                "The objective appears smooth and "
                "quadratic-like. The fallback selected "
                "an optimizer suited to continuous "
                "numerical optimization."
            )

        elif trigonometric:

            reason = (
                "The objective contains trigonometric "
                "terms and may contain multiple local "
                "regions. A global continuous optimizer "
                "was selected."
            )

        else:

            reason = (
                "Gemini is unavailable. The local "
                "fallback selected an optimizer based "
                "on the objective characteristics, "
                "dimensionality, and search requirements."
            )

        # ==================================================
        # RESULT
        # ==================================================

        result = {

            "success": True,

            "recommended_strategy": (
                selected
            ),

            "reason": reason,

            "exploration_level": (
                exploration
            ),

            "confidence": (
                confidence
            ),

            "source": "local_fallback",
        }

        self.last_recommendation = result

        print()
        print(
            "=" * 60
        )

        print(
            "       LOCAL FALLBACK DECISION"
        )

        print(
            "=" * 60
        )

        print(
            f">>> Strategy: {selected}"
        )

        print(
            f">>> Confidence: {confidence:.2f}"
        )

        print(
            f">>> Exploration: {exploration}"
        )

        print(
            f">>> Reason: {reason}"
        )

        print(
            "=" * 60
        )

        return result

    # ======================================================
    # SEND GEMINI REQUEST
    # ======================================================

    def _send_request(
        self,
        prompt,
        max_attempts=2,
    ):

        if self.client is None:

            raise RuntimeError(
                "Gemini client is unavailable."
            )

        if self.gemini_quota_exhausted:

            raise RuntimeError(
                "Gemini API quota is already known "
                "to be exhausted."
            )

        print()
        print(
            ">>> Gemini agent is reasoning..."
        )

        last_error = None

        # ==================================================
        # RETRIES
        # ==================================================

        for attempt in range(
            1,
            max_attempts + 1,
        ):

            try:

                print()

                print(
                    f">>> Gemini request "
                    f"{attempt}/{max_attempts}"
                )

                # ==========================================
                # CONFIG
                # ==========================================

                config = (
                    types.GenerateContentConfig(

                        temperature=0.1,

                        system_instruction=(

                            "You are the strategic "
                            "optimization brain of "
                            "OptiAgent. "

                            "You MUST call "
                            "select_optimization_strategy "
                            "exactly once. "

                            "Select exactly one "
                            "available optimizer. "

                            "If an optimizer is explicitly "
                            "excluded, NEVER select it."
                        ),

                        tools=[
                            self._get_tool()
                        ],

                        tool_config=(
                            types.ToolConfig(

                                function_calling_config=(

                                    types.FunctionCallingConfig(

                                        mode="ANY",

                                        allowed_function_names=[

                                            "select_optimization_strategy"

                                        ],
                                    )
                                )
                            )
                        ),
                    )
                )

                # ==========================================
                # REQUEST
                # ==========================================

                response = (
                    self.client.models.generate_content(

                        model=self.model,

                        contents=prompt,

                        config=config,
                    )
                )

                if response is None:

                    raise RuntimeError(
                        "Gemini returned an empty response."
                    )

                # ==========================================
                # FIND FUNCTION CALL
                # ==========================================

                function_call = None

                for candidate in (
                    response.candidates
                    or []
                ):

                    content = (
                        candidate.content
                    )

                    if content is None:
                        continue

                    for part in (
                        content.parts
                        or []
                    ):

                        if getattr(
                            part,
                            "function_call",
                            None,
                        ):

                            function_call = (
                                part.function_call
                            )

                            break

                    if function_call:
                        break

                # ==========================================
                # NO FUNCTION CALL
                # ==========================================

                if function_call is None:

                    response_text = ""

                    try:

                        response_text = (
                            response.text
                            or ""
                        )

                    except Exception:

                        pass

                    raise RuntimeError(
                        "Gemini did not make the "
                        "required Function Calling decision.\n"
                        f"Response: {response_text}"
                    )

                # ==========================================
                # VERIFY
                # ==========================================

                if (
                    function_call.name
                    !=
                    "select_optimization_strategy"
                ):

                    raise RuntimeError(
                        "Unexpected Gemini function: "
                        f"{function_call.name}"
                    )

                # ==========================================
                # ARGUMENTS
                # ==========================================

                arguments = dict(
                    function_call.args
                    or {}
                )

                print()
                print(
                    ">>> Function call received"
                )

                print(
                    f">>> Algorithm: "
                    f"{arguments.get('algorithm')}"
                )

                # ==========================================
                # EXECUTE
                # ==========================================

                return (
                    self.select_optimization_strategy(
                        **arguments
                    )
                )

            # ==================================================
            # CLIENT ERROR
            # ==================================================

            except errors.ClientError as exc:

                last_error = exc

                error_text = str(
                    exc
                )

                print()
                print(
                    f">>> Gemini client error: "
                    f"{error_text}"
                )

                # ==========================================
                # QUOTA
                # ==========================================

                if (
                    "429" in error_text
                    or
                    "RESOURCE_EXHAUSTED"
                    in error_text
                    or
                    "quota"
                    in error_text.lower()
                ):

                    # IMPORTANT:
                    # Never retry a known quota failure.
                    self.gemini_quota_exhausted = True
                    self.gemini_available = False

                    raise RuntimeError(
                        "Gemini API quota exhausted."
                    ) from exc

                # ==========================================
                # RETRY OTHER CLIENT ERRORS
                # ==========================================

                if attempt < max_attempts:

                    wait_time = (
                        2 ** (
                            attempt - 1
                        )
                    )

                    print(
                        f">>> Retrying in "
                        f"{wait_time} seconds..."
                    )

                    time.sleep(
                        wait_time
                    )

            # ==================================================
            # SERVER ERROR
            # ==================================================

            except errors.ServerError as exc:

                last_error = exc

                print(
                    f">>> Gemini server error: {exc}"
                )

                if attempt < max_attempts:

                    time.sleep(
                        2 ** (
                            attempt - 1
                        )
                    )

            # ==================================================
            # TIMEOUT
            # ==================================================

            except httpx.ReadTimeout as exc:

                last_error = exc

                print(
                    ">>> Gemini request timed out."
                )

                if attempt < max_attempts:

                    time.sleep(
                        2 ** (
                            attempt - 1
                        )
                    )

            # ==================================================
            # NETWORK ERROR
            # ==================================================

            except httpx.HTTPError as exc:

                last_error = exc

                print(
                    f">>> Gemini network error: {exc}"
                )

                if attempt < max_attempts:

                    time.sleep(
                        2 ** (
                            attempt - 1
                        )
                    )

        # ==================================================
        # FAILURE
        # ==================================================

        raise RuntimeError(
            "Gemini failed after "
            f"{max_attempts} attempts. "
            f"Last error: {last_error}"
        ) from last_error

    # ======================================================
    # PUBLIC STRATEGY METHOD
    # ======================================================

    def recommend_strategy(
        self,
        problem_description,
        dimensions,
        bounds,
        current_strategy=None,
        optimization_status="initial",
        best_score=None,
        validation=None,
        avoid_strategy=None,
    ):
        """
        Select an optimization strategy.

        Gemini is tried first.

        Once Gemini quota is exhausted or the Gemini
        service becomes unavailable, all subsequent
        decisions use the local fallback.
        """

        # ==================================================
        # RESET LAST RECOMMENDATION
        # ==================================================

        self.last_recommendation = None

        # ==================================================
        # BUILD PROMPT
        # ==================================================

        prompt = self._build_prompt(

            problem_description=(
                problem_description
            ),

            dimensions=(
                dimensions
            ),

            bounds=(
                bounds
            ),

            current_strategy=(
                current_strategy
            ),

            optimization_status=(
                optimization_status
            ),

            best_score=(
                best_score
            ),

            validation=(
                validation
            ),

            avoid_strategy=(
                avoid_strategy
            ),
        )
      # ==================================================
        # TRY GEMINI
        # ==================================================

        recommendation = None

        if (
            self.gemini_available
            and
            not self.gemini_quota_exhausted
        ):

            try:

                recommendation = (
                    self._send_request(

                        prompt=prompt,

                        max_attempts=2,
                    )
                )

            except Exception as exc:

                self.gemini_available = False

                error_text = str(
                    exc
                )

                if (
                    "429" in error_text
                    or
                    "RESOURCE_EXHAUSTED"
                    in error_text
                    or
                    "quota"
                    in error_text.lower()
                ):

                    self.gemini_quota_exhausted = True

                print()
                print(
                    ">>> Gemini unavailable."
                )

                print(
                    f">>> Reason: {exc}"
                )

                print()
                print(
                    ">>> Switching to local fallback..."
                )

        # ==================================================
        # FALLBACK
        # ==================================================

        if recommendation is None:

            recommendation = (
                self._local_fallback(

                    problem_description=(
                        problem_description
                    ),

                    dimensions=(
                        dimensions
                    ),

                    bounds=(
                        bounds
                    ),

                    current_strategy=(
                        current_strategy
                    ),

                    optimization_status=(
                        optimization_status
                    ),

                    best_score=(
                        best_score
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
        # VALIDATION
        # ==================================================

        if not isinstance(
            recommendation,
            dict,
        ):

            raise RuntimeError(
                "Strategy planner returned "
                "an invalid recommendation."
            )

        if not recommendation.get(
            "success",
            False,
        ):

            raise RuntimeError(
                "Strategy planner failed "
                "to select a strategy."
            )

        selected = (
            recommendation.get(
                "recommended_strategy"
            )
        )

        if selected not in self.algorithms:

            raise RuntimeError(
                "Strategy planner selected "
                f"an unavailable optimizer: "
                f"{selected}"
            )

        # ==================================================
        # ENFORCE EXCLUSION
        # ==================================================

        if (
            avoid_strategy
            and
            selected.strip().lower()
            ==
            str(
                avoid_strategy
            ).strip().lower()
        ):

            raise RuntimeError(
                f"Strategy '{selected}' is "
                f"explicitly excluded because "
                f"'{avoid_strategy}' stagnated."
            )

        # ==================================================
        # CONFIDENCE
        # ==================================================

        try:

            confidence = float(
                recommendation.get(
                    "confidence",
                    0.5,
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            confidence = 0.5

        confidence = max(
            0.0,
            min(
                1.0,
                confidence,
            ),
        )

        recommendation[
            "confidence"
        ] = confidence

        # ==================================================
        # EXPLORATION
        # ==================================================

        exploration = (
            recommendation.get(
                "exploration_level",
                "medium",
            )
        )

        if exploration not in {
            "low",
            "medium",
            "high",
        }:

            exploration = "medium"

        recommendation[
            "exploration_level"
        ] = exploration

        # ==================================================
        # HISTORY
        # ==================================================

        self.decision_history.append(

            {

                "status": (
                    optimization_status
                ),

                "strategy": (
                    selected
                ),

                "reason": (
                    recommendation.get(
                        "reason",
                        "",
                    )
                ),

                "exploration_level": (
                    exploration
                ),

                "confidence": (
                    confidence
                ),

                "source": (
                    recommendation.get(
                        "source",
                        "gemini",
                    )
                ),
            }
        )

        # ==================================================
        # DISPLAY
        # ==================================================

        print()
        print(
            ">>> STRATEGIC DECISION"
        )

        print(
            f">>> Strategy: {selected}"
        )

        print(
            f">>> Confidence: "
            f"{confidence:.2f}"
        )

        print(
            f">>> Exploration: "
            f"{exploration}"
        )

        print(
            f">>> Source: "
            f"{recommendation.get('source', 'gemini')}"
        )

        print(
            f">>> Reason: "
            f"{recommendation.get('reason', '')}"
        )

        return recommendation

    # ======================================================
    # HISTORY
    # ======================================================

    def get_decision_history(
        self,
    ):

        return list(
            self.decision_history
        )

    # ======================================================
    # RESET HISTORY
    # ======================================================

    def reset_history(
        self,
    ):

        self.decision_history.clear()

        self.last_recommendation = None