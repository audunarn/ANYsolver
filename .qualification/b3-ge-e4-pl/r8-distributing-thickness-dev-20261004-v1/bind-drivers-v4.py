from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent; REPO=ROOT.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prior=REPO/'.qualification/b3-ge-e4-pl/r8-distributing-multihost-dev-20261004-v1/paired-comparison-v1.json'
assert sha(prior)=='cf6f6c62339ca37008c7ce82fd59fd2d2c1c9ab6b3cff7dd10b165cbd56917b7'
verify="""
 for rel,expected in binding['drivers'].items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==expected
 assert hashlib.sha256(Path(binding['prior_comparison']).read_bytes()).hexdigest()==binding['prior_comparison_sha256']
"""
run=(ROOT/'run-v1.py').read_text(encoding='utf-8').replace("'probe-v1.py'","'probe-v4.py'").replace("'binding-v1.json'","'binding-v4.json'").replace("kind+'-v1'","kind+'-v4'")
run=run.replace("if kind in ('checks','prepare','parse'):","if kind=='parse':\n binding=json.loads((ROOT/'binding-v4.json').read_text(encoding='utf-8'))"+verify)
run=run.replace(" for rel,expected in binding['sources'].items():",verify+" for rel,expected in binding['sources'].items():")
probe=(ROOT/'probe-v1.py').read_text(encoding='utf-8').replace("'binding-v1.json'","'binding-v4.json'").replace("'execution-v1/","'execution-v4/").replace("'parsed-v1.json'","'parsed-v4.json'").replace("'comparison-v1.json'","'comparison-v4.json'")
probe=probe.replace(" prior=json.loads((OLD/'paired-comparison-v1.json').read_text(encoding='utf-8'))",verify+" prior=json.loads(Path(binding['prior_comparison']).read_text(encoding='utf-8'))")
for name,text in [('run-v4.py',run),('probe-v4.py',probe)]:
 compile(text,name,'exec');(ROOT/name).open('x',encoding='utf-8',newline='').write(text)
binding=json.loads((ROOT/'binding-v1.json').read_text(encoding='utf-8'))
binding.update(prior_comparison=str(prior),prior_comparison_sha256=sha(prior),drivers={n:sha(ROOT/n) for n in ('run-v4.py','probe-v4.py')})
(ROOT/'binding-v4.json').open('x',encoding='utf-8').write(json.dumps(binding,indent=2)+'\n')
print(json.dumps({'rows':38859,'elements':2560,'drivers':binding['drivers'],'prior':binding['prior_comparison_sha256']}))
