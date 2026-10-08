"""Non-numerical exact source/input freeze for one new API check."""
import ast
from hashlib import sha256
import json
from pathlib import Path

base = Path(__file__).parent
stem = base/'native_dynamic_interface_v3_20261001'
root = Path('C:/Users/AudunArnesenNyhus/.codex/worktrees/general-contact-native-dynamics/ANYsolver')
old = json.loads((base/'native_vibration_solve_control_v1_20261001.inputs.json').read_text())
source = dict(old['source_sha256'])
for path, expected in source.items():
    assert sha256(Path(path).read_bytes()).hexdigest() == expected, path
for relative in ('src/anysolver/ge_beam3_native_dynamics.py',
                 'src/anysolver/_ge_beam3_native_dynamic_analysis.py',
                 'tests/test_ge_beam3_native_dynamic_analysis.py',
                 'examples/native_contact_free_finite_velocity_dev.py'):
    path = str(root/relative)
    assert path not in source
    source[path] = sha256(Path(path).read_bytes()).hexdigest()
# Read the unchanged literal public policy without importing/evaluating mechanics.
tree = ast.parse((root/'src/anysolver/ge_beam3_native.py').read_text())
symbols = {}
for node in tree.body:
    if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name):
        name = node.targets[0].id
        if name in ('SELECTOR','PROFILE_ID'): symbols[name] = ast.literal_eval(node.value)
        if name == 'PROFILE_BYTES':
            call = node.value.args[0]
            policy = {kw.arg:(symbols[kw.value.id] if isinstance(kw.value,ast.Name)
                             else ast.literal_eval(kw.value)) for kw in call.keywords}
            old_profile = (json.dumps(policy,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
cache = Path(str(stem)+'.numba_cache'); cache.mkdir(exist_ok=False)
environment = {k:v for k,v in old['environment'].items() if k not in
               ('NUMBA_CACHE_DIR','PYTHONPATH','NATIVE_VIBRATION_INPUTS','NATIVE_VIBRATION_RAW_OUTPUT')}
environment.update(PYTHONPATH=';'.join(str(root/x) for x in ('src','tests','examples','.')),
    NUMBA_CACHE_DIR=str(cache),NATIVE_DYNAMIC_INTERFACE_INPUTS=str(stem)+'.inputs.json',
    NATIVE_DYNAMIC_INTERFACE_RAW_OUTPUT=str(stem)+'.raw.json')
inputs = dict(managed_worktree=str(root),source_sha256=source,environment=environment,
    old_public_profile_sha256=sha256(old_profile).hexdigest(),
    contract_sha256=sha256((base/'D6_NATIVE_MIDPOINT_DEVELOPMENT_20260930.md').read_bytes()).hexdigest(),
    maximum_accepted_steps=2,dt_seconds=.001,stage_residual_tolerance=1e-15,
    internal_time_limit_seconds=120,time_limit_seconds=180,memory_limit_bytes=1073741824,
    criteria=dict(step_and_cumulative_P_H_energy=1e-6,endpoint_algebraic=1e-11,elastic_witness=1e-10),
    pytest_args=['tests/test_ge_beam3_native_dynamic_analysis.py::test_two_step_native_dynamic_interface',
                 '-q','-s','--tb=short','--junitxml='+str(stem)+'.xml'])
input_path = Path(str(stem)+'.inputs.json')
with input_path.open('x') as out: out.write(json.dumps(inputs,indent=2)+'\n')
old_entry = (base/'native_vibration_solve_identity_v1_20261001.entry.source.py').read_text()
entry = old_entry.replace('native_vibration_solve_identity_v1_20261001','native_dynamic_interface_v3_20261001')
entry = entry.replace('89beb3c2f302ced5e5405e25beb2140d7cabc167a7d661b9713fa98f5cfa2e11',sha256(input_path.read_bytes()).hexdigest())
entry = entry.replace('import anysolver\n','import anysolver\nfrom anysolver.ge_beam3_native_dynamics import create_analysis\n')
entry = entry.replace("((MidpointContext, '_ge_beam3_native_midpoint.py'),",
                     "((create_analysis, 'ge_beam3_native_dynamics.py'),\n                        (MidpointContext, '_ge_beam3_native_midpoint.py'),")
entry_path = Path(str(stem)+'.entry.source.py')
with entry_path.open('x') as out: out.write(entry)
print(json.dumps(dict(source_count=len(source),input_sha256=sha256(input_path.read_bytes()).hexdigest(),
    entry_sha256=sha256(entry_path.read_bytes()).hexdigest(),contract_sha256=inputs['contract_sha256'],
    old_public_profile_sha256=inputs['old_public_profile_sha256'])))

