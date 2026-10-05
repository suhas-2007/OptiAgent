import os
import base64
import json
import re
from dotenv import load_dotenv
load_dotenv()

from flask import (
    Flask,
    request,
    jsonify,
)
from flask_cors import CORS
from function_parser import SafeFunction
from agent import OptimizationAgent
from google import genai
from google.genai import types

# flask app

app = Flask(__name__)
CORS(app)

# home

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


# health

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


# optimize

@app.route(
    "/optimize",
    methods=["POST"],
)
def optimize():

    try:

        # request data

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

        # objective

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

        # dimensions

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

        # bounds

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

        # safe function

        objective_function = (
            SafeFunction(
                expression
            )
        )

        # agent

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

        # run optimization

        result = agent.optimize()
        print()
        print(">>> RESULT KEYS:")
        print(result.keys())

        print()
        print(">>> GEMINI RECOMMENDATION:")
        print(result.get("recommendation"))
        # convert numpy values

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

        # response

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

    # known error

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

    # validation error

    except ValueError as exc:

        return jsonify(
            {
                "success": False,
                "error": str(exc),
                "error_type": "ValueError",
            }
        ), 400

    # unexpected error

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


# benchmark presets & extract problem

PRESET_BENCHMARKS = {
    "nelder mead": {
        "name": "Rosenbrock Function (Nelder-Mead Benchmark)",
        "objective": "(1 - x1)**2 + 100 * (x2 - x1**2)**2",
        "dimensions": 2,
        "bounds": [[-5.0, 5.0], [-5.0, 5.0]],
        "explanation": "The classic Rosenbrock banana valley function, famously used to benchmark the Nelder-Mead simplex method. It has a narrow, curved parabolic valley leading to the global minimum at (1, 1).",
    },
    "rosenbrock": {
        "name": "Rosenbrock Function",
        "objective": "(1 - x1)**2 + 100 * (x2 - x1**2)**2",
        "dimensions": 2,
        "bounds": [[-5.0, 5.0], [-5.0, 5.0]],
        "explanation": "A non-convex valley function where finding the valley is easy, but converging along the narrow curve to (1, 1) is difficult.",
    },
    "sphere": {
        "name": "Sphere Function",
        "objective": "x1**2 + x2**2",
        "dimensions": 2,
        "bounds": [[-10.0, 10.0], [-10.0, 10.0]],
        "explanation": "A smooth, convex quadratic benchmark with global minimum 0 at (0, 0).",
    },
    "ackley": {
        "name": "Ackley Function",
        "objective": "-20 * exp(-0.2 * sqrt(0.5 * (x1**2 + x2**2))) - exp(0.5 * (cos(2 * pi * x1) + cos(2 * pi * x2))) + e + 20",
        "dimensions": 2,
        "bounds": [[-5.0, 5.0], [-5.0, 5.0]],
        "explanation": "A multimodal test function with nearly flat outer regions and a deep central hole surrounded by numerous local minima.",
    },
    "rastrigin": {
        "name": "Rastrigin Function",
        "objective": "20 + x1**2 - 10 * cos(2 * pi * x1) + x2**2 - 10 * cos(2 * pi * x2)",
        "dimensions": 2,
        "bounds": [[-5.12, 5.12], [-5.12, 5.12]],
        "explanation": "A highly multimodal function with a large number of regularly distributed local minima.",
    },
    "beale": {
        "name": "Beale Function",
        "objective": "(1.5 - x1 + x1*x2)**2 + (2.25 - x1 + x1*x2**2)**2 + (2.625 - x1 + x1*x2**3)**2",
        "dimensions": 2,
        "bounds": [[-4.5, 4.5], [-4.5, 4.5]],
        "explanation": "A multimodal 2D benchmark with sharp peaks near the corners and minimum at (3, 0.5).",
    },
    "booth": {
        "name": "Booth Function",
        "objective": "(x1 + 2*x2 - 7)**2 + (2*x1 + x2 - 5)**2",
        "dimensions": 2,
        "bounds": [[-10.0, 10.0], [-10.0, 10.0]],
        "explanation": "A quadratic plate function with global minimum 0 at (1, 3).",
    },
    "himmelblau": {
        "name": "Himmelblau Function",
        "objective": "(x1**2 + x2 - 11)**2 + (x1 + x2**2 - 7)**2",
        "dimensions": 2,
        "bounds": [[-5.0, 5.0], [-5.0, 5.0]],
        "explanation": "A 2D benchmark with 4 identical global minima, used to test multimodal search capabilities.",
    },
    "shifted": {
        "name": "Shifted Quadratic Function",
        "objective": "(x1 - 3)**2 + (x2 + 2)**2",
        "dimensions": 2,
        "bounds": [[-10.0, 10.0], [-10.0, 10.0]],
        "explanation": "A simple quadratic function shifted away from the origin, with minimum 0 at (3, -2).",
    },
    "trigonometric": {
        "name": "Trigonometric Function",
        "objective": "sin(x1)**2 + cos(x2)**2",
        "dimensions": 2,
        "bounds": [[-5.0, 5.0], [-5.0, 5.0]],
        "explanation": "An oscillating periodic function with infinite periodic local minima.",
    },
}

