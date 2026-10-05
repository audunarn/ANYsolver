"""Small Q4 nested-field and saved-state matrix-action identity checks."""

import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import _b3_e4_f03_variational_attribution as attribution
import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_shell as shell
import _b3_e4_f03_kkt_scaling as scaling


def _shell_at(model,q,x,y):
    ids,weights=shell.sample(model,x,y)
    _,grad,_=shell.shape(model.nodes[list(ids)],'Q4',(x,y))
    local=q[np.array([2*i+axis for i in ids for axis in (0,1)])]
    return (np.asarray(weights)@local.reshape(-1,2),
            shell.strain_matrix(grad)@local)


def _beam_at(n,q,s):
    cell=min(int(s*n),n-1)
    field,strain=beam.fields(s*n-cell,1/n)
    local=q[beam.element_dofs(n,cell)]
    return field@local,strain@local


@pytest.mark.parametrize('mesh',((1,2,1),(2,4,2),(4,8,4)))
def test_q4_beam_nested_off_grid_fields_strains_and_supports(mesh):
    ns,ny,nb=mesh
    p=attribution.nested_q4_prolongation(*mesh)
    coarse=shell.panel(ns,ny,'Q4')
    fine=shell.panel(2*ns,2*ny,'Q4')
    rng=np.random.default_rng(20260922+ns)
    q=rng.normal(size=p.shape[1])*1e-5
    fixed=np.r_[coarse.supported,coarse.dof_count+beam.root_dofs(nb)]
    q[fixed]=0.
    fine_q=p@q
    fixed_f=np.r_[fine.supported,fine.dof_count+beam.root_dofs(2*nb)]
    np.testing.assert_array_equal(fine_q[fixed_f],0.)
    for x,y in ((-.373,-.411),(.027,-.013),(.881,.279),(1.363,.429)):
        cdisp,cstrain=_shell_at(coarse,q[:coarse.dof_count],x,y)
        fdisp,fstrain=_shell_at(fine,fine_q[:fine.dof_count],x,y)
        np.testing.assert_allclose(fdisp,cdisp,rtol=1e-11,atol=1e-17)
        np.testing.assert_allclose(fstrain,cstrain,rtol=1e-11,atol=1e-16)
    for s in (.073,.241,.511,.839,.971):
        cfield,cstrain=_beam_at(nb,q[coarse.dof_count:],s)
        ffield,fstrain=_beam_at(2*nb,fine_q[fine.dof_count:],s)
        np.testing.assert_allclose(ffield,cfield,rtol=1e-11,atol=1e-17)
        np.testing.assert_allclose(fstrain,cstrain,rtol=1e-11,atol=1e-16)
    # Root transverse slope remains independent and maps exactly; it is
    # intentionally absent from the three beam root support coordinates.
    slope=np.zeros(p.shape[1]); slope[coarse.dof_count+2*nb+2]=1.
    prolonged=p@slope
    assert prolonged[fine.dof_count+4*nb+2]==pytest.approx(1.)


