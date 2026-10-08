from pathlib import Path
import ast,json
from hashlib import sha256
from dataclasses import asdict
from unittest.mock import patch
RAW=Path(__file__).resolve().parent
tree=ast.parse((RAW/'progress-screen-v1.py').read_bytes());prefix=[]
for statement in tree.body:
    if isinstance(statement,ast.ImportFrom) and statement.module=='anysolver._stiffened_shell_arc_trial':break
    prefix.append(statement)
namespace=dict(__file__=str(RAW/'progress-prefix-v1.py'),__name__='fixture_only')
exec(compile(ast.Module(body=prefix,type_ignores=[]),'fixed-screen-fixture','exec'),namespace)
ss=namespace['ss'];model=namespace['model']
from anysolver._stiffened_shell_arc_trial import select_trial,ArcSelectionFailure
from anysolver._stiffened_shell_arc_checkpoint import identities
record=dict(status='IN_PROGRESS',production_qualified=False,
    scope='trial-only prospective V2 predicate; no publication or V1 migration',
    artifact=namespace['namespace']['artifact'])
def save():(RAW/'progress-prefix-result-v1.json').write_bytes((json.dumps(record,indent=2)+'\n').encode('ascii'))
owner=ss.create_analysis(definition=model)
try:
    raw=(RAW/'turning-successor-v2.checkpoint').read_bytes();owner.restore(raw)
    assert owner.checkpoint()==raw
    _,m,a=owner._arc_snapshot
    assert m['steps']==33 and m['policy'].endswith('_V1_DEV')
    record.update(predecessor_sha256=sha256(raw).hexdigest(),historical_policy=m['policy'],
        trial_policy=identities(owner)[1],predecessor_steps=m['steps']);save()
    knobs={name:m[name] for name in ('max_cutbacks','max_attempts','max_iterations','max_backtracks')}
    try:
        with patch('anysolver._stiffened_shell_arc_checkpoint.active_policy',lambda _:identities(owner)[1]):
            selection=select_trial(owner._finite_driver,load_direction=a['load_direction'],
                metric=ss.PhysicalChordMetric(a['metric_weights'],m['metric_length']),
                radius=m['requested_radius'],predictor_dof=m['predictor_dof'],orientation=m['orientation'],
                load_base=a['base_load'],amplitude_origin=float(a['history'][-1,1]),**knobs)
        trial=selection.trial
        progress=m['orientation']*(trial.state.q[m['predictor_dof']]-trial.predecessor_state.q[m['predictor_dof']])
        assert progress>0.
        record.update(status='POSITIVE_PROGRESS_TRIAL_CUTBACK',oriented_increment=float(progress),
            amplitude=trial.amplitude,radius=trial.radius,path_error=trial.path_error,
            equilibrium=trial.evaluation[2],constraint=trial.evaluation[3],
            attempts=[asdict(row) for row in selection.attempts])
    except ArcSelectionFailure as error:
        record.update(status='TYPED_SELECTION_EXHAUSTION',failure=str(error),
            attempts=[asdict(row) for row in error.attempts])
    assert owner.checkpoint()==raw
    record['accepted_prefix_byte_identical']=True
    save();print(json.dumps(record))
except BaseException as error:
    record.update(status='UNEXPECTED_FAILURE',failure=repr(error));save();raise
finally:owner.close()
