from pathlib import Path
from math import fsum
import hashlib, json, xml.etree.ElementTree as ET

root = Path(__file__).resolve().parent
repo = root.parents[2]
sha = lambda b:hashlib.sha256(b).hexdigest()
runtime = json.loads((root/'installed-runtime-v1.json').read_text())
execution = json.loads((root/'installed-v1/execution.json').read_text())
proof = json.loads((root/'saved-proof-v1.json').read_text())
tree = ET.parse(root/'native-plastic-chart-v1.xml')
assert sum(int(s.get('tests',0)) for s in tree.iter('testsuite')) == 1
assert all(int(s.get('failures',0))+int(s.get('errors',0)) == 0 for s in tree.iter('testsuite'))
assert execution['status'] == 'completed' and execution['exit_code'] == 0
assert execution['elapsed_seconds'] < 600 and execution['sampled_peak_tree_bytes'] < 2*1024**3
assert execution['affinity_before_child_code'] == [0]
assert all(p['num_threads'] == 1 for p in runtime['pools'])
assert runtime['test_sha256'] == sha((root/'test-v2.py').read_bytes())
assert proof['test_sha256'] == sha((repo/'tests/test_stiffened_shell_native_plastic_chart.py').read_bytes())
assert proof['cross_cell_false_positive_rejected'] and proof['wrong_member_false_positive_rejected']
assert proof['actual_generation_increment'] == 1 and proof['prefix_actual_flow']
for name,digest in proof['data_sha256'].items():
    original = root/name
    archived = root/name.replace('pytest-v1/test_loaded_native_fibre_cycli0','accepted-states-v1',1)
    assert sha(original.read_bytes()) == digest == sha(archived.read_bytes())
records = {}
for label in ('prefix','control','reset','restored'):
    rows = []
    for folder in sorted((root/'accepted-states-v1').glob(label+'-*'),key=lambda p:int(p.name.split('-')[-1])):
        if not folder.is_dir():continue
        raw = json.loads((folder/'material.json').read_text())['result']
        balance = json.loads((folder/'balance.json').read_text())
        rows.append(dict(position=raw['load_position'],generation=raw['generation'],
            equilibrium=raw['free_equilibrium_ratio'],compatibility=raw['constraint_max'],
            last_increment_dissipation_j=sum(fsum(v['incremental_dissipation_j']) for v in raw['beam_fibre_energy']),
            stored_fibre_material_energy_j=sum(fsum(v['stored_energy_j']) for v in raw['beam_fibre_energy']),
            balance=balance))
    records[label] = rows
assert len(records['prefix']) == 4 and all(len(records[k]) == 8 for k in ('control','reset','restored'))
allrows = [v for rows in records.values() for v in rows]
assert all(v['equilibrium'] <= 1e-8 and v['compatibility'] <= 1e-9
           and v['last_increment_dissipation_j'] >= 0. for v in allrows)
scoped = dict(scope='native-fibre plastic/cyclic point chart transport development, not aggregate acceptance',
    installed_runtime=runtime,execution=execution,saved_same_cell_proof='saved-proof-v1.json',
    accepted_inventory=records, max_equilibrium=max(v['equilibrium'] for v in allrows),
    max_gap=max(v['compatibility'] for v in allrows),
    numerical_test='test-v2.py', strengthened_test='test-v3.py',
    no_mechanical_repeat=True, no_global_total_energy_claim=True)
(root/'results-v1.json').open('x').write(json.dumps(scoped,indent=2)+'\n')
for stem,target in (
    ('report','docs/agent_plans/development/r8-distributing-reference-linear-20261004/results.md'),
    ('matrix','docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md'),
    ('active','docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md'),
    ('goal','docs/agent_plans/B3_GE_E4_PL_REVISION_8_GOAL.md'),
    ('plan','docs/agent_plans/B3_GE_E4_PL_REVISION_8_PLAN.md')):
    (root/(stem+'-before-final-v1.bin')).open('xb').write((repo/target).read_bytes())
