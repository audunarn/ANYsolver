"""Diagnose the failed bound, never accept an actual kernel with zero shift."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from threadpoolctl import threadpool_info
from scripts import r8_bl5_sparse_envelope_kernel_dev as family
from scripts import r8_bl5_sparse_kernel_saved_dev as bound
from scripts.r8_bl5_sparse_kernel_interval_dev import IntervalBudget,certify_decimal_lower
ROOT=Path(__file__).resolve().parent
case=ROOT/'ns16_b8/kernel-v1.json';pre=json.loads(case.read_text())
assert pre['status']=='HOLD_MECHANICAL_KERNEL' and pre['fixture_case']=='ns16_b8'
archive=case.with_suffix('.npz');assert family.sha(archive)==pre['arrays_sha256']
assert all(p['num_threads']==1 for p in threadpool_info())
with np.load(archive,allow_pickle=False) as data:
 a=bound.saved_csr(data,'A_representative',sparse_budget=family.GRAPH_BUDGET)
 pattern=bound.saved_csr(data,'complete_pattern',sparse_budget=family.GRAPH_BUDGET)
 order=data['permutation'].astype(int).tolist()
proof=certify_decimal_lower(a,pattern,order,shift=0.,budget=IntervalBudget(**pre['budgets']['proof']))
pivlo,pivhi=proof.pop('pivot_lower'),proof.pop('pivot_upper')
out=ROOT/'ns16_b8/representative-only-v1.json';assert not out.exists()
np.savez_compressed(out.with_suffix('.npz'),pivot_lower=pivlo,pivot_upper=pivhi)
record=dict(identity='UNSHIFTED_VERIFICATION_REPRESENTATIVE_DIAGNOSTIC_ONLY_V1',
 source_sha256=family.sha(__file__),predecessor_json_sha256=family.sha(case),
 predecessor_arrays_sha256=family.sha(archive),actual_mechanical_kernel_claim=False,
 original_error_upper=pre['kernel_error_upper'],original_required_shift=pre['fixed_shift'],
 arrays_sha256=family.sha(out.with_suffix('.npz')),proof=proof,
 limitation='Zero shift diagnoses representative only; not an epsilon reduction, acceptance or exact mechanical-kernel proof.')
with out.open('x') as handle:json.dump(record,handle,indent=2,allow_nan=False)
print(json.dumps(dict(status=proof['status'],completed_pivots=proof['completed_pivots'],actual_kernel_claim=False)))
