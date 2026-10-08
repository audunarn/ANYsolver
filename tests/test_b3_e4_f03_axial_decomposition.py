"""Independent bounded checks of shell/beam line-Schur decomposition."""

from pathlib import Path
import sys

import numpy as np
import pytest
from scipy import linalg

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import _b3_e4_f03_axial_decomposition as patch
import _b3_e4_f03_nm128_stability as stability


@pytest.mark.parametrize('topology',('Q4','CST-CB'))
def test_bounded_side_actions_reconstruct_existing_total(topology):
    result,matrices=patch.decompose(2,4,64,64,topology,retain_matrices=True)
    existing,payload=stability.analyze(2,4,64,64,topology,
                                       retain_matrices=True)
    np.testing.assert_allclose(matrices['total'],payload['schur'],
                               rtol=2e-8,atol=2e-8)
    np.testing.assert_allclose(matrices['dual'],payload['dual'],
                               rtol=0,atol=0)
    assert existing['numerical_checks_pass']
    assert result['axial_shell_action']>0 and result['axial_beam_action']>0
    assert result['axial_shell_action']+result['axial_beam_action']==pytest.approx(
        result['axial_minimum_generalized_eigen'],rel=1e-10)
    assert 0<result['axial_shell_fraction']<1
    assert result['primal_cross_block_max']==0
    assert result['primal_skew']<1e-10
    assert result['max_side_solve_residual']<1e-9
    assert result['axial_eigen_residual']<1e-9
    assert len(result['side_alone_axial_status'])==2
    axial=np.arange(0,matrices['total'].shape[0],3)
    first=linalg.eigh(matrices['total'][np.ix_(axial,axial)],
                      matrices['dual'][np.ix_(axial,axial)],
                      eigvals_only=True)[0]
    assert result['axial_minimum_generalized_eigen']==pytest.approx(first)


def test_invalid_bounded_patch_rejected():
    with pytest.raises(ValueError,match='unsupported'):
        patch.decompose(128,64,512,128,'Q4')


@pytest.mark.parametrize('topology',('Q4','CST-CB'))
def test_same_nested_traction_preserves_both_side_actions(topology):
    coarse,low=patch.decompose(2,4,64,32,topology,retain_matrices=True)
    fine,high=patch.decompose(2,4,64,64,topology,retain_matrices=True)
    interpolation=np.zeros((65,33))
    for node in range(33):
        interpolation[2*node,node]=1
    for node in range(32):
        interpolation[2*node+1,node:node+2]=.5
    transform=np.kron(interpolation,np.eye(3))
    # Independent shared-traction work check, not only sum additivity.
    for side in ('shell','beam'):
        np.testing.assert_allclose(transform.T@high[side]@transform,low[side],
                                   rtol=1e-8,atol=1e-8)
    assert fine['mesh']['n_mortar']==2*coarse['mesh']['n_mortar']
