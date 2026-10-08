from pathlib import Path
import hashlib
import json
from scripts.r8_e02_distributing_feasibility import parse_result

ROOT = Path(__file__).resolve().parent
native = json.loads((ROOT/'native-result-v2.json').read_text())
binding = json.loads((ROOT/'feasibility-binding-v2.json').read_text())
comparison = dict(scope='one coarse common-action pair, not convergence/accuracy/acceptance',cases={})
for name in ('Mx','Fy'):
    case = ROOT/('ccx-'+name+'-v2')
    if hashlib.sha256((case/'reference.inp').read_bytes()).hexdigest() != binding['cases'][name]['deck_sha256']:
        raise ValueError('changed executed deck')
    parsed = parse_result((case/'reference.dat').read_text(),
        (case/'execution/stdout.log').read_text(), json.loads((case/'metadata.json').read_text()))
    (case/'parsed-v1.json').open('x').write(json.dumps(parsed,indent=2)+'\n')
    base = parsed['external_final_pairing_J']
    candidate = native['results'][name]['external_final_pairing_J']
    comparison['cases'][name] = dict(native_pairing_J=candidate,solid_pairing_J=base,
        relative_pairing_difference=(candidate-base)/base,
        solid_pairing_print_bound_J=parsed['pairing_print_bound_J'],
        root_wrench_error=parsed['root_wrench_error'],
        root_wrench_print_bounds=parsed['root_wrench_print_bounds'],
        native_port_translation_m=native['results'][name]['port_translation_m'],
        solid_port_translation_m=parsed['observable']['port_translation_m'],
        native_rotation_rad=native['results'][name]['port_rotation_rad'],
        solid_rotation_rad=parsed['observable']['rotation_components_rad'])
(ROOT/'comparison-v1.json').open('x').write(json.dumps(comparison,indent=2)+'\n')
print(json.dumps(comparison))
