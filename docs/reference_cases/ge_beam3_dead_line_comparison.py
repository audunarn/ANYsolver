"""Native dead-line recovery compared with a separately solved continuum BVP."""
from dataclasses import asdict
from hashlib import sha256
from math import fsum
import json
import numpy as np

from docs.reference_cases import ge_beam3_curved_moment_fixture as fixture
from docs.reference_cases import ge_beam3_dead_line_reference as reference
from docs.reference_cases import ge_beam3_centered_line_load_oracle as work_oracle
from docs.reference_cases.ge_beam3_arch_field_comparison import native_recovery, paired
from docs.reference_cases.ge_beam3_curved_moment_comparison import sample_indices
from docs.reference_cases.ge_beam3_preserved_arch_load_comparison import canonical, _seal


FORCE=(.3,-.2,.1)
MACROS=(1,2,4)
TARGETS=(.25,.5,1.)


def metrics(record,recovery,locations,macros,fine,coarse):
    stations=[s for e in recovery for s in e['stations']]
    nodes=np.linspace(-1.,1.,2*macros+1)
    if len(stations)!=8*macros or len(locations)!=len(stations): raise ValueError('complete line station coverage')
    if (fine['parameter']!=coarse['parameter'] or fine['profile']!='BVP9' or coarse['profile']!='BVP7'
            or fine['production_qualified'] is not False or coarse['production_qualified'] is not False):
        raise ValueError('exact reference profiles required')
    si=sample_indices(fine['parameter'],locations); ni=sample_indices(fine['parameter'],nodes)
    c=np.asarray(fine['section']); strains=np.asarray(fine['strains']); frames=np.asarray(fine['frames'])
    expected_force=np.asarray(fine['spatial_forces']); expected_moment=np.asarray(fine['spatial_moments'])
    force_scale=float(np.max(np.linalg.norm(expected_force,axis=1)))
    moment_scale=float(np.max(np.linalg.norm(expected_moment,axis=1)))
    if min(force_scale,moment_scale,fine['strain_energy'])<=0: raise ValueError('nonzero continuum scales')
    numerator=denominator=energy=0.; force_errors=[]; moment_errors=[]; frame_errors=[]
    for row,i in zip(stations,si):
        e=paired(row['strain'],row['strain_low']); s=paired(row['resultants'],row['resultants_low'])
        q=np.asarray(row['current_frame']); w=row['measure']
        if type(w) is not float or not np.isfinite(w) or w<=0 or np.max(abs(q.T@q-np.eye(3)))>1e-11:
            raise ValueError('proper native station frame and positive measure')
        d=e-strains[i]; numerator+=w*float(d@c@d); denominator+=w*float(strains[i]@c@strains[i])
        energy+=.5*w*float(e@s)
        force_errors.append(float(np.linalg.norm(q@s[:3]-expected_force[i])/force_scale))
        moment_errors.append(float(np.linalg.norm(q@s[3:]-expected_moment[i])/moment_scale))
        frame_errors.append(float(np.max(abs(q-frames[i]))))
    if denominator<=0: raise ValueError('positive reference strain energy norm')
    mechanical=record['mechanical']; x=np.asarray(mechanical['positions']); low=np.asarray(mechanical['position_low'])
    qnodes=np.asarray(mechanical['nodal_frames']); cells=np.asarray(mechanical['cell_rotations'])
    coordinates=np.column_stack((nodes,fixture.HEIGHT*(1-nodes**2),np.zeros(len(nodes))))
    displacement=np.array([[fsum((a,b,-r)) for a,b,r in zip(hi,lo,ref)] for hi,lo,ref in zip(x,low,coordinates)])
    external_force=np.zeros((len(nodes),3)); external_moment=np.zeros(3); work=0.
    # Independently rebuild distributed-load rigid work from rational Q2
    # geometry and closed rotation derivatives, not the native load module.
    for cell in range(macros):
        indices=list(range(2*cell,2*cell+3))
        made=work_oracle.evaluate(coordinates[indices],displacement[indices],cells[cell],fine['force'],order=4)
        external_force[indices]+=made.force[:18].reshape(3,6)[:,:3]
        external_moment+=made.force[18:24].reshape(2,3).sum(axis=0)
        work+=made.work
    external_moment+=np.cross(x+low,external_force).sum(axis=0)
    residual=np.asarray(record['residual'][:6*len(nodes)]).reshape(-1,6)
    force_balance=residual[:,:3].sum(axis=0)+external_force.sum(axis=0)
    moment_balance=(residual[:,3:]+np.cross(x+low,residual[:,:3])).sum(axis=0)+external_moment
    reference_displacement=np.asarray(fine['positions'])[ni]-coordinates
    values=dict(stations=len(stations),native_equilibrium_metric=max(record['metrics']),
        nodal_position_max_absolute_error=float(np.max(abs(x+low-np.asarray(fine['positions'])[ni]))),
        nodal_frame_max_absolute_error=float(np.max(abs(qnodes-frames[ni]))),
        tip_displacement_relative_error=float(np.linalg.norm(displacement[-1]-reference_displacement[-1])/np.linalg.norm(reference_displacement[-1])),
        recovered_frame_max_absolute_error=max(frame_errors),
        strain_energy_norm_relative_error=float(np.sqrt(numerator/denominator)),
        integrated_energy_relative_error=float(abs(energy/fine['strain_energy']-1)),
        native_integrated_energy=float(energy),reference_energy=float(fine['strain_energy']),
        station_rule_reference_energy_relative_error=float(abs(.5*denominator/fine['strain_energy']-1)),
        spatial_force_max_relative_error=max(force_errors),spatial_moment_max_relative_error=max(moment_errors),
        reaction_force_absolute_error=float(np.linalg.norm(force_balance)),
        reaction_moment_absolute_error=float(np.linalg.norm(moment_balance)),
        native_external_work=float(work),
        reference_profile_field_max_difference=float(max(np.max(abs(np.asarray(fine[k])-np.asarray(coarse[k]))) for k in ('positions','frames','strains','resultants'))),
        reference_profile_energy_relative_difference=float(abs(coarse['strain_energy']/fine['strain_energy']-1)))
    if any(not np.isfinite(v) or v<0 for v in values.values()): raise ValueError('finite nonnegative comparison metrics')
    return values


