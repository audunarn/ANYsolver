"""Synthetic exact local pad moments; no mesh, equilibrium or saved states."""
from dataclasses import FrozenInstanceError
from fractions import Fraction

import numpy as np
import pytest
from numpy.polynomial.legendre import leggauss

from scripts import _b3_e4_f03_local_moments as local
from scripts import _b3_e4_f03_spatial_contract as c


def _nodes(rect,p):
    return tuple((rect.x0+(rect.x1-rect.x0)*Fraction(i,p),
                  rect.y0+(rect.y1-rect.y0)*Fraction(j,p))
                 for j in range(p+1) for i in range(p+1))


def _rigid_q(rect,p,tx,ty,omega):
    nodes=_nodes(rect,p)
    return tuple(tx-omega*y for x,y in nodes)+tuple(
        ty+omega*x for x,y in nodes)


def _apply_exact(matrix,q):
    return tuple(sum((v*w for v,w in zip(row,q)),Fraction(0))
                 for row in matrix)


@pytest.mark.parametrize('p',[1,2,3])
def test_global_affine_rigid_gamma_and_physical_derivatives(p):
    rect=local.Rectangle(Fraction(-1,2),Fraction(3,2),
                         Fraction(-1,2),Fraction(1,2))
    assert local.station_events(rect)==(Fraction(0),Fraction(1))
    trace=local.trace_segment(rect,p,Fraction(0),Fraction(1))
    assert len(trace.coefficients)==3
    assert len(trace.coefficients[0])==2*(p+1)**2
    assert all(len(poly)==p+3 for row in trace.coefficients for poly in row)
    tx,ty,omega=Fraction(3,7),Fraction(-5,11),Fraction(2,13)
    q=_rigid_q(rect,p,tx,ty,omega)
    for station in (Fraction(0),Fraction(3,8),Fraction(1)):
        value=_apply_exact(trace.evaluate_exact(station),q)
        assert value==(tx,ty+omega*station,omega*c.Q_GAMMA)
        derivative=_apply_exact(trace.evaluate_exact(station,1),q)
        assert derivative==(Fraction(0),omega,Fraction(0))
        assert _apply_exact(trace.evaluate_exact(station,2),q)==(
            Fraction(0),)*3


def _lagrange_float(value,nodes,index):
    result=1.
    for j,other in enumerate(nodes):
        if j!=index: result*= (value-other)/(nodes[index]-other)
    return result


def test_direct_physical_rectangle_gauss_moments_and_signs():
    rect=local.Rectangle(Fraction(-1,10),Fraction(3,5),
                         Fraction(-2,5),Fraction(3,10))
    p=2;s=Fraction(1,3)
    events=local.station_events(rect)
    k=next(i for i in range(len(events)-1) if events[i]<s<events[i+1])
    segment=local.trace_segment(rect,p,events[k],events[k+1])
    tau=(s-segment.s0)/(segment.s1-segment.s0)
    q=np.array([(.3+index*.17)*1e-4 for index in range(segment.dof_count)])
    nodex=[float(rect.x0+(rect.x1-rect.x0)*Fraction(i,p)) for i in range(p+1)]
    nodey=[float(rect.y0+(rect.y1-rect.y0)*Fraction(j,p)) for j in range(p+1)]
    rule,weight=leggauss(8)
    direct=np.zeros(3)
    for l,r,yl,yh in c.PADS:
        xl=max(float(rect.x0),float(s+l));xh=min(float(rect.x1),float(s+r))
        ylo=max(float(rect.y0),float(yl));yhi=min(float(rect.y1),float(yh))
        if xl>=xh or ylo>=yhi: continue
        for ix,x_rule in enumerate(rule):
            x=(xl+xh+(xh-xl)*x_rule)/2
            for iy,y_rule in enumerate(rule):
                y=(ylo+yhi+(yhi-ylo)*y_rule)/2
                displ=np.zeros(2)
                for comp in (0,1):
                    for j in range(p+1):
                        for i in range(p+1):
                            dof=comp*(p+1)**2+j*(p+1)+i
                            displ[comp]+=q[dof]*_lagrange_float(x,nodex,i)*(
                                _lagrange_float(y,nodey,j))
                w=weight[ix]*weight[iy]*(xh-xl)*(yhi-ylo)/(4*float(c.Q_AREA))
                direct+=w*np.array((displ[0],displ[1],
                                     ((x-float(s))*displ[1]-y*displ[0])/c.J))
    actual=segment.evaluate(float(tau))@q
    np.testing.assert_allclose(actual,direct,rtol=2e-13,atol=2e-17)


