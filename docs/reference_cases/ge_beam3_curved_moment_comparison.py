"""Private curved end-couple development comparison; never qualification."""
from dataclasses import asdict
from hashlib import sha256
import json
import numpy as np

from docs.reference_cases import ge_beam3_curved_moment_fixture as fixture
from docs.reference_cases import ge_beam3_curved_moment_reference as reference
from docs.reference_cases.ge_beam3_arch_field_comparison import native_recovery, paired
from docs.reference_cases.ge_beam3_preserved_arch_load_comparison import canonical, _seal


def sample_indices(parameters, locations):
    p=np.asarray(parameters, dtype=float)
    if p.ndim!=1 or not np.isfinite(p).all() or np.any(np.diff(p)<=0):
        raise ValueError('unique finite ordered reference samples')
    indices=[]
    for x in locations:
        hits=np.flatnonzero(p==x)
        if len(hits)!=1: raise ValueError('exact explicit reference sample absent')
        indices.append(int(hits[0]))
    return indices


def metrics(record, recovery, locations, nodes, fine, coarse):
    """Recompute diagnostic norms directly from saved arrays, with no solve."""
    stations=[s for e in recovery for s in e['stations']]
    if len(stations)!=len(locations) or not stations: raise ValueError('complete station locations')
    if (fine['parameter']!=coarse['parameter'] or fine['profile']!='IVP13' or coarse['profile']!='IVP9'
            or fine['production_qualified'] is not False or coarse['production_qualified'] is not False):
        raise ValueError('paired development reference profiles')
    si=sample_indices(fine['parameter'],locations); ni=sample_indices(fine['parameter'],nodes)
    frames=np.asarray(fine['frames']); strains=np.asarray(fine['strains']); positions=np.asarray(fine['positions'])
    c=np.asarray(fine['section']); expected_m=np.asarray(fine['moment']); scale=np.linalg.norm(expected_m)
    if scale<=0 or fine['strain_energy']<=0: raise ValueError('nonzero end moment and positive reference energy')
    numerator=denominator=energy=0.; force_error=[]; moment_error=[]; frame_error=[]
    for row,i in zip(stations,si):
        strain=paired(row['strain'],row['strain_low']); resultants=paired(row['resultants'],row['resultants_low'])
        q=np.asarray(row['current_frame']); weight=row['measure']
        if (type(weight) is not float or not np.isfinite(weight) or weight<=0 or q.shape!=(3,3)
                or not np.isfinite(q).all() or np.max(abs(q.T@q-np.eye(3)))>1e-11
                or abs(np.linalg.det(q)-1)>1e-11): raise ValueError('proper station frame and positive measure')
        difference=strain-strains[i]
        numerator+=weight*float(difference@c@difference)
        denominator+=weight*float(strains[i]@c@strains[i])
        energy+=.5*weight*float(strain@resultants)
        force_error.append(float(np.linalg.norm(q@resultants[:3])))
        moment_error.append(float(np.linalg.norm(q@resultants[3:]-expected_m)/scale))
        frame_error.append(float(np.max(abs(q-frames[i]))))
    if denominator<=0: raise ValueError('positive reference energy norm')
    native_positions=np.asarray(record['mechanical']['positions'])+np.asarray(record['mechanical']['position_low'])
    native_frames=np.asarray(record['mechanical']['nodal_frames'])
    residual=np.asarray(record['residual'][:6*len(nodes)]).reshape(-1,6)
    applied=np.zeros_like(residual); applied[-1,3:]=expected_m
    total=residual+applied
    values=dict(stations=len(stations),
        nodal_position_max_absolute_error=float(np.max(abs(native_positions-positions[ni]))),
        nodal_frame_max_absolute_error=float(np.max(abs(native_frames-frames[ni]))),
        recovered_frame_max_absolute_error=max(frame_error),
        strain_energy_norm_relative_error=float(np.sqrt(numerator/denominator)),
        integrated_energy_relative_error=float(abs(energy/fine['strain_energy']-1)),
        native_integrated_energy=float(energy), reference_energy=float(fine['strain_energy']),
        station_rule_reference_energy_relative_error=float(abs(.5*denominator/fine['strain_energy']-1)),
        spatial_force_max_absolute_error=max(force_error), spatial_moment_max_relative_error=max(moment_error),
        reaction_force_absolute_error=float(np.linalg.norm(total[:,:3].sum(axis=0))),
        reaction_moment_absolute_error=float(np.linalg.norm((total[:,3:]+np.cross(native_positions,total[:,:3])).sum(axis=0))),
        native_equilibrium_metric=max(record['metrics']),
        reference_profile_field_max_difference=float(max(np.max(abs(frames-np.asarray(coarse['frames']))),
            np.max(abs(positions-np.asarray(coarse['positions']))),np.max(abs(strains-np.asarray(coarse['strains']))))),
        reference_profile_energy_relative_difference=float(abs(coarse['strain_energy']/fine['strain_energy']-1)))
    if any(not np.isfinite(v) or v<0 for v in values.values()): raise ValueError('finite nonnegative diagnostics')
    return values


