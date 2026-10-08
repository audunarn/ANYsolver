"""One fixed-mesh BL5 work allocation; diagnostic only, no product condensation.

Compare exact local stationary elimination, a counterfactual frozen retained
lift, and strong nodal ties. The latter includes five endpoint rows at the
root, unlike integrated BL5. No SPD interpretation or multiplier selection.
"""
from pathlib import Path
from dataclasses import asdict
import argparse
import hashlib
import json
import subprocess
import sys

import anysolver
from anysolver import stiffened_shell
from anysolver._stiffened_shell_ge_experimental import _linear_equilibrium, _scaled_constraint_gap
import numpy as np
import numba
from scipy import sparse
from scipy.sparse.linalg import splu
from threadpoolctl import threadpool_info, threadpool_limits

from b3_e4_f03_bl5_native_nodal_comparator_dev import (
    INTERVALS, LOADS, _load, _metrics, _nodal_rows, _strong_case,
)
from test_stiffened_shell_l1_assembly_experimental import _bl5_joint_mesh_definition

ROOT = Path(__file__).resolve().parents[1]


class DiagnosticNumericalFailure(RuntimeError):
    """A computed counterfactual did not satisfy the existing numerical checks."""


def _quality(owner,k,c,b,w,free,load,q,lam,row_scale):
    residual = k@q+b@lam-load
    equilibrium = _linear_equilibrium(residual[free],load[free],owner._coordinate_scale[free])
    gap = _scaled_constraint_gap(c@q-w@lam,row_scale)
    if equilibrium > 1e-8 or gap > 1e-9:
        raise DiagnosticNumericalFailure(f"equilibrium={equilibrium}, constraint={gap}")
    actual, adjoint = b@lam, c.T@lam
    scale = owner._coordinate_scale[:len(q)]
    relative = float(np.linalg.norm((actual-adjoint)*scale)/max(
        np.linalg.norm(actual*scale),np.linalg.norm(adjoint*scale),1e-20))
    if relative > 1e-8:
        raise DiagnosticNumericalFailure(f"reduced coupling/adjoint work-map defect={relative}")
    return {'scaled_equilibrium':equilibrium,'scaled_constraint':gap,
            'coupling_adjoint_relative_work_norm':relative,
            'coupling_adjoint_actual_work_difference_j':float((actual-adjoint)@q)}


def _add(rows, columns, values, ri, ci, block):
    """Scatter one locally bounded block; never construct a global dense array."""
    rows.extend(np.repeat(ri, len(ci)).tolist())
    columns.extend(np.tile(ci, len(ri)).tolist())
    values.extend(block.ravel().tolist())


def _assemble(shape, triples):
    rows, columns, values = triples
    result = sparse.coo_matrix((values, (rows, columns)), shape=shape).tocsr()
    result.sum_duplicates(); result.eliminate_zeros()
    return result


def _seed(matrix):
    entries = matrix.tocoo()
    return entries.row.tolist(), entries.col.tolist(), entries.data.tolist()


def _reduce(owner):
    k, c = owner._K.tocsr(), owner._C.tocsr()
    n = owner._shell_count + 6*len(owner._beam_ids)
    blocks = len(owner._beam_parts)
    if k.shape != (n+24*blocks, n+24*blocks):
        raise ValueError("diagnostic requires unchanged native generalized layout")
    m = c.shape[0]
    kk, cc, bb, ww = _seed(k[:n, :n]), _seed(c[:, :n]), _seed(c[:, :n].T), ([], [], [])
    maps, retained_blocks = [], []
    for i in range(blocks):
        r = np.arange(n+24*i, n+24*(i+1))
        rr = k[r, :][:, r].tocsc()
        retained_blocks.append(rr)
        rn = k[r, :n]
        p = np.unique(rn.nonzero()[1])
        cr = c[:, r]
        rows = np.unique(cr.nonzero()[0])
        if len(p) > 18 or len(rows) > 10:
            raise ValueError("fixed P0 fixture local scatter exceeded its declared layout")
        factor = splu(rr)
        lift = factor.solve(-rn[:, p].toarray())
        response = factor.solve(cr[rows, :].T.toarray())
        nr = k[p, :][:, r].toarray()
        local_c = cr[rows, :].toarray()
        _add(*kk, p, p, nr@lift)
        _add(*cc, rows, p, local_c@lift)
        _add(*bb, p, rows, -nr@response)
        _add(*ww, rows, rows, local_c@response)
        maps.append((r, p, rows, lift, response))
    defect = k[n:, n:] - sparse.block_diag(retained_blocks, format="csr")
    if np.max(np.abs(defect.data), initial=0.) != 0.:
        raise ValueError("retained blocks are not independent in this fixture")
    return n, _assemble((n,n),kk), _assemble((m,n),cc), _assemble((n,m),bb), _assemble((m,m),ww), maps


