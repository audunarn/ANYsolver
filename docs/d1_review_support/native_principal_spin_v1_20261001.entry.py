from pathlib import Path
from hashlib import sha256
import json, os, runpy, sys
p = Path(sys.argv[1])
data = p.read_bytes()
assert sha256(data).hexdigest() == sys.argv[2]
spec = json.loads(data)
for path, expected in spec['source_sha256'].items():
    assert sha256(Path(path).read_bytes()).hexdigest() == expected, path
os.environ.update(spec['environment'])
sys.path[:0] = spec['pythonpath']
import anysolver
assert Path(anysolver.__file__).resolve() == Path(spec['actual_anysolver_module']).resolve()
runpy.run_path(spec['runner'], run_name='__main__')
