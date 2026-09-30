"""Lever arms and joint constraints must survive reaction recovery."""
from types import SimpleNamespace
import numpy as np
import pytest
from docs.d1_review_support.d1_guided_reaction_wrench import guided_wrench_diagnostics


def fixture():
    nodes = {1: SimpleNamespace(x=0., y=0., z=0.),
             2: SimpleNamespace(x=2., y=0., z=0.)}
    dofs = SimpleNamespace(total_dofs=12,
        get_node_dofs=lambda node: np.arange(6*(node-1), 6*node))
    return SimpleNamespace(mesh=SimpleNamespace(nodes=nodes, dof_manager=dofs))


def check(model, structural, contact, external, free=None, u=None, force=(0.,0.,0.), moment=(0.,0.,0.)):
    return guided_wrench_diagnostics(model, np.zeros(12) if u is None else u,
        structural, contact, external, np.zeros((12,0)) if free is None else free,
        physical_contact_force=force, physical_contact_moment=moment,
        origin=(0.,0.,0.), force_scale_n=1., moment_scale_nm=1.)


def test_mpc_and_path_reactions_use_both_nodes_and_lever_arms():
    # Distributed boundary actuation: opposite vertical forces have a couple,
    # despite their zero sum. Neither slave-only nor six-component sums suffice.
    ext=np.zeros(12); ext[2]=1.; ext[8]=-1.
    result=check(fixture(),np.zeros(12),np.zeros(12),ext)
    np.testing.assert_array_equal(result['total_reaction_wrench'],[0,0,0,0,-2,0])
    np.testing.assert_array_equal(result['total_balance_defect'],np.zeros(6))


def test_residual_is_not_a_constrained_reaction():
    structural=np.zeros(12); structural[2]=3.
    free=np.zeros((12,1)); free[2,0]=2.
    result=check(fixture(),structural,np.zeros(12),np.zeros(12),free)
    np.testing.assert_array_equal(result['total_reaction_wrench'],np.zeros(6))
    assert result['constraint_reconstruction_relative_force']==3.


def test_current_lever_arm_and_physical_contact_sign():
    contact=np.zeros(12); contact[8]=-4.
    u=np.zeros(12);u[6]=1.
    result=check(fixture(),np.zeros(12),contact,np.zeros(12),u=u,
                 force=(0,0,4),moment=(0,-12,0))
    assert result['contact_conversion_max_scaled']==0.
    assert result['balance_relative_force']==0.
    assert result['balance_relative_moment']==0.


def test_structural_angular_defect_is_measured_not_assumed_zero():
    internal=np.zeros(12);internal[2]=1.;internal[8]=-1.
    result=check(fixture(),internal,np.zeros(12),np.zeros(12))
    assert result['structural_internal_max_scaled']==2.
    assert result['balance_relative_moment']==2.


def test_equal_opposite_body_map_defects_cannot_cancel():
    contact=np.zeros(12);contact[0]=-1.;contact[6]=1.
    result=guided_wrench_diagnostics(fixture(),np.zeros(12),np.zeros(12),
        contact,np.zeros(12),np.zeros((12,0)),
        physical_contact_force=(0,0,0),physical_contact_moment=(0,0,0),
        origin=(0,0,0),force_scale_n=1.,moment_scale_nm=1.,
        bodies={'source':dict(node_ids=(1,),physical_contact_force=(2,0,0),
                             physical_contact_moment=(0,0,0)),
                'target':dict(node_ids=(2,),physical_contact_force=(-2,0,0),
                             physical_contact_moment=(0,0,0))})
    assert result['contact_conversion_max_scaled']==0.
    assert result['balance_relative_force']==0.
    for body in result['bodies'].values():
        assert body['contact_conversion_max_scaled']==1.
        assert body['balance_relative_force']==1.


@pytest.mark.parametrize('defect',['rotation','free_rotation','wide_map','rank','scale'])
def test_rejects_invalid_work_scope(defect):
    kwargs={};u=np.zeros(12);free=np.zeros((12,0))
    if defect=='rotation': u[3]=1e-8
    elif defect=='free_rotation':
        free=np.zeros((12,1));free[3,0]=1.
    elif defect=='wide_map': free=np.column_stack((np.eye(12),np.ones(12)))
    elif defect=='rank': free=np.zeros((12,1))
    else: kwargs['force_scale_n']=0.
    with pytest.raises(ValueError):
        guided_wrench_diagnostics(fixture(),u,np.zeros(12),np.zeros(12),np.zeros(12),free,
            physical_contact_force=(0,0,0),physical_contact_moment=(0,0,0),**kwargs)
