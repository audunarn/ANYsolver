"""Single offline wheel/install from isolated accepted-source staging."""
from pathlib import Path
from hashlib import sha256
import json
import os
import shutil
import subprocess
import sys
import zipfile

RAW=Path(__file__).resolve().parent
REPO=RAW.parents[2]
COMMIT='c3950ae69dcc3fa14f97502f9eafb86a3a11276e'
STAGE=RAW/'build-source-v2'
WHEELS=RAW/'wheel-v2'
TARGET=RAW/'installed-v2'
assert not STAGE.exists() and not WHEELS.exists() and not TARGET.exists()
STAGE.mkdir();WHEELS.mkdir()
metadata=('pyproject.toml','README.md','LICENSE','COPYRIGHT','THIRD_PARTY_NOTICES.md')
for name in metadata:shutil.copyfile(REPO/name,STAGE/name)
shutil.copytree(REPO/'src/anysolver',STAGE/'src/anysolver',
    ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.pyo','*.egg-info'))
source={str(path.relative_to(STAGE)).replace('\\','/'):sha256(path.read_bytes()).hexdigest()
    for path in (STAGE/'src/anysolver').rglob('*') if path.is_file()}
for name in metadata:source[name]=sha256((STAGE/name).read_bytes()).hexdigest()
for name,digest in source.items():assert sha256((REPO/name).read_bytes()).hexdigest()==digest,name
(RAW/'source-package-binding-v2.json').write_text(json.dumps(dict(commit=COMMIT,files=source),indent=2)+'\n')
commands=[[sys.executable,'-m','pip','wheel','--no-deps','--no-build-isolation',
    '--no-index','--no-cache-dir','--wheel-dir',str(WHEELS),str(STAGE)]]
env=os.environ.copy()
env['TEMP']=env['TMP']=str(RAW/'build-temp-v2')
Path(env['TEMP']).mkdir()
(RAW/'build-commands-v2.json').write_text(json.dumps(commands,indent=2)+'\n')
subprocess.run(commands[0],cwd=STAGE,env=env,check=True)
wheels=list(WHEELS.glob('*.whl'));assert len(wheels)==1,wheels
wheel=wheels[0]
commands.append([sys.executable,'-m','pip','install','--no-deps','--no-index',
    '--no-cache-dir','--no-compile','--target',str(TARGET),str(wheel)])
(RAW/'build-commands-v2.json').write_text(json.dumps(commands,indent=2)+'\n')
subprocess.run(commands[1],cwd=STAGE,env=env,check=True)
with zipfile.ZipFile(wheel) as archive:
    payload={name:sha256(archive.read(name)).hexdigest() for name in archive.namelist()
        if name.startswith('anysolver/') and not name.endswith('/')}
for name,digest in payload.items():
    assert source['src/'+name]==digest,name
    assert sha256((TARGET/name).read_bytes()).hexdigest()==digest,name
source_python={name.removeprefix('src/') for name in source if name.startswith('src/') and name.endswith('.py')}
assert source_python=={name for name in payload if name.endswith('.py')}
provenance=dict(commit=COMMIT,version='0.4.7',wheel=str(wheel),
    wheel_sha256=sha256(wheel.read_bytes()).hexdigest(),
    source_package_file_count=len(source)-len(metadata),wheel_package_file_count=len(payload),
    installed_package_file_count=len(payload),source_python_module_count=len(source_python),
    payload=payload,commands=commands,source_wheel_site_bytes_equal=True)
(RAW/'artifact-provenance-v2.json').write_text(json.dumps(provenance,indent=2)+'\n')
print(json.dumps({key:value for key,value in provenance.items() if key not in ('payload','commands')},indent=2))
