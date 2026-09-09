"""Noncommitting native retained-potential directional test, not a solver."""
from math import fsum,isfinite
import numpy as np
from anysolver._ge_beam3_p5_seeded.core import canonical,sha
from anysolver._ge_beam3_retained_generalized_modal import _elastic_interior

STEPS=(1e-4,5e-5)


def lift(physical,packet,direction):
    size=len(packet['geometric']);free=tuple(packet['free_dofs'])
    expected=tuple(int(i) for i in physical.free if i<physical.nodal_count)+tuple(range(physical.nodal_count,size))
    if (free!=expected or len(direction)!=len(free) or size!=physical.nodal_count+6*len(physical.elements)):
        raise ValueError('complete physical free-space mapping')
    x=np.zeros(size);x[list(free)]=np.asarray(direction,dtype=float)
    if not np.isfinite(x).all() or not np.any(x):raise ValueError('finite nonzero kinematic direction')
    left=np.asarray(packet['left']);right=np.asarray(packet['right'])
    if left.shape!=(18*len(physical.elements),)*2 or right.shape!=(len(left),size):raise ValueError('complete stationary factors')
    dp=left.T@(left@(right@x));local=[];full=np.zeros(physical.count)
    for i,(eid,element) in enumerate(physical.elements):
        internal=list(range(physical.nodal_count+6*i,physical.nodal_count+6*i+6))
        if packet['internal_layout'][i]!=[eid,internal]:raise ValueError('internal coordinate identity/order')
        slots=list(element.get_dof_mapping(physical.model.mesh))+internal
        z=np.r_[x[slots],dp[18*i:18*(i+1)]];local.append(z)
        full[physical.slots[i]]=z
    # Shared nodal coordinates must agree, not be accumulated per element.
    for i,z in enumerate(local):
        if not np.array_equal(full[physical.slots[i]],z):raise ValueError('shared nodal direction disagrees')
    return x,local,full


def evaluate(context,state,packet,direction,progress=lambda row:None):
    before=canonical(state);context._require_issued(state,expected_snapshot=before)
    captured=sha(packet);p=context.physical;mechanical=state.mechanical
    x,local,full=lift(p,packet,direction)
    force=p.nodal_external(state.parameter);external_slope=float(force@x[:p.nodal_count])
    points={};baseline_product=np.zeros(p.count);local_work=[];lift_errors=[]
    def check():context._require_issued(state,expected_snapshot=before)
    for amount in (0.,STEPS[0],-STEPS[0],STEPS[1],-STEPS[1]):
        check();progress(dict(stage='native-trial-point',amount=amount))
        potentials=[];residual=np.zeros(p.count)
        for i,(eid,element) in enumerate(p.elements):
            check();nodes=p.nodes[i];core=element.operator;z=local[i]
            response=core.evaluate(mechanical.positions[nodes],mechanical.position_low[nodes],
                mechanical.nodal_frames[nodes],mechanical.cell_rotations[i],mechanical.resultants[i],
                origin=state.histories[i],increment=amount*z,check=check)
            _elastic_interior(core,response,state.histories[i])
            potentials.append(response.potential);residual[p.slots[i]]+=response.residual
            if amount==0.:
                h=response.hessian+response.hessian_low
                hv=h@z;baseline_product[p.slots[i]]+=hv
                local_work.append(float(z@hv))
                compatibility=h[24:,:24]@z[:24]+h[24:,24:]@z[24:]
                lift_errors.append(float(np.linalg.norm(compatibility))/max(1.,float(np.linalg.norm(h[24:,:24]@z[:24]))))
                # Captured coupling must still be the replayed native coupling.
                slots=list(element.get_dof_mapping(p.model.mesh))+list(packet['internal_layout'][i][1])
                expected=np.asarray(packet['right'])[18*i:18*(i+1),slots]
                if not np.array_equal(expected,h[24:,:24]):raise ValueError('saved/native coupling changed')
        residual[:p.nodal_count]-=force
        # The omitted external baseline constant has zero derivatives. Keep the
        # actual spatial-dead-load incremental work; it has zero Hessian.
        potential=fsum([*potentials,-amount*external_slope])
        points[amount]=(potential,residual)
    check()
    if sha(packet)!=captured or canonical(state)!=before:raise ValueError('native trial mutated frozen input/state')
    work=fsum(local_work);rows=[]
    for step in STEPS:
        plus,rplus=points[step];minus,rminus=points[-step]
        second=fsum((plus,minus,-2*points[0.][0]))/(step*step)
        derivative=(rplus-rminus)/(2*step)
        scalar=fsum(float(a)*float(b) for a,b in zip(full,derivative))
        rows.append(dict(step=step,potential_second=second,residual_directional_work=scalar,
            potential_error=abs(second-work)/max(1.,abs(work)),
            directional_work_error=abs(scalar-work)/max(1.,abs(work)),
            full_residual_direction_error=float(np.linalg.norm(derivative-baseline_product))/max(1.,float(np.linalg.norm(baseline_product)))))
    return dict(native_mixed_directional_work=work,max_stationary_lift_error=max(lift_errors),
        rows=rows,elements=len(p.elements),retained_dimension=p.count,original_free_dimension=len(packet['free_dofs']),
        trial_points=len(points),accepted_state_unchanged=True,
        physical_control_constraint_added=False,material_history_committed=False,
        incremental_dead_load_slope=external_slope,production_qualified=False)


def adjudicate(result,expected):
    numeric=[expected,result['native_mixed_directional_work'],result['max_stationary_lift_error'],
             *[v for row in result['rows'] for v in row.values()]]
    if any(type(v) is not float or not isfinite(v) for v in numeric):raise ValueError('finite binary64 trial metrics')
    if (result['elements']!=24 or result['retained_dimension']!=870 or result['original_free_dimension']!=426
            or result['trial_points']!=5 or result['accepted_state_unchanged'] is not True
            or result['material_history_committed'] is not False or result['physical_control_constraint_added'] is not False):
        raise ValueError('complete noncommitting native trial coverage')
    if result['max_stationary_lift_error']>1e-11:raise ValueError('stationary resultant lift disagreement')
    if expected>=0 or result['native_mixed_directional_work']>=0:raise ValueError('native negative work not reproduced')
    if abs(result['native_mixed_directional_work']-expected)/max(1.,abs(expected))>1e-11:
        raise ValueError('native/factor work disagreement')
    if tuple(row['step'] for row in result['rows'])!=STEPS:raise ValueError('fixed directional steps')
    for row in result['rows']:
        if row['potential_second']>=0 or row['residual_directional_work']>=0:raise ValueError('native trial did not show negative second variation')
        if max(row[k] for k in ('potential_error','directional_work_error','full_residual_direction_error'))>1e-7:
            raise ValueError('native variational directional disagreement')
