from pathlib import Path
import hashlib, json, os, sys, zipfile
root=Path(__file__).resolve().parent
repo=Path('C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001')
wheel=next((root/'dist').glob('*.whl'))
sha=lambda b: hashlib.sha256(b).hexdigest()
with zipfile.ZipFile(wheel) as archive:
    bindings={}
    for name in ('_stiffened_shell_b2_q4_panel_experimental.py','stiffened_shell.py'):
        relative='anysolver/'+name
        source=repo/'src'/relative
        installed=root/'site'/relative
        blobs=(source.read_bytes(),installed.read_bytes(),archive.read(relative))
        assert blobs[0]==blobs[1]==blobs[2], name
        bindings[relative]=sha(blobs[0])
(root/'binding.json').write_text(json.dumps(dict(wheel_sha256=sha(wheel.read_bytes()),modules=bindings,site=str(root/'site'),scope='unreleased B2 free reference modal development'),indent=2)+'\n')
import pytest, anysolver
from threadpoolctl import threadpool_info
assert Path(anysolver.__file__).is_relative_to(root/'site')
class Runtime:
    def pytest_sessionfinish(self,session,exitstatus):
        modules={name: str(Path(module.__file__).resolve()) for name,module in tuple(sys.modules.items()) if name.startswith('anysolver') and getattr(module,'__file__',None)}
        assert all(Path(p).is_relative_to(root/'site') for p in modules.values())
        pools=threadpool_info()
        assert pools and all(p['num_threads']==1 for p in pools)
        import numba
        assert numba.get_num_threads()==1 and numba.config.DISABLE_JIT
        (root/'runtime.json').write_text(json.dumps(dict(imports=modules,pools=pools,numba_threads=numba.get_num_threads(),jit_disabled=bool(numba.config.DISABLE_JIT),collected=session.testscollected,failed=session.testsfailed,exit_status=int(exitstatus)),indent=2)+'\n')
files=['test_stiffened_shell_b2_free_reference_modes.py','test_stiffened_shell_b2_mixed_reference_modes.py','test_stiffened_shell_b2_reference_modes.py','test_stiffened_shell_b2_footprint_reference_modes.py']
sys.path.insert(0,str(repo/'tests'))
raise SystemExit(pytest.main(['-q','-c',str(root/'pytest.ini'),*(str(repo/'tests'/name) for name in files)],plugins=[Runtime()]))
