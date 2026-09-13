"""Independently authored analytic polar/Exp/Log chart; research checker only.

No production, producer, recovery, or cached-matrix imports. Second derivatives
are analytic: the polar Sylvester equation, then scalar chain/product rules.
"""
import math
import numpy as np

DIM = 24


class Scalar:
    __slots__ = ('v', 'g', 'h')

    def __init__(self, value, gradient=None, hessian=None):
        self.v = float(value)
        self.g = np.zeros(DIM) if gradient is None else np.asarray(gradient, dtype=float)
        self.h = np.zeros((DIM, DIM)) if hessian is None else np.asarray(hessian, dtype=float)

    @staticmethod
    def coordinate(value, index):
        g = np.zeros(DIM); g[index] = 1.
        return Scalar(value, g)

    def __add__(self, other):
        b = other if isinstance(other, Scalar) else Scalar(other)
        return Scalar(self.v+b.v, self.g+b.g, self.h+b.h)

    __radd__ = __add__

    def __neg__(self):
        return Scalar(-self.v, -self.g, -self.h)

    def __sub__(self, other):
        return self + (-other)

    def __rsub__(self, other):
        return other + (-self)

    def __mul__(self, other):
        b = other if isinstance(other, Scalar) else Scalar(other)
        return Scalar(self.v*b.v, self.g*b.v+b.g*self.v,
                      self.h*b.v+b.h*self.v+np.outer(self.g,b.g)+np.outer(b.g,self.g))

    __rmul__ = __mul__

    def function(self, value, first, second):
        return Scalar(value, first*self.g, first*self.h+second*np.outer(self.g,self.g))

    def __pow__(self, exponent):
        p = float(exponent)
        if p == 0: return Scalar(1.)
        if p == 1: return self
        return self.function(self.v**p, p*self.v**(p-1), p*(p-1)*self.v**(p-2))

    def __truediv__(self, other):
        b = other if isinstance(other, Scalar) else Scalar(other)
        return self * b**(-1)

    def __rtruediv__(self, other):
        return other * self**(-1)


def sine(a): return a.function(math.sin(a.v), math.cos(a.v), -math.sin(a.v))
def cosine(a): return a.function(math.cos(a.v), -math.sin(a.v), -math.cos(a.v))


def arccosine(a):
    z = 1-a.v*a.v
    if z <= 0: raise ValueError('checker Log outside smooth branch')
    return a.function(math.acos(a.v), -1/math.sqrt(z), -a.v/z**1.5)


def hat(v):
    return np.array([[0.,-v[2],v[1]],[v[2],0.,-v[0]],[-v[1],v[0],0.]], dtype=object)


def skew(v):
    return np.asarray(hat(v), dtype=float)


def axl(a):
    return np.array([a[2,1],a[0,2],a[1,0]])


def constants(a):
    a = np.asarray(a, dtype=float)
    return np.array([Scalar(v) for v in a.flat], dtype=object).reshape(a.shape)


def series(s, offset):
    # sum (-s)^k/(2k+offset)!, with enough terms for s<0.1 including d2.
    result = Scalar(0.); power = Scalar(1.)
    for k in range(12):
        result += ((-1.)**k/math.factorial(2*k+offset))*power
        power *= s
    return result


def exponential(vector):
    s = sum(a*a for a in vector)
    if s.v < .1:
        a, b = series(s,1), series(s,2)
    else:
        theta = s**.5
        a, b = sine(theta)/theta, (1-cosine(theta))/s
    w = hat(vector)
    return constants(np.eye(3)) + a_matrix(w,a) + a_matrix(w@w,b)


def a_matrix(matrix, scalar):
    return np.array([scalar*x for x in matrix.flat], dtype=object).reshape(matrix.shape)


def logarithm(rotation):
    c = (sum(rotation[i,i] for i in range(3))-1)/2
    t = 1-c
    if t.v < .02:
        factor = Scalar(0.); power = Scalar(1.)
        for k in range(16):
            coefficient = 2**k*math.factorial(k)**2/math.factorial(2*k+1)
            factor += coefficient*power; power *= t
    else:
        angle = arccosine(c)
        if angle.v >= .9*math.pi: raise ValueError('checker relative rotation requires cutback')
        factor = angle/(1-c*c)**.5
    return [factor*(rotation[b,a]-rotation[a,b])/2 for a,b in ((1,2),(2,0),(0,1))]


