from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
snapshot=ROOT/'final-bytes';snapshot.mkdir()
for rel in ('scripts/r8_e02_distributing_thickness.py','scripts/r8_e02_distributing_feasibility.py','tests/test_r8_e02_distributing_thickness.py'):
 target=snapshot/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(REPO/rel,target)
active=REPO/'docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md'
shutil.copyfile(active,ROOT/'active-before-thickness-result.md')
files=[p for p in ROOT.rglob('*') if p.is_file() and not any(part.startswith('pytest-') or part=='__pycache__' for part in p.relative_to(ROOT).parts)]
inventory={str(p.relative_to(ROOT)).replace('\\','/'):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in files}
(ROOT/'inventory-v1.json').open('x',encoding='utf-8').write(json.dumps(inventory,indent=2)+'\n')
print(json.dumps({'retained_files':len(files),'bytes':sum(v['bytes'] for v in inventory.values()),'final_source':sha(REPO/'scripts/r8_e02_distributing_thickness.py')}))
