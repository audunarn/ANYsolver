from pathlib import Path
import hashlib
import json
import os
import sys
import time

import numpy as np
from threadpoolctl import threadpool_info
import anysolver
from scripts.r8_e02_distributing_feasibility import LOADS, build_case, native_cases

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
SITE = REPO/'.qualification/b3-ge-e4-pl/r8-distributing-ge-owner-dev-20261004-v1/site'
WHEEL = SITE.parent/'dist/anysolver-0.4.7-py3-none-any.whl'
CCX = Path('C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/calculix-223/CalculiX-2.23.0-win-x64/bin/ccx.exe')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(WHEEL) == 'f0267b0f5803ce69c1a181bfd7aa22bde06fa1aafdb65cbd56bba4d550745b4e'
assert sha(CCX) == '27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f'
assert Path(anysolver.__file__).resolve().is_relative_to(SITE)
assert os.environ['NUMBA_DISABLE_JIT'] == '1' and not sys.flags.optimize
sources = ['scripts/r8_e02_distributing_solid_area.py',
    'scripts/r8_e02_distributing_feasibility.py', 'scripts/r8_e02_native_rigid_tip.py',
    'scripts/r8_e02_rigid_tip_reference.py', 'tests/test_r8_e02_distributing_solid_area.py',
    'tests/test_r8_e02_distributing_feasibility.py']
record = dict(scope='coarse common-action feasibility, no scientific acceptance/F03',
    sources={p:sha(REPO/p) for p in sources}, installed_anysolver=str(anysolver.__file__),
    wheel_sha256=sha(WHEEL), executable=str(CCX), executable_sha256=sha(CCX))
for name in LOADS:
    case = ROOT/('ccx-'+name+'-v1')
    case.mkdir(exist_ok=False)
    deck, metadata, area = build_case(name)
    if 3*len(metadata['physical_nodes']) > 100000:
        raise ValueError('registered row ceiling')
    (case/'reference.inp').write_text(deck, encoding='ascii', newline='\n')
    (case/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    record.setdefault('cases',{})[name] = dict(rows=3*len(metadata['physical_nodes']),
        elements=len(metadata['elements']), deck_sha256=sha(case/'reference.inp'), map=area.identity)
(ROOT/'feasibility-binding-v1.json').write_text(json.dumps(record,indent=2)+'\n')
started = time.monotonic()
native = native_cases()
pools = threadpool_info()
assert pools and all(p['num_threads']==1 for p in pools)
native.update(runtime_seconds=time.monotonic()-started,numerical_pools=pools,
    installed_anysolver=str(anysolver.__file__), sources=record['sources'])
(ROOT/'native-result-v1.json').write_text(json.dumps(native,indent=2,
    default=lambda value:value.tolist())+'\n')
print(json.dumps(dict(status='COMPLETED_DEVELOPMENT_ONLY',factors=native['factors'],
    cases={name:dict(pairing_J=r['external_final_pairing_J'], controls=r['controls'])
           for name,r in native['results'].items()})))