def _reconstruct(n, q, lam, maps):
    full = np.zeros(n+24*len(maps)); full[:n] = q
    for r, p, rows, lift, response in maps:
        full[r] = lift@q[p] - response@lam[rows]
    return full


def _solve(k, c, b, w, free, load):
    matrix = sparse.bmat([[k[free,:][:,free], b[free,:]],
                          [c[:,free], -w]], format="csc")
    rhs = np.r_[load[free], np.zeros(c.shape[0])]
    factor = splu(matrix)
    result = factor.solve(rhs)
    for _ in range(2): result += factor.solve(rhs-matrix@result)
    if not np.isfinite(result).all():
        raise ValueError("finite diagnostic solution required")
    q = np.zeros(k.shape[0]); q[free] = result[:len(free)]
    residual = matrix@result-rhs
    return q, result[len(free):], matrix, float(np.linalg.norm(residual)/max(np.linalg.norm(rhs),1.))


def _parity(a, b, n):
    tail_a, tail_b = a[n:].reshape(-1,24), b[n:].reshape(-1,24)
    pairs = (("nodal", a[:n], b[:n]),
             ("retained_rotations", tail_a[:,:6], tail_b[:,:6]),
             ("retained_resultants", tail_a[:,6:], tail_b[:,6:]))
    ratios = {name:float(np.linalg.norm(x-y)/max(np.linalg.norm(y),1e-20))
              for name,x,y in pairs}
    if max(ratios.values()) > 1e-10:
        raise ValueError(f"stationary reconstruction fails registered small-case parity: {ratios}")
    return ratios