def _get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_BACKUP_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        print(f"[API] Failed to initialize Gemini client: {e}")
        return None

@app.route("/api/extract-problem", methods=["POST"])
def extract_problem():
    try:
        data = request.get_json(silent=True) or {}
        text = str(data.get("text", "")).strip()
        image_data = data.get("image")

        # 1. Quick check against preset benchmarks if text is given
        if text:
            lower_text = text.lower()
            for key, preset in PRESET_BENCHMARKS.items():
                if key in lower_text:
                    return jsonify({
                        "success": True,
                        "source": "preset",
                        "name": preset["name"],
                        "objective": preset["objective"],
                        "dimensions": preset["dimensions"],
                        "bounds": preset["bounds"],
                        "explanation": preset["explanation"]
                    })

        # 2. Try Gemini multimodal if image or freeform text is provided
        client = _get_gemini_client()
        if client and (text or image_data):
            contents = []

            if image_data:
                # parse base64 image (handles data:image/png;base64,... header)
                if "," in image_data:
                    header, encoded = image_data.split(",", 1)
                    mime_match = re.search(r"data:([^;]+);", header)
                    mime_type = mime_match.group(1) if mime_match else "image/png"
                else:
                    encoded = image_data
                    mime_type = "image/png"

                raw_bytes = base64.b64decode(encoded)
                contents.append(types.Part.from_bytes(data=raw_bytes, mime_type=mime_type))

            prompt = """You are a mathematical optimization parser.
Analyze this image or question. Extract the objective function to minimize, its dimensions, and reasonable search bounds.
Objective function MUST be in valid Python math syntax using variables x1, x2, x3... (or x, y).
Use ** for powers (e.g. x1**2).
Allowed math functions: sin, cos, tan, exp, sqrt, log, abs.
Allowed constants: pi, e.

Respond ONLY with a valid JSON object (no markdown code blocks, just raw JSON) with exact keys:
{
  "name": "Function Name or Problem Title",
  "objective": "Python expression like (1-x1)**2 + 100*(x2-x1**2)**2",
  "dimensions": 2,
  "bounds": [[-5.0, 5.0], [-5.0, 5.0]],
  "explanation": "Short 1-2 sentence description of the function and behavior"
}"""
            if text:
                prompt += f"\nUser Question / Query: {text}"
            contents.append(prompt)

            model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
            response = client.models.generate_content(
                model=model,
                contents=contents
            )

            raw_text = response.text or ""
            # strip markdown code blocks if any
            cleaned_json = re.sub(r"^```json\s*", "", raw_text.strip(), flags=re.MULTILINE)
            cleaned_json = re.sub(r"^```\s*", "", cleaned_json.strip(), flags=re.MULTILINE)
            cleaned_json = cleaned_json.strip("` \n")

            parsed = json.loads(cleaned_json)
            obj_expr = parsed.get("objective", "").strip()
            dims = int(parsed.get("dimensions", 2))
            bounds = parsed.get("bounds", [[-10.0, 10.0]] * dims)

            # validate with SafeFunction
            SafeFunction(obj_expr)([0.0] * dims)

            return jsonify({
                "success": True,
                "source": "gemini",
                "name": parsed.get("name", "Extracted Optimization Problem"),
                "objective": obj_expr,
                "dimensions": dims,
                "bounds": bounds,
                "explanation": parsed.get("explanation", "Extracted from question.")
            })

        # 3. Fallback: if user typed something like a simple equation
        if text:
            # check if text looks like a formula e.g. x1**2 + x2**2 or x^2 + y^2
            candidate_expr = text.replace("^", "**")
            try:
                SafeFunction(candidate_expr)([0.0, 0.0])
                return jsonify({
                    "success": True,
                    "source": "direct_formula",
                    "name": "Custom Objective Function",
                    "objective": candidate_expr,
                    "dimensions": 2,
                    "bounds": [[-10.0, 10.0], [-10.0, 10.0]],
                    "explanation": "Direct mathematical objective entered by user."
                })
            except Exception:
                pass

        return jsonify({
            "success": False,
            "error": "Could not identify optimization problem. Please provide a clear function name, formula, or screenshot."
        }), 400

    except Exception as e:
        print(f"[API] Error in /api/extract-problem: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/ask-info", methods=["POST"])
