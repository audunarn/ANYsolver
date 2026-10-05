"""One startup-only diagnostic; no initializer, pytest execution or dynamics."""
import faulthandler
import hashlib
import importlib
import json
from pathlib import Path
import sys
from time import perf_counter

faulthandler.enable()
faulthandler.dump_traceback_later(15, repeat=False)
started = perf_counter()
record = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
root = Path(record['workspace']).resolve()
assert Path.cwd().resolve() == root
def report(stage):
    print(json.dumps({'stage':stage,'elapsed_seconds':perf_counter()-started}),flush=True)
report('entry')
for item in record['sources']:
    path = (root/item['path']).resolve()
    assert path.is_relative_to(root)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256']
report('445_source_bindings_verified')
for module in ('anysolver','numpy','scipy','pytest','threadpoolctl'):
    report('before_'+module)
    imported = importlib.import_module(module)
    report('after_'+module)
report('completed_imports_no_solver_execution')
faulthandler.cancel_dump_traceback_later()
