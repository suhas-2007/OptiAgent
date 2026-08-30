from flask import (
    Flask,
    request,
    jsonify,
)
from flask_cors import CORS
from function_parser import SafeFunction
from agent import OptimizationAgent

# ==========================================================
# FLASK APP
# ==========================================================

app = Flask(__name__)
CORS(app)

# ==========================================================
# HOME
# ==========================================================

@app.route(
    "/",
    methods=["GET"],
)
def home():

    return jsonify(
        {
            "success": True,
            "name": "OptiAgent API",
            "status": "running",
            "message": (
                "OptiAgent optimization API "
                "is running."
            ),
        }
    )


# ==========================================================
# HEALTH
# ==========================================================

@app.route(
    "/health",
    methods=["GET"],
)
def health():

    return jsonify(
        {
            "status": "ok"
        }
    )


# ==========================================================
# OPTIMIZE
# ==========================================================

@app.route(
    "/optimize",
    methods=["POST"],
)
def optimize():

    try:

        # ==================================================
        # REQUEST DATA
        # ==================================================

        data = request.get_json(
            silent=True
        )

        if not data:

            return jsonify(
                {
                    "success": False,
                    "error": (
                        "Request body must contain "
                        "valid JSON."
                    ),
                }
            ), 400

        # ==================================================
        # OBJECTIVE
        # ==================================================

        expression = data.get(
            "objective"
        )

        if not expression:

            return jsonify(
                {
                    "success": False,
                    "error": (
                        "Missing 'objective'."
                    ),
                }
            ), 400

        # ==================================================
        # DIMENSIONS
        # ==================================================

        dimensions = data.get(
            "dimensions"
        )

        if dimensions is None:

            return jsonify(
                {
                    "success": False,
                    "error": (
                        "Missing 'dimensions'."
                    ),
                }
            ), 400

        try:

            dimensions = int(
                dimensions
            )

        except (
            TypeError,
            ValueError,
        ):

            return jsonify(
                {
                    "success": False,
                    "error": (
                        "'dimensions' must be "
                        "an integer."
                    ),
                }
            ), 400

        if dimensions <= 0:

            return jsonify(
                {
                    "success": False,
                    "error": (
                        "'dimensions' must be "
                        "greater than zero."
                    ),
                }
            ), 400

        # ==================================================
        # BOUNDS
        # ==================================================

        bounds = data.get(
            "bounds"
        )

        if not isinstance(
            bounds,
            list,
        ):

            return jsonify(
                {
                    "success": False,
                    "error": (
                        "'bounds' must be a list."
                    ),
                }
            ), 400

        if len(bounds) != dimensions:

            return jsonify(
                {
                    "success": False,
                    "error": (
                        "Number of bounds must "
                        "match dimensions."
                    ),
                }
            ), 400

        cleaned_bounds = []

        for index, bound in enumerate(
            bounds,
            start=1,
        ):

            if not isinstance(
                bound,
                (list, tuple),
            ):

                return jsonify(
                    {
                        "success": False,
                        "error": (
                            f"Bounds for x{index} "
                            "must contain "
                            "[lower, upper]."
                        ),
                    }
                ), 400

            if len(bound) != 2:

                return jsonify(
                    {
                        "success": False,
                        "error": (
                            f"Bounds for x{index} "
                            "must contain "
                            "exactly two values."
                        ),
                    }
                ), 400

            try:

                lower = float(
                    bound[0]
                )

                upper = float(
                    bound[1]
                )

            except (
                TypeError,
                ValueError,
            ):

                return jsonify(
                    {
                        "success": False,
                        "error": (
                            f"Bounds for x{index} "
                            "must be numeric."
                        ),
                    }
                ), 400

            if lower >= upper:

                return jsonify(
                    {
                        "success": False,
                        "error": (
                            f"Lower bound must be "
                            f"less than upper "
                            f"bound for x{index}."
                        ),
                    }
                ), 400

            cleaned_bounds.append(
                (
                    lower,
                    upper,
                )
            )

        # ==================================================
        # SAFE FUNCTION
        # ==================================================

        objective_function = (
            SafeFunction(
                expression
            )
        )

        # ==================================================
        # AGENT
        # ==================================================

        agent = OptimizationAgent(

            objective_function=(
                objective_function
            ),

            dimensions=(
                dimensions
            ),

            bounds=(
                cleaned_bounds
            ),

            expression=(
                expression
            ),

            max_stages=int(
                data.get(
                    "max_stages",
                    5,
                )
            ),

            patience=int(
                data.get(
                    "patience",
                    3,
                )
            ),
        )

        # ==================================================
        # RUN OPTIMIZATION
        # ==================================================

        result = agent.optimize()
        print()
        print(">>> RESULT KEYS:")
        print(result.keys())

        print()
        print(">>> GEMINI RECOMMENDATION:")
        print(result.get("recommendation"))
        # ==================================================
        # CONVERT NUMPY VALUES
        # ==================================================

        best_position = result.get(
            "best_position"
        )

        if hasattr(
            best_position,
            "tolist",
        ):

            best_position = (
                best_position.tolist()
            )

        elif best_position is not None:

            best_position = list(
                best_position
            )

        # ==================================================
        # RESPONSE
        # ==================================================

        return jsonify(
            {
                "success": True,

                "objective": (
                    expression
                ),

                "dimensions": (
                    dimensions
                ),

                "bounds": (
                    cleaned_bounds
                ),

                "best_position": (
                    best_position
                ),

                "best_score": float(
                    result[
                        "best_score"
                    ]
                ),

                "strategy_history": (
                    result[
                        "strategy_history"
                    ]
                ),

                "stage_history": (
                    result[
                        "stage_history"
                    ]
                ),

                "convergence_history": (
                    result[
                        "convergence_history"
                    ]
                ),

                "recommendation": (
                    result.get(
                        "recommendation",
                        {},
                    )
                ),
            }
        )

    # ======================================================
    # KNOWN ERROR
    # ======================================================

    except RuntimeError as exc:

        print()
        print("=" * 70)
        print(
            "                 OPTIMIZATION ERROR"
        )
        print("=" * 70)

        print(
            f"Error type: "
            f"{type(exc).__name__}"
        )

        print(
            f"Error: {exc}"
        )

        print("=" * 70)

        return jsonify(
            {
                "success": False,
                "error": str(exc),
                "error_type": (
                    type(exc).__name__
                ),
            }
        ), 500

    # ======================================================
    # VALIDATION ERROR
    # ======================================================

    except ValueError as exc:

        return jsonify(
            {
                "success": False,
                "error": str(exc),
                "error_type": "ValueError",
            }
        ), 400

    # ======================================================
    # UNEXPECTED ERROR
    # ======================================================

    except Exception as exc:

        print()
        print("=" * 70)
        print(
            "              UNEXPECTED API ERROR"
        )
        print("=" * 70)

        print(
            f"Error type: "
            f"{type(exc).__name__}"
        )

        print(
            f"Error: {exc}"
        )

        print("=" * 70)

        return jsonify(
            {
                "success": False,
                "error": str(exc),
                "error_type": (
                    type(exc).__name__
                ),
            }
        ), 500


# ==========================================================
# START SERVER
# ==========================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print(
        "                 OPTIAGENT API"
    )
    print("=" * 60)

    print()

    print(
        "Server: http://127.0.0.1:5000"
    )

    print()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
    )