"""Independent small-system work and solution parity for KKT scaling."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pytest
from scipy import sparse
from scipy.sparse.linalg import spsolve

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_line as line
import _b3_e4_f03_independent_shell as shell
import _b3_e4_f03_kkt_scaling as scaling


@pytest.mark.parametrize('topology',('Q4','CST'))
@pytest.mark.parametrize('law',('P0','P1'))
def test_scaled_saddle_is_exact_congruence_and_recovers_small_solution(topology,law):
    model=shell.panel(3,6,topology)
    nb=6; nm=3
    ks=shell.stiffness(model); kb=beam.assembled_stiffness(nb)
    cs,cb,_=line.coupling(model,nb,nm,law)
    k=sparse.block_diag((ks,kb),format='csr')
    c=sparse.hstack((-cs,cb),format='csr')
    f=np.r_[np.zeros(model.dof_count),beam.assembled_load(nb,'smooth')]
    fixed=np.r_[model.supported,model.dof_count+beam.root_dofs(nb)]
    free=np.setdiff1d(np.arange(k.shape[0]),fixed)
    physical=sparse.bmat(((k[free,:][:,free],c[:,free].T),
                          (c[:,free],None)),format='csc')
    b=np.r_[f[free],np.zeros(c.shape[0])]
    transformed=scaling.build(k,c,f,free,model.dof_count,nb,nm,law)
    # Check the physical layout independently of the scaling helper.  The
    # chosen L0 is one metre, so angular and translational numerical scales
    # coincide here; their classification still matters for other lengths.
    beam_global=free-model.dof_count
    u_start=2*nb+1
    theta_start=u_start+2*(nb+1)
    expected_angular=((beam_global>=u_start)&
                      (beam_global<theta_start)&
                      ((beam_global-u_start)%2==1)) | (beam_global>=theta_start)
    np.testing.assert_array_equal(transformed.angular_free_mask,expected_angular)
    expected_measure=np.full(nm+(law=='P1'),1/nm)
    if law=='P1':
        expected_measure[0]=expected_measure[-1]=1/(2*nm)
    np.testing.assert_allclose(transformed.physical_multiplier_scale,
                               np.repeat(scaling.F0/expected_measure,3),rtol=1e-14)
    # The root theta is supported; the first mortar row therefore has the
    # exact quadratic-interpolation deficit 1/12 (P0) or 1/6 (P1).
    # All remaining rows integrate a unit rotation over their test support.
    unit_rotation=np.zeros(len(free))
    unit_rotation[beam_global>=theta_start]=1
    weak=transformed.matrix[len(free):,:len(free)]@unit_rotation
    expected_yaw=np.full(len(expected_measure),line.YAW_LENGTH/scaling.L0)
    expected_yaw[0]*=(5/6 if law=='P1' else 11/12)
    np.testing.assert_allclose(weak.reshape(-1,3)[:,2],expected_yaw,
                               rtol=1e-12,atol=1e-12)
    np.testing.assert_allclose(weak.reshape(-1,3)[:,:2],0,atol=1e-12)
    diagonal=np.r_[transformed.physical_coordinate_scale,
                   transformed.physical_multiplier_scale]
    t=sparse.diags(diagonal)
    expected=(t@physical@t)*(1/scaling.E0)
    np.testing.assert_allclose(transformed.matrix.toarray(),expected.toarray(),
                               rtol=1e-13,atol=1e-14)
    np.testing.assert_allclose(transformed.rhs,diagonal*b/scaling.E0,
                               rtol=1e-14,atol=1e-15)
    original=spsolve(physical,b)
    scaled=spsolve(transformed.matrix,transformed.rhs)
    q,lam=transformed.recover(scaled)
    np.testing.assert_allclose(q,original[:len(free)],rtol=1e-7,atol=1e-9)
    np.testing.assert_allclose(lam,original[len(free):],rtol=1e-7,atol=1e-5)
    assert np.max(np.abs(transformed.matrix@scaled-transformed.rhs))<1e-8
    physical_residual=physical@np.r_[q,lam]-b
    scaled_residual=transformed.matrix@scaled-transformed.rhs
    np.testing.assert_allclose(scaled_residual,
                               diagonal*physical_residual/scaling.E0,
                               rtol=0,atol=1e-10)
    full=np.zeros(k.shape[0]); full[free]=q
    np.testing.assert_allclose(full@(k@full),f@full,rtol=1e-8,atol=1e-7)
    assert np.linalg.norm(c@full)<1e-8