def test_two_cell_continuous_field_pose_and_first_derivative_at_event():
    left=local.Rectangle(Fraction(-1,2),Fraction(1,2),
                         Fraction(-1,2),Fraction(1,2))
    right=local.Rectangle(Fraction(1,2),Fraction(3,2),
                          Fraction(-1,2),Fraction(1,2))
    event=Fraction(1,2)-(c.Q_DX+c.Q_A)
    events=tuple(sorted(set(local.station_events(left)+local.station_events(right))))
    k=events.index(event)
    assert 0<k<len(events)-1
    tx,ty,omega=Fraction(1,5),Fraction(-2,7),Fraction(3,11)
    qleft=_rigid_q(left,1,tx,ty,omega)
    qright=_rigid_q(right,1,tx,ty,omega)
    for order in (0,1):
        before=tuple(sum(terms,Fraction(0)) for terms in zip(
            _apply_exact(local.trace_segment(left,1,events[k-1],event
                 ).evaluate_exact(Fraction(1),order),qleft),
            _apply_exact(local.trace_segment(right,1,events[k-1],event
                 ).evaluate_exact(Fraction(1),order),qright)))
        after=tuple(sum(terms,Fraction(0)) for terms in zip(
            _apply_exact(local.trace_segment(left,1,event,events[k+1]
                 ).evaluate_exact(Fraction(0),order),qleft),
            _apply_exact(local.trace_segment(right,1,event,events[k+1]
                 ).evaluate_exact(Fraction(0),order),qright)))
        target=((tx,ty+omega*event,omega*c.Q_GAMMA) if order==0 else
                (Fraction(0),omega,Fraction(0)))
        assert before==after==target


def test_distinct_rational_events_collapsed_binary64_local_chart():
    first=2*(c.Q_DX+c.Q_A)
    second=1-first
    lo,hi=sorted((first,second))
    assert lo<hi and float(lo)==float(hi)
    l,r,yl,yh=c.PADS[0]
    rect=local.Rectangle(lo+r,hi+r,yl,yh)
    events=local.station_events(rect)
    assert lo in events and hi in events
    index=events.index(lo)
    assert events[index+1]==hi
    segment=local.trace_segment(rect,1,lo,hi)
    q=(Fraction(1),)*4+(Fraction(0),)*4
    for tau in (Fraction(1,4),Fraction(3,4)):
        actual=_apply_exact(segment.evaluate_exact(tau),q)
        assert actual[0]==(hi-lo)*tau*(2*c.Q_A)/c.Q_AREA
        assert _apply_exact(segment.evaluate_exact(tau,1),q)[0]==(
            2*c.Q_A)/c.Q_AREA
        assert _apply_exact(segment.evaluate_exact(tau,2),q)[0]==0
    assert np.all(np.isfinite(segment.evaluate(.25,1)))
    with pytest.raises(ValueError,match='interior exact'):
        local.trace_segment(rect,1,lo-Fraction(1,100),hi)


def test_immutable_ownership_and_rejections():
    rect=local.Rectangle(Fraction(0),Fraction(1),
                         Fraction(-1,2),Fraction(1,2))
    events=local.station_events(rect)
    segment=local.trace_segment(rect,3,events[0],events[1])
    first=segment.evaluate(np.array([.2,.8]));first[...,0,0]=123.
    assert not np.any(segment.evaluate(np.array([.2,.8]))[...,0,0]==123.)
    with pytest.raises(FrozenInstanceError): rect.x0=Fraction(1,10)
    with pytest.raises(TypeError): segment.coefficients[0][0][0]=Fraction(1)
    with pytest.raises(ValueError):
        local.Rectangle(Fraction(1,2),Fraction(1,2),Fraction(0),Fraction(1))
    with pytest.raises(ValueError): local.trace_segment(rect,True,events[0],events[1])
    with pytest.raises(ValueError): local.trace_segment(rect,4,events[0],events[1])
    with pytest.raises(ValueError): local.trace_segment(rect,1,events[0],events[-1])
    with pytest.raises(ValueError): segment.evaluate(float('nan'))
    with pytest.raises(ValueError): segment.evaluate_exact(Fraction(1,2),True)


