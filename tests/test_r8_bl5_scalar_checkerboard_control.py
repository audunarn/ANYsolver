"""Analytic scalar controls for the prospective F03 inf-sup calculation.

These are independent 1D H1/P1/P0 controls, not a BL5 formulation test or
authorization to transfer an F03 numerical floor to mixed beam/shell meshes.
"""
import numpy as np
import pytest
from scipy import sparse
from scipy.sparse.linalg import spsolve


def _scalar_pair(cells):
    """Unit-interval H1_0 primal P1 stiffness and P0 density work rows."""
    if type(cells) is not int or cells < 2 or cells % 2:
        raise ValueError("even scalar interval count required")
    h = 1. / cells
    primal = cells - 1
    stiffness = sparse.diags(((-1./h)*np.ones(primal-1),
                              (2./h)*np.ones(primal),
                              (-1./h)*np.ones(primal-1)), (-1, 0, 1),
                             format="csc")
    rows, columns, data = [], [], []
    for interval in range(cells):
        for node in (interval, interval+1):
            if 0 < node < cells:
                rows.append(interval)
                columns.append(node-1)
                data.append(h/2.)
    work = sparse.coo_matrix((data, (rows, columns)),
                             shape=(cells, primal)).tocsr()
    return h, stiffness, work


@pytest.mark.parametrize("cells", (4, 8, 16))
def test_nonzero_checkerboard_has_positive_independent_dual_and_zero_p1_work(cells):
    h, stiffness, work = _scalar_pair(cells)
    density = (-1.)**np.arange(cells)
    # Each interior hat sees the average of adjacent opposite densities.
    np.testing.assert_array_equal(work.T@density, np.zeros(cells-1))
    assert np.linalg.norm(density) > 0.
    # Solve -u''=density in H1_0(0,1). Its derivative is the alternating
    # mean h/2 minus the triangular primitive, so ||density||_H-1^2=h^2/12.
    gauss = np.array((-1./np.sqrt(3.), 1./np.sqrt(3.)))
    reference_dual_squared = 0.
    for interval in range(cells):
        primitive = (0. if interval % 2 == 0 else h) + (
            1. if interval % 2 == 0 else -1.)*h*(gauss+1.)/2.
        reference_dual_squared += (h/2.)*sum((primitive-h/2.)**2)
    assert reference_dual_squared == pytest.approx(h*h/12., rel=2e-14)
    assert reference_dual_squared > 0.
    discrete_load = work.T@density
    discrete_dual_squared = float(discrete_load@spsolve(stiffness, discrete_load))
    assert discrete_dual_squared == 0.


@pytest.mark.parametrize("cells", (4, 8, 16))
def test_smooth_density_has_calibrated_nonzero_p1_quotient(cells):
    h, stiffness, work = _scalar_pair(cells)
    density = np.ones(cells)
    load = work.T@density
    discrete_dual_squared = float(load@spsolve(stiffness, load))
    # Continuous -u''=1 has u=x(1-x)/2 and H^-1 norm squared 1/12.
    gauss = np.array((-1./np.sqrt(3.), 1./np.sqrt(3.)))
    continuous_dual_squared = .5*sum((.5-(gauss+1.)/2.)**2)
    assert continuous_dual_squared == pytest.approx(1./12., rel=2e-14)
    expected = (1.-h*h)/12.
    assert discrete_dual_squared == pytest.approx(expected, rel=2e-14)
    assert np.sqrt(discrete_dual_squared/continuous_dual_squared) == pytest.approx(
        np.sqrt(1.-h*h), rel=2e-14)
