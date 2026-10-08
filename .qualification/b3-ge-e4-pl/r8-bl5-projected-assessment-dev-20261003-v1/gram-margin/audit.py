"""Scalar/source/evidence adjudication only; never reruns the numerical case."""
from pathlib import Path
import hashlib
import json

import numpy as np
from scripts.r8_bl5_sparse_kernel_interval_dev import down, up

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
p = json.loads((ROOT/'gram-v1.json').read_text())
proof = p['gram_margin_proof']
execution = json.loads((ROOT/'ns16_b8-v1/execution.json').read_text())
pre = REPO/'.qualification/b3-ge-e4-pl/r8-bl5-projected-assessment-dev-20261003-v1/sparse-family/ns16_b8/incidence-v1.json'
old = json.loads(pre.read_text())
checks = dict(
    original_case=sha(pre)==p['predecessor_json_sha256'],
    original_arrays=sha(pre.with_suffix('.npz'))==p['predecessor_arrays_sha256'],
    arrays_bound=sha(ROOT/'gram-v1.npz')==p['arrays_sha256'],
    exact_source=sha(ROOT/'probe-v1.py')==p['source_sha256'],
    dependencies=all(sha(REPO/'scripts'/name)==expected for name,expected in p['dependencies'].items()),
    original_targets=all(p[key]==old[oldkey] for key,oldkey in (
        ('epsilon','kernel_error_upper'),('fixed_shift','fixed_shift'),('graph_metric_upper','graph_metric_upper'))),
    fixed_extra_shift=p['producer_shift']==float(up(p['fixed_shift']+float(up(2*p['saved_rho_upper'])))),
    directed_gram_margin=proof['margin_lower']==float(down(float(down(p['producer_shift']-p['fixed_shift']))-proof['rho_upper']))>0,
    original_physical_floor=p['physical_kernel_lower_bound']==float(down(float(down(p['fixed_shift']-p['epsilon']))/p['graph_metric_upper']))>0,
    positive_complete_target=proof['positive'] and proof['status']=='POSITIVE_FIXED_SHIFT_GRAM_MARGIN' and proof['order']==2745,
    terminal=p['stage']=='TERMINAL' and execution['status']=='completed' and execution['exit_code']==0,
    effective_pools=bool(p['effective_pools']) and all(pool['num_threads']==1 for pool in p['effective_pools']),
    process_resources=execution['elapsed_seconds']<600 and execution['sampled_peak_tree_bytes']<2*1024**3,
    formal_authority_unconsumed=p['formal_f03_authority_consumed'] is False,
    unchanged_supervisor=sha(ROOT/'supervisor-v1.py')==execution['supervisor_sha256'],
)
with np.load(ROOT/'gram-v1.npz', allow_pickle=False) as data:
    checks['complete_permutation']=np.array_equal(np.sort(data['permutation']),np.arange(2745))
    checks['finite_saved_arrays']=all(np.isfinite(data[name]).all() for name in data.files)
    inventory={name:{'shape':list(data[name].shape),'dtype':str(data[name].dtype)} for name in data.files}
report=dict(status='PASS' if all(checks.values()) else 'FAILED', checks={k:bool(v) for k,v in checks.items()},
    arrays=inventory, limitation='Scalar/provenance adjudication, not a second numerical run or qualification.')
(ROOT/'root-audit.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',newline='\n')
print(json.dumps({'status':report['status'],'checks':len(checks),'failures':[k for k,v in checks.items() if not v]}))
if not all(checks.values()):
    raise ValueError('saved evidence audit failed')
