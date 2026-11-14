"""Run a paired, seeded optimizer comparison and write run and summary CSVs."""
import argparse
import contextlib
import csv
import itertools
import os
from pathlib import Path
import platform
import statistics
import time

# Keep the comparison single-threaded even on hosts with large BLAS pools.
for variable in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[variable] = '1'

import numpy as np
import scipy

from backend.agent import OptimizationAgent
from backend.benchmarks import build_benchmark
from backend.cma_es import CMAES
from backend.differential_evolution import DifferentialEvolution
from backend.function_parser import SafeFunction
from search import SearchContext, SearchLimit


PROBLEMS = ('sphere', 'rosenbrock', 'rastrigin', 'beale', 'rotated_rastrigin')
METHODS = ('adaptive_uniform', 'adaptive_diverse', 'differential_evolution', 'optiagent_cma_es')
TARGET = 1e-6


def problem(name, dimensions):
    if name != 'rotated_rastrigin':
        preset = build_benchmark(name, dimensions)
        return preset['objective'], preset['bounds']
    coordinates = [
        f'((x{i}{operator}x{i+1})/sqrt(2){shift})'
        for i in range(1, dimensions, 2)
        for operator, shift in (('-', '-0.317'), ('+', '+0.271'))
    ]
    if dimensions % 2:
        coordinates.append(f'(x{dimensions}-0.317)')
    expression = f'{10 * dimensions} + ' + ' + '.join(
        f'{coordinate}**2 - 10*cos(2*pi*{coordinate})' for coordinate in coordinates
    )
    return expression, [[-5.12, 5.12]] * dimensions


def run(name, dimensions, seed, method, budget, time_limit, stages, patience):
    expression, bounds = problem(name, dimensions)
    objective = SafeFunction(expression)
    started = time.monotonic()
    restarts = samples = 0
    if method.startswith('adaptive_'):
        agent = OptimizationAgent(
            objective, dimensions, bounds, expression, max_stages=stages, patience=patience,
            max_evaluations=budget, time_limit_seconds=time_limit, random_seed=seed,
            planner_mode='local', restart_mode=method.split('_', 1)[1],
        )
        result = agent.optimize()
        context = agent.context
        termination = result['termination_reason']
        restarts = sum(stage['restarted'] for stage in result['stage_history'])
        samples = sum(stage['restart_samples'] for stage in result['stage_history'])
        stage_count = len(result['stage_history'])
    else:
        context = SearchContext(objective, bounds, budget, time_limit)
        solver_type = DifferentialEvolution if method == 'differential_evolution' else CMAES
        solver = solver_type(context, dimensions, bounds, seed=seed, generations=budget)
        termination = 'solver_completed'
        stage_count = 1
        try:
            solver.optimize()
        except SearchLimit as limit:
            termination = str(limit)
    elapsed = time.monotonic() - started
    score = float(objective(context.best_position))
    target_call = next((count for count, value in zip(context.improvement_evaluations, context.improvements)
                        if abs(value) <= TARGET), None)
    return dict(problem=name, dimensions=dimensions, seed=seed, method=method,
                budget=budget, time_limit_seconds=time_limit, max_stages=stages,
                patience=patience, target=TARGET, score=score, error=abs(score),
                success=abs(score) <= TARGET, calls_to_target=target_call,
                objective_calls=context.objective_evaluations, component_calls=context.component_evaluations,
                total_calls=context.evaluations, seconds=round(elapsed, 6), termination=termination,
                stages=stage_count, restarts=restarts, restart_samples=samples,
                python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__)


def write_csv(path, rows):
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--dimensions', nargs='+', type=int, default=[2, 20, 100])
    parser.add_argument('--seeds', nargs='+', type=int, default=[7, 41, 87])
    parser.add_argument('--problems', nargs='+', choices=PROBLEMS, default=PROBLEMS)
    parser.add_argument('--budget', type=int, default=6000)
    parser.add_argument('--time-limit', type=float, default=60)
    parser.add_argument('--stages', type=int, default=5)
    parser.add_argument('--patience', type=int, default=1)
    options = parser.parse_args()
    if not all(2 <= n <= 100 for n in options.dimensions):
        parser.error('Study dimensions must be between 2 and 100.')
    options.output.mkdir(parents=True, exist_ok=True)
    rows = []
    with open(os.devnull, 'w') as quiet:
        for name, n, seed, method in itertools.product(
                options.problems, options.dimensions, options.seeds, METHODS):
            with contextlib.redirect_stdout(quiet):
                row = run(name, n, seed, method, options.budget, options.time_limit, options.stages, options.patience)
            rows.append(row)
            write_csv(options.output / 'runs.csv', rows)
            print(name, n, seed, method, format(row['error'], '.5g'), row['termination'], flush=True)
    summary = []
    for (name, n, method), group in itertools.groupby(
            sorted(rows, key=lambda r: (r['problem'], r['dimensions'], r['method'])),
            key=lambda r: (r['problem'], r['dimensions'], r['method'])):
        group = list(group)
        hits = [row['calls_to_target'] for row in group if row['success']]
        summary.append(dict(problem=name, dimensions=n, method=method, runs=len(group),
                            successes=len(hits), success_rate=len(hits) / len(group),
                            median_error=statistics.median(row['error'] for row in group),
                            median_calls_to_target=statistics.median(hits) if hits else None,
                            median_total_calls=statistics.median(row['total_calls'] for row in group),
                            time_limits=sum(row['termination'] == 'time_limit' for row in group),
                            median_seconds=statistics.median(row['seconds'] for row in group)))
    write_csv(options.output / 'summary.csv', summary)


if __name__ == '__main__':
    main()
