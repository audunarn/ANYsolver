"""Bounded manufactured recovery only; no physical equilibrium states."""
from dataclasses import replace
from decimal import Decimal, localcontext
from fractions import Fraction as F
import math

import numpy as np
import pytest

from scripts import _b3_e4_f03_local_recovery as r
from scripts import _b3_e4_f03_local_grid as grid
from scripts import _b3_e4_f03_local_primal_assembly as assembly
from scripts import _b3_e4_f03_local_functional as functional
from scripts import _b3_e4_f03_local_work_oracle as oracle
from scripts import _b3_e4_f03_spatial_contract as c

Z=F(0);O=F(1)
BUDGET=r.RecoveryBudget(assembly.AssemblyBudget(512,1,128*1024**2,8_000_000),
                       1024,128,8_000_000,256*1024**2,1_000_000_000)
ETA=(F(7),F(-11),F(13))
ALPHA=F(2,10**6);BETA=F(3,10**6);GAMMA=F(-5,10**6);DELTA=F(7,10**6)


def model(p=2):
    return grid.compile_grid((F(-1,2),F(1,2),F(3,2)),(F(-1,2),Z,F(1,2)),p)


def field(x,y):
    bubble=O-(x-F(1,2))**2
    return (bubble*(ALPHA+BETA*y),bubble*(GAMMA+DELTA*y))


def vector(g,fn=field):
    nx=len(g.x_nodes);nc=nx*len(g.y_nodes);values=[]
    for index in g.free_to_full:
        component,node=divmod(int(index),nc);j,i=divmod(node,nx)
        values.append(fn(g.x_nodes[i],g.y_nodes[j])[component])
    return tuple(values)


@pytest.fixture(scope='module')
def recovered():
    g=model();return g,r.recover(g,vector(g),ETA,BUDGET)


def local_rows(cuts,global_rows):
    out=[]
    for a,b in zip(cuts,cuts[1:]):
        row=[]
        for p in global_rows:
            row.append(tuple(sum((v*math.comb(k,j)*a**(k-j)*(b-a)**j
                        for k,v in enumerate(p) if k>=j),Z) for j in range(6)))
        out.append(tuple(row))
    return tuple(out)


def test_exact_separable_pose_derivatives_resultants_and_signed_atoms(recovered):
    _,value=recovered;xx=c.Q_DX**2+c.Q_A**2/3;yy=c.Q_DY**2+c.Q_A**2/3
    for s in (Z,F(1,3),O):
        t=s-F(1,2);B=O-t*t-xx
        theta=(-2*GAMMA*t*xx-BETA*yy*B)/c.Q_J
        dtheta=(-2*GAMMA*xx+2*BETA*yy*t)/c.Q_J
        ddtheta=2*BETA*yy/c.Q_J
        assert r.station(value,s)==(ALPHA*B,GAMMA*B,theta)
        assert r.station(value,s,order=1)==(-2*ALPHA*t,-2*GAMMA*t,dtheta)
        assert r.station(value,s,order=2)==(-2*ALPHA,-2*GAMMA,ddtheta)
        expected=(c.Q_EA*(-2*ALPHA*t),c.Q_GAS*(-2*GAMMA*t-theta),c.Q_EI*dtheta)
        assert r.station(value,s,resultants=True)==expected
    assert value.interface.atoms[0]==tuple(v-e for v,e in zip(value.root_resultants,ETA))
    assert value.interface.atoms[1]==tuple(-v for v in value.tip_resultants)
    assert value.root_reaction==tuple(-e for e in ETA)
    assert tuple(-v+a for v,a in zip(value.root_resultants,value.interface.atoms[0]))==value.root_reaction
    assert value.root_slope==GAMMA!=0
    assert any(value.root_gap)
    assert value.interface.cosine==(Z,c.Q_F0/(4*c.Q_L0),Z)


def test_free_endpoint_virtual_work_and_atom_omission_is_visible(recovered):
    _,value=recovered
    test=local_rows(value.cuts,((O,Z,O),(F(2),-O,Z,O),(F(3),F(4))))
    assert r.virtual_work_defect(value,test)==r.Action(Z)
    missing=functional.Functional(value.cuts,value.interface.coefficients,value.interface.cosine,
                                  (value.interface.atoms[0],(Z,Z,Z)))
    omitted=r.functional_work(missing,test)-r.functional_work(value.interface,test)
    expected=-sum((v*sum(p) for v,p in zip(value.interface.atoms[1],test[-1])),Z)
    assert omitted==r.Action(expected)
    assert expected!=0


