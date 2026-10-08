"""Retain source/evidence identities and list exact scoped delivery paths."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
FEM=Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
exclude={'site','dist','fem-site','fem-dist','__pycache__','installed-pytest-v1','consumer-pytest-v1','consumer-source-pytest-v1','pytest-v1','pytest-v2'}
raw=[p for p in ROOT.rglob('*') if p.is_file() and not any(part in exclude or part.endswith('-pytest-v1') or part.endswith('-pytest-v2') for part in p.relative_to(ROOT).parts)]
solver_paths=[
 '.gitattributes','src/anysolver/_stiffened_shell_ge_body_load.py',
 'src/anysolver/_stiffened_shell_ge_checkpoint_binary.py',
 'src/anysolver/_stiffened_shell_ge_distributed_load.py',
 'src/anysolver/_stiffened_shell_ge_distributing_finite.py',
 'src/anysolver/_stiffened_shell_ge_experimental.py',
 'src/anysolver/_stiffened_shell_ge_finite_experimental.py',
 'src/anysolver/_stiffened_shell_ge_pressure_load.py',
 'src/anysolver/_stiffened_shell_ge_reference_modal.py','src/anysolver/stiffened_shell.py',
 'tests/test_stiffened_shell_ge_distributing_finite_public.py',
 'examples/stiffened_shell_ge_distributing_finite.py',
 'docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md',
 'docs/agent_plans/B3_GE_E4_PL_REVISION_8_PLAN.md',
 'docs/agent_plans/B3_GE_E4_PL_REVISION_8_GOAL.md',
 'docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md',
 'docs/agent_plans/development/r8-distributing-reference-linear-20261004/results.md',
 'docs/agent_plans/development/r8-distributing-reference-linear-20261004/active-before-public-finite-owner-20261004.md',
]
fem_paths=['.gitattributes','src/anyfem/solve/stiffened_shell.py',
 'tests/test_stiffened_shell_ge_reference_modal_consumer.py',
 'tests/test_stiffened_shell_ge_distributing_consumer.py',
 'docs/development/r8-ge-finite-distributing-compatibility-20261004.md']
record=dict(scope='Experimental finite distributing installed development, not qualification/release',
 solver_preceding_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
 fem_preceding_commit=subprocess.check_output(['git','-c','safe.directory='+FEM.as_posix(),'rev-parse','HEAD'],cwd=FEM,text=True).strip(),
 solver_source={p:sha(REPO/p) for p in solver_paths},
 consumer_source={p:sha(FEM/p) for p in fem_paths},
 raw_files={p.relative_to(REPO).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(raw)},
 installed_wheels={p.name:dict(sha256=sha(p),bytes=p.stat().st_size) for folder in ('dist','fem-dist') for p in (ROOT/folder).glob('*.whl')})
(ROOT/'delivery-inventory-v1.json').open('x').write(json.dumps(record,indent=2)+'\n')
raw.extend([ROOT/'delivery-inventory-v1.json',ROOT/'stage-solver-paths-v1.txt',ROOT/'stage-fem-paths-v1.txt'])
solver_paths.extend(p.relative_to(REPO).as_posix() for p in sorted(raw))
(ROOT/'stage-solver-paths-v1.txt').open('x').write('\n'.join(solver_paths)+'\n')
(ROOT/'stage-fem-paths-v1.txt').open('x').write('\n'.join(fem_paths)+'\n')
print(json.dumps(dict(solver_paths=len(solver_paths),consumer_paths=len(fem_paths),raw_bytes=sum(p.stat().st_size for p in raw),excluded_sites_and_wheels=True)))
