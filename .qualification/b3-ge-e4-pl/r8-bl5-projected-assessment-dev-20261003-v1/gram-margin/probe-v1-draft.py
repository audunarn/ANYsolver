"""Same frozen shifted work target, independently enclosed candidate factor."""
from pathlib import Path
import json,sys,time
import numpy as np
from scipy import sparse
from threadpoolctl import threadpool_info
from scripts import r8_bl5_sparse_envelope_kernel_dev as family
from scripts import r8_bl5_sparse_kernel_saved_dev as bound
from scripts.r8_bl5_sparse_gram_margin_dev import certify_gram_margin
from scripts.r8_bl5_sparse_kernel_interval_dev import down,up,IntervalBudget
def require(condition,message):
 if not condition:raise ValueError(message)
require(not sys.flags.optimize,'unoptimized explicitly guarded development execution required')
ROOT=Path(__file__).resolve().parent
GROUP=family.ROOT/'docs/agent_plans/development/r8-bl5-projected-assessment-20261003'
manifest=GROUP/'raw-manifest-v9.json'
require(family.sha(manifest)=='5af39a3e686138941bfc7ccd02cbba65f74a22c5b99de363a77f04c408ec96f8','immutable campaign manifest differs')
records={r['path']:r['sha256'] for r in json.loads(manifest.read_text())['files']}
case=family.RAW/'sparse-family/ns16_b8/incidence-v1.json';archive=case.with_suffix('.npz')
for p in (case,archive):require(family.sha(p)==records[p.relative_to(family.ROOT).as_posix()],'immutable target pair differs')
pre=json.loads(case.read_text());require(pre['status']=='HOLD_MECHANICAL_KERNEL' and pre['fixture_case']=='ns16_b8','saved case/status differs')
require(family.sha(archive)==pre['arrays_sha256'] and pre['stationary_bound']=='incidence','saved incidence binding differs')
require(np.isfinite([pre['fixed_shift'],pre['kernel_error_upper'],pre['graph_metric_upper']]).all() and pre['fixed_shift']==float(up(2*pre['kernel_error_upper'])) and pre['kernel_error_upper']>0 and pre['graph_metric_upper']>0,'fixed positive2epsilon and metric required')
require(family.sha(family.__file__)==pre['source_sha256'],'exact compatible caller source required')
for name in ('r8_bl5_sparse_kernel_saved_dev.py','r8_bl5_sparse_kernel_interval_dev.py','_b3_e4_f03_sparse_certificate.py'):
 require(family.sha(family.ROOT/'scripts'/name)==pre['dependencies'][name],'predecessor dependency source differs')
pools=threadpool_info();require(pools and all(p['num_threads']==1 for p in pools),'nonempty effective pools1 required')
require(not any(n.split('.')[0]=='anysolver' for n in sys.modules),'saved discriminator must be product-free')
BINDINGS={'.qualification/b3-ge-e4-pl/r8-bl5-projected-assessment-dev-20261003-v1/factor-residual/factor-v2.json': '44d556b375524756a6190d456e30b1475f526d8315e356b642c896d7812c723d', '.qualification/b3-ge-e4-pl/r8-bl5-projected-assessment-dev-20261003-v1/factor-residual/factor-v2.npz': '1b235bbd29925c9697f5fb8717e84d88a06dfc6d4c677030d66387adc0e22bf7', 'scripts/r8_bl5_sparse_gram_margin_dev.py': '8e087dae9e42d8d9f6e9a9de68594c7f457434570f85ae02ba73ae3bc1aeefbf', 'scripts/r8_bl5_sparse_factor_residual_dev.py': 'cd56272435d4df22de7a08ff27362faf453c35ac1f97f138976d1f3aa70359f1', 'docs/agent_plans/development/r8-bl5-projected-assessment-20261003/raw-manifest-v10.json': '11c78508848846ee6b51d2b2621154531ad081f34266ae8d788231185c547568'}
for name,expected in BINDINGS.items():require(family.sha(family.ROOT/name)==expected,'pinned extra-shift dependency differs')
old=family.RAW/'factor-residual/factor-v2.json'
oldproof=json.loads(old.read_text())
require(family.sha(old.with_suffix('.npz'))==oldproof['arrays_sha256'],'saved rho arrays differ')
oldmanifest=json.loads((GROUP/'raw-manifest-v10.json').read_text())
oldrecords={r['path']:r['sha256'] for r in oldmanifest['files']}
for p in (old,old.with_suffix('.npz')):require(family.sha(p)==oldrecords[p.relative_to(family.ROOT).as_posix()],'saved rho manifest differs')
rho_saved=oldproof['gram_margin_proof']['rho_upper']
require(oldproof['predecessor_arrays_sha256']==family.sha(archive) and oldproof['fixed_shift']==pre['fixed_shift'] and rho_saved==3.799961133131045e-11,'same frozen target and rho required')
tau=float(up(pre['fixed_shift']+float(up(2*rho_saved))))
started=time.monotonic();out=ROOT/'gram-v1.json';require(not out.exists() and not out.with_suffix('.npz').exists(),'fresh paired outputs required')
report=dict(identity='BL5_SAVED_FIXED_SHIFT_GRAM_MARGIN_DEV_V1',status='STARTED',formal_f03_authority_consumed=False,
 source_sha256=family.sha(__file__),predecessor_json_sha256=family.sha(case),predecessor_arrays_sha256=family.sha(archive),
 epsilon=pre['kernel_error_upper'],fixed_shift=pre['fixed_shift'],graph_metric_upper=pre['graph_metric_upper'],effective_pools=threadpool_info(),
 dependencies={n:family.sha(family.ROOT/'scripts'/n) for n in ('r8_bl5_sparse_gram_margin_dev.py','r8_bl5_sparse_factor_residual_dev.py','r8_bl5_sparse_kernel_saved_dev.py','r8_bl5_sparse_kernel_interval_dev.py','r8_bl5_sparse_envelope_kernel_dev.py','_b3_e4_f03_sparse_certificate.py')},
 limitation='Saved exact work-kernel only. No fullKSPD, nativebeta, uniform stability, physical qualification or release.')