def recompute(detail,checkpoints):
    if set(checkpoints)!=set(MACROS): raise ValueError('exact three macro refinements required')
    refs=detail['references']; recs=detail['recoveries']
    if [(r['target'],r['value']['profile']) for r in refs]!=[(t,p) for t in TARGETS for p in ('BVP7','BVP9')]:
        raise ValueError('complete ordered continuum profiles')
    if [(r['macros'],r['target']) for r in recs]!=[(m,t) for m in MACROS for t in TARGETS]:
        raise ValueError('complete ordered native recoveries')
    for r in refs:
        value=r['value']
        if (value['height']!=fixture.HEIGHT or canonical(value['section'])!=canonical(fixture.reference_section().tolist())
                or value['force']!=list(r['target']*np.asarray(FORCE))):
            raise ValueError('continuum fixture input mismatch')
        tolerance={'BVP7':1e-7,'BVP9':1e-9}[value['profile']]
        if any(type(value[k]) is not float or not 0<=value[k]<=20*tolerance for k in
               ('boundary_error','differential_error','orthogonality_error')):
            raise ValueError('reference residual/rotation validation failed')
    bykey={(r['target'],r['value']['profile']):r['value'] for r in refs}; rows=[]
    for rec in recs:
        m=rec['macros']; t=rec['target']; packet=checkpoints[m]; _seal(packet,'checkpoint_sha256')
        if packet['completed_targets']!=3 or len(packet['records'])!=3: raise ValueError('all native load targets required')
        expected_load=dict(policy='GE_BEAM3_RETAINED_FIBRE_SPATIAL_DEAD_REFERENCE_LINE_FORCE_V1',
            rows=[[eid,*FORCE] for eid in range(1,m+1)],axes='FIXED_SPATIAL',measure='REFERENCE_ARCLENGTH',
            quadrature='ELEMENT_STIFFNESS_RULE',field='CENTERED_TWO_CELL_OBJECTIVE_LIFT',
            conservative_potential=True,internal_load_work_retained=True,production_qualified=False)
        if (packet['program']['line_forces']!=expected_load or packet['program']['targets']!=list(TARGETS)
                or packet['program']['nodal_forces']!=[] or packet['program']['spectral_authority'] is not False
                or packet['program']['schema']!='GE_BEAM3_RETAINED_FIBRE_CONSERVATIVE_LINE_PROGRAM_DEVELOPMENT_V1'):
            raise ValueError('exact native distributed force pattern')
        row=packet['records'][TARGETS.index(t)]; _seal(row,'record_sha256')
        if (row['parameter']!=t or len(rec['fields'])!=m or len(rec['locations'])!=8*m
                or any(len(e['stations'])!=8 for e in rec['fields'])
                or sha256(canonical(rec['fields'])).hexdigest()!=row['recovery_sha256']):
            raise ValueError('complete hash-bound native station recovery')
        values=metrics(row,rec['fields'],rec['locations'],m,bykey[t,'BVP9'],bykey[t,'BVP7'])
        if max(values[k] for k in ('native_equilibrium_metric','reaction_force_absolute_error','reaction_moment_absolute_error'))>1e-11:
            raise ValueError('native action/reaction/equilibrium failure')
        if max(values[k] for k in ('reference_profile_field_max_difference','reference_profile_energy_relative_difference'))>1e-7:
            raise ValueError('continuum profile disagreement')
        rows.append(dict(macros=m,target=t,metrics=values))
    return rows


