"""Preserve terminal portable development records and final source identities."""
from pathlib import Path
from hashlib import sha256
import json,shutil
ROOT=Path(__file__).resolve().parents[3];RAW=Path(__file__).resolve().parent
for label,folder in (('source-initial-v1','anysolver-portable-ci-yk9vh6f0'),
                     ('source-grouped-v1-records','anysolver-portable-ci-atne4hwe')):
    source=Path('C:/Users/AudunArnesenNyhus/AppData/Local/Temp')/folder/'P01'
    resource=json.loads((source/'resource.json').read_bytes())
    assert resource['status']=='terminal' and resource['child_exit_codes']==[0]
    dest=RAW/label;dest.mkdir(exist_ok=False)
    for path in source.iterdir():
        if path.is_file():shutil.copyfile(path,dest/path.name)
names=list(json.loads((RAW/'source-grouped-inputs-v1.json').read_bytes()))
names+=['examples/stiffened_shell_native_arc.py','docs/stiffened_shell_arc_development.md']
hashes={name:sha256((ROOT/name).read_bytes()).hexdigest() for name in names}
(RAW/'source-final-inputs-v1.json').write_bytes((json.dumps(hashes,indent=2)+'\n').encode('ascii'))
print('Preserved two terminal source runs and final source/test identities.')
