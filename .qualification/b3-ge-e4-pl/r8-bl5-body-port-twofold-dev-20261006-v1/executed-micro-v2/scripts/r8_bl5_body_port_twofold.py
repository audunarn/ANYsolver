"""Manufactured-control two-part body solution candidate; no specimen execution.

The original sparse K, load, supports and G=R.T are retained. Decimal is an
accumulator for stored binary64 products, never an alternative equation solve.
The candidate is not wired into the original body probe or solver facade.
"""
from dataclasses import dataclass
from decimal import Decimal as D, localcontext
from fractions import Fraction as F
from math import fma
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu

IDENTITY = 'R8_BL5_BODY_TWO_PART_PHYSICAL_SOLUTION_DEV_V1'
EQUILIBRIUM = 1e-8
WORK_RELATIVE = 1e-8
WORK_DENOMINATOR = 1e-12
GAUGE_COVECTOR = 1e-8
GAUGE_POSE = 1e-9


def _owned(values):
    a=np.asarray(values,dtype=np.float64)
    if a.ndim!=1 or not np.isfinite(a).all():
        raise ValueError('finite one-dimensional binary64 values required')
    return np.frombuffer(a.tobytes(),dtype=np.float64)


def two_sum(a,b):
    """Error-free finite binary64 addition, absent overflow/underflow loss."""
    a=np.asarray(a,dtype=float);b=np.asarray(b,dtype=float)
    with np.errstate(over='ignore',invalid='ignore'):
        s=a+b;v=s-a;e=(a-(s-v))+(b-v)
    if not np.isfinite(s).all() or not np.isfinite(e).all():
        raise FloatingPointError('nonfinite two-part addition')
    return s,e


def _product(a,b):
    high=np.asarray(a,dtype=float)*np.asarray(b,dtype=float)
    if not np.isfinite(high).all():raise FloatingPointError('nonfinite scaled correction')
    low=np.array([fma(float(x),float(y),-float(z)) for x,y,z in zip(a,b,high)],dtype=float)
    if not np.isfinite(low).all():raise FloatingPointError('nonfinite product remainder')
    return high,low


@dataclass(frozen=True)
class TwofoldVector:
    high: np.ndarray
    low: np.ndarray

    def __post_init__(self):
        high=_owned(self.high);low=_owned(self.low)
        if high.shape!=low.shape:raise ValueError('matching two-part vector shapes required')
        object.__setattr__(self,'high',high);object.__setattr__(self,'low',low)

    def fraction_values(self):
        return tuple(F.from_float(float(h))+F.from_float(float(l)) for h,l in zip(self.high,self.low))

    def decimal_values(self):
        return tuple(_decimal(v) for v in self.fraction_values())

    def add(self,high,low):
        """Compensated double-double update; no magnitude assumption at cancellation.

        TwoSum stages retain the leading correction and its remainder. The final
        tail sum is rounded: two parts are finite precision, not exact arithmetic.
        """
        s,e=two_sum(self.high,high);t,f=two_sum(self.low,low)
        u,v=two_sum(e,t);h,l=two_sum(s,u)
        h,l=two_sum(h,l+(v+f))
        return TwofoldVector(h,l)


def _decimal(value):
    # Exact dyadic contractions have finite decimal expansions. This formatter
    # covers three binary64 factors across their full exponent range; decisions
    # below use Fraction directly and never depend on this formatting precision.
    with localcontext() as context:
        context.prec=8192
        return D(value.numerator)/D(value.denominator)


def matrix_action(matrix,vector):
    """Exact dyadic contraction of original CSR entries and BOTH stored parts."""
    if (not sparse.issparse(matrix) or matrix.format!='csr' or matrix.shape[1]!=len(vector.high)
            or not np.isfinite(matrix.data).all()):
        raise ValueError('matching finite original CSR operator required')
    q=vector.fraction_values();result=[]
    for i in range(matrix.shape[0]):
        lo,hi=matrix.indptr[i:i+2]
        result.append(sum((F.from_float(float(v))*q[int(j)]
                           for v,j in zip(matrix.data[lo:hi],matrix.indices[lo:hi])),F(0)))
    return tuple(result)


