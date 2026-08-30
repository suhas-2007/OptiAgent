import ast
import math


class SafeFunction:

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

        self.expression = expression

        # Parse expression without executing it.
        self.tree = ast.parse(
            expression,
            mode="eval",
        )

    def _evaluate(self, node, variables):

        if isinstance(node, ast.Expression):
            return self._evaluate(
                node.body,
                variables,
            )

        # Numbers
        if isinstance(node, ast.Constant):

            if isinstance(node.value, (int, float)):
                return float(node.value)

            raise ValueError(
                "Only numeric constants are allowed."
            )

        # Variables such as x1, x2, x3...
        if isinstance(node, ast.Name):

            if node.id in variables:
                return variables[node.id]

            if node.id in self.ALLOWED_CONSTANTS:
                return self.ALLOWED_CONSTANTS[node.id]

            raise ValueError(
                f"Unknown variable or constant: {node.id}"
            )

        # Operators
        if isinstance(node, ast.BinOp):

            if not isinstance(
                node.op,
                self.ALLOWED_OPERATORS,
            ):
                raise ValueError(
                    "Unsupported operator."
                )

            left = self._evaluate(
                node.left,
                variables,
            )

            right = self._evaluate(
                node.right,
                variables,
            )

            if isinstance(node.op, ast.Add):
                return left + right

            if isinstance(node.op, ast.Sub):
                return left - right

            if isinstance(node.op, ast.Mult):
                return left * right

            if isinstance(node.op, ast.Div):
                return left / right

            if isinstance(node.op, ast.Pow):
                return left ** right

            if isinstance(node.op, ast.Mod):
                return left % right

        # Unary + / -
        if isinstance(node, ast.UnaryOp):

            value = self._evaluate(
                node.operand,
                variables,
            )

            if isinstance(node.op, ast.USub):
                return -value

            if isinstance(node.op, ast.UAdd):
                return value

        # Mathematical functions
        if isinstance(node, ast.Call):

            if not isinstance(
                node.func,
                ast.Name,
            ):
                raise ValueError(
                    "Only approved mathematical functions are allowed."
                )

            function_name = node.func.id

            if function_name not in self.ALLOWED_FUNCTIONS:
                raise ValueError(
                    f"Function '{function_name}' is not allowed."
                )

            if len(node.args) != 1:
                raise ValueError(
                    f"{function_name}() accepts one argument."
                )

            argument = self._evaluate(
                node.args[0],
                variables,
            )

            return self.ALLOWED_FUNCTIONS[
                function_name
            ](argument)

        raise ValueError(
            "Unsupported expression."
        )

    def __call__(self, x):

        variables = {
            f"x{i + 1}": float(value)
            for i, value in enumerate(x)
        }

        return float(
            self._evaluate(
                self.tree,
                variables,
            )
        )