def ask_info():
    try:
        data = request.get_json(silent=True) or {}
        question = str(data.get("question", "")).strip()
        objective = data.get("objective", "")
        current_strategy = data.get("current_strategy", "")
        best_score = data.get("best_score")
        best_position = data.get("best_position")

        if not question:
            return jsonify({
                "success": False,
                "error": "Missing question."
            }), 400

        # Try Gemini first
        client = _get_gemini_client()
        if client:
            try:
                prompt = f"""You are a helpful mathematical optimization tutor for OptiAgent.
Context:
- Objective Function: {objective or 'Not specified'}
- Current / Selected Optimizer: {current_strategy or 'None'}
- Best Score Found: {best_score if best_score is not None else 'None'}
- Best Position: {best_position if best_position is not None else 'None'}

User Question: {question}

Explain clearly, accurately, and intuitively in 2-3 concise paragraphs.
Focus on how the algorithm or function behaves, its convergence properties, landscape challenges (valleys, local minima, saddle points), and practical intuition."""

                model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )
                if response.text:
                    return jsonify({
                        "success": True,
                        "source": "gemini",
                        "answer": response.text.strip()
                    })
            except Exception as e:
                print(f"[API] Gemini ask-info failed: {e}")

        # Local intelligent explanation fallback
        q_lower = question.lower()
        if "nelder" in q_lower or "simplex" in q_lower:
            ans = ("Nelder-Mead is a heuristic search method based on a simplex of N+1 vertices in N dimensions. "
                   "It moves downhill by reflecting the worst point through the centroid of the remaining points, "
                   "expanding if the reflection is very good, or contracting/shrinking if no improvement is found. "
                   "It works without derivative calculations (gradients) and is particularly famous for navigating "
                   "curved valleys like the Rosenbrock function, though it can stall on flat plateaus or get trapped in local minima.")
        elif "pso" in q_lower or "swarm" in q_lower:
            ans = ("Particle Swarm Optimization (PSO) simulates a flock of birds or school of fish. "
                   "Each particle has a position and velocity, and is pulled toward both its own personal best position "
                   "and the entire swarm's global best position. This makes PSO great at exploring multimodal landscapes "
                   "while balancing exploration (inertia) and exploitation (social attraction).")
        elif "cma" in q_lower:
            ans = ("CMA-ES (Covariance Matrix Adaptation Evolution Strategy) continuously adapts a multivariate Gaussian "
                   "sampling distribution. It estimates second-order curvature (similar to the inverse Hessian matrix) "
                   "without computing derivatives, making it state-of-the-art on ill-conditioned, non-separable continuous problems.")
        elif "genetic" in q_lower or "ga" in q_lower:
            ans = ("Genetic Algorithm uses evolutionary principles: selection, crossover, and mutation over a population. "
                   "It maintains diversity across wide search spaces, preventing premature convergence into local minima, "
                   "though convergence near the exact minimum can be slower compared to local search.")
        elif "annealing" in q_lower or "sa" in q_lower:
            ans = ("Simulated Annealing models the thermodynamic cooling of heated metals. "
                   "At high temperatures, it frequently accepts worse solutions to climb out of local minima. "
                   "As temperature cools, it becomes increasingly greedy, settling into the deepest basin found.")
        elif "climbing" in q_lower:
            ans = ("Hill Climbing is an iterative local search algorithm that samples neighbors and only moves if a candidate "
                   "is strictly better. While very fast on smooth unimodal functions, it can get permanently trapped in the first local minimum it encounters.")
        elif "rosenbrock" in q_lower or "banana" in q_lower:
            ans = ("The Rosenbrock function has a parabolic valley along x2 = x1^2. While finding the valley is easy, "
                   "converging along its shallow bottom toward the global minimum at (1, 1) requires algorithms to take small, adaptive steps. "
                   "This is why gradient-free methods like Nelder-Mead and CMA-ES are frequently benchmarked on it.")
        elif "ackley" in q_lower or "rastrigin" in q_lower:
            ans = ("This is a multimodal benchmark designed to trap optimizers in local minima. "
                   "It has high-frequency cosine ripples that create hundreds of deceptive basins. "
                   "Population-based methods like Differential Evolution and PSO perform best here because individual local search easily gets trapped.")
        else:
            ans = (f"In optimization, algorithm behavior depends on the interplay between landscape topology and search operators. "
                   f"For objective '{objective or 'f(x)'}', the agent monitors convergence progress. If stagnation occurs, "
                   f"OptiAgent adapts hyperparameters or transitions to a complementary optimizer (e.g. from global exploration to local simplex refinement).")

        return jsonify({
            "success": True,
            "source": "local_knowledge",
            "answer": ans
        })

    except Exception as e:
        print(f"[API] Error in /api/ask-info: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500# START SERVER
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