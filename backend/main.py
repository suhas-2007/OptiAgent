from function_parser import SafeFunction
from agent import OptimizationAgent


def get_integer(prompt):

    while True:

        try:

            value = int(
                input(prompt)
            )

            if value < 1:

                print(
                    "Enter a number greater than 0."
                )

                continue

            return value

        except ValueError:

            print(
                "Enter a valid integer."
            )


def get_float(prompt):

    while True:

        try:

            return float(
                input(prompt)
            )

        except ValueError:

            print(
                "Enter a valid number."
            )


def main():

    print()
    print("=" * 60)
    print("                    OPTIAGENT")
    print("       Autonomous Dynamic Optimization")
    print("=" * 60)

    # ==================================================
    # OBJECTIVE FUNCTION
    # ==================================================

    print()
    print(
        "Enter your objective function."
    )

    print(
        "Use variables x1, x2, x3, ..."
    )

    print()
    print(
        "Examples:"
    )

    print(
        "  x1**2 + x2**2"
    )

    print(
        "  (x1-3)**2 + (x2+2)**2"
    )

    print(
        "  sin(x1)**2 + cos(x2)**2"
    )

    print()

    expression = input(
        "Objective function: "
    ).strip()

    if not expression:

        print(
            "Function cannot be empty."
        )

        return

    # ==================================================
    # DIMENSIONS
    # ==================================================

    print()

    dimensions = get_integer(
        "Number of dimensions: "
    )

    # ==================================================
    # FUNCTION VALIDATION
    # ==================================================

    try:

        objective_function = SafeFunction(
            expression
        )

        test_point = [
            0.0
            for _ in range(dimensions)
        ]

        objective_function(
            test_point
        )

    except Exception as error:

        print()
        print(
            "Invalid objective function:"
        )

        print(error)

        return

    # ==================================================
    # BOUNDS
    # ==================================================

    print()
    print(
        "Enter bounds for each variable."
    )

    bounds = []

    for i in range(dimensions):

        print()

        lower = get_float(
            f"x{i + 1} lower bound: "
        )

        upper = get_float(
            f"x{i + 1} upper bound: "
        )

        if lower >= upper:

            print(
                "Lower bound must be smaller "
                "than upper bound."
            )

            return

        bounds.append(
            (lower, upper)
        )

    # ==================================================
    # CREATE AGENT
    # ==================================================

    print()
    print(
        "Starting OptiAgent..."
    )

    agent = OptimizationAgent(
        objective_function=objective_function,
        dimensions=dimensions,
        bounds=bounds,
        expression=expression,
        max_stages=5,
        patience=3,
    )

    # ==================================================
    # OPTIMIZE
    # ==================================================

    result = agent.optimize()

    # ==================================================
    # FINAL OUTPUT
    # ==================================================

    print()
    print("=" * 60)
    print("                  COMPLETED")
    print("=" * 60)

    print()

    print(
        f"Function: {expression}"
    )

    print(
        f"Best position: "
        f"{result['best_position']}"
    )

    print(
        f"Best score: "
        f"{result['best_score']}"
    )

    print()

    print(
        "Optimization stages:"
    )

    for stage in result[
        "stage_history"
    ]:

        print(
            f"  Stage {stage['stage']}: "
            f"{stage['strategy']} -> "
            f"{stage['global_best_score']}"
        )

    print()
    print(
        "OptiAgent finished successfully."
    )


if __name__ == "__main__":
    main()