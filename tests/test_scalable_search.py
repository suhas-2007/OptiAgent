import math
import time
import numpy as np
import pytest
from backend.function_parser import SafeFunction
from backend.agent import OptimizationAgent
from backend.search import additive_components
from backend.api import app


def rastrigin(n, shift=0):
    terms = [f'(x{i}-{shift})**2 - 10*cos(2*pi*(x{i}-{shift}))' for i in range(1,n+1)]
    return f'{10*n} + ' + ' + '.join(terms)


@pytest.mark.parametrize('n', [5,20,100])
@pytest.mark.parametrize('shift', [0,0.317])
def test_rastrigin_including_shifted_100_dimensions(n,shift):
    f = SafeFunction(rastrigin(n,shift))
    result = OptimizationAgent(f,n,[[-5.12,5.12]]*n,f.expression,random_seed=19).optimize()
    assert abs(result['best_score']) < 1e-7
    assert np.max(np.abs(result['best_position']-shift)) < 1e-5
    assert result['recommendation']['source']=='structural_analysis'
    assert not result['global_optimum_certified']
    assert result['best_score']==pytest.approx(f(result['best_position']),abs=1e-10)


def test_negative_offset_and_bound_optimum():
    f=SafeFunction('(x1-7.3)**2 + (x2+1.7)**2 - 100')
    result=OptimizationAgent(f,2,[[2,4],[-3,0]],f.expression,random_seed=2).optimize()
    assert result['best_score']==pytest.approx(3.3**2-100,abs=1e-7)
    assert np.allclose(result['best_position'],[4,-1.7],atol=1e-5)


def test_coupled_functions_are_not_treated_as_separable():
    for expression in ('(x1+x2)**2','cos(x1*x2)','(1-x1)**2+100*(x2-x1**2)**2'):
        assert additive_components(SafeFunction(expression),2) is None
    assert additive_components(SafeFunction('x1**2 + x2**2 - 10*(cos(x1)+cos(x2))'),2) is not None


def test_grid_refines_nonzero_multimodal_minimum_without_name_detection():
    f=SafeFunction('(x1-0.273)**2 + 0.02*sin(40*(x1-0.273))**2 + (x2+2.371)**2')
    result=OptimizationAgent(f,2,[[-1,1],[-4,0]],f.expression,random_seed=7).optimize()
    assert result['best_score']<1e-9
    assert np.allclose(result['best_position'],[0.273,-2.371],atol=1e-5)


def test_budget_interruption_returns_verified_incumbent():
    f=SafeFunction('(x1+x2-0.37)**2 + sin(3*x1*x2)**2 - 10')
    result=OptimizationAgent(f,2,[[-5,5]]*2,f.expression,max_evaluations=100,random_seed=9).optimize()
    assert result['termination_reason']=='evaluation_limit'
    assert result['evaluations']<=100
    assert math.isfinite(result['best_score'])
    assert result['best_score']==pytest.approx(f(result['best_position']))
    assert not result['global_optimum_certified']


@pytest.mark.parametrize('restart_mode, expected_samples', [('uniform', 0), ('diverse', 16)])
def test_restart_is_real_and_negative_scores_do_not_stop_early(monkeypatch, restart_mode, expected_samples):
    f=SafeFunction('(x1+x2)**2-100')
    agent=OptimizationAgent(f,2,[[-1,1]]*2,f.expression,max_stages=3,patience=1,random_seed=3,
                            planner_mode='local', restart_mode=restart_mode)
    def plan(**kwargs):
        return {'recommended_strategy':'Differential Evolution','source':'test','confidence':0.5}
    monkeypatch.setattr(agent.planner,'recommend_strategy',plan)
    seeds=[]
    class Solver:
        initial_position=None
        def optimize(self):
            agent.context([0,0])
            return {'best_position':[0,0], 'best_score':-100, 'history':[-100]*5}
    def create(name,objective,dimensions,bounds,seed):
        seeds.append(seed)
        return Solver()
    monkeypatch.setattr(agent.registry,'create',create)
    result=agent.optimize()
    assert len(result['stage_history'])==3
    assert len(set(seeds))==3
    assert not result['stage_history'][1]['restarted']
    assert result['stage_history'][2]['restarted']
    assert result['stage_history'][2]['restart_samples'] == expected_samples
    assert result['settings']['restart_mode'] == restart_mode


def test_api_accepts_restart_sampling_and_rejects_unknown_modes():
    payload = dict(benchmark='sphere', dimensions=2, bounds=[[-5, 5]] * 2,
                   max_stages=1, max_evaluations=100, planner_mode='local')
    with app.test_client() as client:
        response = client.post('/optimize', json=dict(payload, restart_mode='diverse'))
        assert response.status_code == 200
        assert response.get_json()['settings']['restart_mode'] == 'diverse'
        assert client.post('/optimize', json=dict(payload, restart_mode='invalid')).status_code == 400


def test_100_dimensional_api_response_and_unused_variable_warning():
    with app.test_client() as client:
        response=client.post('/optimize',json={'objective':rastrigin(100),'dimensions':100,
                                             'bounds':[[-5.12,5.12]]*100,'random_seed':1})
        assert response.status_code==200
        result=response.get_json()
        assert result['success'] and len(result['best_position'])==100
        assert abs(result['best_score'])<1e-7
        assert result['unused_variables']==[]
        response=client.post('/optimize',json={'objective':'x1**2','dimensions':5,'bounds':[[-5,5]]*5})
        assert response.status_code==200
        assert response.get_json()['unused_variables']==['x2','x3','x4','x5']


