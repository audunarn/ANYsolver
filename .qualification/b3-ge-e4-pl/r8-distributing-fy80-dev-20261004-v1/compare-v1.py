"""Interpret the single measured Fy80 case; no numerical solver is called."""
from pathlib import Path
import hashlib, json

ROOT = Path(__file__).resolve().parent
paths = {
    'native': ROOT / 'native-v2.json',
    'execution': ROOT / 'native-v2/execution.json',
    'paired': ROOT.parent / 'r8-distributing-multihost-dev-20261004-v1/paired-comparison-v1.json',
    'torque80': ROOT.parent / 'r8-distributing-native-adequacy-dev-20261004-v1/native.json',
    'solid': ROOT.parent / 'r8-e02-double-output-dev-20261004-v1/fine-comparison-v1.json',
    'solid_binding': ROOT.parent / 'r8-e02-double-output-dev-20261004-v1/fine-binding-v1.json',
}
data = {name:json.loads(path.read_text()) for name,path in paths.items()}
assert data['native']['status']=='COMPLETED_DEVELOPMENT_ONLY'
assert data['execution']['status']=='completed' and data['execution']['exit_code']==0
native = data['native']['native']
assert set(native['results'])=={'Fy'} and native['factors']==1
case = native['results']['Fy']
solid = data['solid']['results']['Fy']
pose = case['port_translation_m']+case['port_rotation_rad']
reference = solid['observable']['port_translation_m']+solid['observable']['rotation_components_rad']
assert all(value!=0. for value in reference)
relative = [(x-y)/y for x,y in zip(pose,reference)]
mx = data['torque80']['results']['Mx']
reflection = case['port_rotation_rad'][1]+.5*mx['port_rotation_rad'][1]
previous = data['paired']['levels']['40x16']['Fy']
old_pose = previous['native_port_translation_m']+previous['native_rotation_rad']
record = dict(scope='MEASURED_DEVELOPMENT_PAIR; not converged/aggregate qualification',
    source_binding=str(ROOT / 'binding-v2.json'),
    inputs={name:dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            for name,path in paths.items()},
    labels=('ux_m','uy_m','uz_m','roll_rad','pitch_rad','curl_rad'),
    native_pose=pose, solid_pose=reference,
    absolute_deltas=[x-y for x,y in zip(pose,reference)],
    relative_differences=relative,
    all_six_measured_differences_below_one_percent=all(abs(v)<.01 for v in relative),
    native40_to80_component_movement=[(x-y)/y for x,y in zip(pose,old_pose)],
    reflection_residual_rad=reflection,
    work_difference_relative=case['external_final_pairing_J']/solid['external_final_pairing_J']-1.,
    controls=case['controls'],
    decisions=['Retain declared reference-linear law for experimental development.',
        'No observed Fy/torque reflection or work-map defect in this fixture.',
        'Stop this diagnostic slice; no automatic further refinement.',
        'Native pitch moved2.03% despite pair agreement<1%; converged acceptance remains separate.',
        'Advance mandatory native-fibre material integration; do not relabel point/reference evidence as finite material qualification.'])
(ROOT / 'comparison-v1.json').open('x').write(json.dumps(record,indent=2,allow_nan=False)+'\n')
print(json.dumps({name:record[name] for name in ('relative_differences','reflection_residual_rad',
    'work_difference_relative','all_six_measured_differences_below_one_percent')},indent=2))
