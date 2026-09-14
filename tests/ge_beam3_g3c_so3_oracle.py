"""Independent Decimal SO(3) value/gradient/Hessian oracle; no solver imports.

Scalar references use factorial/recurrence series over the complete requested
finite grid, not the candidate's piecewise elementary formulas. This helper
does not run a mechanics case, issue authority, or replace runtime dispatch.
"""
from dataclasses import dataclass
from decimal import Decimal as D, localcontext
from math import factorial


def decimal(value):
    if type(value) is float:
        return D.from_float(value)
    if type(value) is D:
        return value
    if type(value) is int:
        return D(value)
    raise TypeError('exact float, int or Decimal required')


def coefficient(kind, value, precision=100):
    """Return f, f', f'' and term count, independently differentiated series.

    For Log, value is cosine; others receive theta squared. The convergent
    series supports |1-c|<2. Its positive absolute derivative-term ratios
    decrease for n>=2. The reported stop uses a geometric majorant for each
    remaining derivative tail. No candidate/source coefficient is consulted.
    """
    with localcontext() as ctx:
        ctx.prec = precision
        x = decimal(value)
        z = 1-x if kind == 'log' else x
        if kind not in ('log', 'sinc', 'cosc'):
            raise ValueError('coefficient kind')
        if kind == 'log' and abs(z) >= 2:
            raise ValueError('Log series domain')
        if kind != 'log' and not 0 <= x <= 40:
            raise ValueError('oracle frozen Exp grid bound')
        total = [D(0), D(0), D(0)]
        a = D(1)
        tolerance = D(10) ** (-(precision-20))
        for n in range(16384):
            if kind == 'log':
                if n:
                    a *= D(n)/D(2*n+1)
            else:
                a = D((-1)**n)/D(factorial(2*n+(1 if kind == 'sinc' else 2)))
            terms = []
            for k in range(3):
                term = D(0)
                if n >= k:
                    power = D(1) if n == k else z**(n-k)
                    sign = (-1)**k if kind == 'log' else 1
                    term = sign*a*D((1,n,n*(n-1))[k])*power
                terms.append(term)
                total[k] += term
            if n >= 32:
                bounds = []
                for k in range(3):
                    ratio = D(n+1)/D(n+1-k)*abs(z)
                    if kind == 'log':
                        ratio *= D(n+1)/D(2*n+3)
                    else:
                        offset = 1 if kind == 'sinc' else 2
                        ratio /= D((2*n+offset+1)*(2*n+offset+2))
                    bounds.append(abs(terms[k])*ratio/(1-ratio) if ratio < 1 else D('Infinity'))
                if all(bound <= tolerance*max(D(1),abs(t)) for bound,t in zip(bounds,total)):
                    return tuple(+v for v in total), n+1
        raise RuntimeError('bounded Decimal series did not converge')


@dataclass(frozen=True)
class DJet:
    value: D
    gradient: tuple
    hessian: tuple

    @staticmethod
    def constant(value, size):
        return DJet(decimal(value), (D(0),)*size, tuple((D(0),)*size for _ in range(size)))

    @staticmethod
    def variable(value, index, size):
        g = tuple(D(int(i == index)) for i in range(size))
        return DJet(decimal(value), g, tuple((D(0),)*size for _ in range(size)))

    def lift(self, other):
        if type(other) is DJet:
            if len(other.gradient) != len(self.gradient):
                raise ValueError('jet dimensions')
            return other
        return DJet.constant(other,len(self.gradient))

    def __add__(self, other):
        b = self.lift(other); n = len(self.gradient)
        return DJet(self.value+b.value, tuple(self.gradient[i]+b.gradient[i] for i in range(n)),
            tuple(tuple(self.hessian[i][j]+b.hessian[i][j] for j in range(n)) for i in range(n)))

    __radd__ = __add__

    def __neg__(self):
        return DJet(-self.value, tuple(-v for v in self.gradient),
                    tuple(tuple(-v for v in row) for row in self.hessian))

    def __sub__(self, other): return self + (-self.lift(other))
    def __rsub__(self, other): return self.lift(other) + (-self)

    def __mul__(self, other):
        b = self.lift(other); n = len(self.gradient)
        g = tuple(self.gradient[i]*b.value+self.value*b.gradient[i] for i in range(n))
        h = tuple(tuple(self.hessian[i][j]*b.value+self.value*b.hessian[i][j]
            +self.gradient[i]*b.gradient[j]+self.gradient[j]*b.gradient[i]
            for j in range(n)) for i in range(n))
        return DJet(self.value*b.value,g,h)

    __rmul__ = __mul__

    def __truediv__(self, other):
        b = self.lift(other)
        return self*compose(b,(1/b.value,-1/(b.value*b.value),2/(b.value*b.value*b.value)))


