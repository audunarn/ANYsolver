from pathlib import Path
import ast,hashlib,json,shutil,subprocess,sys

repo=Path('C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling')
previous=Path('C:/Users/AudunArnesenNyhus/AppData/Local/Temp/r8-ge-fibre-finite-installed-v2')
root=Path('C:/Users/AudunArnesenNyhus/AppData/Local/Temp/r8-ge-native-energy-coupled-installed-v1')
assert not root.exists(), 'never overwrite a run'
root.mkdir();(root/'tests').mkdir();(root/'scripts').mkdir();(root/'wheels').mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
selected=['test_stiffened_shell_ge_experimental.py','test_stiffened_shell_ge_finite_experimental.py',
 'test_stiffened_shell_ge_physical_fibre_finite.py','test_stiffened_shell_ge_physical_fibre_linear.py',
 'test_stiffened_shell_native_fibre_energy.py','test_stiffened_shell_native_coupled_material.py',
 'test_ge_beam3_fibre_cell.py','test_ge_beam3_retained_fibre.py']
pending=[repo/'tests'/name for name in selected];seen=set()
while pending:
    path=pending.pop()
    if path in seen:continue
    seen.add(path);relative=path.relative_to(repo);target=root/relative
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
    tree=ast.parse(path.read_text(encoding='utf-8-sig'))
    for node in ast.walk(tree):
        if isinstance(node,ast.ImportFrom) and node.module:
            module=node.module
            if node.level and relative.parts[0]=='docs':
                base=list(relative.with_suffix('').parts[:-1])
                module='.'.join(base[:len(base)-node.level+1]+module.split('.'))
            if module.startswith('test_'):
                pending.append(repo/'tests'/(module+'.py'))
            elif module.startswith('docs.'):
                dependency=repo/Path(*module.split('.')).with_suffix('.py')
                if dependency.is_file():pending.append(dependency)
for name in ('experimental_stiffened_ge_fibre_history.py','experimental_stiffened_ge_panel.py'):
    shutil.copyfile(repo/'scripts'/name,root/'scripts'/name)
shutil.copyfile(previous/'pytest.ini',root/'pytest.ini')
runner=(previous/'run_installed.py').read_text()
runner=runner.replace("assert manifest['wheels']['anysolver-0.4.7-py3-none-any.whl']=='909f26ce982470dec3c2030ea72f78b227085672855c67b99897579c7872a531'",'')
runner=runner.replace("selected=sorted((root/'tests').glob('test_*.py'))",'selected=[root/"tests"/name for name in '+repr(selected)+']')
(root/'run_installed.py').write_text(runner)
supervisor=(previous/'run_bounded.py').read_text()
supervisor=supervisor.replace('r8-ge-fibre-finite-installed-v2','r8-ge-native-energy-coupled-installed-v1')
supervisor=supervisor.replace("OMP_NUM_THREADS='1')","OMP_NUM_THREADS='1',NUMBA_NUM_THREADS='1')")
(root/'run_bounded.py').write_text(supervisor)
build=root/'build-source';build.mkdir()
for name in ('pyproject.toml','README.md','LICENSE'):
    if (repo/name).is_file():shutil.copyfile(repo/name,build/name)
shutil.copytree(repo/'src',build/'src',ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.egg-info'))
with (root/'build.log').open('w') as log:
    subprocess.run([sys.executable,'-m','pip','wheel','--no-cache-dir','--no-build-isolation','--no-deps',
                    '--wheel-dir',str(root/'wheels'),str(build)],stdout=log,stderr=subprocess.STDOUT,check=True)
consumer=next((previous/'wheels').glob('anyfem-*.whl'))
assert sha(consumer)=='ff143e5fece9dd4cec261aa69edbec03acc801d3d0bbfcb90cea7519d814f0c0'
shutil.copyfile(consumer,root/'wheels'/consumer.name)
with (root/'install.log').open('w') as log:
    subprocess.run([sys.executable,'-m','pip','install','--no-cache-dir','--no-deps','--no-compile',
                    '--target',str(root/'site')]+[str(p) for p in (root/'wheels').glob('*.whl')],
                    stdout=log,stderr=subprocess.STDOUT,check=True)
inputs=[p for folder in ('tests','docs','scripts') for p in (root/folder).rglob('*.py')]
inputs += [root/'pytest.ini',root/'run_installed.py',root/'run_bounded.py']
manifest={'source_head':'565685c1ea6fa1a42509f132a8bd4396977ca709',
 'candidate':'native beam energy and coupled shell-J2 state development',
 'selected':selected,'wheels':{p.name:sha(p) for p in (root/'wheels').glob('*.whl')},
 'inputs':{p.relative_to(root).as_posix():sha(p) for p in inputs}}
(root/'manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'root':str(root),'inputs':len(inputs),'wheels':manifest['wheels']}))
