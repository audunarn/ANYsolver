from pathlib import Path
from hashlib import sha256
import json,os,shutil,subprocess,sys,time,zipfile
RAW=Path(__file__).resolve().parent;REPO=RAW.parents[2]
PLAN=json.loads((RAW/'plan-v1.json').read_text());STAGE=RAW/'build-source-v1';WHEELS=RAW/'wheel-v1';TARGET=RAW/'installed-host-v1'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()==PLAN['commit']
assert all(p.is_dir() and not any(p.iterdir()) for p in (STAGE,WHEELS,TARGET))
source={**PLAN['package_inventory'],**PLAN['metadata']}
for name,digest in source.items():
    assert sha256((REPO/name).read_bytes()).hexdigest()==digest,name
    target=STAGE/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(REPO/name,target)
    assert sha256(target.read_bytes()).hexdigest()==digest,name
(RAW/'source-stage-binding-v1.json').write_text(json.dumps(dict(commit=PLAN['commit'],source=source,source_stage_bytes_equal=True),indent=2)+'\n')
env=os.environ.copy();env['TEMP']=env['TMP']=str(RAW/'build-temp-v1');Path(env['TEMP']).mkdir()
commands=[[sys.executable,'-m','pip','wheel','--no-deps','--no-build-isolation','--no-index','--no-cache-dir','--wheel-dir',str(WHEELS),str(STAGE)]]
records=[]
def run(command):
    started=time.monotonic();code=subprocess.run(command,cwd=STAGE,env=env).returncode
    records.append(dict(command=command,elapsed_seconds=time.monotonic()-started,exit_code=code))
    (RAW/'build-commands-v1.json').write_text(json.dumps(records,indent=2)+'\n')
    if code:raise RuntimeError('offline build/install failed')
run(commands[0]);wheels=list(WHEELS.glob('*.whl'));assert len(wheels)==1
wheel=wheels[0];assert wheel.name=='anysolver-0.4.7-py3-none-any.whl',wheel.name
commands.append([sys.executable,'-m','pip','install','--no-deps','--no-index','--no-cache-dir','--no-compile','--target',str(TARGET),str(wheel)])
run(commands[1])
with zipfile.ZipFile(wheel) as archive:
    payload={n:sha256(archive.read(n)).hexdigest() for n in archive.namelist() if n.startswith('anysolver/') and not n.endswith('/')}
source_payload={n.removeprefix('src/'):d for n,d in PLAN['package_inventory'].items()}
assert payload==source_payload,'complete source/stage/wheel payload identity'
installed={p.relative_to(TARGET).as_posix():sha256(p.read_bytes()).hexdigest() for p in (TARGET/'anysolver').rglob('*') if p.is_file()}
assert installed==payload,'complete installed package identity'
for n,d in payload.items():assert sha256((REPO/'src'/n).read_bytes()).hexdigest()==d
record=dict(commit=PLAN['commit'],version='0.4.7',wheel=wheel.relative_to(RAW).as_posix(),wheel_sha256=sha256(wheel.read_bytes()).hexdigest(),installed_target=TARGET.relative_to(RAW).as_posix(),source_package_file_count=len(source_payload),wheel_package_file_count=len(payload),installed_package_file_count=len(installed),payload=payload,source_stage_wheel_installed_bytes_equal=True,command_receipts=records)
(RAW/'artifact-provenance-v1.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k not in ('payload','command_receipts')},indent=2))
