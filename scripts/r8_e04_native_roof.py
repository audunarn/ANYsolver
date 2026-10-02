"""Bounded E04 development screen through the public curved-point owner.

Run under the task's existing serial resource supervisor. This is not capacity
adjudication. A numerical failure leaves outputs and the accepted checkpoint.
"""
from pathlib import Path
import argparse
import json
import time
import numpy as np


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--size',type=int,default=4)
    parser.add_argument('--density',type=float,required=True)
    parser.add_argument('--seed-force',type=float,default=10.)
    parser.add_argument('--radius',type=float,default=1e-5)
    parser.add_argument('--steps',type=int,default=2)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    from anysolver import stiffened_shell as ss
    from docs.reference_cases.stiffened_shell_e04_roof import build,definition
    import anysolver,threadpoolctl,numba
    pools=threadpoolctl.threadpool_info()
    assert pools and all(p['num_threads']==1 for p in pools)
    assert numba.get_num_threads()==1 and numba.config.DISABLE_JIT
    c=build(args.size,args.size);d=definition(c,density_kg_m3=args.density)
    node=c.loaded_shell_node+1;row=c.loaded_shell_node
    action=(ss.NodalAction('shell',node,(0.,0.,-args.seed_force,0.,0.,0.)),)
    record=dict(status='IN_PROGRESS',size=args.size,shells=len(c.quads),beams=len(c.beam_cells),
        density_kg_m3=args.density,density_use='static bookkeeping; spectra excluded',
        seed_force_n=args.seed_force,radius=args.radius,requested_arc_steps=args.steps,
        connection='six-channel nodal full-pose bonds',samples=[],timings={},
        imported_solver=str(Path(anysolver.__file__).resolve()),threadpools=pools)
    def save():
        (args.output/'result.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    def sample(result,force,phase):
        value=dict(phase=phase,downward_force_n=float(force),global_z_force_n=-float(force),
            central_translation_m=result.shell_displacement.reshape(-1,6)[row,:3].tolist(),
            equilibrium=float(result.free_equilibrium_ratio),constraint=float(result.constraint_max))
        if phase=='arc':
            from dataclasses import asdict
            value['accepted_radius']=result.history[-1][0]
            value['amplitude']=result.amplitude
            value['attempts']=[asdict(a) for a in result.increment_attempts]
        record['samples'].append(value);save();print(json.dumps(value),flush=True)
    owner=None
    try:
        t=time.monotonic();owner=ss.create_analysis(definition=d)
        record['timings']['compile']=time.monotonic()-t;record['preflight']=owner.preflight();save()
        t=time.monotonic();linear=owner.solve_linear(action)
        record['timings']['linear']=time.monotonic()-t
        record['linear']=dict(equilibrium=linear.free_equilibrium_ratio,constraint=linear.constraint_max,
            central_translation_m=linear.shell_displacement.reshape(-1,6)[row,:3].tolist())
        save()
        owner.close()
        t=time.monotonic();owner=ss.create_analysis(definition=d)
        record['timings']['finite_compile']=time.monotonic()-t
        t=time.monotonic();seed=owner.solve(action,(1.,));record['timings']['seed']=time.monotonic()-t
        sample(seed,args.seed_force,'seed');(args.output/'seed.bin').write_bytes(owner.checkpoint())
        metric=ss.PhysicalChordMetric(c.metric_weights,c.length)
        expected=tuple(('shell',n) for n in d.shell.node_ids)+tuple(('beam',n) for n in range(100001,100001+len(c.beam_positions)))
        assert owner.preflight()['arc_metric_node_order']==expected
        control=ss.ArcLengthControl('shell',node,2,metric,args.radius,-1)
        def accepted(result):
            sample(result,args.seed_force*(1+result.amplitude),'arc')
            (args.output/'accepted.bin').write_bytes(owner.checkpoint())
        t=time.monotonic();arc=owner.continue_arc_length(action,control,steps=args.steps,on_accepted=accepted)
        record['timings']['arc']=time.monotonic()-t
        saved=owner.checkpoint()
        t=time.monotonic();restored=ss.create_analysis(definition=d)
        try:
            repeated=restored.restore(saved)
            assert restored.checkpoint()==saved
            np.testing.assert_array_equal(repeated.cell_resultants,arc.cell_resultants)
        finally:restored.close()
        record['timings']['restore']=time.monotonic()-t
        record['restart_bytes_equal']=True;record['status']='COMPLETED_DEVELOPMENT_ONLY';save()
    except Exception as error:
        record['status']='FAILED';record['failure']=dict(type=type(error).__name__,message=str(error))
        if hasattr(error,'attempts'):
            from dataclasses import asdict
            record['failure']['attempts']=[asdict(a) for a in error.attempts]
        save();raise
    finally:
        if owner is not None:owner.close()


if __name__=='__main__':main()
