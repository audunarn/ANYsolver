"""Audit retained evidence without a new factorization or proof attempt."""
from pathlib import Path
import hashlib,json
import numpy as np

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[3]
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
load=lambda path:json.loads(path.read_text())
bindings=load(ROOT/'bindings-v1.json')
result=load(ROOT/'kernel-v1.json')
execution=load(ROOT/'case-v1/execution.json')
assert all(sha(REPO/p)==h for p,h in {**bindings['sources'],**bindings['inputs']}.items())
assert sha(ROOT/'probe-v1.py')==bindings['driver_sha256']
assert sha(ROOT/'run-v2.py')==bindings['wrapper_sha256']
assert sha(ROOT/'kernel-v1.npz')==result['arrays_sha256']
assert result['stage']=='TERMINAL' and result['status']=='HOLD_MECHANICAL_KERNEL'
assert result['physical_kernel_lower_bound'] is None
assert result['formal_f03_authority_consumed'] is False
assert result['fixed_shift']==result['original_fixed_shift']
assert result['producer_shift']==result['original_producer_shift']
assert result['epsilon']==result['original_epsilon']
assert result['graph_metric_upper']==result['original_graph_metric']
proof=result['gram_margin_proof']
assert proof['status']=='HOLD_GRAM_MARGIN' and proof['hold_kind']=='RESOURCE_REFUSAL'
assert proof['workspace_estimate_bytes']>result['budgets']['max_workspace_bytes']==2*1024**3
assert 'rho_upper' not in proof and 'margin_lower' not in proof and proof['positive'] is False
assert execution['status']=='completed' and execution['exit_code']==0
assert execution['elapsed_seconds']<600 and execution['sampled_peak_tree_bytes']<2*1024**3
assert execution['environment']['NUMBA_DISABLE_JIT']=='1'
assert all(p['num_threads']==1 for p in result['effective_pools'])
with np.load(ROOT/'kernel-v1.npz',allow_pickle=False) as data:
    for prefix in ('producer_L','candidate_F'):
        assert all(prefix+'_'+name in data.files for name in ('shape','data','indices','indptr'))
        assert data[prefix+'_shape'].tolist()==[6257,6257]
        assert np.isfinite(data[prefix+'_data']).all()
    assert np.array_equal(data['producer_perm_r'],data['expected_perm_r'])
    assert np.array_equal(data['producer_perm_c'],data['expected_perm_c'])
    assert np.array_equal(data['producer_diagonal_positive_part'],np.maximum(data['producer_diagonal'],0.))
    assert int((data['producer_diagonal']<0.).sum())==2
assert not (ROOT.parent/'envelope-gram/stage-64-v1.json').exists()
audit=dict(status='PASS_SAVED_EVIDENCE_AUDIT',no_numerical_reexecution=True,
    source_bindings=12,input_bindings=4,complete_producer_and_candidate_retained=True,
    original_target_unchanged=True,resource_refusal_before_residual=True,
    no_negative_mode_conclusion=True,fine_stage_not_started=True,
    method_attempt_closed=True,formal_f03_authority_consumed=False)
(ROOT/'audit-v1.json').write_text(json.dumps(audit,indent=2)+'\n',newline='\n')
print(json.dumps(audit))
