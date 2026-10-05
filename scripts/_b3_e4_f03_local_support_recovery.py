"""Supplemental exact Q1/Qp support lifts for manufactured local states.

This leaves the original P1-unavailable Recovery untouched. Symbolic Actions
are returned without Decimal evaluation, acceptance, or equilibrium solves.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
from types import MappingProxyType

import numpy as np

from scripts import _b3_e4_f03_local_grid as topology
from scripts import _b3_e4_f03_local_primal_assembly as assembly
from scripts import _b3_e4_f03_local_recovery as rec
from scripts import _b3_e4_f03_local_shell as shell
from scripts import _b3_e4_f03_spatial_contract as c


Z=F(0);O=F(1)


@dataclass(frozen=True,slots=True)
class SupportBudget:
    recovery_budget:rec.RecoveryBudget
    max_free_dofs:int
    max_intervals:int
    max_operations:int
    max_integer_bits:int
    max_work_bytes:int

    def __post_init__(self):
        if type(self.recovery_budget) is not rec.RecoveryBudget or any(
                type(getattr(self,key)) is not int or getattr(self,key)<=0
                for key in ('max_free_dofs','max_intervals','max_operations',
                            'max_integer_bits','max_work_bytes')):
            raise ValueError('explicit bounded support recovery budgets required')


@dataclass(frozen=True,slots=True,init=False)
class SupportResult:
    lift_family:str
    q:tuple
    eta:tuple
    cuts:tuple
    shell_work:tuple
    interface_work:tuple
    route1:tuple
    route2:tuple
    route_difference:tuple
    first_free_route1_residual:rec.Action
    first_free_route2_residual:rec.Action
    shift_route1_delta:rec.Action
    shift_route2_delta:rec.Action
    shift_binding_defects:tuple
    force_balance_actual:tuple
    force_balance_nominal:tuple
    physical_moment_defect:rec.Action
    predicted_physical_moment_defect:rec.Action
    represented_moment_identity:rec.Action
    rigid_yaw_functional:rec.Action
    actual_load:tuple
    nominal_load:tuple
    load_actual_minus_nominal:tuple
    diagnostics:object

    def __init__(self,*args,**kwargs):
        raise TypeError('SupportResult requires validated supplemental factory')


def _pose_rows(cuts,global_polys):
    return tuple(tuple(rec._restrict(rec._poly(p),a,b-a) for p in global_polys)
                 for a,b in zip(cuts,cuts[1:]))


def lift_pose(cuts,side,channel,p):
    """The Q1 origin-rotation lift uses edge x, with exact pad moments."""
    if (type(p) is not int or p not in (1,2,3) or
            side not in ('left','right') or type(channel) is not int or
            channel not in (0,1,2) or type(cuts) not in (tuple,list) or
            not 2<=len(cuts)<=rec.MAX_TERMS+1):
        raise ValueError('bounded Qp support lift arguments required')
    cc=tuple(rec._coordinate(v) for v in cuts)
    if cc[0]!=Z or cc[-1]!=O or any(a>=b for a,b in zip(cc,cc[1:])):
        raise ValueError('exact positive support station partition required')
    if p>=2 or channel!=2:
        return rec.lift_pose(cc,side,channel)
    a,b,e=(F(3,4),-F(1,2),-F(1,2)) if side=='left' else (
           F(1,4),F(1,2),F(3,2))
    x2=c.Q_DX**2+c.Q_A**2/3
    y2=c.Q_DY**2+c.Q_A**2/3
    return _pose_rows(cc,((Z,),(e*a,e*b),
                          ((e*b*x2+a*y2)/c.Q_J,b*y2/c.Q_J)))


def _nodal_lift(x,y,side,channel,p):
    e=-F(1,2) if side==0 else F(3,2)
    phi=(F(3,2)-x)/2 if side==0 else (x+F(1,2))/2
    if channel==0:return (phi,Z)
    if channel==1:return (Z,phi)
    return (-y*phi,(e if p==1 else x)*phi)


def _shell_works(grid,q):
    works=[Z]*6;first=Z
    nx=len(grid.x_nodes);nc=nx*len(grid.y_nodes)
    for rect,gather,free in zip(grid.rectangles,grid.full_gathers,grid.free_gathers):
        local=tuple(q[int(i)] if i>=0 else Z for i in free)
        matrix=shell.stiffness_exact(rect,grid.p)
        residual=tuple(sum((a*b for a,b in zip(row,local)),Z) for row in matrix)
        for j,index in enumerate(gather):
            component,node=divmod(int(index),nc);iy,ix=divmod(node,nx)
            x,y=grid.x_nodes[ix],grid.y_nodes[iy]
            for side in (0,1):
                for channel in range(3):
                    works[side*3+channel]+=residual[j]*_nodal_lift(
                        x,y,side,channel,grid.p)[component]
            if free[j]==0:first+=residual[j]
    return tuple(rec._rational(v) for v in works),rec._rational(first)


def _first_free_trace(grid,budget):
    rows=[]
    for i in range(len(grid.station_cuts)-1):
        trace=assembly.trace_interval(grid,i,budget)
        position=np.flatnonzero(trace.indices==0)
        if len(position)>1:
            raise ArithmeticError('duplicate first free-coordinate trace')
        rows.append(tuple(tuple(trace.coefficients[channel][int(position[0])])
                          if len(position) else (Z,)*6 for channel in range(3)))
    return tuple(rows)


def _add_rows(first,second):
    return tuple(tuple(rec._add(a,b) for a,b in zip(left,right))
                 for left,right in zip(first,second))


def _route1(value,shell_work,rows):
    root=sum((e*p[0] for e,p in zip(value.eta,rows[0])),Z)
    return rec.Action(shell_work+rec.beam_work(value,rows)+root)-rec.load_work(value,rows)


def _route2(value,shell_work,rows):
    return rec.Action(shell_work)-rec.functional_work(value.interface,rows)


def _global_test(cuts,channel,polynomial):
    global_polys=[(Z,),(Z,),(Z,)]
    global_polys[channel]=polynomial
    return _pose_rows(cuts,global_polys)


def _action_bits(value):
    return rec._bits(value.rational)+sum(rec._bits(a)+rec._bits(b)+
        sum(rec._bits(v) for v in p) for a,b,p in value.cosine_terms)


def _scale_action(value,factor):
    return rec.Action(value.rational*factor,
                      tuple((a,b,rec._scale(p,factor))
                            for a,b,p in value.cosine_terms))


def _symbolic_preflight_bits(grid,value):
    """Conservative live exact storage before constructing any new Action.

    160 Action slots cover retained results and every temporary unary/binary
    Action created by the two routes, shifts and balances. Each slot admits a
    rational plus every interval's endpoints and six coefficients at the
    recovery module's per-Fraction cap. Pose, first-hat, state and cuts are
    charged separately. This intentionally over-counts shared immutable data.
    """
    ni=len(grid.station_cuts)-1
    fraction_bits=2*rec.BITS
    actions=160*(1+8*ni)*fraction_bits
    poses=(6*ni*3*6+ni*3*6)*fraction_bits
    state=(len(value.q)+len(value.eta)+len(value.cuts)+6)*fraction_bits
    return actions+poses+state


def support_recovery(grid,value,budget):
    """Bind the manufactured state to this grid, then recover support routes."""
    if (type(grid) is not topology.CompiledGrid or type(value) is not rec.Recovery or
            type(budget) is not SupportBudget):
        raise ValueError('factory grid, recovery and explicit support budget required')
    ni=len(grid.station_cuts)-1
    local=2*(grid.p+1)**2
    if (grid.free_dofs<1 or grid.free_dofs>budget.max_free_dofs or
            ni>min(budget.max_intervals,rec.MAX_TERMS) or
            value.cuts!=grid.station_cuts or len(value.q)!=grid.free_dofs or
            len(value.eta)!=3):
        reason=('support recovery requires a first free-coordinate shift inventory'
                if grid.free_dofs<1 else
                'support state/grid inventory or station binding mismatch')
        raise ValueError(reason)
    # The supplemental verification rederives existing factory fields once;
    # its cost is separately reported, not a physical equilibrium solve.
    operations=(len(grid.rectangles)*local*(local+24)*32+
                ni*max(1,max(len(v) for v in grid.trace_incidence))*(grid.p+3)*96)
    workspace=(768*(12*local*len(grid.rectangles)+ni*360+grid.free_dofs)+
               budget.max_integer_bits//8)
    if operations>budget.max_operations:
        raise ValueError('support operation estimate exceeds budget')
    if workspace>budget.max_work_bytes:
        raise ValueError('support workspace estimate exceeds budget')
    symbolic_preflight=_symbolic_preflight_bits(grid,value)
    if symbolic_preflight>budget.max_integer_bits:
        raise ValueError('support symbolic storage preflight exceeds bit budget')
    rebound=rec.recover(grid,value.q,value.eta,budget.recovery_budget)
    for name in ('q','eta','cuts','pose','resultants','interface','root_gap',
                 'root_slope','tip_pose','root_resultants','tip_resultants'):
        if getattr(value,name)!=getattr(rebound,name):
            raise ValueError(f'support recovery {name} does not bind to this grid/state')
    # Continue solely from the newly owned, factory-validated state.
    value=rebound
    q,eta=tuple(rebound.q),tuple(rebound.eta)
    shell_works,first_shell=_shell_works(grid,q)
    poses=tuple(lift_pose(value.cuts,side,channel,grid.p)
                for side in ('left','right') for channel in range(3))
    interface_works=tuple(rec.functional_work(value.interface,rows) for rows in poses)
    route1=tuple(_route1(value,w,rows) for w,rows in zip(shell_works,poses))
    route2=tuple(rec.Action(w)-action for w,action in zip(shell_works,interface_works))
    differences=tuple(a-b for a,b in zip(route1,route2))
    if grid.p>=2 and (shell_works!=value.shell_lift_work or
            interface_works!=value.interface_lift_work or
            route2!=value.support_lift_actions):
        raise ArithmeticError('existing p>=2 support lift parity failed')
    hat=_first_free_trace(grid,budget.recovery_budget.trace_budget)
    first1=_route1(value,first_shell,hat)
    first2=_route2(value,first_shell,hat)
    shifted=_add_rows(poses[0],hat)
    shifted1=_route1(value,shell_works[0]+first_shell,shifted)-route1[0]
    shifted2=_route2(value,shell_works[0]+first_shell,shifted)-route2[0]
    shift_defects=(shifted1-first1,shifted2-first2)
    fx=route2[0]+route2[3]
    fy=route2[1]+route2[4]
    moment=route2[2]+route2[5]
    force_load=rec.load_work(value,_global_test(value.cuts,1,(O,)))
    moment_load=rec.load_work(value,_global_test(value.cuts,1,(Z,O)))
    nominal=(rec.Action(c.Q_F0),rec.Action(c.Q_F0*c.Q_L0/2))
    force_actual=(fx-rec.Action(eta[0]),fy-rec.Action(eta[1])+force_load)
    force_nominal=(fx-rec.Action(eta[0]),fy-rec.Action(eta[1])+nominal[0])
    integral_q=sum(((b-a)*rec._product_integral(p,(O,))
                    for (a,b),row in zip(zip(value.cuts,value.cuts[1:]),
                                          value.resultants) for p in (row[1],)),Z)
    yaw=rec.functional_work(value.interface,_global_test(value.cuts,2,(O,)))
    physical=moment-rec.Action(eta[2])+moment_load
    predicted=_scale_action(yaw,O-c.Q_GAMMA)
    represented=(moment-rec.Action(c.Q_GAMMA*eta[2])+moment_load-
                 rec.Action((O-c.Q_GAMMA)*integral_q))
    load_differences=(force_load-nominal[0],moment_load-nominal[1])
    actions=(*interface_works,*route1,*route2,*differences,first1,first2,
             shifted1,shifted2,*shift_defects,*force_actual,*force_nominal,
             physical,predicted,represented,yaw,force_load,moment_load,*nominal,
             *load_differences)
    retained=sum(_action_bits(action) for action in actions)+sum(
        rec._bits(v) for lift in poses for row in lift for channel in row for v in channel)+sum(
        rec._bits(v) for row in hat for channel in row for v in channel)+sum(
        rec._bits(v) for v in (*q,*eta,*shell_works,*value.cuts))
    if retained>symbolic_preflight:
        raise ArithmeticError('support symbolic storage exceeded conservative preflight')
    if retained>budget.max_integer_bits:
        raise ValueError('support retained integer-bit budget exceeded')
    result=object.__new__(SupportResult)
    fields=dict(lift_family='Q1_EDGE_ROTATION' if grid.p==1 else 'Q2_Q3_CLASSICAL_ROTATION',
        q=q,eta=eta,cuts=value.cuts,shell_work=shell_works,
        interface_work=interface_works,route1=route1,route2=route2,
        route_difference=differences,first_free_route1_residual=first1,
        first_free_route2_residual=first2,shift_route1_delta=shifted1,
        shift_route2_delta=shifted2,shift_binding_defects=shift_defects,
        force_balance_actual=force_actual,force_balance_nominal=force_nominal,
        physical_moment_defect=physical,predicted_physical_moment_defect=predicted,
        represented_moment_identity=represented,rigid_yaw_functional=yaw,
        actual_load=(force_load,moment_load),nominal_load=nominal,
        load_actual_minus_nominal=load_differences,
        diagnostics=MappingProxyType(dict(state_recovery_rebindings=1,
            equilibrium_solves=0,factorizations=0,decimal_acceptance_evaluations=0,
            retained_integer_bits=retained,operation_estimate=operations,
            symbolic_preflight_bits=symbolic_preflight,
            workspace_estimate_bytes=workspace,gamma=c.Q_GAMMA,
            support_family='Q1_EDGE_ROTATION' if grid.p==1 else 'Q2_Q3_CLASSICAL_ROTATION')))
    for name,item in fields.items():object.__setattr__(result,name,item)
    return result
