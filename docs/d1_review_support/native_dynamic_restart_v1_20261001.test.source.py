"""Prospective bounded split restart test. Not authorized/executed yet."""
from contextlib import contextmanager
from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
from time import perf_counter
import numpy as np
import pytest

from anysolver.ge_beam3_native_dynamics import create_analysis, SELECTOR, workflow_provenance
from anysolver._ge_beam3_native_dynamic_restart import MAX_BYTES
from anysolver._ge_beam3_p5_seeded.core import canonical, sha, NativeMaterialError
from anysolver._ge_beam3_p5.algebra import rotation
from anysolver._native_reference_modal import _owned
from anysolver.control import CancellationToken, SolveCancelled
from native_contact_free_finite_velocity_dev import build_definition, initial_velocity


def test_committed_native_dynamic_split_restart(record_property):
    started=perf_counter()
    output=Path(os.environ['NATIVE_DYNAMIC_RESTART_RAW_OUTPUT'])
    assert not output.exists()
    evidence=dict(status='RUNNING',accepted_steps=0,scope='development restart only',
                  trajectories={},negative_controls=[],restore_controls={})
    def save(stage):
        evidence.update(last_stage=stage,elapsed_seconds=perf_counter()-started)
        output.write_text(json.dumps(evidence,indent=2)+'\n')
        print(json.dumps(dict(stage=stage,elapsed_seconds=evidence['elapsed_seconds'])),flush=True)
        assert evidence['elapsed_seconds']<120.
    def new_owner():
        definition,_=build_definition()
        return create_analysis(SELECTOR,(definition,),())
    def fresh(owner):
        c=owner._context
        assert c.current is None and c._current is None and c._visible_current is None
        assert c._current_bytes is None and not c._issued and not c._candidates
        assert c._initial_checks is None and c._restore_checks is None
        assert c._dynamic._active_session is None and c._work_session is None
        assert len(c._dynamic._issued)==1
    def account(owner,state): return json.loads(canonical(owner.endpoint_accounting(state)))
    def modified(raw,change):
        row=json.loads(raw);change(row)
        row['state_sha256']=sha(row['state'])
        row['checkpoint_sha256']=sha({k:v for k,v in row.items() if k!='checkpoint_sha256'})
        return canonical(row)
    def reject(raw,label,digest=None):
        owner=new_owner();fresh(owner)
        with pytest.raises((ValueError,NativeMaterialError)):
            owner.restore_checkpoint(raw,expected_sha256=sha256(raw).hexdigest() if digest is None else digest)
        fresh(owner);evidence['negative_controls'].append(label)
    def advance(owner,state,label,pending_control=False):
        c=owner._context;original=c._stage;observed=[]
        def observe(accepted,unknown,h,token=None):
            stage=original(accepted,unknown,h,token)
            observed.append(dict(unknown42=np.asarray(unknown).tolist(),
                structural_residual42=stage.structural_residual.tolist(),
                inertial_work42=stage.inertia.mixed_inertia.tolist(),residual42=stage.residual.tolist(),
                stage_sha256=sha(stage),predecessor_sha256=sha(accepted),
                context_sha256=c._identity,active_trial_session=c._work_session is not None))
            assert len(observed)<=128
            return stage
        c._stage=observe
        try: candidate=owner.trial(state,dt=.001)
        finally:
            c._stage=original
            evidence.setdefault('stage_observations',{})[label]=observed
        if pending_control:
            with pytest.raises(ValueError,match='pending'):
                owner.create_checkpoint()
            assert owner.current is state
            owner.candidate_stage_audit(candidate)  # Historical evidence, no wire credential.
            evidence['restore_controls']['pending_export_rejection']=True
        before=owner.endpoint_accounting(state)
        state=owner.commit(candidate)
        now=owner.endpoint_accounting(state)
        energy=evidence['initial_energy_j'];pstar=np.sqrt(2.*5.4*energy);hstar=2.*pstar
        # Complete high+low endpoint differences retained in the raw record.
        from fractions import Fraction
        def delta(key,baseline):
            return np.array([float(Fraction(float(h))+Fraction(float(l))-
                                   Fraction(float(h0))-Fraction(float(l0)))
                for h,l,h0,l0 in zip(getattr(now,key),getattr(now,key+'_low'),
                    getattr(baseline,key),getattr(baseline,key+'_low'))])
        defects=dict(energy=abs(now.total_energy-before.total_energy)/energy,
                     P=float(np.linalg.norm(delta('linear_momentum',before))/pstar),
                     H=float(np.linalg.norm(delta('angular_momentum',before))/hstar))
        cumulative=dict(energy=abs(now.total_energy-initial_account.total_energy)/energy,
            P=float(np.linalg.norm(delta('linear_momentum',initial_account))/pstar),
            H=float(np.linalg.norm(delta('angular_momentum',initial_account))/hstar))
        evidence['trajectories'][label]=dict(state=json.loads(canonical(state)),
            accounting=json.loads(canonical(now)),stage_residual_norm=candidate.stage_residual_norm,
            endpoint_algebraic_norm=candidate.endpoint_algebraic_norm,step_defects=defects,
            cumulative_defects=cumulative)
        evidence['accepted_steps']+=1;save(label)
        assert max(defects.values())<=1e-6 and max(cumulative.values())<=1e-6
        assert candidate.stage_residual_norm<=1e-11 and candidate.endpoint_algebraic_norm<=1e-11
        assert now.elastic_consistency_witness/energy<=1e-10
        return state
    try:
        owner=new_owner();definition,points=build_definition()
        rot=rotation(np.array((2e-4,-1e-4,3e-4)))
        positions=points@rot.T+np.array((.002,-.001,.003))
        low=np.zeros((3,3));low[0,0]=low[2,0]=1e-18
        cells=np.tile(rot,(2,1,1));velocity=initial_velocity(positions)
        initial=owner.initialize(positions,cells,velocity,position_low=low)
        initial_account=owner.endpoint_accounting(initial)
        evidence['initial_energy_j']=initial_account.total_energy
        evidence['initial_accounting']=json.loads(canonical(initial_account))
        assert evidence['initial_energy_j']>0.
        evidence['profile']=workflow_provenance(owner)
        u1=advance(owner,initial,'uninterrupted1')
        u2=advance(owner,u1,'uninterrupted2')
        split=new_owner();s0=split.initialize(positions,cells,velocity,position_low=low)
        assert canonical(s0)==canonical(initial)
        s1=advance(split,s0,'split1',pending_control=True)
        raw=split.create_checkpoint();digest=sha256(raw).hexdigest()
        evidence['checkpoint_ascii']=raw.decode('ascii');evidence['checkpoint_sha256']=digest
        with pytest.raises(ValueError,match='fresh'):
            split.restore_checkpoint(raw,expected_sha256=digest)
        assert split.current is s1
        reject(raw,'wrong_external_digest','0'*64)
        reject(raw+b' ','noncanonical')
        reject(b'x'*(MAX_BYTES+1),'byte_bound')
        reject(modified(raw,lambda d:d.update(unknown=True)),'unknown_key')
        reject(modified(raw,lambda d:d['header']['settings'].update(stage_residual_tolerance=1e-15)),'settings')
        reject(modified(raw,lambda d:d['header'].update(analysis_sha256='0'*64)),'model')
        reject(modified(raw,lambda d:d['header']['owned_source_sha256'].__setitem__('_ge_beam3_native_midpoint.py','0'*64)),'artifact')
        reject(modified(raw,lambda d:d['state']['mechanical'].update(cell_rotations=np.zeros((1,2,3,3)).tolist())),'frames')
        reject(modified(raw,lambda d:d['state']['histories'][0]['stations'][0]['plastic'][0].__setitem__(0,.1)),'history')
        reject(modified(raw,lambda d:d['state']['physical_velocity24'].__setitem__(3,.1)),'algebraic_velocity')
        reject(modified(raw,lambda d:d['state']['physical_acceleration24'].__setitem__(3,.1)),'algebraic_acceleration')
        reject(modified(raw,lambda d:d['state']['physical_acceleration24'].__setitem__(0,d['state']['physical_acceleration24'][0]+.1)), 'physical_balance')
        # Literal residual-only negative witness using measured actual C_z.
        negative=new_owner();c=negative._context;original=c._loaded_work
        def bad_algebraic_work(mechanical,origins):
            work=original(mechanical,origins);z=list(c.algebraic_free)
            u,_,_=np.linalg.svd(work.spatial_jacobian[np.ix_(z,z)])
            residual=np.array(work.residual,copy=True);residual[z]=1e-12*u[:,-1]
            step=np.zeros(42)
            step[z]=np.linalg.solve(work.spatial_jacobian[np.ix_(z,z)],-residual[z])
            correction=max(float(np.linalg.norm(step[[i for i in z if i<24]])),
                float(np.linalg.norm(step[24:]))/max(1.,float(np.linalg.norm(mechanical.resultants))))
            norm=c._norm(residual,z)
            evidence['injected_algebraic_control']=dict(scaled_residual=norm,correction=correction,
                scope='injected residual-only witness control; not physical source evidence')
            assert norm<=1e-11 and correction>1e-11
            return replace(work,residual=_owned(residual))
        c._loaded_work=bad_algebraic_work
        try:
            with pytest.raises(ValueError,match='correction'):
                negative.restore_checkpoint(raw,expected_sha256=digest)
        finally: c._loaded_work=original
        fresh(negative)
        cancelled=new_owner();token=CancellationToken();token.cancel('restart control')
        with pytest.raises(SolveCancelled): cancelled.restore_checkpoint(raw,expected_sha256=digest,cancellation_token=token)
        fresh(cancelled)
        class CancelReady(CancellationToken):
            def raise_if_cancelled(self,stage=''):
                if stage=='midpoint.restore.ready': self.cancel('before restore publication')
                return super().raise_if_cancelled(stage)
        cancelled=new_owner()
        with pytest.raises(SolveCancelled): cancelled.restore_checkpoint(raw,expected_sha256=digest,cancellation_token=CancelReady())
        fresh(cancelled)
        failed=new_owner();original_operation=failed._native._operation
        @contextmanager
        def exit_failure():
            with original_operation():
                yield
                raise RuntimeError('injected restart publication exit')
        failed._native._operation=exit_failure
        try:
            with pytest.raises(RuntimeError,match='publication exit'):
                failed.restore_checkpoint(raw,expected_sha256=digest)
        finally: failed._native._operation=original_operation
        fresh(failed)
        restored=new_owner()
        state=restored.restore_checkpoint(raw,expected_sha256=digest)
        assert state is restored.current and state is not s1
        assert canonical(state)==canonical(s1)
        assert restored.create_checkpoint()==raw
        assert restored.initial_checks==split.initial_checks
        evidence['restore_checks']=restored.restore_checks
        with pytest.raises(ValueError): restored.trial(s1,dt=.001)
        with pytest.raises(ValueError): restored.trial(replace(state),dt=.001)
        final=advance(restored,state,'restored2')
        assert canonical(final)==canonical(u2)
        assert canonical(restored.endpoint_accounting(final))==canonical(owner.endpoint_accounting(u2))
        assert final.time==.002 and final.epoch==2
        evidence['restore_controls'].update(fresh_only=True,typed_semantics=True,
            correction_witness=True,cancellation=True,publication_rollback=True,
            canonical_roundtrip=True,old_object_rejection=True,split_state_exact=True)
        evidence['status']='PASS';save('complete')
        record_property('accepted_steps',4)
    except BaseException as error:
        evidence.update(status='NONPASS',failure_type=type(error).__name__,failure=str(error))
        save('failure');raise
