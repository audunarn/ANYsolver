"""Exact represented-law recovery for bounded manufactured local Qp states.

No equilibrium, factorization, Green norm or scientific acceptance is performed.
Physical moments remain unscaled. Decimal values are displays of symbolic
cosine actions, not exact transcendental values or certified error bounds.
"""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from decimal import Decimal, localcontext, ROUND_HALF_EVEN
from fractions import Fraction as F
import math
from types import MappingProxyType

import numpy as np

from scripts import _b3_e4_f03_local_grid as topology
from scripts import _b3_e4_f03_local_primal_assembly as assembly
from scripts import _b3_e4_f03_local_shell as shell
from scripts import _b3_e4_f03_local_functional as functional
from scripts import _b3_e4_f03_spatial_contract as c

Z=F(0)
O=F(1)
BITS=4096
ACTION_BITS=32_000_000
MAX_TERMS=2048


def _bits(x): return x.numerator.bit_length()+x.denominator.bit_length()


def _rational(x):
    if (type(x) is not F or x.numerator.bit_length()>BITS or
            x.denominator.bit_length()>BITS):
        raise ValueError('bounded exact recovery Fraction required')
    return x


def _coordinate(x):
    if (type(x) is not F or not Z<=x<=O or
            max(x.numerator.bit_length(),x.denominator.bit_length())>256):
        raise ValueError('bounded exact station in [0,1] required')
    return x


def _poly(values):
    if type(values) not in (tuple,list) or not 1<=len(values)<=6:
        raise ValueError('at most six exact local polynomial coefficients required')
    return tuple(_rational(v) for v in values)+(Z,)*(6-len(values))


def _at(poly,t):
    result=Z
    for v in reversed(poly): result=result*t+v
    return _rational(result)


def _add(a,b): return _poly(tuple(x+y for x,y in zip(_poly(a),_poly(b))))
def _scale(a,v): return _poly(tuple(x*v for x in a))


def _derivative(poly,h,order=1):
    return _poly(tuple(poly[k]*F(math.factorial(k),math.factorial(k-order))/h**order
                       for k in range(order,len(poly))))


def _product_integral(a,b):
    return _rational(sum((x*y/F(i+j+1) for i,x in enumerate(a)
                          for j,y in enumerate(b)),Z))


def _restrict(poly,offset,scale):
    out=[Z]*6
    for k,value in enumerate(poly):
        for j in range(k+1): out[j]+=value*math.comb(k,j)*offset**(k-j)*scale**j
    return _poly(out)


def _decimal(x): return Decimal(x.numerator)/Decimal(x.denominator)


