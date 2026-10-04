from pathlib import Path
import hashlib, json, sys

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
from scripts.r8_e02_double_output import compare_double_with_print
from scripts.r8_e02_distributing_feasibility import build_case, _hash

ROOT = Path(__file__).resolve().parent
binding = json.loads((ROOT/'binding-v2.json').read_text())
_, expected, area = build_case('Mx', 10, 4)
assert _hash(expected) == _hash(binding['original_metadata'])
assert hashlib.sha256((ROOT/'ccx/reference.inp').read_bytes()).hexdigest() == binding['deck_sha256']
execution = json.loads((ROOT/'ccx/execution-v2/execution.json').read_text())
assert execution['status'] == 'completed' and execution['exit_code'] == 0
assert not (ROOT/'ccx/execution-v2/stderr.log').read_text().strip()
sta = (ROOT/'ccx/reference.sta').read_text().splitlines()
assert len(sta) == 3 and sta[-1].split() == ['1','1','1','1','0.100000E+01','0.100000E+01','0.100000E+01']
result = compare_double_with_print((ROOT/'ccx/reference.frd').read_bytes(),
    (ROOT/'ccx/reference.dat').read_text(), (ROOT/'ccx/execution-v2/stdout.log').read_text(),
    expected, area)
result['sources'] = {p: hashlib.sha256((REPO/p).read_bytes()).hexdigest() for p in (
    'scripts/r8_e02_double_output.py', 'scripts/r8_e02_distributing_feasibility.py')}
result['inputs'] = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in (
    'binding-v2.json', 'ccx/reference.inp', 'ccx/reference.dat', 'ccx/reference.frd')}
(ROOT/'parsed-v1.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n', encoding='ascii')
print(json.dumps({k:result[k] for k in ('displacement_count','reaction_count',
    'printed_bound_max_fraction','root_wrench_error','external_final_pairing_J')}))
