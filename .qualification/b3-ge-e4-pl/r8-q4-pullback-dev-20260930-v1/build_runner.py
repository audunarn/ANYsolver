from pathlib import Path
import ast, hashlib, json, os, shutil, subprocess, sys, zipfile
repo=Path.cwd(); fem=Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer')
root=Path(os.environ['TEMP'])/'r8-q4-pullback-installed-v1'
root.mkdir(exist_ok=False)
selected=['test_stiffened_shell_q4_algorithmic_pullback.py','test_stiffened_shell_q4_pullback_owner.py','test_stiffened_shell_ge_owned_rebase.py','test_stiffened_shell_ge_experimental.py','test_stiffened_shell_ge_finite_experimental.py','test_stiffened_shell_s3_algorithmic_pullback.py','test_ge_beam3_variational_shell.py']
inputs=set(selected); pending=list(selected)
while pending:
    name=pending.pop()
    for node in ast.walk(ast.parse((repo/'tests'/name).read_text(encoding='utf-8-sig'))):
        modules=([node.module] if isinstance(node,ast.ImportFrom) else [a.name for a in node.names] if isinstance(node,ast.Import) else [])
        for module in modules:
            filename=(module or '').split('.')[0]+'.py'
            if filename.startswith('test_') and (repo/'tests'/filename).exists() and filename not in inputs:
                inputs.add(filename);pending.append(filename)
(root/'tests').mkdir()
for name in sorted(inputs): shutil.copy2(repo/'tests'/name,root/'tests'/name)
shutil.copy2(fem/'tests'/'test_experimental_stiffened_shell_consumer.py',root/'tests'/'test_experimental_stiffened_shell_consumer.py')
selected.append('test_experimental_stiffened_shell_consumer.py')
(root/'pytest.ini').write_text('[pytest]\n',encoding='utf-8')
shutil.copytree(repo/'docs'/'reference_cases',root/'docs'/'reference_cases')
artifacts={}
for label,checkout in [('anysolver',repo),('anyfem',fem)]:
    source=root/(label+'-build-source'); source.mkdir()
    shutil.copytree(checkout/'src',source/'src',ignore=shutil.ignore_patterns('__pycache__','*.egg-info'))
    for name in ('pyproject.toml','README.md','LICENSE','COPYRIGHT','THIRD_PARTY_NOTICES.md'):
        if (checkout/name).exists(): shutil.copy2(checkout/name,source/name)
    wheel_dir=root/(label+'-wheels');wheel_dir.mkdir()
    with (root/(label+'-wheel.log')).open('w') as out:
        subprocess.run([sys.executable,'-m','pip','wheel',str(source),'--no-deps','--no-build-isolation','--no-cache-dir','-w',str(wheel_dir)],stdout=out,stderr=subprocess.STDOUT,check=True,timeout=120)
    wheel=next(wheel_dir.glob('*.whl'))
    with (root/(label+'-install.log')).open('w') as out:
        subprocess.run([sys.executable,'-m','pip','install','--no-deps','--no-cache-dir','--target',str(root/'site'),str(wheel)],stdout=out,stderr=subprocess.STDOUT,check=True,timeout=120)
    with zipfile.ZipFile(wheel) as archive:
        members=[n for n in archive.namelist() if n.startswith(label+'/') and n.endswith('.py')]
        mismatches=[n for n in members if archive.read(n)!=(checkout/'src'/n).read_bytes()]
    assert not mismatches,mismatches
    artifacts[label]={'wheel':str(wheel),'sha256':hashlib.sha256(wheel.read_bytes()).hexdigest(),'matching_python_modules':len(members),'source_commit':subprocess.check_output(['git','-c','safe.directory='+str(checkout),'-C',str(checkout),'rev-parse','HEAD'],text=True).strip()}
runner='''from pathlib import Path
import hashlib, json, os, sys
import anysolver, anyfem, pytest, threadpoolctl
root=Path(__file__).resolve().parent;site=(root/'site').resolve()
for module in (anysolver,anyfem): assert Path(module.__file__).resolve().is_relative_to(site),module.__file__
pools=threadpoolctl.threadpool_info();assert all(p['num_threads']==1 for p in pools),pools
assert os.environ['NUMBA_DISABLE_JIT']=='1'
print(json.dumps({'anysolver':anysolver.__file__,'anyfem':anyfem.__file__,'threadpools':pools,'python':sys.version,'numba_disable_jit':os.environ['NUMBA_DISABLE_JIT']}),flush=True)
status=pytest.main(['-q','-c',str(root/'pytest.ini'),'--basetemp',str(root/'pytest-tmp')]+SELECTED)
loaded={name:str(Path(module.__file__).resolve()) for name,module in list(sys.modules.items()) if (name.split('.')[0] in ('anysolver','anyfem')) and getattr(module,'__file__',None)}
assert all(Path(path).is_relative_to(site) for path in loaded.values()),loaded
(root/'imports.json').write_text(json.dumps(loaded,indent=2))
print(json.dumps({'loaded_anysolver_modules':sum(n.split('.')[0]=='anysolver' for n in loaded),'loaded_anyfem_modules':sum(n.split('.')[0]=='anyfem' for n in loaded)}),flush=True)
sys.exit(status)
'''.replace('SELECTED',repr(['tests/'+v for v in selected]))
(root/'run_installed.py').write_text(runner,encoding='utf-8')
shutil.copy2(Path(os.environ['TEMP'])/'r8-owned-rebase-installed-v1'/'run_bounded.py',root/'run_bounded.py')
alltests=list((root/'tests').glob('*.py'))
metadata={'purpose':'Q4 selected pullback and consumer development; not foundation acceptance','artifacts':artifacts,'selected':selected,'test_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in alltests},'source_modules_sha256':{str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (repo/'src'/'anysolver').glob('*.py')}}
(root/'build.json').write_text(json.dumps(metadata,indent=2))
print(json.dumps({'root':str(root),'artifacts':artifacts,'fixtures':len(alltests)}))
