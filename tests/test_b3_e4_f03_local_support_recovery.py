"""Manufactured supplemental support work only; no equilibrium solve."""
from dataclasses import replace
from fractions import Fraction as F

import pytest

from scripts import _b3_e4_f03_local_support_recovery as support
from scripts import _b3_e4_f03_local_recovery as rec
from scripts import _b3_e4_f03_local_grid as grid
from scripts import _b3_e4_f03_local_primal_assembly as assembly
from scripts import _b3_e4_f03_spatial_contract as c


Z=F(0);O=F(1)
RB=rec.RecoveryBudget(assembly.AssemblyBudget(512,1,128*1024**2,8_000_000),
                      1024,128,8_000_000,256*1024**2,1_000_000_000)
BUDGET=support.SupportBudget(RB,1024,128,1_000_000_000,80_000_000,
                             256*1024**2)
ETA=(F(7),F(-11),F(13))


def _model(p):
    return grid.compile_grid((F(-1,2),F(1,2),F(3,2)),
                             (F(-1,2),Z,F(1,2)),p)


def _state(g):
    nx=len(g.x_nodes);nc=nx*len(g.y_nodes)
    q=[]
    for index in g.free_to_full:
        component,node=divmod(int(index),nc);y,x=divmod(node,nx)
        q.append(F((component+2)*(x+1)*(y+3),10**7))
    q=tuple(q)
    return q,rec.recover(g,q,ETA,RB)


def _direct_q1_pad_pose(side,s):
    e=(-F(1,2),F(3,2))[side]
    a,b=((F(3,4),-F(1,2)),(F(1,4),F(1,2)))[side]
    # Integrate the globally Q1 nodal interpolant z=(-y phi,e phi)
    # independently over all four represented squares.
    area=c.Q_AREA
    ux=uy=yaw=Z
    for cx,cy in ((-c.Q_DX,-c.Q_DY),(c.Q_DX,-c.Q_DY),
                  (c.Q_DX,c.Q_DY),(-c.Q_DX,c.Q_DY)):
        xl=s+cx-c.Q_A;xr=s+cx+c.Q_A
        yl=cy-c.Q_A;yr=cy+c.Q_A
        integral_phi=(a*(xr-xl)+b*(xr*xr-xl*xl)/2)
        integral_xphi=(a*(xr*xr-xl*xl)/2+b*(xr**3-xl**3)/3)
        integral_y=(yr*yr-yl*yl)/2
        integral_y2=(yr**3-yl**3)/3
        ux-=integral_phi*integral_y/area
        uy+=e*integral_phi*(yr-yl)/area
        yaw+=(e*(integral_xphi-s*integral_phi)*(yr-yl)+
              integral_phi*integral_y2)/(area*c.Q_J)
    return (ux,uy,yaw)


def test_q1_rotation_is_true_nodal_lift_and_direct_pad_pose():
    g=_model(1)
    for side in (0,1):
        e=(-F(1,2),F(3,2))[side]
        for x in g.x_nodes:
            for y in g.y_nodes:
                z=support._nodal_lift(x,y,side,2,1)
                assert z==(-y*((F(3,2)-x)/2 if side==0 else (x+F(1,2))/2),
                           e*((F(3,2)-x)/2 if side==0 else (x+F(1,2))/2))
                if x==e:assert z==(-y,x)
                if x==O-e:assert z==(Z,Z)
        rows=support.lift_pose(g.station_cuts,('left','right')[side],2,1)
        for s in (Z,F(1,8),F(3,8),F(7,8),O):
            index=min((i for i,(a,b) in enumerate(zip(g.station_cuts,g.station_cuts[1:]))
                       if a<=s<=b),default=len(rows)-1)
            a,b=g.station_cuts[index:index+2]
            actual=tuple(rec._at(poly,(s-a)/(b-a)) for poly in rows[index])
            assert actual==_direct_q1_pad_pose(side,s)
    for x in g.x_nodes:
        for y in g.y_nodes:
            assert tuple(sum(support._nodal_lift(x,y,side,2,1)[k]
                             for side in (0,1)) for k in (0,1))==(-y,x)
    # Independently reconstruct a genuinely bilinear interior Q1 cell from
    # all four nodal values, rather than only comparing a symbolic formula.
    x=F(1,8);y=F(1,8);xl=F(-1,2);xr=F(1,2);yb=Z;yt=F(1,2)
    for side in (0,1):
        interpolated=[]
        for component in (0,1):
            interpolated.append(sum(
                support._nodal_lift(xnode,ynode,side,2,1)[component]*
                ((xr-x)/(xr-xl) if xnode==xl else (x-xl)/(xr-xl))*
                ((yt-y)/(yt-yb) if ynode==yb else (y-yb)/(yt-yb))
                for xnode in (xl,xr) for ynode in (yb,yt)))
        assert tuple(interpolated)==support._nodal_lift(x,y,side,2,1)


