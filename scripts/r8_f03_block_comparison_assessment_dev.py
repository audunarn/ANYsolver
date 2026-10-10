"""Single owned fresh180s development ledger, bounded serial process-tree checks.

Explicit run only; final60s reserve. Existing attempts/failures are immutable; one unchanged saved809 assessment only.
No factorization, source reconstruction, physical solve or qualification.
"""
import argparse
from dataclasses import asdict
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT/'docs/agent_plans/development/r8-f03-common-density-20261010/block-assessment-v1'
ENV = {name: '1' for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
       'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'NUMBA_NUM_THREADS', 'NUMBA_DISABLE_JIT')}
ENV['PYTHONOPTIMIZE'] = '0'
SOURCES = ('scripts/r8_f03_block_comparison_dev.py', 'scripts/r8_f03_block_comparison_assessment_dev.py',
    'scripts/r8_f03_finite_local_dev.py',
    'scripts/r8_f03_finite_sparse_dev.py', 'scripts/_b3_e4_f03_local_scientific_supervisor.py',
    'scripts/_b3_e4_f03_local_scientific_cases.py',
    'docs/agent_plans/development/r8-f03-common-density-20261010/block-assessment-v1/AUTHORITY.json',
    'docs/agent_plans/development/r8-f03-common-density-20261010/block-comparison-v1/DERIVATION.md',
    'docs/agent_plans/development/r8-f03-common-density-20261010/block-comparison-v1/SAME_PENCIL_BINDINGS.json',
    'docs/agent_plans/development/r8-f03-common-density-20261010/block-comparison-v1/CONTROLS_FINAL_BINDINGS.json',
    'docs/agent_plans/development/r8-f03-common-density-20261010/growing-v1/FINAL_BINDINGS.json')



def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False, default=str)+'\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def trusted_inputs():
    base=ROOT/'docs/agent_plans/development/r8-f03-common-density-20261010'
    prior=json.loads((base/'block-comparison-v1/SAME_PENCIL_BINDINGS.json').read_text())
    frozen=json.loads((base/'growing-v1/FINAL_BINDINGS.json').read_text())['files']
    folder=base/'growing-v1/attempt-01'; expected=prior['expected_hashes']
    if Path(prior['folder']).resolve()!=folder.resolve() or len(expected)!=7:
        raise RuntimeError('fixed saved809 binding required')
    checks=[]
    for name,h in expected.items():
        rel=(folder/name).relative_to(ROOT).as_posix()
        if frozen.get(rel)!=h or sha(folder/name)!=h:raise RuntimeError('prior frozen hash mismatch')
        checks.append({'path':rel,'sha256':h,'bytes':(folder/name).stat().st_size})
    controls=json.loads((base/'block-comparison-v1/CONTROLS_FINAL_BINDINGS.json').read_text())
    for rel in ('scripts/r8_f03_block_comparison_dev.py','scripts/r8_f03_finite_local_dev.py','scripts/r8_f03_finite_sparse_dev.py'):
        if sha(ROOT/rel)!=controls['files'].get(rel,controls['files'].get('docs/agent_plans/development/r8-f03-common-density-20261010/block-comparison-v1/attempt-01/source/'+rel)):raise RuntimeError('tested algorithm dependency changed')
    return folder,expected,checks


