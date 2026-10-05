"""Fixed physical fixture; stop after first new-policy coordinate rejection."""
from pathlib import Path
from hashlib import sha256
import ast,json
from dataclasses import asdict
RAW=Path(__file__).resolve().parent
source=(RAW/'screen-v2.py').read_text()
source=source.replace("ART=RAW.parent/'r8-native-arc-dev-20261005-v1'",'ART=RAW')
source=source.replace("ART/'site-v1'","ART/'site-progress-v1'")
source=source.replace("ART/'artifact-v1.json'","ART/'artifact-progress-v1.json'")
tree=ast.parse(source);prefix=[]
for statement in tree.body:
    if isinstance(statement,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='record' for t in statement.targets):break
    prefix.append(statement)
namespace=dict(__file__=str(RAW/'progress-screen-v1.py'),__name__='fixture_only')
exec(compile(ast.Module(body=prefix,type_ignores=[]),'fixed-screen-v2-fixture','exec'),namespace)
ss=namespace['ss'];model=namespace['model'];weights=namespace['weights'];h=namespace['h']
from anysolver._stiffened_shell_arc_trial import ArcSelectionFailure
record=dict(status='IN_PROGRESS',production_qualified=False,rows=[],
    fixture_script_sha256=sha256((RAW/'screen-v2.py').read_bytes()).hexdigest(),
    artifact=namespace['artifact'],pools=namespace['threadpool_info']())
def save():(RAW/'progress-screen-result-v1.json').write_bytes((json.dumps(record,indent=2)+'\n').encode('ascii'))
analysis=ss.create_analysis(definition=model);resumed=None
try:
    analysis.solve((ss.NodalAction('beam',103,(0.,0.,0.,0.,0.,0.)),),(1.,),max_iterations=20,max_backtracks=12)
    control=ss.ArcLengthControl('beam',103,2,ss.PhysicalChordMetric(weights,namespace['a']),.003,orientation=-1)
    actions=(ss.NodalAction('beam',103,(0.,0.,-1.,0.,0.,0.)),)
    previous_w=0.;save()
    for step in range(32):
        parent=analysis.checkpoint()
        try:result=analysis.continue_arc_length(actions,control)
        except ArcSelectionFailure as failure:
            assert analysis.checkpoint()==parent
            record.update(status='TYPED_EXHAUSTION_ACCEPTED_PREFIX_PRESERVED',
                failure=str(failure),attempts=[asdict(r) for r in failure.attempts])
            (RAW/'progress-screen-terminal-prefix-v1.checkpoint').write_bytes(parent)
            save();break
        raw=analysis.checkpoint();metadata=analysis._arc_snapshot[1]
        assert metadata['policy'].endswith('_V2_DEV')
        w=h-float(result.beam_positions[2,2]);progress=w-previous_w
        assert progress>0.
        attempts=[asdict(r) for r in result.increment_attempts]
        guard=any('no oriented progress' in (r['failure'] or '') for r in attempts)
        record['rows'].append(dict(step=step+1,w=w,load=result.amplitude,
            oriented_increment=progress,eq=result.free_equilibrium_ratio,
            gap=result.constraint_max,radius=result.history[-1][0],attempts=attempts,
            policy=metadata['policy']))
        save();print(json.dumps(record['rows'][-1]),flush=True)
        if guard:
            (RAW/'progress-screen-guard-predecessor-v1.checkpoint').write_bytes(parent)
            (RAW/'progress-screen-guard-successor-v1.checkpoint').write_bytes(raw)
            resumed=ss.create_analysis(definition=model);resumed.restore(parent)
            repeated=resumed.continue_arc_length(actions,control)
            assert resumed.checkpoint()==raw and repeated.history==result.history
            record.update(status='GUARD_CUTBACK_POSITIVE_PROGRESS_EXACT_RESTART',
                exact_guard_restart=True,final_checkpoint_sha256=sha256(raw).hexdigest())
            save();break
        previous_w=w
    else:record['status']='NO_GUARD_EVENT_WITHIN_BOUNDED_STEPS';save()
except BaseException as failure:
    record.update(status='UNEXPECTED_FAILURE',failure=repr(failure));save();raise
finally:
    if resumed is not None:resumed.close()
    analysis.close()