def compose(argument, derivatives):
    v, first, second = derivatives; n = len(argument.gradient)
    return DJet(v,tuple(first*x for x in argument.gradient),
        tuple(tuple(first*argument.hessian[i][j]+second*argument.gradient[i]*argument.gradient[j]
                    for j in range(n)) for i in range(n)))


def matmul(a,b):
    return [[sum((a[i][k]*b[k][j] for k in range(len(b))),0)
             for j in range(len(b[0]))] for i in range(len(a))]


def exp_jets(vector, precision=100):
    with localcontext() as ctx:
        ctx.prec = precision
        x = sum((v*v for v in vector),0)
        a = compose(x,coefficient('sinc',x.value,precision)[0])
        b = compose(x,coefficient('cosc',x.value,precision)[0])
        vx,vy,vz = vector; zero = DJet.constant(0,len(vx.gradient))
        cross = [[zero,-vz,vy],[vz,zero,-vx],[-vy,vx,zero]]
        squared = matmul(cross,cross)
        return [[int(i==j)+a*cross[i][j]+b*squared[i][j] for j in range(3)] for i in range(3)]


def log_jets(matrix, precision=100):
    with localcontext() as ctx:
        ctx.prec = precision
        c = (matrix[0][0]+matrix[1][1]+matrix[2][2]-1)/2
        f = compose(c,coefficient('log',c.value,precision)[0])
        axial = [(matrix[2][1]-matrix[1][2])/2,
                 (matrix[0][2]-matrix[2][0])/2,
                 (matrix[1][0]-matrix[0][1])/2]
        return [f*v for v in axial]


def exp_from_vector(values, precision=100):
    with localcontext() as ctx:
        ctx.prec = precision
        return exp_jets([DJet.variable(v,i,3) for i,v in enumerate(values)],precision)


def self_test():
    with localcontext() as ctx:
        ctx.prec = 100
        assert coefficient('sinc',0)[0] == (D(1),-D(1)/6,D(1)/60)
        assert coefficient('cosc',0)[0] == (D(1)/2,-D(1)/24,D(1)/360)
        assert all(abs(a-b)<D('1e-98') for a,b in
                   zip(coefficient('log',1)[0],(D(1),-D(1)/3,D(4)/15)))
        for values in ((0,0,0),(.001,-.0007,.0004),(.7,-.4,.2)):
            result = log_jets(exp_from_vector(values))
            for i,j in enumerate(result):
                assert abs(j.value-decimal(values[i])) < D('1e-75')
                assert max(abs(v-D(int(k==i))) for k,v in enumerate(j.gradient)) < D('1e-75')
                assert max(abs(v) for row in j.hessian for v in row) < D('1e-75')
        for kind,value in (('sinc',19.4),('cosc',19.4),('log',-.9510565162951535)):
            low,terms = coefficient(kind,value,90)
            high,_ = coefficient(kind,value,110)
            assert tuple(float(v) for v in low) == tuple(float(v) for v in high)
        return dict(status='ORACLE_SELF_TEST_ONLY', mechanics_executed=False,
                    production_imports=False, largest_log_terms=terms)


if __name__ == '__main__':
    print(self_test())
