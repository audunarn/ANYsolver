from pathlib import Path
import hashlib, json, shutil, subprocess

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
FEM = Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer')
runtime = json.loads((ROOT / 'installed-runtime-v1.json').read_text())
execution = json.loads((ROOT / 'installed-v1/execution.json').read_text())
assert runtime['exit_code'] == 0 and execution['status'] == 'completed'
assert runtime['example']['status'] == 'EXPERIMENTAL_NOT_QUALIFIED'
assert '226 passed' in (ROOT / 'installed-v1/stdout.log').read_text()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
solver_files = (
    'src/anysolver/_stiffened_shell_ge_experimental.py',
    'src/anysolver/_stiffened_shell_ge_finite_experimental.py',
    'src/anysolver/_stiffened_shell_ge_checkpoint_binary.py',
    'src/anysolver/stiffened_shell.py',
    'tests/test_stiffened_shell_distributing_cyclic.py',
    'docs/stiffened_shell_distributing_material_development.md')
fem_files = (
    'src/anyfem/solve/stiffened_shell.py',
    'src/anyfem/solve/stiffened_shell_ge_distributing_material.py',
    'tests/test_stiffened_shell_ge_distributing_cyclic_consumer.py',
    'examples/stiffened_shell_ge_distributing_cyclic_consumer.py')
bindings = {}
for label, repo, names in (('solver', REPO, solver_files), ('fem', FEM, fem_files)):
    for name in names:
        target = ROOT / 'source-v1' / label / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo / name, target)
        bindings[label + '/' + name] = sha(target)
bindings.update(artifacts=runtime['artifacts'], solver_source_parent='f9f45f01',
    consumer_source_parent='aaccbaa', scope='ordinary integrated development evidence, not qualification')
(ROOT / 'source-bindings-v1.json').open('x').write(json.dumps(bindings, indent=2) + '\n')
review = '''# Supporting cyclic slice review, 4 October 2026

OpenAI Read reviewer finite_material_consumer did not implement these changes,
execute tests, edit files or perform Git operations. This is supporting review,
not different-family scientific acceptance. Optional lower-tier reviewers remain
unavailable/exhausted; no repeat probes were made.

Closed findings: historical coupled checkpoint classification was omitted from
shell-material reconstruction and restored; cyclic consumer admission still used
the historical monotone token and now has exact selected-policy pairing; cyclic
factory now checks fixed-only increments, model-bound zero normalization and no
adaptive backtrack admission. Canonically re-encoded changed zero-pattern
checkpoint rejects atomically. Reviewer found no further concrete defect in
accepted-history/restart/ownership semantics or the public persistence example.

Reference action arrays are compiled and owned once, identity-bound, with nonzero
representable free-coordinate work. Actual zero-load force remains zero. Existing
nonzero normalization, equilibrium/compatibility tolerances and constitutive laws
are unchanged. Cyclic schema/kind/policy are separate; historical defaults retain
their admission and identity. Signed adaptive/chart/staged requests are rejected.
'''
(ROOT / 'review-v1.md').open('x').write(review)
(ROOT / 'failures-v1.md').open('x').write('''# Retained development failures

Sourcev1:3FAIL4.84s. Owned definition reconstruction dropped the new reference
actions; fixed the forwarding seam. Full stdout/runtime/resource records retained.
Sourcev2:2FAIL1PASS22.89s. Actual16-step histories completed; test wrongly demanded
plastic-strain sign reversal inside an expanded isotropic yield surface. Corrected
the assertion to physical resultant reversal and nondecreasing accumulated state;
no material law or tolerance changed. Logs/runtime records retained.
Sourcev3:3PASS37.08s. Integratedsourcev4:57PASS111.34s, whole113.15s/sample207568896B.
Current installed solver/consumer:226PASS199.83s; public example completes.
Sourcev4 precedes two metadata-only corrections (fixed-only adaptive capability
and generic checkpoint error wording); installed verification covers final bytes.
Previous fixed1.01 and adaptive1.01 incompletion remain in their original evidence.
No failure was erased, no scientific criterion or run budget was enlarged.
''')
report = REPO / 'docs/agent_plans/development/r8-distributing-reference-linear-20261004/results.md'
matrix = REPO / 'docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md'
active = REPO / 'docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md'
for name, path in (('report-before-v1.bin', report), ('matrix-before-v1.bin', matrix),
                   ('active-before-v1.bin', active)):
    (ROOT / name).open('xb').write(path.read_bytes())
