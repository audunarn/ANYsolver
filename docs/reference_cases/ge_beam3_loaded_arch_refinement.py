"""Explicit bounded six/twelve-macro spectra using preserved evidence."""
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


def configuration(macros):
    if type(macros) is not int or macros not in (6,12): raise ValueError('registered spectral refinement size required')
    if macros==6:
        return dict(macros=6,word='six',input=INPUT,size=141754,sha=INPUT_SHA,old=OLD,base_size=3689,base_sha=BASELINE_SHA,
            base_revision=BASELINE_REVISION,coordinate_limit=128,exact_dimension_limit=96,retained_limit=256,
            spectral_dimension=114,dynamic_dimension=69,artifacts=ARTIFACTS)
    return dict(macros=12,word='twelve',input=EXTERNAL/'ge-beam3-fibre-arch12-20260907-v1/checkpoint-diagnostic.json',
        size=278640,sha='ca95e88b6d354c3aeeb4bcebc1f49791cb3b1cef0781644f3be0e696e3a33683',
        old=EXTERNAL/'ge-beam3-loaded-six-20260907-v2',base_size=3490,
        base_sha='f50285799e45a7fdbbcb7d9cad997b13e83a8e7bf38e6904c4c1e247595d5362',
        base_revision='4204f3a38c65fc215a76c595f994a7a71c317d54',coordinate_limit=256,exact_dimension_limit=160,
        retained_limit=512,spectral_dimension=222,dynamic_dimension=141,artifacts=('input-twelve.json',)+ARTIFACTS[1:])


def inputs(macros=6):
    config=configuration(macros); old=config['old']; raw=read(config['input']); base=read(old/'comparison.json')
    if len(raw)!=config['size'] or sha256(raw).hexdigest()!=config['sha']: raise ValueError(config['word']+'-macro input changed')
    if len(base)!=config['base_size'] or sha256(base).hexdigest()!=config['base_sha']: raise ValueError('baseline comparison changed')
    if macros==6: baseline.validate(old,base,config['base_revision'])
    else: validate(old,base,config['base_revision'])
    value=parse(base); artifacts={a['path']:a for a in value['artifacts']}
    found={config['artifacts'][0]:raw,'baseline-comparison.json':base}
    for cursor in (1,4):
        for src,dst in ((f'equilibrium-{cursor}.json',f'equilibrium-{cursor}.json'),
                        (f'ritz-{cursor}-16.json' if macros==6 else f'reference-{cursor}.json',f'reference-{cursor}.json')):
            data=read(old/src)
            if len(data)!=artifacts[src]['bytes'] or sha256(data).hexdigest()!=artifacts[src]['sha256']:
                raise ValueError('saved continuum reference changed')
            found[dst]=data
    return found


def row(cursor,native,reference,equilibrium,coarse,macros=6):
    import numpy as np
    a=np.asarray(native['eigenvalues']); b=np.asarray(reference['eigenvalues'])
    if a.shape!=(6,) or b.shape!=(6,): raise ValueError('six signed roots required')
    errors=abs(a-b)/np.maximum(1.,abs(b))
    return dict(cursor=cursor,displacement=equilibrium['displacement'],macros=macros,
        native_load=native['equilibrium_load_parameter'],continuum_load=float(1e6*equilibrium['load']),
        native_eigenvalues=a.tolist(),continuum_eigenvalues=b.tolist(),
        native_negative_modes=int(np.count_nonzero(a<0)),continuum_negative_modes=int(np.count_nonzero(b<0)),
        eigenvalue_relative_errors=errors.tolist(),coarse_eigenvalue_relative_errors=coarse['eigenvalue_relative_errors'],
        every_error_decreased=bool(np.all(errors<np.asarray(coarse['eigenvalue_relative_errors']))),
        native_spectral_residual=native['spectral_residual'],native_original_ritz_residual=native['original_ritz_residual'],
        same_equilibrium_branch_proved=False,buckling_factor_authorized=False)


def validate(output,raw,revision,macros=6):
    config=configuration(macros)
    value=parse(raw)
    if (value['schema']!='GE_BEAM3_'+config['word'].upper()+'_MACRO_LOADED_SPECTRA_DEVELOPMENT_V1' or value['revision']!=revision
            or value['status']!='DEVELOPMENT_REFINEMENT_NOT_QUALIFICATION' or value['production_qualified'] is not False
            or value['independent_review']!='PENDING' or value['new_native_nonlinear_solves']!=0
            or value['new_reference_solves']!=0 or value['new_native_spectra']!=2
            or value['coordinate_limit']!=config['coordinate_limit'] or value['exact_dimension_limit']!=config['exact_dimension_limit']
            or (macros==12 and value['retained_coordinate_limit']!=512)):
        raise ValueError('six-macro development scope')
    inventory=[]
    for name in config['artifacts']:
        data=read(output/name); inventory.append(dict(path=name,bytes=len(data),sha256=sha256(data).hexdigest()))
    if value['artifacts']!=inventory: raise ValueError('six-macro hash DAG')
    for name,data in inputs(macros).items():
        if read(output/name)!=data: raise ValueError('six-macro bound input copy')
    coarse=parse(read(output/'baseline-comparison.json')); rows=[]
    for index,cursor in enumerate((1,4)):
        native=parse(read(output/f'native-{cursor}.json')); modes=native['modes']; packet=native['packet']
        if (modes['checkpoint_sha256']!=sha256(read(output/f'checkpoint-{cursor}.json')).hexdigest()
                or modes['state_advanced'] is not False or modes['continuation_constraint_retained'] is not False
                or modes['checkpoint_converted'] is not False or modes['buckling_factor_authorized'] is not False
                or modes['production_qualified'] is not False or len(packet['geometric'])!=config['spectral_dimension']
                or len(packet['free'])-len(packet['algebraic'])!=config['dynamic_dimension']):
            raise ValueError('six-macro state or allocation identity')
        if max(modes['spectral_residual'],modes['original_ritz_residual'])>1e-11: raise ValueError('six-macro native residual')
        rows.append(row(cursor,modes,parse(read(output/f'reference-{cursor}.json')),
            parse(read(output/f'equilibrium-{cursor}.json')),coarse['rows'][index],macros))
    if canonical(rows)!=canonical(value['rows']): raise ValueError('six-macro summary changed')
    return value


