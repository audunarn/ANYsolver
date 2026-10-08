"""One prospective replacement Gram producer on a hash-bound saved kernel."""
from pathlib import Path
from dataclasses import asdict
import hashlib
import json
import os
import sys
import time

import numpy as np
from threadpoolctl import threadpool_info
from scripts import r8_bl5_positive_part_gram_dev as assessment
from scripts import r8_bl5_envelope_gram_dev as prepared_helper

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[3]
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
bindings=json.loads((ROOT/'bindings-v1.json').read_text())
require=prepared_helper.require
require(not sys.flags.optimize,'unoptimized execution required')
require(not any(name.split('.')[0]=='anysolver' for name in sys.modules),'saved-data only required')
require(os.environ.get('NUMBA_DISABLE_JIT')=='1','JIT off required')
require(threadpool_info() and all(p['num_threads']==1 for p in threadpool_info()),'effective pools1 required')
for name,expected in {**bindings['sources'],**bindings['inputs']}.items():
    require(sha(REPO/name)==expected,'pinned input/source differs: '+name)
require(sha(ROOT/'design-v1.md')==bindings['design_sha256'],'design changed')
old_folder=ROOT.parent/'envelope-gram/campaign-v1/ns32_b8'
old=json.loads((old_folder/'kernel-v1.json').read_text())
pre=json.loads((old_folder/'prepared-v1.json').read_text())
require(old['status']=='HOLD_MECHANICAL_KERNEL' and old['hold_kind']=='PRODUCER_DIAGONAL','original HOLD required')
require(pre['status']=='PREPARED_MECHANICAL_KERNEL' and pre['kernel_error_upper']==old['epsilon'],'original error changed')
require(pre['fixed_shift']==old['fixed_shift'] and pre['graph_metric_upper']==old['graph_metric_upper'],'original target/metric changed')
output=ROOT/'kernel-v1.json'
require(not output.exists() and not output.with_suffix('.npz').exists(),'fresh paired outputs required')
started=time.monotonic()
report=dict(identity='BL5_ONE_POSITIVE_PART_GRAM_PRODUCER_DEV_V1',status='STARTED',
    fixture_case='ns32_b8',bindings=bindings,effective_pools=threadpool_info(),
    formal_f03_authority_consumed=False,qualification_claim=False,
    original_epsilon=pre['kernel_error_upper'],original_fixed_shift=pre['fixed_shift'],
    original_producer_shift=old['producer_shift'],original_graph_metric=pre['graph_metric_upper'],
    budgets=asdict(assessment.PROOF_BUDGET))
arrays={}
def save(stage):
    report.update(stage=stage,elapsed_seconds=time.monotonic()-started)
    np.savez_compressed(output.with_suffix('.npz'),**arrays)
    report['arrays_sha256']=sha(output.with_suffix('.npz'))
    output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',newline='\n')
try:
    with np.load(old_folder/'prepared-v1.npz',allow_pickle=False) as data:
        a=prepared_helper.bound.saved_csr(data,'A_representative',sparse_budget=prepared_helper.GRAPH_BUDGET)
    with np.load(old_folder/'kernel-v1.npz',allow_pickle=False) as data:
        row,column=data['producer_perm_r'].copy(),data['producer_perm_c'].copy()
    def checkpoint(stage,candidate,raw):
        global arrays
        arrays=raw
        report.update(candidate)
        save(stage)
    result,arrays=assessment.certify_target(a,epsilon=pre['kernel_error_upper'],
        metric=pre['graph_metric_upper'],expected_perm_r=row,expected_perm_c=column,checkpoint=checkpoint)
    require(result['fixed_shift']==old['fixed_shift'] and result['producer_shift']==old['producer_shift'],'fixed shifts changed')
    report.update(result)
    save('TERMINAL')
    print(json.dumps({k:report.get(k) for k in ('status','hold_kind','physical_kernel_lower_bound','elapsed_seconds')}))
except BaseException as error:
    report.update(status='FAILED_ONE_POSITIVE_PART_PRODUCER',physical_kernel_lower_bound=None,
        failure=dict(type=type(error).__name__,message=str(error)))
    try:save('FAILED')
    except BaseException as recording_error:error.add_note('Recording also failed: '+repr(recording_error))
    raise
