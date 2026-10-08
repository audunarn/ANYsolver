"""Append development disposition and prepare an explicit local staging list."""
from pathlib import Path
import json

root = Path(__file__).resolve().parent
repo = root.parents[2]
for mode in ('source', 'installed'):
    assert json.loads((root/(mode+'-v2/execution.json')).read_text())['exit_code'] == 0
suffix = b'''\n\n### 5 October - accepted-state point buckling development\n\nIMPLEMENTED_NOT_QUALIFIED: objective elastic Q4/generalized native GE six-pose\npoint accepted-state buckling keeps full42/member and multipliers in a general\nsparse descriptor; no SPD, artificial mass, condensation or symmetry repair.\nLocal Q4 material/prestress components and actual mixed-chart point curvature\nreconstruct the conservative Hessian. Lambda scales frozen accepted stress, not\na nonlinear limit load; nearest-shift finite pairs do not prove completeness.\nInitial source41PASS191.13s, installed18PASS4.31s. Review-driven failure/admission\ncoverage adds fresh source-v2/installed-v2 18PASS4.60/4.50s; product bytes unchanged.\nSupporting independent OpenAI full-slice/delta review leaves no identified defect,\nnot required different-family scientific acceptance.\nInstalled compression example completes, unchanged accepted checkpoint, factors\n13115.7456715/42746.5121121, original equation/constraint residuals<1e-15; split\nerror9.299e-17/skew2.120e-16, one factorization/21 inverse solves.\nWheel4d23ea7e9073ef3651234abe649ca6c7731ef79b5a90ea3a86a6b036697dbd45.\nSource/install package bytes, imports, effective pools1/JIToff and supervised\n600s/2GiB/affinity1 verified; no speedup or complete installed-graph claim.\nRaw .qualification/b3-ge-e4-pl/r8-ge-point-buckling-dev-20261005-v1 preserves\nbindings, sources, logs, JUnit, artifacts, sparse packets, modes and checkpoint.\nFull G4B, S3/fibre/line/footprint/B2 extensions, external/platform/scale and\naggregate acceptance remain OPEN mandatory obligations, not permanent exclusions.\nNext: continue remaining conservative spectral coverage under adopted contracts;\ndo not reopen closed F03/Fy/material/turning campaigns or qualify a subset as full.\n'''
for name in ('docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md',
             'docs/agent_plans/B3_GE_E4_PL_REVISION_8_PLAN.md',
             'docs/agent_plans/development/r8-distributing-reference-linear-20261004/results.md'):
    path = repo/name
    assert b'### 5 October - accepted-state point buckling development' not in path.read_bytes()
    with path.open('ab') as handle:
        handle.write(suffix)
excluded = {'site-v1', 'solver-dist-v1', '__pycache__'}
files = []
def visit(folder):
    for path in sorted(folder.iterdir()):
        if path.is_dir():
            if path.name not in excluded and not path.name.startswith('pytest-temp-'):
                visit(path)
        elif path.name != 'stage-paths-v2.json':
            files.append(path.relative_to(repo).as_posix())
visit(root)
product = ['src/anysolver/_stiffened_shell_ge_point_buckling.py',
    'src/anysolver/_stiffened_shell_q4_algorithmic_pullback.py',
    'src/anysolver/_stiffened_shell_ge_experimental.py', 'src/anysolver/stiffened_shell.py',
    'tests/test_stiffened_shell_ge_point_buckling.py', 'scripts/r8_ge_point_buckling_dev.py',
    'docs/reference_cases/stiffened_shell_ge_point_buckling.md',
    'docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md',
    'docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md',
    'docs/agent_plans/B3_GE_E4_PL_REVISION_8_PLAN.md',
    'docs/agent_plans/development/r8-distributing-reference-linear-20261004/results.md']
(root/'stage-paths-v2.json').write_text(json.dumps(product+files, indent=2)+'\n')
print(json.dumps(dict(product_and_docs=len(product), evidence_files=len(files),
    evidence_bytes=sum((repo/name).stat().st_size for name in files))))
