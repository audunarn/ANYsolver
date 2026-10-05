from pathlib import Path
import hashlib,json,shutil,subprocess,sys
source=Path('C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling')
root=Path(__file__).parent/'r8-ge-fibre-finite-installed-v1'
root.mkdir(exist_ok=False)
build=root/'build-source'; build.mkdir()
shutil.copytree(source/'src',build/'src',ignore=shutil.ignore_patterns('__pycache__','*.egg-info'))
for name in ('pyproject.toml','README.md','LICENSE','COPYRIGHT','THIRD_PARTY_NOTICES.md'):
    shutil.copy2(source/name,build/name)
tests=root/'tests';tests.mkdir()
for name in ('test_stiffened_shell_ge_experimental.py','test_stiffened_shell_ge_finite_experimental.py','test_stiffened_shell_ge_physical_fibre_linear.py','test_stiffened_shell_ge_physical_fibre_finite.py'):
    shutil.copy2(source/'tests'/name,tests/name)
scripts=root/'scripts';scripts.mkdir()
for name in ('experimental_stiffened_ge_panel.py','experimental_stiffened_ge_fibre_history.py'):
    shutil.copy2(source/'scripts'/name,scripts/name)
(root/'pytest.ini').write_text('[pytest]\naddopts = -ra -p no:cacheprovider\n')
with (root/'build.log').open('w') as log:
    subprocess.run([sys.executable,'-m','pip','wheel','--no-build-isolation','--no-deps','--wheel-dir',str(root/'wheels'),str(build)],stdout=log,stderr=subprocess.STDOUT,check=True)
wheel=root/'wheels/anysolver-0.4.7-py3-none-any.whl'
consumer=source/'.qualification/b3-ge-e4-pl/r8-ge-fibre-linear-dev-20260930-v1/solver/wheels/anyfem-0.4.1-py3-none-any.whl'
shutil.copy2(consumer,root/'wheels'/consumer.name)
with (root/'install.log').open('w') as log:
    subprocess.run([sys.executable,'-m','pip','install','--no-deps','--no-compile','--target',str(root/'site'),str(wheel),str(root/'wheels'/consumer.name)],stdout=log,stderr=subprocess.STDOUT,check=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest={'source_head':'b52a3a5ac92c255989cf0076b316b335ead9c2f5','candidate':'dirty native history slice','wheels':{p.name:sha(p) for p in (root/'wheels').glob('*.whl')},'inputs':{p.relative_to(root).as_posix():sha(p) for folder in (tests,scripts) for p in folder.glob('*.py')}}
(root/'manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest['wheels']))
