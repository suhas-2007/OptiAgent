import ast
import math
import numpy as np


class SafeFunction:
    """
    Safely parses and evaluates mathematical expressions without eval().
    Uses Python's AST module to enforce a strict whitelist of operators,
    functions, constants, and variables.
    """

    ALLOWED_FUNCTIONS = {
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "exp": math.exp,
        "sqrt": math.sqrt,
        "log": math.log,
        "abs": abs,
    }

    ALLOWED_CONSTANTS = {
        "pi": math.pi,
        "e": math.e,
        "PI": math.pi,
        "E": math.e,
        "pi_val": math.pi,
    }

    ALLOWED_OPERATORS = (
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Pow,
        ast.USub,
        ast.UAdd,
        ast.Mod,
    )

    def __init__(self, expression):
        if not expression or not str(expression).strip():
            raise ValueError("Objective function expression cannot be empty.")

        cleaned = str(expression).strip().replace("^", "**")
        self.expression = cleaned

        try:
            # Parse expression without executing it
            self.tree = ast.parse(cleaned, mode="eval")
        except SyntaxError as exc:
            raise ValueError(f"Invalid mathematical expression syntax: {exc}") from exc

    def _evaluate(self, node, variables):
        if isinstance(node, ast.Expression):
            return self._evaluate(node.body, variables)

        # Numbers
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float, np.number)):
                return float(node.value)
            raise ValueError("Only numeric constants are allowed.")

        # Variables such as x1, x2, x3... or x, y, z
        if isinstance(node, ast.Name):
            if node.id in variables:
                return variables[node.id]
            if node.id in self.ALLOWED_CONSTANTS:
                return self.ALLOWED_CONSTANTS[node.id]
            raise ValueError(f"Unknown variable or constant: {node.id}")

        # Binary operators
        if isinstance(node, ast.BinOp):
            if not isinstance(node.op, self.ALLOWED_OPERATORS):
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")

            left = self._evaluate(node.left, variables)
            right = self._evaluate(node.right, variables)

            if isinstance(node.op, ast.Add):
                return left + right

            if isinstance(node.op, ast.Sub):
                return left - right

            if isinstance(node.op, ast.Mult):
                return left * right

            if isinstance(node.op, ast.Div):
                if right == 0.0:
                    return float("inf")
                try:
                    return left / right
                except (ZeroDivisionError, OverflowError):
                    return float("inf")

            if isinstance(node.op, ast.Pow):
                try:
                    # Prevent unbounded powers from hanging the process
                    if abs(left) > 1e12 and right > 100:
                        return float("inf")
                    return left ** right
                except (OverflowError, ZeroDivisionError, ValueError):
                    return float("inf")

            if isinstance(node.op, ast.Mod):
                if right == 0.0:
                    return float("inf")
                return left % right

        # Unary operators (+ / -)
        if isinstance(node, ast.UnaryOp):
            value = self._evaluate(node.operand, variables)
            if isinstance(node.op, ast.USub):
                return -value
            if isinstance(node.op, ast.UAdd):
                return value
            raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")

        # Approved mathematical functions
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only approved mathematical functions are allowed.")

            function_name = node.func.id
            if function_name not in self.ALLOWED_FUNCTIONS:
                raise ValueError(f"Function '{function_name}' is not allowed.")

            if len(node.args) != 1:
                raise ValueError(f"{function_name}() accepts exactly one argument.")
            if node.keywords:
                raise ValueError('Keyword arguments are not allowed in mathematical functions.')

            argument = self._evaluate(node.args[0], variables)

            try:
                # Safe domain handling for numerical search
                if function_name == "log" and argument <= 0:
                    return float("inf")
                if function_name == "sqrt" and argument < 0:
                    return float("inf")

                func = self.ALLOWED_FUNCTIONS[function_name]
                val = func(argument)
                return float(val)
            except (ValueError, OverflowError, ZeroDivisionError):
                return float("inf")

        raise ValueError(f"Unsupported syntax construct: {type(node).__name__}")

    def __call__(self, x):
        # Normalize scalar or array input to list
        if isinstance(x, (int, float, np.floating, np.integer)):
            x_list = [float(x)]
        elif hasattr(x, "flatten"):
            x_list = [float(val) for val in x.flatten()]
        elif isinstance(x, (list, tuple)):
            x_list = [float(val) for val in x]
        else:
            try:
                x_list = [float(val) for val in list(x)]
            except Exception as exc:
                raise ValueError(f"Cannot evaluate objective on input {x}: {exc}") from exc

        variables = {
            f"x{i + 1}": x_list[i]
            for i in range(len(x_list))
        }

        # Convenient aliases for 1D, 2D, 3D
        named_aliases = ["x", "y", "z"]
        for i, name in enumerate(named_aliases):
            if i < len(x_list):
                variables[name] = x_list[i]

        try:
            result = float(self._evaluate(self.tree, variables))
            return result
        except (OverflowError, ZeroDivisionError):
            return float("inf")
