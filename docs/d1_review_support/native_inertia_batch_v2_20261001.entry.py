from pathlib import Path
from hashlib import sha256
import json,os,sys
p=Path(sys.argv[1]);b=p.read_bytes()
assert sha256(b).hexdigest()==sys.argv[2]
spec=json.loads(b)
os.environ.update(spec['environment'])
sys.path[:0]=spec['pythonpath']
for path,h in spec['source_sha256'].items(): assert sha256(Path(path).read_bytes()).hexdigest()==h,path
print(json.dumps(dict(stage='authenticated_before_pytest',input_sha256=sys.argv[2])),flush=True)
import pytest
raise SystemExit(pytest.main([spec['test']+'::test_complete_prepared_kernel_batch','-q','-s','--import-mode=importlib',
 '--basetemp',spec['basetemp'],'--junitxml',spec['xml_output']]))
