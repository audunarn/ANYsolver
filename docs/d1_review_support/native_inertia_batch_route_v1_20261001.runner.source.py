"""Balanced scalar/batched prepared finite-inertia route; original physical gates."""
from contextlib import nullcontext
from fractions import Fraction
import inspect
import statistics
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
from time import perf_counter
import traceback

INPUT = Path(os.environ['NATIVE_INERTIA_BATCH_ROUTE_INPUTS'])
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
from anysolver._ge_beam3_centered_finite_inertia import _CenteredFiniteKernel
from anysolver._ge_beam3_p5.inertia import LiftedInertia
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
    profile='none; balanced completephase timing with equal evidence overhead',
    claim='development cost/parity only; no temporal accuracy or new qualification')
journal = journal_path.open('xb')
journal_hash = sha256()
states = state_path.open('xb')
states_hash = sha256()
wired_function = _CenteredFiniteKernel.__dict__['evaluate']
scalar_function = LiftedInertia.evaluate
assert wired_function.__qualname__ == '_CenteredFiniteKernel.evaluate'
assert Path(inspect.getsourcefile(wired_function)).resolve() == Path(spec['wired_owner']).resolve()
assert Path(inspect.getsourcefile(scalar_function)).resolve() == Path(spec['scalar_owner']).resolve()
for name,function in (('scalar',scalar_function),('batch',wired_function)):
    assert sha256(inspect.getsource(function).encode('utf-8')).hexdigest()==spec['callable_source_sha256'][name]
active_kernel_calls = 0
selected_function = None

def make_characteristics(reference, mass, energy, speed):
    points = positions(reference)
    length = float(np.linalg.norm(points[-1]-points[0]))
    assert length > 0. and mass > 0. and speed > 0.
    return dict(length_m=length,mass_kg=mass,velocity_m_per_s=speed,omega_per_s=speed/length,
        acceleration_m_per_s2=speed**2/length,angular_acceleration_per_s2=speed**2/length**2,
        force_n=mass*speed**2/length,moment_nm=mass*speed**2,energy_j=energy,
        work_j=mass*speed**2,momentum_n_s=mass*speed,angular_momentum_nm_s=mass*length*speed)


