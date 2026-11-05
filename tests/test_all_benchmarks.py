import ast
import json
import subprocess
from pathlib import Path
import numpy as np
import pytest
from backend.benchmarks import build_benchmark
from backend.function_parser import SafeFunction
from backend.agent import OptimizationAgent
from backend.api import app

KEYS=['sphere','rosenbrock','rastrigin','ackley','shifted','trigonometric','beale','booth','himmelblau']


@pytest.mark.parametrize('key',KEYS)
@pytest.mark.parametrize('n',[2,5,100])
def test_every_preset_uses_every_coordinate_and_correct_bounds(key,n):
    definition=build_benchmark(key,n)
    f=SafeFunction(definition['objective'])
    used={node.id for node in ast.walk(f.tree) if isinstance(node,ast.Name)}
    assert {f'x{i}' for i in range(1,n+1)}.issubset(used)
    assert len(definition['bounds'])==n
    assert np.isfinite(f(np.zeros(n)))
    assert definition['is_extension']==(key in ['beale','booth','himmelblau'] and n!=2)
    if definition['is_extension']: assert 'not the standard' in definition['explanation']


def test_browser_and_backend_formulas_match():
    module=Path(__file__).parents[1]/'frontend/benchmarks.js'
    script='const {buildBenchmark}=require(process.argv[1]); console.log(JSON.stringify('+json.dumps(KEYS)+'.flatMap(k=>[2,5,100].map(n=>buildBenchmark(k,n)))));'
    browser=json.loads(subprocess.check_output(['node','-e',script,str(module)],text=True))
    server=[build_benchmark(k,n) for k in KEYS for n in (2,5,100)]
    assert browser==server


@pytest.mark.parametrize('key',KEYS)
def test_identification_respects_100_dimensions(key):
    with app.test_client() as client:
        response=client.post('/api/extract-problem',json={'text':key,'dimensions':100})
    assert response.status_code==200
    data=response.get_json()
    assert data['dimensions']==100 and len(data['bounds'])==100


def test_named_benchmark_can_be_optimized_without_manually_typing_100_terms():
    with app.test_client() as client:
        result=client.post('/optimize',json={'benchmark':'sphere','dimensions':100,'bounds':[[-10,10]]*100}).get_json()
    assert result['success'] and len(result['best_position'])==100
    assert result['best_score']<1e-8


@pytest.mark.parametrize('key',KEYS)
def test_every_function_runs_at_100_dimensions_with_bounded_work(key):
    d=build_benchmark(key,100)
    f=SafeFunction(d['objective'])
    result=OptimizationAgent(f,100,d['bounds'],f.expression,max_evaluations=2000,
                             time_limit_seconds=5,random_seed=7,max_stages=1).optimize()
    assert len(result['best_position'])==100
    assert np.isfinite(result['best_score'])
    assert result['evaluations']<=2000
    assert result['best_score']==pytest.approx(f(result['best_position']))
    assert not result['global_optimum_certified']


def test_dimension_errors_are_explicit():
    with pytest.raises(ValueError): build_benchmark('rosenbrock',1)
    with app.test_client() as client:
        assert client.post('/api/extract-problem',json={'text':'sphere','dimensions':101}).status_code==400


def test_100d_rosenbrock_refinement_with_expression_gradient():
    d=build_benchmark('rosenbrock',100)
    f=SafeFunction(d['objective'])
    result=OptimizationAgent(f,100,d['bounds'],f.expression,max_evaluations=10000,
                             time_limit_seconds=15,random_seed=7,max_stages=1).optimize()
    assert result['best_score']<1e-6
    assert np.max(np.abs(result['best_position']-1))<1e-3
