"""Analytical membrane and four-sample work checks for F03 comparator."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import _b3_e4_f03_independent_shell as shell


def affine(model, gradient, translation=(0.,0.)):
    return (model.nodes@np.asarray(gradient).T+translation).ravel()


@pytest.mark.parametrize('topology',('Q4','CST'))
def test_plane_stress_affine_patch_and_internal_equilibrium(topology):
    model=shell.panel(2,4,topology)
    gradient=np.array(((.8e-3,-.3e-3),(.2e-3,-.4e-3)))
    strain=np.array((gradient[0,0],gradient[1,1],gradient[0,1]+gradient[1,0]))
    q=affine(model,gradient)
    k=shell.stiffness(model)
    expected=2*shell.THICKNESS*(strain@shell.CONSTITUTIVE@strain)
    np.testing.assert_allclose(q@(k@q),expected,rtol=2e-11)
    translated=affine(model,gradient,translation=(.13,-.27))
    # Large rigid translations in q^T K q amplify floating cancellation.
    np.testing.assert_allclose(translated@(k@translated),expected,rtol=1e-8)
    interior=np.array([2*(j*(2*model.n_s+1)+i)+d
                       for j in range(1,model.n_y) for i in range(1,2*model.n_s)
                       for d in (0,1)])
    assert np.linalg.norm((k@q)[interior])/np.linalg.norm(k@q)<1e-11
    np.testing.assert_allclose((k-k.T).data,0,rtol=0,atol=1e-5)


@pytest.mark.parametrize('topology',('Q4','CST'))
def test_rigid_pose_and_virtual_work(topology):
    model=shell.panel(4,6,topology)
    tx,ty,spin=.018,-.012,.003
    q=np.column_stack((tx-spin*model.nodes[:,1],
                       ty+spin*model.nodes[:,0])).ravel()
    k=shell.stiffness(model)
    assert np.linalg.norm(k@q)/(sparse_norm(k)*np.linalg.norm(q))<1e-13
    for s in (0.,.125,.5,.75,1.):
        p=shell.pose(model,s)
        np.testing.assert_allclose(p@q,[tx,ty+spin*s,spin],rtol=2e-13,atol=1e-15)
        wrench=np.array((125.,-930.,72.))
        nodal=np.asarray(p.T@wrench).ravel()
        np.testing.assert_allclose(nodal[0::2].sum(),wrench[0],rtol=2e-13)
        np.testing.assert_allclose(nodal[1::2].sum(),wrench[1],rtol=2e-13)
        moment=(model.nodes[:,0]-s)@nodal[1::2]-model.nodes[:,1]@nodal[0::2]
        np.testing.assert_allclose(moment,wrench[2],rtol=2e-13,atol=1e-11)
        np.testing.assert_allclose(q@nodal,wrench@(p@q),rtol=2e-13,atol=1e-12)


def sparse_norm(matrix):
    return np.sqrt(matrix.multiply(matrix).sum())


def test_q4_cst_affine_pose_and_energy_parity():
    gradient=np.array(((.001,.0004),(-.0007,.0003)))
    models=[shell.panel(4,6,name) for name in ('Q4','CST')]
    for model in models:
        q=affine(model,gradient)
        for s in (0.,.125,.5,.875,1.):
            p=shell.pose(model,s)
            offsets=np.array(shell.OFFSETS)
            displaced=offsets@gradient.T
            expected_yaw=np.sum(offsets[:,0]*displaced[:,1]-
                                offsets[:,1]*displaced[:,0])/shell.YAW_DENOMINATOR
            np.testing.assert_allclose(p@q,[gradient[0,0]*s,gradient[1,0]*s,expected_yaw],
                                       rtol=1e-12,atol=1e-15)
    energies=[affine(m,gradient)@(shell.stiffness(m)@affine(m,gradient)) for m in models]
    np.testing.assert_allclose(energies[0],energies[1],rtol=1e-11)


@pytest.mark.parametrize('topology',('Q4','CST'))
def test_hand_derived_uniaxial_and_shear_energy(topology):
    model=shell.panel(3,4,topology)
    elastic=210e9; poisson=.3; thickness=.07; area=2.
    eps=.0007
    uniaxial=np.array(((eps,0.),(0.,-poisson*eps)))
    q=affine(model,uniaxial)
    np.testing.assert_allclose(q@(shell.stiffness(model)@q),
                               area*thickness*elastic*eps**2,rtol=2e-11)
    gamma=.0009
    pure_shear=np.array(((0.,gamma/2),(gamma/2,0.)))
    q=affine(model,pure_shear)
    shear_modulus=elastic/(2*(1+poisson))
    np.testing.assert_allclose(q@(shell.stiffness(model)@q),
                               area*thickness*shear_modulus*gamma**2,rtol=2e-11)


def test_host_lines_and_cst_diagonal_are_continuous():
    delta=1e-9
    for topology in ('Q4','CST'):
        model=shell.panel(5,10,topology)
        q=np.sin(np.arange(model.dof_count)*.717)*.001
        # Both x sample coordinates at s=.1 fall on shell x-grid lines.
        for s in (.1,.16):
            left=np.asarray(shell.pose(model,s-delta)@q).ravel()
            exact=np.asarray(shell.pose(model,s)@q).ravel()
            right=np.asarray(shell.pose(model,s+delta)@q).ravel()
            assert np.linalg.norm(left-exact)<1e-8
            assert np.linalg.norm(right-exact)<1e-8
        if topology=='CST':
            # y=.23 in the cell y=.2..3: its BL→TR diagonal crosses x=-.04.
            before=shell.sample(model,-.04-delta,.23)[0]
            after=shell.sample(model,-.04+delta,.23)[0]
            assert before!=after
            for x in (-.04-delta,-.04,-.04+delta):
                ids,weights=shell.sample(model,x,.23)
                assert len(ids)==3
                np.testing.assert_allclose(sum(weights),1,rtol=0,atol=1e-12)
    with pytest.raises(ValueError,match='axis-aligned'):
        bad=np.array(((0.,0.),(1.,0.),(1.1,1.),(0.,1.)))
        shell.shape(bad,'Q4',(.5,.5))


@pytest.mark.parametrize('topology',('Q4','CST'))
def test_nonaffine_pose_from_individual_samples_and_directional_work(topology):
    model=shell.panel(5,10,topology)
    s=.337
    q=np.cos(np.arange(model.dof_count)*.47)*.002
    dq=np.sin(np.arange(model.dof_count)*.31)*.0003
    def from_samples(vector):
        displacements=[]
        for dx,dy in ((-.2,-.23),(.2,-.23),(.2,.23),(-.2,.23)):
            indices,weights=shell.sample(model,s+dx,dy)
            displacements.append(weights@vector.reshape(-1,2)[list(indices)])
        displacements=np.array(displacements)
        x=np.array((-.2,.2,.2,-.2))
        y=np.array((-.23,-.23,.23,.23))
        return np.r_[displacements.mean(axis=0),
                     (x@displacements[:,1]-y@displacements[:,0])/
                     (4*(.2**2+.23**2))]
    p=shell.pose(model,s)
    np.testing.assert_allclose(p@q,from_samples(q),rtol=1e-12,atol=1e-15)
    wrench=np.array((125.,-930.,72.))
    step=.001
    numerical=(from_samples(q+step*dq)-from_samples(q-step*dq))/(2*step)
    np.testing.assert_allclose(dq@(p.T@wrench),wrench@numerical,rtol=1e-10)
