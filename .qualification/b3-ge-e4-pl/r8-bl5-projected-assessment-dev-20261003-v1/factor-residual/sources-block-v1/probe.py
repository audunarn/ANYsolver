"""One fixed18 discriminator on the exact saved V2 factor, no owner solve."""
from pathlib import Path
import json,time,sys
import numpy as np
from threadpoolctl import threadpool_info
from scripts import r8_bl5_sparse_envelope_kernel_dev as family
from scripts.r8_bl5_sparse_kernel_saved_dev import saved_csr
from scripts.r8_bl5_sparse_factor_block_dev import certify_block_inverse
from scripts.r8_bl5_sparse_kernel_interval_dev import IntervalBudget,down

def require(value,message):
 if not value:raise ValueError(message)

ROOT=Path(__file__).resolve().parent
require(not sys.flags.optimize,'explicit unoptimized admission required')
source=family.ROOT/'scripts/r8_bl5_sparse_factor_block_dev.py'
require(family.sha(source)=='d57095c2699520c04425900bdfbf02c0d808beedee646e17d81bc713499bb437','reviewed fixed18 helper source required')
previous=ROOT/'factor-v2.json'; archive=previous.with_suffix('.npz')
require(family.sha(previous)=='44d556b375524756a6190d456e30b1475f526d8315e356b642c896d7812c723d','exact V2 report required')
require(family.sha(archive)=='1b235bbd29925c9697f5fb8717e84d88a06dfc6d4c677030d66387adc0e22bf7','exact V2 arrays required')
pre=json.loads(previous.read_text())
require(pre['arrays_sha256']==family.sha(archive) and pre['status']=='HOLD_MECHANICAL_KERNEL','complete frozen V2 HOLD pair required')
proof=pre['factor_residual_proof']
require(proof['status']=='HOLD_FACTOR_RESIDUAL' and proof['hold_kind']=='INSUFFICIENT_MARGIN','original residual proof required')
require(proof['order']==2745 and proof['rho_upper']>0 and np.isfinite(proof['rho_upper']),'finite frozen original FF.T residual required')
for name,digest in pre['dependencies'].items():
 require(family.sha(family.ROOT/'scripts'/name)==digest,'frozen dependency differs: '+name)
manifest=family.ROOT/'docs/agent_plans/development/r8-bl5-projected-assessment-20261003/raw-manifest-v9.json'
require(family.sha(manifest)=='5af39a3e686138941bfc7ccd02cbba65f74a22c5b99de363a77f04c408ec96f8','frozen parent campaign required')
pools=threadpool_info();require(pools and all(p['num_threads']==1 for p in pools),'nonempty effective pools1 required')
require(not any(n.split('.')[0]=='anysolver' for n in sys.modules),'saved proof must be product-free')
out=ROOT/'factor-v3.json';require(not out.exists() and not out.with_suffix('.npz').exists(),'new output pair required')
started=time.monotonic();arrays={}
report=dict(identity='BL5_SAVED_FIXED18_FACTOR_INVERSE_DISCRIMINATOR_DEV_V1',status='STARTED',formal_f03_authority_consumed=False,
 source_sha256=family.sha(__file__),helper_sha256=family.sha(source),predecessor_json_sha256=family.sha(previous),
 predecessor_arrays_sha256=family.sha(archive),epsilon=pre['epsilon'],fixed_shift=pre['fixed_shift'],
 graph_metric_upper=pre['graph_metric_upper'],original_rho_upper=proof['rho_upper'],effective_pools=pools,
 limitations='Exact saved work kernel only; no fullKSPD/nativebeta/uniform stability/physical qualification/release. Fixed18 only; no tuning campaign.')
def save(stage):
 report.update(stage=stage,elapsed_seconds=time.monotonic()-started)
 np.savez_compressed(out.with_suffix('.npz'),**arrays)
 report['arrays_sha256']=family.sha(out.with_suffix('.npz'))
 out.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
try:
 with np.load(archive,allow_pickle=False) as data:
  f=saved_csr(data,'candidate_F',sparse_budget=family.GRAPH_BUDGET)
  for name in ('candidate_F_data','candidate_F_indices','candidate_F_indptr','candidate_F_shape','permutation'):
   arrays[name]=data[name].copy()
 require(f.shape==(2745,2745),'same complete stored factor order required')
 report['original_factor_nnz']=f.nnz
 save('SAVED_EXACT_FACTOR')
 result=certify_block_inverse(f,budget=IntervalBudget(**proof['budget']),block_size=18)
 for name,value in list(result.items()):
  if isinstance(value,np.ndarray):arrays['block_'+name]=result.pop(name)
 report['block_inverse_proof']=result
 margin=None
 if result['status']=='FINITE_FACTOR_INVERSE_BOUND':
  margin=float(down(result['mu_lower']-proof['rho_upper']))
 report['factor_residual_margin_lower']=margin
 physical=float(down(down(pre['fixed_shift']-pre['epsilon'])/pre['graph_metric_upper']))
 passed=margin is not None and np.isfinite(margin) and margin>0 and np.isfinite(physical) and physical>0
 report['status']='POSITIVE_SAVED_MECHANICAL_KERNEL_DEVELOPMENT_ONLY' if passed else 'HOLD_MECHANICAL_KERNEL'
 report['physical_kernel_lower_bound']=physical if passed else None
 save('TERMINAL')
 print(json.dumps({k:report.get(k) for k in ('status','factor_residual_margin_lower','physical_kernel_lower_bound','elapsed_seconds')}))
except BaseException as error:
 report.update(status='FAILED_DISCRIMINATOR',failure=dict(type=type(error).__name__,message=str(error)))
 try:save('FAILED')
 except BaseException as recording_error:error.add_note('Recording also failed: '+repr(recording_error))
 raise
