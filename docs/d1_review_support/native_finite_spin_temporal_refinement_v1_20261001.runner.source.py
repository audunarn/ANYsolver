"""Two parameterized virgin finite-spin trajectories; source-only prepared."""
from dataclasses import asdict
from fractions import Fraction
from hashlib import sha256
import inspect,json,os,sys,traceback
from pathlib import Path
from time import perf_counter

def compare_saved(coarse_path,coarse_sha,middle_path,middle_sha,fine_path,fine_sha):
    """Pure saved-field arithmetic; no production imports, issuance or evaluation."""
    import numpy as np
    def read(path,want):
        b=Path(path).read_bytes();assert sha256(b).hexdigest()==want
        return b
    coarse_initial=None;coarse={}
    for line in read(coarse_path,coarse_sha).splitlines():
        if not line.strip():continue
        row=json.loads(line)
        if row['step']==0:coarse_initial=row
        elif row['event']=='step_development_gates_pass' and row['step']<=108 and row['step']%2==0:
            assert row['row']['gate_status']=='DEVELOPMENT_GATES_PASS'
            coarse[row['step']//2]=row['row']
    middle=json.loads(read(middle_path,middle_sha));fine=json.loads(read(fine_path,fine_sha))
    for raw,N in ((middle,162),(fine,216)):
        assert raw['status']=='PASS' and all(raw['source_postverify'].values())
        assert raw['N']==N and raw['T_seconds']==.0045
        assert raw['trajectory']['gate_passing_steps']==raw['trajectory']['solver_committed_steps']==N
    scales=coarse_initial['scales'];E0=scales['energy'];L=2.;angle=np.sqrt(2250)*.0045
    P=(0,1,2,6,7,8,12,13,14,18,19,20,21,22,23)
    M=np.asarray(coarse_initial['independent_mass_input_M42'])[np.ix_(P,P)]
    assert E0>0 and angle>0 and np.isfinite(M).all()
    def stable_json(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
    for raw in (middle,fine):
        a,b=raw['trajectory']['initial'],coarse_initial['row']
        for key in ('mechanical','physical_velocity24','physical_acceleration24','histories','origins','time','epoch'):
            assert stable_json(a['state'][key])==stable_json(b['state'][key]),key
        for key in ('R42','I42','M42','J42','balance42','scaled_free_balance'):
            assert stable_json(a[key])==stable_json(b[key]),key
        assert raw['trajectory']['scales']['energy']==E0
    views=[coarse]
    for raw,factor in ((middle,3),(fine,4)):
        rows={row['step']//factor:row for row in raw['trajectory']['endpoints'] if row['step']%factor==0}
        assert len(rows)==54
        for j,row in rows.items():assert row['gate_status']=='PASS' and row['state']['epoch']==j*factor
        views.append(rows)
    def compensated(a,b):
        out=[]
        for ah,al,bh,bl in zip(np.asarray(a['positions']).flat,np.asarray(a['position_low']).flat,np.asarray(b['positions']).flat,np.asarray(b['position_low']).flat):
            out.append(float(Fraction(float(ah))+Fraction(float(al))-Fraction(float(bh))-Fraction(float(bl))))
        return np.asarray(out).reshape(3,3)
    def difference(a,b):
        ma,mb=a['state']['mechanical'],b['state']['mechanical']
        dv=(np.asarray(a['state']['physical_velocity24'])-np.asarray(b['state']['physical_velocity24']))[list(P)]
        square=float(dv@M@dv);assert square>=0
        position=float(np.linalg.norm(compensated(ma,mb))/(np.sqrt(3)*L))
        angles=[]
        for ra,rb in zip(ma['cell_rotations'][0],mb['cell_rotations'][0]):
            R=np.asarray(ra)@np.asarray(rb).T
            theta=float(np.arctan2(np.linalg.norm(R-R.T)/(2*np.sqrt(2)),(np.trace(R)-1)/2))
            assert 0<=theta<np.pi/2
            angles.append(theta)
        result=dict(velocity=float(np.sqrt(square/(2*E0))),position=position,cell_rotation=float(np.linalg.norm(angles)/(np.sqrt(2)*angle)))
        assert all(np.isfinite(x) for x in result.values());return result
    pairs={}
    for name,a,b in (('coarse_middle',views[0],views[1]),('middle_fine',views[1],views[2])):
        curve=[]
        for j in range(1,55):
            for row in (a[j],b[j]):assert abs(row['state']['time']-j*.0045/54)<= (4*216+4)*np.finfo(float).eps*.0045
            curve.append(dict(j=j,time_seconds=j*.0045/54,**difference(a[j],b[j])))
        pairs[name]=dict(curve=curve,observables={key:dict(rms=float(np.sqrt(sum(row[key]**2 for row in curve)/54)),maximum=max(row[key] for row in curve),final=curve[-1][key]) for key in ('velocity','position','cell_rotation')})
    disposition={};passed=True
    for key in ('velocity','position','cell_rotation'):
        cm=pairs['coarse_middle']['observables'][key];mf=pairs['middle_fine']['observables'][key]
        resolved=cm['rms']>1e-9 and mf['rms']>1e-9
        ratio=cm['rms']/mf['rms'] if resolved else None
        in_band=resolved and 16/7<=ratio<=24/7
        disposition[key]=dict(resolved=resolved,ratio=ratio,status='PASS' if in_band else ('UNRESOLVED' if not resolved else 'NONPASS'),conditional_fine_error_estimate={field:9/7*value for field,value in mf.items()},estimate_condition='Common leading h^2 expansion; not a certified bound')
        if key in ('velocity','cell_rotation') and not in_band:passed=False
        if key=='position' and resolved and not in_band:passed=False
    return dict(status='PASS' if passed else 'NONPASS',claim='Empirical second-order-compatible temporal self-convergence only; no rigorous bound/2percent/independent-code/spatial/C7 claim',source_inputs=dict(coarse_sha256=coarse_sha,middle_sha256=middle_sha,fine_sha256=fine_sha),scales=scales,length_m=L,attitude_scale_rad=float(angle),diagnostic_floor=1e-10,resolved_minimum=1e-9,expected_ratio=20/7,ratio_band=[16/7,24/7],pairs=pairs,disposition=disposition)

if len(sys.argv)>1 and sys.argv[1]=='--compare':
    assert len(sys.argv)==9
    output=Path(sys.argv[8]);assert not output.exists()
    answer=compare_saved(*sys.argv[2:8])
    with output.open('x',encoding='utf-8',newline='\n') as stream:json.dump(answer,stream,indent=2);stream.write('\n')
    raise SystemExit(0 if answer['status']=='PASS' else 1)

INPUT=Path(os.environ['NATIVE_FINITE_SPIN_TEMPORAL_INPUTS'])
spec=json.loads(INPUT.read_text())
for p,want in spec['source_sha256'].items():assert sha256(Path(p).read_bytes()).hexdigest()==want,p
for key,want in spec['environment'].items():assert os.environ.get(key)==want,key
print(json.dumps(dict(stage='authenticated_before_import',input_sha256=sha256(INPUT.read_bytes()).hexdigest())),flush=True)
import numpy as np
from threadpoolctl import threadpool_info
import anysolver
from anysolver.ge_beam3_native_dynamics import create_analysis,SELECTOR
from anysolver._ge_beam3_p5_seeded.core import canonical,sha
from anysolver._ge_beam3_centered_finite_inertia import _CenteredFiniteKernel
from anysolver import _ge_beam3_operator_validation_scope as scheduling
from test_ge_beam3_native_midpoint import make_analysis
from test_ge_beam3_native_finite_spin_acceleration_chart import P,Z,accounting,momentum_delta
from native_forced_response_reference import positions
assert Path(anysolver.__file__).resolve()==Path(spec['actual_anysolver_module']).resolve()
N,T=spec['N'],spec['T_seconds']
assert N in (162,216) and T==.0045
h=T/N
assert spec['runtime_seconds']==840 and spec['criteria']==spec['approved_criteria']
assert scheduling._ACTIVE.get() is None
actual_threadpools=threadpool_info()
assert actual_threadpools and all(x['num_threads']==1 for x in actual_threadpools)
assert sha256(inspect.getsource(_CenteredFiniteKernel.evaluate).encode()).hexdigest()==spec['wired_callable_sha256']
raw_path,journal_path,state_path,progress_path=(Path(spec[k]) for k in ('raw_output','stage_journal','state_journal','progress_output'))
for p in (raw_path,journal_path,state_path,progress_path):assert not p.exists(),p
started=perf_counter();phase_index=0
phase=dict(index=0,mode='batch',status='RUNNING',endpoints=[],original_stages=[],stage_counts=[],solver_committed_steps=0,gate_passing_steps=0)
result=dict(status='RUNNING',trajectory=phase,criteria=spec['criteria'],N=N,T_seconds=T,input_sha256=sha256(INPUT.read_bytes()).hexdigest(),effective_environment={k:os.environ[k] for k in spec['environment']},module_file=str(Path(anysolver.__file__).resolve()),scope='Finite-angle temporal self-convergence preparation/control; no independent spatial/continuum/C7 acceptance',actual_threadpools=actual_threadpools,temporal_comparison='Pending both terminal outputs and trusted raw hashes; physical PASS alone does not close comparison')
journal=journal_path.open('xb');journal_hash=sha256();states=state_path.open('xb');states_hash=sha256()
state_references=[]
def progress(label):
    progress_path.write_bytes(canonical(dict(stage=label,committed=phase['solver_committed_steps'],gate_passing=phase['gate_passing_steps'],elapsed=perf_counter()-started))+b'\n')
    print(json.dumps(dict(stage=label,committed=phase['solver_committed_steps'],gate_passing=phase['gate_passing_steps'],elapsed=perf_counter()-started)),flush=True)
def persist_state(phase,kind,row):
    payload=dict(event=kind,step=row.get('step',0),row=row,criteria=spec['criteria'],scales=phase['scales'],solver_committed_steps=phase['solver_committed_steps'],gate_passing_steps=phase['gate_passing_steps'])
    if kind=='initial_before_gates':payload.update(definition=phase['definition'],initial_checks=phase['initial_checks'],context_identity=phase['context_identity'],captured_runtime=phase['captured_runtime'])
    b=canonical(payload)+b'\n';offset=states.tell();assert states.write(b)==len(b);states.flush();states_hash.update(b)
    state_references.append(dict(event=kind,step=payload['step'],offset_bytes=offset,length_bytes=len(b),sha256=sha256(b).hexdigest()))
    assert len(state_references)<=1+2*N
    progress(kind)
def assert_initial_matches(actual,reference,scales):
    for k in ('mechanical','histories','origins','physical_velocity24','physical_acceleration24','time','epoch'):
        assert canonical(actual['state'][k])==canonical(reference['state'][k]),k
    for k in ('R42','I42','J42','M42','balance42','scaled_free_balance'):
        assert canonical(actual[k])==canonical(reference[k]),k
    for k in actual['accounting']:
        if k!='state_sha256':assert canonical(actual['accounting'][k])==canonical(reference['accounting'][k]),k
    assert scales['energy']==coarse_scales['energy'] and scales['mass']==coarse_scales['mass']
    assert scales['momentum']==coarse_scales['momentum'] and scales['angular_momentum']==coarse_scales['angular_momentum']
def read_coarse():
    rows={};initial=None;scales=None
    for p,want in spec['coarse_asset_sha256'].items():assert sha256(Path(p).read_bytes()).hexdigest()==want,p
    with Path(spec['coarse_endpoints']).open('rb') as stream:
        for line in stream:
            if not line.strip():continue
            event=json.loads(line)
            if event['step']==0:initial,scales=event['row'],event['scales']
            elif event['event']=='step_development_gates_pass' and event['step']<=108 and event['step']%2==0:
                assert event['row']['gate_status']=='DEVELOPMENT_GATES_PASS'
                rows[event['step']//2]=event['row']
    assert initial is not None and len(rows)==54
    return initial,scales,rows
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

try:
    coarse_initial,coarse_scales,coarse_rows=read_coarse()
    saved_bytes=Path(spec["mass_reference"]).read_bytes()
    assert sha256(saved_bytes).hexdigest()==spec["mass_reference_sha256"]
    saved=json.loads(saved_bytes)["reference"]
    m0=np.asarray(saved["M42"])
    phase_started=perf_counter()
    _, definition = make_analysis()
    owner = create_analysis(SELECTOR,(definition,),(),inertia_order=24,
        stage_coordinates='acceleration',stage_residual_tolerance=1e-12,runtime_limit_seconds=840)
    c = owner._context
    assert c.runtime_limit_seconds == c._dynamic.runtime_limit_seconds == 840.
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
    state = owner.initialize(physical_velocity15=velocity[list(P)])
    initial = previous = owner.endpoint_accounting(state)
    phase['initial'] = signed_endpoint(owner,state,initial)
    phase['initial_checks'] = owner.initial_checks
    phase['definition'] = json.loads(definition.raw)
    phase['context_identity'] = c._identity
    phase['captured_runtime'] = dict(started=c._dynamic.started,seconds=c._dynamic.runtime_limit_seconds)
    persist_state(phase,'initial_before_gates',phase['initial'])
    assert_initial_matches(phase['initial'],coarse_initial,scales)
    assert phase['initial']['scaled_free_balance'] <= 1e-11
    assert abs(initial.kinetic_energy-energy)/energy <= 1e-12
    assert np.linalg.norm(np.asarray(phase['initial']['M42'])-m0)/np.linalg.norm(m0) <= 1e-12
    assert canonical(state.mechanical) == canonical(reference)
    phase['initialization_seconds'] = perf_counter()-phase_started
    operations_started = perf_counter()
    for step in range(N):
        prior = state
        phase['pending_attempt']=dict(step=step+1,predecessor_sha256=sha(prior),predecessor_epoch=prior.epoch,context_sha256=c._identity,dt=h)
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
            candidate = owner.trial(prior,dt=h)
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
        row['step']=step+1
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
        assert state.epoch == step+1 and state.time == prior.time+h
        row['gate_status'] = 'PASS'
        phase['gate_passing_steps'] += 1
        phase['stage_counts'].append(len(phase['original_stages'])-before)
        persist_state(phase,'committed_endpoint_after_gates',row)
        previous = now
        print(json.dumps(dict(stage='step_pass',phase=phase_index,step=step+1,elapsed=perf_counter()-started)),flush=True)

    phase['operations_seconds']=perf_counter()-operations_started
    assert phase['gate_passing_steps']==phase['solver_committed_steps']==N
    assert scheduling._ACTIVE.get() is None
    for row in phase['endpoints']:
        assert abs(row['state']['time']-row['step']*h)<=(4*N+4)*np.finfo(float).eps*T
    angles=[]
    for a,b in zip(state.mechanical.cell_rotations[0],reference.cell_rotations[0]):
        r=a@b.T;sine=np.linalg.norm(r-r.T)/(2*np.sqrt(2));cosine=(np.trace(r)-1)/2
        angles.append(float(np.arctan2(sine,cosine)))
    phase['final_cell_attitude_rad']=angles
    assert min(angles)>=.2
    phase['common_time_rows']=[dict(j=j,coarse_step=2*j,new_step=(3 if N==162 else 4)*j) for j in range(1,55)]
    phase['status']='PASS';result['status']='PASS'
except BaseException as exc:
    result['status']='NONPASS';result['failure']=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc())
    raise
finally:
    journal.flush();journal.close();states.flush();states.close()
    result['journal']=dict(path=str(journal_path),bytes=journal_path.stat().st_size,sha256=journal_hash.hexdigest())
    result['state_journal']=dict(path=str(state_path),bytes=state_path.stat().st_size,sha256=states_hash.hexdigest(),records=state_references)
    result['elapsed_seconds']=perf_counter()-started
    result['source_postverify']={p:sha256(Path(p).read_bytes()).hexdigest()==want for p,want in spec['source_sha256'].items()}
    if not all(result['source_postverify'].values()):result['status']='NONPASS'
    with raw_path.open('xb') as stream:stream.write(canonical(result)+b'\n')
    progress('terminal_'+result['status'])
    if not all(result['source_postverify'].values()):raise AssertionError('source postmatch failed')