def pairing(covector,vector):
    """Exact represented physical work; no low-part loss or float underflow."""
    if len(covector)!=len(vector.high):raise ValueError('matching work covector required')
    left=[]
    for v in covector:
        if isinstance(v,F):left.append(v)
        elif isinstance(v,D):
            if not v.is_finite():raise ValueError('finite work covector required')
            left.append(F(v))
        else:
            if not np.isfinite(v):raise ValueError('finite work covector required')
            left.append(F.from_float(float(v)))
    return sum((f*q for f,q in zip(left,vector.fraction_values())),F(0))


def _ratio(residual,load,scale):
    """Original active gate and squared global work gate, checked exactly."""
    f=[F.from_float(float(v)) for v in load];s=[F.from_float(float(v)) for v in scale]
    rn2=sum(((r*w)**2 for r,w in zip(residual,s)),F(0))
    fn2=sum(((v*w)**2 for v,w in zip(f,s)),F(0))
    active=max((abs(r/v) for r,v in zip(residual,f) if v),default=F(0))
    tolerance=F.from_float(EQUILIBRIUM)
    passed=active<=tolerance and (rn2<=tolerance*tolerance*fn2 if fn2 else rn2==0)
    with localcontext() as context:
        context.prec=80
        global_ratio=(D((rn2/fn2).numerator)/D((rn2/fn2).denominator)).sqrt() if fn2 else (D(0) if not rn2 else D('Infinity'))
        displayed=max(global_ratio,D(active.numerator)/D(active.denominator))
    return displayed,passed


@dataclass(frozen=True)
class BodySolution:
    coordinates: TwofoldVector
    gauge_multipliers: TwofoldVector
    report: dict


