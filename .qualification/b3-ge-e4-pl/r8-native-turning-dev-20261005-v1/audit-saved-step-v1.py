"""Inspect saved binary arrays only; no imports of solver or numerical libraries."""
from pathlib import Path
import hashlib, json, math, struct

root = Path(__file__).resolve().parent
raw = (root / 'last-prefix-v2.checkpoint').read_bytes()
assert hashlib.sha256(raw[:-32]).digest() == raw[-32:]
assert raw.startswith(b'ANYSSARC1')
length = int.from_bytes(raw[9:13], 'little')
metadata = json.loads(raw[13:13+length])
inner = raw[13+length:-32]
assert inner.startswith(b'ANYSGECP2\0')
assert hashlib.sha256(inner[:-32]).digest() == inner[-32:]
length = int.from_bytes(inner[10:14], 'little')
header = json.loads(inner[14:14+length])
cursor = 14+length
arrays = {}
for name, shape in header['arrays']:
    count = math.prod(shape)
    arrays[name] = (shape, struct.unpack_from('<' + str(count) + 'd', inner, cursor))
    cursor += 8*count
assert cursor == len(inner)-32
dof = metadata['predictor_dof']
node, axis = divmod(dof, 6)
q = arrays['q'][1]
origin = arrays['origin_translations'][1]
normal = arrays['normal_translations'][1]
weights = arrays['metric_weights'][1]
length = metadata['metric_length']
translation_projection = sum(weights[i] * sum(
    (q[6*i+j]-origin[3*i+j])*normal[3*i+j] for j in range(3))
    for i in range(len(weights))) / length**2
rows = json.loads((root/'result-v2.json').read_bytes())['rows']
report = dict(status='SAVED_STEP_AUDIT_NO_NEW_SOLVE',
    checkpoint_sha256=hashlib.sha256(raw).hexdigest(),
    predictor_dof=dof, orientation=metadata['orientation'],
    oriented_selected_increment=metadata['orientation']*(q[dof]-origin[3*node+axis]),
    oriented_predictor_component=metadata['orientation']*normal[3*node+axis],
    translation_plane_projection=translation_projection,
    final_radius=arrays['history'][1][-2],
    late_steps=[dict(step=row['step'], w=row['w'], load=row['load'], radius=row['radius'])
                for row in rows[-8:]],
    limitations='Endpoint coordinate reversal does not by itself prove complete physical-state cycling.')
(root/'saved-step-audit-v1.json').write_bytes((json.dumps(report,indent=2)+'\n').encode('ascii'))
print(json.dumps(report))
