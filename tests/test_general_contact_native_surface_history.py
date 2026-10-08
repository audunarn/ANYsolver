"""History queries at old/new material coordinates without state interpolation."""
from dataclasses import asdict
from hashlib import sha256

import numpy as np
import pytest

from anysolver._ge_beam3_p5_seeded.core import sha
from anysolver.general_contact.native_surface_history import (
    NativeSurfaceHistoryField,NativeSurfaceMotionSegment,NativeSurfaceReplayBudget)
from anysolver.general_contact.native_surface_s3_friction import NativeS3MaterialConfiguration
from anysolver.general_contact.native_surface_transaction import NativeS3MaterialTransaction
from test_general_contact_native_surface_patch import _patch
from test_general_contact_native_surface_normal import _settings


def _origin(owner):
    original=owner.initial;nodes=owner.context.nodes[0]
    return NativeS3MaterialConfiguration(original.mechanical.positions[nodes],original.mechanical.position_low[nodes],
        original.mechanical.cell_rotations[0],original.shell_displacement)


def _segment(x,z):
    return NativeSurfaceMotionSegment(np.tile((x,0.,z),(3,1)),np.zeros((2,3)),np.zeros(18))


def test_new_material_query_first_touch_matches_scalar_slider_and_keeps_path():
    owner,bridge=_patch(activation_policy='transverse_events',gap_check='straight_patch')
    initial=_origin(owner);path=(_segment(.004,-.004),)
    field=NativeSurfaceHistoryField(bridge.pair,initial,path)
    before=field.identity;budget=NativeSurfaceReplayBudget(2)
    result=field.query(.43,np.pi+.013,budget=budget)
    assert all(result.pair.source.identity!=p.source.identity for p in bridge.pair.pairs)
    point=result.pair.source.evaluate(initial.positions,initial.position_low,initial.cell_rotations).surface_position
    target=result.pair.target.physical_pose(initial.shell_displacement)
    gap=float((point-np.asarray(target.position))@np.asarray(target.material_frame)[:,2])
    fraction=gap/.004;pressure=1e4*(.004-gap)
    traction=min(1000*.004*(1-fraction),.3*pressure)
    value=result.last_contribution
    assert value.event_fraction==pytest.approx(fraction,abs=1e-13)
    assert sum(value.residual[6*i] for i in range(3))==pytest.approx(traction,rel=1e-10)
    assert sum(value.residual[6*i+2] for i in range(3))==pytest.approx(-pressure,rel=1e-10)
    assert field.identity==before and budget.point_paths==2
    assert result.pair.reference_weight_m2==1.


def test_replay_matches_stored_nodes_through_open_recontact_and_caps():
    owner,bridge=_patch(activation_policy='transverse_events',gap_check='straight_patch')
    initial=_origin(owner);pose=initial;history=bridge.pair.initial_history(initial.shell_displacement)
    segments=(_segment(.004,-.004),_segment(.005,0.),_segment(0.,.006),_segment(-.003,-.006))
    for segment in segments:
        value=bridge.pair.evaluate_path(pose,history,segment.translations,segment.angular,segment.shell_increment)
        pose=value.configuration;history=value.contribution.trial.candidate_state
    field=NativeSurfaceHistoryField(bridge.pair,initial,segments)
    budget=NativeSurfaceReplayBudget((1+len(segments))*len(bridge.pair.pairs))
    for point,expected in zip(bridge.pair.pairs,history.points):
        query=field.query(point.source.xi,point.source.angle,budget=budget)
        assert asdict(query.history)==asdict(expected)
        assert sha(asdict(query.configuration))==sha(asdict(pose))
    assert any(h.cumulative_dissipation_density>0 for h in history.points)
    before=field.identity
    with pytest.raises(MemoryError,match='total replay'):
        field.query(.43,np.pi,budget=budget)
    assert field.identity==before
    with pytest.raises(MemoryError,match='segment cap'):
        NativeSurfaceHistoryField(bridge.pair,initial,segments,maximum_segments=2)


def test_history_snapshot_from_coupled_transaction_and_restored_path():
    owner,bridge=_patch(activation_policy='transverse_events',gap_check='straight_patch',
        normal_integration='straight_segmented',normal_integration_settings=_settings())
    transaction=NativeS3MaterialTransaction(bridge)
    owner.solve_material_increment(transaction,1.)
    before=transaction.checkpoint()
    field=NativeSurfaceHistoryField.from_transaction(transaction)
    assert field.accepted_origin_sha256==transaction.origin_sha256
    assert field.maximum_intervals==owner.maximum_swept_intervals
    with pytest.raises(ValueError,match='bound history cap'):
        field.query(.79,np.pi+.013,budget=NativeSurfaceReplayBudget(2),
            maximum_intervals=owner.maximum_swept_intervals+1)
    budget=NativeSurfaceReplayBudget(10)
    for pair,expected in zip(bridge.pair.pairs,transaction.accepted.friction_history.points):
        assert asdict(field.query(pair.source.xi,pair.source.angle,budget=budget).history)==asdict(expected)
    new=field.query(.79,np.pi+.013,budget=budget)
    assert new.history.partner_key is not None
    assert transaction.checkpoint()==before
    restored=NativeS3MaterialTransaction.restore(bridge,before,sha256(before).hexdigest())
    replay=NativeSurfaceHistoryField.from_transaction(restored)
    assert replay.identity==field.identity
    assert asdict(replay.query(.79,np.pi+.013,budget=NativeSurfaceReplayBudget(2)).history)==asdict(new.history)
