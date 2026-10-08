"""Reinterpret unchanged completed raw control; retain original parser failure."""
from pathlib import Path
import hashlib, importlib.util, json

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
SOURCE = REPO/'scripts/r8_e04_ccx_restricted_membrane.py'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
spec = importlib.util.spec_from_file_location('ccx_control_adjudication', SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
RAW = ROOT/'inverse-control-v1'
OUT = ROOT/'inverse-control-adjudicated-v2'
OUT.mkdir(exist_ok=False)
status = json.loads((RAW/'status.json').read_text())
assert status['returncode'] == 0
assert status['deck_sha256'] == sha(RAW/'reference.inp')
assert status['deck_sha256'] == hashlib.sha256(m.deck('full', inverse_elastic_control=True).encode('ascii')).hexdigest()
m.clean_execution(status['returncode'], (RAW/'stdout.log').read_text(), (RAW/'stderr.log').read_text())
record, = m.parse_dat((RAW/'reference.dat').read_text(), 'full', endpoint_count=1)
inventory = m.parse_sta((RAW/'reference.sta').read_text(), 'full', endpoint_count=1)
assert inventory['matched_one_increment_per_native_target']
boundary = m.verify_inverse_boundary(record, m.elastic_patch_strain()*m.patch.LENGTH)
observed = m.inverse_observables(record, m.patch.TARGETS[0], elastic_control=True)
observed.update(boundary)
observed['balance_checks'] = m.balance_checks(observed)
m.validate_balances(observed)
m.save(OUT/'control.json', observed)
m.save(OUT/'increments.json', inventory)
for key in ('error_type', 'error', 'failed_iteration_summary'):
    status.pop(key, None)
status.update(status='COMPLETED_INVERSE_CONTROL', imposed_boundary_verified=True,
    imposed_strain_scored=False, parser_source_sha256=sha(SOURCE),
    adjudicator_sha256=sha(__file__), raw_execution_directory=str(RAW),
    raw_files_sha256={name: sha(RAW/name) for name in
        ('status.json', 'reference.inp', 'reference.dat', 'reference.sta', 'stdout.log', 'stderr.log')},
    original_parser_failure_preserved=True, physical_execution_repeated=False)
m.save(OUT/'status.json', status)
print(json.dumps(dict(status=status['status'], force_n=observed['actual_actuator_force_n'],
    checks=observed['balance_checks'], imposed_boundary_verified=True)))
