"""One exact-control frozen-history least-squares corrector; harness only.

Residual is the original reduced physical equilibrium, scaled by its frozen
reference. A retained linear probe row is eliminated exactly after checking
that the nonlinear kinematic map leaves that master probe unchanged. There
are at most40 distinct force/tangent evaluations and an internal100s deadline.
Optimizer stopping is never scientific admission or a production capability.
"""
import argparse, copy, json, pickle, sys, time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from scipy.optimize import least_squares
sys.path.insert(0, str(Path(__file__).resolve().parents[3]/'tests'))
from test_nonlinear_beam_shell_slice3_continuation import _build_ep_model, _add_tip_load, _independent_equilibrium
from anysolver.corotational import build_nonlinear_rotating_mpc_map
from anysolver.nonlinear_static import _assemble_nonlinear_system
from anysolver.constraint_audit import constraint_residual_summary
from assessment_support import identical, source_identity

class BoundReached(Exception): pass
class RootReached(Exception): pass

def main():
    p=argparse.ArgumentParser(); p.add_argument('capture'); p.add_argument('output')
    p.add_argument('--coupling', choices=('direct','interp'), default='interp')
    p.add_argument('--recover-from', type=Path, help='Summarize preserved evaluations; no corrector rerun')
    a=p.parse_args()
    out=Path(a.output); out.mkdir(parents=True,exist_ok=False); started=time.perf_counter()
    c=pickle.loads(Path(a.capture).read_bytes()); original=copy.deepcopy(c)
    model,load,probe,grid=_build_ep_model(a.coupling); _add_tip_load(model,load,grid)
    m=build_nonlinear_rotating_mpc_map(model,c['T'])
    row=np.asarray(c['row']@c['T']).reshape(-1); pivot=int(np.argmax(abs(row)))
    if abs(row[pivot])<1e-15: raise ValueError('no eliminable retained control row')
    free=np.delete(np.arange(len(row)),pivot)
    Z=np.eye(len(row))[:,free]; Z[pivot,:]=-row[free]/row[pivot]
    q0=c['q'].copy(); q0[pivot]+=(c['target']-float(c['row']@c['u']))/row[pivot]
    lam_scale=max(abs(c['lam']),1.)
    x0=np.r_[np.zeros(len(free)),c['lam']/lam_scale]
    cache={}; trace=[]; report=dict(diagnostic_only=True,production_adoption=False)
    best=None
    def evaluate(x):
        nonlocal cache,best
        if cache and np.array_equal(cache['x'],x): return cache
        if len(trace)>=40 or time.perf_counter()-started>=100: raise BoundReached()
        q=q0+Z@x[:-1]; lam=lam_scale*x[-1]
        linear=np.asarray(c['T']@q+c['u0']).reshape(-1); u=m.apply_kinematics(linear)
        control=float(c['row']@u); linear_control=float(c['row']@linear)
        if abs(control-linear_control)>1e-12 or abs(control-c['target'])>1e-12:
            raise ValueError('retained probe control is not exactly linear under mapping')
        H=copy.deepcopy(c['states']); Hbefore=copy.deepcopy(H); ubefore=u.copy()
        fint,K,trial=_assemble_nonlinear_system(model,u,H,5,tangent=True,kinematics='corotational',corotational_tangent='work_conjugate')
        assert identical(H,Hbefore) and np.array_equal(u,ubefore)
        ext=c['F_const']+lam*c['F']; r=m.reduce_force(u,fint-ext)
        ref=max(float(np.linalg.norm(m.reduce_force(u,c['F_const']+max(abs(lam),1.)*c['F']))),1.)
        kr=m.reduce_tangent(u,K,fint-ext)
        J=np.column_stack((kr@Z,-lam_scale*m.reduce_force(u,c['F'])))
        cache=dict(x=x.copy(),q=q,u=u,lam=lam,states=copy.deepcopy(trial),r=r,reference=ref,
                   fun=r/c['reference'],jac=J/c['reference'])
        tr=dict(evaluation=len(trace)+1,elapsed=time.perf_counter()-started,residual=float(np.linalg.norm(r)),
                relative_residual=float(np.linalg.norm(r)/ref),control=control,lam=float(lam))
        trace.append(tr)
        with (out/'trace.jsonl').open('a') as stream: stream.write(json.dumps(tr)+'\n')
        if best is None or np.linalg.norm(r)<np.linalg.norm(best['r']): best=copy.deepcopy(cache)
        with (out/f'evaluation-{len(trace):02d}.pkl').open('xb') as stream: pickle.dump(cache,stream)
        if np.linalg.norm(r)<=1e-8*ref: raise RootReached()
        return cache
    try:
        if a.recover_from:
            saved=[pickle.loads(f.read_bytes()) for f in sorted(a.recover_from.glob('evaluation-*.pkl'))]
            if not saved: raise ValueError('no preserved evaluations')
            best=min(saved,key=lambda v:np.linalg.norm(v['r']))
            trace=[json.loads(line) for line in (a.recover_from/'trace.jsonl').read_text().splitlines()]
            report.update(outcome='recovered_bounded_corrector_evidence', recovery_source=str(a.recover_from),
                          new_corrector_evaluations=0)
        else:
            solved=least_squares(lambda x:evaluate(x)['fun'],x0,jac=lambda x:evaluate(x)['jac'],
                                 method='trf',x_scale='jac',tr_solver='exact',max_nfev=40,
                                 ftol=None,xtol=None,gtol=1e-15)
            report.update(outcome='optimizer_stopped',optimizer_message=solved.message,optimizer_status=int(solved.status))
    except RootReached:
        report.update(outcome='strict_corrector_root')
        best=copy.deepcopy(cache)
    except BoundReached:
        report.update(outcome='evaluation_or_wall_bound')
    finally:
        report.update(identity=source_identity(),evaluations=len(trace),trace=trace,
                      actual_input_unchanged=identical(c['states'],original['states'])
                          and all(np.array_equal(c[k],original[k]) for k in ('u','q','delta','F','F_const','row')),
                      elapsed=time.perf_counter()-started)
        if best is not None:
            case=dict(model=model,load=load,probe=probe,grid=grid,coupling=a.coupling,result=SimpleNamespace(
                displacements=best['u'],load_factor=best['lam'],element_states=best['states']))
            checks=_independent_equilibrium(case)
            constraints=constraint_residual_summary(model,m.to_linear_displacement(best['u']))
            report.update(best_relative=float(np.linalg.norm(best['r'])/best['reference']),
                          best_control=float(c['row']@best['u']),best_lambda=float(best['lam']),
                          independent_relative=checks['relative_residual'],
                          constraint_summary=constraints,
                          strict_force_pass=bool(np.linalg.norm(best['r'])<=1e-8*best['reference']),
                          independent_force_pass=bool(checks['relative_residual']<=1e-7),
                          wrench_relative=float(np.linalg.norm(checks['balance'])/max(np.linalg.norm(checks['applied_wrench']),1e-30)))
            with (out/'best.pkl').open('xb') as stream: pickle.dump(best,stream)
        (out/'result.json').write_text(json.dumps(report,indent=2)); print(json.dumps(report))

if __name__=='__main__':main()
