"""Existing terminal metadata plus explicitly optional independent force replay."""
import argparse, copy, json, pickle
from pathlib import Path
from types import SimpleNamespace
import numpy as np


def serial(value):
    if isinstance(value, np.ndarray): return value.tolist()
    if isinstance(value, (np.integer, np.floating, np.bool_)): return value.item()
    raise TypeError(type(value).__name__)


def main():
    p=argparse.ArgumentParser(); p.add_argument('raw_root'); p.add_argument('output')
    p.add_argument('--reconstruct-returned',action='store_true'); a=p.parse_args()
    out=Path(a.output); out.mkdir(parents=True,exist_ok=False); summaries={}; raw={}
    for suffix,route in ((0,'direct'),(1,'interp')):
        folder=Path(a.raw_root)/('test_dc_full_target_plasticity'+str(suffix))
        paths=sorted(folder.glob('accepted-*.pkl'))
        accepted=[pickle.loads(path.read_bytes()) for path in paths]
        terminal=pickle.loads((folder/'terminal.pkl').read_bytes()); saved=pickle.dumps((accepted,terminal))
        info=terminal['info']; adaptation=info.get('displacement_control_adaptation',{})
        states=terminal['element_states']
        alphas={int(eid):float(np.max(state['alpha'])) for eid,state in states.items() if isinstance(state,dict) and 'alpha' in state}
        seeds=adaptation.get('uncommitted_seeds',[])
        same_u=bool(np.array_equal(accepted[-1]['displacements'],terminal['displacements']))
        data=dict(status=terminal['status'],reason=terminal['stop_reason'],load_factor=terminal['load_factor'],
            last_accepted_control=accepted[-1]['control'],terminal_equals_last_accepted_displacement=same_u,
            accepted_count=len(accepted),last_two_accepted=[dict(file=paths[i].name,control=accepted[i]['control'],lambda_value=accepted[i]['lam']) for i in range(-min(2,len(accepted)),0)],
            alpha_maxima=alphas,adaptation=adaptation,
            total_newton_iterations=info.get('total_newton_iterations'),
            seed_status_counts={name:sum(s['status']==name for s in seeds) for name in sorted({s['status'] for s in seeds})},
            seeded_attempt_budget_checks=[dict(target=s['target'],seed_solves=s['solves'],normal_iteration_budget=s['remaining_iterations'],
                sum=s['solves']+s['remaining_iterations']) for s in seeds],
            exact_per_attempt_rhs_counts='Not persisted from pytest local counter; inline<=40 assertion executed on each actual RHS. No replay to reconstruct counts.',
            physical_reconstruction_executed=bool(a.reconstruct_returned))
        if a.reconstruct_returned:
            import continuation_actual_finite_entry as entry
            model,load,probe,grid=entry._build_ep_model(route); entry._add_tip_load(model,load,grid)
            public=SimpleNamespace(displacements=np.asarray(terminal['displacements']),load_factor=float(terminal['load_factor']),element_states=copy.deepcopy(states))
            case=dict(model=model,load=load,probe=probe,grid=grid,coupling=route,result=public)
            returned=entry._independent_equilibrium(case)
            preceding=accepted[-2]['element_states'] if len(accepted)>1 else {}
            frozen=entry._independent_equilibrium(case,element_states=copy.deepcopy(preceding))
            constraints=entry.constraint_residual_summary(model,case['_oracle']['mpc_map'].to_linear_displacement(public.displacements))
            wrench=lambda eq: bool(np.linalg.norm(eq['balance'])<=1e-6*max(np.linalg.norm(eq['applied_wrench']),1e-30))
            data.update(returned_relative_R=returned['relative_residual'],returned_wrench_pass=wrench(returned),
                previous_accepted_frozen_relative_R=frozen['relative_residual'],previous_frozen_wrench_pass=wrench(frozen),
                constraints=constraints,
                reconstruction_scope='Residuals at the stopped ACCEPTED state using its returnedH and preceding acceptedH; not at a failed unaccepted Newtonstate.')
            raw[route+'-returned-equilibrium']=returned; raw[route+'-frozen-equilibrium']=frozen
        assert pickle.dumps((accepted,terminal))==saved
        summaries[route]=data
    (out/'result.json').write_text(json.dumps(summaries,indent=2,default=serial))
    (out/'raw.pkl').write_bytes(pickle.dumps(raw))
    print(json.dumps({route:{k:v for k,v in data.items() if k not in ('adaptation','seeded_attempt_budget_checks','alpha_maxima')} for route,data in summaries.items()},default=serial))


if __name__=='__main__': main()
