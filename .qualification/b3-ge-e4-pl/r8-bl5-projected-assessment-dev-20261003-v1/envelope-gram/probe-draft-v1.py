"""One fixed fresh saved-envelope preparation/certificate; no product imports."""
from pathlib import Path
from dataclasses import asdict
import json
import os
import sys
import time

import numpy as np
from threadpoolctl import threadpool_info
from scripts import r8_bl5_envelope_gram_dev as assessment
from scripts.r8_bl5_projected_envelope_norm_dev import case_from_id

ROOT = Path(__file__).resolve().parent
REPO = assessment.ROOT
require = assessment.require
require(not sys.flags.optimize, 'unoptimized execution required')
bindings = json.loads((ROOT/'bindings-v1.json').read_text())
for name, expected in bindings['sources'].items():
    require(assessment.sha(REPO/name)==expected, 'pinned source differs: '+name)
require(not any(name.split('.')[0]=='anysolver' for name in sys.modules), 'saved-data only required')
require(threadpool_info() and all(p['num_threads']==1 for p in threadpool_info()), 'effective pools1 required')
require(os.environ.get('NUMBA_DISABLE_JIT')=='1', 'JIT off required')
case = case_from_id('ns32_b2')
require(case.counts['kernel']==2801, 'frozen expected kernel2801 required')
owner = assessment.RAW/'envelope/owners'/case.fixture_case/'owner-v1'
prepared = ROOT/'prepared-v1.json'
output = ROOT/'kernel-v1.json'
require(not any(p.exists() for p in (prepared,prepared.with_suffix('.npz'),output,output.with_suffix('.npz'))), 'fresh paired outputs required')
started = time.monotonic()
report = dict(identity='BL5_FRESH_SAVED_KERNEL_GRAM_DISCRIMINATOR_DEV_V1',
    status='STARTED',fixture_case=case.fixture_case,source_sha256=assessment.sha(__file__),
    sources=bindings['sources'],design_sha256=assessment.sha(ROOT/'design.md'),
    formal_f03_authority_consumed=False,effective_pools=threadpool_info(),
    limitations='Finite saved mechanical kernel only; no law/space/physical or aggregate qualification.')
arrays = {}
def save(stage):
    report.update(stage=stage,elapsed_seconds=time.monotonic()-started)
    np.savez_compressed(output.with_suffix('.npz'),**arrays)
    report['arrays_sha256']=assessment.sha(output.with_suffix('.npz'))
    output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',newline='\n')
try:
    wheel = Path(os.environ['TEMP'])/'r8-bl5-projected-joint32-v2/dist/anysolver-0.4.7-py3-none-any.whl'
    site = wheel.parent.parent/'site'
    pre = assessment.prepare(case,owner,prepared,wheel=wheel,site=site)
    require(pre['status']=='PREPARED_MECHANICAL_KERNEL' and pre['kernel_order']==2801, 'complete preparation required')
    require(assessment.sha(prepared.with_suffix('.npz'))==pre['arrays_sha256'], 'prepared arrays differ')
    report.update(prepared_json_sha256=assessment.sha(prepared),prepared_arrays_sha256=pre['arrays_sha256'],
                  original_kernel_error_upper=pre['kernel_error_upper'],original_fixed_shift=pre['fixed_shift'],
                  graph_metric_upper=pre['graph_metric_upper'],budgets=asdict(assessment.PROOF_BUDGET))
    with np.load(prepared.with_suffix('.npz'),allow_pickle=False) as data:
        a=assessment.bound.saved_csr(data,'A_representative',sparse_budget=assessment.GRAPH_BUDGET)
    result, arrays = assessment.certify_target(a,epsilon=pre['kernel_error_upper'],metric=pre['graph_metric_upper'])
    require(result['fixed_shift']==pre['fixed_shift'], 'original target shift changed')
    report.update(result)
    save('TERMINAL')
    print(json.dumps({k:report.get(k) for k in ('status','physical_kernel_lower_bound','elapsed_seconds')}))
except BaseException as error:
    report.update(status='FAILED_FRESH_KERNEL_DISCRIMINATOR',failure=dict(type=type(error).__name__,message=str(error)))
    try:save('FAILED')
    except BaseException as recording_error:error.add_note('Recording also failed: '+repr(recording_error))
    raise
