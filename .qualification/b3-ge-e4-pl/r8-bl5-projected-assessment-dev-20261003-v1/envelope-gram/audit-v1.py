"""Inspect retained results and bindings; no solve or certificate recomputation."""
from pathlib import Path
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path): return json.loads(path.read_text())
rows = []
cases = [ROOT] + sorted((ROOT/'campaign-v1').iterdir())
for folder in cases:
    result = load(folder/'kernel-v1.json')
    prepared = load(folder/'prepared-v1.json')
    run_folder = folder/('ns32_b2-v1' if folder==ROOT else 'run-v1')
    execution = load(run_folder/'execution.json')
    checks = {}
    checks['prepared_json'] = sha(folder/'prepared-v1.json') == result['prepared_json_sha256']
    checks['prepared_arrays'] = sha(folder/'prepared-v1.npz') == result['prepared_arrays_sha256'] == prepared['arrays_sha256']
    checks['result_arrays'] = sha(folder/'kernel-v1.npz') == result['arrays_sha256']
    checks['source_bindings'] = all(sha(REPO/p)==h for p,h in result['sources'].items())
    checks['original_epsilon'] = prepared['kernel_error_upper']==result['original_kernel_error_upper']==result['epsilon']
    checks['original_shift'] = prepared['fixed_shift']==result['original_fixed_shift']==result['fixed_shift']
    checks['original_metric'] = prepared['graph_metric_upper']==result['graph_metric_upper']
    checks['no_formal_authority'] = result['formal_f03_authority_consumed'] is False
    checks['resource_scope'] = execution['seconds_limit']==600 and execution['memory_limit_bytes']==2*1024**3 and execution['elapsed_seconds']<600 and execution['sampled_peak_tree_bytes']<2*1024**3
    checks['runtime_settings'] = execution['environment']['NUMBA_DISABLE_JIT']=='1' and all(p['num_threads']==1 for p in result['effective_pools'])
    checks['terminal_execution'] = execution['status']=='completed' and execution['exit_code']==0
    if result['status']=='POSITIVE_ENVELOPE_MECHANICAL_KERNEL_DEVELOPMENT_ONLY':
        proof=result['gram_margin_proof']
        checks['positive_gate']=proof['status']=='POSITIVE_FIXED_SHIFT_GRAM_MARGIN' and proof['positive'] and proof['margin_lower']>0 and result['physical_kernel_lower_bound']>0
        checks['unmodified_target']=proof['target_shift']==result['fixed_shift'] and proof['producer_shift']==result['producer_shift']
    else:
        checks['explicit_hold']=result['status']=='HOLD_MECHANICAL_KERNEL' and result['hold_kind']=='PRODUCER_DIAGONAL' and result['physical_kernel_lower_bound'] is None and 'gram_margin_proof' not in result
    assert all(checks.values()), (result['fixture_case'], checks)
    rows.append(dict(case=result['fixture_case'],status=result['status'],checks=checks,
        elapsed_seconds=execution['elapsed_seconds'],sampled_peak_tree_bytes=execution['sampled_peak_tree_bytes']))
assert len(rows)==11 and sum(r['status'].startswith('POSITIVE') for r in rows)==10
assert load(ROOT/'stage-16-v1.json')['complete'] is True
assert load(ROOT/'stage-32-v1.json')['complete'] is False
assert not (ROOT/'stage-64-v1.json').exists()
regional=load(ROOT/'regional-v1/regional-actions.json')
assert all(sha(REPO/p)==regional['input_sha256'][key] for key,p in regional['input_paths'].items())
assert sha(REPO/'scripts/r8_bl5_regional_action_dev.py')==regional['source_sha256']
report=dict(identity='BL5_SAVED_ENVELOPE_RESULTS_AUDIT_DEV_V1',no_numerical_reexecution=True,
    cases=rows,regional_input_bindings=8,positive_new_cases=10,producer_hold_cases=1,
    total_positive_with_previous=13,fine_stage_not_started=True,qualification_claim=False)
(ROOT/'audit-v1.json').write_text(json.dumps(report,indent=2)+'\n',newline='\n')
print(json.dumps({k:v for k,v in report.items() if k!='cases'}))
