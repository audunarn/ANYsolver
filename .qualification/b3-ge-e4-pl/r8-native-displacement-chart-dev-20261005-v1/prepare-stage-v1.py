"""Explicit chart-slice staging inventory; no Git mutations or worker edits."""
from pathlib import Path
from hashlib import sha256
import json
ROOT=Path(__file__).resolve().parents[3];RAW=Path(__file__).resolve().parent
names=['.gitattributes','docs/stiffened_shell_native_chart_development.md',
       'tests/test_stiffened_shell_native_displacement_chart.py',
       'tests/test_stiffened_shell_native_point_displacement.py']
names += ['src/anysolver/'+name+'.py' for name in (
    '_stiffened_shell_affine_endpoint','_stiffened_shell_displacement_adaptive',
    '_stiffened_shell_displacement_checkpoint','_stiffened_shell_displacement_control',
    '_stiffened_shell_displacement_corrector','_stiffened_shell_ge_experimental',
    '_stiffened_shell_ge_finite_experimental')]
names += ['docs/agent_plans/'+name+'.md' for name in (
    'B3_GE_E4_PL_ACTIVE_STATE','B3_GE_E4_PL_REVISION_8_GOAL',
    'B3_GE_E4_PL_REVISION_8_PLAN','B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX')]
names += ['docs/agent_plans/development/r8-distributing-reference-linear-20261004/results.md']
for path in RAW.rglob('*'):
    if not path.is_file():continue
    rel=path.relative_to(RAW)
    if any(x in ('site-v1','solver-dist-v1','__pycache__','.pytest_cache') for x in rel.parts):continue
    if path.suffix in ('.pyc','.whl'):continue
    if path.name in ('stage-inputs-v1.txt','stage-working-bytes-v1.json','staged-proof-v1.json'):continue
    names.append(str(path.relative_to(ROOT)).replace('\\','/'))
names=sorted(set(names))
inventory={name:dict(bytes=(ROOT/name).stat().st_size,
    sha256=sha256((ROOT/name).read_bytes()).hexdigest()) for name in names}
(RAW/'stage-working-bytes-v1.json').write_bytes((json.dumps(inventory,indent=2)+'\n').encode('ascii'))
names.append(str((RAW/'stage-working-bytes-v1.json').relative_to(ROOT)).replace('\\','/'))
(RAW/'stage-inputs-v1.txt').write_bytes(('\n'.join(names)+'\n').encode('ascii'))
print(json.dumps(dict(files=len(names),bytes=sum(v['bytes'] for v in inventory.values()))))
