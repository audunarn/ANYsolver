from pathlib import Path
import shutil,subprocess,sys,json,hashlib,zipfile,tempfile
root=Path(tempfile.gettempdir())/'r8-anyfem-staged-installed-v2';root.mkdir(exist_ok=False)
fem=Path(r'C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer');solver=Path(r'C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling')
build=root/'build-source';build.mkdir();shutil.copytree(fem/'src',build/'src',ignore=shutil.ignore_patterns('__pycache__','*.egg-info'))
for name in ('pyproject.toml','README.md','LICENSE','NOTICE','THIRD_PARTY_NOTICES.md','dependency-licenses.json','docs/LICENSE.md'):
 target=build/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(fem/name,target)
fixtures=root/'fixtures';fixtures.mkdir()
for name in ('test_stiffened_shell_staged_load_consumer.py','test_stiffened_shell_project.py','test_experimental_stiffened_shell_consumer.py'):
 shutil.copyfile(fem/'tests'/name,fixtures/name)
(root/'pytest.ini').write_text('[pytest]\naddopts = -ra -p no:cacheprovider\n')
with (root/'build.log').open('w') as out:subprocess.run([sys.executable,'-m','pip','wheel','--no-cache-dir','--no-build-isolation','--no-deps','--wheel-dir',str(root/'wheels'),str(build)],stdout=out,stderr=subprocess.STDOUT,check=True)
solverwheel=next((Path(tempfile.gettempdir())/'r8-staged-load-installed-v1/wheels').glob('anysolver-*.whl'))
shutil.copyfile(solverwheel,root/'wheels'/solverwheel.name)
with (root/'install.log').open('w') as out:subprocess.run([sys.executable,'-m','pip','install','--no-cache-dir','--no-deps','--no-compile','--target',str(root/'site'),*[str(x) for x in (root/'wheels').glob('*.whl')]],stdout=out,stderr=subprocess.STDOUT,check=True)
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
modules={name:{name+'/'+x.relative_to(src).as_posix():sha(x) for x in src.rglob('*.py')} for name,src in [('anysolver',solver/'src/anysolver'),('anyfem',fem/'src/anyfem')]}
(root/'input-manifest.json').write_text(json.dumps({'source_heads':{'anysolver':'9f1f5a10bf4059f2f7362c345316131311ed25ae','anyfem':'6226230d0395bb917f88ca2271157d528bf05e20'},'modules':modules,'wheels':{x.name:sha(x) for x in (root/'wheels').glob('*.whl')},'fixtures':{x.name:sha(x) for x in fixtures.glob('*.py')},'scope':'installed staged consumer slice, no qualification or speedup'},indent=2))
print(json.dumps({'wheels':{x.name:sha(x) for x in (root/'wheels').glob('*.whl')},'modules':{k:len(v) for k,v in modules.items()}}))
