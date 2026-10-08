"""Save the exact grouped development inputs while the worker is not editing."""
from pathlib import Path
from hashlib import sha256
import json
ROOT=Path(__file__).resolve().parents[3];RAW=Path(__file__).resolve().parent
names=['src/anysolver/'+name+'.py' for name in (
    '_stiffened_shell_arc_control','_stiffened_shell_arc_trial',
    '_stiffened_shell_arc_checkpoint','_stiffened_shell_arc_publication',
    '_stiffened_shell_ge_experimental')]
names += ['tests/'+name+'.py' for name in (
    'test_stiffened_shell_native_arc','test_stiffened_shell_arc_chart',
    'test_stiffened_shell_arc_selection','test_stiffened_shell_arc_trial',
    'test_stiffened_shell_curved_arc','test_stiffened_shell_curved_material_arc')]
target=RAW/'source-grouped-v1';target.mkdir(exist_ok=False)
hashes={}
for name in names:
    content=(ROOT/name).read_bytes();output=target/name
    output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(content)
    hashes[name]=sha256(content).hexdigest()
(RAW/'source-grouped-inputs-v1.json').write_bytes((json.dumps(hashes,indent=2)+'\n').encode('ascii'))
print(f'Preserved {len(names)} exact grouped inputs.')