def recompute(diagnostic, checkpoints):
    if set(checkpoints)!={1,2,4}: raise ValueError('exact three macro refinements')
    refs=diagnostic['references']; recs=diagnostic['recoveries']
    if [(r['target'],r['value']['profile']) for r in refs]!=[(t,p) for t in fixture.TARGETS for p in ('IVP9','IVP13')]:
        raise ValueError('complete ordered reference records')
    if [(r['macros'],r['target']) for r in recs]!=[(m,t) for m in (1,2,4) for t in fixture.TARGETS]:
        raise ValueError('complete ordered recovery records')
    bykey={(r['target'],r['value']['profile']):r['value'] for r in refs}
    for r in refs:
        value=r['value']
        if (value['height']!=fixture.HEIGHT or canonical(value['section'])!=canonical(fixture.reference_section().tolist())
                or value['moment']!=list(np.asarray(fixture.MOMENT)*r['target'])):
            raise ValueError('reference input fixture changed')
    rows=[]
    for rec in recs:
        m=rec['macros']; t=rec['target']; packet=checkpoints[m]
        _seal(packet,'checkpoint_sha256')
        if packet['completed_targets']!=3 or len(packet['records'])!=3: raise ValueError('incomplete native targets')
        row=packet['records'][fixture.TARGETS.index(t)]; _seal(row,'record_sha256')
        if (row['parameter']!=t or len(rec['fields'])!=m or len(rec['locations'])!=8*m
                or any(len(e['stations'])!=8 for e in rec['fields'])
                or sha256(canonical(rec['fields'])).hexdigest()!=row['recovery_sha256']):
            raise ValueError('native recovery coverage or hash changed')
        values=metrics(row,rec['fields'],rec['locations'],np.linspace(-1.,1.,2*m+1),bykey[t,'IVP13'],bykey[t,'IVP9'])
        if max(values[k] for k in ('native_equilibrium_metric','reaction_force_absolute_error','reaction_moment_absolute_error'))>1e-11:
            raise ValueError('native equilibrium or action/reaction check failed')
        rows.append(dict(macros=m,target=t,metrics=values))
    return rows


def build(save,progress):
    from anysolver._ge_beam3_seeded_load_program import ForceProgram
    from anysolver._ge_beam3_spatial_nodal_moments import SpatialNodalMoments
    from anysolver import _ge_beam3_spatial_fibre_program as native
    from anysolver._ge_beam3_p5_seeded.core import canonical as native_canonical
    models={m:fixture.model(m) for m in (1,2,4)}
    samples=set()
    for m,model in models.items():
        samples.update(map(float,np.linspace(-1.,1.,2*m+1)))
        for element in model.mesh.elements.values():
            samples.update(float(element.operator.reference.position(xi)[0]) for _,_,xi,_,_ in element.operator.stations)
    samples=sorted(samples); refs=[]; recoveries=[]; checkpoints={}
    for target in fixture.TARGETS:
        for profile in ('IVP9','IVP13'):
            progress(dict(stage='REFERENCE',target=target,profile=profile))
            result=reference.solve(fixture.reference_section(),(target*np.asarray(fixture.MOMENT)).tolist(),samples,profile=profile)
            refs.append(dict(target=target,value=json.loads(native_canonical(asdict(result)))))
    save('reference-diagnostic.json',canonical(refs))
    for m,model in models.items():
        progress(dict(stage='NATIVE',macros=m))
        program=ForceProgram(fixture.TARGETS,(),max_iterations=24)
        moments=SpatialNodalMoments(((2*m+1,*fixture.MOMENT),))
        result=native.solve_force_program(model,program,nodal_moments=moments,progress=progress)
        save(f'checkpoint-{m}.json',result.checkpoint)
        save(f'native-status-{m}.json',canonical(dict(status=result.status,failure=result.failure)))
        if result.status!='completed': raise RuntimeError(f'native {m}-macro failure: {result.failure}; no retry')
        context=native.Context(model,program,nodal_moments=moments)
        _,records=context.restore(result.checkpoint)
        if context.checkpoint(records)!=result.checkpoint: raise ValueError('native checkpoint replay differs')
        packet=json.loads(result.checkpoint); checkpoints[m]=packet
        for row in packet['records']:
            progress(dict(stage='RECOVERY',macros=m,target=row['parameter']))
            fields,locations=native_recovery(model,row)
            recoveries.append(dict(macros=m,target=row['parameter'],fields=json.loads(native_canonical(fields)),locations=locations))
    diagnostic=dict(references=refs,recoveries=recoveries)
    rows=recompute(diagnostic,checkpoints)
    return rows,diagnostic