@pytest.mark.parametrize('p',(1,2,3))
def test_dual_routes_shift_and_actual_represented_balances(p):
    g=_model(p);q,value=_state(g)
    result=support.support_recovery(g,value,BUDGET)
    assert result.q==q and result.eta==ETA
    if p==1:assert value.support_lift_actions is None
    else:assert result.route2==value.support_lift_actions
    assert all(v==rec.Action(Z) for v in result.route_difference)
    assert all(v==rec.Action(Z) for v in result.shift_binding_defects)
    assert result.shift_route1_delta==result.first_free_route1_residual
    assert result.shift_route2_delta==result.first_free_route2_residual
    assert result.first_free_route1_residual!=rec.Action(Z)
    assert result.force_balance_actual==(rec.Action(Z),rec.Action(Z))
    assert result.represented_moment_identity==rec.Action(Z)
    assert result.physical_moment_defect==result.predicted_physical_moment_defect
    qintegral=sum(((b-a)*rec._product_integral(row[1],(O,))
                  for a,b,row in zip(value.cuts,value.cuts[1:],value.resultants)),Z)
    assert result.rigid_yaw_functional==rec.Action(qintegral-ETA[2])
    assert result.diagnostics['equilibrium_solves']==0
    assert result.diagnostics['decimal_acceptance_evaluations']==0
    if p>=2:
        assert result.shell_work==value.shell_lift_work
        assert result.interface_work==value.interface_lift_work


def test_frequency_actual_nominal_difference_and_signed_moment_defect():
    g=_model(1);_,value=_state(g)
    result=support.support_recovery(g,value,BUDGET)
    assert result.actual_load[0]-result.nominal_load[0]==result.load_actual_minus_nominal[0]
    assert result.actual_load[1]-result.nominal_load[1]==result.load_actual_minus_nominal[1]
    assert result.load_actual_minus_nominal[0]!=rec.Action(Z)
    assert c.Q_GAMMA!=O
    assert result.physical_moment_defect!=rec.Action(Z)
    assert result.force_balance_nominal[1]==result.nominal_load[0]-result.actual_load[0]


def test_mismatched_grid_and_budget_reject_before_lift_work(monkeypatch):
    g=_model(1);_,value=_state(g)
    other=grid.compile_grid((F(-1,2),F(1,4),F(3,2)),
                            (F(-1,2),Z,F(1,2)),1)
    with pytest.raises(ValueError):support.support_recovery(other,value,BUDGET)
    same_stations=grid.compile_grid(g.x_cuts,
                                    (F(-1,2),F(1,4),F(1,2)),1)
    assert same_stations.station_cuts==g.station_cuts
    assert same_stations.free_dofs==g.free_dofs
    with pytest.raises(ValueError,match='does not bind'):
        support.support_recovery(same_stations,value,BUDGET)
    def forbidden(*args,**kwargs):
        pytest.fail('expensive factory entered after failed preflight')
    monkeypatch.setattr(rec,'recover',forbidden)
    for changes in (dict(max_free_dofs=1),dict(max_intervals=1),
                    dict(max_operations=1),dict(max_work_bytes=1)):
        with pytest.raises(ValueError):support.support_recovery(g,value,replace(BUDGET,**changes))


def test_public_lift_and_first_hat_preflight_guards():
    g=_model(1)
    for cuts in (iter(g.station_cuts),(Z,),tuple([Z]*2050)):
        with pytest.raises(ValueError):support.lift_pose(cuts,'left',2,1)
    for channel in (2.0,-1,3):
        with pytest.raises(ValueError):support.lift_pose(g.station_cuts,'left',channel,1)
    single=grid.compile_grid((F(-1,2),F(3,2)),(F(-1,2),F(1,2)),1)
    assert single.free_dofs==0
    value=rec.recover(single,(),ETA,RB)
    with pytest.raises(ValueError,match='first free-coordinate'):
        support.support_recovery(single,value,BUDGET)


def test_symbolic_storage_cap_rejects_before_action_construction(monkeypatch):
    g=_model(1);_,value=_state(g)
    def forbidden(*args,**kwargs):
        pytest.fail('symbolic Action constructed after failed storage preflight')
    monkeypatch.setattr(rec,'Action',forbidden)
    with pytest.raises(ValueError,match='symbolic storage'):
        support.support_recovery(g,value,replace(BUDGET,max_integer_bits=1))


def test_result_owns_input_and_constructor_is_closed():
    g=_model(1)
    q=[Z]*g.free_dofs
    value=rec.recover(g,q,ETA,RB)
    result=support.support_recovery(g,value,BUDGET)
    q[0]=F(999)
    assert result.q==(Z,)*g.free_dofs
    with pytest.raises(TypeError):support.SupportResult()
    with pytest.raises(TypeError):result.diagnostics['equilibrium_solves']=1