def child(folder):
    import psutil
    psutil.Process().cpu_affinity([0])
    import numpy as np
    import numba
    from threadpoolctl import threadpool_info
    import traceback
    import xml.etree.ElementTree as xml
    from scripts import r8_f03_block_comparison_dev as block
    runtime={'affinity':psutil.Process().cpu_affinity(),'environment':{k:os.getenv(k) for k in ENV},
             'optimization':sys.flags.optimize,'pools':threadpool_info(),'python':sys.version,
             'numpy':np.__version__,'numba_disable_jit':bool(numba.config.DISABLE_JIT),'numba_threads':numba.get_num_threads()}
    save(folder/'effective-runtime.json',runtime)
    if (runtime['affinity']!=[0] or runtime['environment']!=ENV or runtime['optimization']!=0 or
        not runtime['numba_disable_jit'] or runtime['numba_threads']!=1 or not runtime['pools'] or
        any(p['num_threads']!=1 for p in runtime['pools'])):raise RuntimeError('effective runtime contract')
    launch=json.loads((folder/'binding.json').read_text())
    for relative,h in launch['sources'].items():
        if sha(ROOT/relative)!=h:raise RuntimeError('bound source changed before assessment')
    inputs,expected,checks=trusted_inputs();save(folder/'validated-input-hashes.json',checks)
    budget=block.exact_budget();phase='loader';save(folder/'progress.json',{'phase':phase,'loader_calls':1,'bound_calls':0})
    started=time.perf_counter();result=None;loaded=None
    try:
        loaded=block.saved_candidate_inputs(inputs,expected,budget=budget)
        if len(loaded['permuted_rhs'])!=809:raise RuntimeError('fixed809 inventory required')
        phase='block_bound';save(folder/'progress.json',{'phase':phase,'loader_calls':1,'bound_calls':1,'input_operations':budget.operations})
        result=block.lu_block_comparison(loaded['lower'],loaded['upper'],loaded['permuted_rhs'],loaded['pr'],loaded['pc'],
                                       width=18,provenance=loaded['provenance'],budget=budget)
        summary={k:result[k] for k in ('status','q_upper','q_exact','operations_used','width','provenance','inertia','coercivity','physical_acceptance','qualification')}
        summary.update(lower_maximum=max(result['lower']['bound']),upper_maximum=max(result['upper']['bound']),
                       lower_block_count=len(result['lower']['blocks']),upper_block_count=len(result['upper']['blocks']))
        save(folder/'block-bounds.json',{'factor_coordinate_bound':result['factor_coordinate_bound'],
                                       'original_coordinate_bound':result['original_coordinate_bound'],
                                       'lower':result['lower'],'upper':result['upper']})
    except block.Unresolved as error:
        traceback.print_exc();summary={'status':'UNRESOLVED','refusal_type':'Unresolved','refusal':str(error),'phase':phase,'operations_used':budget.operations}
    finally:
        runtime.update(final_pools=threadpool_info(),final_numba_disable_jit=bool(numba.config.DISABLE_JIT),
                       final_numba_threads=numba.get_num_threads(),final_affinity=psutil.Process().cpu_affinity())
        save(folder/'effective-runtime.json',runtime)
    valid=(runtime['final_affinity']==[0] and runtime['final_numba_disable_jit'] and runtime['final_numba_threads']==1
           and bool(runtime['final_pools']) and all(p['num_threads']==1 for p in runtime['final_pools']))
    summary.update(dimension=809,width=18,loader_calls=1,bound_calls=int(phase=='block_bound'),
                   caller_conditional_only=True,source_assessment=False,factorization=False,scientific_floor_comparison=None,
                   qualification=False,inertia=None,coercivity=None,physical_acceptance=None,
                   final_runtime_contract_passed=valid,assessment_body_seconds=time.perf_counter()-started)
    if loaded is not None:
        summary.update(prior_q=loaded['retained_prior_q'],unchanged_kappa=loaded['unchanged_kappa'],
                       unchanged_J_sha256=hashlib.sha256(json.dumps(loaded['unchanged_J'],sort_keys=True).encode()).hexdigest(),
                       retained_raw_target_flags=loaded['retained_raw_target_flags'],residual_maximum=max(loaded['permuted_rhs']))
    save(folder/'result.json',summary)
    tree=xml.Element('testsuite',name='one_saved809_assessment',tests='1',failures='0',errors='0',skipped='1' if summary['status']=='UNRESOLVED' else '0')
    node=xml.SubElement(tree,'testcase',name='unchanged_saved809_signed_block_bound')
    if summary['status']=='UNRESOLVED':xml.SubElement(node,'skipped',message='UNRESOLVED is no preservation claim').text=summary.get('refusal','q>=1')
    xml.ElementTree(tree).write(folder/'junit.xml',encoding='utf-8',xml_declaration=True)
    print(json.dumps({k:summary.get(k) for k in ('status','q_upper','refusal','phase','operations_used','final_runtime_contract_passed')},allow_nan=False))
    return 0 if valid else 1


