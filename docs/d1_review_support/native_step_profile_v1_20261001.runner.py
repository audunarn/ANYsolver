"""One source-bound two-step cProfile probe; no unprofiled benchmark claim."""
from contextlib import nullcontext
import cProfile
import pstats
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
from time import perf_counter
import traceback

INPUT = Path(os.environ['NATIVE_STEP_PROFILE_INPUTS'])
spec = json.loads(INPUT.read_text())
for path, expected in spec['source_sha256'].items():
    assert sha256(Path(path).read_bytes()).hexdigest() == expected, path
for name, expected in spec['environment'].items():
    assert os.environ.get(name) == expected, name
print(json.dumps(dict(stage='authenticated_before_import', input_sha256=sha256(INPUT.read_bytes()).hexdigest())), flush=True)

import numpy as np
import anysolver
from anysolver.ge_beam3_native_dynamics import create_analysis, SELECTOR
from anysolver._ge_beam3_p5_seeded.core import canonical, sha
from anysolver import _ge_beam3_operator_validation_scope as scheduling
from test_ge_beam3_native_midpoint import make_analysis
from test_ge_beam3_native_finite_spin_acceleration_chart import P, Z, accounting, momentum_delta
from native_forced_response_reference import positions

assert Path(anysolver.__file__).resolve() == Path(spec['actual_anysolver_module']).resolve()
raw_path, journal_path, state_path = (Path(spec[key]) for key in ('raw_output', 'stage_journal', 'state_journal'))
assert not raw_path.exists() and not journal_path.exists() and not state_path.exists()
started = perf_counter()
result = dict(status='RUNNING', phases=[], criteria=spec['criteria'],
    module_file=str(Path(anysolver.__file__).resolve()), input_sha256=sha256(INPUT.read_bytes()).hexdigest(),
    effective_environment={key:os.environ[key] for key in spec['environment']},
    profile_scope='two steps only; creation/initialization outside; includes declared evidence recovery/serialization',
    claim='development two-step profile only; no unprofiled benchmark, temporal accuracy or new qualification')
journal = journal_path.open('xb')
journal_hash = sha256()
states = state_path.open('xb')
states_hash = sha256()
profiler = cProfile.Profile()
profile_enabled = False

def signed_endpoint(owner, state, account):
    c = owner._context
    with c._atomic_operation():
        c._guard()
        work = c._loaded_work(state.mechanical, state.histories)
        inertia = c._inertia(state.mechanical, state.physical_velocity24, state.physical_acceleration24)
    return dict(state=json.loads(canonical(state)), accounting=accounting(account),
        R42=work.residual.tolist(), I42=inertia.mixed_inertia.tolist(), J42=work.spatial_jacobian.tolist(),
        M42=inertia.mixed_mass.tolist(), balance42=(work.residual+inertia.mixed_inertia).tolist(),
        scaled_free_balance=c._norm(work.residual+inertia.mixed_inertia,c.free))

def persist_state(phase, kind, row):
    record = canonical(dict(phase=phase['index'],mode=phase['mode'],kind=kind,row=row,
        scales=phase['scales'],criteria=spec['criteria']))+b'\n'
    states.write(record); states.flush(); states_hash.update(record)