def build(save,progress,macros=6):
    config=configuration(macros); captured=inputs(macros); input_name=config['artifacts'][0]
    for name,data in captured.items(): save(name,data)
    from docs.reference_cases import ge_beam3_fibre_arch_refinement as family
    from anysolver import _ge_beam3_seeded_fibre_control as control
    from anysolver import _ge_beam3_controlled_fibre_modes as spectral
    from anysolver._ge_beam3_p5_seeded.core import canonical as native_canonical
    import numpy as np
    model=family.model(macros); program=family.program(macros); context=control.Context(model,program,max_coordinates=config['retained_limit'])
    _,records=context.restore(captured[input_name],expected_sha256=config['sha'])
    if context.checkpoint(records)!=captured[input_name]: raise ValueError('refinement replay changed')
    inertias={eid:np.diag([1.,1.,1.,.02,.01,.01]) for eid in model.mesh.elements}
    coarse=parse(captured['baseline-comparison.json']); rows=[]
    for index,cursor in enumerate((1,4)):
        capsule=context.checkpoint(records[:cursor]); save(f'checkpoint-{cursor}.json',capsule)
        progress(dict(stage='NATIVE_FIXED_LOAD_SPECTRUM',cursor=cursor,macros=macros))
        packet,modes=spectral.solve_modes(model,program,capsule,inertias,material_policy=spectral.FROZEN,
            bounds=(-1e6,1e8),num_modes=6,expected_checkpoint_sha256=sha256(capsule).hexdigest(),
            coordinate_limit=config['coordinate_limit'],exact_dimension_limit=config['exact_dimension_limit'],
            max_coordinates=config['retained_limit'])
        data=native_canonical(dict(packet=packet,modes=modes)); save(f'native-{cursor}.json',data)
        rows.append(row(cursor,parse(data)['modes'],parse(captured[f'reference-{cursor}.json']),
            parse(captured[f'equilibrium-{cursor}.json']),coarse['rows'][index],macros))
        progress(dict(stage='TARGET_COMPLETE',cursor=cursor))
    if inputs(macros)!=captured: raise ValueError('refinement inputs changed during comparison')
    return dict(schema='GE_BEAM3_'+config['word'].upper()+'_MACRO_LOADED_SPECTRA_DEVELOPMENT_V1',rows=rows,
        status='DEVELOPMENT_REFINEMENT_NOT_QUALIFICATION',production_qualified=False,independent_review='PENDING',
        new_native_nonlinear_solves=0,new_reference_solves=0,new_native_spectra=2,
        coordinate_limit=config['coordinate_limit'],exact_dimension_limit=config['exact_dimension_limit'],
        **({'retained_coordinate_limit':512} if macros==12 else {}))


def worker(revision,output,macros=6):
    guard(revision)
    config=configuration(macros)
    if any(os.environ.get(k)!=v for k,v in THREAD_ENVIRONMENT.items()): raise ValueError('one numerical thread')
    sys.path.insert(0,str(ROOT/'src'))
    def save(name,data):
        with (output/name).open('xb') as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
    def progress(event): print(json.dumps(event,sort_keys=True),flush=True)
    progress(dict(stage='INITIALIZATION')); value=build(save,progress,macros); inventory=[]
    for name in config['artifacts']:
        data=read(output/name); inventory.append(dict(path=name,bytes=len(data),sha256=sha256(data).hexdigest()))
    value.update(revision=revision,artifacts=inventory); raw=canonical(value)
    validate(output,raw,revision,macros); guard(revision); save('comparison.pending.json',raw); progress(dict(stage='COMPLETION'))


def run(revision,output,macros=6):
    guard(revision)
    configuration(macros)
    if os.name!='nt' or not output.is_absolute() or output.resolve().is_relative_to(Path('C:/Github')): raise ValueError('external Windows output')
    output.mkdir(parents=True,exist_ok=False); env=dict(os.environ); env.update(THREAD_ENVIRONMENT)
    env.pop('PYTHONPATH',None); env['PYTHONDONTWRITEBYTECODE']='1'; env['PYTHONHASHSEED']='0'
    command=[sys.executable,'-B','-m','docs.reference_cases.ge_beam3_loaded_arch_refinement','--worker','--revision',revision,'--output',str(output),'--macros',str(macros)]
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
        raw=read(output/'comparison.pending.json'); validate(output,raw,revision,macros); guard(revision)
    finally:
        try:
            if not job.terminate(): raise RuntimeError('six-macro cleanup unproven')
        finally: job.close()
    guard(revision)
    if read(output/'comparison.pending.json')!=raw: raise ValueError('six-macro result changed after cleanup')
    validate(output,raw,revision,macros); os.link(output/'comparison.pending.json',output/'comparison.json')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--revision',required=True)
    parser.add_argument('--output',required=True,type=Path); parser.add_argument('--worker',action='store_true')
    parser.add_argument('--macros',type=int,choices=(6,12),default=6)
    args=parser.parse_args(); (worker if args.worker else run)(args.revision,args.output,args.macros)
