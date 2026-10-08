from pathlib import Path
import hashlib,json,shutil,zipfile

temp=Path(__file__).resolve().parent
run=temp/'r8-bl5-finite-installed-v2'
repo=Path('C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling')
out=temp/'r8-bl5-finite-evidence'
out.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((run/'manifest.json').read_text())
assert all(sha(run/p)==h for p,h in manifest['inputs'].items())
with zipfile.ZipFile(out/'frozen-inputs.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(manifest['inputs']):z.write(run/p,p)
with zipfile.ZipFile(out/'installed-runtime.zip','w',zipfile.ZIP_DEFLATED) as z:
    for name in ('anysolver','anyfem'):
        for p in sorted((run/'site'/name).rglob('*.py')):
            z.write(p,p.relative_to(run/'site').as_posix())
with zipfile.ZipFile(out/'preparation-v1-partial.zip','w',zipfile.ZIP_DEFLATED) as z:
    old=temp/'r8-bl5-finite-installed-v1'
    for p in sorted(old.rglob('*')):
        if p.is_file():z.write(p,p.relative_to(old).as_posix())
for p in temp.glob('r8-bl5-finite-source-v*.log'):shutil.copy2(p,out/p.name)
for name in ('r8-bl5-finite-prepare.py','r8-bl5-finite-prepare-v2.log'):
    shutil.copy2(temp/name,out/name)
shutil.copy2(repo/'docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md',out/'active-note-before.md')
copied=out/'installed-v2';copied.mkdir(exist_ok=True)
for name in ('manifest.json','run_installed.py','run_bounded.py','pytest.ini',
             'build.log','install.log','identity.json','legacy.checkpoint'):
    if (run/name).exists():shutil.copy2(run/name,copied/name)
print(json.dumps({'out':str(out),'frozen_inputs':len(manifest['inputs']),
                 'runtime_modules':sum(1 for n in ('anysolver','anyfem') for p in (run/'site'/n).rglob('*.py')),
                 'archives':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in out.glob('*.zip')}},indent=2))
