"""Supported numerical-completion action on saved BL5 shell states.

Reuse mapped PL+HG after exact shell-operator parity. No coefficient change,
new structural solve, dense Schur matrix, refinement or formal F03 assessment.
Spin elimination is only the shell's unforced normal-spin block; the native
beam/constraint mixed matrix is neither condensed nor declared SPD.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu

CASES = ('fy','mx','mz')
COMPLETION_SHA = 'b710b71f7581a8761168b39a319bb9d14cfac394207a616d1b78649634606287'
ORIGINAL_RUNNER_SHA = 'be7eb0f008974aad72d9970b906038c9bfa5b2caceed4113dccd267482d682ca'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def csr(data, name):
    return sparse.csr_matrix((data[name+'_data'],data[name+'_indices'],data[name+'_indptr']),
                              shape=tuple(data[name+'_shape']))


def weighted_norm(matrix, scales):
    values = sparse.diags(scales)@matrix@sparse.diags(scales)
    return float(np.linalg.norm(values.data))


def main(inputs, inventory, old, completion, original_runner, output):
    output.mkdir(parents=True, exist_ok=False)
    report = {'status':'incomplete', 'classification':'supported completion action, development only',
              'runner_sha256':sha(Path(__file__)), 'cases':{}}
    try:
        if sha(completion) != COMPLETION_SHA or sha(original_runner) != ORIGINAL_RUNNER_SHA:
            raise ValueError('protected mapped completion/runner differs')
        if sha(old/'operators.npz') != '844ae9f5101a1238346cd67976b51bda78ecf0c9c4546875873185253783ea55':
            raise ValueError('original component-gate shell operator differs')
        registration = json.loads(inventory.read_text())
        needed = ('operators.npz','layout.json')+tuple(f'{case}/{name}' for case in CASES
                    for name in ('raw-state.npz','result.json'))
        bindings = {}
        for name in needed:
            digest = registration['member_sha256']['n64/outputs/'+name]
            if sha(inputs/name) != digest: raise ValueError('protected endpoint input differs: '+name)
            bindings[name] = digest
        layout = json.loads((inputs/'layout.json').read_text())
        if layout['shell_node_ids'] != list(range(1,1106)):
            raise ValueError('exact native shell numbering required')
        ns = 6630
        with np.load(inputs/'operators.npz',allow_pickle=False) as data:
            K, C = csr(data,'K'), csr(data,'C')
            fixed = data['fixed'].copy()
            scales = data['coordinate_scale'][:ns].copy()
        with np.load(old/'operators.npz',allow_pickle=False) as data:
            oldK = csr(data,'K')
        # This allows reuse across changed beam counts, not changed shell models.
        Ks = K[:ns,:ns].tocsr()
        if (Ks-oldK[:ns,:ns]).nnz != 0:
            raise ValueError('saved shell operator differs; component reuse invalid')
        Nall = sparse.load_npz(completion).tocsr()
        if Nall.shape != oldK.shape or Nall[ns:,:].nnz or Nall[:,ns:].nnz:
            raise ValueError('mapped completion contains non-shell coordinates')
        N = Nall[:ns,:ns].tocsr()
        core = Ks-N
        spin = np.arange(5,ns,6)
        physical = np.setdiff1d(np.arange(ns),spin)
        d = np.setdiff1d(spin,fixed)
        p = np.setdiff1d(physical,fixed)
        if len(d) != 1088 or len(p) != 5440 or C[:,spin].nnz != 0:
            raise ValueError('unforced, uncoupled normal-spin/support partition differs')
        if not np.all(np.isfinite(scales)) or np.any(scales<=0.):
            raise ValueError('finite native coordinate scales required')
        spin_core = sparse.diags(scales[spin])@core[spin,:]@sparse.diags(scales)
        # Roundoff from subtracting separately assembled terms is measured,
        # not repaired by zeroing or symmetrizing the production operator.
        spin_error = float(np.linalg.norm(spin_core.data))/weighted_norm(Ks,scales)
        if not np.isfinite(spin_error) or spin_error>1e-10:
            raise ValueError('physical core has material spin coupling')
        stiffness_asymmetry = weighted_norm(Ks-Ks.T,scales)/weighted_norm(Ks,scales)
        if stiffness_asymmetry>1e-9: raise ValueError('conservative shell symmetry criterion failed')
        from threadpoolctl import threadpool_info
        pools = threadpool_info()
        if not pools or any(pool['num_threads']!=1 for pool in pools):
            raise ValueError('effective numerical thread count differs')
        Ndd = N[d][:,d].tocsc()
        factor = splu(Ndd)  # General sparse solve; no artificial regularization.
        report.update(input_sha256=bindings, inventory_sha256=sha(inventory),
            old_operator_sha256=sha(old/'operators.npz'), completion_sha256=COMPLETION_SHA,
            original_runner_sha256=ORIGINAL_RUNNER_SHA, source_of_reused_component='v1 component gate passed before derivative predicate failure',
            physical_rows=len(p),free_spin_rows=len(d),shell_rows=ns,spin_block_nnz=Ndd.nnz,
            spin_core_relative_roundoff=spin_error,shell_symmetry_relative=stiffness_asymmetry,
            spin_factorizations=1,pools=pools,python=sys.version)
        arrays = {}
        for case in CASES:
            accepted = json.loads((inputs/case/'result.json').read_text())
            if (accepted['status']!='COMPLETED_DEVELOPMENT_ONLY' or accepted['failures'] or
                any(not np.isfinite(value) or value>(1e-9 if 'gap' in name else 1e-8)
                    for name,value in accepted['checks'].items())):
                raise ValueError('saved native predicates not passed')
            with np.load(inputs/case/'raw-state.npz',allow_pickle=False) as data:
                q = data['q'][:ns].copy()
                action = data['load'][:ns]-data['constraint_resisting'][:ns]
                xyz = data['xyz_m'][:1105].copy()
            if (not np.all(q[fixed[fixed<ns]]==0.) or np.any(action[spin]!=0.) or
                    np.any(xyz[:,2]!=0.) or not np.isfinite(q).all() or not np.isfinite(action).all()):
                raise ValueError('saved homogeneous flat spin-unforced state differs')
            rhs = -(N[d][:,p]@q[p])
            dhat = factor.solve(rhs)
            spin_residual = Ndd@dhat-rhs
            if not np.isfinite(dhat).all(): raise ValueError('nonfinite spin relaxation')
            balance_scale = max(float(np.linalg.norm(rhs)),np.finfo(float).tiny)
            balance = float(np.linalg.norm(spin_residual))/balance_scale
            if not np.isfinite(balance) or balance>1e-10:
                raise ValueError('spin sparse solve equilibrium failed')
            relaxed = q.copy()
            relaxed[d] = dhat
            numerical = N@relaxed
            physical_action = core@q
            saved_numerical = N@q
            work = float(q@action)
            if not np.isfinite(work) or work<=1e-12: raise ValueError('positive frozen shell work required')
            nwork = float(q[p]@numerical[p])
            corework = float(q@physical_action)
            completion_full_work = float(relaxed@numerical)
            fullwork = float(q@(Ks@q))
            work_scale = accepted['work_scale_J']
            if not np.isfinite(work_scale) or work_scale<=0.:
                raise ValueError('existing frozen work normalization required')
            controls = {'relaxed_numerical_work_closure':abs(nwork-completion_full_work)/work_scale,
                'stored_vs_relaxed_numerical_work':abs(float(q@saved_numerical)-nwork)/work_scale,
                'core_completion_work_closure':abs(corework+nwork-fullwork)/work_scale,
                'same_action_shell_equilibrium_work':abs(fullwork-work)/work_scale}
            if any(not np.isfinite(v) or v>1e-8 for v in controls.values()):
                raise ValueError('same-action component work controls failed')
            supports = fixed[fixed<ns]
            root_action = np.zeros(ns)
            root_action[supports] = numerical[supports]
            root = root_action.reshape(1105,6)
            wrench = np.r_[np.sum(root[:,:3],axis=0),
                           np.sum(root[:,3:]+np.cross(xyz,root[:,:3]),axis=0)]
            weighted_numerical = numerical[p]*scales[p]
            weighted_action = action[p]*scales[p]
            report['cases'][case] = {'work_J':work,'physical_core_work_J':corework,
                'relaxed_completion_work_J':nwork,'completion_work_fraction':nwork/work,
                'completion_physical_action_norm':float(np.linalg.norm(weighted_numerical)),
                'completion_action_fraction':float(np.linalg.norm(weighted_numerical)/np.linalg.norm(weighted_action)),
                'saved_vs_relaxed_spin_norm':float(np.linalg.norm(q[d]-dhat)),
                'spin_solve_relative_residual':balance,'work_controls':controls,'frozen_work_scale_J':work_scale,
                'completion_resisting_wrench_on_constrained_shell_coordinates':wrench.tolist(),
                'wrench_origin_m':[0.,0.,0.],
                'wrench_boundary':'completion resisting action only; not total ground reaction or removal-induced change',
                'claim_boundary':'fixed-state action/work decomposition; not removal, root-transfer sensitivity or causal fraction'}
            arrays[case+'_spin_relaxed'] = dhat
            arrays[case+'_completion_action'] = numerical
            arrays[case+'_core_action'] = physical_action
        # No product imports are needed: all operator/state inputs are frozen.
        arrays.update(physical_free=p,spin_free=d)
        np.savez_compressed(output/'actions.npz',**arrays)
        report['status'] = 'COMPLETED_DEVELOPMENT_ONLY'
    except Exception as error:
        report.update(status='failed',error_type=type(error).__name__,error=str(error))
        raise
    finally:
        (output/'result.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':report['status'],'spin_factorizations':1,
        'cases':{k:{n:v for n,v in values.items() if n in ('completion_work_fraction','completion_action_fraction')}
                 for k,values in report['cases'].items()}}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('inputs','inventory','old','completion','original-runner','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    main(args.inputs,args.inventory,args.old,args.completion,args.original_runner,args.output)
