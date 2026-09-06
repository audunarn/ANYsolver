"""Read-only source binding for the private coordinate-state successor.

No mechanics import, source rewrite, authority generation or execution mode.
"""

import ast
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
TARGET = 'src/anysolver/_ge_beam3_p5_coordinates'
BASE = 'cdf71995570b3d1aaeda44b7ed046c04528ae6b8'
MANIFEST = 'docs/reference_cases/ge_beam3_curved_p5_coordinate_source_map.json'
FILES = ('__init__.py','codec.py','committed_modal.py','core.py','element.py','positions.py','reference_modal.py')
OLD_MAP = 'docs/reference_cases/ge_beam3_curved_p5_package_source_map.json'
OLD_MAP_SHA256 = '74af7d7c242cd3367bb7b8ea91ef3f71d2d5d6cebfee18e05bb5951410a6fc65'


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode('ascii')


def source(path):
    return (ROOT/path).read_text(encoding='utf-8').encode('utf-8')


def binding(raw):
    return dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def build():
    old_raw = source(OLD_MAP)
    if hashlib.sha256(old_raw).hexdigest() != OLD_MAP_SHA256:
        raise ValueError('preserved package source authority changed')
    inherited = json.loads(old_raw)['outputs']
    for path, expected in inherited.items():
        if binding(source(path)) != expected:
            raise ValueError('preserved package mechanics changed: '+path)
    if {p.name for p in (ROOT/TARGET).glob('*.py')} != set(FILES):
        raise ValueError('coordinate package extent differs from seven registered modules')
    outputs = dict(inherited)
    for name in FILES:
        path = TARGET+'/'+name; raw = source(path)
        for node in ast.walk(ast.parse(raw)):
            modules = ([node.module or ''] if isinstance(node, ast.ImportFrom) else
                       [n.name for n in node.names] if isinstance(node, ast.Import) else [])
            if any(module.split('.')[0] in ('docs','tests') for module in modules):
                raise ValueError('research import in native coordinate package')
        outputs[path] = binding(raw)
    return dict(schema='GE_BEAM3_P5_COORDINATE_SOURCE_MAP_V2', output_text_normalization='UTF8_LF',
        preserved_package_commit=BASE, preserved_package_source_map_sha256=OLD_MAP_SHA256,
        formulation_id='CANDIDATE_GE_BEAM3_P5_NATIVE_COORDINATE_V2',
        coordinate_policy='GE_BEAM3_P5_REFERENCE_PLUS_TOTAL_TWO_COMPONENT_V1',
        production_qualified=False, independent_review_status='PENDING', outputs=outputs,
        derived_from={name:'src/anysolver/_ge_beam3_p5/'+name for name in FILES
                      if name not in ('__init__.py','positions.py')},
        correction_extent=['native_total_position_pair','state_identity_and_validation','typed_restart_codec',
            'split_station_position_recovery','accepted_operator_position_pair','rest_mass_coordinate_independence'])


if __name__ == '__main__':
    made = canonical(build())
    if sys.argv[1:] == ['--check']:
        if source(MANIFEST) != made: raise ValueError('coordinate successor source binding mismatch')
        print('COORDINATE_SOURCE_BINDING_EXACT: 7 successor modules, 17 preserved modules')
    elif not sys.argv[1:]:
        print(made.decode('ascii'), end='')
    else:
        raise SystemExit('only no arguments (stdout manifest) or --check are supported')
