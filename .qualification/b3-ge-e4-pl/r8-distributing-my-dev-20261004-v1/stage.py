from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
prefix=str(ROOT.relative_to(REPO)).replace('\\','/')+'/'
git=lambda *args:subprocess.check_output(['git',*args],cwd=REPO)
assert not git('diff','--cached','--name-only').strip()
inventory=json.loads((ROOT/'inventory.json').read_text(encoding='utf-8'))
for rel,record in inventory.items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==record['sha256']
raw=[prefix+rel for rel in inventory]+[prefix+n for n in ('inventory.json','stage.py')]
regular=['.gitattributes','scripts/r8_e02_distributing_feasibility.py','scripts/r8_e02_distributing_my.py','tests/test_r8_e02_distributing_my.py',
 'docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md','docs/agent_plans/B3_GE_E4_PL_REVISION_8_PLAN.md','docs/agent_plans/B3_GE_E4_PL_REVISION_8_GOAL.md',
 'docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md','docs/agent_plans/development/r8-distributing-reference-linear-20261004/results.md']
paths=regular+raw;assert len(paths)==len(set(paths))
subprocess.run(['git','add','--',*regular],cwd=REPO,check=True)
subprocess.run(['git','add','-f','--',*raw],cwd=REPO,check=True)
staged=git('diff','--cached','--name-only','-z').decode().split('\0')[:-1];assert set(staged)==set(paths)
text={'.gitattributes',*regular[4:8]}
for rel in staged:
 a=(REPO/rel).read_bytes();b=git('show',':'+rel)
 if rel in text:a=a.replace(b'\r\n',b'\n');b=b.replace(b'\r\n',b'\n')
 assert a==b,rel
for rel in regular[1:4]:assert (REPO/rel).read_bytes()==(ROOT/'final-bytes'/rel).read_bytes()
subprocess.run(['git','-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','diff','--cached','--check'],cwd=REPO,check=True)
print(json.dumps({'files':len(staged),'raw':len(raw),'exact_source_raw_bytes':True,'only_declared_living_text_normalization':True}))
