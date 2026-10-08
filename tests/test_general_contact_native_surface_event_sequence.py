"""Multiple normal events on one actual retained-material motion segment."""
from dataclasses import replace
from math import acos,cos,sin,fsum,pi

import numpy as np
import pytest

from anysolver.general_contact.friction_point import initial_friction_point
from anysolver.general_contact.native_surface_event_sequence import locate_material_event_sequence,evaluate_open_event_sequence
from anysolver.general_contact.native_surface_history import NativeSurfaceMotionSegment
from test_general_contact_native_surface_support import _field


def pulse(height=.025):
    segment=NativeSurfaceMotionSegment(np.zeros((3,3)),np.array(((1.6,0.,0.),(0.,0.,0.))),np.zeros(18))
    field=_field(height=height,rotation=-.8,segments=(segment,))
    pair=field.pair_at(-.5,1.5*pi)
    history=initial_friction_point(pair.target.physical_pose(field.initial.shell_displacement).material_frame)
    return field,pair,history,segment


def test_analytical_two_event_roots_and_discrete_history_work():
    field,pair,history,segment=pulse()
    history=replace(history,cumulative_plastic_slip=.07,cumulative_dissipation_density=.1)
    args=(pair,field.initial,segment.translations,segment.angular,segment.shell_increment)
    sequence=locate_material_event_sequence(*args)
    theta=acos(.025/.03);expected=((.8-theta)/1.6,(.8+theta)/1.6)
    assert [e.fraction for e in sequence.events]==pytest.approx(expected,abs=2e-12)
    assert [e.opening for e in sequence.events]==[False,True]
    value=evaluate_open_event_sequence(pair,field.initial,history,*args[2:])
    # Independent scalar dry-friction return map, same declared32-step rule.
    elastic=0.;previous=.03*sin(-theta);dissipation=[];plastic=0.
    for index in range(1,pair.event_history_substeps):
        angle=-theta+2*theta*index/pair.event_history_substeps
        y=.03*sin(angle);trial=elastic+y-previous
        pressure=1000*(.03*cos(angle)-.025);cap=.3*pressure
        next_elastic=min(trial,cap/1000)
        increment=trial-next_elastic;dissipation.append(cap*increment);plastic+=increment
        elastic=next_elastic;previous=y
    assert value.trial.dissipated_increment_density==pytest.approx(fsum(dissipation),rel=1e-10)
    assert value.trial.released_storage_density==pytest.approx(.5*1000*elastic**2,rel=1e-10)
    assert value.trial.candidate_state.cumulative_dissipation_density==pytest.approx(.1+fsum(dissipation),rel=1e-12)
    assert value.trial.candidate_state.cumulative_plastic_slip==pytest.approx(.07+plastic,rel=1e-10)
    assert value.trial.candidate_state.partner_key is None
    assert np.array_equal(value.residual,np.zeros(60)) and np.array_equal(value.spatial_tangent(),np.zeros((60,60)))
    assert history.cumulative_dissipation_density==.1
    assert value.history_evaluations==pair.event_history_substeps+3


def test_sequence_counts_actual_coulomb_evaluations(monkeypatch):
    from anysolver.general_contact import native_surface_event_sequence as sequence_module
    from anysolver.general_contact import native_surface_activation as activation_module
    original=sequence_module.trial_coulomb_point;calls=[]
    def counted(*args,**kwargs):
        calls.append(1)
        return original(*args,**kwargs)
    monkeypatch.setattr(sequence_module,'trial_coulomb_point',counted)
    monkeypatch.setattr(activation_module,'trial_coulomb_point',counted)
    field,pair,history,segment=pulse()
    value=evaluate_open_event_sequence(pair,field.initial,history,segment.translations,segment.angular,segment.shell_increment)
    assert value.history_evaluations==len(calls)==35


def test_explicit_sequence_policy_routes_full_saved_query_and_binds_identity():
    import json
    from pathlib import Path
    from anysolver.general_contact.native_surface_history import NativeSurfaceHistoryField,NativeSurfaceReplayBudget
    from anysolver.general_contact.native_surface_s3_friction import NativeS3MaterialConfiguration
    from test_general_contact_native_surface_replay_owner import _replay_patch,_patch,normal_settings,friction_settings
    _,bridge=_patch(activation_policy='transverse_event_sequence',gap_check='straight_patch',
        normal_integration='straight_segmented',normal_integration_settings=normal_settings(),
        friction_integration='replay',friction_integration_settings=friction_settings())
    _,legacy=_replay_patch()
    assert bridge.pair.definition_sha256!=legacy.pair.definition_sha256
    folder=Path(__file__).parents[1]/'docs/d1_review_support/contact_c5_native_surface_point_20261002'
    saved=json.loads((folder/'replay_owner_second_load_rejected_path.json').read_text())
    field=NativeSurfaceHistoryField(bridge.pair,
        NativeS3MaterialConfiguration(**{k:np.asarray(v) for k,v in saved['initial'].items()}),
        tuple(NativeSurfaceMotionSegment(**{k:np.asarray(v) for k,v in s.items()}) for s in saved['segments']),
        maximum_intervals=saved['maximum_intervals'])
    value=field.query(.7244843513242318,3.1990185900472157,budget=NativeSurfaceReplayBudget(30))
    assert value.history.partner_key is None and value.history.cumulative_dissipation_density>0
    assert value.last_contribution.profile=='NATIVE_S3_OPEN_EVENT_SEQUENCE_POINT_DEV_V1'
    assert len(value.last_contribution.event_fractions)==2
    assert np.array_equal(value.last_contribution.residual,np.zeros(60))


