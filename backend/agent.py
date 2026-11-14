"""Multi-stage search with bounded work and independent score validation."""
import math
import os
import sys
import time
import numpy as np
from scipy.optimize import minimize

_backend_dir = os.path.dirname(os.path.abspath(__file__))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)
from optimizer_registry import OptimizerRegistry
from ai_planner import AIPlanner
from solution_validator import SolutionValidator
from search import SearchContext, SearchLimit, StageBudgetReached, additive_components, separable_search
from differentiation import ExpressionGradient, UnsupportedGradient


class OptimizationAgent:
    def __init__(self, objective_function, dimensions, bounds, expression,
                 max_stages=5, patience=3, max_evaluations=None,
                 time_limit_seconds=45, random_seed=None, planner_mode='auto'):
        self.dimensions = int(dimensions)
        if not 1 <= self.dimensions <= 100:
            raise ValueError('Dimensions must be between 1 and 100.')
        self.bounds = np.asarray(bounds, dtype=float)
        if (self.bounds.shape != (self.dimensions, 2) or not np.all(np.isfinite(self.bounds))
                or np.any(self.bounds[:, 0] >= self.bounds[:, 1])):
            raise ValueError('Provide one finite, increasing bound pair per dimension.')
        self.objective_function, self.expression = objective_function, expression
        self.max_stages, self.patience = max_stages, patience
        if not 1 <= max_stages <= 50 or not 1 <= patience <= 50:
            raise ValueError('Stage limit and restart patience must be between 1 and 50.')
        if planner_mode not in ('auto', 'local'):
            raise ValueError('Planner must be auto or local.')
        self.planner_mode = planner_mode
        self.max_evaluations = max_evaluations if max_evaluations is not None else min(200000, max(10000, 2000*self.dimensions))
        if not 100 <= self.max_evaluations <= 500000:
            raise ValueError('max_evaluations must be between 100 and 500000.')
        if not math.isfinite(time_limit_seconds) or not 0 < time_limit_seconds <= 90:
            raise ValueError('time_limit_seconds must be greater than 0 and at most 90.')
        self.time_limit_seconds = time_limit_seconds
        self.random_seed = random_seed if random_seed is not None else int(np.random.default_rng().integers(2**31))
        self.rng = np.random.default_rng(self.random_seed)
        self.registry = OptimizerRegistry()
        self.algorithms = self.registry.available_algorithms()
        self.planner = AIPlanner(self.algorithms)
        if planner_mode == 'local':
            self.planner.gemini_available = False
        self.validator = SolutionValidator(objective_function, self.dimensions, self.bounds)
        self.best_position, self.best_score = None, math.inf
        self.current_strategy, self.last_recommendation = None, None
        self.strategy_history, self.stage_history, self.convergence_history = [], [], []
        self.restart, self.context = False, None
        try:
            self.gradient = ExpressionGradient(objective_function, self.dimensions)
        except (UnsupportedGradient, AttributeError):
            self.gradient = None

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
            rec = dict(rec, recommended_strategy=selected, source='local_override',
                       confidence=None, reason=f'Switched from {avoid_strategy} after stagnation.')
        self.current_strategy, self.last_recommendation = selected, rec
        return rec

    def _run_optimizer(self):
        # Refine a feasible start before population search. This also helps smooth
        # coupled objectives; it does not assume a benchmark's known solution.
        start = (self.context.best_position.copy() if self.context.best_position is not None
                 else (self.bounds[:, 0]+self.bounds[:, 1])/2)
        if self.restart:
            start = self.rng.uniform(self.bounds[:, 0], self.bounds[:, 1])
        allowance = max(1, min(50000, (self.context.stage_end-self.context.evaluations)//3))
        calls = 0
        class RefinementLimit(Exception):
            pass
        def refine_objective(point):
            nonlocal calls
            if calls >= allowance:
                raise RefinementLimit()
            calls += 1
            return self.context(point)
        try:
            # Use exact expression derivatives when available; retain finite
            # differences for unsupported operations or singular start points.
            jac = None
            if self.gradient is not None:
                try:
                    self.gradient(start)
                    jac = self.gradient
                except UnsupportedGradient:
                    pass
            refined = minimize(refine_objective, start, jac=jac, method='L-BFGS-B', bounds=self.bounds,
                               options={'maxiter':2000, 'ftol':1e-13, 'gtol':1e-7, 'maxls':30})
            start = refined.x
        except (RefinementLimit, UnsupportedGradient):
            start = self.context.best_position.copy() if self.context.best_position is not None else start
        seed = int(self.rng.integers(0, 2**31-1))
        optimizer = self.registry.create(self.current_strategy, self.context,
                                         self.dimensions, self.bounds, seed=seed)
        optimizer.initial_position = start.copy()
        result = optimizer.optimize()
        if not isinstance(result, dict):
            raise RuntimeError('Optimizer returned an invalid result.')
        return optimizer, result

    def _record_stage(self, stage, start, first_evaluation, previous_best, outcome, started):
        scores = self.context.improvements[start:]
        counts = self.context.improvement_evaluations[start:]
        stride = max(1, (len(scores) + 399) // 400)
        for index in range(0, len(scores), stride):
            self.convergence_history.append({'stage': stage, 'algorithm': self.current_strategy,
                                             'iteration': counts[index], 'evaluations': counts[index],
                                             'score': scores[index]})
        self.best_position = self.context.best_position.copy() if self.context.best_position is not None else None
        self.best_score = self.context.best_score
        if self.best_position is None:
            checked = {'reliable': False, 'actual_score': None}
        else:
            checked = self.validator.validate_result({'best_position': self.best_position,
                                                      'best_score': self.best_score, 'history': [self.best_score]})
            if not checked['valid'] or not checked.get('score_consistent', False):
                raise RuntimeError('Best candidate failed independent validation.')
            self.best_score = checked['actual_score']
        improved = math.isfinite(self.best_score) and previous_best-self.best_score > 1e-9*max(1, abs(self.best_score))
        self.strategy_history.append(self.current_strategy)
        self.stage_history.append({'stage':stage, 'strategy':self.current_strategy,
            'stage_best_score':self.context.stage_best_score if math.isfinite(self.context.stage_best_score) else None,
            'verified_score':checked['actual_score'], 'global_best_score':checked['actual_score'],
            'improved': improved, 'trend':'improving' if improved else 'flat', 'stagnating':not improved,
            'reliable':bool(checked['reliable']), 'restarted':self.restart,
            'recommendation':self.last_recommendation.copy(), 'outcome':outcome,
            'stage_evaluations':self.context.evaluations-first_evaluation,
            'elapsed_seconds':time.monotonic()-started, 'evaluations':self.context.evaluations})
        if self.best_position is not None:
            self.convergence_history.append({'stage':stage, 'algorithm':self.current_strategy,
                'iteration':self.context.evaluations, 'evaluations':self.context.evaluations, 'score':self.best_score})
        return improved

    def optimize(self):
        self.context = SearchContext(self.objective_function, self.bounds,
                                     self.max_evaluations, self.time_limit_seconds)
        components = additive_components(self.objective_function, self.dimensions)
        termination = 'stage_limit'
        stages_without_improvement = 0
        if components is not None:
            self.current_strategy = 'Separable bounded search'
            self.last_recommendation = {
                'success': True,
                'recommended_strategy': self.current_strategy,
                'confidence': None,
                'exploration_level': 'high',
                'source': 'structural_analysis',
                'reason': 'Search independent coordinates on bounded grids and refine sampled minima.'
            }
        try:
            for stage in range(1, self.max_stages + 1):
                self.context.begin_stage(self.max_stages - stage + 1)
                previous_best = self.context.best_score
                start = len(self.context.improvements)
                first_evaluation = self.context.evaluations
                started = time.monotonic()
                outcome = 'search_completed'
                try:
                    if components is not None:
                        position = self.context.best_position
                        if position is None or self.restart:
                            position = self.rng.uniform(self.bounds[:, 0], self.bounds[:, 1])
                        offset = (stage - 1) * self.dimensions // self.max_stages
                        separable_search(self.context, components, position,
                                         rng=self.rng if stage > 1 else None, offset=offset)
                    else:
                        if stage == 1:
                            self.context(self.bounds[:, 0] / 2 + self.bounds[:, 1] / 2)
                            self.context(self.rng.uniform(self.bounds[:, 0], self.bounds[:, 1]))
                        if self.current_strategy not in self.algorithms:
                            self._ask_gemini('initial')
                        elif self.restart:
                            self._ask_gemini('stagnating', avoid_strategy=self.current_strategy)
                        self._run_optimizer()
                except StageBudgetReached:
                    outcome = 'stage_budget'
                except SearchLimit as limit:
                    termination = outcome = str(limit)
                if self.context.evaluations > first_evaluation:
                    if self.current_strategy is None:
                        self.current_strategy = 'Initial sampling'
                        self.last_recommendation = {
                            'source': 'initial_sampling',
                            'recommended_strategy': self.current_strategy,
                            'reason': 'The run reached its budget during initial sampling.',
                        }
                    improved = self._record_stage(stage, start, first_evaluation,
                                                  previous_best, outcome, started)
                    stages_without_improvement = 0 if improved else stages_without_improvement + 1
                    self.restart = stages_without_improvement >= self.patience
                    if self.restart:
                        stages_without_improvement = 0
                if outcome in ('time_limit', 'evaluation_limit'):
                    break
                if self.context.evaluations >= self.max_evaluations:
                    termination = 'evaluation_limit'
                    break
        except SearchLimit as limit:
            termination = str(limit)
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
            'settings': {'max_stages':self.max_stages, 'patience':self.patience,
                         'max_evaluations':self.max_evaluations, 'time_limit_seconds':self.time_limit_seconds,
                         'random_seed':self.random_seed, 'planner_mode':self.planner_mode},
            'warnings':['Numerical search returned the best verified candidate; global optimality is not certified.']}
