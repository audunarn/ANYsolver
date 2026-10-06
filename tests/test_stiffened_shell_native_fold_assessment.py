"""SOURCE_ONLY_UNRUN exact bounded controls for the supported tangent tool.

Toy controls test the mathematical caller contract independently of the panel.
They are not numerical, physical or scientific acceptance of saved checkpoints.
"""
import numpy as np
import pytest
from scipy import sparse
from examples import stiffened_shell_native_fold_assessment as fold


def scalar_tangent(stiffness,*,length=1.,column=1.,row=1.,orientation=1):
    result = fold.supported_branch_tangent(sparse.csc_matrix([[stiffness]]),np.array([1.]),
        np.array([0]),tip_dof=0,physical_translation_dofs=np.array([0]),length=length,
        column_scales=np.array([column]),row_scales=np.array([row]),constraint_start=1,
        orientation=orientation)
    result['status'] = 'SUPPORTED_TANGENT_EVIDENCE'
    return result


def test_exact_scalar_fold_uses_equilibrium_tangent_and_physical_orientation():
    # R=1-u^2-lambda, p=1. Therefore d(lambda)/du=-2u.
    rows = [scalar_tangent(-2*u) for u in (-.125,0.,.125)]
    np.testing.assert_allclose([r['d_factor_d_tip'] for r in rows],(.25,0.,-.25),
                               rtol=0.,atol=1e-14)  # Well-conditioned toy limit.
    assert fold.supported_sign_assessment(rows)['status'] == 'CANDIDATE'
    assert all(abs(r['residuals']['physical_control_residual']) <= 1e-14 for r in rows)
    assert all(r['residuals']['equation_reference_work_ratio'] <= 1e-14 for r in rows)
    assert not fold.supported_sign_assessment(rows)['simple_fold_proved']
    with pytest.raises(fold.AssessmentRefusal,match='fixed_positive_physical_orientation'):
        scalar_tangent(.25,orientation=-1)


def test_load_reversal_alone_and_orientation_invention_do_not_prove_fold():
    raw = [dict(proportional_factor=factor) for factor in (.7,.8,.75)]
    assert fold.supported_sign_assessment(raw)['status'] == 'INCONCLUSIVE'
    supported = [dict(scalar_tangent(2.),proportional_factor=row['proportional_factor']) for row in raw]
    assert fold.supported_sign_assessment(supported)['status'] == 'NO_SUPPORTED_TANGENT_SIGN_BRACKET'
    assert not fold.supported_sign_assessment(supported)['capacity_proved']


def test_indefinite_nonsymmetric_saddle_keeps_algebraic_variables():
    # R0=1-u^2-lambda; R1=2m; R2=3z-7m. The exact tangent is
    # (du,dz,dm,d(lambda))=(1,0,0,-2u), despite indefinite/nonsymmetric J.
    rows = []
    for u in (-.125,0.,.125):
        matrix = sparse.csc_matrix([[-2*u,0.,0.],[0.,0.,2.],[0.,3.,-7.]])
        row = fold.supported_branch_tangent(matrix,np.array([1.,0.,0.]),np.arange(3),
            tip_dof=0,physical_translation_dofs=np.array([0]),length=1.,
            column_scales=np.array([2.,3.,5.]),row_scales=np.array([.5,.25,.125]),
            constraint_start=2)
        np.testing.assert_allclose(row['tangent'],(1.,0.,0.),rtol=0.,atol=1e-14)
        assert row['load_tangent'] == pytest.approx(-2*u,abs=1e-14)
        assert row['residuals']['original_compatibility_residual'] == [0.]
        rows.append(dict(row,status='SUPPORTED_TANGENT_EVIDENCE'))
    assert fold.supported_sign_assessment(rows)['status'] == 'CANDIDATE'


@pytest.mark.parametrize('matrix,direction',(
    ([[1.,0.],[0.,0.]],[1.,0.]),  # Independent unsupported algebraic null mode.
    ([[0.,0.],[0.,1.]],[0.,1.]),  # Pitchfork branch u=0, load column cannot span its row.
    ([[0.,0.],[0.,0.]],[1.,0.])))  # Degenerate multi-null border.
def test_bifurcation_and_unresolved_null_borders_refuse(matrix,direction):
    with pytest.raises(fold.AssessmentRefusal,match='singular_or_nonfinite_supported_border'):
        fold.supported_branch_tangent(sparse.csc_matrix(matrix),np.array(direction),np.arange(2),
            tip_dof=0,physical_translation_dofs=np.array([0,1]),length=1.,
            column_scales=np.ones(2),row_scales=np.ones(2),constraint_start=2)


def test_algebraic_progress_is_rejected_even_when_border_is_invertible():
    # Algebraically [diag(1,0),-e2;e2.T,0] is invertible, but row2 is
    # retained/algebraic, not a declared physical translation.
    with pytest.raises(fold.AssessmentRefusal,match='free_physical_translation_progress'):
        fold.supported_branch_tangent(sparse.diags([1.,0.],format='csc'),np.array([1.,0.]),
            np.arange(2),tip_dof=1,physical_translation_dofs=np.array([0]),length=1.,
            column_scales=np.ones(2),row_scales=np.ones(2),constraint_start=2)


def test_flat_degenerate_turn_remains_candidate_and_not_simple_fold():
    # R=u^4-lambda has a sign-changing derivative and zero second derivative
    # at u=0. A sign bracket cannot distinguish this from a simple fold.
    rows = [scalar_tangent(4*u**3) for u in (-.125,0.,.125)]
    assessment = fold.supported_sign_assessment(rows)
    assert assessment['status'] == 'CANDIDATE'
    for claim in ('simple_fold_proved','first_fold_proved','stability_proved','capacity_proved',
                  'continuity_proved','slope_signs_certified'):
        assert assessment[claim] is False