def build(save,progress):
    from anysolver._ge_beam3_seeded_load_program import ForceProgram
    from anysolver._ge_beam3_fibre_line_work import ReferenceLineForces
    from anysolver import _ge_beam3_fibre_line_program as native
    from anysolver._ge_beam3_p5_seeded.core import canonical as native_canonical
    models={m:fixture.model(m) for m in MACROS}; samples=set()
    for m,model in models.items():
        samples.update(map(float,np.linspace(-1.,1.,2*m+1)))
        for element in model.mesh.elements.values():
            samples.update(float(element.operator.reference.position(xi)[0]) for _,_,xi,_,_ in element.operator.stations)
    refs=[]; recs=[]; checkpoints={}
    for target in TARGETS:
        for profile in ('BVP7','BVP9'):
            progress(dict(stage='REFERENCE',target=target,profile=profile))
            result=reference.solve(fixture.reference_section().tolist(),(target*np.asarray(FORCE)).tolist(),sorted(samples),profile=profile)
            refs.append(dict(target=target,value=json.loads(native_canonical(asdict(result)))))
    save('reference-diagnostic.json',canonical(refs))
    for m,model in models.items():
        progress(dict(stage='NATIVE',macros=m))
        program=ForceProgram(TARGETS,(),max_iterations=24)
        line=ReferenceLineForces(tuple((eid,*FORCE) for eid in range(1,m+1)))
        result=native.solve_force_program(model,program,line_forces=line,progress=progress)
        save(f'checkpoint-{m}.json',result.checkpoint)
        save(f'native-status-{m}.json',canonical(dict(status=result.status,failure=result.failure)))
        if result.status!='completed': raise RuntimeError(f'native {m}-macro line failure: {result.failure}; no retry')
        context=native.Context(model,program,line_forces=line)
        _,records=context.restore(result.checkpoint)
        if context.checkpoint(records)!=result.checkpoint: raise ValueError('line checkpoint replay mismatch')
        packet=json.loads(result.checkpoint); checkpoints[m]=packet
        for row in packet['records']:
            progress(dict(stage='RECOVERY',macros=m,target=row['parameter']))
            fields,locations=native_recovery(model,row)
            recs.append(dict(macros=m,target=row['parameter'],fields=json.loads(native_canonical(fields)),locations=locations))
    detail=dict(references=refs,recoveries=recs)
    return recompute(detail,checkpoints),detail
