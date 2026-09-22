"""Exact-rational Bernstein bounds for classical F03 gap fields.

Each stored finite binary input is interpreted as an exact rational number.
The piecewise polynomial FE field is reconstructed from those inputs rather
than from floating station sampling. This remains preflight until its
full-inventory resource cost and physical normalization are reviewed.
"""

from __future__ import annotations

from bisect import bisect_right
from fractions import Fraction
import math

import numpy as np

import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_line as line
import _b3_e4_f03_independent_shell as shell


def _r(value: float) -> Fraction:
    return Fraction.from_float(float(value))


def _axes(model: shell.Panel) -> tuple[tuple[Fraction,...],tuple[Fraction,...]]:
    nx=2*model.n_s
    xs=tuple(_r(model.nodes[i,0]) for i in range(nx+1))
    ys=tuple(_r(model.nodes[j*(nx+1),1]) for j in range(model.n_y+1))
    return xs,ys


def _host(model: shell.Panel, s: Fraction, offset: tuple[float,float],
          axes: tuple[tuple[Fraction,...],tuple[Fraction,...]]
          ) -> tuple[int,...]:
    """Host of the rational piecewise FE interpolant on stored node axes."""
    xs,ys=axes
    x=s+_r(offset[0]); y=_r(offset[1])
    if not xs[0]<=x<=xs[-1] or not ys[0]<=y<=ys[-1]:
        raise ValueError('rational sample outside panel')
    i=min(max(bisect_right(xs,x)-1,0),len(xs)-2)
    j=min(max(bisect_right(ys,y)-1,0),len(ys)-2)
    nx=2*model.n_s
    bl=j*(nx+1)+i; br=bl+1; tl=bl+nx+1; tr=tl+1
    if model.topology=='Q4':
        return bl,br,tr,tl
    dx=xs[i+1]-xs[i]; dy=ys[j+1]-ys[j]
    if model.topology=='CST-CB' and (i+j)%2:
        lower=(x-xs[i])*dy+(y-ys[j])*dx <= dx*dy
        return (bl,br,tl) if lower else (br,tr,tl)
    lower=(x-xs[i])*dy >= (y-ys[j])*dx
    return (bl,br,tr) if lower else (bl,tr,tl)


def exact_overlay(model: shell.Panel, n_beam: int, n_mortar: int
                  ) -> tuple[Fraction,...]:
    """All exact branches of the rational field, including CST diagonals."""
    beam.dof_count(n_beam)
    if not isinstance(n_mortar,int) or not 1<=n_mortar<=128:
        raise ValueError('unsupported exact mortar resolution')
    xs,ys=_axes(model)
    knots={Fraction(0),Fraction(1)}
    knots.update(Fraction(i,n_beam) for i in range(1,n_beam))
    knots.update(Fraction(i,n_mortar) for i in range(1,n_mortar))
    for offset in shell.OFFSETS:
        dx=_r(offset[0]); y=_r(offset[1])
        j=min(max(bisect_right(ys,y)-1,0),len(ys)-2)
        for x in xs:
            knots.add(x-dx)
        if model.topology in ('CST','CST-CB'):
            for i,(x0,x1) in enumerate(zip(xs[:-1],xs[1:])):
                fraction=(y-ys[j])/(ys[j+1]-ys[j])
                if model.topology=='CST-CB' and (i+j)%2:
                    fraction=1-fraction
                crossing=x0+fraction*(x1-x0)
                knots.add(crossing-dx)
    ordered=tuple(sorted(k for k in knots if 0<=k<=1))
    for a,b in zip(ordered[:-1],ordered[1:]):
        reference=tuple(_host(model,(a+b)/2,o,(xs,ys))
                        for o in shell.OFFSETS)
        for t in (Fraction(1,8),Fraction(1,4),Fraction(3,4),Fraction(7,8)):
            if any(_host(model,a+(b-a)*t,o,(xs,ys))!=host
                   for o,host in zip(shell.OFFSETS,reference)):
                raise ValueError('exact overlay misses a shell host transition')
        if (min(int(((a+b)/2)*n_beam),n_beam-1)!=
                min(int((a+(b-a)/8)*n_beam),n_beam-1)):
            raise ValueError('exact overlay misses a beam transition')
    return ordered


def _shell_pose(model: shell.Panel, s: Fraction,
                q: tuple[Fraction,...], hosts: tuple[tuple[int,...],...]
                ) -> tuple[Fraction,Fraction,Fraction]:
    total_x=total_y=yaw=Fraction(0)
    denominator=_r(shell.YAW_DENOMINATOR)
    for (dx,dy),indices in zip(shell.OFFSETS,hosts):
        x=s+_r(dx); y=_r(dy)
        nodes=[(_r(model.nodes[i,0]),_r(model.nodes[i,1])) for i in indices]
        if model.topology=='Q4':
            x0,y0=nodes[0]; x1=nodes[1][0]; y1=nodes[2][1]
            fx=(x-x0)/(x1-x0); fy=(y-y0)/(y1-y0)
            weights=((1-fx)*(1-fy),fx*(1-fy),fx*fy,(1-fx)*fy)
        else:
            (x0,y0),(x1,y1),(x2,y2)=nodes
            det=(x1-x0)*(y2-y0)-(y1-y0)*(x2-x0)
            w1=((x-x0)*(y2-y0)-(y-y0)*(x2-x0))/det
            w2=((x1-x0)*(y-y0)-(y1-y0)*(x-x0))/det
            weights=(1-w1-w2,w1,w2)
        ux=sum((w*q[2*i] for i,w in zip(indices,weights)),Fraction(0))
        uy=sum((w*q[2*i+1] for i,w in zip(indices,weights)),Fraction(0))
        total_x+=ux/4; total_y+=uy/4
        yaw+=(-_r(dy)*ux+_r(dx)*uy)/denominator
    return total_x,total_y,yaw


