from pathlib import Path
import json, os, sys
import anysolver, pytest, threadpoolctl
root=Path(__file__).resolve().parent;site=(root/'site').resolve()
assert Path(anysolver.__file__).resolve().is_relative_to(site),anysolver.__file__
pools=threadpoolctl.threadpool_info();assert all(p['num_threads']==1 for p in pools),pools
assert os.environ['NUMBA_DISABLE_JIT']=='1'
print(json.dumps({'anysolver':anysolver.__file__,'threadpools':pools,'python':sys.version,'numba_disable_jit':os.environ['NUMBA_DISABLE_JIT']}),flush=True)
status=pytest.main(['-q','-c',str(root/'pytest.ini'),'--basetemp',str(root/'pytest-tmp')]+['tests/test_stiffened_shell_ge_owned_rebase.py', 'tests/test_stiffened_shell_ge_experimental.py', 'tests/test_stiffened_shell_ge_finite_experimental.py', 'tests/test_stiffened_shell_s3_algorithmic_pullback.py', 'tests/test_ge_beam3_variational_shell.py'])
loaded={name:str(Path(module.__file__).resolve()) for name,module in list(sys.modules.items()) if (name=='anysolver' or name.startswith('anysolver.')) and getattr(module,'__file__',None)}
assert all(Path(path).is_relative_to(site) for path in loaded.values()),loaded
print(json.dumps({'loaded_anysolver_modules':len(loaded),'after_import':anysolver.__file__}),flush=True)
sys.exit(status)
