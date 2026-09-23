"""Owned saved support and full local virtual-work admission; no norm or solve."""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction as F
import hashlib
import numpy as np
from scripts import _b3_e4_f03_local_recovery as rec
from scripts import _b3_e4_f03_local_support_recovery as support
from scripts import _b3_e4_f03_action_enclosure as bound
from scripts import _b3_e4_f03_local_functional as functional
from scripts import _b3_e4_f03_local_grid as topology
from scripts import _b3_e4_f03_spatial_contract as c

Z=F(0);O=F(1)
SCOPE='SAVED_SUPPORT_AND_LOCAL_VIRTUAL_WORK_ONLY'
WORK_LIMIT=F.from_float(1e-10)
SUPPORT_LIMIT=F.from_float(1e-8)


def _cuts(values):
    if type(values) not in (tuple,list) or not 2<=len(values)<=rec.MAX_TERMS+1:
        raise ValueError('bounded exact work partition required')
    cc=tuple(rec._coordinate(v) for v in values)
    if cc[0]!=Z or cc[-1]!=O or any(a>=b for a,b in zip(cc,cc[1:])):
        raise ValueError('positive exact work partition required')
    return cc


def _array(value,shape):
    if (type(value) is not np.ndarray or value.dtype!=np.float64 or
            value.shape!=shape):
        raise ValueError('finite exact-shape float64 saved work array required')
    # Immutable bytes own the snapshot; writeability cannot be re-enabled.
    owned=np.frombuffer(value.tobytes(order='C'),dtype=np.float64).reshape(shape)
    if not np.isfinite(owned).all():
        raise ValueError('finite exact-shape float64 saved work array required')
    return owned


@dataclass(frozen=True,slots=True)
class SavedWork:
    p:int
    cuts:tuple
    lift_family:str
    lift_coefficients:np.ndarray
    shell_work:np.ndarray
    interface_work:np.ndarray
    edge_route1:np.ndarray
    edge_route2:np.ndarray
    first_free:np.ndarray
    shift_delta:np.ndarray
    virtual_terms:np.ndarray
    virtual_defects:np.ndarray

    def __post_init__(self):
        if type(self.p) is not int or self.p not in (1,2,3):
            raise ValueError('explicit Q1/Q2/Q3 degree required')
        cc=_cuts(self.cuts);ni=len(cc)-1
        expected='Q1_EDGE_ROTATION' if self.p==1 else 'Q2_Q3_CLASSICAL_ROTATION'
        if self.lift_family!=expected:raise ValueError('saved support lift identity mismatch')
        object.__setattr__(self,'cuts',cc)
        count=ni*(self.p+2)+1
        shapes={'lift_coefficients':(6,ni,3,6),'shell_work':(6,),
            'interface_work':(6,),'edge_route1':(6,),'edge_route2':(6,),
            'first_free':(2,),'shift_delta':(2,),
            'virtual_terms':(3,count,4),'virtual_defects':(3,count)}
        for name,shape in shapes.items():
            object.__setattr__(self,name,_array(getattr(self,name),shape))


@dataclass(frozen=True,slots=True)
class WorkBudget:
    support_budget:support.SupportBudget
    action_budget:bound.ActionBudget
    max_virtual_tests:int
    max_comparisons:int
    max_aggregate_operations:int
    max_aggregate_bits:int
    max_work_bytes:int

    def __post_init__(self):
        if (type(self.support_budget) is not support.SupportBudget or
                type(self.action_budget) is not bound.ActionBudget or any(
                type(getattr(self,key)) is not int or getattr(self,key)<=0
                for key in ('max_virtual_tests','max_comparisons',
                            'max_aggregate_operations','max_aggregate_bits','max_work_bytes'))):
            raise ValueError('explicit positive saved-work budgets required')


def virtual_inventory(cuts,p):
    """Stream the entire C0 P_(p+2) basis: channel, vertices, interval bubbles."""
    cc=_cuts(cuts)
    if type(p) is not int or p not in (1,2,3):raise ValueError('explicit Qp degree required')
    ni=len(cc)-1;degree=p+2
    # P_k(2*tau-1), k=0..3. Bubble degree is k+2 <=5.
    legendre=((O,),(-O,F(2)),(O,F(-6),F(6)),(-O,F(12),F(-30),F(20)))
    for channel in range(3):
        amplitude=c.Q_U0 if channel<2 else c.Q_U0/functional.ELL
        for index in range(ni+1+ni*(degree-1)):
            rows=[[(Z,)*6 for _ in range(3)] for _ in range(ni)]
            if index<=ni:
                key=(channel,'vertex',index)
                if index>0:rows[index-1][channel]=rec._scale((Z,O),amplitude)
                if index<ni:rows[index][channel]=rec._scale((O,-O),amplitude)
            else:
                interval,k=divmod(index-ni-1,degree-1)
                key=(channel,'bubble',interval,k)
                poly=[Z]*6
                for j,v in enumerate(legendre[k]):
                    poly[j+1]+=v;poly[j+2]-=v
                rows[interval][channel]=rec._scale(tuple(poly),amplitude)
            yield key,tuple(tuple(rec._poly(poly) for poly in row) for row in rows)