def test_piecewise_q1_has_no_internal_atoms_and_keeps_exact_collapsed_events():
    g=grid.compile_grid(c.X_CUTS,c.Y_CUTS,1)
    q=tuple(F((i%7)-3,10**6) for i in range(g.free_dofs))
    value=r.recover(g,q,ETA,BUDGET)
    assert len(value.interface.atoms)==2
    assert any(float(a)==float(b) and a<b for a,b in zip(value.cuts,value.cuts[1:]))
    for s in value.cuts[1:-1]:
        assert r.station(value,s,side='left')==r.station(value,s,side='right')
        assert r.station(value,s,order=1,side='left')==r.station(value,s,order=1,side='right')
        assert r.station(value,s,resultants=True,side='left')==r.station(value,s,resultants=True,side='right')
    assert value.support_lift_actions is None
    assert value.diagnostics['support_lifts']=='unavailable_p1'
    test=local_rows(value.cuts,((O,O),(O,Z,O),(Z,O)))
    assert r.virtual_work_defect(value,test)==r.Action(Z)


def test_bands_include_two_external_atoms_once_with_origin_lever_arm(recovered):
    _,value=recovered
    constant=local_rows(value.cuts,((O,),(Z,),(Z,)))
    transverse=local_rows(value.cuts,((Z,),(O,),(Z,)))
    origin=local_rows(value.cuts,((Z,),(Z,O),(O,)))
    whole=r.band(value,Z,O)
    for result,test in zip(whole,(constant,transverse,origin)):
        assert result==r.functional_work(value.interface,test)
    quarters=[r.band(value,F(i,4),F(i+1,4)) for i in range(4)]
    # Symbolic integrals on different partitions have the same rational part
    # and Decimal values. No false equality between distinct symbolic charts.
    for j in range(3):
        combined=sum((part[j].rational for part in quarters),Z)
        assert combined==whole[j].rational
        with localcontext() as ctx:
            ctx.prec=70
            error=sum((part[j].decimal_value() for part in quarters),Decimal(0))-whole[j].decimal_value()
            assert abs(error)<Decimal('1e-55')


def test_panel_lift_shell_work_matches_independent_exact_oracle(recovered):
    _,value=recovered
    u=oracle.Patch.sample(2,field)
    no_load=oracle.Load((Z,Z,Z),((Z,Z,Z),(Z,Z,Z)))
    for side in range(2):
        for channel in range(3):
            def lift(x,y):
                phi=(F(3,2)-x)/2 if side==0 else (x+F(1,2))/2
                motion=((O,Z),(Z,O),(-y,x))[channel]
                return tuple(phi*v for v in motion)
            work=oracle.work_identity(u,oracle.Patch.sample(2,lift),no_load)
            index=side*3+channel
            assert value.shell_lift_work[index]==work['strain_work']
            assert value.support_lift_actions[index]==r.Action(work['strain_work'])-value.interface_lift_work[index]
    for channel in range(3):
        assert value.shell_lift_work[channel]+value.shell_lift_work[channel+3]==0


def test_constant_density_and_atoms_against_independent_spatial_work_oracle():
    g=model();value=r.recover(g,(Z,)*g.free_dofs,ETA,BUDGET)
    load=oracle.Load((Z,c.Q_F0/c.Q_L0,Z),value.interface.atoms)
    zero=oracle.Patch.sample(2,lambda x,y:(Z,Z))
    for side in range(2):
        for channel in range(3):
            def lift(x,y):
                phi=(F(3,2)-x)/2 if side==0 else (x+F(1,2))/2
                return tuple(phi*v for v in ((O,Z),(Z,O),(-y,x))[channel])
            result=oracle.work_identity(zero,oracle.Patch.sample(2,lift),load)
            index=side*3+channel
            # Oracle is constant-density only; compare that exact component.
            assert value.interface_lift_work[index].rational==result['direct_pad_work']
            assert value.support_lift_actions[index].rational==result['reaction_work']
    rigid_moment=value.interface_lift_work[2]+value.interface_lift_work[5]
    assert rigid_moment.rational==c.Q_F0/2-c.Q_GAMMA*ETA[2]
    assert c.Q_GAMMA!=O