def test_sequence_budget_and_tangency_remain_explicit_non_success():
    field,pair,history,segment=pulse()
    with pytest.raises((MemoryError,ValueError)):
        locate_material_event_sequence(pair,field.initial,segment.translations,segment.angular,segment.shell_increment,maximum_intervals=1)
    field,pair,history,segment=pulse(.03)
    with pytest.raises((MemoryError,ValueError)):
        locate_material_event_sequence(pair,field.initial,segment.translations,segment.angular,segment.shell_increment,maximum_intervals=32)


def test_two_chart_admitted_segments_accumulate_physical_history():
    from anysolver.general_contact.native_surface_path import material_path_pose
    field,pair,history,segment=pulse()
    first=evaluate_open_event_sequence(pair,field.initial,history,segment.translations,segment.angular,segment.shell_increment)
    endpoint=material_path_pose(field.initial,segment.translations,segment.angular,segment.shell_increment,1.)
    both=evaluate_open_event_sequence(pair,endpoint,first.trial.candidate_state,
        segment.translations,-segment.angular,segment.shell_increment)
    assert len(both.event_fractions)==2
    assert both.history_evaluations==pair.event_history_substeps+3
    assert both.trial.dissipated_increment_density==pytest.approx(first.trial.dissipated_increment_density,rel=1e-9)
    assert both.trial.candidate_state.cumulative_dissipation_density==pytest.approx(2*first.trial.dissipated_increment_density,rel=1e-9)
    assert both.trial.released_storage_density==pytest.approx(first.trial.released_storage_density,rel=1e-9)
    assert both.trial.candidate_state.cumulative_plastic_slip==pytest.approx(2*first.trial.candidate_state.cumulative_plastic_slip,rel=1e-9)
    assert both.trial.candidate_state.partner_key is None


def test_saved_two_event_point_replays_closed_window(tmp_path):
    import json,os
    from pathlib import Path
    from anysolver.general_contact.native_surface_history import NativeSurfaceHistoryField
    from anysolver.general_contact.native_surface_s3_friction import NativeS3MaterialConfiguration
    from anysolver.general_contact.native_surface_path import material_path_pose
    from test_general_contact_native_surface_replay_owner import _replay_patch
    folder=Path(__file__).parents[1]/'docs/d1_review_support/contact_c5_native_surface_point_20261002'
    saved=json.loads((folder/'replay_owner_second_load_rejected_path.json').read_text())
    _,bridge=_replay_patch()
    field=NativeSurfaceHistoryField(bridge.pair,
        NativeS3MaterialConfiguration(**{k:np.asarray(v) for k,v in saved['initial'].items()}),
        tuple(NativeSurfaceMotionSegment(**{k:np.asarray(v) for k,v in s.items()}) for s in saved['segments']),
        maximum_intervals=saved['maximum_intervals'])
    pair=field.pair_at(.7244843513242318,3.1990185900472157);pose=field.initial
    state=initial_friction_point(pair.target.physical_pose(pose.shell_displacement).material_frame)
    value=None
    for index,segment in enumerate(field.segments):
        if index==1:
            value=evaluate_open_event_sequence(pair,pose,state,segment.translations,segment.angular,segment.shell_increment,
                maximum_intervals=field.maximum_intervals)
            state=value.trial.candidate_state
        else:
            result=pair.evaluate_path(pose,state,segment.translations,segment.angular,segment.shell_increment,
                maximum_intervals=field.maximum_intervals)
            state=result.contribution.trial.candidate_state
        pose=material_path_pose(pose,segment.translations,segment.angular,segment.shell_increment,1.)
    assert len(value.event_fractions)==2 and state.partner_key is None
    assert state.cumulative_dissipation_density>0
    output=Path(os.environ.get('RUNNER_TEMP',str(tmp_path)))/'open_sequence_saved_point.json'
    output.write_text(json.dumps(dict(roots=value.event_fractions,intervals=value.ownership_intervals,
        history_evaluations=value.history_evaluations,dissipation=state.cumulative_dissipation_density,
        released_storage=value.trial.released_storage_density,gap=value.normal_gap_m),indent=2)+'\n')
