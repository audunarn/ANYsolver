"""One actual adaptive continuation; no failure injection or altered physics."""
from pathlib import Path
from dataclasses import asdict
import hashlib, json, os, sys
import numpy as np
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
SITE = ROOT / 'site-v1'
assert Path(ss.__file__).resolve().is_relative_to(SITE)
sys.path.insert(0, str(REPO / 'tests'))
from test_stiffened_shell_ge_distributing_material import definition, actions

pools = threadpool_info()
assert pools and all(p['num_threads'] == 1 for p in pools)
assert os.environ['NUMBA_DISABLE_JIT'] == '1' and not sys.flags.optimize
owner = ss.create_analysis(definition=definition())
control = ss.AdaptiveIncrementControl(max_cutbacks=4, max_attempts=8)
record = dict(scope='one bounded development continuation; adapted history is not fixed-history parity',
    decision='Can existing adaptive halving complete the retained 1.01 target under a bounded actual solve?',
    actions=[asdict(row) for row in actions()], requested_targets=(1.01,),
    controls=asdict(control), max_iterations=24, max_backtracks=12,
    model=owner._identity, pools=pools,
    wheel_sha256=hashlib.sha256((ROOT / 'dist-v1/anysolver-0.4.7-py3-none-any.whl').read_bytes()).hexdigest(),
    fixture_sha256=hashlib.sha256((REPO / 'tests/test_stiffened_shell_ge_distributing_material.py').read_bytes()).hexdigest())
(ROOT / 'physical-binding-v1.json').open('x').write(json.dumps(record, indent=2) + '\n')
def save(result):
    raw = owner.checkpoint()
    (ROOT / f'physical-prefix-{result.generation}.bin').open('xb').write(raw)
    (ROOT / f'physical-accepted-{result.generation}.json').open('x').write(json.dumps(dict(
        generation=result.generation, factors=result.accepted_factors,
        equilibrium=result.free_equilibrium_ratio, constraint_max=result.constraint_max,
        checkpoint_sha256=hashlib.sha256(raw).hexdigest(),
        shell_alpha_max=float(np.max(result.shell_layer_alpha)),
        beam_accumulated_max=float(np.max(result.beam_station_accumulated))), indent=2) + '\n')
try:
    prefix = owner.solve(actions(), (.25, .5, .75, 1.), max_iterations=24,
                         max_backtracks=16, on_accepted=save)
    record['fresh_prefix'] = prefix.accepted_factors
    try:
        result = owner.solve(actions(), (1.01,), increment_control=control,
            max_iterations=24, max_backtracks=12, on_accepted=save)
        record.update(status=result.status, accepted_factors=result.accepted_factors,
            attempts=[asdict(row) for row in result.increment_attempts],
            equilibrium=result.free_equilibrium_ratio, constraint_max=result.constraint_max)
    except ss.AdaptiveIncrementExhausted as error:
        record.update(status='INCOMPLETE_ADAPTIVE_LIMIT', failure=str(error),
            accepted_factors=error.accepted_factors, attempts=[asdict(row) for row in error.attempts])
    except ss.FiniteIncrementFailure as error:
        record.update(status='INCOMPLETE_FIXED_PREFIX', failure=str(error), attempt=asdict(error.attempt))
    record['final_checkpoint_sha256'] = hashlib.sha256(owner.checkpoint()).hexdigest()
    (ROOT / 'physical-result-v1.json').open('x').write(json.dumps(record, indent=2, allow_nan=False) + '\n')
    print(json.dumps({key:record[key] for key in ('status','accepted_factors')}))
finally:
    owner.close()
