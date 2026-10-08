"""One new two-endpoint API check; existing temporal campaigns are not replayed."""
from contextlib import contextmanager
from dataclasses import replace
from fractions import Fraction
from hashlib import sha256
import inspect
import json
import os
from pathlib import Path
from time import perf_counter
import numpy as np
import pytest

from anysolver.ge_beam3_native_dynamics import (
    create_analysis, SELECTOR, workflow_provenance, MidpointState, MidpointCandidate)
from anysolver.ge_beam3_native import PROFILE_BYTES as OLD_PROFILE_BYTES
from anysolver.boundary import BoundaryCondition
from anysolver.control import CancellationToken, SolveCancelled
from anysolver._ge_beam3_centered_finite_inertia import PHYSICAL_DOFS, ALGEBRAIC_DOFS
from anysolver._ge_beam3_p5.algebra import rotation
from anysolver._ge_beam3_p5_seeded.core import canonical
from native_contact_free_finite_velocity_dev import build_definition, initial_velocity


def test_two_step_native_dynamic_interface(record_property):
    started = perf_counter()
    inputs = json.loads(Path(os.environ['NATIVE_DYNAMIC_INTERFACE_INPUTS']).read_text())
    output = Path(os.environ['NATIVE_DYNAMIC_INTERFACE_RAW_OUTPUT'])
    assert not output.exists()
    evidence = dict(status='RUNNING', accepted_steps=0, endpoints=[], controls={},
                    source_sha256=inputs['source_sha256'], scope='development API routing only')
    def save(stage):
        evidence.update(last_stage=stage,elapsed_seconds=perf_counter()-started)
        output.write_text(json.dumps(evidence,indent=2)+'\n')
        print(json.dumps(dict(stage=stage,elapsed_seconds=evidence['elapsed_seconds'])),flush=True)
        assert evidence['elapsed_seconds'] < 120.
    def account(value):
        return {k:(v.tolist() if isinstance(v,np.ndarray) else
                   json.loads(v) if isinstance(v,bytes) else v)
                for k,v in vars(value).items()}
    def diff(a,b,key):
        return np.array([float(Fraction(float(h))+Fraction(float(l))-
                               Fraction(float(h0))-Fraction(float(l0)))
            for h,l,h0,l0 in zip(getattr(a,key),getattr(a,key+'_low'),
                                getattr(b,key),getattr(b,key+'_low'))])
    try:
        assert sha256(OLD_PROFILE_BYTES).hexdigest() == inputs['old_public_profile_sha256']
        module = Path(inspect.getsourcefile(create_analysis)).resolve()
        assert module == Path(inputs['managed_worktree'])/'src/anysolver/ge_beam3_native_dynamics.py'
        definition,points = build_definition()
        with pytest.raises(ValueError): create_analysis('ge-beam3-native',(definition,),())
        partial = BoundaryCondition('partial',[1],{'ux':0.})
        with pytest.raises(ValueError): create_analysis(SELECTOR,(definition,),(partial,))
        clamp = BoundaryCondition('clamp',[1],{k:0. for k in ('ux','uy','uz','rx','ry','rz')})
        default = create_analysis(SELECTOR,(definition,),(clamp,))
        assert default.current is None and default._context.stage_residual_tolerance == 1e-11
        analysis = create_analysis(SELECTOR,(definition,),(),stage_residual_tolerance=1e-15)
        assert len(analysis._context.physical_free)==15 and len(analysis._context.algebraic_free)==27
        with pytest.raises(ValueError): analysis.initialize(points,np.zeros((2,3,3)),np.zeros(15))
        assert analysis.current is None
        rot = rotation(np.array((2e-4,-1e-4,3e-4)))
        positions = points@rot.T+np.array((.002,-.001,.003))
        low = np.zeros((3,3)); low[0,0]=low[2,0]=1e-18
        frames = np.tile(rot,(2,1,1)); velocity = initial_velocity(positions)
        state = analysis.initialize(positions,frames,velocity,position_low=low)
        assert type(state) is MidpointState and state is analysis.current
        assert state is analysis._context.current
        assert np.array_equal(state.mechanical.positions,positions)
        assert np.array_equal(state.mechanical.position_low,low)
        assert np.array_equal(state.mechanical.cell_rotations[0],frames)
        assert np.array_equal(state.physical_velocity24[list(PHYSICAL_DOFS)],velocity)
        assert np.count_nonzero(state.physical_velocity24[list(ALGEBRAIC_DOFS[:9])]) == 0
        assert np.allclose(np.linalg.det(state.mechanical.nodal_frames),1.,rtol=0.,atol=1e-12)
        initial = analysis.endpoint_accounting(state)
        energy = initial.total_energy; assert energy>0.
        # Initial physical mass 2.7 per unit reference length, centered length=2.
        scales = dict(energy=energy,linear=np.sqrt(2.*5.4*energy),angular=2.*np.sqrt(2.*5.4*energy))
        evidence.update(initial=account(initial),initial_checks=analysis.initial_checks,
            initial_mechanical={k:v.tolist() for k,v in state.mechanical.descriptor().items()},
            physical_velocity15=velocity.tolist(),scales=scales,provenance=workflow_provenance(analysis))
        with pytest.raises(ValueError): analysis.trial(replace(state),dt=.001)
        with pytest.raises(NotImplementedError): analysis.restore_checkpoint(b'not-a-restart')
        with pytest.raises(NotImplementedError): analysis.create_checkpoint()
        token = CancellationToken(); token.cancel('API control')
        with pytest.raises(SolveCancelled): analysis.trial(state,dt=.001,cancellation_token=token)
        assert analysis.current is state
        previous = initial
        for index in range(2):
            before = canonical(state)
            candidate = analysis.trial(state,dt=.001)
            assert type(candidate) is MidpointCandidate and analysis.current is state
            with pytest.raises(ValueError): analysis.commit(replace(candidate))
            with pytest.raises(SolveCancelled): analysis.commit(candidate,cancellation_token=token)
            assert canonical(state)==before and analysis.current is state
            audit = analysis.candidate_stage_audit(candidate)
            assert audit.stage is candidate.stage
            with pytest.raises(ValueError): analysis.commit(audit)
            with pytest.raises(ValueError): analysis.discard(replace(candidate))
            # Publication exit failure exercises the unchanged atomic rollback.
            original = analysis._native._operation
            @contextmanager
            def fail_exit():
                with original():
                    yield
                    raise RuntimeError('injected API publication exit failure')
            analysis._native._operation = fail_exit
            try:
                with pytest.raises(RuntimeError,match='publication exit'): analysis.commit(candidate)
                assert analysis.current is state and canonical(state)==before
            finally:
                analysis._native._operation = original
            old_state = state
            state = analysis.commit(candidate)
            assert state is candidate.endpoint and state is analysis.current
            with pytest.raises(ValueError): analysis.trial(old_state,dt=.001)
            with pytest.raises(ValueError): analysis.candidate_stage_audit(candidate)
            with pytest.raises(ValueError): analysis.discard(candidate)
            now = analysis.endpoint_accounting(state)
            linear = float(np.linalg.norm(diff(now,previous,'linear_momentum'))/scales['linear'])
            angular = float(np.linalg.norm(diff(now,previous,'angular_momentum'))/scales['angular'])
            defects = dict(energy=abs(now.total_energy-previous.total_energy)/energy,
                           linear=linear,angular=angular)
            cumulative = dict(energy=abs(now.total_energy-initial.total_energy)/energy,
                linear=float(np.linalg.norm(diff(now,initial,'linear_momentum'))/scales['linear']),
                angular=float(np.linalg.norm(diff(now,initial,'angular_momentum'))/scales['angular']))
            load = analysis.physical_load_accounting(state.mechanical)
            evidence['endpoints'].append(dict(accounting=account(now),defects=defects,cumulative=cumulative,
                physical_velocity24=state.physical_velocity24.tolist(),
                stage_residual42=candidate.stage.residual.tolist(),unknown42=candidate.unknown42.tolist(),
                stage_residual_norm=candidate.stage_residual_norm,
                endpoint_algebraic_norm=candidate.endpoint_algebraic_norm,
                audit_context=audit.context_sha256,load=account(load)))
            evidence['accepted_steps'] += 1
            save('endpoint_'+str(index+1))
            assert max(defects.values()) <= 1e-6 and max(cumulative.values()) <= 1e-6
            assert candidate.stage_residual_norm <= 1e-15 and candidate.endpoint_algebraic_norm <= 1e-11
            assert abs(now.elastic_consistency_witness)/energy <= 1e-10
            assert np.count_nonzero(candidate.stage.inertia.mixed_inertia[list(ALGEBRAIC_DOFS)]) == 0
            assert np.count_nonzero(load.external_load42)==0
            assert canonical(state.histories)==canonical(state.origins)
            previous=now
        evidence['controls'] = dict(mapping=True,default_unchanged=True,scope_rejection=True,
            stale_forged_audit_rejection=True,cancellation=True,publication_rollback=True,restart_rejection=True)
        assert state.epoch==2 and state.time==.002
        assert analysis._context._dynamic._active_session is None
        evidence['status']='PASS'; save('complete')
        record_property('accepted_steps',2)
    except BaseException as exc:
        evidence.update(status='NONPASS',failure_type=type(exc).__name__,failure=str(exc))
        save('failure'); raise
