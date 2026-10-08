from pathlib import Path
import hashlib, json, os, sys
import anysolver, anyfem, pytest, threadpoolctl
root=Path(__file__).resolve().parent;site=(root/'site').resolve()
for module in (anysolver,anyfem): assert Path(module.__file__).resolve().is_relative_to(site),module.__file__
pools=threadpoolctl.threadpool_info();assert all(p['num_threads']==1 for p in pools),pools
assert os.environ['NUMBA_DISABLE_JIT']=='1'
print(json.dumps({'anysolver':anysolver.__file__,'anyfem':anyfem.__file__,'threadpools':pools,'python':sys.version,'numba_disable_jit':os.environ['NUMBA_DISABLE_JIT']}),flush=True)
status=pytest.main(['-q','-c',str(root/'pytest.ini'),'--basetemp',str(root/'pytest-tmp')]+['tests/test_stiffened_shell_q4_algorithmic_pullback.py', 'tests/test_stiffened_shell_q4_pullback_owner.py', 'tests/test_stiffened_shell_ge_owned_rebase.py', 'tests/test_stiffened_shell_ge_experimental.py', 'tests/test_stiffened_shell_ge_finite_experimental.py', 'tests/test_stiffened_shell_s3_algorithmic_pullback.py', 'tests/test_ge_beam3_variational_shell.py', 'tests/test_experimental_stiffened_shell_consumer.py'])
loaded={name:str(Path(module.__file__).resolve()) for name,module in list(sys.modules.items()) if (name.split('.')[0] in ('anysolver','anyfem')) and getattr(module,'__file__',None)}
assert all(Path(path).is_relative_to(site) for path in loaded.values()),loaded
(root/'imports.json').write_text(json.dumps(loaded,indent=2))
print(json.dumps({'loaded_anysolver_modules':sum(n.split('.')[0]=='anysolver' for n in loaded),'loaded_anyfem_modules':sum(n.split('.')[0]=='anyfem' for n in loaded)}),flush=True)
sys.exit(status)
