from pathlib import Path
from hashlib import sha256
import ast, json, shutil, subprocess, sys
work=Path('C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling')
temp=Path('C:/Users/AudunArnesenNyhus/AppData/Local/Temp')
prior=temp/'r8-adaptive-installed-v1'
root=temp/'r8-bl5-finite-installed-v3'
if root.exists(): raise FileExistsError(root)
root.mkdir()
build=root/'build-source';build.mkdir()
for p in (prior/'build-source').iterdir():
    if p.is_file(): shutil.copyfile(p,build/p.name)
for name in ['pyproject.toml','setup.py','setup.cfg','README.md','LICENSE']:
    if (work/name).exists():shutil.copyfile(work/name,build/name)
shutil.copytree(work/'src',build/'src',ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.egg-info'))
for name in ['tests','docs','scripts']:
    shutil.copytree(prior/name,root/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
todo=['tests/test_stiffened_shell_bl5_finite.py',
      'tests/test_stiffened_shell_bl5_local_experimental.py',
      'tests/test_stiffened_shell_l1_assembly_experimental.py',
      'scripts/experimental_stiffened_ge_bl5_history.py']
copied=set()
while todo:
    name=todo.pop()
    if name in copied:continue
    source=work/name
    if not source.exists():raise FileNotFoundError(source)
    dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
    copied.add(name)
    for node in ast.walk(ast.parse(source.read_text(encoding='utf-8-sig'))):
        modules=([node.module] if isinstance(node,ast.ImportFrom) and node.module else
                 [alias.name for alias in node.names] if isinstance(node,ast.Import) else [])
        for module in modules:
            if module.startswith('scripts.') or module.startswith('docs.'):
                path=module.replace('.','/')+'.py'
                if (work/path).exists():todo.append(path)
            elif module.startswith('test_'):
                path='tests/'+module+'.py'
                if (work/path).exists():todo.append(path)
for name in ['pytest.ini','legacy.checkpoint','run_bounded.py']:
    shutil.copyfile(prior/name,root/name)
runner=(prior/'run_installed.py').read_text(encoding='utf-8')
runner=runner.replace("selected=[root/\"tests\"/name for name in [",
    "selected=[root/\"tests\"/name for name in ['test_stiffened_shell_bl5_finite.py','test_stiffened_shell_bl5_local_experimental.py','test_stiffened_shell_l1_assembly_experimental.py',")
needle="reports={}"
example="""reports={}
from scripts.experimental_stiffened_ge_bl5_history import run as line_example
for basis in ('p0','continuous_p1_coarse'):
    report=line_example(basis)
    assert report['status']=='completed' and report['restart_bytes_equal']
    assert Path(report['source']).resolve().is_relative_to(site)
    reports[basis]=report
(root/'examples.json').write_text(json.dumps(reports,indent=2))
"""
assert needle in runner;runner=runner.replace(needle,example)

runner=runner.replace("Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer/src/anyfem')", "Path("+repr(str(temp/'r8-bl5-finite-installed-v2/site/anyfem'))+")")
start=runner.index('selected=')
end=runner.index('code=pytest.main',start)
runner=runner[:start]+'''selected=[root/'tests/test_stiffened_shell_bl5_finite.py',
    str(root/'tests/test_stiffened_shell_ge_physical_fibre_finite.py')+'::test_finite_native_response_restart_and_predecessor',
    str(root/'tests/test_stiffened_shell_ge_physical_fibre_linear.py')+'::test_physical_fibre_legacy_finite_checkpoints_reject_without_state_change']
'''+runner[end:]

(root/'run_installed.py').write_text(runner)
wheels=root/'wheels';wheels.mkdir()
with (root/'build.log').open('w') as log:
    subprocess.run([sys.executable,'-m','pip','wheel','--no-cache-dir','--no-build-isolation',
        '--no-deps','--wheel-dir',str(wheels),str(build)],stdout=log,stderr=subprocess.STDOUT,check=True)
consumer=next((prior/'wheels').glob('anyfem-*.whl'));shutil.copyfile(consumer,wheels/consumer.name)
with (root/'install.log').open('w') as log:
    subprocess.run([sys.executable,'-m','pip','install','--no-cache-dir','--no-deps','--no-compile',
        '--target',str(root/'site')]+[str(p) for p in wheels.glob('*.whl')],
        stdout=log,stderr=subprocess.STDOUT,check=True)
inputs={str(p.relative_to(root)).replace('\\','/'):sha256(p.read_bytes()).hexdigest()
    for name in ['tests','docs','scripts'] for p in (root/name).rglob('*') if p.is_file()}
for name in ['run_installed.py','run_bounded.py','legacy.checkpoint','pytest.ini']:
    inputs[name]=sha256((root/name).read_bytes()).hexdigest()
manifest={'source':'e64db0e5 plus reviewed experimental finite BL5/V11',
          'wheels':{p.name:sha256(p.read_bytes()).hexdigest() for p in wheels.glob('*.whl')},
          'inputs':inputs,'new_fixture_closure':sorted(copied),
          'classification':'experimental installed development, not F03/G2 acceptance'}
(root/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True))
print(json.dumps({'path':str(root),'wheels':manifest['wheels'],'inputs':len(inputs),'closure_files':len(copied)}))