try:
    saved_bytes = Path(spec['mass_reference']).read_bytes()
    assert sha256(saved_bytes).hexdigest() == spec['mass_reference_sha256']
    saved = json.loads(saved_bytes)['reference']
    m0 = np.asarray(saved['M42'])
    for phase_index, mode in enumerate(('full',)):
        phase_started = perf_counter()
        phase = dict(index=phase_index, mode=mode, status='RUNNING', endpoints=[], original_stages=[],
            stage_counts=[], method_wall_seconds=[], solver_committed_steps=0, gate_passing_steps=0)
        result['phases'].append(phase)
        print(json.dumps(dict(stage='phase_start', index=phase_index, mode=mode, elapsed=perf_counter()-started)), flush=True)
        _, definition = make_analysis()
        owner = create_analysis(SELECTOR,(definition,),(),inertia_order=24,
            stage_coordinates='acceleration',stage_residual_tolerance=1e-12)
        c = owner._context
        assert c.runtime_limit_seconds == c._dynamic.runtime_limit_seconds == 120.
        assert c.fixed == () and tuple(c.physical_free) == P and tuple(c.algebraic_free) == Z
        assert c.load_pattern is None and c.element.operator.order == 4
        assert canonical(c._reference_mechanical) == canonical(saved['reference_mechanical'])
        assert canonical(c._reference_origins) == canonical(saved['virgin_histories'])
        assert np.array_equal(c.analysis._inertias[c.element.element_id],saved['section_inertia'])
        reference = c._reference_mechanical
        velocity = np.zeros(24)
        omega = np.array((35.,-25.,20.))
        for node, point in enumerate(positions(reference)):
            velocity[6*node:6*node+3] = np.cross(omega,point)
        velocity[18:21] = velocity[21:24] = omega
        t = np.zeros((42,3))
        for node in range(3): t[6*node:6*node+3] = np.eye(3)
        mass = float(np.trace(t.T@m0@t)/3)
        energy = float(.5*velocity@m0[:24,:24]@velocity)
        speed = float(np.sqrt(2*energy/mass))
        scales = dict(mass=mass,energy=energy,momentum=mass*speed,angular_momentum=2*mass*speed)
        assert all(np.isfinite(x) and x>0 for x in scales.values())
        state = owner.initialize(physical_velocity15=velocity[list(P)])
        initial = previous = owner.endpoint_accounting(state)
        phase['scales'] = scales
        phase['initial'] = signed_endpoint(owner,state,initial)
        phase['initial_checks'] = owner.initial_checks
        persist_state(phase,'initial_before_gates',phase['initial'])
        assert phase['initial']['scaled_free_balance'] <= 1e-11
        assert abs(initial.kinetic_energy-energy)/energy <= 1e-12
        assert np.linalg.norm(np.asarray(phase['initial']['M42'])-m0)/np.linalg.norm(m0) <= 1e-12
        assert canonical(state.mechanical) == canonical(reference)
        phase['initialization_seconds'] = perf_counter()-phase_started
        operations_started = perf_counter()
        profiler.enable(); profile_enabled = True
        scope = scheduling.operator_validation_scope() if mode=='scoped' else nullcontext()
        with scope:
            for step in range(2):
                prior = state
                original_stage = c._stage
                before = len(phase['original_stages'])
                def observe(predecessor, unknown, h, token=None):
                    actual = original_stage(predecessor,unknown,h,token)
                    payload = dict(phase=phase_index,step=step+1,unknown42=np.asarray(unknown).tolist(),
                        stage=json.loads(canonical(actual)),predecessor_sha256=sha(predecessor),
                        predecessor_epoch=predecessor.epoch,context_sha256=c._identity)
                    record = canonical(payload)+b'\n'
                    offset = journal.tell()
                    assert journal.write(record) == len(record)
                    journal.flush(); journal_hash.update(record)
                    phase['original_stages'].append(dict(offset_bytes=offset,length_bytes=len(record),
                        sha256=sha256(record).hexdigest(),step=step+1,
                        physical_sha256=sha(dict(unknown42=payload['unknown42'],stage=payload['stage']))))
                    assert len(phase['original_stages'])-before <= 128
                    return actual
                c._stage = observe
                method_times = dict(step=step+1)
                mark = perf_counter()
                try:
                    candidate = owner.trial(prior,dt=.00025)
                finally:
                    c._stage = original_stage
                method_times['trial'] = perf_counter()-mark
                mark = perf_counter()
                audit = owner.candidate_stage_audit(candidate)
                method_times['candidate_stage_audit'] = perf_counter()-mark
                phase['pending_candidate'] = json.loads(canonical(candidate))
                audit_row = asdict(audit)
                audit_row['session_provenance'] = json.loads(audit_row['session_provenance'])
                phase['pending_audit'] = json.loads(canonical(audit_row))
                assert candidate.stage_residual_norm <= 1e-12
                assert candidate.endpoint_algebraic_norm <= 1e-11
                assert audit.stage_coordinates == 'acceleration'
                mark = perf_counter()
                state = owner.commit(candidate)
                method_times['commit'] = perf_counter()-mark
                phase['solver_committed_steps'] += 1
                phase['committed_state_before_accounting'] = json.loads(canonical(state))
                mark = perf_counter()
                now = owner.endpoint_accounting(state)
                method_times['endpoint_accounting'] = perf_counter()-mark
                mark = perf_counter()
                row = signed_endpoint(owner,state,now)
                method_times['harness_signed_endpoint_recovery'] = perf_counter()-mark
                phase['method_wall_seconds'].append(method_times)
                row['candidate'] = phase['pending_candidate']
                row['audit'] = phase['pending_audit']
                step_defects = dict(P=float(np.linalg.norm(momentum_delta(now,previous,'linear'))/scales['momentum']),
                    H=float(np.linalg.norm(momentum_delta(now,previous,'angular'))/scales['angular_momentum']),
                    E=abs(now.total_energy-previous.total_energy)/energy)
                total_defects = dict(P=float(np.linalg.norm(momentum_delta(now,initial,'linear'))/scales['momentum']),
                    H=float(np.linalg.norm(momentum_delta(now,initial,'angular'))/scales['angular_momentum']),
                    E=abs(now.total_energy-initial.total_energy)/energy)
                row.update(normalized_step_defects=step_defects, normalized_cumulative_defects=total_defects,
                    elastic_witness_normalized=now.elastic_consistency_witness/energy,gate_status='UNASSESSED')
                phase['endpoints'].append(row)
                persist_state(phase,'committed_endpoint_before_gates',row)
                assert max(step_defects.values()) <= 1e-6 and max(total_defects.values()) <= 1e-6
                assert row['scaled_free_balance'] <= 1e-11 and row['elastic_witness_normalized'] <= 1e-10
                assert np.count_nonzero(np.asarray(row['I42'])[list(Z)]) == 0
                assert np.count_nonzero(state.physical_velocity24[[i for i in range(24) if i not in P]]) == 0
                assert np.count_nonzero(state.physical_acceleration24[[i for i in range(24) if i not in P]]) == 0
                assert canonical(state.histories) == canonical(c._reference_origins)
                assert state.epoch == step+1 and state.time == prior.time+.00025
                row['gate_status'] = 'PASS'
                phase['gate_passing_steps'] += 1
                phase['stage_counts'].append(len(phase['original_stages'])-before)
                previous = now
                print(json.dumps(dict(stage='step_pass',phase=phase_index,step=step+1,elapsed=perf_counter()-started)),flush=True)
        phase['operations_seconds'] = perf_counter()-operations_started
        profiler.disable(); profile_enabled = False
        phase['status'] = 'PASS'
        phase['elapsed_seconds'] = perf_counter()-phase_started
        assert phase['stage_counts'] == [3]*2
        assert scheduling._ACTIVE.get() is None
    result['status'] = 'PASS'
