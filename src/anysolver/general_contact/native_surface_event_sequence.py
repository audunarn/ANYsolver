"""Bounded transverse event sequences; initially open endpoint development.

The explicit development selection binds its own restart identity. Closed-ending
paths still require composed algorithmic history/event derivatives. An ending-open
path has zero endpoint force/tangent but retains physical dissipation and slip.
"""
from dataclasses import dataclass,replace
from math import fsum

import numpy as np
from scipy.optimize import brentq

from anysolver._ge_beam3_p5_seeded.core import sha
from .friction_point import FrictionPointState,trial_coulomb_point
from .native_retained_station import _readonly
from .native_surface_path import material_path_pose,certify_material_ownership
from .native_surface_support import point_gap_slab_enclosure


@dataclass(frozen=True)
class MaterialSequenceEvent:
    fraction: float
    opening: bool
    bracket: tuple
    gap_residual: float


@dataclass(frozen=True)
class MaterialEventSequence:
    events: tuple
    intervals: int
    path_sha256: str
    endpoint_gap: float


def locate_material_event_sequence(pair,start,translations,angular,shell_increment,*,maximum_intervals=256):
    """Cover the complete actual path before admitting any event schedule."""
    if type(maximum_intervals) is not int or maximum_intervals<1:
        raise ValueError('positive shared event interval cap required')
    if sha(pair._definition())!=pair.definition_sha256:
        raise ValueError('native/S3 material-point definition changed')
    ownership=certify_material_ownership(pair,start,translations,angular,shell_increment,
        maximum_intervals=maximum_intervals)
    if not ownership.certified:raise ValueError('event sequence ownership unresolved: '+ownership.reason)
    remaining=maximum_intervals-ownership.intervals
    if remaining<1:raise MemoryError('native material event sequence interval cap exhausted')
    from .native_surface_quadrature import certify_station_orientation_path
    orientation=certify_station_orientation_path(pair.source,start,translations,angular,
        shell_increment,maximum_intervals=remaining)
    enclose=point_gap_slab_enclosure(pair,start,translations,angular,shell_increment)
    cache={}
    def gap(fraction):
        if fraction not in cache:
            pose=material_path_pose(start,translations,angular,shell_increment,float(fraction))
            source=pair.source.evaluate(pose.positions,pose.position_low,pose.cell_rotations).surface_position
            target=pair.target.physical_pose(pose.shell_displacement)
            cache[fraction]=float((source-np.asarray(target.position))@np.asarray(target.material_frame)[:,2])
        return cache[fraction]
    count=ownership.intervals+orientation;pending=[(0.,1.)];events={}
    while pending:
        if count>=maximum_intervals:raise MemoryError('native material event sequence interval cap exhausted')
        left,right=pending.pop();count+=1
        bounds=enclose(left,right)
        if bounds.gap_lower>0. or bounds.gap_upper<0.:continue
        direction=1 if bounds.derivative_lower>0. else -1 if bounds.derivative_upper<0. else 0
        if direction:
            gl,gr=gap(left),gap(right)
            if gl*gr>0.:continue
            root=left if gl==0. else right if gr==0. else brentq(gap,left,right,
                xtol=4*np.finfo(float).eps,rtol=4*np.finfo(float).eps,maxiter=64)
            residual=gap(root)
            scale=max(1.,float(np.max(np.abs(start.positions))),
                float(np.max(np.abs(pair.target.adapter.reference_positions))))
            if abs(residual)>512*np.finfo(float).eps*scale:
                raise ValueError('event sequence root residual unresolved')
            event=MaterialSequenceEvent(float(root),direction>0,(left,right),residual)
            if root in events and events[root].opening!=event.opening:
                raise ValueError('event sequence root ownership inconsistent')
            events[root]=event
            continue
        middle=(left+right)/2
        if not left<middle<right:raise ValueError('event sequence temporal resolution exhausted')
        pending.extend(((middle,right),(left,middle)))
    ordered=tuple(events[t] for t in sorted(events))
    return MaterialEventSequence(ordered,count,ownership.path_sha256,gap(1.))