def virtual_terms(value,rows):
    root=sum((eta*row[0] for eta,row in zip(value.eta,rows[0])),Z)
    terms=(rec.functional_work(value.interface,rows),
           rec.Action(rec.beam_work(value,rows)),rec.load_work(value,rows),rec.Action(root))
    return terms,terms[0]+terms[1]-terms[2]+terms[3]


def _status(comparisons,parity):
    states=[v['status'] for v in comparisons.values()]
    if not parity or 'FAILED' in states:return 'FAILED'
    if 'HOLD_UNRESOLVED' in states:return 'HOLD_UNRESOLVED'
    return 'PASSED'


def _identity(grid,value,saved):
    digest=hashlib.sha256(b'F03_SAVED_WORK_V1\0')
    digest.update(bytes((grid.p,)))
    for seq in (grid.x_cuts,grid.y_cuts,grid.station_cuts,value.q,value.eta):
        digest.update(len(seq).to_bytes(8,'little'))
        for item in seq:bound._hash_fraction(digest,item)
    digest.update(np.asarray(grid.free_to_full,dtype='<i8').tobytes())
    digest.update(saved.lift_family.encode('ascii'))
    for name in ('lift_coefficients','shell_work','interface_work','edge_route1',
                 'edge_route2','first_free','shift_delta','virtual_terms','virtual_defects'):
        digest.update(name.encode('ascii'))
        digest.update(np.asarray(getattr(saved,name),dtype='<f8').tobytes())
    return digest.hexdigest()


def input_identity(grid,value,saved):
    """Bind one compiled grid/state to an owned saved-work record."""
    if (type(grid) is not topology.CompiledGrid or type(value) is not rec.Recovery
            or type(saved) is not SavedWork):
        raise ValueError('compiled grid, Recovery and SavedWork required')
    return _identity(grid,value,saved)


