"""Preserve previous checkpoint bytes, append disposition, list exact local edits."""
from pathlib import Path
import json, subprocess

root = Path(__file__).resolve().parent
repo = root.parents[2]
for phase in ('source', 'installed', 'example-installed'):
    assert json.loads((root/(phase+'-v4/execution.json')).read_text())['exit_code'] == 0
history = repo/'docs/agent_plans/history/PRE_BL5_BUCKLING_20261005.md'
with history.open('xb') as handle:
    handle.write(subprocess.check_output(['git','show','HEAD:docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md'], cwd=repo))
suffix = b'''\n\n### 5 October - nonmatching BL5 conservative buckling development\n\nIMPLEMENTED_NOT_QUALIFIED: GELineBucklingRequest/result and separate experimental\npolicy extend existing owner.buckling. Existing point API/defaults unchanged.\nExact BL5 additive-shell covector/Hessian pullback preserves five-channel law,\nfrozen basis/quadrature, native cell lifts, all42/member and point+line curvature.\nBoundary witnesses bind actual compiled stations and owned density/gap maps.\nNo SPD, artificial mass, condensation, symmetry repair or multiplier-space choice.\nInitial source-v1:39PASS2FAIL due new negative test None.copy assumption, fixed\nwithout product edit. v2 supervisor refused output reuse before child launch.\nAll failed evidence preserved. Source-v3:41PASS19.37s. Anchored independent AD,\nactual rebase covariance/history/factor/restart and controlled nonzero-lift work\nchecks extend source-v4:45PASS28.96s; installed-v4:45PASS26.48s. Rebase finite\nfactors agree within1e-9 relative; actual-update derivative plateau<=1e-6.\nThe local lift witness does not confer whole-model geometry qualification.\nInstalled P0 public example COMPLETE_DEVELOPMENT, unchanged checkpoint, accepted\nequilibrium9.250e-11/gap1.258e-17, two frozen-prestress factors7436.23653335 and\n40821.1606844, original pair equation/constraint residuals<3e-16. One factorization\nand21 inverse solves; split1.069e-16/skew1.668e-16. No nonlinear limit-load or\nlowest-instability/completeness claim.\nSolverwheel7aa5b9f911cb9e506ca5d25fbbaaa063e8d18a1f450930061cb1dd18fe753777.\nSource/package bytes, actual imports, effective pools1/JIToff, supervisor600s/2GiB\nprocess tree/affinity1 verified. No speedup or complete dependency/platform claim.\nSupporting independent OpenAI contract/full/delta reviews leave no identified\ndefect; different-family scientific acceptance remains pending.\nRaw .qualification/b3-ge-e4-pl/r8-ge-line-buckling-dev-20261005-v1 binds immutable\nsource versions, failed/startup and successful logs, JUnit, wheel/import identities,\nsparse packets, checkpoint and coefficient/density/gap recovery.\nFull G4B, remaining materials/shells/attachments/loads, B2 and external/platform/\nscale/consumer qualification remain mandatory OPEN. Continue those obligations\nunder adopted contracts, without reopening closed campaigns or narrowing scope.\n'''
docs = ['docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md',
    'docs/agent_plans/B3_GE_E4_PL_REVISION_8_PLAN.md',
    'docs/agent_plans/development/r8-distributing-reference-linear-20261004/results.md']
for name in docs:
    path = repo/name
    assert b'### 5 October - nonmatching BL5 conservative buckling development' not in path.read_bytes()
    with path.open('ab') as handle:
        handle.write(suffix)
files = []
def visit(folder):
    for path in sorted(folder.iterdir()):
        if path.is_dir():
            if not (path.name.startswith(('site-', 'solver-dist-', 'pytest-temp-')) or path.name == '__pycache__'):
                visit(path)
        elif path.name != 'stage-paths.json':
            files.append(path.relative_to(repo).as_posix())
visit(root)
product = ['src/anysolver/_stiffened_shell_ge_point_buckling.py',
    'src/anysolver/_stiffened_shell_ge_experimental.py', 'src/anysolver/stiffened_shell.py',
    'tests/test_stiffened_shell_ge_line_buckling.py', 'scripts/r8_ge_line_buckling_dev.py',
    'docs/reference_cases/stiffened_shell_ge_line_buckling.md',
    'docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md', history.relative_to(repo).as_posix(), *docs]
(root/'stage-paths.json').write_text(json.dumps(product+files, indent=2)+'\n')
print(json.dumps(dict(product_and_docs=len(product), evidence_files=len(files),
    evidence_bytes=sum((repo/name).stat().st_size for name in files))))
