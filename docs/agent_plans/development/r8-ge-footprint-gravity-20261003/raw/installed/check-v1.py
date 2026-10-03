import json,runpy,sys
from pathlib import Path
import anysolver,anymaterial,numpy,scipy,numba,pytest
from threadpoolctl import threadpool_info
ROOT=Path(__file__).resolve().parent;SITE=ROOT/'site'
assert Path(anysolver.__file__).resolve().is_relative_to(SITE)
assert numba.get_num_threads()==1 and numba.config.DISABLE_JIT
sys.path.insert(0,str(ROOT/'fixtures'))
print(json.dumps(dict(imports={m.__name__:m.__file__ for m in (anysolver,anymaterial,numpy,scipy,numba,pytest)},versions={m.__name__:getattr(m,'__version__',None) for m in (numpy,scipy,numba,pytest)},numba_threads=numba.get_num_threads(),jit_disabled=bool(numba.config.DISABLE_JIT))),flush=True)
if sys.argv[1]=='tests':
 tests=('test_stiffened_shell_ge_footprint_gravity.py','test_stiffened_shell_ge_body_load.py','test_stiffened_shell_ge_gravity_owner.py','test_stiffened_shell_footprint_increment_charts.py')
 code=pytest.main(['-q','-c',str(ROOT/'pytest.ini'),'--basetemp',str(ROOT/'pytest-temp'),*[str(ROOT/'fixtures'/name) for name in tests]])
else:
 runpy.run_path(str(ROOT/'fixtures/stiffened_shell_ge_footprint_gravity.py'),run_name='__main__');code=0
imports={name:m.__file__ for name,m in tuple(sys.modules.items()) if name.split('.')[0]=='anysolver' and getattr(m,'__file__',None)}
assert all(Path(p).resolve().is_relative_to(SITE) for p in imports.values())
assert all(p['num_threads']==1 for p in threadpool_info())
(ROOT/(sys.argv[1]+'-identity.json')).write_text(json.dumps(dict(imports=imports,pools=threadpool_info(),exit_code=code),indent=2)+'\n')
print(json.dumps(dict(onsite_modules=len(imports),pools=threadpool_info())),flush=True)
raise SystemExit(code)
