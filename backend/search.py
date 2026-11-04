"""Bounded search accounting and structural optimization of additive objectives.

No benchmark names or known minimizers are used. A finite grid plus local
refinement is a numerical search, not a certificate of global optimality.
"""
import ast
import math
import time
import numpy as np
from scipy.optimize import minimize_scalar


class SearchLimit(RuntimeError):
    pass


class SearchContext:
    def __init__(self, objective, bounds, max_evaluations, time_limit):
        self.objective = objective
        self.bounds = np.asarray(bounds, dtype=float)
        self.max_evaluations = max_evaluations
        self.time_limit = time_limit
        self.started = time.monotonic()
        self.objective_evaluations = 0
        self.component_evaluations = 0
        self.best_score = math.inf
        self.best_position = None
        self.improvements = []

    @property
    def evaluations(self):
        return self.objective_evaluations + self.component_evaluations

    def check(self):
        if time.monotonic() - self.started >= self.time_limit:
            raise SearchLimit('time_limit')
        if self.evaluations >= self.max_evaluations:
            raise SearchLimit('evaluation_limit')

    def __call__(self, position):
        self.check()
        self.objective_evaluations += 1
        position = np.asarray(position, dtype=float)
        if (position.shape != (len(self.bounds),) or not np.all(np.isfinite(position))
                or np.any(position < self.bounds[:, 0]) or np.any(position > self.bounds[:, 1])):
            return math.inf
        score = float(self.objective(position))
        if math.isfinite(score) and score < self.best_score:
            self.best_position = position.copy()
            self.best_score = score
            self.improvements.append(score)
        return score if math.isfinite(score) else math.inf

    def component(self, function, value):
        self.check()
        self.component_evaluations += 1
        result = float(function(value))
        return result if math.isfinite(result) else math.inf


def additive_components(objective, dimensions):
    """Prove syntactic additive separability, conservatively; otherwise return None.

    Distribute only constant multiplication/division over sums. Products,
    powers, and function calls involving multiple coordinates remain coupled.
    Every term is evaluated by the original safe AST interpreter.
    """
    if not hasattr(objective, 'tree') or not hasattr(objective, '_evaluate'):
        return None
    aliases = {f'x{i + 1}': i for i in range(dimensions)}
    aliases.update({name: i for i, name in enumerate(('x', 'y', 'z')) if i < dimensions})
    ignored = set(objective.ALLOWED_CONSTANTS) | set(objective.ALLOWED_FUNCTIONS)

    def dependencies(node):
        names = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)} - ignored
        if not names.issubset(aliases):
            raise ValueError('Unknown coordinate in objective')
        return {aliases[name] for name in names}

    terms = []

    def split(node, coefficient=1.0):
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub)):
            split(node.left, coefficient)
            split(node.right, coefficient * (-1 if isinstance(node.op, ast.Sub) else 1))
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            split(node.operand, coefficient * (-1 if isinstance(node.op, ast.USub) else 1))
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult) and not dependencies(node.left):
            value = float(objective._evaluate(node.left, {}))
            if not math.isfinite(value): raise ValueError('Nonfinite constant')
            split(node.right, coefficient * value)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult) and not dependencies(node.right):
            value = float(objective._evaluate(node.right, {}))
            if not math.isfinite(value): raise ValueError('Nonfinite constant')
            split(node.left, coefficient * value)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div) and not dependencies(node.right):
            value = float(objective._evaluate(node.right, {}))
            if not math.isfinite(value) or value == 0: raise ValueError('Invalid constant divisor')
            split(node.left, coefficient / value)
        else:
            used = dependencies(node)
            if len(used) > 1:
                raise ValueError('Coupled term')
            if used:
                terms.append((next(iter(used)), coefficient, node))

    try:
        split(objective.tree.body)
    except (ValueError, OverflowError, RecursionError):
        return None
    groups = [[] for _ in range(dimensions)]
    for index, coefficient, node in terms:
        groups[index].append((coefficient, node))

    def make_component(index, group):
        names = [name for name, coordinate in aliases.items() if coordinate == index]
        def component(value):
            variables = dict.fromkeys(names, value)
            return sum(coefficient * objective._evaluate(node, variables) for coefficient, node in group)
        return component
    return [make_component(i, group) if group else None for i, group in enumerate(groups)]


def separable_search(context, components, initial_position):
    """Explore every 1D interval, refine its sampled basins, then verify full f(x)."""
    position = np.asarray(initial_position, dtype=float).copy()
    history = [context(position)]
    for index, component in enumerate(components):
        if component is None:
            continue
        lower, upper = context.bounds[index]
        remaining_dimensions = max(1, sum(c is not None for c in components[index:]))
        allowance = max(0, (context.max_evaluations - context.evaluations) // remaining_dimensions - 1)
        if allowance < 8:
            raise SearchLimit('evaluation_limit')
        grid_size = min(257, max(9, allowance // 3))
        used = 0
        def evaluate(value):
            nonlocal used
            if used >= allowance:
                return math.inf
            used += 1
            return context.component(component, float(value))
        grid = np.linspace(lower, upper, grid_size)
        scores = np.array([evaluate(v) for v in grid])
        best_index = int(np.argmin(scores))
        best_x, best_score = float(grid[best_index]), float(scores[best_index])
        # Include the incumbent explicitly, preserving good prior solutions.
        incumbent_score = evaluate(position[index])
        if incumbent_score < best_score:
            best_x, best_score = position[index], incumbent_score
        basins = [j for j in range(1, grid_size - 1)
                  if scores[j] <= scores[j-1] and scores[j] <= scores[j+1] and math.isfinite(scores[j])]
        intervals = {(max(0, j-1), min(grid_size-1, j+1)) for j in basins + [best_index]}
        for left, right in sorted(intervals, key=lambda pair: min(scores[pair[0]:pair[1]+1])):
            if used >= allowance:
                break
            result = minimize_scalar(evaluate, bounds=(grid[left], grid[right]), method='bounded',
                                     options={'xatol':1e-11, 'maxiter':min(80, allowance-used)})
            if math.isfinite(result.fun) and result.fun < best_score:
                best_x, best_score = float(result.x), float(result.fun)
        # No surrogate score is reported: independently evaluate the entire expression.
        position[index] = best_x
        history.append(context(position))
    return history