@dataclass(frozen=True,slots=True)
class Action:
    """Rational part plus sum integral_a^b p(tau)*cos(held_omega*s) ds.

    Canonical exact combination makes cancellation of identical load-work
    terms algebraic. Each retained interval has its own exact local chart.
    """
    rational: F
    cosine_terms: tuple=()

    def __post_init__(self):
        _rational(self.rational)
        if type(self.cosine_terms) not in (tuple,list) or len(self.cosine_terms)>2*MAX_TERMS:
            raise ValueError('bounded cosine action inventory required')
        grouped={};bits=_bits(self.rational)
        for term in self.cosine_terms:
            if type(term) not in (tuple,list) or len(term)!=3:
                raise ValueError('cosine term requires exact left/right/polynomial')
            a,b,p=term;_coordinate(a);_coordinate(b)
            if a>=b: raise ValueError('positive exact cosine interval required')
            old=grouped.get((a,b));new=_add(old or (Z,)*6,_poly(p))
            bits+=sum(_bits(v) for v in new)
            if old is None: bits+=_bits(a)+_bits(b)
            else: bits-=sum(_bits(v) for v in old)
            if bits>ACTION_BITS: raise ValueError('cosine action aggregate bit cap exceeded')
            grouped[a,b]=new
        terms=tuple((a,b,p) for (a,b),p in sorted(grouped.items()) if any(p))
        if len(terms)>MAX_TERMS: raise ValueError('cosine action interval cap exceeded')
        object.__setattr__(self,'cosine_terms',terms)

    def __neg__(self):
        return Action(-self.rational,tuple((a,b,_scale(p,-O)) for a,b,p in self.cosine_terms))

    def __add__(self,other):
        if not isinstance(other,Action): return NotImplemented
        return Action(self.rational+other.rational,self.cosine_terms+other.cosine_terms)

    def __sub__(self,other): return self+-other

    def decimal_value(self):
        """Fixed 70-digit display, 120 sine/cosine Taylor pairs; no clipping.

        Expand on exact local tau so positive intervals with identical float
        endpoints are retained. This is not a posterior error certificate.
        """
        with localcontext() as ctx:
            ctx.prec=70;ctx.rounding=ROUND_HALF_EVEN
            total=_decimal(self.rational)
            for a,b,poly in self.cosine_terms:
                x=_decimal(c.Q_OMEGA*a);delta=_decimal(c.Q_OMEGA*(b-a))
                cos=ct=Decimal(1);sin=st=x
                for k in range(1,120):
                    ct*=-x*x/Decimal((2*k-1)*(2*k));cos+=ct
                    st*=-x*x/Decimal((2*k)*(2*k+1));sin+=st
                coefficients=tuple(_decimal(v) for v in poly)
                ce=Decimal(1);so=delta;integral=Decimal(0)
                for k in range(120):
                    even=sum((v/Decimal(j+2*k+1) for j,v in enumerate(coefficients)),Decimal(0))
                    odd=sum((v/Decimal(j+2*k+2) for j,v in enumerate(coefficients)),Decimal(0))
                    integral+=cos*ce*even-sin*so*odd
                    ce*=-delta*delta/Decimal((2*k+1)*(2*k+2))
                    so*=-delta*delta/Decimal((2*k+2)*(2*k+3))
                total+=_decimal(b-a)*integral
            if not total.is_finite(): raise ArithmeticError('nonfinite cosine action display')
            return +total


@dataclass(frozen=True,slots=True)
class RecoveryBudget:
    trace_budget: assembly.AssemblyBudget
    max_free_dofs: int
    max_intervals: int
    max_integer_bits: int
    max_work_bytes: int
    max_operations: int

    def __post_init__(self):
        if not isinstance(self.trace_budget,assembly.AssemblyBudget) or any(
                type(v) is not int or v<=0 for v in (self.max_free_dofs,
                self.max_intervals,self.max_integer_bits,self.max_work_bytes,self.max_operations)):
            raise ValueError('explicit positive recovery budgets required')


@dataclass(frozen=True,slots=True,init=False)
class Recovery:
    q: tuple
    eta: tuple
    cuts: tuple
    pose: tuple
    resultants: tuple
    interface: functional.Functional
    root_gap: tuple
    root_slope: F
    tip_pose: tuple
    root_resultants: tuple
    tip_resultants: tuple
    root_reaction: tuple
    support_lift_actions: tuple|None
    shell_lift_work: tuple|None
    interface_lift_work: tuple|None
    diagnostics: object

    def __init__(self,*args,**kwargs):
        raise TypeError('Recovery requires the validated recover factory')


def _vector(values,size,max_bits):
    if type(values) is np.ndarray:
        if values.dtype!=np.float64 or values.shape!=(size,) or not np.isfinite(values).all():
            raise ValueError('finite float64 recovery vector shape required')
        values=values.copy()
        items=(F.from_float(float(v)) for v in values)
    elif type(values) in (tuple,list) and len(values)==size:
        items=iter(values)
    else: raise ValueError('owned float64 or bounded exact recovery vector required')
    out=[];bits=0
    for v in items:
        _rational(v);bits+=_bits(v)
        if bits>max_bits: raise ValueError('recovery aggregate integer budget exceeded')
        out.append(v)
    return tuple(out)


def _test_rows(cuts,rows):
    if type(rows) not in (tuple,list) or len(rows)!=len(cuts)-1:
        raise ValueError('test pose must use the same exact station partition')
    result=[];bits=0
    for row in rows:
        if type(row) not in (tuple,list) or len(row)!=3:
            raise ValueError('three physical test pose channels required')
        owned=tuple(_poly(p) for p in row)
        bits+=sum(_bits(v) for p in owned for v in p)
        if bits>ACTION_BITS: raise ValueError('test pose aggregate bit cap exceeded')
        result.append(owned)
    return tuple(result)


