"""Runtime/source identity before the focused area work-map checks."""
from pathlib import Path
import hashlib
import json
import os
import sys
import time
import numpy
import pytest
from threadpoolctl import threadpool_info

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
inputs = [REPO/'scripts/r8_e02_distributing_solid_area.py',
          REPO/'tests/test_r8_e02_distributing_solid_area.py',
          REPO/'scripts/r8_e02_rigid_tip_reference.py', REPO/'scripts/r8_e02_distributing_feasibility.py', REPO/'tests/test_r8_e02_distributing_feasibility.py']
pools = threadpool_info()
if not pools or any(p['num_threads'] != 1 for p in pools) or sys.flags.optimize:
    raise ValueError('effective one-thread unoptimized runtime required')
record = dict(scope='Level A local reference work-map, not accuracy/qualification',
    inputs={str(p.relative_to(REPO)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
    pools=pools, jit_disabled=os.environ.get('NUMBA_DISABLE_JIT')=='1')
path = ROOT/'map-runtime-v4.json'
path.write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
start = time.monotonic()
status = pytest.main(['-q', str(inputs[1]), str(inputs[4]), '-p', 'no:cacheprovider',
                     '--basetemp', str(ROOT/'map-pytest-v4')])
record.update(exit_code=int(status), checks_seconds=time.monotonic()-start)
path.write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
raise SystemExit(status)