@pytest.mark.parametrize('field,value',[('max_evaluations',99),('max_evaluations',True),
    ('max_evaluations',1.5),('time_limit_seconds',0),('time_limit_seconds',float('nan')),
    ('time_limit_seconds',91),('random_seed',-1),('dimensions',1.5),('dimensions',True)])
def test_invalid_search_controls(field,value):
    with app.test_client() as client:
        response=client.post('/optimize',json={'objective':'x1**2','dimensions':1,'bounds':[[-1,1]],field:value})
    assert response.status_code==400


def test_safe_functions_reject_keyword_arguments():
    with pytest.raises(ValueError):
        SafeFunction('cos(x1, bad=x2)')([0,0])


def test_coupled_100_dimensions_return_feasible_best_under_budget():
    f=SafeFunction('(x1+x100-0.7)**2 + '+ ' + '.join(f'(x{i}-0.2)**2' for i in range(1,101)))
    result=OptimizationAgent(f,100,[[-2,3]]*100,f.expression,max_evaluations=1000,
                             time_limit_seconds=5,random_seed=7).optimize()
    assert len(result['best_position'])==100
    assert result['evaluations']<=1000
    assert result['termination_reason'] in ('time_limit','evaluation_limit')
    assert np.all(result['best_position']>=-2) and np.all(result['best_position']<=3)
    assert result['best_score']==pytest.approx(f(result['best_position']))
    assert not result['global_optimum_certified']


def test_time_budget_keeps_best_candidate():
    def slow(point):
        time.sleep(0.003)
        return float(np.sum(np.square(point-0.4)))
    result=OptimizationAgent(slow,2,[[-2,2]]*2,'test callable',time_limit_seconds=0.02,random_seed=1).optimize()
    assert result['termination_reason']=='time_limit'
    assert math.isfinite(result['best_score'])


@pytest.mark.parametrize('expression', ['(x1-0.3)**2+x2**2', '(x1+x2-0.3)**2+x2**2'])
def test_api_runs_configured_stages_on_both_search_paths(expression):
    request = {'objective': expression, 'dimensions': 2, 'bounds': [[-5, 5]]*2,
               'max_stages': 4, 'patience': 2, 'max_evaluations': 1200,
               'random_seed': 17, 'planner_mode': 'local'}
    with app.test_client() as client:
        response = client.post('/optimize', json=request)
        repeat = client.post('/optimize', json=request).get_json()
    assert response.status_code == 200
    result = response.get_json()
    assert len(result['stage_history']) == 4
    assert result['evaluations'] <= 1200
    assert sum(stage['stage_evaluations'] for stage in result['stage_history']) == result['evaluations']
    assert all(stage['stage_evaluations'] > 0 for stage in result['stage_history'])
    assert all(stage['reliable'] for stage in result['stage_history'])
    assert [stage['restarted'] for stage in result['stage_history']] == [False, False, False, True]
    assert result['convergence_history'] == repeat['convergence_history']
    assert result['best_position'] == repeat['best_position']
    assert result['settings']['random_seed'] == 17
def test_shifted_rotated_pairs_at_100_dimensions():
    n = 100
    pairs = [f'((x{i}{op}x{i+1})/sqrt(2){shift})'
             for i in range(1, n, 2) for op, shift in (('-', '-0.317'), ('+', '+0.271'))]
    expression = f'{10*n} + ' + ' + '.join(f'{point}**2 - 10*cos(2*pi*{point})' for point in pairs)
    objective = SafeFunction(expression)
    result = OptimizationAgent(objective, n, [[-5.12, 5.12]] * n, expression,
                               max_stages=10, max_evaluations=100000, time_limit_seconds=90,
                               random_seed=7, planner_mode='local').optimize()
    assert result['recommendation']['recommended_strategy'] == 'Independent block search'
    assert abs(result['best_score']) < 1e-6
    assert result['evaluations'] <= 100000


def test_block_detection_rejects_overlapping_pairs():
    objective = SafeFunction('(x1+x2)**2 + (x2-x3)**2')
    assert additive_components(objective, 3, pairs=True) is None


def test_maximize_reports_original_scores():
    expression = '4 - (x1 - 2)**2 - (x2 + 1)**2'
    payload = dict(objective=expression, dimensions=2, bounds=[[-5, 5]] * 2,
                   max_evaluations=1000, random_seed=7, planner_mode='local')
    with app.test_client() as client:
        response = client.post('/optimize', json=dict(payload, direction='maximize'))
        assert response.status_code == 200
        result = response.get_json()
        assert result['direction'] == 'maximize'
        assert result['objective'] == expression
        assert result['best_position'] == pytest.approx([2, -1], abs=1e-6)
        assert result['best_score'] == pytest.approx(4)
        assert result['stage_history'][-1]['verified_score'] == pytest.approx(4)
        scores = [point['score'] for point in result['convergence_history']]
        assert scores == sorted(scores)
        assert scores[-1] == pytest.approx(4)
        assert client.post('/optimize', json=payload).get_json()['direction'] == 'minimize'
        assert client.post('/optimize', json=dict(payload, direction='invalid')).status_code == 400
