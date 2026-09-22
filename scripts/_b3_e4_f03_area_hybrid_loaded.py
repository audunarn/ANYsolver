"""Bounded three-family classical finite-pad comparison, not qualification.

P1, equal-row endpoint hybrid, and fully enriched P1+endpoints share the
same shell/beam stiffness, load and fixed DOFs. All physical reactions use
the uneliminated signed constraint adjoint. The dense matrices formed by
the auxiliary stability diagnostic have only interface-row dimensions;
the structural solve and its inverse actions remain sparse.
"""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
import math

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu

import _b3_e4_f03_area_hybrid as hybrid
import _b3_e4_f03_area_line as line
import _b3_e4_f03_area_loaded as loaded
import _b3_e4_f03_area_port as port
import _b3_e4_f03_hybrid_stability as stability
import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_line as original
import _b3_e4_f03_independent_shell as shell
import _b3_e4_f03_kkt_scaling as scaling
import _b3_e4_f03_trace_dual as trace_dual


def _layout(n_s: int, n_y: int, n_beam: int, n_mortar: int,
            topology: str, halfwidth: float) -> None:
    if (any(type(value) is not int for value in
            (n_s,n_y,n_beam,n_mortar)) or
            not 1<=n_s<=16 or not 2<=n_y<=32 or
            not 1<=n_beam<=32 or not 2<=n_mortar<=16 or
            topology not in ('Q4','CST-CB') or
            not math.isfinite(halfwidth) or not 1e-4<=halfwidth<=.2):
        raise ValueError('outside bounded finite-pad family comparison')


def _endpoint_operators(model: shell.Panel, n_beam: int,
                        halfwidth: float) -> tuple[sparse.csr_matrix,sparse.csr_matrix]:
    scale=sparse.diags((1.,1.,original.YAW_LENGTH),format='csr')
    return (sparse.vstack((scale@port.pose(model,0.,halfwidth),
                           scale@port.pose(model,1.,halfwidth)),format='csr'),
            sparse.vstack((scale@beam.trace(n_beam,0.),
                           scale@beam.trace(n_beam,1.)),format='csr'))


def _physical_coefficients(family: str, lam: np.ndarray, n_mortar: int
                           ) -> tuple[np.ndarray,np.ndarray]:
    count=3*(n_mortar+1)
    if family=='P1':
        line_lam=lam.copy()
        atoms=np.zeros(6)
    elif family=='hybrid':
        line_lam=np.zeros(count)
        line_lam[3:3*n_mortar]=lam[:3*(n_mortar-1)]
        atoms=lam[3*(n_mortar-1):].copy()
    else:
        line_lam=lam[:count].copy()
        atoms=lam[count:].copy()
    return line_lam,atoms


def _endpoint_gaps(model: shell.Panel, n_beam: int, halfwidth: float,
                   qs: np.ndarray, qb: np.ndarray) -> list[list[float]]:
    gaps=[]
    for station in (0.,1.):
        value=beam.trace(n_beam,station)@qb-port.pose(
            model,station,halfwidth)@qs
        value[2]*=original.YAW_LENGTH
        gaps.append(value.tolist())
    return gaps


def _quarter_wrenches(line_lam: np.ndarray, atoms: np.ndarray,
                      n_mortar: int) -> tuple[list[list[float]],list[list[float]]]:
    line_wrenches=np.asarray(loaded._port_quarters(line_lam,n_mortar,'P1'))
    physical=line_wrenches.copy()
    physical[0]+=(atoms[0],atoms[1],original.YAW_LENGTH*atoms[2])
    physical[3]+=(atoms[3],atoms[4],atoms[4]+original.YAW_LENGTH*atoms[5])
    return line_wrenches.tolist(),physical.tolist()


