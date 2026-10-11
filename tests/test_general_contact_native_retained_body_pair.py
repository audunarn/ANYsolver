"""Focused connected-body development controls; independent straight line law."""
from dataclasses import replace
from pathlib import Path
from hashlib import sha256
import json, os, time
import numpy as np
import pytest
from examples.general_contact_native_retained_body_pair import analysis
from anysolver.general_contact.native_retained_body_pair import omitted_cell_dominated
from test_general_contact_native_curved_static import _canonical_fixture_payload


def test_complete_line_potential_work_crossblocks_and_refusals():
    owner=analysis();ctx=owner.context;initial=ctx.initial.mechanical
    positions=initial.positions.copy();positions[5:,1]=.09998
    pose=replace(initial,positions=positions)
    result=owner.contact.evaluate(pose);g=-.00002;k=4000.;length=2.
    assert ctx.count==156
    assert result.native_residual_component_error>=result.force_error_n
    assert result.native_tangent_component_error>=result.tangent_error_n_per_m
    assert result.potential_j==pytest.approx(.5*k*length*g*g,rel=1e-8)
    assert result.beam_a_force_n[1]==pytest.approx(k*length*g,rel=1e-8)
    assert result.beam_b_force_n[1]==pytest.approx(-k*length*g,rel=1e-8)
    assert result.beam_a_moment_nm[2]==pytest.approx(k*length*g,rel=1e-8)
    assert np.linalg.norm(result.tangent[:30,30:60])>0
    direction=np.zeros(ctx.count);direction[6*2+1]=1.
    # Shared middle junction's hat function integrates to .5 m; scalar line
    # distance derivative is -1 on body A: directional dE = -k*g*.5.
    assert result.residual@direction==pytest.approx(-k*g*.5,rel=1e-8)
    assert result.conservative_lower_gap_m<=g+1e-13
    with pytest.raises(ValueError):
        owner.contact.bodies=((11,),(12,13,14));owner._guard()


def test_endpoint_plateau_refusal_and_internal_motion():
    source=np.array(((0.,-.2,0.),(0.,0.,0.),(0.,.2,0.)))
    target=np.array(((0.,0.,0.),(.5,0.,0.),(1.,0.,0.)))
    assert not omitted_cell_dominated(source,target,(target[0],target[-1]),0.,1.,1e-12,(True,False))
    source=np.array(((-1.,.1,0.),(-.75,.1,0.),(-.5,.1,0.)))
    assert omitted_cell_dominated(source,target,(target[0],target[-1]),0.,1.,1e-12,(True,False))
    moved=target.copy();moved[1]=(-1.,.1,0.)
    assert not omitted_cell_dominated(source,moved,(target[0],target[-1]),0.,1.,1e-12,(True,False))


def test_default_saved_curved_energy_and_identity():
    from test_general_contact_native_curved_fibre_pair_static import _curved_owner
    from anysolver._ge_beam3_p5_seeded.codec import _load
    owner=_curved_owner()
    fixture=Path(__file__).parent/'data/general_contact_native_curved_fibre_pair_v14.checkpoint'
    capsule=_load(_canonical_fixture_payload(fixture).decode('ascii'))
    assert owner.identity==capsule['identity']
    record=capsule['records'][-1]
    raw=_canonical_fixture_payload(fixture)
    state,records=owner._restore(raw,sha256(raw).hexdigest())
    assert state.contact.potential_j>0
    assert owner._checkpoint(records)==raw


def test_active_connected_static_restart_and_rollback():
    if os.environ.get('CONTACT_NATIVE_BODY_SOLVE')!='1':pytest.skip('explicit bounded active solve')
    owner=analysis();initial=owner._checkpoint(())
    result=owner.solve()
    record=os.environ.get('CONTACT_APP_RESULT_RECORD')
    if record:Path(record).write_text(json.dumps({'result':str(result)},indent=2))
    assert result.status=='completed', result.failure
    assert result.accepted.contact.potential_j>0
    restored,records=analysis()._restore(result.checkpoint,result.checkpoint_sha256)
    assert restored.completed_targets==1
    assert analysis()._checkpoint(records)==result.checkpoint
    assert owner._checkpoint(())==initial


def test_bound_chain_and_indices_mutations_failclosed():
    owner=analysis();pose=owner.initial.mechanical
    owner.contact.chains=(owner.contact.chains[0][:-1],owner.contact.chains[1])
    with pytest.raises(ValueError):owner._physical_gap(pose)
    owner=analysis();owner.indices=()
    with pytest.raises(ValueError):owner._physical_gap(owner.initial.mechanical)

    owner=analysis();owner.contact.cells[0].geometry.cell=1
    with pytest.raises(ValueError):owner._physical_gap(owner.initial.mechanical)