def functional_work(value,test_pose):
    """Density plus both endpoint atoms on a continuous polynomial test pose."""
    if not isinstance(value,functional.Functional): raise ValueError('owned physical functional required')
    rows=_test_rows(value.cuts,test_pose)
    for left,right in zip(rows,rows[1:]):
        if any(_at(a,O)!=b[0] for a,b in zip(left,right)):
            raise ValueError('functional test pose must be continuous')
    rational=Z;terms=[]
    for (a,b),density,test in zip(zip(value.cuts,value.cuts[1:]),value.coefficients,rows):
        rational+=(b-a)*sum((_product_integral(p,w) for p,w in zip(density,test)),Z)
        cosine=(Z,)*6
        for amp,w in zip(value.cosine,test): cosine=_add(cosine,_scale(w,amp))
        terms.append((a,b,cosine))
    rational+=sum((v*w[0] for v,w in zip(value.atoms[0],rows[0])),Z)
    rational+=sum((v*_at(w,O) for v,w in zip(value.atoms[1],rows[-1])),Z)
    return Action(rational,tuple(terms))


def beam_work(value,test_pose):
    """Exact integral N*w_u' + Q*(w_v'-w_theta) + M*w_theta'."""
    if not isinstance(value,Recovery): raise ValueError('owned recovery required')
    rows=_test_rows(value.cuts,test_pose);answer=Z
    for (a,b),resultant,test in zip(zip(value.cuts,value.cuts[1:]),value.resultants,rows):
        dw=tuple(_derivative(w,b-a) for w in test)
        strain=(dw[0],_add(dw[1],_scale(test[2],-O)),dw[2])
        answer+=(b-a)*sum((_product_integral(v,w) for v,w in zip(resultant,strain)),Z)
    return _rational(answer)


def load_work(value,test_pose):
    if not isinstance(value,Recovery): raise ValueError('owned recovery required')
    rows=_test_rows(value.cuts,test_pose);constant=c.Q_F0/c.Q_L0
    rational=sum(((b-a)*constant*_product_integral((O,),row[1])
                  for (a,b),row in zip(zip(value.cuts,value.cuts[1:]),rows)),Z)
    return Action(rational,tuple((a,b,_scale(row[1],constant/4))
        for (a,b),row in zip(zip(value.cuts,value.cuts[1:]),rows)))


def virtual_work_defect(value,test_pose):
    rows=_test_rows(value.cuts,test_pose)
    root=sum((eta*row[0] for eta,row in zip(value.eta,rows[0])),Z)
    return (functional_work(value.interface,rows)+Action(beam_work(value,rows)+root)
            -load_work(value,rows))


def station(value,s,*,order=0,side='right',resultants=False):
    """Exact one-sided observations; second pose derivatives may jump."""
    if not isinstance(value,Recovery) or type(order) is not int or order not in (0,1,2):
        raise ValueError('owned recovery and derivative order 0..2 required')
    _coordinate(s)
    if side not in ('left','right') or type(resultants) is not bool:
        raise ValueError('explicit station side and resultant flag required')
    i=min(bisect_right(value.cuts,s)-1,len(value.cuts)-2)
    if side=='left' and i>0 and s==value.cuts[i]: i-=1
    a,b=value.cuts[i:i+2];rows=(value.resultants if resultants else value.pose)[i]
    return tuple(_at(_derivative(p,b-a,order) if order else p,(s-a)/(b-a)) for p in rows)


def band(value,left,right):
    """Signed (Fx,Fy,M_origin) including external endpoints exactly once.

    M_origin integrates s*mu_y+mu_theta. There are no internal atoms.
    Adjacent positive bands therefore sum without shared-edge double counting.
    """
    if not isinstance(value,Recovery): raise ValueError('owned recovery required')
    _coordinate(left);_coordinate(right)
    if left>=right: raise ValueError('positive exact band required')
    rational=[Z]*3;terms=[[],[],[]];f=value.interface
    for (a,b),density in zip(zip(value.cuts,value.cuts[1:]),f.coefficients):
        lo=max(a,left);hi=min(b,right)
        if lo>=hi: continue
        rows=tuple(_restrict(p,(lo-a)/(b-a),(hi-lo)/(b-a)) for p in density)
        for channel in (0,1):
            rational[channel]+=(hi-lo)*_product_integral(rows[channel],(O,))
            terms[channel].append((lo,hi,(f.cosine[channel],)))
        rational[2]+=(hi-lo)*(_product_integral(rows[1],(lo,hi-lo))+
                                            _product_integral(rows[2],(O,)))
        terms[2].append((lo,hi,(f.cosine[2]+lo*f.cosine[1],(hi-lo)*f.cosine[1])))
    for s,atom,include in ((Z,f.atoms[0],left==Z),(O,f.atoms[1],right==O)):
        if include:
            rational[0]+=atom[0];rational[1]+=atom[1];rational[2]+=s*atom[1]+atom[2]
    return tuple(Action(v,tuple(t)) for v,t in zip(rational,terms))


