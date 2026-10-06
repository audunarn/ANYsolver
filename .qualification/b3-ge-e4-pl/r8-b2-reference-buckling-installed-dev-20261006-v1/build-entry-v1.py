"""Single offline host-created stage/wheel/install of committed B2 candidate."""
from pathlib import Path
from hashlib import sha256
import json,os,shutil,subprocess,sys,zipfile
RAW=Path(__file__).resolve().parent
REPO=RAW.parents[2]
COMMIT='71dfeddbcc2d4328b251220ffeb8779ee5f93408'
STAGE=RAW/'build-source-v1';WHEELS=RAW/'wheel-v1';TARGET=RAW/'installed-host-v1'
assert not STAGE.exists() and not WHEELS.exists() and not TARGET.exists()
accepted=json.loads((REPO/'.qualification/b3-ge-e4-pl/r8-b2-reference-buckling-dev-20261006-v1/worker-manifest-v1.json').read_text())
for entry in accepted['source_files']:
    assert sha256((REPO/entry['path']).read_bytes()).hexdigest()==entry['sha256'],entry['path']
STAGE.mkdir();WHEELS.mkdir()
metadata=('pyproject.toml','README.md','LICENSE','COPYRIGHT','THIRD_PARTY_NOTICES.md')
for name in metadata:shutil.copyfile(REPO/name,STAGE/name)
shutil.copytree(REPO/'src/anysolver',STAGE/'src/anysolver',ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.pyo','*.egg-info'))
source={path.relative_to(STAGE).as_posix():sha256(path.read_bytes()).hexdigest() for path in (STAGE/'src/anysolver').rglob('*') if path.is_file()}
for name in metadata:source[name]=sha256((STAGE/name).read_bytes()).hexdigest()
for name,digest in source.items():assert sha256((REPO/name).read_bytes()).hexdigest()==digest,name
(RAW/'source-package-binding-v1.json').write_text(json.dumps(dict(commit=COMMIT,files=source,frozen_source_bindings=accepted['source_files']),indent=2)+'\n')
commands=[[sys.executable,'-m','pip','wheel','--no-deps','--no-build-isolation','--no-index','--no-cache-dir','--wheel-dir',str(WHEELS),str(STAGE)]]
env=os.environ.copy();env['TEMP']=env['TMP']=str(RAW/'build-temp-v1');Path(env['TEMP']).mkdir()
(RAW/'build-commands-v1.json').write_text(json.dumps(commands,indent=2)+'\n')
subprocess.run(commands[0],cwd=STAGE,env=env,check=True)
wheels=list(WHEELS.glob('*.whl'));assert len(wheels)==1,wheels
wheel=wheels[0]
commands.append([sys.executable,'-m','pip','install','--no-deps','--no-index','--no-cache-dir','--no-compile','--target',str(TARGET),str(wheel)])
(RAW/'build-commands-v1.json').write_text(json.dumps(commands,indent=2)+'\n')
subprocess.run(commands[1],cwd=STAGE,env=env,check=True)
with zipfile.ZipFile(wheel) as archive:
    payload={name:sha256(archive.read(name)).hexdigest() for name in archive.namelist() if name.startswith('anysolver/') and not name.endswith('/')}
source_payload={name.removeprefix('src/'):digest for name,digest in source.items() if name.startswith('src/')}
assert payload==source_payload,'complete source/stage/wheel payload identity'
for name,digest in payload.items():assert sha256((TARGET/name).read_bytes()).hexdigest()==digest,name
installed={p.relative_to(TARGET).as_posix():sha256(p.read_bytes()).hexdigest() for p in (TARGET/'anysolver').rglob('*') if p.is_file()}
assert installed==payload,'complete installed payload identity'
provenance=dict(commit=COMMIT,version='0.4.7',wheel=str(wheel),wheel_sha256=sha256(wheel.read_bytes()).hexdigest(),installed_target=str(TARGET),source_package_file_count=len(source_payload),wheel_package_file_count=len(payload),installed_package_file_count=len(installed),payload=payload,commands=commands,source_stage_wheel_site_bytes_equal=True,host_created_stage_and_target=True)
(RAW/'artifact-provenance-v1.json').write_text(json.dumps(provenance,indent=2)+'\n')
print(json.dumps({key:value for key,value in provenance.items() if key not in ('payload','commands')},indent=2))
