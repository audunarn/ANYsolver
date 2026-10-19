"""One original nx16 arithmetic-candidate recheck with live solver observers."""
import argparse,copy,inspect,json,pickle,time
from pathlib import Path
import arc_reference as arc
import anysolver.nonlinear_static as ns


def main():
    p=argparse.ArgumentParser(); p.add_argument('output'); a=p.parse_args(); out=Path(a.output); out.mkdir(parents=True,exist_ok=False)
    started=time.perf_counter(); constructor=arc.InterpolatedBeamShellMPCElement; snapshot=ns._increment_snapshot; solve=arc.solve_static_nonlinear
    accepted=[]; iterations=[]
    def integrated(*args,**kwargs):
        kwargs['connection_trace']='director_integrated'; return constructor(*args,**kwargs)
    def record(*args,**kwargs):
        value=snapshot(*args,**kwargs)
        raw=dict(u=value.displacements.copy(),states=copy.deepcopy(dict(value.element_states)),lam=value.load_factor,control=value.control_value)
        accepted.append(raw); path=out/f'accepted-{len(accepted):04d}.pkl'; path.write_bytes(pickle.dumps(raw))
        row=dict(kind='accepted',elapsed=time.perf_counter()-started,index=len(accepted),lam=value.load_factor,control=value.control_value)
        with (out/'progress.jsonl').open('a') as stream: stream.write(json.dumps(row)+'\n')
        return value
    def status(message):
        frame=inspect.currentframe().f_back
        try:
            c=frame.f_locals
            row=dict(kind='status',elapsed=time.perf_counter()-started,message=str(message),frame=frame.f_code.co_name)
            if frame.f_code.co_name=='_newton_increment':
                row.update(iteration=int(c['iteration']),lam=float(c['path_factor']),residual=float(c['residual_norm']),reference=float(c['reference']),relative=float(c['residual_norm']/c['reference']))
                raw=dict(u=c['u'].copy(),q=c['q_trial'].copy(),states=copy.deepcopy(dict(c['committed_states'])),
                         lam=float(c['path_factor']),residual=c['residual'].copy(),K=c['K_T'].copy(),F_int=c['F_int'].copy(),iteration=int(c['iteration']))
                # Atomic latest pending Newton input, never an accepted result.
                temporary=out/'latest-iteration.tmp'; temporary.write_bytes(pickle.dumps(raw)); temporary.replace(out/'latest-iteration.pkl')
            iterations.append(row)
            with (out/'iterations.jsonl').open('a') as stream: stream.write(json.dumps(row)+'\n')
        finally: del frame
    def observed(*args,**kwargs):
        kwargs.update(record_increment_snapshots=True,status_callback=status)
        value=solve(*args,**kwargs)
        raw=dict(u=value.displacements.copy(),states=copy.deepcopy(dict(value.element_states)),lam=value.load_factor,
                 status=value.status,reason=value.stop_reason,info=value.info)
        (out/'terminal.pkl').write_bytes(pickle.dumps(raw))
        return value
    arc.InterpolatedBeamShellMPCElement=integrated; ns._increment_snapshot=record; arc.solve_static_nonlinear=observed
    try:
        result=arc.run_case(16,'nonmatching',.002,30.)
        result.update(experimental_connection_trace='director_integrated',arithmetic_candidate='stable_displacement_and_exact_reference_closure',
                      observer_iterations=len(iterations),observer_accepted=len(accepted))
        arc.write_result(result,out/'result.json')
    finally:
        arc.InterpolatedBeamShellMPCElement=constructor; ns._increment_snapshot=snapshot; arc.solve_static_nonlinear=solve


if __name__=='__main__': main()
