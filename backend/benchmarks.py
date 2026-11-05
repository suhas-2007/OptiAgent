"""Dimension-aware benchmarks; fixed-2D extensions are explicitly identified."""
def build_benchmark(key, dimensions):
    if isinstance(dimensions, bool) or not isinstance(dimensions, int) or not 1 <= dimensions <= 100:
        raise ValueError('Benchmark dimensions must be an integer between 1 and 100.')
    n = dimensions
    xs = [f'x{i}' for i in range(1,n+1)]
    total = lambda items: ' + '.join(items)
    limits = {'sphere':10,'rosenbrock':5,'rastrigin':5.12,'ackley':5,'shifted':10,
              'trigonometric':5,'beale':4.5,'booth':10,'himmelblau':5}
    names = {'sphere':'Sphere','rosenbrock':'Rosenbrock','rastrigin':'Rastrigin','ackley':'Ackley',
             'shifted':'Shifted Quadratic','trigonometric':'Trigonometric','beale':'Beale','booth':'Booth','himmelblau':'Himmelblau'}
    if key not in limits: raise ValueError('Unknown benchmark name.')
    extension = key in ('beale','booth','himmelblau') and n != 2
    if key == 'sphere': expression = total([f'{x}**2' for x in xs])
    elif key == 'rosenbrock':
        if n < 2: raise ValueError('Standard Rosenbrock requires at least 2 dimensions.')
        expression = total([f'(1-x{i})**2 + 100*(x{i+1}-x{i}**2)**2' for i in range(1,n)])
    elif key == 'rastrigin': expression = f'{10*n} + '+total([f'{x}**2 - 10*cos(2*pi*{x})' for x in xs])
    elif key == 'ackley': expression = f'-20*exp(-0.2*sqrt(({total([x+"**2" for x in xs])})/{n})) - exp(({total(["cos(2*pi*"+x+")" for x in xs])})/{n}) + e + 20'
    elif key == 'shifted': expression = total([f'({x}-({3 if i%2==0 else -2}))**2' for i,x in enumerate(xs)])
    elif key == 'trigonometric': expression = total([f'{"sin" if i%2==0 else "cos"}({x})**2' for i,x in enumerate(xs)])
    else:
        blocks=[]
        for i in range(1,n,2):
            a,b=f'x{i}',f'x{i+1}'
            if key=='beale': blocks.append(f'(1.5-{a}+{a}*{b})**2 + (2.25-{a}+{a}*{b}**2)**2 + (2.625-{a}+{a}*{b}**3)**2')
            elif key=='booth': blocks.append(f'({a}+2*{b}-7)**2 + (2*{a}+{b}-5)**2')
            else: blocks.append(f'({a}**2+{b}-11)**2 + ({a}+{b}**2-7)**2')
        if n%2: blocks.append(f'x{n}**2')
        expression=total(blocks)
    explanation = ('Block extension: sum of independent 2D benchmark blocks; an odd remaining variable contributes its square. This is not the standard 2D benchmark.' if extension else f'{n}-dimensional {names[key]} objective; all declared coordinates participate.')
    return {'name':f'{"Block-extended " if extension else ""}{names[key]} ({n}D)',
            'objective':expression,'dimensions':n,'bounds':[[-limits[key],limits[key]] for _ in xs],
            'explanation':explanation,'is_extension':extension}