def compare_phase(actual, reference, scales):
    """Complete physical comparison with frozen work-conjugate dimensional maps.

    Error is normalized-difference norm/max(1, normalized-reference norm).
    The1 is the declared positive characteristic in physical units, not a floor
    inferred from a cancelled output. All source/context/session IDs remain raw
    authenticated provenance; none is substituted for a physical comparison.
    """
    ledger = {}
    L,m,V,omega = (scales[k] for k in ('length_m','mass_kg','velocity_m_per_s','omega_per_s'))
    E,W,F,T = (scales[k] for k in ('energy_j','work_j','force_n','moment_nm'))
    q = np.ones(42)
    q[[0,1,2,6,7,8,12,13,14]] = L
    q[24:30],q[30:] = F,T  # z6 then ell12, exact retained conjugate ordering.
    u = q.copy()
    u[[0,1,2,6,7,8,12,13,14]] = scales['acceleration_m_per_s2']
    u[18:24] = scales['angular_acceleration_per_s2']
    vscale = np.ones(24)*omega
    vscale[[0,1,2,6,7,8,12,13,14]] = V
    ascale = np.ones(24)*scales['angular_acceleration_per_s2']
    ascale[[0,1,2,6,7,8,12,13,14]] = scales['acceleration_m_per_s2']
    def check(name,a,b,row=1.,col=None,divisor=1.):
        a,b = np.asarray(a,dtype=float),np.asarray(b,dtype=float)
        assert a.shape==b.shape and np.isfinite(a).all() and np.isfinite(b).all(),name
        if col is None:
            na,nb=a*np.asarray(row)/divisor,b*np.asarray(row)/divisor
        else:
            na=np.asarray(row)[:,None]*a*np.asarray(col)[None,:]/divisor
            nb=np.asarray(row)[:,None]*b*np.asarray(col)[None,:]/divisor
        ledger[name]=float(np.linalg.norm(na-nb)/max(1.,np.linalg.norm(nb)))
    def exact(name,a,b):
        assert canonical(a)==canonical(b),name
    def pair_difference(ah,al,bh,bl):
        aa,bb,cc,dd=(np.asarray(x) for x in (ah,al,bh,bl))
        return np.array([float(Fraction(float(a))+Fraction(float(b))-Fraction(float(c))-Fraction(float(d)))
            for a,b,c,d in zip(aa.flat,bb.flat,cc.flat,dd.flat)]).reshape(aa.shape)
    def mechanical(name,a,b):
        delta=pair_difference(a['positions'],a['position_low'],b['positions'],b['position_low'])
        check(name+'.physical_position',delta,np.zeros_like(delta),divisor=L)
        check(name+'.nodal_frames',a['nodal_frames'],b['nodal_frames'])
        check(name+'.cell_rotations',a['cell_rotations'],b['cell_rotations'])
        check(name+'.resultants',a['resultants'],b['resultants'],row=1/q[24:])
    def state(name,a,b):
        exact(name+'.time_epoch',(a['time'],a['epoch']),(b['time'],b['epoch']))
        for key in ('histories','origins'): exact(name+'.'+key,a[key],b[key])
        mechanical(name+'.mechanical',a['mechanical'],b['mechanical'])
        check(name+'.velocity',a['physical_velocity24'],b['physical_velocity24'],row=1/vscale)
        check(name+'.acceleration',a['physical_acceleration24'],b['physical_acceleration24'],row=1/ascale)
    def rank_checks(name,a,b):
        exact(name+'.rank',a['algebraic_rank'],b['algebraic_rank'])
        for key in a:
            if key!='algebraic_rank':
                assert a[key]>0. and b[key]>0.
                check(name+'.'+key,a[key],b[key],divisor=b[key])
    def account(name,a,b):
        exact(name+'.time_epoch',(a['time'],a['epoch']),(b['time'],b['epoch']))
        for key,scale in (('linear',m*V),('angular',m*L*V)):
            delta=pair_difference(a[key+'_momentum'],a[key+'_momentum_low'],b[key+'_momentum'],b[key+'_momentum_low'])
            check(name+'.'+key+'_momentum',delta,np.zeros(3),divisor=scale)
        for key in ('kinetic_energy','elastic_energy','total_energy','elastic_consistency_witness'):
            check(name+'.'+key,a[key],b[key],divisor=E)
        check(name+'.compatibility18',a['resultant_compatibility18'],b['resultant_compatibility18'],row=q[24:]/W)
        rank_checks(name+'.rank_mass',a['rank_mass_checks'],b['rank_mass_checks'])
    def inertia(name,a,b):
        ap,bp=a['physical'],b['physical']
        check(name+'.energy',ap['kinetic_energy'],bp['kinetic_energy'],divisor=E)
        for prefix,aa,bb,d in (('physical',ap,bp,q[:24]),('mixed',a,b,q)):
            fields=(('mass','mass',d,m*L*L),('generalized_momentum','generalized_momentum',None,m*L*V),
                ('inertia','inertia',None,W),('velocity_derivative','velocity_derivative',d,m*L*L*omega),
                ('configuration_derivative','configuration_derivative',d,W))
            for label,key,col,denominator in fields:
                if prefix=='mixed':key='mixed_'+key
                check(name+'.'+prefix+'.'+label,aa[key],bb[key],row=d,col=col,divisor=denominator)
        for key,scale in (('linear',m*V),('angular',m*L*V)):
            delta=pair_difference(ap[key+'_momentum'],a[key+'_momentum_low'],bp[key+'_momentum'],b[key+'_momentum_low'])
            check(name+'.'+key+'_momentum',delta,np.zeros(3),divisor=scale)
        for key in ('algebraic_dofs','physical_dofs','kinetic_station_count','implementation_id','production_qualified',
                'momentum_origin_high','momentum_origin_low'):
            exact(name+'.'+key,a[key],b[key])
    def stage(name,a,b):
        mechanical(name+'.mechanical',a['mechanical'],b['mechanical'])
        check(name+'.velocity',a['physical_velocity24'],b['physical_velocity24'],row=1/vscale)
        check(name+'.acceleration',a['physical_acceleration24'],b['physical_acceleration24'],row=1/ascale)
        for key in ('residual','structural_residual'):check(name+'.'+key,a[key],b[key],row=q,divisor=W)
        check(name+'.J_stage',a['jacobian'],b['jacobian'],row=q,col=u,divisor=W)
        check(name+'.J_structural',a['structural_jacobian'],b['structural_jacobian'],row=q,col=q,divisor=W)
        check(name+'.configuration_map',a['configuration_map'],b['configuration_map'],row=1/q,col=u)
        inertia(name+'.inertia',a['inertia'],b['inertia'])
    def endpoint(name,a,b):
        state(name+'.state',a['state'],b['state'])
        account(name+'.accounting',a['accounting'],b['accounting'])
        for key in ('R42','I42','balance42'):check(name+'.'+key,a[key],b[key],row=q,divisor=W)
        check(name+'.J42',a['J42'],b['J42'],row=q,col=q,divisor=W)
        check(name+'.M42',a['M42'],b['M42'],row=q,col=q,divisor=m*L*L)
        check(name+'.scaled_balance',a['scaled_free_balance'],b['scaled_free_balance'])
    endpoint('initial',actual['initial'],reference['initial'])
    rank_checks('initial_checks',actual['initial_checks'],reference['initial_checks'])
    assert len(actual['endpoints'])==len(reference['endpoints'])==4
    for index,(a,b) in enumerate(zip(actual['endpoints'],reference['endpoints'])):
        name='step'+str(index+1)
        endpoint(name,a,b)
        check(name+'.elastic_witness',a['elastic_witness_normalized'],b['elastic_witness_normalized'])
        for key in ('normalized_step_defects','normalized_cumulative_defects'):
            for component in ('E','P','H'):check(name+'.'+key+'.'+component,a[key][component],b[key][component])
        exact(name+'.gate_status',a['gate_status'],b['gate_status'])
        ca,cb=a['candidate'],b['candidate']
        state(name+'.candidate_endpoint',ca['endpoint'],cb['endpoint'])
        stage(name+'.candidate_stage',ca['stage'],cb['stage'])
        check(name+'.candidate_unknown',ca['unknown42'],cb['unknown42'],row=1/u)
        check(name+'.endpoint_reaction',ca['endpoint_reaction42'],cb['endpoint_reaction42'],row=q,divisor=W)
        for key in ('dt','iterations','backtracks'):exact(name+'.'+key,ca[key],cb[key])
        for key in ('stage_residual_norm','endpoint_algebraic_norm'):check(name+'.'+key,ca[key],cb[key])
        aa,bb=a['audit'],b['audit']
        for key in ('stage_coordinates','predecessor_epoch','endpoint_epoch','dt','stage_residual_tolerance'):
            exact(name+'.audit.'+key,aa[key],bb[key])
        stage(name+'.audit.stage',aa['stage'],bb['stage'])
        check(name+'.audit.unknown',aa['unknown42'],bb['unknown42'],row=1/u)
        check(name+'.audit.increment',aa['increment42'],bb['increment42'],row=1/q)
        exact(name+'.audit.residual_scales',aa['residual_scales42'],bb['residual_scales42'])
        for key in ('stage_residual_norm',):check(name+'.audit.'+key,aa[key],bb[key])
    assert len(actual['original_stages'])==len(reference['original_stages'])==12
    with journal_path.open('rb') as stream:
        def read(row):
            stream.seek(row['offset_bytes']);record=stream.read(row['length_bytes'])
            assert sha256(record).hexdigest()==row['sha256']
            return json.loads(record)
        for index,(a,b) in enumerate(zip(actual['original_stages'],reference['original_stages'])):
            a,b=read(a),read(b)
            exact('observation.step',a['step'],b['step'])
            stage('observation'+str(index),a['stage'],b['stage'])
            check('observation'+str(index)+'.unknown',a['unknown42'],b['unknown42'],row=1/u)
    return dict(status='PASS' if max(ledger.values())<=1e-13 else 'NONPASS',
        maximum_error=max(ledger.values()),worst_field=max(ledger,key=ledger.get),metrics=ledger)

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
    baseline = None
    for phase_index, mode in enumerate(('scalar','batch','batch','scalar')):
        phase_started = perf_counter()
        phase = dict(index=phase_index, mode=mode, status='RUNNING', endpoints=[], original_stages=[],
            stage_counts=[], solver_committed_steps=0, gate_passing_steps=0)
        result['phases'].append(phase)
        print(json.dumps(dict(stage='phase_start', index=phase_index, mode=mode, elapsed=perf_counter()-started)), flush=True)
        active_kernel_calls = 0
        selected_function = scalar_function if mode=='scalar' else wired_function
        phase['active_callable'] = dict(module=selected_function.__module__,qualname=selected_function.__qualname__,
            file=inspect.getsourcefile(selected_function),function_source_sha256=sha256(inspect.getsource(selected_function).encode('utf-8')).hexdigest())
        def observed_evaluate(kernel,*args,**kwargs):
            global active_kernel_calls
            assert _CenteredFiniteKernel.evaluate is observed_evaluate
            assert type(kernel) is _CenteredFiniteKernel
            assert selected_function is (scalar_function if mode=='scalar' else wired_function)
            active_kernel_calls += 1
            return selected_function(kernel,*args,**kwargs)
        _CenteredFiniteKernel.evaluate = observed_evaluate
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
        phase['scales'] = scales
        characteristics = make_characteristics(reference,mass,energy,speed)
        assert characteristics == spec['parity_characteristics']
        phase['parity_characteristics_before_initialization'] = characteristics
        state = owner.initialize(physical_velocity15=velocity[list(P)])
        initial = previous = owner.endpoint_accounting(state)
        phase['initial'] = signed_endpoint(owner,state,initial)
        phase['initial_checks'] = owner.initial_checks
        persist_state(phase,'initial_before_gates',phase['initial'])
        assert phase['initial']['scaled_free_balance'] <= 1e-11
        assert abs(initial.kinetic_energy-energy)/energy <= 1e-12
        assert np.linalg.norm(np.asarray(phase['initial']['M42'])-m0)/np.linalg.norm(m0) <= 1e-12
        assert canonical(state.mechanical) == canonical(reference)
        phase['initialization_seconds'] = perf_counter()-phase_started
        phase['initialization_kernel_calls'] = active_kernel_calls
        active_kernel_calls = 0
        operations_started = perf_counter()
        scope = nullcontext()  # Explicit default120/fullcallback path in all4phases.
        with scope:
            for step in range(4):
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
                try:
                    candidate = owner.trial(prior,dt=.00025)
                finally:
                    c._stage = original_stage
                audit = owner.candidate_stage_audit(candidate)
                phase['pending_candidate'] = json.loads(canonical(candidate))
                audit_row = asdict(audit)
                audit_row['session_provenance'] = json.loads(audit_row['session_provenance'])
                phase['pending_audit'] = json.loads(canonical(audit_row))
                assert candidate.stage_residual_norm <= 1e-12
                assert candidate.endpoint_algebraic_norm <= 1e-11
                assert audit.stage_coordinates == 'acceleration'
                state = owner.commit(candidate)
                phase['solver_committed_steps'] += 1
                phase['committed_state_before_accounting'] = json.loads(canonical(state))
                now = owner.endpoint_accounting(state)
                row = signed_endpoint(owner,state,now)
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
        phase['operation_kernel_calls'] = active_kernel_calls
        _CenteredFiniteKernel.evaluate = wired_function
        assert scheduling._ACTIVE.get() is None
        phase['status'] = 'PHYSICAL_GATES_PASS'
        phase['elapsed_seconds'] = perf_counter()-phase_started
        assert phase['stage_counts'] == [3]*4
        parity_started = perf_counter()
        if baseline is None:
            baseline = phase
            phase['parity'] = dict(status='REFERENCE',maximum_error=0.)
        else:
            phase['parity'] = compare_phase(phase,baseline,characteristics)
            assert phase['parity']['maximum_error'] <= 1e-13
        phase['parity_check_seconds'] = perf_counter()-parity_started
        phase['total_including_parity_seconds'] = perf_counter()-phase_started
        phase['status'] = 'PASS'
        assert _CenteredFiniteKernel.evaluate is wired_function
    assert len({p['operation_kernel_calls'] for p in result['phases']})==1
    result['timing_summary'] = {}
    for mode in ('scalar','batch'):
        selected=[p for p in result['phases'] if p['mode']==mode]
        result['timing_summary'][mode]={}
        for field in ('operations_seconds','elapsed_seconds','total_including_parity_seconds'):
            values=[p[field] for p in selected]
            result['timing_summary'][mode][field]=dict(values=values,median=statistics.median(values),spread=max(values)-min(values))
    result['status'] = 'PASS'
except BaseException as exc:
    result['status'] = 'NONPASS'
    result['failure'] = dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc())
    raise
finally:
    _CenteredFiniteKernel.evaluate = wired_function
    journal.flush(); journal.close()
    states.flush(); states.close()
    result['journal'] = dict(path=str(journal_path),bytes=journal_path.stat().st_size,sha256=journal_hash.hexdigest())
    result['state_journal'] = dict(path=str(state_path),bytes=state_path.stat().st_size,sha256=states_hash.hexdigest())
    result['elapsed_seconds'] = perf_counter()-started
    result['source_postverify'] = {path:sha256(Path(path).read_bytes()).hexdigest()==expected for path,expected in spec['source_sha256'].items()}
    with raw_path.open('xb') as stream: stream.write(canonical(result)+b'\n')
    print(json.dumps(dict(stage='complete',status=result['status'],elapsed=result['elapsed_seconds'])),flush=True)
