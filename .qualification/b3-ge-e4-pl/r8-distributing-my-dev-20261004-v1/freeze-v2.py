from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
run=(ROOT/'run.py').read_text(encoding='utf-8').replace("'binding.json'","'binding-v2.json'").replace("'probe.py'","'probe-v2.py'").replace("('checks','prepare','native','ccx','compare')","('native','ccx','compare')")
probe=(ROOT/'probe.py').read_text(encoding='utf-8').replace("'binding.json'","'binding-v2.json'")
probe=probe.replace(" native=json.loads((ROOT/'native.json').read_text(encoding='utf-8'));n=native['results']['My']", """ binding=json.loads((ROOT/'binding-v2.json').read_text(encoding='utf-8'))
 nevent=json.loads((ROOT/'native/execution.json').read_text(encoding='utf-8'))
 assert nevent['status']=='completed' and nevent['exit_code']==0
 assert not (ROOT/'native/stderr.log').read_text().strip()
 native=json.loads((ROOT/'native.json').read_text(encoding='utf-8'))
 assert native['sources']==binding['sources'] and native['wheel_sha256']==binding['wheel_sha256']
 assert native['installed_files']==binding['installed_files']
 assert native['actual_imports'] and all(Path(p).is_relative_to(OLD/'site') for p in native['actual_imports'].values())
 n=native['results']['My']""")
for name,text in [('run-v2.py',run),('probe-v2.py',probe)]:
 compile(text,name,'exec');(ROOT/name).open('x',encoding='utf-8',newline='').write(text)
binding=json.loads((ROOT/'binding.json').read_text(encoding='utf-8'))
binding['drivers']={n:sha(ROOT/n) for n in ('run-v2.py','probe-v2.py')}
(ROOT/'binding-v2.json').open('x',encoding='utf-8').write(json.dumps(binding,indent=2)+'\n')
print('Native terminal/provenance gate frozen before execution; original preparation retained')
