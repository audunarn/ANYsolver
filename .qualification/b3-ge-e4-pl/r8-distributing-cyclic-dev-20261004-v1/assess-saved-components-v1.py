"""Read saved scalar/vector outputs only; no assembly or solver execution."""
from pathlib import Path
import hashlib, json

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent
paths = {
    'paired': BASE / 'r8-distributing-multihost-dev-20261004-v1/paired-comparison-v1.json',
    'native80': BASE / 'r8-distributing-native-adequacy-dev-20261004-v1/native.json',
    'thickness': BASE / 'r8-distributing-thickness-dev-20261004-v1/comparison-v5.json',
    'binary': BASE / 'r8-e02-double-output-dev-20261004-v1/fine-comparison-v1.json',
    'binary_binding': BASE / 'r8-e02-double-output-dev-20261004-v1/fine-binding-v1.json',
}
data = {name:json.loads(path.read_text()) for name,path in paths.items()}
rows = []
for level, cases in data['paired']['levels'].items():
    mx, fy = cases['Mx'], cases['Fy']
    rows.append(dict(level=level, native_mx_pitch=mx['native_rotation_rad'][1],
        native_fy_pitch=fy['native_rotation_rad'][1],
        native_reflection_residual_rad=fy['native_rotation_rad'][1]+.5*mx['native_rotation_rad'][1],
        solid_mx_pitch=mx['solid_rotation_rad'][1], solid_fy_pitch=fy['solid_rotation_rad'][1],
        solid_reflection_residual_rad=fy['solid_rotation_rad'][1]+.5*mx['solid_rotation_rad'][1],
        native_mx_pose=mx['native_port_translation_m']+mx['native_rotation_rad'],
        native_fy_pose=fy['native_port_translation_m']+fy['native_rotation_rad'],
        solid_mx_pose=mx['solid_port_translation_m']+mx['solid_rotation_rad'],
        solid_fy_pose=fy['solid_port_translation_m']+fy['solid_rotation_rad']))
fine = data['binary']['results']
solid_pitch = fine['Fy']['observable']['rotation_components_rad'][1]
mx80 = data['native80']['results']['Mx']['port_rotation_rad'][1]
predicted = -.5*mx80
native40 = next(row for row in rows if row['level']=='40x16')
record = dict(scope='SAVED_DEVELOPMENT_OUTPUTS_ONLY; no new numerical run or acceptance',
    inputs={name:dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            for name,path in paths.items()},
    paired=rows,
    native80=dict(executed_case='Mx', fy_executed=False, mx_pitch=mx80,
        predicted_fy_pitch=predicted, predicate='conditional reflection relation, not executed Fy'),
    binary_solid=dict(fy_pitch=solid_pitch, mx_pitch=fine['Mx']['observable']['rotation_components_rad'][1],
        reflection_residual_rad=solid_pitch+.5*fine['Mx']['observable']['rotation_components_rad'][1]),
    native40_fy_difference_fraction=abs(native40['native_fy_pitch']/solid_pitch-1.),
    predicted80_fy_difference_fraction=abs(predicted/solid_pitch-1.),
    native40_to80_cross_movement_fraction=abs(mx80/native40['native_mx_pitch']-1.),
    decisions=['Pitch is a physical cross-bending component, not removable by total-work normalization.',
        'Native discretization remains supported; reference residual and idealization error are not eliminated.',
        'Frozen converged1% criterion remains open; no extrapolated acceptance.',
        'No new Fy, finer mesh, factorization or formal F03 authority consumed.'])
(ROOT / 'next-mechanics-components-v1.json').open('x').write(json.dumps(record,indent=2)+'\n')
print(json.dumps({name:record[name] for name in (
    'native40_fy_difference_fraction','predicted80_fy_difference_fraction',
    'native40_to80_cross_movement_fraction')},indent=2))
