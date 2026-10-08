from pathlib import Path
import hashlib, importlib.util, json
import anysolver
import numpy as np
from threadpoolctl import threadpool_info
ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
SITE = REPO/'.qualification/b3-ge-e4-pl/r8-distributing-ge-owner-dev-20261004-v1/site'
assert Path(anysolver.__file__).resolve().is_relative_to(SITE)
spec = importlib.util.spec_from_file_location('existing_fixture',REPO/'tests/test_stiffened_shell_distributing_footprint.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
compiled = module.compiled()
pools = threadpool_info()
assert pools and all(p['num_threads']==1 for p in pools)
fields = ('shell_positions_m','beam_position_m','centroid_m','eccentricity_m','area_mean','planar_gradients','shell_trace','constraint_matrix','gather_slots')
record = dict(scope='exact historical two-host compiler compatibility baseline, no new scientific run',
    identity=compiled.identity, arrays={n:dict(shape=list(getattr(compiled,n).shape),dtype=str(getattr(compiled,n).dtype),sha256=hashlib.sha256(getattr(compiled,n).tobytes()).hexdigest(),values=getattr(compiled,n).tolist()) for n in fields},
    area_m2=compiled.area_m2, imported_solver=str(anysolver.__file__),pools=pools)
(ROOT/'two-host-baseline-v1.json').open('x').write(json.dumps(record,indent=2)+'\n')
print(json.dumps(dict(identity=compiled.identity,arrays=len(fields))))