@pytest.mark.parametrize('family',('P1','hybrid','enriched'))
def test_saved_state_attribution_signed_identity_and_owned_actions(family):
    ns,ny,nb,nm=1,2,1,2
    p=attribution.nested_q4_prolongation(ns,ny,nb)
    rng=np.random.default_rng(113)
    qm=rng.normal(size=p.shape[1])*1e-5
    coarse=shell.panel(ns,ny,'Q4')
    fine=shell.panel(2*ns,2*ny,'Q4')
    qm[np.r_[coarse.supported,coarse.dof_count+beam.root_dofs(nb)]]=0.
    qf=np.asarray(p@qm).copy()
    fixed_f=np.r_[fine.supported,fine.dof_count+beam.root_dofs(2*nb)]
    perturb=rng.normal(size=len(qf))*1e-7
    perturb[fixed_f]=0.
    qf+=perturb
    c=attribution._fine_constraint(fine,2*nb,2*nm,family,.05)
    lam=rng.normal(size=c.shape[0])*1e4
    metrics,actions=attribution.attribute_saved_states(
        ns,ny,nb,nm,family,qm,qf,lam)
    assert metrics['middle_mesh']==[ns,ny,nb,nm]
    assert metrics['fine_mesh']==[2*ns,2*ny,2*nb,2*nm]
    for key in ('P','K_coarse','K_fine','C_fine'):
        assert sparse.isspmatrix_csr(actions[key])
    np.testing.assert_allclose(actions['P']@actions['q_middle'],
                               actions['prolonged_q'],rtol=0,atol=0)
    pullback=(actions['P'].T@actions['K_fine']@actions['P']-
              actions['K_coarse']).tocsr()
    assert np.linalg.norm(pullback.data)/np.linalg.norm(
        actions['K_coarse'].data)<1e-11
    assert np.linalg.norm(actions['P'].T@actions['f_fine']-
                          actions['f_coarse'])/scaling.F0<1e-11
    np.testing.assert_allclose(actions['K_fine']@actions['e'],actions['Kf_e'])
    np.testing.assert_allclose(actions['C_fine']@actions['e'],actions['Cf_e'])
    np.testing.assert_allclose(actions['K_fine']@actions['prolonged_q'],
                               actions['Kf_prolonged_q'])
    np.testing.assert_allclose(actions['C_fine']@actions['q_fine'],actions['Cf_qfine'])
    np.testing.assert_allclose(actions['C_fine']@actions['prolonged_q'],
                               actions['Cf_prolonged_q'])
    np.testing.assert_allclose(actions['C_fine'].T@actions['lambda_fine'],
                               actions['CfT_lambda'])
    np.testing.assert_allclose(actions['K_fine']@actions['q_fine']+
        actions['C_fine'].T@actions['lambda_fine']-actions['f_fine'],
        actions['r_fine'],rtol=0,atol=1e-10)
    e=actions['e']; split=metrics['shell_dofs_fine']
    assert metrics['shell_distance_j']==pytest.approx(.5*e[:split]@actions['Kf_e'][:split])
    assert metrics['beam_distance_j']==pytest.approx(.5*e[split:]@actions['Kf_e'][split:])
    assert metrics['constraint_mismatch_work_j']==pytest.approx(
        -actions['lambda_fine']@actions['Cf_e'])
    assert metrics['residual_work_j']==pytest.approx(e@actions['r_fine'])
    assert metrics['direct_potential_change_j']==pytest.approx(
        metrics['attributed_potential_change_j'],rel=1e-9,abs=1e-8)
    assert metrics['identity_defect_scaled']<1e-11
    assert metrics['prolonged_fixed_max_abs']==0.
    for key in ('elastic_energy_preservation_error_j',
                'shell_energy_preservation_error_j',
                'beam_energy_preservation_error_j',
                'load_work_preservation_error_j'):
        assert abs(metrics[key])/scaling.E0<1e-11
    before=actions['q_middle'].copy()
    qm[0]=np.nan; qf[0]=np.nan; lam[0]=np.nan
    np.testing.assert_array_equal(actions['q_middle'],before)
    assert np.all(np.isfinite(actions['q_fine']))
    assert np.all(np.isfinite(actions['lambda_fine']))


def test_rejects_bad_saved_state_supports_and_bounds():
    with pytest.raises(ValueError,match='bounded nested Q4'):
        attribution.nested_q4_prolongation(9,16,16)
    p=attribution.nested_q4_prolongation(1,2,1)
    qm=np.zeros(p.shape[1]); qf=np.zeros(p.shape[0])
    fine=shell.panel(2,4,'Q4')
    c=attribution._fine_constraint(fine,2,4,'P1',.05)
    lam=np.zeros(c.shape[0])
    with pytest.raises(ValueError,match='supports'):
        wrong=qm.copy(); wrong[0]=1e-8
        attribution.attribute_saved_states(1,2,1,2,'P1',wrong,qf,lam)
    with pytest.raises(ValueError,match='saved physical'):
        attribution.attribute_saved_states(1,2,1,2,'P1',qm,qf,lam.astype('f4'))
    with pytest.raises(ValueError,match='bounded Q4'):
        attribution.attribute_saved_states(1,2,1,9,'P1',qm,qf,lam)
