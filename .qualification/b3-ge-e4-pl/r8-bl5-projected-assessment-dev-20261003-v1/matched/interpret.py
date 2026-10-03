from pathlib import Path
import hashlib,json
import numpy as np
from scipy import sparse
from threadpoolctl import threadpool_info
ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'r8-bl5-affine-flexible-v1'
ASSESS=ROOT.parent/'r8-bl5-projected-integration-v1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def matrix(path,prefix):
 with np.load(path,allow_pickle=False) as z:
  return sparse.csr_matrix((z[prefix+'_data'],z[prefix+'_indices'],z[prefix+'_indptr']),shape=tuple(z[prefix+'_shape']))
oldK=matrix(OLD/'native/operators.npz','K');newK=matrix(ROOT/'native/operators.npz','K')
dk=oldK-newK
assert oldK.shape==newK.shape and np.max(np.abs(dk.data),initial=0.)==0.
predC=matrix(ASSESS/'mixed.npz','C');newC=matrix(ROOT/'native/operators.npz','C')
ce=float(sparse.linalg.norm(predC-newC)/max(1.,sparse.linalg.norm(newC)));assert ce<=1e-12
report={}
for case in ('fy','mx','mz'):
 prior=json.loads((OLD/'native'/case/'comparison.json').read_text())
 current=json.loads((ROOT/'native'/case/'comparison.json').read_text())
 ea=json.loads((ROOT/'external'/case/'recovered-actions.json').read_text())
 assert ea['basis']=='discontinuous_p1_cell_average'
 for p in ('summary.json','inputs.json'):
  assert json.loads((ROOT/'external'/case/p).read_text())['basis']==ea['basis']
 with np.load(ROOT/'native'/case/'raw-state.npz',allow_pickle=False) as a,np.load(ASSESS/'mixed.npz',allow_pickle=False) as b:
  q=a['q'];q2=b[case+'_direct_q'];parity=float(np.linalg.norm(q-q2)/max(np.linalg.norm(q),1e-30));assert parity<=1e-10
 report[case]=dict(old_unmodified_work_difference_percent=100*prior['work_relative_signed'],
  projected_work_difference_percent=100*current['work_relative_signed'],
  old_unmodified_fixed_region_difference=prior['fixed_region_difference'],
  projected_fixed_region_difference=current['fixed_region_difference'],
  old_unmodified_beam_ground_difference=prior['beam_ground_difference'],
  projected_beam_ground_difference=current['beam_ground_difference'],
  projected_fields=current['fields'],installed_vs_saved_general_q_relative=parity,
  previous_comparison_sha256=sha(OLD/'native'/case/'comparison.json'),current_comparison_sha256=sha(ROOT/'native'/case/'comparison.json'))
pools=threadpool_info();assert all(p['num_threads']==1 for p in pools)
result=dict(status='COMPLETED_DEVELOPMENT_ONLY',K_exact_difference_zero=True,C_projected_oracle_relative=ce,
 scope='Same native virgin K/geometry/load, distinct density action on both native and matched reference. Not mechanical equivalence or convergence/qualification.',
 source_sha256=sha(__file__),pools=pools,cases=report)
(ROOT/'combined-interpretation.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps(dict(K_exact_difference_zero=True,C_projected_oracle_relative=ce,cases={k:[v['old_unmodified_work_difference_percent'],v['projected_work_difference_percent'],v['installed_vs_saved_general_q_relative']] for k,v in report.items()})))
