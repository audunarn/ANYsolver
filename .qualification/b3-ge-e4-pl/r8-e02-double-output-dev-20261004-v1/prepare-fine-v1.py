"""Append output only to the saved 40x16/nz4 Mx/Fy decks, never refine."""
from pathlib import Path
import hashlib, json

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
prior = ROOT.parent/'r8-distributing-thickness-dev-20261004-v1'
old = json.loads((prior/'binding-v5.json').read_text())
binding = dict(scope='OUTPUT_ONLY_DEVELOPMENT: raw balance and saved work precision; no acceptance',
    original_binding_sha256=hashlib.sha256((prior/'binding-v5.json').read_bytes()).hexdigest(),
    executable=old['executable'], executable_sha256=old['executable_sha256'], cases={},
    balance_screen=dict(length_m=1., force_N={'Mx':1., 'Fy':10.},
        norm='max(abs(force)/F, abs(moment)/(F*L))', limit=1e-8,
        interpretation='programme screen only; no new convergence/qualification criterion'),
    limits=dict(rows=100000, seconds=600, memory_bytes=2*1024**3, affinity=1, numerical_pools=1),
    sources={p:hashlib.sha256((REPO/p).read_bytes()).hexdigest() for p in (
        'scripts/r8_e02_double_output.py', 'scripts/r8_e02_distributing_solid_area.py',
        'scripts/r8_e02_distributing_feasibility.py', 'scripts/r8_e02_rigid_tip_reference.py')})
addition = b'*NODE OUTPUT,DOUBLE,NSET=ALL\nU\n*NODE OUTPUT,DOUBLE,NSET=ROOT\nRF\n'
for name in ('Mx','Fy'):
    source = prior/('ccx-'+name+'-v5')
    data = (source/'reference.inp').read_bytes()
    metadata = json.loads((source/'metadata.json').read_text())
    assert hashlib.sha256(data).hexdigest() == old['cases'][name]['deck_sha256']
    assert metadata['nx'] == 40 and metadata['ny'] == 16 and metadata['nz'] == 4
    assert len(metadata['elements']) == 2560 and 3*len(metadata['physical_nodes']) <= 100000
    assert data.count(b'*END STEP') == 1 and b'*NODE OUTPUT' not in data
    newline = b'\r\n' if b'\r\n' in data else b'\n'
    inserted = addition.replace(b'\n', newline)
    final = data.replace(b'*END STEP', inserted+b'*END STEP')
    assert final.replace(inserted, b'', 1) == data
    case = ROOT/('fine-'+name+'-v1'); case.mkdir()
    (case/'reference.inp').write_bytes(final)
    (case/'metadata.json').write_bytes((source/'metadata.json').read_bytes())
    binding['cases'][name] = dict(original_deck=str(source/'reference.inp'),
        original_sha256=hashlib.sha256(data).hexdigest(), deck_sha256=hashlib.sha256(final).hexdigest(),
        metadata_sha256=hashlib.sha256((case/'metadata.json').read_bytes()).hexdigest(),
        nodes=len(metadata['physical_nodes']), rows=3*len(metadata['physical_nodes']), elements=2560)
(ROOT/'fine-binding-v1.json').write_text(json.dumps(binding, indent=2)+'\n', encoding='ascii')
print(json.dumps(binding['cases'], indent=2))
