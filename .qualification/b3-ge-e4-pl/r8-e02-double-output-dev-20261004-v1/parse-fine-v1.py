from pathlib import Path
import hashlib, json, math, sys
ROOT = Path(__file__).resolve().parent; REPO = ROOT.parents[2]
sys.path.insert(0, str(REPO))
from scripts.r8_e02_double_output import compare_double_with_print
from scripts.r8_e02_distributing_solid_area import compile_area_map

binding = json.loads((ROOT/'fine-binding-v1.json').read_text())
for rel, sha in binding['sources'].items():
    assert hashlib.sha256((REPO/rel).read_bytes()).hexdigest() == sha
old_dir = ROOT.parent/'r8-distributing-thickness-dev-20261004-v1'
old = json.loads((old_dir/'comparison-v5.json').read_text())
native_path = ROOT.parent/'r8-distributing-native-adequacy-dev-20261004-v1/comparison.json'
native = json.loads(native_path.read_text())
results = {}
for name in ('Mx','Fy'):
    case = ROOT/('fine-'+name+'-v1'); pin = binding['cases'][name]
    assert hashlib.sha256((case/'reference.inp').read_bytes()).hexdigest() == pin['deck_sha256']
    assert hashlib.sha256((case/'metadata.json').read_bytes()).hexdigest() == pin['metadata_sha256']
    event = json.loads((case/'execution-v1/execution.json').read_text())
    assert event['status'] == 'completed' and event['exit_code'] == 0
    assert not (case/'execution-v1/stderr.log').read_text().strip()
    assert (case/'reference.sta').read_text().splitlines()[-1].split() == ['1','1','1','1','0.100000E+01','0.100000E+01','0.100000E+01']
    meta = json.loads((case/'metadata.json').read_text())
    nodes = {int(n):p for n,p in meta['physical_nodes'].items()}
    elements = {int(e):v for e,v in meta['elements'].items()}
    area = compile_area_map(nodes, elements, meta['bounds_xy_m'], meta['thickness_m'], meta['port_m'])
    assert area.identity == meta['area_map_identity']
    result = compare_double_with_print((case/'reference.frd').read_bytes(),
        (case/'reference.dat').read_text(), (case/'execution-v1/stdout.log').read_text(), meta, area)
    length = binding['balance_screen']['length_m']; force = binding['balance_screen']['force_N'][name]
    result['scaled_balance_linf'] = max(abs(e)/(force if j<3 else force*length)
        for j,e in enumerate(result['root_wrench_error']))
    result['balance_screen_satisfied'] = result['scaled_balance_linf'] <= binding['balance_screen']['limit']
    result['dat_byte_identical_to_prior'] = (case/'reference.dat').read_bytes() == (old_dir/('ccx-'+name+'-v5')/'reference.dat').read_bytes()
    work = result['external_final_pairing_J']
    result['work_change_from_saved_decimal_relative'] = (work-old['results'][name]['new_solid_pairing_J'])/old['results'][name]['new_solid_pairing_J']
    native_work = (native['results']['Mx']['new_native_work_J'] if name=='Mx'
        else old['results']['Fy']['native_pairing_J'])
    result['saved_native_pairing_J'] = native_work
    result['saved_native_reference_work_difference_relative'] = (native_work-work)/work
    # Check actual rounded CLOAD wrench separately from its intended continuum action.
    loads = (case/'reference.inp').read_text().split('*CLOAD\n')[1].split('*NODE PRINT')[0]
    terms = []
    for line in loads.splitlines():
        n,j,v = line.split(','); p = nodes[int(n)]; f = [0.,0.,0.]; f[int(j)-1] = float(v)
        terms.append(tuple(f)+(p[1]*f[2]-p[2]*f[1], p[2]*f[0]-p[0]*f[2], p[0]*f[1]-p[1]*f[0]))
    applied = tuple(math.fsum(t[j] for t in terms) for j in range(6))
    result['deck_applied_wrench_about_origin'] = applied
    result['root_plus_actual_deck_wrench'] = tuple(a+b for a,b in zip(result['root_wrench_about_origin'], applied))
    result['inputs'] = {p:hashlib.sha256((case/p).read_bytes()).hexdigest() for p in ('reference.inp','reference.frd','reference.dat','metadata.json')}
    result['execution_elapsed_seconds'] = event['elapsed_seconds']
    result['sampled_peak_tree_bytes'] = event['sampled_peak_tree_bytes']
    result['sampled_numeric_or_unresolved_max'] = event['sampled_numeric_or_unresolved_max']
    results[name] = result
record = dict(scope='OUTPUT_ONLY_DEVELOPMENT: no law/convergence/aggregate acceptance',
    binding_sha256=hashlib.sha256((ROOT/'fine-binding-v1.json').read_bytes()).hexdigest(),
    saved_native_comparison_sha256=hashlib.sha256(native_path.read_bytes()).hexdigest(),
    prior_thickness_comparison_sha256=hashlib.sha256((old_dir/'comparison-v5.json').read_bytes()).hexdigest(),
    results=results)
(ROOT/'fine-comparison-v1.json').write_text(json.dumps(record, indent=2, allow_nan=False)+'\n', encoding='ascii')
print(json.dumps({n:{k:r[k] for k in ('scaled_balance_linf','balance_screen_satisfied',
    'dat_byte_identical_to_prior','external_final_pairing_J','saved_native_reference_work_difference_relative',
    'sampled_numeric_or_unresolved_max')} for n,r in results.items()}))