def verify_work(grid,q,eta,saved,*,budget):
    """Recompute from one owned state; validate every saved work field and gate."""
    if (type(grid) is not topology.CompiledGrid or type(saved) is not SavedWork or
            type(budget) is not WorkBudget):
        raise ValueError('factory grid, SavedWork and explicit WorkBudget required')
    if saved.p!=grid.p or saved.cuts!=grid.station_cuts:
        raise ValueError('saved work does not bind to grid degree/partition')
    ni=len(grid.station_cuts)-1;nv=3*(ni*(grid.p+2)+1)
    # 6 per virtual test, plus bounded support/action and physical balance checks.
    ncomp=6*nv+50
    if nv>budget.max_virtual_tests or ncomp>budget.max_comparisons:
        raise ValueError('saved-work inventory exceeds budget')
    ab=budget.action_budget
    if (ncomp*ab.max_operations>budget.max_aggregate_operations or
            ncomp*ab.max_total_bits>budget.max_aggregate_bits):
        raise ValueError('saved-work aggregate Action envelope exceeds budget')
    # Complete per-test chart, copied saved inputs and retained comparison records.
    # Comparison records retain large rational endpoints, not only scalar metrics.
    workspace=(ni*3*6*(1024+2*rec.BITS//8)*2+
               sum(getattr(saved,name).nbytes for name in (
                   'lift_coefficients','shell_work','interface_work','edge_route1',
                   'edge_route2','first_free','shift_delta','virtual_terms','virtual_defects'))*2+
               ncomp*(4096+64*(1024+2*ab.max_fraction_bits//8))+
               budget.support_budget.max_work_bytes+
               budget.support_budget.recovery_budget.max_work_bytes+ab.max_work_bytes)
    if workspace>budget.max_work_bytes:raise ValueError('saved-work workspace exceeds budget')
    # Own all observations before any evaluation (arrays backed by immutable bytes).
    saved=SavedWork(**{name:getattr(saved,name) for name in saved.__dataclass_fields__})
    value=rec.recover(grid,q,eta,budget.support_budget.recovery_budget)
    result=support.support_recovery(grid,value,budget.support_budget)
    comparisons={};operations=bits=0
    def check(name,action,target,scale,limit):
        nonlocal operations,bits
        if len(comparisons)>=ncomp:raise ArithmeticError('comparison envelope exceeded')
        comparison=bound.compare_saved(action,target,scale,limit,budget=ab)
        operations+=comparison['comparison_work']['exact_operations']
        bits+=comparison['comparison_work']['cumulative_integer_bits']
        if operations>budget.max_aggregate_operations or bits>budget.max_aggregate_bits:
            raise ValueError('saved-work aggregate Action runtime budget exceeded')
        comparisons[name]=comparison
    expected_poses=np.asarray(tuple(support.lift_pose(value.cuts,side,ch,grid.p)
                    for side in ('left','right') for ch in range(3)),dtype=np.float64)
    if not np.isfinite(expected_poses).all():raise ValueError('unrepresentable saved lift chart')
    # Saved chart is a rounded definition record, not an approximate physical solve.
    parity=saved.lift_coefficients.tobytes()==expected_poses.tobytes()
    for name,actions in (('shell_work',tuple(rec.Action(v) for v in result.shell_work)),
            ('interface_work',result.interface_work),('edge_route1',result.route1),
            ('edge_route2',result.route2)):
        for i,action in enumerate(actions):
            check(f'{name}/{i}',action,getattr(saved,name)[i],c.Q_F0,SUPPORT_LIMIT)
    for i,action in enumerate(result.route_difference):
        check(f'route_difference/{i}',action,0.,c.Q_F0,SUPPORT_LIMIT)
    for name,actions in (('first_free',(result.first_free_route1_residual,
                        result.first_free_route2_residual)),
                        ('shift_delta',(result.shift_route1_delta,result.shift_route2_delta))):
        for i,action in enumerate(actions):
            check(f'{name}/saved/{i}',action,getattr(saved,name)[i],c.Q_F0,SUPPORT_LIMIT)
            check(f'{name}/zero/{i}',action,0.,c.Q_F0,SUPPORT_LIMIT)
    for i,action in enumerate(result.shift_binding_defects):
        check(f'shift_identity/{i}',action,0.,c.Q_F0,SUPPORT_LIMIT)
    for name,actions in (('force_actual',result.force_balance_actual),
                        ('force_nominal',result.force_balance_nominal)):
        for i,action in enumerate(actions):
            check(f'{name}/{i}',action,0.,c.Q_F0,SUPPORT_LIMIT)
    check('moment_actual',result.physical_moment_defect,0.,c.Q_F0,SUPPORT_LIMIT)
    nominal_moment=result.physical_moment_defect-result.load_actual_minus_nominal[1]
    check('moment_nominal',nominal_moment,0.,c.Q_F0,SUPPORT_LIMIT)
    check('moment_represented',result.represented_moment_identity,0.,c.Q_F0,SUPPORT_LIMIT)
    check('moment_prediction_identity',result.physical_moment_defect-
          result.predicted_physical_moment_defect,0.,c.Q_F0,SUPPORT_LIMIT)
    per_channel=nv//3;keys=[]
    for number,(key,rows) in enumerate(virtual_inventory(value.cuts,grid.p)):
        channel,index=divmod(number,per_channel);keys.append(key)
        terms,defect=virtual_terms(value,rows)
        for j,term in enumerate(terms):
            check(f'virtual/{number}/term/{j}',term,saved.virtual_terms[channel,index,j],
                  c.Q_E0,WORK_LIMIT)
        check(f'virtual/{number}/saved',defect,saved.virtual_defects[channel,index],c.Q_E0,WORK_LIMIT)
        check(f'virtual/{number}/zero',defect,0.,c.Q_E0,WORK_LIMIT)
    if len(keys)!=nv:raise ArithmeticError('virtual inventory incomplete')
    balance_actions=(*result.force_balance_actual,*result.force_balance_nominal,
        result.physical_moment_defect,result.predicted_physical_moment_defect,
        result.represented_moment_identity,result.rigid_yaw_functional,
        *result.actual_load,*result.nominal_load,*result.load_actual_minus_nominal)
    return dict(status=_status(comparisons,parity),scope=SCOPE,input_sha256=_identity(grid,value,saved),
        comparisons=comparisons,lift_chart_bit_parity=parity,virtual_keys=tuple(keys),
        balance_actions=balance_actions,
        physical_moment_defect=result.physical_moment_defect,
        predicted_physical_moment_defect=result.predicted_physical_moment_defect,
        load_actual_minus_nominal=result.load_actual_minus_nominal,
        diagnostics=dict(equilibrium_solves=0,virtual_tests=nv,comparisons=len(comparisons),
            comparison_envelope=ncomp,exact_operations=operations,cumulative_integer_bits=bits,
            workspace_estimate_bytes=workspace,state_recoveries=2,norm_evaluations=0))