def run():
    from scripts._b3_e4_f03_local_scientific_supervisor import supervise, SupervisorLimits
    OUT.mkdir(parents=True, exist_ok=True)
    ledger_path = OUT/'ledger.json'
    if ledger_path.exists():
        ledger = json.loads(ledger_path.read_text())
        if ledger['status'] != 'ACTIVE': raise RuntimeError('closed fresh ledger cannot be reused')
        if ledger['attempts']: raise RuntimeError('one actual saved809 assessment only; no retry')
    else:
        ledger = {'authority': 'root adopted ONE same saved809 assessment; fresh DEVELOPMENT180s with60reserve',
                  'allowance_seconds': 180., 'final_reserve_seconds': 60., 'used_seconds': 0.,
                  'status': 'ACTIVE', 'attempts': []}
    remaining = 180.-ledger['used_seconds']
    seconds = min(90., remaining-60.)
    if seconds <= 0: raise RuntimeError('no permitted process budget remains')
    attempt = OUT/f'attempt-{len(ledger["attempts"])+1:02d}'
    attempt.mkdir(exist_ok=False)
    environment = dict(os.environ); environment.update(ENV)
    environment['PYTHONPATH'] = os.pathsep.join((str(ROOT/'src'), str(ROOT), str(ROOT/'tests')))
    command = [sys.executable, '-u', str(Path(__file__).resolve()), '--child', str(attempt)]
    input_folder,expected,checks=trusted_inputs()
    from scripts.r8_f03_block_comparison_dev import CAPS
    caps = dict(CAPS)
    caps.update(process_seconds=seconds, process_tree_rss_bytes=2*1024**3,
                numerical_concurrency=1, final_reserve_seconds=60.)
    binding = {'command': command, 'cwd': str(ROOT), 'environment': {k: environment[k] for k in (*ENV, 'PYTHONPATH')},
               'sources': {p: sha(ROOT/p) for p in SOURCES}, 'caps': caps,
               'inputs': {'scope': 'one unchanged saved809 bound-only assessment','width':18,'expected_hashes':expected,'validated_hashes':checks,'factorization':False,'source_reconstruction':False},
               'limits': {'process_seconds': seconds, 'process_tree_rss_bytes': 2*1024**3},
               'remaining_before_seconds': remaining, 'qualification': False}
    binding['candidate_input_identity_sha256'] = hashlib.sha256(json.dumps(binding, sort_keys=True).encode()).hexdigest()
    save(attempt/'binding.json', binding)
    for relative, expected in binding['sources'].items():
        source = ROOT/relative
        if sha(source) != expected: raise RuntimeError('source changed before launch')
        target = attempt/'source'/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    item = {'path': str(attempt), 'status': 'RUNNING'}; ledger['attempts'].append(item); save(ledger_path, ledger)
    with (attempt/'stdout.txt').open('w') as stdout, (attempt/'stderr.txt').open('w') as stderr:
        receipt = supervise(command, cwd=ROOT, environment=environment, stdout=stdout, stderr=stderr,
                            limits=SupervisorLimits(seconds, 2*1024**3, .05))
    record = asdict(receipt); save(attempt/'process-tree-receipt.json', record)
    ledger['used_seconds'] += receipt.elapsed_seconds
    item.update(status=receipt.reason, exit_code=receipt.exit_code, process_wall_seconds=receipt.elapsed_seconds)
    ledger['remaining_seconds'] = 180.-ledger['used_seconds']
    ledger['status'] = 'CLOSED'
    ledger['discarded_unused_seconds'] = ledger['remaining_seconds']
    save(ledger_path, ledger)
    print(json.dumps({'attempt': str(attempt), 'reason': receipt.reason, 'exit_code': receipt.exit_code,
                      'wall_seconds': receipt.elapsed_seconds, 'used_seconds': ledger['used_seconds'],
                      'remaining_seconds': ledger['remaining_seconds']}))
    return 0 if receipt.reason == 'completed' and receipt.exit_code == 0 else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--child', type=Path)
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    if args.child: sys.exit(child(args.child))
    if args.run: sys.exit(run())
    parser.error('explicit --run development check or owned --child required')
