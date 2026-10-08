from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
names = [
    '.gitattributes',
    'src/anysolver/_stiffened_shell_ge_experimental.py',
    'src/anysolver/_stiffened_shell_ge_finite_experimental.py',
    'src/anysolver/_stiffened_shell_ge_checkpoint_binary.py',
    'src/anysolver/stiffened_shell.py',
    'tests/test_stiffened_shell_distributing_cyclic.py',
    'docs/stiffened_shell_distributing_material_development.md',
    'docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md',
    'docs/agent_plans/B3_GE_E4_PL_REVISION_8_GOAL.md',
    'docs/agent_plans/B3_GE_E4_PL_REVISION_8_PLAN.md',
    'docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md',
    'docs/agent_plans/development/r8-distributing-reference-linear-20261004/results.md',
]
excluded = {'site-v1','solver-dist-v1','fem-dist-v1','pytest-v1','__pycache__'}
for path in ROOT.rglob('*'):
    if path.is_file() and not excluded.intersection(path.relative_to(ROOT).parts) and path.suffix != '.pyc':
        names.append(path.relative_to(REPO).as_posix())
names += [(ROOT / name).relative_to(REPO).as_posix() for name in
          ('solver-stage-v1.json', 'solver-stage-v1.bin')]
names = sorted(set(names))
(ROOT / 'solver-stage-v1.json').open('x').write(json.dumps(names, indent=2) + '\n')
(ROOT / 'solver-stage-v1.bin').open('xb').write(b'\0'.join(name.encode() for name in names) + b'\0')
print(f'Scoped {len(names)} files, {sum((REPO/name).stat().st_size for name in names)} bytes; no sites/wheels/caches.')
