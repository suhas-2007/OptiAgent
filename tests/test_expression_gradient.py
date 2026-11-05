import numpy as np
import pytest
from backend.differentiation import ExpressionGradient, UnsupportedGradient
from backend.function_parser import SafeFunction


@pytest.mark.parametrize('expression,point',[
    ('(1-x1)**2+100*(x2-x1**2)**2',[-1.3,0.7]),
    ('sin(x1*x2)+exp(x1/3)+log(x2)+sqrt(x2)',[0.2,1.3]),
    ('x1**x2',[1.7,2.3]),('x1**3-x2**2',[-2,-1]),
    ('(x1+x2)**2 + (x1-x2)**2',[0,0])])
def test_expression_derivatives_match_central_differences(expression,point):
    f=SafeFunction(expression)
    gradient=ExpressionGradient(f,len(point))(point)
    estimate=[]
    for i in range(len(point)):
        lo,hi=np.array(point,dtype=float),np.array(point,dtype=float)
        lo[i]-=1e-6; hi[i]+=1e-6
        estimate.append((f(hi)-f(lo))/2e-6)
    assert np.allclose(gradient,estimate,rtol=1e-5,atol=1e-5)


def test_unsupported_derivatives_and_singular_domains():
    with pytest.raises(UnsupportedGradient): ExpressionGradient(SafeFunction('abs(x1)'),1)
    with pytest.raises(UnsupportedGradient): ExpressionGradient(SafeFunction('log(x1)'),1)([0])
