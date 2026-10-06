"""Preserve reviewed DEV source and exact named raw artifacts; no numerical run."""
from pathlib import Path
import hashlib
import json
import subprocess

raw = Path(__file__).resolve().parent
repo = raw.parents[2]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
load = lambda name: json.loads((raw / name).read_text())
v1 = load('raw-artifact-sha256.json')['artifacts']
v2 = load('raw-artifact-sha256-v2.json')['artifacts']
assert all(v2[name] == expected for name, expected in v1.items())
for name, expected in v2.items():
    p = raw / name
    assert p.resolve().is_relative_to(raw.resolve()), name
    assert p.stat().st_size == expected['bytes'] and sha(p) == expected['sha256'], name
old, latest = load('handoff.json'), load('handoff-v2.json')
source = {name: old['source_sha256'][name] for name in old['changed_product_files']}
source.update(latest['source_sha256'])
for name, expected in source.items():
    assert sha(repo / name) == expected, name
assert not latest['owned_numerical_processes']
extra = ('raw-artifact-sha256.json', 'raw-artifact-sha256-v2.json', 'handoff-v2.json',
         'independent-review-v2.md', 'root-inspection-failure-v2.json',
         'root-integration-verifier-v2.py', 'root-integration-binding-v2.json',
         'root-integration-disposition-v3.md', 'root-preservation-v3.py')
artifacts = dict(v2)
for name in extra:
    p = raw / name
    actual = dict(bytes=p.stat().st_size, sha256=sha(p))
    assert name not in artifacts or artifacts[name] == actual
    artifacts[name] = actual
manifest_name = 'root-preservation-manifest-v3.json'
manifest = raw / manifest_name
assert not manifest.exists(), 'Do not overwrite a preserved inventory'
manifest.write_bytes((json.dumps(dict(scope='Partial experimental preservation; no scientific acceptance',
    original760_preserved=True, artifacts=artifacts, final_source_sha256=source,
    wheel_sha256=latest['installed_input']['sha256']), indent=2) + '\n').encode())
matrix = repo / 'docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md'
old_matrix = matrix.read_bytes()
assert old_matrix == subprocess.check_output(['git', 'show', 'HEAD:' + matrix.relative_to(repo).as_posix()], cwd=repo)
entry = b'''\n\n## 6 October 2026 - native BL5 material lifecycle, partial DEV preservation\n\nIMPLEMENTED_NOT_QUALIFIED: separate Q4 native-fibre material identity, real fibre\nplasticity/recovery and atomic prefix/restart/cancellation/refusal behavior. Four\nrestore admission gaps repaired. Installed partial route and final-report\nregression verified against wheel ca2503e2178aa536b79d556a2c105faef29977f6d7a1442e989bddde077cd849;\n424 source/site/wheel module identities and244 actual imports. Historical impact\ncoverage remains scoped to executed controls. Original760 raw paths preserved;\nV2 has779. Exact source, reviews, failures and checks: material-dev-20261006-v1\nroot-preservation-manifest-v3.json and root-integration-disposition-v3.md.\n\nOPEN/FAILED: strict full .5/1 histories remain visible and unpassed; corrected-CI\ncontinuation accepts through.284375, then fails.3125 before shell yielding.\nWhole-free-KKT failed-trial directional errors do not meet1e-5. Safeguarded\nquadratic candidate failed and was removed; original dyadic dispatch restored.\nNo simultaneous shell/fibre, physical-limit, convergence or aggregate G3 claim.\nFinal partial example.25625/gen4 reports actual fibre alpha1.2678570601992559e-6,\nshell alpha0. No qualification, main change, merge, publication or F03 consumption.\nNext: saved rejected-trial work/chart/branch/precision interpretation, no automatic\ncontinuation, fixture, strength, globalization or refinement sweep.\n'''
matrix.write_bytes(old_matrix + entry)
assert matrix.read_bytes().startswith(old_matrix)
paths = list(source) + ['.gitattributes', matrix.relative_to(repo).as_posix(),
    'docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md']
paths += [(raw / name).relative_to(repo).as_posix() for name in artifacts]
paths.append(manifest.relative_to(repo).as_posix())
paths = sorted(set(paths))
for start in range(0, len(paths), 24):
    subprocess.run(['git', '-c', 'core.longpaths=true', 'add', '-f', '--', *paths[start:start+24]], cwd=repo, check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
for name, expected in source.items():
    assert hashlib.sha256(subprocess.check_output(['git', 'show', ':' + name], cwd=repo)).hexdigest() == expected, name
for name, expected in artifacts.items():
    path = (raw / name).relative_to(repo).as_posix()
    assert hashlib.sha256(subprocess.check_output(['git', 'show', ':' + path], cwd=repo)).hexdigest() == expected['sha256'], path
subprocess.run(['git', 'diff', '--cached', '--check'], cwd=repo, check=True)
print(json.dumps(dict(staged_paths=len(paths), raw_artifacts=len(artifacts),
    source_files=len(source), original760_preserved=True, matrix_prefix_preserved=True,
    installed_partial_verified=True, full_material_gate=False, disposition='PARTIAL_NOT_MERGE_READY')))
