from pathlib import Path
from hashlib import sha256
import json,ast
raw=Path('.qualification/b3-ge-e4-pl/r8-b2-reference-buckling-installed-dev-20261006-v1')
files=('tests/test_stiffened_shell_b2_reference_buckling.py','tests/test_stiffened_shell_b2_q4_panel_experimental.py','tests/test_b2_f09_physical_off_axis_elbow.py','tests/conftest.py','scripts/probe_b3_ge_e4_pl_g0_f09_graph_reversal.py','examples/stiffened_shell_b2_reference_buckling.py','pyproject.toml')
record={'commit':'71dfeddbcc2d4328b251220ffeb8779ee5f93408','files':{name:sha256(Path(name).read_bytes()).hexdigest() for name in files},'selection':'17 new buckling instances +2 existing public static dense-oracle instances','expected_cases':19,'original_source_manifest_sha256':sha256(Path('.qualification/b3-ge-e4-pl/r8-b2-reference-buckling-dev-20261006-v1/worker-manifest-v1.json').read_bytes()).hexdigest()}
(raw/'check-input-binding-v1.json').write_text(json.dumps(record,indent=2)+'\n')
for name in ('build-entry-v1.py','launch-build-v1.py','installed-entry-v1.py','launch-installed-v1.py'):
    ast.parse((raw/name).read_text(encoding='utf-8-sig'))
print(json.dumps({'bound_inputs':len(files),'entries_ast_passed':4,'artifact':json.loads((raw/'artifact-provenance-v1.json').read_text())['wheel_sha256'],'payload_count':json.loads((raw/'artifact-provenance-v1.json').read_text())['wheel_package_file_count']},indent=2))
