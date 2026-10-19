"""One unchanged registered arc input with explicit experimental trace selection."""
import argparse, copy, json, pickle
from pathlib import Path
import arc_reference as arc
import anysolver.nonlinear_static as ns


def main():
    p=argparse.ArgumentParser(); p.add_argument("nx",type=int,choices=(8,16)); p.add_argument("output"); a=p.parse_args()
    out=Path(a.output); out.mkdir(parents=True,exist_ok=False)
    constructor=arc.InterpolatedBeamShellMPCElement; snapshot=ns._increment_snapshot; solve=arc.solve_static_nonlinear
    accepted=[]
    def integrated(*args,**kwargs):
        kwargs["connection_trace"]="director_integrated"
        return constructor(*args,**kwargs)
    def record(*args,**kwargs):
        value=snapshot(*args,**kwargs)
        raw=dict(u=value.displacements.copy(),states=copy.deepcopy(dict(value.element_states)),
                 lam=value.load_factor,control=value.control_value)
        accepted.append(raw)
        (out/f"accepted-{len(accepted):04d}.pkl").write_bytes(pickle.dumps(raw))
        return value
    def observed_solve(*args,**kwargs):
        kwargs["record_increment_snapshots"]=True
        value=solve(*args,**kwargs)
        raw=dict(u=value.displacements.copy(),states=copy.deepcopy(dict(value.element_states)),lam=value.load_factor,
                 status=value.status,reason=value.stop_reason,info=value.info)
        (out/"terminal.pkl").write_bytes(pickle.dumps(raw))
        return value
    arc.InterpolatedBeamShellMPCElement=integrated; ns._increment_snapshot=record; arc.solve_static_nonlinear=observed_solve
    try:
        result=arc.run_case(a.nx,"nonmatching",.002,30.)
        result["experimental_connection_trace"]="director_integrated"
        arc.write_result(result,out/"result.json")
    finally:
        arc.InterpolatedBeamShellMPCElement=constructor; ns._increment_snapshot=snapshot; arc.solve_static_nonlinear=solve


if __name__=="__main__": main()