def main(destination):
    if destination.exists(): raise FileExistsError("preserve previous decision output")
    destination.mkdir()
    expected = (ROOT/'src/anysolver/__init__.py').resolve()
    if Path(anysolver.__file__).resolve() != expected:
        raise ValueError("decision imported another solver checkout")
    definition = _bl5_joint_mesh_definition(INTERVALS, INTERVALS, 1)
    report = {"status":"IN_PROGRESS", "source_git":subprocess.check_output(
        ['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        "runner_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "imported_anysolver":str(expected), "physical_shell":asdict(definition.shell),
        "runtime":{"python":sys.version,"numba_jit_disabled":bool(numba.config.DISABLE_JIT),
                   "numba_threads":numba.config.NUMBA_NUM_THREADS},
        "beam_definition_hashes":[b.sha256 for b in definition.beams],
        "load":LOADS['mx'], "load_node":101+INTERVALS,
        "supports":[asdict(s) for s in definition.fixed],
        "line":definition.lines[0].descriptor(),
        "limitations":"One fixed reference-linear native torque case; frozen lift is a counterfactual, not product physics. Strong ties include root endpoints. No SPD, external continuous-trace bridge, multiplier selection, F03 or gate acceptance."}
    owner = None
    try:
        with threadpool_limits(limits=1):
            report['threadpools'] = threadpool_info()
            if (not report['threadpools'] or any(p['num_threads']!=1 for p in report['threadpools'])
                    or not numba.config.DISABLE_JIT or numba.config.NUMBA_NUM_THREADS!=1):
                raise ValueError("bounded decision requires effective one-thread/JIT-off settings")
            owner = stiffened_shell.create_analysis(definition=definition)
            report['model_identity'] = owner._identity
            full = owner.solve_linear((stiffened_shell.NodalAction('beam',101+INTERVALS,LOADS['mx']),))
            qw = np.r_[full.shell_displacement,full.beam_coordinates]
            lw = full.multipliers; load = _load(owner,'mx')
            n,k,c,b,w,maps = _reduce(owner)
            free = owner._free[owner._free<n]
            qr,lr,matrix,defect = _solve(k,c,b,w,free,load[:n])
            reconstructed = _reconstruct(n,qr,lr,maps)
            report['full_reconstruction_parity'] = _parity(reconstructed,qw,n)
            report['full_multiplier_parity'] = float(np.linalg.norm(lr-lw)/max(np.linalg.norm(lw),1e-20))
            if report['full_multiplier_parity'] > 1e-10:
                raise ValueError("stationary reconstruction fails multiplier parity")
            report['full_reduced_equilibrium_relative'] = defect
            report['full_reduced_checks'] = _quality(owner,k,c,b,w,free,load[:n],qr,lr,owner._constraint_scale)
            report['full'] = _metrics(owner,qw,lw,owner._C,load)
            nodal = _nodal_rows(owner)
            sm,_,qs,ls = _strong_case(owner,nodal,'mx')
            cn = nodal[:,:n].tocsr()
            qsn,lsn,_,sdefect = _solve(k,cn,cn.T,sparse.csr_matrix((len(ls),len(ls))),free,load[:n])
            strong_reconstruction = _reconstruct(n,qsn,np.zeros_like(lw),maps)
            report['strong_reconstruction_parity'] = _parity(strong_reconstruction,qs,n)
            report['strong_reduced_equilibrium_relative'] = sdefect
            report['strong_reduced_checks'] = _quality(owner,k,cn,cn.T,
                sparse.csr_matrix((len(ls),len(ls))),free,load[:n],qsn,lsn,
                np.asarray(abs(cn)@owner._coordinate_scale[:n]).ravel())
            report['strong_nodal'] = sm
            cross_strong = ls*(nodal@qw)
            cross_weak = lw*(owner._C@qs)
            difference = float(load@(qw-qs))
            closure = float(np.sum(cross_strong)-np.sum(cross_weak)-difference)
            report['reciprocal_cross_work'] = {
                'applied_difference_j':difference,'strong_root_term_j':float(sum(cross_strong[:5])),
                'strong_nonroot_term_j':float(sum(cross_strong[5:])),
                'weak_on_strong_term_j':float(sum(cross_weak)),
                'weak_on_strong_by_channel_j':cross_weak.reshape(5,-1).sum(axis=1).tolist(),
                'closure_j':closure}
            if abs(closure) > 1e-8*max(abs(load@qw),abs(load@qs),1e-20):
                raise ValueError("reciprocal work allocation does not close")
            induced = _reconstruct(n,qw[:n],lw,maps)-_reconstruct(n,qw[:n],np.zeros_like(lw),maps)
            report['retained_correction_work_j'] = float(lw@(owner._C@induced))
            report['negative_lambda_W_lambda_j'] = float(-lw@(w@lw))
            if abs(report['retained_correction_work_j']-report['negative_lambda_W_lambda_j']) > 1e-8*max(abs(load@qw),1e-20):
                raise ValueError("retained correction work does not match exact W action")
            report['effective_trace_on_strong_by_channel'] = np.max(
                np.abs(c@qs[:n]).reshape(5,-1),axis=1).tolist()
            report['projected_action_work_j'] = float((c.T@lw)@qw[:n])
            qf,lf,frozen_full = np.empty(0),np.empty(0),np.empty(0)
            try:
                qf,lf,_,fdefect = _solve(k,c,b,sparse.csr_matrix(w.shape),free,load[:n])
                frozen_full = _reconstruct(n,qf,np.zeros_like(lf),maps)
                checks = _quality(owner,k,c,b,sparse.csr_matrix(w.shape),free,load[:n],qf,lf,owner._constraint_scale)
                report['frozen_lift'] = {'status':'completed','applied_work_j':float(load[:n]@qf),
                    'checks':checks,
                    'reduced_equilibrium_relative':fdefect,
                    'effective_gap_max':float(np.max(np.abs(c@qf))),
                    'full_minus_frozen_work_j':float(load[:n]@(qr-qf)),
                    'frozen_minus_strong_work_j':float(load[:n]@(qf-qsn)),
                    'interface_nodal_action':(-c.T@lf).tolist()}
            except RuntimeError as error:
                report['frozen_lift'] = {'status':('numerical_checks_failed' if
                    type(error) is DiagnosticNumericalFailure else 'backend_failed'),
                    'failure_type':type(error).__name__,'details':str(error)}
            for name,value in (('K',owner._K),('C',owner._C),('C_nodal',nodal),
                               ('Kbar',k),('Cbar',c),('Bbar',b),('W',w)):
                sparse.save_npz(destination/(name+'.npz'),value)
            np.savez_compressed(destination/'states.npz',full=qw,full_lambda=lw,
                reconstructed=reconstructed,reconstructed_lambda=lr,strong=qs,strong_lambda=ls,
                frozen=frozen_full,frozen_lambda=lf,load=load,free=owner._free,
                full_projected_nodal_action=-c.T@lw)
            report['sizes'] = {'nodal':n,'retained':len(qw)-n,'multipliers':len(lw),
                'full_primal':owner._K.shape[0],'reduced_mixed':matrix.shape[0],
                'local_blocks':len(maps),'max_local_retained':24,
                'reduced_nnz':matrix.nnz,'W_nnz':w.nnz}
            report['status'] = 'COMPLETED_NATIVE_ALLOCATION_DIAGNOSTIC'
    except Exception as error:
        report['status'] = 'FAILED';report['failure'] = {'type':type(error).__name__,'details':str(error)}
        raise
    finally:
        if owner is not None: owner.close()
        (destination/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'destination':str(destination)}))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination',type=Path)
    main(parser.parse_args().destination)
