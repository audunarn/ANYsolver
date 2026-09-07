"""Frozen bounded unloaded curved spectral diagnostic, no automatic retry."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import time
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,_ProcessJob,THREAD_ENVIRONMENT
from docs.reference_cases.ge_beam3_preserved_arch_load_comparison import canonical,parse

ROOT=Path(__file__).resolve().parents[2]
ARTIFACTS=('checkpoint-1.json','checkpoint-2.json','checkpoint-4.json',
    'modes-1.json','modes-2.json','modes-4.json','reference-diagnostic.json')


def read(path):
    if path.is_symlink() or not path.is_file() or not 0<path.stat().st_size<=2*(1<<20): raise ValueError('bounded regular spectral evidence')
    raw=path.read_bytes(); parse(raw); return raw


def validate(output,raw,revision):
    import numpy as np
    value=parse(raw)
    if (value['revision']!=revision or value['schema']!='GE_BEAM3_CURVED_REFERENCE_MODES_DEVELOPMENT_V1'
            or value['status']!='DEVELOPMENT_SPECTRAL_COMPARISON_NOT_QUALIFICATION'
            or value['production_qualified'] is not False or value['independent_review']!='PENDING'
            or value['nonlinear_solves']!=0 or value['new_reference_solves']!=2 or value['new_native_spectra']!=3
            or value['unloaded_only'] is not True or value['clustered_mac_qualification'] is not False
            or value['buckling_factor_authorized'] is not False or [r['macros'] for r in value['rows']]!=[1,2,4]):
        raise ValueError('complete development-only spectral scope')
    inventory=[]
    for name in ARTIFACTS:
        data=read(output/name); inventory.append(dict(path=name,bytes=len(data),sha256=sha256(data).hexdigest()))
    if value['artifacts']!=inventory: raise ValueError('spectral artifact hash mismatch')
    refs=parse(read(output/'reference-diagnostic.json'))
    if [(r['degree'],r['quadrature']) for r in refs]!=[(14,64),(18,80)]: raise ValueError('reference profile scope')
    fine=np.asarray(refs[-1]['eigenvalues']); discrepancy=float(np.max(abs(np.asarray(refs[0]['eigenvalues'])/fine-1)))
    if len(fine)!=6 or np.min(fine)<=0 or discrepancy>=1e-8: raise ValueError('complete positive converged reference roots')
    for row in value['rows']:
        count=row['macros']; detail=parse(read(output/f'modes-{count}.json')); modes=detail['modes']; fields=detail['field_comparison']
        if detail['checkpoint_sha256']!=sha256(read(output/f'checkpoint-{count}.json')).hexdigest(): raise ValueError('virgin native checkpoint identity')
        eigenvalues=np.asarray(modes['eigenvalues'])
        if eigenvalues.shape!=(6,) or np.min(eigenvalues)<=0: raise ValueError('complete positive native roots')
        expected=dict(macros=count,eigenvalues=eigenvalues.tolist(),reference_eigenvalues=fine.tolist(),
            relative_frequency_errors=np.abs(np.sqrt(eigenvalues/fine)-1).tolist(),diagonal_mac=np.diag(fields['mac']).tolist(),
            spectral_residual=modes['spectral_residual'],original_ritz_residual=modes['original_ritz_residual'],
            reference_profile_eigenvalue_difference=discrepancy)
        if canonical(expected)!=canonical(row): raise ValueError('spectral summary differs from raw packet')
        if max(modes['spectral_residual'],modes['original_ritz_residual'])>1e-11: raise ValueError('native spectral residual')
    return value


def worker(revision,output):
    guard(revision)
    if any(os.environ.get(k)!=v for k,v in THREAD_ENVIRONMENT.items()): raise ValueError('one numerical thread required')
    sys.path.insert(0,str(ROOT/'src'))
    from docs.reference_cases.ge_beam3_curved_reference_modes import build
    def save(name,raw):
        with (output/name).open('xb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    def progress(value): print(json.dumps(value,sort_keys=True),flush=True)
    progress(dict(stage='INITIALIZATION')); value=build(save,progress); inventory=[]
    for name in ARTIFACTS:
        raw=read(output/name); inventory.append(dict(path=name,bytes=len(raw),sha256=sha256(raw).hexdigest()))
    value.update(revision=revision,artifacts=inventory); raw=canonical(value)
    validate(output,raw,revision); guard(revision); save('comparison.pending.json',raw)
    progress(dict(stage='COMPLETION'))


def run(revision,output):
    if os.name!='nt': raise ValueError('Windows process containment required')
    guard(revision)
    if not output.is_absolute() or output.resolve().is_relative_to(Path('C:/Github').resolve()): raise ValueError('fresh external absolute output')
    output.mkdir(parents=True,exist_ok=False)
    env=dict(os.environ); env.update(THREAD_ENVIRONMENT); env.pop('PYTHONPATH',None)
    env['PYTHONDONTWRITEBYTECODE']='1'; env['PYTHONHASHSEED']='0'
    command=[sys.executable,'-B','-m','docs.reference_cases.ge_beam3_curved_reference_modes_probe',
        '--worker','--revision',revision,'--output',str(output)]
    job=_ProcessJob(24*(1<<30)); start=time.monotonic(); activity=start; last=(0,0)
    try:
        with (output/'stdout.log').open('xb') as stdout,(output/'stderr.log').open('xb') as stderr:
            process=job.launch(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
            while True:
                cpu,active,memory=job.accounting(); code=process.poll(); now=time.monotonic()
                current=(cpu,(output/'stdout.log').stat().st_size)
                if current!=last: activity=now; last=current
                if now-start>=600 or now-activity>=120 or memory>=24*(1<<30): raise RuntimeError('spectral wall/inactivity/memory bound')
                if code is not None and active==0: break
                time.sleep(.2)
            if code!=0: raise RuntimeError(f'spectral child failed: {code}; no retry')
        raw=read(output/'comparison.pending.json'); validate(output,raw,revision); guard(revision)
    finally:
        try:
            if not job.terminate(): raise RuntimeError('complete spectral process cleanup unproven')
        finally: job.close()
    guard(revision)
    if read(output/'comparison.pending.json')!=raw: raise ValueError('pending spectral comparison changed')
    validate(output,raw,revision); os.link(output/'comparison.pending.json',output/'comparison.json')


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--revision',required=True)
    parser.add_argument('--output',required=True,type=Path); parser.add_argument('--worker',action='store_true')
    args=parser.parse_args(); (worker if args.worker else run)(args.revision,args.output)


if __name__=='__main__': main()