def test_physical_length_unit_and_coordinate_scaling_covariance():
    metres = scalar_tangent(.25,length=2.,column=2.,row=.5)
    millimetres = scalar_tangent(.25/1000.,length=2000.,column=2000.,row=.5)
    assert metres['d_factor_d_tip_over_length'] == pytest.approx(
        millimetres['d_factor_d_tip_over_length'],rel=1e-14)
    assert millimetres['d_factor_d_tip'] == pytest.approx(metres['d_factor_d_tip']/1000.,rel=1e-14)
    np.testing.assert_allclose(millimetres['tangent'],1000*metres['tangent'],rtol=1e-14)


def test_original_equation_and_constraint_witnesses_cannot_be_hidden(monkeypatch):
    # Discriminating independent exact data: force residual .1 and constraint
    # residual .1 must reject, even if a mocked scaled solver claims success.
    monkeypatch.setattr(fold.corrector,'bordered_path_correction',
                        lambda *args:(np.array([1.,.1]),0.))
    with pytest.raises(fold.AssessmentRefusal) as caught:
        fold.supported_branch_tangent(sparse.eye(2,format='csc'),np.array([1.,0.]),np.arange(2),
            tip_dof=0,physical_translation_dofs=np.array([0]),length=1.,
            column_scales=np.ones(2),row_scales=np.ones(2),constraint_start=1)
    assert caught.value.code == 'original_equation_compatibility_or_control_residual'
    assert caught.value.details['original_compatibility_residual'] == [.1]


def test_bound_and_nonphysical_load_domains_refuse_without_solver(monkeypatch):
    def forbidden(*args): raise AssertionError('domain checks must precede sparse solve')
    monkeypatch.setattr(fold.corrector,'bordered_path_correction',forbidden)
    with pytest.raises(fold.AssessmentRefusal,match='nonzero_free_physical_dead_load'):
        fold.supported_branch_tangent(sparse.eye(2,format='csc'),np.array([0.,1.]),np.arange(2),
            tip_dof=0,physical_translation_dofs=np.array([0]),length=1.,
            column_scales=np.ones(2),row_scales=np.ones(2),constraint_start=1)
    with pytest.raises(fold.AssessmentRefusal,match='mixed_row_bound'):
        fold.supported_branch_tangent(sparse.eye(fold.MAX_MIXED_ROWS+1,format='csc'),
            np.ones(fold.MAX_MIXED_ROWS+1),np.arange(fold.MAX_MIXED_ROWS+1),tip_dof=0,
            physical_translation_dofs=np.array([0]),length=1.,
            column_scales=np.ones(fold.MAX_MIXED_ROWS+1),row_scales=np.ones(fold.MAX_MIXED_ROWS+1),
            constraint_start=fold.MAX_MIXED_ROWS+1)


def test_saved_identity_refuses_before_model_construction(tmp_path):
    (tmp_path/'accepted-g13.bin').write_bytes(b'wrong')
    (tmp_path/'accepted-g13.json').write_text('{}')
    with pytest.raises(ValueError,match='frozen binding'):
        fold.load_saved(tmp_path,13)


def test_directional_relative_reference_is_full_load_not_null_path_derivative():
    # The augmented path derivative can vanish exactly. Its norm is not an
    # admissible relative FD denominator; the declared unit-factor load is.
    witness = fold.directional_error_witness(np.array([.2,.3]),np.array([2.,4.]),
        np.array([0]),1,np.array([100.,0.]))
    assert witness['full_unit_factor_load_reference_norm'] == 200.
    assert witness['equilibrium_absolute_work_scaled_error'] == pytest.approx(.4)
    assert witness['equilibrium_relative_full_load_error'] == pytest.approx(.002)
    assert witness['compatibility_reference_ratio'] == pytest.approx(1.2)
    scaled = fold.directional_error_witness(np.array([2.,.3]),np.array([2.,4.]),
        np.array([0]),1,np.array([1000.,0.]))
    assert scaled['equilibrium_relative_full_load_error'] == pytest.approx(.002)
    with pytest.raises(fold.AssessmentRefusal,match='full_load_fd_reference'):
        fold.directional_error_witness(np.zeros(2),np.ones(2),np.array([0]),1,np.zeros(2))


def test_finite_inputs_with_overflowed_original_witness_refuse(monkeypatch):
    # Finite solver outputs do not ensure finite original equations: inf-inf
    # must never pass merely because NaN > tolerance is false.
    monkeypatch.setattr(fold.corrector,'bordered_path_correction',lambda *args:(np.array([2.]),2.))
    with np.errstate(over='ignore',invalid='ignore'):
        with pytest.raises(fold.AssessmentRefusal,match='original_equation_compatibility_or_control_residual'):
            fold.supported_branch_tangent(sparse.csc_matrix([[1e308]]),np.array([1e308]),np.array([0]),
                tip_dof=0,physical_translation_dofs=np.array([0]),length=2.,
                column_scales=np.ones(1),row_scales=np.ones(1),constraint_start=1)


@pytest.mark.parametrize('difference',((np.nan,0.),(0.,np.inf)))
def test_nonfinite_fd_or_plateau_cannot_be_supported(difference):
    with pytest.raises(fold.AssessmentRefusal,match='nonfinite_directional_or_plateau_witness'):
        fold.directional_error_witness(np.array(difference),np.ones(2),np.array([0]),1,np.array([1.,0.]))