arrays={}
def save(stage):
 report.update(stage=stage,elapsed_seconds=time.monotonic()-started)
 np.savez_compressed(out.with_suffix('.npz'),**arrays)
 report['arrays_sha256']=family.sha(out.with_suffix('.npz'))
 out.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
try:
 with np.load(archive,allow_pickle=False) as data:
  a=bound.saved_csr(data,'A_representative',sparse_budget=family.GRAPH_BUDGET)
  order=data['permutation'].astype(int).tolist()
 require(a.shape==(2745,2745) and len(order)==2745 and set(order)==set(range(2745)),'complete actual case order required')
 arrays['permutation']=np.array(order,dtype=np.int64)
 report.update(saved_rho_upper=rho_saved,producer_shift=tau,saved_rho_json_sha256=family.sha(old),design_sha256=family.sha(ROOT/'design.md'))
 bhat=a[order][:,order].tocsr();bhat.setdiag(bhat.diagonal()-tau)
 backend=sparse.linalg.splu(bhat.tocsc(),permc_spec='NATURAL',diag_pivot_thresh=0.,options={'SymmetricMode':True,'Equil':False})
 d=backend.U.diagonal().copy();arrays['producer_diagonal']=d
 arrays['producer_perm_r']=backend.perm_r.copy();arrays['producer_perm_c']=backend.perm_c.copy()
 report['resource_revision']='explicit2GiB workspace/process ceiling within approved8GiB, same mathematical inputs/criteria; v1guard refusal retained'
 report['producer']=dict(order=a.shape[0],L_nnz=backend.L.nnz,U_nnz=backend.U.nnz,
   positive_diagonal=bool(np.all(d>0) and np.isfinite(d).all()),sign_limitation='Producer signs are not a mechanical certificate.')
 if not report['producer']['positive_diagonal']:
  report['status']='HOLD_FACTOR_CANDIDATE_DIAGONAL';save('TERMINAL')
 else:
  f=sparse.csr_matrix(backend.L.multiply(np.sqrt(d)));f.sum_duplicates();f.sort_indices()
  family.store_sparse(arrays,'candidate_F',f);save('SAVED_CANDIDATE_FACTOR')
  del backend,bhat
  proof=certify_gram_margin(a,f,order,target_shift=pre['fixed_shift'],producer_shift=tau,budget=IntervalBudget(**{**pre['budgets']['proof'],'max_workspace_bytes':2*1024**3}))
  for name,value in list(proof.items()):
   if isinstance(value,np.ndarray):arrays['proof_'+name]=proof.pop(name)
  report['gram_margin_proof']=proof
  margin=float(down(down(pre['fixed_shift']-pre['kernel_error_upper'])/pre['graph_metric_upper']))
  passed=proof['status']=='POSITIVE_FIXED_SHIFT_GRAM_MARGIN' and proof['positive'] and proof['margin_lower']>0 and np.isfinite(margin) and margin>0
  report['status']='POSITIVE_SAVED_MECHANICAL_KERNEL_DEVELOPMENT_ONLY' if passed else 'HOLD_MECHANICAL_KERNEL'
  report['physical_kernel_lower_bound']=margin if passed else None
  save('TERMINAL')
 print(json.dumps({k:report.get(k) for k in ('status','physical_kernel_lower_bound','elapsed_seconds')}))
except BaseException as error:
 report.update(status='FAILED_DISCRIMINATOR',failure=dict(type=type(error).__name__,message=str(error)))
 try:save('FAILED')
 except BaseException as recording_error:error.add_note('Recording also failed: '+repr(recording_error))
 raise
