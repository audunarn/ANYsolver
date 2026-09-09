"""Read-only development source binding for centered native P5 adoption."""

import ast
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
TARGET = 'src/anysolver/_ge_beam3_p5_centered'
MANIFEST = 'docs/reference_cases/ge_beam3_centered_native_source_map.json'
FILES = ('__init__.py','codec.py','committed_modal.py','core.py','element.py','mass.py','positions.py','reference_modal.py')
PARENT = '1ced65643faa63fe01bdcb23e31a0f9da0fc7250'
OLD_MAP = 'docs/reference_cases/ge_beam3_curved_p5_coordinate_source_map.json'
OLD_SHA256 = '4aee73cf0ec59a4190e9a2e4a8d2d97c1bf86d31331a0a53fedbe14f4c1fc8f5'
REFERENCE_EVIDENCE = 'docs/reference_cases/ge_beam3_centered_reference_evidence.json'


def canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode('ascii')


def source(path):
    return (ROOT/path).read_text(encoding='utf-8').encode('utf-8')


def binding(raw):
    return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def build():
    old_raw = source(OLD_MAP)
    if binding(old_raw)['sha256'] != OLD_SHA256: raise ValueError('preserved native V2 source map changed')
    outputs = dict(json.loads(old_raw)['outputs'])
    reference = json.loads(source(REFERENCE_EVIDENCE))
    for path,expected in reference['source_bindings'].items():
        if binding(source(path)) != expected: raise ValueError('preserved reference source changed: '+path)
        if path.startswith('src/'): outputs[path] = expected
    for path,expected in outputs.items():
        if binding(source(path)) != expected: raise ValueError('preserved source module changed: '+path)
    if {p.name for p in (ROOT/TARGET).glob('*.py')} != set(FILES): raise ValueError('native centered module extent mismatch')
    for name in FILES:
        path = TARGET+'/'+name; raw = source(path)
        for node in ast.walk(ast.parse(raw)):
            modules = ([node.module or ''] if isinstance(node,ast.ImportFrom) else
                       [item.name for item in node.names] if isinstance(node,ast.Import) else [])
            if any(module.split('.')[0] in ('docs','tests') for module in modules):
                raise ValueError('native candidate imports research code')
        outputs[path] = binding(raw)
    return dict(schema='GE_BEAM3_CENTERED_NATIVE_SOURCE_MAP_V3',development_parent=PARENT,
        output_text_normalization='UTF8_LF',formulation_id='CANDIDATE_GE_BEAM3_P5_NATIVE_CENTERED_V3',
        reference_evaluation='CENTERED_Q2_TWO_COMPONENT_COEFFICIENT_ANALYTIC_LIFT_V1',
        coordinate_policy='GE_BEAM3_P5_REFERENCE_PLUS_TOTAL_TWO_COMPONENT_V1',
        preserved_coordinate_map_sha256=OLD_SHA256,
        preserved_reference_evidence_sha256=binding(source(REFERENCE_EVIDENCE))['sha256'],
        independent_review_status='PENDING',production_qualified=False,public_selector_authorized=False,
        derived_from={name:'src/anysolver/_ge_beam3_p5_coordinates/'+name for name in FILES if name != 'mass.py'},
        outputs=outputs)


if __name__ == '__main__':
    made = canonical(build())
    if sys.argv[1:] == ['--check']:
        if source(MANIFEST) != made: raise ValueError('centered native source binding mismatch')
        print('CENTERED_NATIVE_SOURCE_BINDING_EXACT: 8 new and 28 preserved source modules')
    elif not sys.argv[1:]:
        print(made.decode('ascii'),end='')
    else:
        raise SystemExit('only stdout binding or --check is supported')
