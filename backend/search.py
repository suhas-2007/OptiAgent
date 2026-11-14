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


class StageBudgetReached(RuntimeError):
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
        self.improvement_evaluations = []
        self.stage_end = max_evaluations
        self.stage_best_score = math.inf

    def begin_stage(self, stages_left):
        self.stage_end = self.evaluations + (self.max_evaluations - self.evaluations) // stages_left
        self.stage_best_score = math.inf

    @property
    def evaluations(self):
        return self.objective_evaluations + self.component_evaluations

    def check(self):
        if time.monotonic() - self.started >= self.time_limit:
            raise SearchLimit('time_limit')
        if self.evaluations >= self.max_evaluations:
            raise SearchLimit('evaluation_limit')
        if self.evaluations >= self.stage_end:
            raise StageBudgetReached()

    def __call__(self, position):
        self.check()
        self.objective_evaluations += 1
        position = np.asarray(position, dtype=float)
        if (position.shape != (len(self.bounds),) or not np.all(np.isfinite(position))
                or np.any(position < self.bounds[:, 0]) or np.any(position > self.bounds[:, 1])):
            return math.inf
        score = float(self.objective(position))
        if math.isfinite(score):
            self.stage_best_score = min(self.stage_best_score, score)
        if math.isfinite(score) and score < self.best_score:
            self.best_position = position.copy()
            self.best_score = score
            self.improvements.append(score)
            self.improvement_evaluations.append(self.evaluations)
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


def separable_search(context, components, initial_position, rng=None, offset=0):
    """Explore every 1D interval, refine its sampled basins, then verify full f(x)."""
    position = np.asarray(initial_position, dtype=float).copy()
    history = [context(position)]
    indices = [index for index, component in enumerate(components) if component is not None]
    if indices:
        offset %= len(indices)
        indices = indices[offset:] + indices[:offset]
    for count, index in enumerate(indices):
        component = components[index]
        lower, upper = context.bounds[index]
        remaining = context.stage_end - context.evaluations
        if remaining < 5:
            if remaining:
                position[index] = lower if position[index] > lower else upper
                history.append(context(position))
            break
        allowance = max(4, remaining // (len(indices) - count) - 1)
        grid_size = min(257, max(3, allowance // 3))
        if grid_size % 2 == 0:
            grid_size -= 1
        used = 0
        def evaluate(value):
            nonlocal used
            if used >= allowance:
                return math.inf
            used += 1
            return context.component(component, float(value))
        grid = np.linspace(lower, upper, grid_size)
        if rng is not None and grid_size > 3:
            spacing = (upper - lower) / (grid_size - 1)
            grid[1:-1] += rng.uniform(-0.4, 0.4, grid_size - 2) * spacing
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
