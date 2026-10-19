"""Run unchanged continuation test IDs with pending/accepted/final evidence."""
import argparse,copy,inspect,json,pickle,sys,time
from pathlib import Path
import numpy as np
import pytest
import anysolver.nonlinear_static as ns
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'tests'))
import test_nonlinear_beam_shell_slice3_continuation as tests


def main():
    p=argparse.ArgumentParser(); p.add_argument('output'); p.add_argument('tests',nargs='+'); a=p.parse_args()
    out=Path(a.output); out.mkdir(parents=True,exist_ok=False); started=time.perf_counter()
    real_solve=tests.solve_static_nonlinear; real_snapshot=ns._increment_snapshot; real_factorize=ns.factorize
    current={'call':0,'accepted':0,'corrections':0}
    def save(path,value):
        temporary=path.with_suffix('.tmp'); temporary.write_bytes(pickle.dumps(value)); temporary.replace(path)
    def record(*args,**kwargs):
        value=real_snapshot(*args,**kwargs); current['accepted']+=1
        save(out/f"call-{current['call']:02d}-accepted-{current['accepted']:04d}.pkl",
             dict(u=value.displacements.copy(),states=copy.deepcopy(dict(value.element_states)),lam=value.load_factor,control=value.control_value))
        return value
    def solve(*args,**kwargs):
        current.update(call=current['call']+1,accepted=0,corrections=0)
        value=real_solve(*args,**kwargs)
        save(out/f"call-{current['call']:02d}-terminal.pkl",dict(u=value.displacements.copy(),states=copy.deepcopy(dict(value.element_states)),lam=value.load_factor,steps=value.steps,info=value.info))
        row=dict(call=current['call'],elapsed=time.perf_counter()-started,status=value.status,reason=value.stop_reason,lam=value.load_factor,accepted=current['accepted'],corrections=current['corrections'],adaptation=value.info.get('displacement_control_adaptation'))
        with (out/'terminals.jsonl').open('a') as stream: stream.write(json.dumps(row)+'\n')
        return value
    def factorize(matrix,*args,**kwargs):
        frame=inspect.currentframe().f_back
        try:
            for _ in range(8):
                if frame is None or frame.f_code.co_name=='_solve_static_displacement_control': break
                frame=frame.f_back
            c=None if frame is None else dict(frame.f_locals)
        finally: del frame
        handle=real_factorize(matrix,*args,**kwargs)
        if c is None: return handle
        class Handle:
            def __getattr__(self,name): return getattr(handle,name)
            def solve(self,rhs):
                delta=handle.solve(rhs); current['corrections']+=1
                row=dict(call=current['call'],elapsed=time.perf_counter()-started,iteration=c['iteration'],target=c['target'],lam=c['lam'],residual=c['residual_norm'],reference=c['reference'])
                with (out/'iterations.jsonl').open('a') as stream: stream.write(json.dumps(row)+'\n')
                save(out/f"call-{current['call']:02d}-latest-pending.pkl",dict(u=c['u'].copy(),q=c['q'].copy(),states=copy.deepcopy(dict(c['committed_states'])),lam=c['lam'],target=c['target'],rhs=np.asarray(rhs).copy(),delta=np.asarray(delta).copy(),matrix=matrix.copy(),iteration=c['iteration']))
                return delta
        return Handle()
    tests.solve_static_nonlinear=solve; ns._increment_snapshot=record; ns.factorize=factorize
    try:
        return pytest.main(['-s','-vv','-p','no:cacheprovider','--basetemp',str(out/'pytest-tmp'),*a.tests])
    finally:
        tests.solve_static_nonlinear=real_solve; ns._increment_snapshot=real_snapshot; ns.factorize=real_factorize


if __name__=='__main__': raise SystemExit(main())
