from pathlib import Path
import hashlib,json,ast
import numpy as np
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
run=(ROOT/'run-v2.py').read_text(encoding='utf-8').replace('binding-v2','binding-v3').replace('probe-v2','probe-v3').replace("m.supervise(command,kind,", "m.supervise(command,kind+'-v3',")
probe=(ROOT/'probe-v2.py').read_text(encoding='utf-8').replace('binding-v2','binding-v3').replace("'native.json'","'native-v3.json'").replace("'native/execution.json'","'native-v3/execution.json'").replace("'native/stderr.log'","'native-v3/stderr.log'").replace('execution/execution.json','execution-v3/execution.json').replace('execution/stderr.log','execution-v3/stderr.log').replace('execution/stdout.log','execution-v3/stdout.log').replace("'parsed.json'","'parsed-v3.json'").replace("'comparison.json'","'comparison-v3.json'")
probe=probe.replace("def save(p,v):p.open('x',encoding='utf-8').write(json.dumps(v,indent=2,allow_nan=False)+'\\n')", """def encode_array(value):
 if isinstance(value,np.ndarray):return value.tolist()
 raise TypeError('unsupported diagnostic record type: '+type(value).__name__)
def save(p,v):
 text=json.dumps(v,indent=2,allow_nan=False,default=encode_array)+'\\n'
 p.open('x',encoding='utf-8').write(text)""")
# Verify the actual final serializer definitions with nested recovery arrays,
# strict nonfinite rejection and no partial file on encoding failure.
tree=ast.parse(probe)
defs=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('encode_array','save')],type_ignores=[])
env={'np':np,'json':json};exec(compile(defs,'serializer-controls','exec'),env)
record={'transfer':{'centroid_m':np.array((.9,-.025,0.)),'shell_action':np.array((0,0,0,0,1,0))}}
env['save'](ROOT/'serializer-control.json',record)
assert json.loads((ROOT/'serializer-control.json').read_text())['transfer']['centroid_m']==[.9,-.025,0.]
try:env['save'](ROOT/'must-not-exist.json',{'response':np.array((np.nan,))})
except ValueError:pass
else:raise AssertionError('nonfinite serializer admitted')
assert not (ROOT/'must-not-exist.json').exists()
for name,text in [('run-v3.py',run),('probe-v3.py',probe)]:
 compile(text,name,'exec');(ROOT/name).open('x',encoding='utf-8',newline='').write(text)
binding=json.loads((ROOT/'binding-v2.json').read_text(encoding='utf-8'))
binding['drivers']={n:sha(ROOT/n) for n in ('run-v3.py','probe-v3.py')}
(ROOT/'binding-v3.json').open('x',encoding='utf-8').write(json.dumps(binding,indent=2)+'\n')
print('Final serializer control PASS; failed native output/log untouched; fresh v3 paths')
