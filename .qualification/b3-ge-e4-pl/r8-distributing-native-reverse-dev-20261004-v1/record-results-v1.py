from pathlib import Path
import hashlib, json, xml.etree.ElementTree as ET

root = Path(__file__).resolve().parent
repo = root.parents[2]
tangent = root.parent/'r8-distributing-native-tangent-dev-20261004-v1'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
def properties(path, key):
    tree = ET.parse(path)
    assert sum(int(s.get('failures', 0))+int(s.get('errors', 0))
               for s in tree.iter('testsuite')) == 0
    return [json.loads(p.get('value')) for p in tree.iter('property')
            if p.get('name') == key]
t = properties(tangent/'native-tangent-v4.xml', 'native_tangent')
r = properties(root/'native-reverse-v1.xml', 'native_reverse_flow')
assert len(t) == 2 and len(r) == 1
assert all(v['branch_masks_unchanged'] for v in t)
worst = max(e for v in t for values in v['relative_errors'].values() for e in values)
assert worst <= 1e-5
r = r[0]
assert len(r['negative_snapshot_reverse_flow_keys']) == 8 and r['exact_restart']
source = json.loads((root/'source-case-v1/history.json').read_text())
installed = json.loads((root/'installed-case-v1/history.json').read_text())
assert source == installed and len(installed) == 14
assert all(s['dissipation_j'] >= 0 for s in installed)
first = {}
for row in installed[:4]:
    for key, value in row['plastic_increments'].items():
        if value:
            first.setdefault(key, value)
negative = next(s for s in installed if s['factor'] == -1.)
reversed_keys = [k for k,v in negative['plastic_increments'].items()
                 if k in first and v*first[k] < 0.]
assert len(reversed_keys) == 8
for row in installed:
    assert (root/'source-case-v1'/row['checkpoint']).read_bytes() == (
        root/'installed-case-v1'/row['checkpoint']).read_bytes()
resources = {label:json.loads(path.read_text()) for label,path in (
    ('tangent',tangent/'installed-v4/execution.json'),
    ('reverse',root/'installed-v1/execution.json'))}
assert all(v['status'] == 'completed' and v['exit_code'] == 0
           and v['elapsed_seconds'] < 600 and v['sampled_peak_tree_bytes'] < 2*1024**3
           and v['affinity_before_child_code'] == [0] for v in resources.values())
bindings = {label: json.loads(path.read_text()) for label,path in (
    ('tangent',tangent/'installed-runtime-v4.json'),
    ('reverse',root/'installed-runtime-v1.json'))}
assert all(v['wheel']['sha256'] ==
    'f31527d54afd93d1a334dbbda545cb9affce847cfac94676fe9e8a2f6718847b'
    for v in bindings.values())
for stem, target in (
    ('report','docs/agent_plans/development/r8-distributing-reference-linear-20261004/results.md'),
    ('matrix','docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md'),
    ('active','docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md'),
    ('goal','docs/agent_plans/B3_GE_E4_PL_REVISION_8_GOAL.md'),
    ('plan','docs/agent_plans/B3_GE_E4_PL_REVISION_8_PLAN.md')):
    path = root/(stem+'-before-final-v1.bin')
    path.open('xb').write((repo/target).read_bytes())
record = dict(scope='development mechanics/lifecycle only; not aggregate qualification',
    tangent=t, worst_directional_group_relative_error=worst, reverse=r,
    identical_source_installed_histories=True, identical_accepted_checkpoints=14,
    negative_checkpoint_reverse_keys=reversed_keys, resources=resources,
    product_source_unchanged=True, bindings=bindings)
(root/'results-v1.json').open('x').write(json.dumps(record,indent=2)+'\n')
report = '''

## Native yielded derivatives and actual reverse flow - 4 October

Development checks on unchanged c5f5d79e product, installed solver wheel
f31527d54afd93d1a334dbbda545cb9affce847cfac94676fe9e8a2f6718847b.
No product equations, tolerances, driver limits, defaults or schemas changed.

Two grouped actual-update directional checks PASS18.12s. Pure fibre/Q4-J2
and simultaneous generalized/fibre/Q4-J2 states use a fixed yielded predecessor.
All tested shell, beam, retained and constraint groups have a finite-difference
plateau below1e-5; maximum over all measured steps2.57528643e-7. Activity masks
are unchanged. This one seeded direction is not every independent tangent column.
Repeated/restored assembly matches exactly; accepted recovery performs no trial
evaluation and preserves generation/history. Whole20.044s/sample181211136B.

Actual biaxial fibre reverse flow PASS81.71s on the existing small-force mixed
fixture, elastic Q4/generalized member and one low-yield physical-fibre member.
All eight initially yielding station keys have opposite nonzero plastic increments
at the -1 snapshot. Fourteen fixed load/unload/zero/reverse/reload positions complete;
beam dissipation0.014314952754535475J, equilibrium maximum3.797728887e-9 and
gap maximum1.395448146e-17. Negative-yielded restart/reload matches uninterrupted
execution exactly. Source and installed histories/all14 checkpoints are byte-identical.
Whole83.722s/sample181108736B. This is constitutive/lifecycle development evidence,
not engineering steel, shell-J2 reverse flow, physical panel capacity or G3 acceptance.

Failed tangent v2 inherited identity-path substitution (before pytest), v3 missing
generalized-only recovery-method test patch (1PASS/1FAIL), initial xunit2 property
warnings, all original test snapshots and logs remain. No solver defect resulted;
v4 uses the actual predecessor identity and physical-only recovery-method patch.
Supporting read review found no remaining defect; different-family scientific
acceptance remains OPEN. Affinity/pools1/JIToff and existing600s/2GiB limits verified.
No wheel rebuild/full204-case rerun: product and imported sources match prior
artifact bytes. Raw tangent/reverse roots retain exact runner, source/test, import,
resource, accepted-history and checkpoint identities.

Next mandatory slice: active-plastic/cyclic F06/V18 chart transport on the existing
mixed native POINT owner. Use admitted stage/rebase machinery and actual loaded
noncommuting rotations, material/energy, reactions and durable continuation.
Keep finite distributing chart admission excluded; do not add an optional operation.
Converged physical transfer, BL5/F03, external/scale/platform and aggregate gates
remain open. No automatic Fy/solid/adaptive/refinement campaign follows.
'''
with (repo/'docs/agent_plans/development/r8-distributing-reference-linear-20261004/results.md').open('ab') as out:
    out.write(report.encode('ascii'))
with (repo/'docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md').open('ab') as out:
    out.write(b'\n\nNative distributing derivatives/reverse flow,4 October: IMPLEMENTED_NOT_QUALIFIED.\n'
        b'Unchanged installed c5 product: two grouped smooth-branch actual-update tangent\n'
        b'checks pass (max2.5753e-7), including retained/multiplier work and fixed yielded\n'
        b'predecessors. Existing small-force biaxial fixture completes14positions;8same\n'
        b'fibre keys reverse at the restarted -1 snapshot, positive dissipation and exact\n'
        b'source/installed/restart histories pass. Elastic shell; no shell-plastic reversal\n'
        b'or engineering capacity claim. Full G3/F06/physical/independent acceptance OPEN.\n'
        b'[Evidence](development/r8-distributing-reference-linear-20261004/results.md).\n')
print(json.dumps(dict(tangent_cases=len(t), reverse_cases=1,
                     directional_error_max=worst, negative_reverse_keys=len(reversed_keys))))
