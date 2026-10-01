"""Verify effective task-owned Numba cache, then use the unchanged bound entry."""
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys

record_path = Path(sys.argv[1]).resolve()
record = json.loads(record_path.read_text(encoding='utf-8'))
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == record['entry_sha256']
for key, value in record['environment'].items():
    assert os.environ.get(key) == value, key
import numba
cache = Path(numba.config.CACHE_DIR).resolve()
assert cache == Path(record['environment']['NUMBA_CACHE_DIR']).resolve()
cache.mkdir(parents=True, exist_ok=False)
probe = cache/'task_write_probe'
probe.write_bytes(b'bounded development cache')
probe.unlink()
print(json.dumps({'effective_numba_cache':str(cache),'numba_version':numba.__version__,
                  'entry_sha256':record['entry_sha256']}),flush=True)
sys.argv = [str(Path(record['workspace'])/'docs/d1_review_support/contact_development_check.py'),str(record_path)]
runpy.run_path(sys.argv[0],run_name='__main__')