def lift_pose(cuts,side,channel):
    """Exact A of phi_side(x)*(e_x,e_y,(-y,x)); moments preserve gamma."""
    if side not in ('left','right') or type(channel) is not int or channel not in (0,1,2):
        raise ValueError('left/right physical translation/rotation lift required')
    if type(cuts) not in (tuple,list) or not 2<=len(cuts)<=MAX_TERMS+1:
        raise ValueError('bounded exact lift partition required')
    cc=tuple(_coordinate(v) for v in cuts)
    if cc[0]!=Z or cc[-1]!=O or any(a>=b for a,b in zip(cc,cc[1:])):
        raise ValueError('exact positive lift partition 0..1 required')
    a,b=(F(3,4),F(-1,2)) if side=='left' else (F(1,4),F(1,2))
    xx=c.Q_DX**2+c.Q_A**2/3;yy=c.Q_DY**2+c.Q_A**2/3
    if channel==0: global_polys=((a,b),(Z,),(Z,))
    elif channel==1: global_polys=((Z,),(a,b),(b*xx/c.Q_J,))
    else: global_polys=((Z,),(b*xx,a,b),(a*c.Q_GAMMA,b*(2*xx+yy)/c.Q_J))
    return tuple(tuple(_restrict(_poly(p),lo,hi-lo) for p in global_polys)
                 for lo,hi in zip(cc,cc[1:]))


def _shell_lifts(grid,q):
    works=[Z]*6;nx=len(grid.x_nodes);nc=nx*len(grid.y_nodes)
    for rect,gather,free in zip(grid.rectangles,grid.full_gathers,grid.free_gathers):
        local=tuple(q[int(i)] if i>=0 else Z for i in free)
        matrix=shell.stiffness_exact(rect,grid.p)
        residual=tuple(sum((a*b for a,b in zip(row,local)),Z) for row in matrix)
        for j,index in enumerate(gather):
            component,node=divmod(int(index),nc);iy,ix=divmod(node,nx)
            x,y=grid.x_nodes[ix],grid.y_nodes[iy]
            rigid=((O,Z),(Z,O),(-y,x))
            for side,phi in enumerate(((F(3,2)-x)/2,(x+F(1,2))/2)):
                for channel in range(3): works[side*3+channel]+=residual[j]*phi*rigid[channel][component]
    return tuple(_rational(v) for v in works)


