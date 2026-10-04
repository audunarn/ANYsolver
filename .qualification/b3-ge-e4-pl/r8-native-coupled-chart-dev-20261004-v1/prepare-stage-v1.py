from pathlib import Path
import json

root = Path(__file__).resolve().parent
repo = root.parents[2]
sources = ['.gitattributes', 'docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md',
 'docs/agent_plans/B3_GE_E4_PL_REVISION_8_GOAL.md',
 'docs/agent_plans/B3_GE_E4_PL_REVISION_8_PLAN.md',
 'docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md',
 'docs/agent_plans/development/r8-distributing-reference-linear-20261004/results.md']
for name in ('check-staged-v1.py','stage-inputs-v1.txt','staged-proof-v1.json'):
    if name == 'staged-proof-v1.json' and not (root/name).exists():
        (root/name).write_text('{}\n')
    sources.append((root/name).relative_to(repo).as_posix())
for path in root.rglob('*'):
    if not path.is_file(): continue
    rel = path.relative_to(root)
    if any(p.startswith(('pytest-','__pycache__')) for p in rel.parts): continue
    if path.suffix == '.pyc': continue
    sources.append(path.relative_to(repo).as_posix())
(root/'stage-inputs-v1.txt').write_text('\n'.join(sorted(set(sources)))+'\n')
print(json.dumps(dict(files=len(set(sources)),bytes=sum((repo/p).stat().st_size for p in set(sources)))))