report = '''

## Loaded native-fibre plastic chart transport - 4 October

Existing POINT owner, elastic full-map Q4 and mixed elastic-generalized/physical
biaxial-fibre members. Same large-elastic geometry/supports and1MN beam bending,
then independent shell3/6 +/-375kN couple. Four-stage nonzero quarter-unload/
reload path; FY250MPa/H210GPa fibre law is an explicit constitutive control.
No shell-J2, reverse plastic flow, zero-load, capacity or global total-energy claim.

Installed1PASS149.48s on unchanged product wheel f31527d54afd93d1a334dbbda545cb9affce847cfac94676fe9e8a2f6718847b
and exact520 source/import identities. Whole151.758s/sample181776384B,
affinity/pools1/JIToff, unchanged600s/2GiB and20Newton/12backtrack/Adaptive(4,64).
Control/reset/chart-restored branches retain same12acceptedpositions, without
cutback: .125/.5/.75/1/1.125/1.5/1.75/2/2.5/3/3.5/4. Actual flow at reset1,
physical work balances/gaps, nonnegative native paired dissipation, cancellation/
stale-generation prefix preservation, exact same-event histories and durable
material/reaction/energy successor parity at registered typed-unit1e-9 pass.

Review identified a possible cross-cell false positive in the executed initial
coverage assertion. Original test-v2/XML retained. Stronger test-v3 matches
noncommutating rotation and actual plastic increments to the SAME fibre cell
and asserts chart generation+1. verify-saved-v1 validates exact retained byte-
bound numerical states, rejects cross-cell/wrong-member counterexamples and
passes matching positive control. No duplicate numerical campaign follows a
pure assertion strengthening. Both fibre cells are active/noncommuting at1.125
in every branch; cell commutators8.59425317e-5/1.46998243e-4rad. Actual generation
increment1. Control physical coverage: shell rotation.1230535644/commutator
.00064815997, fibre nodes.1035606403/.00047949745, fibre cells.09738150734/
.00039934079. All exceed unchanged.05rad/1e-5rad floors. Saved31snapshots plus
input/coverage retain every material origin, frame, reaction, force and checkpoint.

The zero endpoint was excluded BEFORE execution: point owner uses actual applied
load normalization and nonzero residual with zero applied load has infinite
ratio. This remaining point zero-load boundary is not a chart failure, relaxation
or a qualified unsupported-domain exclusion. No numerical zero trial was run.
Different-family scientific acceptance and aggregate F06/G3 remain OPEN.
Next ready material transport gap is simultaneous shell-J2/native-fibre loaded
chart behavior using this existing point-owner machinery; preserve partial-support,
curved/line/topology, total-energy and all external/scale/platform obligations.
'''
with (repo/'docs/agent_plans/development/r8-distributing-reference-linear-20261004/results.md').open('ab') as out:
    out.write(report.encode('ascii'))
with (repo/'docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md').open('ab') as out:
    out.write(b'\n\nF06/V18 loaded native-fibre plastic/cyclic POINT transport,4 October:\n'
        b'IMPLEMENTED_NOT_QUALIFIED. Installed1PASS;3branches share12acceptedpositions.\n'
        b'Reset at active predecessor1, matching-cell flow/noncommutation at1.125,\n'
        b'physical .05rad/1e-5rad floors, exact chart-event history/generation+1,\n'
        b'paired native energy/reaction/material restart parity and stale/cancel guards pass.\n'
        b'Pure assertion tightening verified from byte-bound saved states/counterexamples;\n'
        b'no mechanics rerun. Elastic Q4/generalized member; no shell-J2/zero-load/\n'
        b'capacity/global-energy or full F06/G3 acceptance. Independent family remains OPEN.\n'
        b'[Evidence](development/r8-distributing-reference-linear-20261004/results.md).\n')
print(json.dumps(dict(accepted_snapshots=len(allrows),max_equilibrium=scoped['max_equilibrium'],
                     max_gap=scoped['max_gap'], scoped_only=True)))