def test_action_owns_inputs_and_decimal_uses_local_positive_interval():
    tiny=F(1,10**70);left=F(1,2);right=left+tiny
    assert float(left)==float(right)
    term=[left,right,[O/tiny]]
    action=r.Action(Z,[term]);term[2][0]=Z
    with localcontext() as ctx:
        ctx.prec=70
        assert abs(action.decimal_value()+Decimal(1))<Decimal('1e-29')
    assert action+-action==r.Action(Z)
    assert r.Action(F(-3)).decimal_value()==Decimal(-3)
    with pytest.raises(ValueError): r.Action(Z,[(Z,O,[F(1,1<<4097)])])
    with pytest.raises(ValueError): r.Action(Z,[(Z,Z,[O])])


def test_owned_result_float_bits_and_invalid_inventory(recovered):
    g,_=recovered;q=np.zeros(g.free_dofs,dtype=np.float64);q[0]=.1
    eta=np.array((7.,-11.,13.))
    value=r.recover(g,q,eta,BUDGET);q[:]=999;eta[:]=999
    assert value.q[0]==F.from_float(.1)
    assert value.eta==ETA
    with pytest.raises(TypeError): r.Recovery()
    with pytest.raises(TypeError): replace(value,root_slope=Z)
    with pytest.raises(TypeError): value.diagnostics['equilibrium_solves']=1
    with pytest.raises(ValueError): r.recover(g,np.zeros(g.free_dofs,dtype=np.float32),ETA,BUDGET)
    with pytest.raises(ValueError): r.recover(g,[Z]*(g.free_dofs-1),ETA,BUDGET)
    with pytest.raises(ValueError): r.recover(g,(Z,)*g.free_dofs,(Z,Z,0.),BUDGET)
    with pytest.raises(ValueError): r.station(value,F(2))
    with pytest.raises(ValueError): r.band(value,O,Z)


def test_resource_failure_precedes_trace_or_shell_numerics(monkeypatch):
    g=model();q=(Z,)*g.free_dofs
    def forbidden(*args,**kwargs): raise AssertionError('numerical path entered before admission')
    monkeypatch.setattr(assembly,'trace_interval',forbidden)
    for changes in (dict(max_free_dofs=1),dict(max_intervals=1),dict(max_operations=1),
                    dict(max_work_bytes=1),dict(max_integer_bits=1)):
        with pytest.raises(ValueError): r.recover(g,q,ETA,replace(BUDGET,**changes))
    with pytest.raises(ValueError): replace(BUDGET,max_operations=True)


def test_functional_test_must_be_continuous(recovered):
    _,value=recovered
    rows=[list(row) for row in local_rows(value.cuts,((O,),(O,),(O,)))]
    rows[1][0]=(F(2),)
    with pytest.raises(ValueError,match='continuous'):r.functional_work(value.interface,rows)


def test_complete_piecewise_cubic_field_and_second_derivative_jumps():
    g=model(3)
    q=tuple(F(((i+3)**2%19)-9,10**7) for i in range(g.free_dofs))
    value=r.recover(g,q,ETA,BUDGET)
    assert all(len(p)==6 for row in value.interface.coefficients for p in row)
    assert any(r.station(value,s,order=2,side='left')!=r.station(value,s,order=2,side='right')
               for s in value.cuts[1:-1])
    test=local_rows(value.cuts,((O,Z,O,Z,Z,O),(F(2),O,Z,-O),(O,F(3),O)))
    assert r.virtual_work_defect(value,test)==r.Action(Z)
    assert value.support_lift_actions is not None


def test_nonfinite_and_exact_bit_inputs_rejected_before_trace(monkeypatch):
    g=model()
    def forbidden(*args,**kwargs): raise AssertionError('bad input reached trace')
    monkeypatch.setattr(assembly,'trace_interval',forbidden)
    for v in (float('nan'),float('inf')):
        q=np.zeros(g.free_dofs);q[0]=v
        with pytest.raises(ValueError): r.recover(g,q,ETA,BUDGET)
    q=[Z]*g.free_dofs;q[-1]=F(1,1<<4097)
    with pytest.raises(ValueError): r.recover(g,q,ETA,BUDGET)
