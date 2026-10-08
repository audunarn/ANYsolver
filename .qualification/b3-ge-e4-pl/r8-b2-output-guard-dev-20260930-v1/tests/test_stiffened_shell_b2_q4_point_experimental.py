"""Physical Q4/B2 reference-point solve through the experimental owner."""

import numpy as np
from scipy import sparse
from scipy.linalg import null_space

from anysolver._stiffened_shell_b2_q4_point_experimental import (
    create_experimental_b2_q4_point_analysis,
)
from anysolver import stiffened_shell
from test_b2_f10_f11_point_attachment import VERTICES, specimen


def test_q4_b2_point_owner_matches_independent_reduced_work_and_reactions():
    member, law, shell_k, beam_k = specimen()
    fixed = set(range(6)) | set(range(18, 24)) | set(range(24, 30))
    fixed.update(6*i+j for i in (1, 2) for j in (3, 4, 5))
    free = np.array([i for i in range(36) if i not in fixed])
    T = sparse.eye(36, format="csr")[:, free]
    u0 = np.zeros(36)
    analysis = stiffened_shell.create_analysis(definition=
        stiffened_shell.B2Q4PointDefinition(
            stiffened_shell.B2_E4_PL_FAST_LINEAR_V1,
            member, VERTICES, 1000., .3, .15, .4, T, u0,
            offset_local_m=(0., .08, -.03)))
    assert analysis.capabilities.status == "experimental"
    assert not analysis.capabilities.production_qualified
    T.data[:] = 0.
    u0[:] = 1.

    full_k = np.zeros((36, 36))
    full_k[:24, :24] = shell_k
    full_k[24:, 24:] = beam_k
    c = law.constraint[:, free]
    z = null_space(c)
    reduced_k = full_k[np.ix_(free, free)]
    for multiplier in (1., 2.):
        load = np.zeros(36)
        load[12] = .15*multiplier
        load[13] = -.09*multiplier
        load[32] = .11*multiplier
        load[33] = .035*multiplier
        result = analysis.solve_linear(load)
        assert result.status == "completed" and result.failure_reason is None
        assert result.factorization_count == 1
        displacement = np.asarray(result.displacements)
        lam = np.asarray(result.multiplier)
        reactions = np.asarray(result.affine_reactions)
        expected_free = z @ np.linalg.solve(
            z.T @ reduced_k @ z, z.T @ load[free])
        expected_lam = np.linalg.lstsq(
            c.T, load[free]-reduced_k @ expected_free, rcond=None)[0]
        np.testing.assert_allclose(displacement[free], expected_free,
                                   rtol=2e-10, atol=2e-11)
        np.testing.assert_allclose(lam, expected_lam,
                                   rtol=2e-10, atol=2e-11)
        np.testing.assert_allclose(displacement[list(fixed)], 0., atol=1e-13)
        np.testing.assert_allclose(law.constraint @ displacement,
                                   result.point_gap, atol=1e-11)
        np.testing.assert_allclose(reactions[free], 0., atol=1e-10)
        assert np.linalg.norm(reactions[list(fixed)]) > 0.
        assert abs(displacement @ load - 2*result.internal_strain_energy) < 1e-10
        assert len(result.beam_resultants_local) == 3
    analysis.close()


def test_q4_b2_point_solver_failure_is_not_success(monkeypatch):
    member, _, _, _ = specimen()
    fixed = set(range(6)) | set(range(18, 24)) | set(range(24, 30))
    fixed.update(6*i+j for i in (1, 2) for j in (3, 4, 5))
    free = np.array([i for i in range(36) if i not in fixed])
    analysis = create_experimental_b2_q4_point_analysis(
        member, VERTICES, shell_E=1000., shell_nu=.3,
        shell_thickness_m=.15, station=.4,
        offset_local_m=(0., .08, -.03),
        transformation=sparse.eye(36, format="csr")[:, free],
        prescribed_offset=np.zeros(36))
    def numerical_failure(_rhs):
        raise RuntimeError("Sparse solve produced NaN/Inf values")
    monkeypatch.setattr(analysis._handle, "solve", numerical_failure)
    result = analysis.solve_linear(np.zeros(36))
    assert result.status == "failed" and result.displacements == ()
    assert "NaN/Inf" in result.failure_reason
    analysis.close()


def test_q4_b2_point_extreme_finite_load_cannot_report_success():
    member, _, _, _ = specimen()
    fixed = set(range(6)) | set(range(18, 24)) | set(range(24, 30))
    fixed.update(6*i+j for i in (1, 2) for j in (3, 4, 5))
    free = np.array([i for i in range(36) if i not in fixed])
    analysis = create_experimental_b2_q4_point_analysis(
        member, VERTICES, shell_E=1000., shell_nu=.3,
        shell_thickness_m=.15, station=.4,
        offset_local_m=(0., .08, -.03),
        transformation=sparse.eye(36, format="csr")[:, free],
        prescribed_offset=np.zeros(36))
    load = np.zeros(36)
    load[33] = np.finfo(float).max
    with np.errstate(over="ignore", invalid="ignore"):
        result = analysis.solve_linear(load)
    assert result.status == "failed"
    assert result.displacements == ()
    analysis.close()
