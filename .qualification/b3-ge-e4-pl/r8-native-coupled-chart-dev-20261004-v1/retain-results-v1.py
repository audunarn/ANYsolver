from pathlib import Path
import hashlib, json, subprocess

root = Path(__file__).resolve().parent
repo = root.parents[2]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
test = repo/'tests/test_stiffened_shell_native_plastic_chart.py'
assert test.read_bytes() == (root/'test-v3.py').read_bytes()
for name,path in (
    ('active','docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md'),
    ('goal','docs/agent_plans/B3_GE_E4_PL_REVISION_8_GOAL.md'),
    ('plan','docs/agent_plans/B3_GE_E4_PL_REVISION_8_PLAN.md'),
    ('report','docs/agent_plans/development/r8-distributing-reference-linear-20261004/results.md'),
    ('matrix','docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md')):
    (root/(name+'-before-final-v1.bin')).open('xb').write((repo/path).read_bytes())
head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
assert head.startswith('af4059a9')
old = subprocess.check_output(['git','show','HEAD:tests/test_stiffened_shell_native_plastic_chart.py'],cwd=repo)
(root/'regression-before-v1.py').open('xb').write(old)
test.write_bytes(old)
assert test.read_bytes() == old
runs = {version:json.loads((root/('installed-'+version)/'execution.json').read_text()) for version in ('v1','v2')}
diagnosis = json.loads((root/'diagnose-prefix-v2.json').read_text())
for run in runs.values():
    assert run['exit_code'] == 1 and run['sampled_peak_tree_bytes'] < 2*1024**3
assert diagnosis['status'] == 'PASS'
result = dict(source_parent=head,product_changed=False,
    ordinary_regression_restored_exactly=True,regression_sha256=sha(test),
    failed_candidate_retained_as='test-v3.py',
    inactive_shell_v1=dict(status='FAILED_COVERAGE',accepted_positions=[.125,.5,.75,1.],
        explanation='Shell alpha remained zero; fibre activity alone cannot establish simultaneous transport',
        execution=runs['v1']),
    active_shell_v2=dict(status='FAILED_CONTINUATION',accepted_positions=[.125,.3125,.359375,.3828125],
        explanation='Shell J2 active, fibres not yet plastic; cutback limit after finite mixed backtrack exhaustion',
        execution=runs['v2']),
    saved_prefix_directional_check=diagnosis,
    outcome='Simultaneous loaded shell J2/fibre chart transport remains OPEN. One saved-prefix direction has no observed tangent mismatch. No limit-point or formulation-failure claim; no further curve/load/budget campaign.',
    next_action='Design the smallest explicitly selected point zero-load normalization with physical scales and legacy/restart compatibility; do not alter criteria or defaults silently.')
(root/'results-v1.json').open('x').write(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(regression_restored=True,failures_retained=2,diagnostic=diagnosis['status'])))