@dataclass(frozen=True)
class NativeS3OpenSequenceResult:
    residual: np.ndarray
    tangent: np.ndarray
    trial: object
    normal_gap_m: float
    event_fractions: tuple
    path_sha256: str
    ownership_intervals: int
    history_evaluations: int
    normal_pressure_Pa: float=0.
    normal_storage_j: float=0.
    profile: str='NATIVE_S3_OPEN_EVENT_SEQUENCE_POINT_DEV_V1'

    def spatial_tangent(self):return self.tangent
    def normal_spatial_tangent(self):return self.tangent
    @property
    def normal_residual(self):return self.residual


def evaluate_open_event_sequence(pair,start,history,translations,angular,shell_increment,*,maximum_intervals=256):
    """Disposable full replay of closed windows between strictly open endpoints."""
    from .native_surface_activation import _release_history
    if type(history) is not FrictionPointState or history.partner_key is not None:
        raise ValueError('open event sequence requires released physical history')
    sequence=locate_material_event_sequence(pair,start,translations,angular,shell_increment,
        maximum_intervals=maximum_intervals)
    endpoint=material_path_pose(start,translations,angular,shell_increment,1.)
    source=pair.source.evaluate(start.positions,start.position_low,start.cell_rotations).surface_position
    target=pair.target.physical_pose(start.shell_displacement)
    initial_gap=float((source-np.asarray(target.position))@np.asarray(target.material_frame)[:,2])
    if not initial_gap>0. or not sequence.endpoint_gap>0.:
        raise ValueError('open event sequence requires strictly open endpoints')
    events=sequence.events
    if len(events)%2 or any(event.opening!=(i%2==1) for i,event in enumerate(events)):
        raise ValueError('open event sequence requires alternating closing/opening roots')
    state=history;dissipations=[];released=[];plastic=np.zeros(3);evaluations=0
    for closing,opening in zip(events[::2],events[1::2]):
        a,b=closing.fraction,opening.fraction
        if not 0.<a<b<1.:raise ValueError('open event sequence endpoint root unresolved')
        first=material_path_pose(start,translations,angular,shell_increment,a)
        last=material_path_pose(start,translations,angular,shell_increment,b)
        frame=pair.target.physical_pose(first.shell_displacement).material_frame
        state=trial_coulomb_point(state,material_frame=frame,relative_increment=(0.,0.,0.),
            normal_pressure=0.,friction_coefficient=pair.friction_coefficient,
            tangential_stiffness=pair.tangential_stiffness_Pa_per_m,partner_key=None).candidate_state
        evaluations+=1
        value=_release_history(pair,first,last,state,np.asarray(translations)*(b-a),
            np.asarray(angular)*(b-a),np.asarray(shell_increment)*(b-a),1.,0.,sequence)
        state=value.trial.candidate_state;evaluations+=value.history_evaluations
        dissipations.append(value.trial.dissipated_increment_density)
        released.append(value.trial.released_storage_density)
        frame=np.asarray(pair.target.physical_pose(last.shell_displacement).material_frame)
        plastic+=frame.T@np.asarray(value.trial.plastic_slip_increment)
    final_frame=pair.target.physical_pose(endpoint.shell_displacement).material_frame
    trial=trial_coulomb_point(state,material_frame=final_frame,relative_increment=(0.,0.,0.),
        normal_pressure=0.,friction_coefficient=pair.friction_coefficient,
        tangential_stiffness=pair.tangential_stiffness_Pa_per_m,partner_key=None)
    trial=replace(trial,dissipated_increment_density=fsum(dissipations),
        released_storage_density=fsum(released),plastic_slip_increment=tuple(np.asarray(final_frame)@plastic))
    size=42+pair.target.adapter.work_map.shape[1]
    return NativeS3OpenSequenceResult(_readonly(np.zeros(size)),_readonly(np.zeros((size,size))),
        trial,sequence.endpoint_gap,tuple(e.fraction for e in events),sequence.path_sha256,
        sequence.intervals,evaluations+1)
