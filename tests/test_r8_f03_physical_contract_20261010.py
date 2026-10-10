"""Exact scalar/local counterexamples only; no numerical library or matrices."""
from fractions import Fraction
import unittest

from scripts.r8_f03_physical_contract_dev import (
    body_yaw_is_not_coupled_gauge, constant_p1_intersection_obstruction,
    equal_average_not_equal_field, exact_controls, prospective_contract,
    omitted_endpoint_rotation_is_not_physical_null, scalar_stationary_identity, spin_quotient_counterexample,
    common_forty_density_dual_control, common_p0_yaw_balance, continuous_L1_vs_BL5_shear_control,
)


class NativePhysicalContractControls(unittest.TestCase):
    def test_local_resultant_stationarity_and_quadratic_identity(self):
        row = scalar_stationary_identity(a=1, b=2, d=3, x=2)
        self.assertEqual(row["p"], Fraction(4, 3))
        self.assertEqual(row["stationary_S"], Fraction(7, 3))
        self.assertEqual(row["mixed_work"], Fraction(28, 3))
        self.assertEqual(row["resultant_stationarity"], 0)

    def test_nonzero_resultant_source_cannot_be_discarded(self):
        row = scalar_stationary_identity(a=1, b=2, d=3, x=2, resultant_load=1)
        self.assertEqual(row["p"], 1)
        self.assertEqual(row["mixed_work"], 9)
        self.assertEqual(row["signed_resultant_source"], Fraction(-1, 3))
        self.assertNotEqual(row["mixed_work"], 4*row["stationary_S"])

    def test_full_mixed_negative_direction_is_not_mechanical_failure(self):
        row = exact_controls()
        self.assertLess(row["full_mixed_negative_direction"]["work"], 0)
        self.assertGreater(row["stationary_zero_source"]["stationary_S"], 0)

    def test_stationary_negative_direction_is_a_different_obligation(self):
        row = scalar_stationary_identity(a=-2, b=1, d=1, x=1)
        self.assertEqual(row["p"], 1)
        self.assertEqual(row["resultant_stationarity"], 0)
        self.assertEqual(row["mixed_work"], -1)
        self.assertEqual(row["stationary_S"], -1)

    def test_shell_spin_is_physical_director_null_but_total_completion_nonnull(self):
        row = spin_quotient_counterexample(completion_coefficient=2)
        self.assertEqual(row["physical_director_change"], (0, 0, 0))
        self.assertEqual(row["BL5_director_gap"], (0, 0))
        self.assertEqual(row["L1_relative_spin_gap"], 1)
        self.assertEqual(row["completion_work"], 2)
        self.assertFalse(row["total_work_quotient_descends"])

    def test_body_yaw_does_not_descend_to_the_coupled_constraint_kernel(self):
        row = body_yaw_is_not_coupled_gauge(left=0, right=Fraction(1, 8))
        self.assertEqual(row["P0_ty_gap_integral"], Fraction(-1, 128))
        self.assertTrue(row["body_null_does_not_imply_constraint_null"])
        shifted = body_yaw_is_not_coupled_gauge(left=Fraction(1, 8), right=Fraction(1, 4))
        self.assertEqual(shifted["P0_ty_gap_integral"], Fraction(-3, 128))
        intervals = tuple((Fraction(i, 8), Fraction(i+1, 8)) for i in range(8))
        balanced = common_p0_yaw_balance(intervals=intervals, ty_density=(200,)*8, applied_Mz=100)
        self.assertEqual(balanced["beam_yaw_compatibility_residual_Nm"], 0)
        self.assertTrue(balanced["prescribed_body_load_balanced"])
        unbalanced = common_p0_yaw_balance(intervals=intervals, ty_density=(0,)*8, applied_Mz=100)
        self.assertFalse(unbalanced["prescribed_body_load_balanced"])
        self.assertEqual(unbalanced["beam_yaw_compatibility_residual_Nm"], 100)

    def test_continuous_p1_cell_constant_intersection_respects_actual_root_support(self):
        row = constant_p1_intersection_obstruction(cell_tilts=(1, 1), nodal_tilts=(1, 1, 1))
        self.assertTrue(row["pointwise_equal"])
        self.assertFalse(row["support_admitted"])
        self.assertFalse(row["nonzero_supported_tilt_admitted"])
        free = constant_p1_intersection_obstruction(cell_tilts=(1, 1), nodal_tilts=(1, 1, 1), root_tilt_fixed=False)
        self.assertTrue(free["nonzero_supported_tilt_admitted"])
        zero = constant_p1_intersection_obstruction(cell_tilts=(0, 0), nodal_tilts=(0, 0, 0))
        self.assertTrue(zero["pointwise_equal"] and zero["support_admitted"])

    def test_nonconstant_supported_tilt_is_not_in_the_pointwise_intersection(self):
        row = constant_p1_intersection_obstruction(cell_tilts=(1, 2), nodal_tilts=(0, 1, 2))
        self.assertTrue(row["support_admitted"])
        self.assertFalse(row["pointwise_equal"])

    def test_equal_P0_average_does_not_establish_field_equality(self):
        row = equal_average_not_equal_field(left_rotation=0, right_rotation=2)
        self.assertEqual(row["P0_average_difference"], 0)
        self.assertEqual(row["left_pointwise_difference"], 1)
        self.assertEqual(row["right_pointwise_difference"], -1)
        self.assertFalse(row["same_physical_field"])

    def test_reject_nonexact_inputs_and_invalid_local_complement(self):
        for d in (0, -1):
            with self.assertRaises(ValueError):
                scalar_stationary_identity(a=1, b=1, d=d, x=1)
        with self.assertRaises(ValueError):
            scalar_stationary_identity(a=1., b=1, d=1, x=1)
        with self.assertRaises(ValueError):
            constant_p1_intersection_obstruction(cell_tilts=(1, 2), nodal_tilts=(0, 1))
        with self.assertRaises(ValueError):
            body_yaw_is_not_coupled_gauge(left=1, right=0)

    def test_contract_preserves_unadopted_norms_and_full_F03_obligations(self):
        row = prospective_contract()
        self.assertFalse(row["qualification"])
        self.assertIn("UNRESOLVED", row["stability"]["current_H_M_adoption"])
        self.assertIn("seven ratios", row["preserved_obligations"])
        self.assertIn("formal F03 unconsumed", row["preserved_obligations"])
        self.assertTrue(row["body_equations"]["static_condensation_is_not_mass"])
        control = common_forty_density_dual_control()
        self.assertEqual(control["coefficient_count"], 40)
        self.assertEqual(control["native_work"], control["external_work"])
        self.assertFalse(control["complete_body_field_equivalence"])
        self.assertEqual(len(exact_controls()), 12)

    def test_actual_pose_embedding_omission_is_not_a_mechanical_null(self):
        row = omitted_endpoint_rotation_is_not_physical_null()
        self.assertEqual(row["Cx_action"], 0)
        self.assertEqual(row["selected_pose_trace_norm"], 0)
        self.assertEqual(row["endpoint_relative_rotation"], 1)
        self.assertEqual(row["stationary_mechanical_work"], Fraction(1, 2))
        self.assertFalse(row["physical_null"])

    def test_conditional_continuous_full_L1_and_BL5_inplane_shear_semantics_differ(self):
        row = continuous_L1_vs_BL5_shear_control()
        self.assertEqual(row["full_L1_gamma_y"], 0)
        self.assertEqual(row["full_L1_gamma_z"], Fraction(1, 7))
        self.assertEqual(row["BL5_gamma_y"], Fraction(3, 5))
        self.assertEqual(row["BL5_director_gap"], (0, 0))
        self.assertFalse(row["BL5_field_admitted_by_full_L1"])


if __name__ == "__main__":
    unittest.main()
