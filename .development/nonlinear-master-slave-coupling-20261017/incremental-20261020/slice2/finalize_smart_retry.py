"""Record measured acceptance; does not run or alter solver checks."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

FOLDER = Path(__file__).resolve().parent
INC = FOLDER.parent
TASK = INC.parent
REPO = TASK.parents[1]
load = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
receipt = load(FOLDER / 'evidence/smart-retry-remaining-default-execution/receipt.json')
runtime = load(FOLDER / 'portable-runs/anysolver-portable-ci-qur39vy1/P01/runtime.json')
assert receipt['status'] == 'EXIT' and receipt['counts']['passed'] == 4
assert runtime['collected'] == 4 and runtime['failed'] == 0 and not runtime['errors']
assert runtime['jit_disabled'] and runtime['numba_threads'] == 1
assert all(p['num_threads'] == 1 for p in runtime['effective_pools'])
assert receipt['child_env']['ANYSOLVER_RUN_RETIRED_PROGRAMME_TESTS'] == '0'
assert load(FOLDER / 'smart-retry-v1/input_purity.json')['artifacts_unchanged']
prior = load(FOLDER / 'RETRY_DELIVERY.json')
for name in ('src/anysolver/nonlinear_static.py', 'src/anysolver/nonlinear_restart.py',
             'examples/beam_shell_coupling.py', 'tests/test_beam_shell_checkpoint_workflow.py'):
    assert sha(REPO / name) == prior['candidate_identity']['working_file_sha256'][name]
plugin = FOLDER / 'slice2_saved_reference.py'
block = b"        if name == 'selected_root':\n            assert Path(digest) == REPO / 'src'\n            continue\n"
initial = plugin.read_bytes().replace(block, b'')
failed = load(FOLDER / 'evidence/smart-retry-remaining-default/receipt.json')
expected = next(v for k, v in failed['identity_hashes'].items()
                if k.replace('\\', '/').endswith('/slice2_saved_reference.py'))
assert hashlib.sha256(initial).hexdigest() == expected
(FOLDER / 'smart-retry-v1/initial-plugin-failed-setup.py.txt').write_bytes(initial)
nodes = [s.strip() for s in (FOLDER / 'evidence/retry-collection-identities/stdout.txt').read_text().splitlines()
         if s.startswith('tests/') and '::' in s]
assert len(nodes) == len(set(nodes)) == 152
old_selection = load(FOLDER / 'portable-runs/anysolver-portable-ci-3vqp4u2n/P01/selection.json')
base = sum(n.partition('::')[0] in old_selection['targets'][:4] for n in nodes)
progress = [s for s in (FOLDER / 'evidence/retry-final-shared-regression-execution/stdout.txt').read_text().splitlines()
            if re.fullmatch(r'\.+', s)]
assert base == 58 and len(progress) == 1 and len(progress[0]) == 71
default = [n for n in nodes if n.startswith('tests/test_nonlinear_beam_shell_slice3_continuation.py::')]
assert len(default) == 17
assert default[13:] == load(FOLDER / 'portable-runs/anysolver-portable-ci-qur39vy1/P01/selection.json')['targets']
budget = load(FOLDER / 'budget.json')
remaining = budget['allowance_seconds'] - budget['used_seconds']
assert budget['allowance_seconds'] == 1800 and remaining >= 0
assert sha(TASK / 'budget.json') == prior['historical_budget_sha256']
assert sha(REPO / 'tests/test_nonlinear_beam_shell_slice3_director_continuation.py') == prior['director_failure_tests_sha256']
parent = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip()
identity = dict(integration_parent_commit=parent, working_file_sha256={
    n: sha(REPO / n) for n in prior['candidate_identity']['working_file_sha256']})
identity['candidate_identity_sha256'] = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
report = dict(status='ACCEPTED_REGISTERED_SOURCE_WORKFLOW', accepted_slice2=True,
    candidate_identity=identity, source_commit_locator='Git commit containing this receipt',
    verification_base_commit=prior['candidate_identity']['base_commit'],
    concurrent_contact_commit='59f41a324; separate contact static-path/reporting changes retained',
    terminal_pass_counts=dict(checkpoint_workflow=12, shared_and_compatibility=113,
        remaining_default_checks=4, preyield_in_initial_mixed_batch=10),
    default_regression_coverage=dict(retained_pass_progress_node_ids=default[:13],
        new_terminal_pass_node_ids=default[13:], original_combined_exit_status=124,
        original_combined_not_relabelled=True),
    unique_covered_identities=152, single_full_suite_pass_claim=False,
    fixture_reuse='smart-retry-v1/fixture_reuse.json',
    fixture_input_purity='smart-retry-v1/input_purity.json',
    final_attempt_process_wall_seconds=receipt['process_wall_seconds'], budget=budget,
    remaining_seconds=remaining, reserve='protected until final verification, then used for that purpose',
    historical_budget_unchanged=True, director_failure_tests_unchanged=True,
    scientific_gates_unchanged=True, physics_material_controls_tolerances_schema_converged_semantics_unchanged=True,
    installed_artifact_unchanged=True, push_or_release=False,
    preparation_helper_sha256={p.name: sha(p) for p in (plugin, FOLDER / 'verify_remaining.py')})
(FOLDER / 'SMART_RETRY_DELIVERY.json').write_text(json.dumps(report, indent=2) + '\n')
completion = load(INC / 'COMPLETION.json')
completion.update(status='DELIVERED_SOURCE_CHECKPOINT_WITH_PRIOR_PREYIELD_ARTIFACT', core_solver_edits_by_this_delivery=True)
completion['latest_slice2_retry'] = dict(status=report['status'], accepted=True,
    receipt='slice2/SMART_RETRY_DELIVERY.json', candidate_identity_sha256=identity['candidate_identity_sha256'])
completion['verification_reserves_remaining'] = dict(slice1=True, slice2='used for final verification as intended', slice3=True, historical=True)
(INC / 'COMPLETION.json').write_text(json.dumps(completion, indent=2) + '\n')
note = f'''
### Slice 2 accepted source workflow — 2026-10-20

All four unfinished original default checks passed unchanged: interpolated
restart/history comparison, rejected restart admission, cancelled resume/reuse,
and rejected-trial snapshot exclusion. Receipt:
`slice2/evidence/smart-retry-remaining-default-execution`: 4 collected, 4 passed,
zero failed; process wall {receipt['process_wall_seconds']!r} seconds. Terminal
runtime verifies selected-source imports, disabled JIT, one numerical thread,
no runtime errors and disabled retired-programme selection.

Only the prior COMPLETED interpolated uninterrupted comparison was cached: its
actual terminal arrays/status, 15 accepted snapshots, and recorded step/control/
load history. Step plastic maxima derive from original physical alpha arrays.
Source/test/input identities match; all original per-snapshot independent
equilibrium, constraint, reaction and material assertions ran again. Prefixes,
resumes, cancellation/reuse, refusal and rejected-state production solves ran
fresh. Retained input files stayed byte-identical. No failed-state recovery,
new restart format, reference fitting, tolerance or assertion change. The first
preparation attempt failed before any tests ran on a manifest metadata key;
its exact input and full logs remain preserved, charged {failed['process_wall_seconds']!r} s.

Acceptance combines 12 public checkpoint passes, 113 shared/compatibility passes,
the earlier 10 pre-yield passes, and 17 default regressions across the retained
13 pass-progress identities plus these 4 terminal passes. The 152-identity union
is recorded in `slice2/SMART_RETRY_DELIVERY.json`. The interrupted combined run
remains exit124; no successful full-suite claim. Scientific gates remain open;
all three director failures and their source hashes are unchanged.

Final independent Slice 2 ledger: {budget['used_seconds']!r}/1800 s used;
{remaining!r} s remain. The 300-second reserve was protected until this explicit
final-verification-only continuation, then used for its intended purpose.
No extension occurred. Historical numerical allowance/reserve remain unchanged.

The narrow checkpoint repair and executable S355 full/prefix/serialized-resume
source workflow are accepted. Candidate identity:
`{identity['candidate_identity_sha256']}`. The scoped Git commit containing this
record identifies the accepted source. Main advanced concurrently to separate
contact commit {parent}; those contact static-path/reporting changes are retained
and excluded from our ownership. Verified beam-shell runtime files are unchanged
from the passing candidate. The pinned installed Python 3.12 bundle remains
pre-yield only. No rebuild, push, publication, release or extra review here.
'''
with (TASK / 'HANDOVER.md').open('a', encoding='utf-8') as stream:
    stream.write(note)
(FOLDER / 'smart-retry-v1/RECORDING_ERROR.txt').write_text(
    'Metadata-only first finalizer used preflight key threadpools instead of terminal key effective_pools. '
    'It failed before writing acceptance records; corrected using the actual terminal runtime schema. '
    'No numerical process or budget change.\n')
print(json.dumps(dict(status=report['status'], remaining_seconds=remaining,
    candidate_identity_sha256=identity['candidate_identity_sha256'])))
