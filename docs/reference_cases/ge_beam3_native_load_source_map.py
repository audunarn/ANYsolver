"""Read-only native load development binding; not execution authority."""

import ast
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
BASE = '9173d83c0222deed07f4233ab756b9cc2d0f2faf'
OLD = 'docs/reference_cases/ge_beam3_centered_native_source_map.json'
OLD_SHA = '5f6a8cbfce0b6a05eb7839b1db8541d89b0284e66516c2d1748c39f66dbd0493'
TARGET = 'src/anysolver/_ge_beam3_p5_loads'
FILES = ('__init__.py','codec.py','core.py','element.py','state.py','work.py')
MANIFEST = 'docs/reference_cases/ge_beam3_native_load_source_map.json'
# Verified against git blobs at BASE, before importing any native mechanics.
FRAMEWORK = {
    'src/anysolver/_native_material_protocol.py': {'bytes':1904,'sha256':'5d1e6316df3192db47993801fc2600fd9a69991aa26a7a354694a8b3dafc78b0'},
    'src/anysolver/nonlinear_element_evaluation.py': {'bytes':4077,'sha256':'8eb966598028f5099d2e251c1bb161e2d17f51e35a9501aa3e0a13f1396dff92'},
    'src/anysolver/nonlinear_state.py': {'bytes':115917,'sha256':'9a81355dac4ab9d45cdb7f9100b7676cdfa1e842f24031f028e9588e84ecd474'},
    'src/anysolver/nonlinear_static.py': {'bytes':268287,'sha256':'322e315d7a4eb9b9b23f971a73397fb3f8ff42f0dbd4a50549037d2494405c3e'},
}


def source(path): return (ROOT/path).read_text(encoding='utf-8').encode('utf-8')


def binding(raw): return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode('ascii')


def build():
    old = source(OLD)
    if binding(old)['sha256'] != OLD_SHA: raise ValueError('preserved centered source map changed')
    outputs = {**json.loads(old)['outputs'],**FRAMEWORK}
    for path,expected in outputs.items():
        if binding(source(path)) != expected: raise ValueError('preserved source changed: '+path)
    if {p.name for p in (ROOT/TARGET).glob('*.py')} != set(FILES): raise ValueError('load module extent mismatch')
    for name in FILES:
        path = TARGET+'/'+name; raw = source(path)
        for node in ast.walk(ast.parse(raw)):
            modules = ([node.module or ''] if isinstance(node,ast.ImportFrom) else
                       [item.name for item in node.names] if isinstance(node,ast.Import) else [])
            if any(module.split('.')[0] in ('docs','tests') for module in modules):
                raise ValueError('native load source imports research code')
        outputs[path] = binding(raw)
    return dict(schema='GE_BEAM3_NATIVE_LOAD_DEVELOPMENT_SOURCE_MAP_V4',base_commit=BASE,
        output_text_normalization='UTF8_LF',formulation_id='CANDIDATE_GE_BEAM3_P5_NATIVE_LOAD_V4',
        load_policy='SPATIAL_DEAD_FORCE_PER_REFERENCE_ARCLENGTH_V1',outputs=outputs,
        preserved_map_sha256=OLD_SHA,production_qualified=False,public_driver_authorized=False,
        independent_review_status='PENDING')


if __name__ == '__main__':
    raw = canonical(build())
    if sys.argv[1:] == ['--check']:
        if source(MANIFEST) != raw: raise ValueError('native load source binding mismatch')
        print('NATIVE_LOAD_SOURCE_BINDING_EXACT: 6 new and 40 preserved modules')
    elif not sys.argv[1:]: print(raw.decode('ascii'),end='')
    else: raise SystemExit('only stdout binding or --check supported')
