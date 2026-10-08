from pathlib import Path
import json,sys
import pytest,anysolver
from threadpoolctl import threadpool_info
r=Path(__file__).resolve().parent
sys.path.insert(0,str(r/'fixtures'))
assert Path(anysolver.__file__).is_relative_to(r/'site')
assert all(p['num_threads']==1 for p in threadpool_info())
print(json.dumps({'anysolver':anysolver.__file__,'pools':threadpool_info()}))
raise SystemExit(pytest.main(['-q','-c',str(r/'pytest.ini'),str(r/'fixtures/test_stiffened_shell_bl5_affine_supports.py'),'-k','complete_development_rule or third_transfer_moment']))
