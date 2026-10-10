"""Independent exact synthetic B2 prediction controls; no operator payloads.

Stdlib only; prepared under source-only authority, not yet executed.
"""
from fractions import Fraction as F
import unittest
from scripts.r8_b2_original_operator_prediction_dev import (
    Interval as I, original_target_prediction, required_signed_change,
    rounded_dot_radius, kinematic_work_radius, work_tolerance_enclosure,
)


def dot(a, b):
    return sum((x*y for x, y in zip(a, b)), F(0))


def action(a, x):
    return [dot(row, x) for row in a]


def prediction(*, d=F(-1, 100000), linear=F(1, 100000), quadratic=F(0),
               external=I.point(1), kinematic=F(0), evaluation=F(0), rows=None):
    return original_target_prediction(base_defect=I.point(d), linear_raw_work=I.point(linear),
        quadratic_raw_work=I.point(quadratic), kinematic_error_radius=kinematic,
        final_evaluation_radius=evaluation, candidate_external_work=external,
        original_equilibrium_rows=rows)


class OriginalWorkPredictionControls(unittest.TestCase):
    def test_raw_nonsymmetric_work_increment_rejects_symmetric_shortcut(self):
        k, u, v = [[F(1), F(2)], [F(0), F(3)]], [F(2), F(1)], [F(1), F(-1)]
        kt = list(map(list, zip(*k)))
        actual = dot([a+b for a, b in zip(u, v)], action(k, [a+b for a, b in zip(u, v)]))-dot(u, action(k, u))
        linear = dot(v, [a+b for a, b in zip(action(k, u), action(kt, u))])
        quadratic = dot(v, action(k, v))
        self.assertEqual(actual, F(-2))
        self.assertEqual(linear+quadratic, actual)
        self.assertNotEqual(2*dot(v, action(k, u))+quadratic, actual)

    def test_affine_multiplier_identity_is_raw_and_role_correct(self):
        k = [[F(2), F(1)], [F(0), F(3)]]
        q, u0, f, lam = [F(2), F(1)], [F(1), F(-1)], [F(4), F(0)], F(3)
        u = [q[0]+u0[0], 2*q[1]+u0[1]]
        reaction = [a+lam-b for a, b in zip(action(k, u), f)]
        projected = [reaction[0], 2*reaction[1]]
        actual = dot(u, action(k, u))-dot(u, f)
        self.assertEqual(actual, F(12))
        self.assertEqual(dot(q, projected)-lam*sum(u)+dot(u0, reaction), actual)

    def test_stored_zero_residual_does_not_supply_original_work_prediction(self):
        stored = F(2)+F(1, 10**6)
        u = F(2)/stored
        self.assertEqual(stored*u-2, 0)
        original_residual = 2*u-2
        self.assertNotEqual(original_residual, 0)
        v = -original_residual/stored  # Scalar same-factor synthetic response.
        before = 2*u*u-2*u
        made = prediction(d=before, linear=v*(4*u-2), quadratic=2*v*v,
                          external=I.point(2*(u+v)))
        self.assertEqual(made["defect"], I.point(2*(u+v)**2-2*(u+v)))
        self.assertEqual(made["work"], "sufficient_enclosure")
        self.assertEqual(prediction(d=before, linear=0, external=I.point(2*u))["work"], "enclosed_failure")

    def test_signed_prediction_rejects_wrong_direction_and_retains_equilibrium_gap(self):
        self.assertEqual(prediction()["work"], "sufficient_enclosure")
        self.assertEqual(prediction(linear=F(-1, 100000))["work"], "enclosed_failure")
        self.assertEqual(prediction()["equilibrium"], "unresolved_missing_original_rows")
        self.assertFalse(prediction()["qualification"])

    def test_uncertainty_cannot_be_hidden_by_zero_central_defect(self):
        wide = prediction(evaluation=F(1, 100000))
        self.assertEqual(wide["work"], "unresolved_enclosure")
        self.assertIsNone(required_signed_change(I.centered(F(-1, 100000), F(1, 100000)), I.point(1)))

    def test_candidate_external_work_controls_unchanged_allowance(self):
        self.assertEqual(prediction(d=F(2, 10**12), linear=0, external=I.point(1))["work"], "sufficient_enclosure")
        self.assertEqual(prediction(d=F(2, 10**12), linear=0, external=I.point(0))["work"], "enclosed_failure")
        self.assertEqual(prediction(d=0, linear=0, external=I(F(-1), F(1)))["work"], "sufficient_enclosure")

    def test_missing_original_response_is_not_invented_from_stored_scalar(self):
        made = original_target_prediction(base_defect=I.point(-1), linear_raw_work=None,
            quadratic_raw_work=None, kinematic_error_radius=None, final_evaluation_radius=None,
            candidate_external_work=None)
        self.assertEqual(made["status"], "unresolved_missing_original_action_observables")
        self.assertIn("linear_raw_work", made["missing"])

    def test_original_rows_are_separate_and_can_refuse_work_only_success(self):
        made = prediction(rows=((I.point(0), I.point(1)), (I.point(3), I.point(2))))
        self.assertEqual(made["work"], "sufficient_enclosure")
        self.assertEqual(made["equilibrium"], "enclosed_failure")

    def test_reconstruction_restoration_remainder_uses_raw_cross_terms(self):
        # K=2,u=1,f=2, nominal v=1/2, actual v+e=3/5.
        work = lambda x: 2*x*x-2*x
        actual_difference = work(F(8, 5))-work(F(3, 2))
        radius = kinematic_work_radius(F(1, 5), F(1, 5), F(1, 50))
        self.assertEqual(actual_difference, F(21, 50))
        self.assertEqual(radius, abs(actual_difference))

    def test_rounding_bound_refuses_unestablished_assumptions_and_keeps_underflow(self):
        self.assertEqual(rounded_dot_radius(0, 0, finite_round_to_nearest=True), 0)
        self.assertGreater(rounded_dot_radius(1, 0, finite_round_to_nearest=True), 0)
        with self.assertRaises(ValueError):
            rounded_dot_radius(1, 1, finite_round_to_nearest=False)
        with self.assertRaises(ValueError):
            rounded_dot_radius(2**53, 1, finite_round_to_nearest=True)
        exact = F.from_float(1e-12)+F.from_float(1e-8)
        enclosure = work_tolerance_enclosure(I.point(1))
        self.assertLess(enclosure.lo, exact)
        self.assertGreater(enclosure.hi, exact)

    def test_affine_identity_does_not_create_a_new_affine_gate(self):
        with self.assertRaises(ValueError):
            original_target_prediction(base_defect=None, linear_raw_work=None, quadratic_raw_work=None,
                kinematic_error_radius=None, final_evaluation_radius=None, candidate_external_work=None,
                homogeneous_physical_family=False)