def solve_case(n_s: int, n_y: int, n_beam: int, n_mortar: int,
               topology: str, halfwidth: float = .05, *,
               family_sink: Callable[[str,dict,np.ndarray,np.ndarray],None] | None = None
               ) -> tuple[dict,dict[str,np.ndarray]]:
    """One bounded smooth-load P1/hybrid/enriched diagnostic comparison.

    No solver retry or threshold-based candidate selection is performed.
    Returned states contain physical full-coordinate q and physical row
    multipliers in each family's actual row order. A family sink receives
    independent copies after each family completes, preserving partial
    diagnostics if a later family fails.
    """
    _layout(n_s,n_y,n_beam,n_mortar,topology,halfwidth)
    model=shell.panel(n_s,n_y,topology)
    ks=shell.stiffness(model)
    kb=beam.assembled_stiffness(n_beam)
    k=sparse.block_diag((ks,kb),format='csr')
    f=np.r_[np.zeros(model.dof_count),beam.assembled_load(n_beam,'smooth')]
    fixed=np.r_[model.supported,model.dof_count+beam.root_dofs(n_beam)]
    free=np.setdiff1d(np.arange(len(f)),fixed)

    cs_p1,cb_p1,_=line.coupling(model,n_beam,n_mortar,'P1',halfwidth)
    cs_end,cb_end=_endpoint_operators(model,n_beam,halfwidth)
    hy=hybrid.assemble(model,n_beam,n_mortar,halfwidth)
    hy_lift=hybrid.assemble(model,n_beam,n_mortar,halfwidth,lifted=True)
    p1_measure=np.full(n_mortar+1,1/n_mortar)
    p1_measure[[0,-1]]*=.5
    families={
        'P1':(cs_p1,cb_p1,np.repeat(p1_measure,3)),
        'hybrid':(hy.cs,hy.cb,hy.row_measures),
        'enriched':(sparse.vstack((cs_p1,cs_end),format='csr'),
                    sparse.vstack((cb_p1,cb_end),format='csr'),
                    np.r_[np.repeat(p1_measure,3),np.ones(6)]),
    }
    c_p1=sparse.hstack((-cs_p1,cb_p1),format='csr')
    base=scaling.build(k,c_p1,f,free,model.dof_count,n_beam,n_mortar,'P1')
    d=base.physical_coordinate_scale
    nfree=len(free)
    primal=base.matrix[:nfree,:nfree].tocsr()
    rhs=base.rhs[:nfree]
    dmatrix=sparse.diags(d,format='csr')
    moment_mask=np.zeros(len(f),dtype=bool)
    u=2*n_beam+1
    v=2*(n_beam+1)
    moment_mask[model.dof_count+u+v:]=True
    moment_mask[model.dof_count+u+1:model.dof_count+u+v:2]=True
    free_scale=np.where(moment_mask[free],scaling.M0,scaling.F0)
    results={}
    states={}
    energies={}
    for family,(cs,cb,measures) in families.items():
        try:
            c=sparse.hstack((-cs,cb),format='csr')
            if (not np.all(np.isfinite(c.data)) or
                    not np.all(np.isfinite(measures)) or
                    np.any(measures<=0)):
                raise ValueError('nonfinite or nonpositive family constraint')
            constraint=(sparse.diags(1/(scaling.U0*measures))@
                        c[:,free]@dmatrix).tocsr()
            if family=='P1':
                reference=base.matrix[nfree:,:nfree].tocsr()
                difference=(constraint-reference).tocsr()
                difference.eliminate_zeros()
                maximum=float(np.max(np.abs(difference.data),initial=0.))
                reference_max=float(np.max(np.abs(reference.data),initial=0.))
                if (constraint.shape!=reference.shape or
                        maximum>1e-12*(1+reference_max)):
                    raise ValueError('P1 sparse scaling parity failed')
            gram32=trace_dual.dual_gram(n_mortar,family,32)
            gram64=trace_dual.dual_gram(n_mortar,family,64)
            diagnostic,g3=stability.diagnose(primal,constraint,gram32,gram64)
            matrix,load=stability.normalized_kkt(primal,constraint,rhs)
            solution=splu(matrix).solve(load)
            if not np.all(np.isfinite(solution)):
                raise ValueError('nonfinite family KKT solution')
            q=np.zeros(len(f))
            q[free]=d*solution[:nfree]
            muhat=solution[nfree:]
            lam=scaling.E0/(scaling.U0*measures)*muhat
            qs=q[:model.dof_count]
            qb=q[model.dof_count:]
            residual=k@q+c.T@lam-f
            weak=c@q
            shell_energy=float(.5*qs@(ks@qs))
            beam_energy=float(.5*qb@(kb@qb))
            external=float(f@q)
            interface=float(lam@weak)
            energy_scaled=float(abs(2*(shell_energy+beam_energy)+
                                    interface-external)/scaling.E0)
            free_error=float(np.max(np.abs(residual[free])/free_scale))
            weak_error=float(np.max(np.abs(weak)/
                                    (scaling.U0*measures)))
            nx=2*n_s
            left=np.array([j*(nx+1) for j in range(n_y+1)],dtype=int)
            right=left+nx
            root=beam.root_dofs(n_beam)
            wrenches=(loaded._edge_wrench(model,residual,left),
                      loaded._edge_wrench(model,residual,right),
                      tuple(map(float,residual[model.dof_count+root])))
            applied=np.array((0.,scaling.F0,scaling.M0/2))
            balance=np.sum(np.asarray(wrenches),axis=0)+applied
            balance=np.array((balance[0]/scaling.F0,
                              balance[1]/scaling.F0,
                              balance[2]/scaling.M0))
            root_elastic=np.asarray((kb@qb)[root])
            root_port=np.asarray((cb.T@lam)[root])
            root_load=f[model.dof_count+root]
            line_lam,atoms=_physical_coefficients(family,lam,n_mortar)
            root_line=np.asarray((cb_p1.T@line_lam)[root])
            root_endpoint=np.asarray((cb_end.T@atoms)[root])
            line_quarters,physical_quarters=_quarter_wrenches(
                line_lam,atoms,n_mortar)
            tip=beam.trace(n_beam,1.)@qb
            tip[2]*=original.YAW_LENGTH
            gap,_=loaded._gap(model,n_beam,n_mortar,halfwidth,qs,qb)
            dual_squared=float(muhat@g3@muhat)
            if not math.isfinite(dual_squared) or dual_squared<0:
                raise ValueError('nonfinite or negative independent dual quadratic form')
            dual=float(math.sqrt(dual_squared)*scaling.E0/scaling.U0)
            if family=='hybrid':
                # The lifted basis must describe the same finite hybrid
                # functional after its exact multiplier change of basis.
                lifted_lam=hybrid.from_physical_multipliers(lam,n_mortar)
                clift=sparse.hstack((-hy_lift.cs,hy_lift.cb),format='csr')
                np.testing.assert_allclose(clift.T@lifted_lam,c.T@lam,
                                           rtol=2e-11,atol=2e-7)
                np.testing.assert_allclose(lifted_lam@(clift@q),interface,
                                           rtol=2e-11,atol=2e-8)
            values=(shell_energy,beam_energy,external,interface,energy_scaled,
                    free_error,weak_error,*balance,*tip,*root_elastic,
                    *root_port,*root_load,*root_line,*root_endpoint,gap,dual,
                    *(x for group in wrenches for x in group),
                    *(x for group in physical_quarters for x in group))
            if not np.all(np.isfinite(values)):
                raise ValueError('nonfinite physical family observable')
            if not np.allclose(root_line+root_endpoint,root_port,
                               rtol=1e-10,atol=1e-5):
                raise ValueError('root line/endpoint port split failed')
            if not np.allclose(root_elastic+root_port-root_load,wrenches[2],
                               rtol=1e-10,atol=1e-5):
                raise ValueError('beam-root physical wrench partition failed')
            results[family]={
                'free_residual_scaled':free_error,
                'weak_gap_scaled':weak_error,
                'balance_scaled':balance.tolist(),
                'energy_scaled':energy_scaled,
                'shell_energy_j':shell_energy,
                'beam_energy_j':beam_energy,
                'external_work_j':external,
                'interface_work_j':interface,
                'support_wrenches':[list(w) for w in wrenches],
                'tip_pose_m':tip.tolist(),
                'root_elastic_wrench':root_elastic.tolist(),
                'root_port_wrench':root_port.tolist(),
                'root_load_wrench':root_load.tolist(),
                'root_line_wrench':root_line.tolist(),
                'root_endpoint_wrench':root_endpoint.tolist(),
                'physical_line_coefficients':line_lam.reshape(n_mortar+1,3).tolist(),
                'endpoint_atoms':atoms.reshape(2,3).tolist(),
                'line_quarter_wrenches':line_quarters,
                'physical_quarter_wrenches':physical_quarters,
                'endpoint_gaps_m':_endpoint_gaps(model,n_beam,halfwidth,qs,qb),
                'gap_l2_m':gap,
                'stability':diagnostic,
                'combined_dual_norm_N':dual,
            }
            energies[family]=shell_energy+beam_energy
            states[f'{family}_q']=q
            states[f'{family}_lambda']=lam
            if family_sink is not None:
                family_sink(family,deepcopy(results[family]),q.copy(),lam.copy())
        except Exception as exc:
            exc.add_note(f'{family} finite-pad family solve failed')
            raise
    order=max(0.,energies['enriched']-energies['P1'],
              energies['enriched']-energies['hybrid'])/scaling.E0
    return ({'topology':topology,'mesh':[n_s,n_y,n_beam,n_mortar],
             'halfwidth_m':halfwidth,'families':results,
             'enriched_energy_order_scaled':float(order)},states)