def polar_derivatives(reference, current):
    X = reference-reference.mean(axis=0)
    x = current-current.mean(axis=0)
    A = x.T@X
    left, singular, right = np.linalg.svd(A)
    orientation=1. if np.linalg.det(left@right) > 0 else -1.
    correction = np.diag([1.,1.,orientation])
    reference_scale_squared=float(np.sum(X*X))
    if not math.isfinite(reference_scale_squared) or reference_scale_squared <= 0:
        raise ValueError('checker degenerate reference polar scale')
    signed_last=correction[2,2]*singular[2]
    gap=2*(singular[1]+signed_last)/reference_scale_squared
    spectral_scale=float(np.sum(singular))/reference_scale_squared
    if not gap > 1e-11*max(np.finfo(float).tiny,spectral_scale):
        raise ValueError('checker nonunique proper polar fit; refine or cut back')
    R = left@correction@right
    S = R.T@A
    K = np.trace(S)*np.eye(3)-S
    if not np.isfinite(K).all() or singular[1] <= 0:
        raise ValueError('checker degenerate proper polar branch')
    # S can have a tiny signed third eigenvalue for rounded registry geometry.
    # Do not replace it by a projected PSD matrix or regularize K.
    Ai = np.zeros((DIM,3,3))
    for node in range(4):
        for component in range(3): Ai[6*node+component,component,:] = X[node]
    M = np.einsum('ab,ibc->iac',R.T,Ai)
    omega = np.array([np.linalg.solve(K,axl(m-m.T)) for m in M])
    W = np.array([skew(w) for w in omega])
    first = np.array([R@w for w in W])
    second = np.zeros((DIM,DIM,3,3))
    for j in range(DIM):
        Sj = -W[j]@S+M[j]
        Kj = np.trace(Sj)*np.eye(3)-Sj
        for i in range(DIM):
            Mij = -W[j]@M[i]
            wij = np.linalg.solve(K,axl(Mij-Mij.T)-Kj@omega[i])
            second[i,j] = R@(W[j]@W[i]+skew(wij))
    return R,first,second


def evaluate(reference, displacement, accepted):
    reference = np.asarray(reference,dtype=float)
    displacement = np.asarray(displacement,dtype=float)
    accepted = np.asarray(accepted,dtype=float)
    if reference.shape != (4,3) or displacement.shape != (24,) or accepted.shape != (4,3,3):
        raise ValueError('checker chart shapes')
    if not all(np.isfinite(a).all() for a in (reference,displacement,accepted)):
        raise ValueError('checker nonfinite chart input')
    for rotation in accepted:
        if np.linalg.norm(rotation.T@rotation-np.eye(3)) > 1e-11 or abs(np.linalg.det(rotation)-1) > 1e-11:
            raise ValueError('checker improper accepted rotation')
    if np.any(np.linalg.norm(displacement.reshape(4,6)[:,3:],axis=1) >= .9*math.pi):
        raise ValueError('checker trial increment requires cutback')
    current = reference+displacement.reshape(4,6)[:,:3]
    R,first,second = polar_derivatives(reference,current)
    RJ = np.array([[Scalar(R[i,j],first[:,i,j],second[:,:,i,j]) for j in range(3)] for i in range(3)],dtype=object)
    q = [Scalar.coordinate(displacement[i],i) for i in range(DIM)]
    xj = np.array([[q[6*i+j]+reference[i,j] for j in range(3)] for i in range(4)],dtype=object)
    centre = sum(xj)/4
    Xc = reference-reference.mean(axis=0)
    data=[]; rotations=[]
    for i in range(4):
        local = RJ.T@(xj[i]-centre)
        data.extend(local[j]-Xc[i,j] for j in range(3))
        Q = exponential(q[6*i+3:6*i+6])@constants(accepted[i])
        rotations.append([[v.v for v in row] for row in Q])
        data.extend(logarithm(RJ.T@Q))
    return dict(d=np.array([a.v for a in data]),D=np.array([a.g for a in data]),
                D2=np.array([a.h for a in data]),R=R,Q=np.array(rotations),x=current,
                polar_first=first,polar_second=second)


def spatial_work(displacement, gradient, hessian):
    P = np.eye(DIM); dP = np.zeros((DIM,DIM,DIM))
    for node in range(4):
        start=6*node+3
        eta=[Scalar.coordinate(displacement[start+j],start+j) for j in range(3)]
        s=sum(v*v for v in eta)
        if s.v < .1: b,c=series(s,2),series(s,3)
        else:
            theta=s**.5
            b=(1-cosine(theta))/s; c=(theta-sine(theta))/(theta*s)
        W=hat(eta)
        J=constants(np.eye(3))+a_matrix(W,b)+a_matrix(W@W,c)
        for i in range(3):
            for j in range(3):
                P[start+i,start+j]=J[i,j].v
                dP[start+i,start+j]=J[i,j].g
    wrench=np.linalg.solve(P.T,gradient)
    connection=np.einsum('kij,k->ij',dP,wrench)
    return wrench,np.linalg.solve(P.T,hessian-connection),P,connection
