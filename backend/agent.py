"""Multi-stage search with bounded work and independent score validation."""
import math
import os
import sys
import time
import numpy as np

_backend_dir = os.path.dirname(os.path.abspath(__file__))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)
from monitor import ConvergenceMonitor
from optimizer_registry import OptimizerRegistry
from ai_planner import AIPlanner
from solution_validator import SolutionValidator
from search import SearchContext, SearchLimit, additive_components, separable_search


class OptimizationAgent:
    def __init__(self, objective_function, dimensions, bounds, expression,
                 max_stages=5, patience=3, max_evaluations=None,
                 time_limit_seconds=45, random_seed=None):
        self.dimensions = int(dimensions)
        if not 1 <= self.dimensions <= 100:
            raise ValueError('Dimensions must be between 1 and 100.')
        self.bounds = np.asarray(bounds, dtype=float)
        if (self.bounds.shape != (self.dimensions, 2) or not np.all(np.isfinite(self.bounds))
                or np.any(self.bounds[:, 0] >= self.bounds[:, 1])):
            raise ValueError('Provide one finite, increasing bound pair per dimension.')
        self.objective_function, self.expression = objective_function, expression
        self.max_stages, self.patience = max_stages, patience
        self.max_evaluations = max_evaluations if max_evaluations is not None else min(200000, max(10000, 2000*self.dimensions))
        if not 100 <= self.max_evaluations <= 500000:
            raise ValueError('max_evaluations must be between 100 and 500000.')
        if not math.isfinite(time_limit_seconds) or not 0 < time_limit_seconds <= 90:
            raise ValueError('time_limit_seconds must be greater than 0 and at most 90.')
        self.time_limit_seconds = time_limit_seconds
        self.rng = np.random.default_rng(random_seed)
        self.registry = OptimizerRegistry()
        self.algorithms = self.registry.available_algorithms()
        self.planner = AIPlanner(self.algorithms)
        self.monitor = ConvergenceMonitor(patience=patience)
        self.validator = SolutionValidator(objective_function, self.dimensions, self.bounds)
        self.best_position, self.best_score = None, math.inf
        self.current_strategy, self.last_recommendation = None, None
        self.strategy_history, self.stage_history, self.convergence_history = [], [], []
        self.restart, self.context = False, None

    def _ask_gemini(self, status, validation=None, avoid_strategy=None):
        if self.context is not None:
            self.context.check()
            self.planner.deadline = self.context.started + self.context.time_limit
        rec = self.planner.recommend_strategy(
            problem_description=f'Minimize the user-defined objective function:\n{self.expression}',
            dimensions=self.dimensions, bounds=self.bounds.tolist(),
            current_strategy=self.current_strategy, optimization_status=status,
            best_score=self.best_score, validation=validation, avoid_strategy=avoid_strategy)
        selected = rec.get('recommended_strategy')
        if selected not in self.algorithms:
            raise RuntimeError('Planner selected an unavailable optimization strategy.')
        if selected == avoid_strategy and len(self.algorithms) > 1:
            selected = next(name for name in self.algorithms if name != avoid_strategy)
            rec = dict(rec, recommended_strategy=selected, reason=f'Switched from {avoid_strategy} after stagnation.')
        self.current_strategy, self.last_recommendation = selected, rec
        return rec

    def _run_optimizer(self):
        seed = int(self.rng.integers(0, 2**31-1))
        optimizer = self.registry.create(self.current_strategy, self.context,
                                         self.dimensions, self.bounds, seed=seed)
        if self.best_position is not None and not self.restart:
            optimizer.initial_position = self.best_position.copy()
        elif self.restart:
            optimizer.initial_position = self.rng.uniform(self.bounds[:, 0], self.bounds[:, 1])
        result = optimizer.optimize()
        if not isinstance(result, dict):
            raise RuntimeError('Optimizer returned an invalid result.')
        return optimizer, result

    def _record_stage(self, stage, history, previous_best):
        running = previous_best
        for iteration, score in enumerate(history, 1):
            if math.isfinite(float(score)):
                running = min(running, float(score))
                self.convergence_history.append({'stage':stage, 'algorithm':self.current_strategy,
                                                 'iteration':iteration, 'score':running})
        self.best_position = self.context.best_position.copy() if self.context.best_position is not None else None
        self.best_score = self.context.best_score
        if self.best_position is None:
            return None
        checked = self.validator.validate_result({'best_position':self.best_position,
                                                  'best_score':self.best_score, 'history':[self.best_score]})
        if not checked['valid'] or not checked.get('score_consistent', False):
            raise RuntimeError('Best candidate failed independent validation.')
        self.best_score = checked['actual_score']
        progress = self.monitor.analyze_history(history)
        improved = previous_best-self.best_score > 1e-9*max(1, abs(self.best_score))
        self.strategy_history.append(self.current_strategy)
        self.stage_history.append({'stage':stage, 'strategy':self.current_strategy,
            'stage_best_score':self.best_score, 'verified_score':self.best_score,
            'global_best_score':self.best_score, 'improved':bool(improved),
            'trend':progress['trend'], 'stagnating':progress['stagnating'],
            'reliable':bool(checked['reliable']), 'restarted':self.restart,
            'evaluations':self.context.evaluations})
        if not self.convergence_history or self.convergence_history[-1]['score'] != self.best_score:
            self.convergence_history.append({'stage':stage, 'algorithm':self.current_strategy,
                                             'iteration':len(history)+1, 'score':self.best_score})
        return progress

    def optimize(self):
        self.context = SearchContext(self.objective_function, self.bounds,
                                     self.max_evaluations, self.time_limit_seconds)
        components = additive_components(self.objective_function, self.dimensions)
        termination = 'stage_limit'
        if components is not None:
            self.current_strategy = 'Separable bounded search'
            self.last_recommendation = {
                'success':True, 'recommended_strategy':self.current_strategy,
                'confidence':None, 'exploration_level':'high', 'source':'structural_analysis',
                'reason':'The parsed expression is additively separable. Search each bounded coordinate '
                         'on a grid, refine sampled basins, and re-evaluate the complete objective. '
                         'Finite sampling does not certify the global minimum.'}
            try:
                history = separable_search(self.context, components,
                                          self.rng.uniform(self.bounds[:, 0], self.bounds[:, 1]))
                termination = 'separable_search_complete'
            except SearchLimit as limit:
                termination, history = str(limit), self.context.improvements.copy()
            self._record_stage(1, history, math.inf)
        else:
            try:
                self.context((self.bounds[:, 0]+self.bounds[:, 1])/2)
                self.context(self.rng.uniform(self.bounds[:, 0], self.bounds[:, 1]))
                self._ask_gemini('initial')
                self.context.check()
                for stage in range(1, self.max_stages+1):
                    previous, start = self.context.best_score, len(self.context.improvements)
                    try:
                        _, result = self._run_optimizer()
                        history = result.get('history', self.context.improvements[start:])
                    except SearchLimit as limit:
                        termination, history = str(limit), self.context.improvements[start:]
                        self._record_stage(stage, history, previous)
                        break
                    progress = self._record_stage(stage, history, previous)
                    if stage == self.max_stages:
                        break
                    self.context.check()
                    self.restart = (progress is None or progress['stagnating'] or
                                    previous-self.best_score <= 1e-9*max(1, abs(self.best_score)))
                    if self.restart:
                        self._ask_gemini('stagnating', avoid_strategy=self.current_strategy)
            except SearchLimit as limit:
                termination = str(limit)
                if not self.stage_history and self.context.best_position is not None:
                    self._record_stage(1, self.context.improvements, math.inf)
        if self.context.best_position is None:
            raise RuntimeError('No finite feasible solution was found within the search budget.')
        self.best_position = self.context.best_position.copy()
        self.best_score = float(self.objective_function(self.best_position))
        return {'best_position':self.best_position, 'best_score':self.best_score,
            'strategy_history':self.strategy_history, 'stage_history':self.stage_history,
            'convergence_history':self.convergence_history, 'recommendation':self.last_recommendation or {},
            'termination_reason':termination, 'global_optimum_certified':False,
            'evaluations':self.context.evaluations, 'objective_evaluations':self.context.objective_evaluations,
            'component_evaluations':self.context.component_evaluations,
            'elapsed_seconds':time.monotonic()-self.context.started,
            'warnings':['Numerical search returned the best verified candidate; global optimality is not certified.']}
