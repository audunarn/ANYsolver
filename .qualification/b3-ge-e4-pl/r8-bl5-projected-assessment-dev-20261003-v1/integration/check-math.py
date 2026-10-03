from pathlib import Path
import json,sys,os
import numpy,scipy
from threadpoolctl import threadpool_info
import pytest
ROOT=Path(__file__).resolve().parent
pools=threadpool_info();assert pools and all(p['num_threads']==1 for p in pools)
(ROOT/'math-runtime.json').write_text(json.dumps(dict(executable=sys.executable,pools=pools,numpy=numpy.__version__,scipy=scipy.__version__,plugin_autoload_disabled=os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']),indent=2)+'\n')
raise SystemExit(pytest.main(['-v','-c',str(ROOT/'pytest.ini'),'--basetemp',str(ROOT/'math-pytest-temp'),str(ROOT/'fixtures/test_r8_bl5_projected_reference_action_dev.py'),str(ROOT/'fixtures/test_r8_bl5_external_affine_reference_dev.py')]))
