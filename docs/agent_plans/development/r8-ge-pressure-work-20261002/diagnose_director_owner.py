"""One bounded failed-step diagnosis; no altered solve or acceptance rule."""
import json
from dataclasses import asdict
from pathlib import Path
import sys

import numpy as np
from threadpoolctl import threadpool_info

root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(root/'tests'))
from anysolver import stiffened_shell as ss
from anysolver._stiffened_shell_ge_finite_experimental import FinitePointDriver, _trial_work_ratio
from anysolver._stiffened_shell_increment_control import FiniteIncrementFailure
from test_stiffened_shell_ge_pressure_owner import definition
from test_stiffened_shell_ge_director_pressure import director_load

original = FinitePointDriver._assemble
reports = []
try:
    for kind in ('mixed', 's3'):
        owner = ss.create_analysis(definition=definition(kind))
        best = None
        def observed(self, state, factor, *args, **kwargs):
            global best
            result = original(self, state, factor, *args, **kwargs)
            force = factor*self._external.evaluate(state)[0]
            free = owner._free
            residual = result[0][free]
            applied = force[free]
            active = applied != 0.
            ratios = np.zeros(len(free))
            ratios[active] = np.abs(residual[active]/applied[active])
            index = int(np.argmax(ratios))
            row = dict(equilibrium=float(result[2]), gap=float(result[3]),
                global_ratio=_trial_work_ratio(residual, applied, owner._coordinate_scale[free]),
                row=int(free[index]), residual=float(residual[index]), applied=float(applied[index]))
            if best is None or row['global_ratio'] < best['global_ratio']:
                best = row
            return result
        FinitePointDriver._assemble = observed
        try:
            result = owner.solve(director_load(owner), (.1,))
            reports.append(dict(kind=kind, status='completed', best=best))
        except FiniteIncrementFailure as error:
            reports.append(dict(kind=kind, status='failed', attempt=asdict(error.attempt),
                                best_global_state=best, generation=owner._generation))
        finally:
            owner.close()
finally:
    FinitePointDriver._assemble = original
print(json.dumps(dict(reports=reports, pools=[dict(internal_api=p['internal_api'],
    num_threads=p['num_threads']) for p in threadpool_info()]), indent=2))