def test_direct_localtrace_constructor_defensively_copies_and_validates():
    rect=local.Rectangle(Fraction(-1,2),Fraction(3,2),
                         Fraction(-1,2),Fraction(1,2))
    rows=[[[Fraction(0) for _ in range(4)] for _ in range(8)]
          for _ in range(3)]
    rows[0][0][0]=Fraction(3,7)
    direct=local.LocalTrace(rect,1,Fraction(0),Fraction(1),rows)
    rows[0][0][0]=Fraction(9)
    rows[0][0].append(Fraction(0))
    rows.append([])
    assert direct.coefficients[0][0][0]==Fraction(3,7)
    assert isinstance(direct.coefficients,tuple)
    assert isinstance(direct.coefficients[0][0],tuple)
    with pytest.raises(ValueError,match='channel layout'):
        local.LocalTrace(rect,1,Fraction(0),Fraction(1),rows)
    bad=[[[Fraction(0) for _ in range(4)] for _ in range(8)]
         for _ in range(3)]
    bad[2][4][3]=0.
    with pytest.raises(ValueError,match='coefficients'):
        local.LocalTrace(rect,1,Fraction(0),Fraction(1),bad)
    bad[2][4][3]=Fraction(0)
    with pytest.raises(ValueError,match='DOF layout'):
        local.LocalTrace(rect,1,Fraction(0),Fraction(1),[bad[0][:-1],*bad[1:]])
    with pytest.raises(ValueError,match='domain'):
        local.LocalTrace(rect,True,Fraction(0),Fraction(1),bad)
    with pytest.raises(ValueError,match='domain'):
        local.LocalTrace(rect,1,Fraction(1),Fraction(0),bad)
    split=local.Rectangle(Fraction(0),Fraction(1),
                          Fraction(-1,2),Fraction(1,2))
    with pytest.raises(ValueError,match='interior exact'):
        local.LocalTrace(split,1,Fraction(0),Fraction(1),bad)
def test_exact_coordinate_and_trace_coefficient_resource_bounds():
    from fractions import Fraction as F
    from scripts import _b3_e4_f03_local_moments as m
    with pytest.raises(ValueError,match='rectangle'):
        m.Rectangle(F(0),F(1,2**256),F(0),F(1,4))
    rect=m.Rectangle(F(-1,2),F(3,2),F(-1,2),F(1,2))
    with pytest.raises(ValueError):
        m.trace_segment(rect,1,F(0),F(1,2**256))
    a,b=m.station_events(rect)[:2]
    trace=m.trace_segment(rect,1,a,b)
    rows=[[list(v) for v in channel] for channel in trace.coefficients]
    rows[0][0][0]=F(2**8192)
    with pytest.raises(ValueError,match='storage bound'):
        m.LocalTrace(rect,1,a,b,rows)
    odd=(1<<254)+1
    bounded=m.Rectangle(F(1,odd),F(1),F(-1,4),F(1,4))
    with pytest.raises(ValueError,match='derived exact station'):
        m.station_events(bounded)


def test_cubic_trace_and_both_derivatives_against_analytic_pad_moments():
    rect=local.Rectangle(Fraction(-1,2),Fraction(3,2),Fraction(-1,2),Fraction(1,2))
    nodes=_nodes(rect,3);q=(Fraction(0),)*len(nodes)+tuple(x**3 for x,y in nodes)
    trace=local.trace_segment(rect,3,Fraction(0),Fraction(1))
    m2=c.Q_DX**2+c.Q_A**2/3
    m4=c.Q_DX**4+2*c.Q_DX**2*c.Q_A**2+c.Q_A**4/5
    for s in (Fraction(0),Fraction(2,7),Fraction(1)):
        targets=((Fraction(0),s**3+3*s*m2,(3*s*s*m2+m4)/c.Q_J),
                 (Fraction(0),3*s*s+3*m2,6*s*m2/c.Q_J),
                 (Fraction(0),6*s,6*m2/c.Q_J))
        for order,target in enumerate(targets):
            assert _apply_exact(trace.evaluate_exact(s,order),q)==target
