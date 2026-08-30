import sys
import os

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

from backend.function_parser import SafeFunction


def test_basic_function():
    function = SafeFunction("x1**2 + x2**2")

    result = function([3, 4])

    assert result == 25.0


def test_trigonometric_function():
    function = SafeFunction(
        "sin(x1)**2 + cos(x2)**2"
    )

    result = function([0, 0])

    assert abs(result - 1.0) < 1e-10