def _beam_pose(n: int, s: Fraction, q: tuple[Fraction,...],
               index: int) -> tuple[Fraction,Fraction,Fraction]:
    xi=s*n-index
    length=_r(1/n)
    p=(2*(xi-Fraction(1,2))*(xi-1),4*xi*(1-xi),
       2*xi*(xi-Fraction(1,2)))
    h=(1-3*xi*xi+2*xi**3,
       length*(xi-2*xi*xi+xi**3),
       3*xi*xi-2*xi**3,
       length*(-xi*xi+xi**3))
    ids=beam.element_dofs(n,index)
    u=sum((w*q[int(i)] for w,i in zip(p,ids[:3])),Fraction(0))
    v=sum((w*q[int(i)] for w,i in zip(h,ids[3:7])),Fraction(0))
    theta=sum((w*q[int(i)] for w,i in zip(p,ids[7:])),Fraction(0))
    return u,v,theta


def _bernstein(values: tuple[Fraction,...]) -> tuple[Fraction,...]:
    """Four cubic values at t=0,1/3,2/3,1 to Bernstein coefficients."""
    a,d=values[0],values[3]
    u=27*values[1]-8*a-d
    v=27*values[2]-a-8*d
    return (a,(2*u-v)/18,(2*v-u)/18,d)


def _subdivide(b: tuple[Fraction,...]
               ) -> tuple[tuple[Fraction,...],tuple[Fraction,...]]:
    a=(b[0]+b[1])/2; c=(b[1]+b[2])/2; d=(b[2]+b[3])/2
    e=(a+c)/2; f=(c+d)/2; m=(e+f)/2
    return (b[0],a,e,m),(m,f,d,b[3])


def gap_bounds(model: shell.Panel, n_beam: int, n_mortar: int,
               qs: np.ndarray, qb: np.ndarray, depth: int = 8
               ) -> tuple[tuple[float,float],...]:
    """Exact-field absolute component lower/upper bounds, outward floats.

    Lower bounds are attained endpoint/midpoint values; upper bounds use the
    convex hull of Bernstein coefficients. Branches whose upper bound is
    already below an attained global value need no further subdivision.
    """
    if (model.n_s>128 or model.n_y>64 or n_beam>512 or n_mortar>128 or
            not isinstance(depth,int) or not 0<=depth<=12 or
            np.shape(qs)!=(model.dof_count,) or
            np.shape(qb)!=(beam.dof_count(n_beam),) or
            not np.all(np.isfinite(qs)) or not np.all(np.isfinite(qb))):
        raise ValueError('unsupported exact-rational preflight gap')
    q_shell=tuple(map(_r,qs)); q_beam=tuple(map(_r,qb))
    lower=[Fraction(0)]*3; upper=[Fraction(0)]*3
    knots=exact_overlay(model,n_beam,n_mortar)
    axes=_axes(model)
    for left,right in zip(knots[:-1],knots[1:]):
        a=left; b=right
        midpoint=(a+b)/2
        hosts=tuple(_host(model,midpoint,offset,axes)
                    for offset in shell.OFFSETS)
        index=min(int(midpoint*n_beam),n_beam-1)
        samples=[[],[],[]]
        for t in (Fraction(0),Fraction(1,3),Fraction(2,3),Fraction(1)):
            s=a+(b-a)*t
            ps=_shell_pose(model,s,q_shell,hosts)
            pb=_beam_pose(n_beam,s,q_beam,index)
            gap=(pb[0]-ps[0],pb[1]-ps[1],
                 _r(line.YAW_LENGTH)*(pb[2]-ps[2]))
            for channel in range(3):
                samples[channel].append(gap[channel])
        for channel in range(3):
            coefficients=_bernstein(tuple(samples[channel]))
            pending=[(coefficients,0)]
            while pending:
                segment,level=pending.pop()
                lower[channel]=max(lower[channel],abs(segment[0]),
                                   abs(segment[3]))
                bound=max(abs(min(segment)),abs(max(segment)))
                if bound<=lower[channel]:
                    continue
                if level<depth:
                    left,right=_subdivide(segment)
                    pending.append((left,level+1))
                    pending.append((right,level+1))
                else:
                    upper[channel]=max(upper[channel],bound)
    upper=[max(lo,hi) for lo,hi in zip(lower,upper)]
    result=[]
    for lo,hi in zip(lower,upper):
        try:
            low=float(lo); high=float(hi)
        except OverflowError as exc:
            raise ValueError('rational gap bound exceeds finite output range') from exc
        if not math.isfinite(low) or not math.isfinite(high):
            raise ValueError('rational gap bound exceeds finite output range')
        outward_high=math.nextafter(high,math.inf)
        if not math.isfinite(outward_high):
            raise ValueError('outward rational gap bound exceeds finite output range')
        result.append((max(0.,math.nextafter(low,-math.inf)),outward_high))
    return tuple(result)
