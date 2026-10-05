from pathlib import Path
import hashlib, json, shutil

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
binding = json.loads((ROOT / 'binding-v2.json').read_text())
comparison = json.loads((ROOT / 'comparison-v1.json').read_text())
assert comparison['all_six_measured_differences_below_one_percent']
for name, digest in binding['fixtures'].items():
    source = REPO / name
    assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
    target = ROOT / 'fixtures-v1' / name
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,target)
(ROOT / 'review-v1.md').open('x').write('''# Supporting Fy80 review

OpenAI Read reviewer affine_flexible_review did not implement, edit, import or
run this discriminator. No blocking defect or overclaim found. Geometry, hosts,
supports, pad and port match prior native80;419 installed Python files match the
original pinned b7 wheel. V2 changes ndarray serialization/output names only.
V1 failure, empty result and complete error/runtime evidence remain.

Measured six-pose differences<1%, pitch-.864137%, work-.030881% and zero reflection
residual are supported. Equilibrium4.61e-12/gap1.69e-21, unloaded-stub/physical
transfer controls and one factorization pass their existing development checks.
Native pitch40-to80 movement2.032% prevents a converged acceptance claim here.
Stopping this diagnostic slice and retaining the declared law for development
is supported. Different-family scientific and aggregate acceptance remain open.
''')
section = '''

## Executed native80 Fy component exit,4 October 2026

One new10N elevated-Fy RHS on the existing80x32 geometry and original pinned
installed b7ae7ca0 operator completes. Actual full pose now exists: all6 components
are within1% of binary solid; pitch-.864137%, direct work-.030881%, reflection
residual against saved native80 Mx exactly0 in binary64. Eq4.61227e-12/gap1.69407e-21;
unloaded-stub, physical transfer and root controls pass; one factorization.
Runtime96.21s/sample685281280B, pinned affinity1/entrypools1/JIToff.

V1 reached output writing but failed ndarray serialization; no numerical result
survived. V2 repairs the writer only and repeats the exact case. Both sources,
runtime/error/output files remain; v1 is FAILED, not an accepted scientific run.
No geometry/source/operator/load/tolerance/per-run-budget change was made.

Decision: retain declared mean/secant-director/curl law for development and STOP
this diagnostic slice. Do not automatically refine. Native pitch40-to80 movement
2.032385% still leaves converged1% acceptance open; measured pair agreement is
not an asymptotic bound, finite/material/weld/bonded-line equivalence or F04 pass.
Supporting Read review found no correctness finding; required different-family
acceptance and final-artifact applicability remain. No formalF03 consumption.
Advance mandatory native-fibre material/codec integration using existing local
operators and histories; no new coordinate kernel or constitutive law.
Raw .qualification/b3-ge-e4-pl/r8-distributing-fy80-dev-20261004-v1 binds original
installed419 source files, fixtures, actual results/controls/resources, failure,
SHA-bound comparison inputs and review. Prior evidence remains immutable.
'''
report = REPO / 'docs/agent_plans/development/r8-distributing-reference-linear-20261004/results.md'
with report.open('ab') as out:
    out.write(section.encode('ascii'))
matrix = REPO / 'docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md'
with matrix.open('ab') as out:
    out.write(('''

Reference distributing Fy80,4 October: MEASURED_DEVELOPMENT_ONLY. Actual80x32
same-law/same-operator Fy fullpose differs<1% in all6 components; pitch-.864137%,
work-.030881%, reflectionresidual0 and existing physical controls pass.
Native pitch40-to80 movement2.032% leaves converged criterion/independent/final
artifact acceptance open. Stop this slice; no automatic refinement or F04/G0/line
closure. Failed first writer and repaired exact-case execution both retained.
[Evidence](development/r8-distributing-reference-linear-20261004/results.md).
''').encode('ascii'))
print('Recorded measured Fy80 exit; no acceptance or automatic refinement.')