def solve_body_twofold(k,load,coordinate_scale,*,fixed=(),rigid=None,max_corrections=3):
    """One sparse indefinite LU and bounded original-equation residual corrections.

    This returns explicit failure statuses; a failed candidate is not a physical
    body solution. PHYSICAL Kq-load must pass independently of joint KKT residual.
    """
    if not sparse.issparse(k) or k.format!='csr':raise ValueError('original CSR K required')
    k=k.copy();f=_owned(load);sc=_owned(coordinate_scale);n=len(f)
    if (not n or k.shape!=(n,n) or sc.shape!=(n,) or not np.isfinite(k.data).all()
            or np.any(sc<=0) or type(max_corrections)is not int or not 0<=max_corrections<=32):
        raise ValueError('finite square body operator, positive scales and bounded corrections required')
    if any(type(i)is not int or not 0<=i<n for i in fixed) or len(set(fixed))!=len(fixed):
        raise ValueError('distinct physical fixed coordinates required')
    free=np.setdiff1d(np.arange(n),fixed)
    if not len(free):raise ValueError('free original body coordinates required')
    if rigid is None:g=sparse.csr_matrix((0,n))
    else:
        r=np.array(rigid,dtype=float,copy=True)
        if r.shape!=(n,6) or not np.isfinite(r).all():raise ValueError('six finite physical rigid fields required')
        g=sparse.csr_matrix(r.T)
        balanced=matrix_action(g,TwofoldVector(f,np.zeros(n)))
        if max(map(abs,balanced),default=D(0))>D.from_float(GAUGE_COVECTOR):
            raise ValueError('unsupported body load has nonzero physical rigid work')
    rows=len(g.indptr)-1;scale=sc[free];dp=sparse.diags(scale)
    a0=dp@k[free,:][:,free]@dp
    rowmax=np.asarray(abs(a0).max(axis=1).toarray()).ravel()
    if np.any(rowmax<=0) or not np.isfinite(rowmax).all():raise ValueError('nonzero finite mixed body rows required')
    d=scale/np.sqrt(rowmax);dp=sparse.diags(d);gf=g[:,free]
    gn=np.asarray((gf@dp).power(2).sum(axis=1)).ravel()
    if np.any(gn<=0) or not np.isfinite(gn).all():raise ValueError('nonzero finite physical gauge rows required')
    dg=1/np.sqrt(gn);dm=sparse.diags(dg)
    a=sparse.bmat([[dp@k[free,:][:,free]@dp,dp@gf.T@dm],[dm@gf@dp,None]],format='csc')
    q=TwofoldVector(np.zeros(n),np.zeros(n));eta=TwofoldVector(np.zeros(rows),np.zeros(rows))
    work=[];linear_solves=0;status='FAILED_CORRECTION_LIMIT';detail=''
    def observed():
        internal=matrix_action(k,q);physical=tuple(v-F.from_float(float(x)) for v,x in zip(internal,f))
        reaction=matrix_action(g.T.tocsr(),eta);joint=tuple(v+w for v,w in zip(physical,reaction))
        pose=matrix_action(g,q);eq,eq_ok=_ratio(tuple(physical[i] for i in free),f[free],sc[free])
        kkt,_=_ratio(tuple(joint[i] for i in free),f[free],sc[free])
        paired=pairing(f,q);ip=pairing(internal,q);den=max(abs(paired),F.from_float(WORK_DENOMINATOR))
        wr=abs(ip-paired)/den
        passed=(eq_ok and wr<=F.from_float(WORK_RELATIVE)
            and max(map(abs,reaction),default=F(0))<=F.from_float(GAUGE_COVECTOR)
            and max(map(abs,pose),default=F(0))<=F.from_float(GAUGE_POSE))
        return physical,joint,reaction,pose,eq,kkt,paired,ip,den,wr,passed
    if not np.isfinite(a.data).all() or not np.isfinite(d).all() or not np.isfinite(dg).all():
        raise ValueError('representable original congruence required')
    try:
        lu=splu(a)
    except RuntimeError as error:
        status='FAILED_FACTORIZATION';detail=str(error);lu=None
    try:
        for iteration in range(max_corrections+1) if lu is not None else ():
            if iteration==0:rhs=np.r_[d*f[free],np.zeros(rows)]
            else:rhs=-np.r_[d*np.array([float(v) for v in values[1]])[free],dg*np.array([float(v) for v in values[3]])]
            if not np.isfinite(rhs).all():raise FloatingPointError('nonfinite physical correction RHS')
            z=lu.solve(rhs);linear_solves+=1
            if not np.isfinite(z).all():raise FloatingPointError('nonfinite sparse correction')
            h,l=_product(d,z[:len(free)]);dh=np.zeros(n);dl=np.zeros(n);dh[free]=h;dl[free]=l
            qnext=q.add(dh,dl);eh,el=_product(dg,z[len(free):]);enext=eta.add(eh,el)
            unchanged=(np.array_equal(qnext.high,q.high) and np.array_equal(qnext.low,q.low)
                       and np.array_equal(enext.high,eta.high) and np.array_equal(enext.low,eta.low))
            q,eta=qnext,enext;values=observed()
            work.append(dict(iteration=iteration,physical_equation_ratio=str(values[4]),joint_KKT_ratio=str(values[5]),
                             changed=not unchanged,passed=values[-1]))
            if values[-1]:status='DEVELOPMENT_BODY_SOLVED_NOT_ACCEPTED';break
            if unchanged:status='FAILED_STAGNATION';break
    except FloatingPointError as error:status='FAILED_NONFINITE';detail=str(error)
    values=observed();physical,joint,reaction,pose,eq,kkt,paired,ip,den,wr,_=values
    report=dict(identity=IDENTITY,status=status,detail=detail,coordinates_hi=q.high.tolist(),coordinates_lo=q.low.tolist(),
        gauge_multipliers_hi=eta.high.tolist(),gauge_multipliers_lo=eta.low.tolist(),
        physical_residual=[str(_decimal(v)) for v in physical],joint_KKT_residual=[str(_decimal(v)) for v in joint],
        gauge_covector=[str(_decimal(v)) for v in reaction],gauge_pose=[str(_decimal(v)) for v in pose],
        equation_ratio=str(eq),joint_KKT_ratio=str(kkt),paired_work_J=str(_decimal(paired)),internal_pairing_J=str(_decimal(ip)),
        work_relative_error=str(_decimal(wr)),work_denominator_J=str(_decimal(den)),
        support_covector={str(i):str(_decimal(physical[i])) for i in fixed},
        original_load=f.tolist(),coordinate_scale=sc.tolist(),fixed=list(fixed),
        original_gauge_CSR=dict(data=g.data.tolist(),indices=g.indices.tolist(),indptr=g.indptr.tolist(),shape=g.shape),
        ordinary_hi_only_CSR_residual=(k@q.high-f).tolist(),iterations=work,linear_solves=linear_solves,
        factorization_count=1,correction_limit=max_corrections,
        arithmetic='original binary64 coefficients; two-part physical q/eta; exact dyadic represented residual/work accumulation; Decimal diagnostics only',
        limitations='No material energy from a mixed saddle subblock. Downstream pose/material/trace consumers must explicitly preserve both parts; no specimen evaluated.')
    return BodySolution(q,eta,report)
