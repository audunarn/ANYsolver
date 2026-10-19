"""Bounded unchanged -.10/6 production integration observation, not a variant."""
import argparse, copy, inspect, json, pickle, time
from pathlib import Path
import continuation_actual_finite_entry as entry
import anysolver._nonlinear_seed as seeds
from anysolver.control import CancellationToken, SolveCancelled


def main():
    p=argparse.ArgumentParser(); p.add_argument('output'); a=p.parse_args()
    out=Path(a.output); out.mkdir(parents=True,exist_ok=False); start=time.perf_counter(); count=0
    def log(value):
        with (out/'events.jsonl').open('a') as stream: stream.write(json.dumps(dict(value,elapsed=time.perf_counter()-start))+'\n')
    class Deadline(CancellationToken):
        def raise_if_cancelled(self,stage=''):
            if time.perf_counter()-start>60: self.cancel('observer60sdeadline')
            super().raise_if_cancelled(stage)
    token=Deadline(); real=seeds.secant_plane_seed; snapshot=entry.ns._increment_snapshot
    def observed(q,lam,previous,evaluate,solve,**kwargs):
        nonlocal count
        count+=1; frame=inspect.currentframe().f_back
        try:
            values=frame.f_locals; metadata=dict(index=count,target=float(values['target']),step=int(values['step_index']),attempt=int(values['attempts_this_step']),origin_control=float(values['attempt_start_control']),lam=float(lam))
            (out/('seed-'+str(count).zfill(4)+'-origin.pkl')).write_bytes(pickle.dumps(dict(metadata,q=q.copy(),H=copy.deepcopy(dict(values['committed_states'])),previous=copy.deepcopy(previous))))
        finally: del frame
        log(dict(metadata,event='seed_start'))
        x,info=real(q,lam,previous,evaluate,solve,**kwargs)
        log(dict(metadata,event='seed_return',info=info))
        return x,info
    def accepted(*args,**kwargs):
        value=snapshot(*args,**kwargs)
        (out/('accepted-'+str(value.step_index).zfill(4)+'.pkl')).write_bytes(pickle.dumps(value))
        log(dict(event='accepted',index=value.step_index,control=float(value.control_value),lam=float(value.load_factor)))
        return value
    seeds.secant_plane_seed=observed; entry.ns._increment_snapshot=accepted
    model,load,probe,grid=entry._build_ep_model('direct'); entry._add_tip_load(model,load,grid)
    try:
        result=entry.solve_static_nonlinear(model,load,control='displacement',
            displacement_control=entry.DisplacementControl(node_id=probe,dof='uz',target_displacement=-.10),
            num_steps=6,max_iterations=40,tolerance=1e-8,kinematics='corotational',corotational_tangent='work_conjugate',
            emit_restart_checkpoint=False,record_increment_snapshots=True,cancellation_token=token)
        payload=dict(status=result.status,reason=result.stop_reason,info=dict(result.info),u=result.displacements,
            H=dict(result.element_states),lam=result.load_factor)
        (out/'result.pkl').write_bytes(pickle.dumps(payload)); log(dict(event='terminal',status=result.status,reason=result.stop_reason,lam=result.load_factor))
    except SolveCancelled as exc:
        log(dict(event='cooperative_deadline',stage=exc.stage,reason=exc.reason))
    finally:
        seeds.secant_plane_seed=real; entry.ns._increment_snapshot=snapshot


if __name__=='__main__': main()
