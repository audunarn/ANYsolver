"""Single bounded loaded-arch diagnostic, preserved native histories only."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import time
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,_ProcessJob,THREAD_ENVIRONMENT
from docs.reference_cases.ge_beam3_preserved_arch_load_comparison import canonical,_pairs,_constant

ROOT=Path(__file__).resolve().parents[2]
ARTIFACTS=('checkpoint-1.json','checkpoint-4.json','equilibrium-1.json','equilibrium-4.json','input-checkpoint.json',
    'native-1.json','native-4.json','ritz-1-12.json','ritz-1-16.json','ritz-4-12.json','ritz-4-16.json')


def read(path):
    if path.is_symlink() or not path.is_file() or not 0<path.stat().st_size<=8*(1<<20): raise ValueError('bounded regular loaded spectral evidence')
    raw=path.read_bytes(); parse(raw); return raw


def parse(raw):
    if type(raw) is not bytes or not 0<len(raw)<=8*(1<<20): raise ValueError('bounded evidence bytes')
    value=json.loads(raw,object_pairs_hook=_pairs,parse_constant=_constant)
    if canonical(value)!=raw: raise ValueError('strict canonical loaded evidence')
    return value


def validate(output,raw,revision):
    import numpy as np
    value=parse(raw)
    if (value['schema']!='GE_BEAM3_LOADED_ARCH_SPECTRAL_DEVELOPMENT_V1' or value['revision']!=revision
            or value['production_qualified'] is not False or value['independent_review']!='PENDING'
            or value['status']!='DEVELOPMENT_LOADED_SPECTRA_NOT_QUALIFICATION'
            or value['native_nonlinear_solves']!=0 or value['new_continuum_equilibria']!=2
            or value['new_reference_spectra']!=4 or value['new_native_spectra']!=2
            or value['buckling_factor_authorized'] is not False or value['failed_input_invocation_reclassified'] is not False
            or [(r['cursor'],r['displacement']) for r in value['rows']]!=[(1,.01),(4,.055)]):
        raise ValueError('complete loaded development scope')
    inventory=[]
    for name in ARTIFACTS:
        data=read(output/name); inventory.append(dict(path=name,bytes=len(data),sha256=sha256(data).hexdigest()))
    if value['artifacts']!=inventory or sha256(read(output/'input-checkpoint.json')).hexdigest()!=value['input_sha256']:
        raise ValueError('loaded spectral hash DAG mismatch')
    for row in value['rows']:
        i=row['cursor']; native=parse(read(output/f'native-{i}.json'))['modes']
        coarse=parse(read(output/f'ritz-{i}-12.json')); fine=parse(read(output/f'ritz-{i}-16.json'))
        reference=parse(read(output/f'equilibrium-{i}.json'))
        if (native['checkpoint_sha256']!=sha256(read(output/f'checkpoint-{i}.json')).hexdigest()
                or native['state_advanced'] is not False or native['continuation_constraint_retained'] is not False
                or native['checkpoint_converted'] is not False or native['buckling_factor_authorized'] is not False):
            raise ValueError('saved-state spectral authority changed')
        a=np.asarray(native['eigenvalues']); b=np.asarray(fine['eigenvalues'])
        if a.shape!=(6,) or b.shape!=(6,): raise ValueError('six complete spatial roots')
        profile=float(np.max(abs(np.asarray(coarse['eigenvalues'])-b)/np.maximum(1.,abs(b))))
        expected=dict(cursor=i,displacement=reference['displacement'],native_load=native['equilibrium_load_parameter'],
            continuum_load=float(1e6*reference['load']),continuum_load_slope=float(1e6*reference['load_slope']),
            native_eigenvalues=a.tolist(),continuum_eigenvalues=b.tolist(),native_negative_modes=int(np.count_nonzero(a<0)),
            continuum_negative_modes=int(np.count_nonzero(b<0)),eigenvalue_relative_errors=(abs(a-b)/np.maximum(1.,abs(b))).tolist(),
            reference_resolution_error=profile,native_spectral_residual=native['spectral_residual'],
            native_original_ritz_residual=native['original_ritz_residual'],reference_ritz_residual=fine['residual'],
            fixed_load_perturbation=True,control_constraint_retained=False,same_equilibrium_branch_proved=False)
        if canonical(expected)!=canonical(row): raise ValueError('loaded spectral summary differs from raw data')
        if profile>1e-7 or max(native['spectral_residual'],native['original_ritz_residual'])>1e-11:
            raise ValueError('loaded spectrum numerical residual or profile')
    return value


def worker(revision,output):
    guard(revision)
    if any(os.environ.get(k)!=v for k,v in THREAD_ENVIRONMENT.items()): raise ValueError('one numerical thread')
    sys.path.insert(0,str(ROOT/'src'))
    from docs.reference_cases.ge_beam3_loaded_arch_spectra import build
    def save(name,raw):
        with (output/name).open('xb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    def progress(event): print(json.dumps(event,sort_keys=True),flush=True)
    progress(dict(stage='INITIALIZATION')); value=build(save,progress); inventory=[]
    for name in ARTIFACTS:
        raw=read(output/name); inventory.append(dict(path=name,bytes=len(raw),sha256=sha256(raw).hexdigest()))
    value.update(revision=revision,artifacts=inventory); raw=canonical(value)
    validate(output,raw,revision); guard(revision); save('comparison.pending.json',raw); progress(dict(stage='COMPLETION'))


def run(revision,output):
    if os.name!='nt': raise ValueError('Windows Job containment required')
    guard(revision)
    if not output.is_absolute() or output.resolve().is_relative_to(Path('C:/Github').resolve()): raise ValueError('fresh external absolute output')
    output.mkdir(parents=True,exist_ok=False); env=dict(os.environ); env.update(THREAD_ENVIRONMENT)
    env.pop('PYTHONPATH',None); env['PYTHONDONTWRITEBYTECODE']='1'; env['PYTHONHASHSEED']='0'
    command=[sys.executable,'-B','-m','docs.reference_cases.ge_beam3_loaded_arch_spectra_probe','--worker','--revision',revision,'--output',str(output)]
    job=_ProcessJob(24*(1<<30)); start=time.monotonic(); activity=start; last=(0,0)
    try:
        with (output/'stdout.log').open('xb') as stdout,(output/'stderr.log').open('xb') as stderr:
            process=job.launch(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
            while True:
                cpu,active,memory=job.accounting(); code=process.poll(); now=time.monotonic()
                current=(cpu,(output/'stdout.log').stat().st_size)
                if current!=last: activity=now; last=current
                if now-start>=600 or now-activity>=120 or memory>=24*(1<<30): raise RuntimeError('loaded spectrum resource bound')
                if code is not None and active==0: break
                time.sleep(.2)
            if code!=0: raise RuntimeError(f'loaded spectrum child failed: {code}; no retry')
        raw=read(output/'comparison.pending.json'); validate(output,raw,revision); guard(revision)
    finally:
        try:
            if not job.terminate(): raise RuntimeError('loaded spectral process cleanup unproven')
        finally: job.close()
    guard(revision)
    if read(output/'comparison.pending.json')!=raw: raise ValueError('loaded evidence changed after cleanup')
    validate(output,raw,revision); os.link(output/'comparison.pending.json',output/'comparison.json')


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--revision',required=True)
    parser.add_argument('--output',required=True,type=Path); parser.add_argument('--worker',action='store_true')
    args=parser.parse_args(); (worker if args.worker else run)(args.revision,args.output)


if __name__=='__main__': main()