except BaseException as exc:
    result['status'] = 'NONPASS'
    result['failure'] = dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc())
    raise
finally:
    if profile_enabled: profiler.disable()
    profile_path = Path(spec['profile_output'])
    assert not profile_path.exists()
    profiler.dump_stats(str(profile_path))
    stats = pstats.Stats(profiler)
    def stat_row(key,value):
        cc,nc,tt,ct,callers = value
        return dict(file=key[0],line=key[1],function=key[2],primitive_calls=cc,total_calls=nc,
            self_seconds=tt,cumulative_seconds=ct,callers=[dict(file=k[0],line=k[1],function=k[2],
                profile_values=list(v) if isinstance(v,tuple) else v) for k,v in sorted(callers.items())])
    ordered = sorted(stats.stats.items(),key=lambda kv:kv[1][3],reverse=True)
    selected = ('_stage','_inertia','_loaded_work','_finish','endpoint_accounting',
        'evaluate_centered_finite_inertia','_endpoint_acceleration','_solve_algebraic','signed_endpoint','derivative')
    profile_summary = dict(total_profile_self_seconds=stats.total_tt,total_calls=stats.total_calls,
        primitive_calls=stats.prim_calls,top20_cumulative=[stat_row(k,v) for k,v in ordered[:20]],
        top20_self=[stat_row(k,v) for k,v in sorted(stats.stats.items(),key=lambda kv:kv[1][2],reverse=True)[:20]],
        selected=[stat_row(k,v) for k,v in ordered if k[2] in selected],
        missing_selected_names=[name for name in selected if not any(k[2]==name for k in stats.stats)])
    Path(spec['profile_summary']).write_text(json.dumps(profile_summary,indent=2)+'\n',encoding='utf-8')
    result['profile'] = dict(path=str(profile_path),sha256=sha256(profile_path.read_bytes()).hexdigest(),
        summary_path=spec['profile_summary'],total_profile_self_seconds=stats.total_tt)
    journal.flush(); journal.close()
    states.flush(); states.close()
    result['journal'] = dict(path=str(journal_path),bytes=journal_path.stat().st_size,sha256=journal_hash.hexdigest())
    result['state_journal'] = dict(path=str(state_path),bytes=state_path.stat().st_size,sha256=states_hash.hexdigest())
    result['elapsed_seconds'] = perf_counter()-started
    result['source_postverify'] = {path:sha256(Path(path).read_bytes()).hexdigest()==expected for path,expected in spec['source_sha256'].items()}
    with raw_path.open('xb') as stream: stream.write(canonical(result)+b'\n')
    print(json.dumps(dict(stage='complete',status=result['status'],elapsed=result['elapsed_seconds'])),flush=True)