section = '''

## Fixed cyclic distributing material workflow, 4 October 2026

IMPLEMENTED_NOT_QUALIFIED. Explicit generalized/coupled-Q4-J2 cyclic policies
admit finite signed changed fixed-step factors, including unload to zero. The
definition owns explicit reference actions, compiled once and identity-bound.
Zero external force remains exactly zero; its norm uses the model-owned unit
pattern only. Nonzero normalization,1e-8 equilibrium/1e-9 compatibility, local
laws and24Newton/16backtrack ceilings remain. Historical monotone/default/adaptive
contracts are unchanged. Cyclic adaptive/chart/staged/external routes reject.

Actual16-factor histories pass for both material families. Tests check active
initial plasticity, monotone accumulated states, beam station incremental
dissipation, resultant reversal, zero-state exact restart, cancellation at-.5,
same-path resumed byte parity, mutable input isolation and canonically re-encoded
pattern tampering rejected before publication. Force reversal inside an expanded
isotropic yield surface does not prove reverse plastic flow; none is claimed.

ANYfem owns/persists actions through existing material input and Project routes.
New cyclic admission token matches selected policy; old records remain monotone.
Factory validates fixed-only and immutable-zero-norm semantics. Installed226PASS
199.83s; example19.85s; whole222.28s/sample232914944B. Effective affinity/pools1,
JIToff; all imported package bytes match the two isolated wheel sources. Public
coupled16-step save/reopen/zero-restart example has exact final continuation bytes,
eq1.33704438e-10/gap7.54718882e-18 and active states in both domains.
Solverwheel6cf4650208ac3660e1c919b9a136a974b1dc22cb3666cbb45a3d9124168e3316.
Consumerwheel6831ab5d375642ba57ed07748c5a847a566705ea80c0bdf7ca8bd3b736be1f10.

Supporting OpenAI findings are closed; different-family scientific acceptance
and aggregate material/attachment/line/G0/G2/G3/capacity/release remain open.
Previous1.01 exhaustion and2.838825% small-Fy-pitch discrepancy remain. No automatic
continuation/refinement, formalF03 consumption, publication or main merge.
Raw .qualification/b3-ge-e4-pl/r8-distributing-cyclic-dev-20261004-v1 preserves
failed checks, actual artifacts/imports/resources, full logs, public outputs,
source bindings and review. Historical report/matrix/note bytes are retained.
'''
with report.open('ab') as out:
    out.write(section.encode('ascii'))
with matrix.open('ab') as out:
    out.write(('''

Finite distributing cyclic material,4 October: IMPLEMENTED_NOT_QUALIFIED.
Separate generalized/coupled policies own reference actions and zero normalization;
fixed load/unload/zero/signed reversal, cancellation and exact-path restart pass.
Installed solver/consumer226PASS plus16-step coupled Project/public example.
Physical initial yielding is observed; reverse plastic flow is not claimed.
Historical monotone/adaptive contracts and failed1.01 continuation unchanged.
No aggregate G3/F04/line/external/independent/release closure.
[Evidence](development/r8-distributing-reference-linear-20261004/results.md).
''').encode('ascii'))
fem_raw = FEM / '.qualification/stiffened-shell/r8-ge-distributing-cyclic-consumer-dev-20261004-v1'
fem_raw.mkdir(parents=True)
for name in ('artifact-v1.json','installed-runtime-v1.json','review-v1.md','failures-v1.md',
             'source-bindings-v1.json','installed-v1/stdout.log','installed-v1/execution.json',
             'example-v1/observations.json'):
    target = fem_raw / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / name, target)
for name in fem_files:
    target = fem_raw / 'source-v1' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(FEM / name, target)
doc = FEM / 'docs/development/r8-ge-distributing-cyclic-consumer-20261004.md'
doc.open('x').write('''# Experimental cyclic material consumer

Explicit generalized/coupled cyclic policies preserve the existing material input
schema while selecting fixed_signed_zero_nodal_translation_force_history_only.
Historical policies retain monotone_nodal_translation_force_only. Policy/admission
mismatches and missing fixed-only/model-bound-zero normalization capabilities reject.
Owned applied/reference actions match exactly; NumPy inputs are framed before
comparison. Case/Project roundtrips preserve the selected policy and owned loads.

The runnable examples/stiffened_shell_ge_distributing_cyclic_consumer.py completes
initial simultaneous yielding, zero-force restart and signed16-step history through
installed public packages; resumed final checkpoint matches the same-path oracle.
Combined installed226 checks pass199.83s; example19.85s. Detailed imported bytes,
wheel identities, resources, failures and review are retained at
.qualification/stiffened-shell/r8-ge-distributing-cyclic-consumer-dev-20261004-v1.

Solverwheel6cf4650208ac3660e1c919b9a136a974b1dc22cb3666cbb45a3d9124168e3316.
Consumerwheel6831ab5d375642ba57ed07748c5a847a566705ea80c0bdf7ca8bd3b736be1f10.
Supporting OpenAI review findings closed. This is development evidence, not full
material/connection qualification, different-family acceptance or release.
''')
print('Recorded installed cyclic slice; historical report and matrix only appended.')
