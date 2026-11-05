"""Reverse-mode derivatives of the existing whitelisted mathematical AST.

No eval, generated Python, benchmark-name matching, or known minimizers.
Unsupported or nonsmooth expressions retain numerical differentiation.
"""
import ast
import math
import numpy as np


class UnsupportedGradient(ValueError):
    pass


class ExpressionGradient:
    def __init__(self, objective, dimensions):
        self.nodes=[]
        self.dimensions=dimensions
        aliases={f'x{i+1}':i for i in range(dimensions)}
        aliases.update({name:i for i,name in enumerate(('x','y','z')) if i<dimensions})
        def add(op,a=None,b=None,dependent=False):
            self.nodes.append((op,a,b,dependent))
            return len(self.nodes)-1
        def visit(node):
            if isinstance(node,ast.Constant) and isinstance(node.value,(int,float)):
                return add('constant',float(node.value))
            if isinstance(node,ast.Name):
                if node.id in aliases: return add('variable',aliases[node.id],dependent=True)
                if node.id in objective.ALLOWED_CONSTANTS: return add('constant',objective.ALLOWED_CONSTANTS[node.id])
            if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.USub,ast.UAdd)):
                a=visit(node.operand)
                return add('neg' if isinstance(node.op,ast.USub) else 'pos',a,dependent=self.nodes[a][3])
            if isinstance(node,ast.BinOp):
                ops={ast.Add:'add',ast.Sub:'sub',ast.Mult:'mul',ast.Div:'div',ast.Pow:'pow'}
                if type(node.op) in ops:
                    a,b=visit(node.left),visit(node.right)
                    return add(ops[type(node.op)],a,b,self.nodes[a][3] or self.nodes[b][3])
            if (isinstance(node,ast.Call) and isinstance(node.func,ast.Name)
                    and node.func.id in ('sin','cos','exp','sqrt','log') and len(node.args)==1 and not node.keywords):
                a=visit(node.args[0])
                return add(node.func.id,a,dependent=self.nodes[a][3])
            raise UnsupportedGradient('Expression uses an operation without a smooth derivative.')
        self.output=visit(objective.tree.body)

    def __call__(self, point):
        values=[]
        try:
            for op,a,b,_ in self.nodes:
                if op=='constant': value=a
                elif op=='variable': value=float(point[a])
                else:
                    u=values[a]
                    v=values[b] if b is not None else None
                    if op=='add': value=u+v
                    elif op=='sub': value=u-v
                    elif op=='mul': value=u*v
                    elif op=='div': value=u/v
                    elif op=='pow': value=u**v
                    elif op=='neg': value=-u
                    elif op=='pos': value=u
                    else: value=getattr(math,op)(u)
                value=float(value)
                if not math.isfinite(value): raise UnsupportedGradient('Nonfinite derivative domain.')
                values.append(value)
            adjoints=[0.0]*len(self.nodes)
            adjoints[self.output]=1.0
            gradient=np.zeros(self.dimensions)
            for i in range(len(self.nodes)-1,-1,-1):
                op,a,b,dependent=self.nodes[i]
                weight=adjoints[i]
                if not dependent or weight==0: continue
                if op=='variable': gradient[a]+=weight; continue
                u=values[a]
                v=values[b] if b is not None else None
                if op=='add': da,db=1,1
                elif op=='sub': da,db=1,-1
                elif op=='mul': da,db=v,u
                elif op=='div': da,db=1/v,-u/v**2
                elif op=='pow':
                    da=0 if v==0 else v*u**(v-1)
                    db=values[i]*math.log(u) if self.nodes[b][3] else 0
                elif op=='neg': da,db=-1,0
                elif op=='pos': da,db=1,0
                elif op=='sin': da,db=math.cos(u),0
                elif op=='cos': da,db=-math.sin(u),0
                elif op=='exp': da,db=values[i],0
                elif op=='sqrt': da,db=0.5/values[i],0
                elif op=='log': da,db=1/u,0
                adjoints[a]+=weight*da
                if b is not None: adjoints[b]+=weight*db
            if not np.all(np.isfinite(gradient)): raise UnsupportedGradient('Nonfinite gradient.')
            return gradient
        except (ArithmeticError,ValueError,TypeError) as error:
            raise UnsupportedGradient('Cannot differentiate at this point.') from error
