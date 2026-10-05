"""Local evidence inventory/scope, not a scientific adjudicator or Git mutation."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=['.gitattributes','scripts/r8_e02_distributing_feasibility.py','tests/test_r8_e02_distributing_feasibility.py','src/anysolver/_stiffened_shell_distributing_footprint.py','src/anysolver/_stiffened_shell_ge_distributing_reference.py','tests/test_stiffened_shell_distributing_footprint.py','tests/test_stiffened_shell_ge_distributing_reference.py','tests/test_stiffened_shell_ge_distributing_owner.py','docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md','docs/agent_plans/B3_GE_E4_PL_REVISION_8_PLAN.md','docs/agent_plans/B3_GE_E4_PL_REVISION_8_GOAL.md','docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md','docs/agent_plans/development/r8-distributing-reference-linear-20261004/results.md']
for record in ('installed-runtime-v1.json','consumer-runtime-v1.json','example-runtime-v1.json','fixture-runtime-v2.json'):
 r=json.loads((ROOT/record).read_text());assert r['exit_code']==0
binding=json.loads((ROOT/'paired-binding-v1.json').read_text())
assert all(sha(REPO/p)==h for p,h in binding['sources'].items())
assert sha(ROOT/'dist/anysolver-0.4.7-py3-none-any.whl')==binding['wheel_sha256']
assert all(json.loads(p.read_text())['status']=='completed' for p in ROOT.rglob('execution.json'))
raw=[p for p in ROOT.rglob('*') if p.is_file() and not any(part in ('site','dist','__pycache__') or 'pytest' in part for part in p.relative_to(ROOT).parts) and p.name not in ('artifact-inventory-v1.json','stage-paths-v1.txt','git-byte-verification-v1.json')]
raw.sort();protected=[p for p in files if p.endswith('.py')]+[p.relative_to(REPO).as_posix() for p in raw]
inventory=dict(scope='Recoverable local source/evidence delivery; no scientific gate or release',wheel_sha256=binding['wheel_sha256'],protected={p:dict(sha256=sha(REPO/p),bytes=(REPO/p).stat().st_size) for p in protected},external_supervisor_sha256='ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec',supervisor_used_excerpt='../r8-e02-distributing-area-feasibility-dev-20261004-v1/supervisor-excerpt-used.py')
(ROOT/'artifact-inventory-v1.json').open('x').write(json.dumps(inventory,indent=2)+'\n')
paths=files+[p.relative_to(REPO).as_posix() for p in raw]+[(ROOT/'artifact-inventory-v1.json').relative_to(REPO).as_posix(),(ROOT/'stage-paths-v1.txt').relative_to(REPO).as_posix()]
(ROOT/'stage-paths-v1.txt').open('x').write('\n'.join(paths)+'\n')
print(json.dumps(dict(stage_paths=len(paths),protected_files=len(protected),raw_bytes=sum(p.stat().st_size for p in raw),wheel_sha256=binding['wheel_sha256'])))
