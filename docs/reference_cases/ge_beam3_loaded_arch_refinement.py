"""Bounded six-macro spectra, preserved histories and continuum references."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import time
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,_ProcessJob,THREAD_ENVIRONMENT
from docs.reference_cases import ge_beam3_loaded_arch_spectra_probe as baseline

ROOT=Path(__file__).resolve().parents[2]
EXTERNAL=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease')
OLD=EXTERNAL/'ge-beam3-loaded-spectra-20260907-v2'
INPUT=EXTERNAL/'ge-beam3-fibre-arch6-20260907-v1/checkpoint-diagnostic.json'
INPUT_SHA='20a1a48cf6e2dfdc669c4f2d823deb89a9da8c6560ab716eb32e95b1b917a940'
BASELINE_SHA='c0a4a321eeba0de537282b4f20c951bf4678c9c50143663562b223eb8e7eca54'
BASELINE_REVISION='1a3c4cc6cfb26ac3412b1f03a94bf657f4c27bf0'
ARTIFACTS=('input-six.json','baseline-comparison.json','equilibrium-1.json','equilibrium-4.json',
    'reference-1.json','reference-4.json','checkpoint-1.json','checkpoint-4.json','native-1.json','native-4.json')
canonical=baseline.canonical
read=baseline.read
parse=baseline.parse


def inputs():
    raw=read(INPUT); base=read(OLD/'comparison.json')
    if len(raw)!=141754 or sha256(raw).hexdigest()!=INPUT_SHA: raise ValueError('six-macro input changed')
    if len(base)!=3689 or sha256(base).hexdigest()!=BASELINE_SHA: raise ValueError('baseline comparison changed')
    baseline.validate(OLD,base,BASELINE_REVISION)
    value=parse(base); artifacts={a['path']:a for a in value['artifacts']}
    found={'input-six.json':raw,'baseline-comparison.json':base}
    for cursor in (1,4):
        for src,dst in ((f'equilibrium-{cursor}.json',f'equilibrium-{cursor}.json'),
                        (f'ritz-{cursor}-16.json',f'reference-{cursor}.json')):
            data=read(OLD/src)
            if len(data)!=artifacts[src]['bytes'] or sha256(data).hexdigest()!=artifacts[src]['sha256']:
                raise ValueError('saved continuum reference changed')
            found[dst]=data
    return found


def row(cursor,native,reference,equilibrium,coarse):
    import numpy as np
    a=np.asarray(native['eigenvalues']); b=np.asarray(reference['eigenvalues'])
    if a.shape!=(6,) or b.shape!=(6,): raise ValueError('six signed roots required')
    errors=abs(a-b)/np.maximum(1.,abs(b))
    return dict(cursor=cursor,displacement=equilibrium['displacement'],macros=6,
        native_load=native['equilibrium_load_parameter'],continuum_load=float(1e6*equilibrium['load']),
        native_eigenvalues=a.tolist(),continuum_eigenvalues=b.tolist(),
        native_negative_modes=int(np.count_nonzero(a<0)),continuum_negative_modes=int(np.count_nonzero(b<0)),
        eigenvalue_relative_errors=errors.tolist(),coarse_eigenvalue_relative_errors=coarse['eigenvalue_relative_errors'],
        every_error_decreased=bool(np.all(errors<np.asarray(coarse['eigenvalue_relative_errors']))),
        native_spectral_residual=native['spectral_residual'],native_original_ritz_residual=native['original_ritz_residual'],
        same_equilibrium_branch_proved=False,buckling_factor_authorized=False)


def validate(output,raw,revision):
    value=parse(raw)
    if (value['schema']!='GE_BEAM3_SIX_MACRO_LOADED_SPECTRA_DEVELOPMENT_V1' or value['revision']!=revision
            or value['status']!='DEVELOPMENT_REFINEMENT_NOT_QUALIFICATION' or value['production_qualified'] is not False
            or value['independent_review']!='PENDING' or value['new_native_nonlinear_solves']!=0
            or value['new_reference_solves']!=0 or value['new_native_spectra']!=2
            or value['coordinate_limit']!=128 or value['exact_dimension_limit']!=96):
        raise ValueError('six-macro development scope')
    inventory=[]
    for name in ARTIFACTS:
        data=read(output/name); inventory.append(dict(path=name,bytes=len(data),sha256=sha256(data).hexdigest()))
    if value['artifacts']!=inventory: raise ValueError('six-macro hash DAG')
    for name,data in inputs().items():
        if read(output/name)!=data: raise ValueError('six-macro bound input copy')
    coarse=parse(read(output/'baseline-comparison.json')); rows=[]
    for index,cursor in enumerate((1,4)):
        native=parse(read(output/f'native-{cursor}.json')); modes=native['modes']; packet=native['packet']
        if (modes['checkpoint_sha256']!=sha256(read(output/f'checkpoint-{cursor}.json')).hexdigest()
                or modes['state_advanced'] is not False or modes['continuation_constraint_retained'] is not False
                or modes['checkpoint_converted'] is not False or modes['buckling_factor_authorized'] is not False
                or modes['production_qualified'] is not False or len(packet['geometric'])!=114
                or len(packet['free'])-len(packet['algebraic'])!=69):
            raise ValueError('six-macro state or allocation identity')
        if max(modes['spectral_residual'],modes['original_ritz_residual'])>1e-11: raise ValueError('six-macro native residual')
        rows.append(row(cursor,modes,parse(read(output/f'reference-{cursor}.json')),
            parse(read(output/f'equilibrium-{cursor}.json')),coarse['rows'][index]))
    if canonical(rows)!=canonical(value['rows']): raise ValueError('six-macro summary changed')
    return value


def build(save,progress):
    captured=inputs()
    for name,data in captured.items(): save(name,data)
    from docs.reference_cases import ge_beam3_fibre_arch_refinement as family
    from anysolver import _ge_beam3_seeded_fibre_control as control
    from anysolver import _ge_beam3_controlled_fibre_modes as spectral
    from anysolver._ge_beam3_p5_seeded.core import canonical as native_canonical
    import numpy as np
    model=family.model(6); program=family.program(6); context=control.Context(model,program)
    _,records=context.restore(captured['input-six.json'],expected_sha256=INPUT_SHA)
    if context.checkpoint(records)!=captured['input-six.json']: raise ValueError('six-macro replay changed')
    inertias={eid:np.diag([1.,1.,1.,.02,.01,.01]) for eid in model.mesh.elements}
    coarse=parse(captured['baseline-comparison.json']); rows=[]
    for index,cursor in enumerate((1,4)):
        capsule=context.checkpoint(records[:cursor]); save(f'checkpoint-{cursor}.json',capsule)
        progress(dict(stage='NATIVE_FIXED_LOAD_SPECTRUM',cursor=cursor,macros=6))
        packet,modes=spectral.solve_modes(model,program,capsule,inertias,material_policy=spectral.FROZEN,
            bounds=(-1e6,1e8),num_modes=6,expected_checkpoint_sha256=sha256(capsule).hexdigest(),
            coordinate_limit=128,exact_dimension_limit=96)
        data=native_canonical(dict(packet=packet,modes=modes)); save(f'native-{cursor}.json',data)
        rows.append(row(cursor,parse(data)['modes'],parse(captured[f'reference-{cursor}.json']),
            parse(captured[f'equilibrium-{cursor}.json']),coarse['rows'][index]))
        progress(dict(stage='TARGET_COMPLETE',cursor=cursor))
    if inputs()!=captured: raise ValueError('six-macro inputs changed during comparison')
    return dict(schema='GE_BEAM3_SIX_MACRO_LOADED_SPECTRA_DEVELOPMENT_V1',rows=rows,
        status='DEVELOPMENT_REFINEMENT_NOT_QUALIFICATION',production_qualified=False,independent_review='PENDING',
        new_native_nonlinear_solves=0,new_reference_solves=0,new_native_spectra=2,
        coordinate_limit=128,exact_dimension_limit=96)


def worker(revision,output):
    guard(revision)
    if any(os.environ.get(k)!=v for k,v in THREAD_ENVIRONMENT.items()): raise ValueError('one numerical thread')
    sys.path.insert(0,str(ROOT/'src'))
    def save(name,data):
        with (output/name).open('xb') as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
    def progress(event): print(json.dumps(event,sort_keys=True),flush=True)
    progress(dict(stage='INITIALIZATION')); value=build(save,progress); inventory=[]
    for name in ARTIFACTS:
        data=read(output/name); inventory.append(dict(path=name,bytes=len(data),sha256=sha256(data).hexdigest()))
    value.update(revision=revision,artifacts=inventory); raw=canonical(value)
    validate(output,raw,revision); guard(revision); save('comparison.pending.json',raw); progress(dict(stage='COMPLETION'))


def run(revision,output):
    guard(revision)
    if os.name!='nt' or not output.is_absolute() or output.resolve().is_relative_to(Path('C:/Github')): raise ValueError('external Windows output')
    output.mkdir(parents=True,exist_ok=False); env=dict(os.environ); env.update(THREAD_ENVIRONMENT)
    env.pop('PYTHONPATH',None); env['PYTHONDONTWRITEBYTECODE']='1'; env['PYTHONHASHSEED']='0'
    command=[sys.executable,'-B','-m','docs.reference_cases.ge_beam3_loaded_arch_refinement','--worker','--revision',revision,'--output',str(output)]
    job=_ProcessJob(24*(1<<30)); start=time.monotonic(); last=(0,0); activity=start
    try:
        with (output/'stdout.log').open('xb') as stdout,(output/'stderr.log').open('xb') as stderr:
            process=job.launch(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
            while True:
                cpu,active,memory=job.accounting(); now=time.monotonic(); code=process.poll()
                current=(cpu,(output/'stdout.log').stat().st_size)
                if current!=last: activity=now; last=current
                if now-start>=600 or now-activity>=120 or memory>=24*(1<<30): raise RuntimeError('six-macro process resource bound')
                if code is not None and active==0: break
                time.sleep(.2)
            if code!=0: raise RuntimeError('six-macro spectral child failed; no retry')
        raw=read(output/'comparison.pending.json'); validate(output,raw,revision); guard(revision)
    finally:
        try:
            if not job.terminate(): raise RuntimeError('six-macro cleanup unproven')
        finally: job.close()
    guard(revision)
    if read(output/'comparison.pending.json')!=raw: raise ValueError('six-macro result changed after cleanup')
    validate(output,raw,revision); os.link(output/'comparison.pending.json',output/'comparison.json')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--revision',required=True)
    parser.add_argument('--output',required=True,type=Path); parser.add_argument('--worker',action='store_true')
    args=parser.parse_args(); (worker if args.worker else run)(args.revision,args.output)