def recover(grid,q,eta,budget):
    """Recover a manufactured state without imposing equilibrium or root slope."""
    if not isinstance(grid,topology.CompiledGrid) or not isinstance(budget,RecoveryBudget):
        raise ValueError('owned grid and explicit recovery budget required')
    ni=len(grid.station_cuts)-1
    if grid.free_dofs>budget.max_free_dofs or ni>min(budget.max_intervals,MAX_TERMS):
        raise ValueError('recovery state/interval inventory exceeds budget')
    active=max((len(ids) for ids in grid.trace_incidence),default=0)
    local=2*(grid.p+1)**2
    # Conservative symbolic-loop/storage estimates, not CPU/RSS guarantees.
    operations=ni*len(grid.rectangles)*256*(grid.p+3)**4+len(grid.rectangles)*local*(local+12)
    # Pose/resultant/density blocks, temporary density ownership, and twelve
    # lift actions (six interface and six residual actions) are all counted.
    retained=grid.free_dofs+ni*180+128
    workspace=(retained*768+budget.max_integer_bits//8+local*local*768+
               active*3*(grid.p+3)*768+budget.trace_budget.max_trace_integer_bits//8)
    if operations>budget.max_operations: raise ValueError('recovery operation estimate exceeds budget')
    if workspace>budget.max_work_bytes: raise ValueError('recovery workspace estimate exceeds budget')
    q=_vector(q,grid.free_dofs,budget.max_integer_bits)
    eta=_vector(eta,3,budget.max_integer_bits-sum(_bits(v) for v in q))
    stored=sum(_bits(v) for v in (*q,*eta,*grid.station_cuts))
    def retain(values):
        nonlocal stored
        for v in values:
            _rational(v);stored+=_bits(v)
            if stored>budget.max_integer_bits: raise ValueError('recovery aggregate integer budget exceeded')
    retain(())
    if stored>budget.max_integer_bits: raise ValueError('recovery aggregate integer budget exceeded')
    poses=[];resultants=[];densities=[]
    for i,(a,b) in enumerate(zip(grid.station_cuts,grid.station_cuts[1:])):
        trace=assembly.trace_interval(grid,i,budget.trace_budget);rows=[]
        for channel in trace.coefficients:
            poly=[Z]*6
            for index,coefficients in zip(trace.indices,channel):
                for k,coefficient in enumerate(coefficients):
                    poly[k]=_rational(poly[k]+q[int(index)]*coefficient)
            rows.append(tuple(poly))
        rows=tuple(rows);derivatives=tuple(_derivative(p,b-a) for p in rows)
        if poses:
            previous_h=a-grid.station_cuts[i-1]
            for before,after,da in zip(poses[-1],rows,derivatives):
                if _at(before,O)!=after[0] or _at(_derivative(before,previous_h),O)!=da[0]:
                    raise ArithmeticError('exact pose or first derivative discontinuity; internal atoms forbidden')
        stress=(_scale(derivatives[0],c.Q_EA),
                _scale(_add(derivatives[1],_scale(rows[2],-O)),c.Q_GAS),
                _scale(derivatives[2],c.Q_EI))
        density=(_derivative(stress[0],b-a),
                 _add(_derivative(stress[1],b-a),(c.Q_F0/c.Q_L0,)),
                 _add(_derivative(stress[2],b-a),stress[1]))
        for inventory in (rows,stress,density): retain(v for p in inventory for v in p)
        poses.append(rows);resultants.append(stress);densities.append(density)
    root=tuple(p[0] for p in resultants[0]);tip=tuple(_at(p,O) for p in resultants[-1])
    atoms=(tuple(v-e for v,e in zip(root,eta)),tuple(-v for v in tip))
    retain(v for atom in atoms for v in atom)
    interface=functional.Functional(grid.station_cuts,tuple(densities),
        (Z,c.Q_F0/(4*c.Q_L0),Z),atoms)
    sw=iw=actions=None
    if grid.p>=2:
        sw=_shell_lifts(grid,q)
        retain(sw);interface_actions=[];residual_actions=[]
        for side in ('left','right'):
            for channel in range(3):
                w=functional_work(interface,lift_pose(grid.station_cuts,side,channel))
                residual=Action(sw[len(interface_actions)])-w
                for action in (w,residual):
                    retain((action.rational,))
                    for a,b,p in action.cosine_terms: retain((a,b,*p))
                interface_actions.append(w);residual_actions.append(residual)
        iw=tuple(interface_actions);actions=tuple(residual_actions)
    result=object.__new__(Recovery)
    values=dict(q=q,eta=eta,cuts=grid.station_cuts,pose=tuple(poses),resultants=tuple(resultants),
        interface=interface,root_gap=tuple(p[0] for p in poses[0]),
        root_slope=_derivative(poses[0][1],grid.station_cuts[1])[0],
        tip_pose=tuple(_at(p,O) for p in poses[-1]),root_resultants=root,tip_resultants=tip,
        root_reaction=tuple(-v for v in eta),support_lift_actions=actions,
        shell_lift_work=sw,interface_lift_work=iw,
        diagnostics=MappingProxyType(dict(equilibrium_solves=0,factorizations=0,
            norm_evaluations=0,trace_intervals=ni,retained_integer_bits=stored,
            operation_estimate=operations,workspace_estimate_bytes=workspace,
            support_lifts='available_residual_actions' if grid.p>=2 else 'unavailable_p1',
            root_slope_constrained=False,physical_moment_scale='unscaled',gamma=c.Q_GAMMA)))
    for name,value in values.items(): object.__setattr__(result,name,value)
    return result
