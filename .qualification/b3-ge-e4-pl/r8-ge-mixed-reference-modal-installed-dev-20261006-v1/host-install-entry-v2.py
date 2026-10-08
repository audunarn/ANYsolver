"""Host-readable target from the same immutable V2 wheel; no rebuild."""
from pathlib import Path
from hashlib import sha256
import json
import os
import subprocess
import sys

RAW=Path(__file__).resolve().parent
REPO=RAW.parents[2]
original=json.loads((RAW/'artifact-provenance-v2.json').read_text())
wheel=Path(original['wheel'])
assert sha256(wheel.read_bytes()).hexdigest()==original['wheel_sha256']
target=RAW/'installed-host-v2';assert not target.exists()
env=os.environ.copy()
env['TEMP']=env['TMP']=str(RAW/'host-install-temp-v2')
Path(env['TEMP']).mkdir()
command=[sys.executable,'-m','pip','install','--no-deps','--no-index','--no-cache-dir',
    '--no-compile','--target',str(target),str(wheel)]
subprocess.run(command,cwd=RAW,env=env,check=True)
for name,digest in original['payload'].items():
    assert sha256((target/name).read_bytes()).hexdigest()==digest,name
    assert sha256((REPO/'src'/name).read_bytes()).hexdigest()==digest,name
original.update(installed_target=str(target),host_install_command=command,
    reason='Sandbox-created pip target cannot be read by host; identical wheel installed into new host-created target without rebuilding',
    host_installed_payload_count=len(original['payload']),host_source_wheel_site_bytes_equal=True)
(RAW/'host-artifact-provenance-v2.json').write_text(json.dumps(original,indent=2)+'\n')
print(json.dumps(dict(commit=original['commit'],wheel_sha256=original['wheel_sha256'],
    installed_target=str(target),host_installed_payload_count=len(original['payload']),
    host_source_wheel_site_bytes_equal=True),indent=2))
