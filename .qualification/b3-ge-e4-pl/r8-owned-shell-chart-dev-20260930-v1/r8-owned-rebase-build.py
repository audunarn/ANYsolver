from pathlib import Path
import ast, hashlib, json, os, shutil, subprocess, sys
repo=Path.cwd()
root=Path(os.environ['TEMP'])/'r8-owned-rebase-installed-v1'
root.mkdir(exist_ok=False)
source=root/'build-source'; source.mkdir()
shutil.copytree(repo/'src',source/'src',ignore=shutil.ignore_patterns('__pycache__','*.egg-info'))
for name in ('pyproject.toml','README.md','LICENSE','COPYRIGHT','THIRD_PARTY_NOTICES.md'):
    shutil.copy2(repo/name,source/name)
selected=['test_stiffened_shell_ge_owned_rebase.py','test_stiffened_shell_ge_experimental.py','test_stiffened_shell_ge_finite_experimental.py','test_stiffened_shell_s3_algorithmic_pullback.py','test_ge_beam3_variational_shell.py']
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
(root/'pytest.ini').write_text('[pytest]\n',encoding='utf-8')
# Historical variational fixtures read these protected, immutable reference cases.
shutil.copytree(repo/'docs'/'reference_cases',root/'docs'/'reference_cases')
wheel_dir=root/'wheels';wheel_dir.mkdir()
with (root/'wheel.log').open('w') as out:
    subprocess.run([sys.executable,'-m','pip','wheel',str(source),'--no-deps','--no-build-isolation','--no-cache-dir','-w',str(wheel_dir)],stdout=out,stderr=subprocess.STDOUT,check=True,timeout=120)
wheel=next(wheel_dir.glob('*.whl'))
with (root/'install.log').open('w') as out:
    subprocess.run([sys.executable,'-m','pip','install','--no-deps','--no-cache-dir','--target',str(root/'site'),str(wheel)],stdout=out,stderr=subprocess.STDOUT,check=True,timeout=120)
runner='''from pathlib import Path
import json, os, sys
import anysolver, pytest, threadpoolctl
root=Path(__file__).resolve().parent;site=(root/'site').resolve()
assert Path(anysolver.__file__).resolve().is_relative_to(site),anysolver.__file__
pools=threadpoolctl.threadpool_info();assert all(p['num_threads']==1 for p in pools),pools
assert os.environ['NUMBA_DISABLE_JIT']=='1'
print(json.dumps({'anysolver':anysolver.__file__,'threadpools':pools,'python':sys.version,'numba_disable_jit':os.environ['NUMBA_DISABLE_JIT']}),flush=True)
status=pytest.main(['-q','-c',str(root/'pytest.ini'),'--basetemp',str(root/'pytest-tmp')]+SELECTED)
loaded={name:str(Path(module.__file__).resolve()) for name,module in list(sys.modules.items()) if (name=='anysolver' or name.startswith('anysolver.')) and getattr(module,'__file__',None)}
assert all(Path(path).is_relative_to(site) for path in loaded.values()),loaded
print(json.dumps({'loaded_anysolver_modules':len(loaded),'after_import':anysolver.__file__}),flush=True)
sys.exit(status)
'''.replace('SELECTED',repr(['tests/'+v for v in selected]))
(root/'run_installed.py').write_text(runner,encoding='utf-8')
paths=['src/anysolver/_ge_beam3_variational_shell.py','src/anysolver/_stiffened_shell_ge_checkpoint_binary.py','src/anysolver/_stiffened_shell_ge_experimental.py','src/anysolver/_stiffened_shell_ge_finite_experimental.py','src/anysolver/_stiffened_shell_s3_algorithmic_pullback.py','src/anysolver/_stiffened_shell_rotation_charts.py']
meta={'root':str(root),'wheel':wheel.name,'wheel_sha256':hashlib.sha256(wheel.read_bytes()).hexdigest(),'source_sha256':{p:hashlib.sha256((repo/p).read_bytes()).hexdigest() for p in paths},'selected':selected,'test_inputs_sha256':{v:hashlib.sha256((root/'tests'/v).read_bytes()).hexdigest() for v in sorted(inputs)}}
(root/'build.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
print(json.dumps({'root':str(root),'wheel_sha256':meta['wheel_sha256'],'fixture_files':len(inputs)}))
