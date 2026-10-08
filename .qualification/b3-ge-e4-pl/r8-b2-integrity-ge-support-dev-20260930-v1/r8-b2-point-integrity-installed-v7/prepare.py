from pathlib import Path
import hashlib,json,shutil,subprocess,sys

w=Path('C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling')
previous=Path(__file__).parent/'r8-b2-point-integrity-installed-v6'
root=Path(__file__).parent/'r8-b2-point-integrity-installed-v7'
root.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
build=root/'build-source';build.mkdir()
for name in ('pyproject.toml','README.md','LICENSE','COPYRIGHT','THIRD_PARTY_NOTICES.md'):
    shutil.copy2(w/name,build/name)
shutil.copytree(w/'src',build/'src',ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.egg-info'))
for directory in ('tests','scripts','consumer-tests','wheels'):(root/directory).mkdir()
for p in (w/'tests').glob('*.py'):shutil.copy2(p,root/'tests'/p.name)
for name in ('probe_b3_ge_e4_pl_g0_f09_graph_reversal.py','experimental_stiffened_ge_bl5_reference_panel.py'):
    shutil.copy2(w/'scripts'/name,root/'scripts'/name)
for p in (previous/'consumer-tests').glob('*.py'):shutil.copy2(p,root/'consumer-tests'/p.name)
shutil.copy2(next((previous/'wheels').glob('anyfem-*.whl')),root/'wheels')
shutil.copy2(previous/'run_bounded.py',root/'run_bounded.py')
shutil.copy2(Path(__file__),root/'prepare.py')
(root/'pytest.ini').write_text('[pytest]\naddopts = -p no:cacheprovider\n')
source={p.relative_to(w).as_posix():sha(p) for p in (w/'src').rglob('*.py') if '__pycache__' not in p.parts}
(root/'source-manifest.json').write_text(json.dumps({'head':'e60d220e10c171e83141d0df0433a1149ae02f7d','source_sha256':source},indent=2)+'\n')
commands=[]
def call(argv,log):
    commands.append({'argv':argv,'cwd':str(root),'log':log})
    (root/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
    with (root/log).open('w') as out:
        subprocess.run([sys.executable,*argv],cwd=root,stdout=out,stderr=subprocess.STDOUT,check=True)
call(['-m','pip','wheel','--no-deps','--no-build-isolation','--no-cache-dir','--wheel-dir',str(root/'wheels'),str(build)],'build.log')
for p in sorted((root/'wheels').glob('*.whl')):
    call(['-m','pip','install','--no-deps','--no-compile','--no-cache-dir','--target',str(root/'site'),str(p)],p.stem+'-install.log')
fixtures={p.relative_to(root).as_posix():sha(p) for d in ('tests','scripts','consumer-tests') for p in (root/d).rglob('*.py')}
(root/'runners-manifest.json').write_text(json.dumps({'fixtures_sha256':fixtures,'wheels_sha256':{p.name:sha(p) for p in (root/'wheels').glob('*.whl')}},indent=2)+'\n')
print(json.dumps({'directory':str(root),'wheels':json.loads((root/'runners-manifest.json').read_text())['wheels_sha256']}))
