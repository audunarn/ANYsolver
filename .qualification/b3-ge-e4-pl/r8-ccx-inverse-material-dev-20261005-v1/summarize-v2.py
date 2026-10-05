"""Compact raw-result inventory, not an acceptance adjudicator."""
from pathlib import Path
import json, hashlib
ROOT = Path(__file__).resolve().parent
FULL = ROOT/'inverse-response-v2'
read = lambda p: json.loads(p.read_text())
status = read(FULL/'status.json')
observed = read(FULL/'actual-observables.json')
comparison = read(FULL/'comparison.json')
thickness = read(FULL/'unload-thickness-diagnostic.json')
execution = read(ROOT/'full-v2/execution.json')
quantities = [q for r in comparison for q in r['quantities']]
summary = dict(status=status['status'], accepted_endpoints=len(observed),
    source_sha256=status['script_sha256'],
    actual_force_n=[r['actual_actuator_force_n'] for r in observed],
    max_normalized_response_difference=max(q['normalized_difference'] for q in quantities),
    max_normalized_response_difference_plus_print_bound=max(
        q['normalized_difference']+q['print_bound']/q['denominator'] for q in quantities),
    max_force_difference_n=max(abs(q['difference']) for q in quantities if q['quantity']=='measured_actuator_force'),
    max_stress_difference_pa=max(abs(q['difference']) for q in quantities if q['quantity'].startswith('sigma_')),
    max_actual_alpha_peeq_statistic_difference=max(abs(q['difference']) for r in comparison for q in r['actual_history_differences']),
    max_actual_peeq=max(l['actual_peeq'] for r in observed for l in r['actual_layers']),
    max_actual_szz_pa=max(abs(l['stress_pa'][2]) for r in observed for l in r['actual_layers'])
        if 'stress_pa' in observed[0]['actual_layers'][0] else None,
    balance_check_counts={state:sum(c['status']==state for r in observed for c in r['balance_checks'].values())
        for state in ('PASS', 'INSUFFICIENT_PRINT_PRECISION')},
    unload_thickness_pass_count=sum(r['status']=='PASS' for r in thickness),
    max_unload_thickness_residual=max(abs(r['residual']) for r in thickness),
    imposed_boundary_verified=status['imposed_boundary_verified'], imposed_strain_scored=False,
    history_acceptance=status['actual_history_acceptance'],
    uniform_stress_precision_insufficient=status['uniform_stress_precision_insufficient'],
    seconds=execution['elapsed_seconds'], sampled_peak_tree_bytes=execution['sampled_peak_tree_bytes'],
    sampled_numeric_or_unresolved_max=execution['sampled_numeric_or_unresolved_max'],
    original_force_case_completed=False, e04_closed=False, g4d_closed=False, qualified=False,
    raw_status_sha256=hashlib.sha256((FULL/'status.json').read_bytes()).hexdigest())
with (ROOT/'summary-v2.json').open('x') as handle:
    json.dump(summary, handle, indent=2)
print(json.dumps(summary))
