"""Focused actual physical-pencil and counterexample controls; no F03 campaign."""
from dataclasses import replace
from fractions import Fraction as F
import unittest

from scripts import r8_f03_physical_interval_dev as physical
from scripts.r8_f03_finite_local_dev import Unresolved
from scripts.r8_f03_finite_sparse_dev import Caps, sparse_lu_homotopy

ASSESSMENT = None
MEASUREMENTS = {}


class PhysicalControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global ASSESSMENT
        ASSESSMENT = physical.assess()
        cls.result = ASSESSMENT

    def test_01_actual_signed_compiler_pipeline(self):
        r = self.result; ref = r['reference']; stored = r['stored']
        self.assertEqual(stored['adapter'], 'UNCHANGED_ACTUAL_REFERENCE_LOCAL_COMPILERS')
        self.assertEqual((ref['dim'], ref['nx'], ref['nx_full']), (66, 43, 60))
        self.assertEqual(stored['source_native_local_shape'], (42, 42))
        self.assertEqual((stored['native_physical_coordinates'], stored['native_resultants']), (24, 18))
        self.assertEqual((stored['owner_factorizations'], stored['owner_solves']), (0, 0))
        self.assertEqual(r['known_ideal_inertia'], (43, 23, 0))
        self.assertFalse(r['qualification']); self.assertFalse(r['stored_nonsymmetric_coercivity_claim'])
        self.assertIsNone(r['scientific_floor_comparison']); self.assertIsNone(r['physical_acceptance'])
        # Preserve a real sufficient-certificate discriminator. Unresolved
        # comparison is a recorded limitation, not a claim of instability.
        self.assertIn(r['status'], ('CERTIFIED_LITERAL_IDEAL_HALF_MARGIN', 'UNRESOLVED'))
        MEASUREMENTS.update(status=r['status'], contraction_upper=r['certificate']['contraction_upper'],
            kappa=r['literal_ideal_kappa_N_per_m'], stored_skew=r['source_stored_max_abs_skew'])

    def test_02_exact_source_roles_and_actual_negative_D(self):
        ref, stored = self.result['reference'], self.result['stored']['entries']
        lookup = {old: new for new, old in enumerate(ref['full_free'])}
        expected_b, observed_b = {}, {}
        for i, row in enumerate(ref['B']):
            pi = ref['nx']+i
            for j, value in enumerate(row):
                old = ref['shell_count']+j
                if old in lookup:
                    expected_b[i, j] = value
                    observed_b[i, j] = F(stored.get((pi, lookup[old]), 0.))
        error = max((abs(observed_b[key]-value) for key, value in expected_b.items()), default=F())
        self.assertLess(error, F(1, 10**12))
        MEASUREMENTS['actual_B_max_abs_source_difference'] = float(error)
        for i in range(18): self.assertLess(stored[ref['nx']+i, ref['nx']+i], 0.)
        difference_d = max(abs(F(stored.get((ref['nx']+i, ref['nx']+j), 0.))+ref['D'][i][j])
            for i in range(18) for j in range(18))
        scale_d = max(abs(v) for row in ref['D'] for v in row)
        self.assertLess(difference_d/scale_d, F(1, 10**12))
        MEASUREMENTS['actual_full_LOCAL18_D_relative_difference'] = float(difference_d/scale_d)
        self.assertEqual(ref['proof']['native']['B_minor_identity'], True)
        self.assertEqual(ref['proof']['native']['signed_block'], '-D')
        self.assertEqual(ref['inventory']['P0_row_rank_certificate']['scope'],
            'single whole-member constant-density support, all five channels')
        # Actual five scaled rows retain original force-equivalent map T.
        expected_c = {}
        for channel, row in enumerate(ref['inventory']['P0_five_channel_actions_z']):
            scale = ref['inputs'].ell if channel >= 3 else F(1)
            for old, value in enumerate(row):
                if old in lookup: expected_c[channel, lookup[old]] = value*scale
        error_c = max((abs(F(stored.get((ref['nx']+18+i, j), 0.))-v) for (i, j), v in expected_c.items()), default=F())
        self.assertLess(error_c, F(1, 10**12))
        MEASUREMENTS['actual_scaled_P0_max_abs_source_difference'] = float(error_c)

    def test_03_all_actual_endpoint_entries_enclose_independent_ideal(self):
        count = 0; largest = 0.
        for endpoint in (self.result['endpoint0'], self.result['endpoint_half']):
            for key, value in endpoint['exact'].items():
                center = F(endpoint['center_entries'].get(key, 0.))
                radius = F(endpoint['radius_entries'].get(key, 0.))
                self.assertLessEqual(center-radius, value)
                self.assertGreaterEqual(center+radius, value)
                count += 1; largest = max(largest, float(radius))
        self.assertGreater(count, 100)
        self.assertGreater(largest, 0.)
        MEASUREMENTS['exact_endpoint_enclosure_entries'] = count
        MEASUREMENTS['max_computational_endpoint_radius'] = largest

    def test_04_actual_skew_preserved_and_missing_radius_detected(self):
        r = self.result
        self.assertGreater(r['source_stored_max_abs_skew'], 0.)
        # A positive source discrepancy must not be silently declared exact.
        endpoint = r['endpoint0']
        key = next(k for k, value in endpoint['exact'].items() if value != F(endpoint['center_entries'].get(k, 0.)))
        self.assertNotEqual(endpoint['exact'][key], F(endpoint['center_entries'].get(key, 0.)))
        self.assertGreater(endpoint['radius_entries'][key], 0.)
        a = endpoint['center']; zero = a*0
        with self.assertRaises(Unresolved):
            sparse_lu_homotopy(a, a, zero, zero, r['_factor'], uncertainty_provenance={})

    def corrupted_certificate(self, mutations):
        r = self.result
        stored = dict(r['stored']); stored['entries'] = dict(stored['entries']); stored['entries'].update(mutations)
        caps = Caps(dimension=84, fill=10_000, operations=1_000_000, bits=4096)
        first = physical.endpoint_intervals(r['reference'], stored, r['congruence'], F(), caps)
        last = physical.endpoint_intervals(r['reference'], stored, r['congruence'], F(1, 2), caps)
        result = sparse_lu_homotopy(first['center'], last['center'], first['radius'], last['radius'], r['_factor'],
            uncertainty_provenance=r['certificate']['uncertainty_provenance'], caps=caps)
        return result

    def test_05_negative_complementary_sign_corruption_refuses(self):
        r = self.result; index = r['reference']['nx']
        value = r['stored']['entries'][index, index]
        result = self.corrupted_certificate({(index, index): -value})
        self.assertEqual(result['status'], 'UNRESOLVED')
        MEASUREMENTS['negative_D_sign_counterexample_contraction'] = result['contraction_upper']

    def test_06_constraint_role_and_skew_corruption_refuse(self):
        r = self.result; nx = r['reference']['nx']; constraint = nx+18
        # A role-offset defect must be enclosed as an actual large discrepancy,
        # not hidden behind successful LU or a floating rank observation.
        result = self.corrupted_certificate({(constraint, 0): 1e8, (0, constraint): -1e8})
        self.assertEqual(result['status'], 'UNRESOLVED')
        MEASUREMENTS['constraint_role_counterexample_contraction'] = result['contraction_upper']

    def test_07_nondefault_physics_geometry_refuses_before_source_compilation(self):
        for changes in ({'width': F(1, 10)}, {'nu': F(3, 4)}, {'ell': F(1, 3)},
                        {'e': F(200_000_000_000)}, {'arm_z': F()}, {'cells': 1}):
            with self.assertRaises(Unresolved): physical.exact_reference(replace(physical.Inputs(), **changes))

    def test_08_frozen_caps_and_source_bounds(self):
        r = self.result
        self.assertLess(r['reference']['exact_operations'], physical.CAPS['exact_operations'])
        self.assertLess(r['certificate']['factor_fill'], physical.CAPS['factor_fill'])
        self.assertLess(r['certificate']['operations_used'], physical.CAPS['interval_operations'])
        self.assertGreater(r['reference']['kappa'], 0)
        self.assertLessEqual(r['certificate']['max_product_row_entries'], 84)
        MEASUREMENTS['exact_operations'] = r['reference']['exact_operations']
        MEASUREMENTS['interval_operations'] = r['certificate']['operations_used']
        MEASUREMENTS['factor_fill'] = r['certificate']['factor_fill']

    def test_09_native_cross_axis_reconstruction_counterexample(self):
        from scripts.r8_f03_finite_local_dev import ExactBudget, native_chain_bounds, native_member_rows
        b = native_chain_bounds(F(1), F(2, 5), ExactBudget())
        z = [F()]*24
        z[11] = F(1); z[20] = F(3, 2); z[7] = F(23, 8)
        z[17] = F(2); z[23] = F(5, 2); z[13] = F(7)
        rows = native_member_rows(F(1), F(2, 5), ExactBudget())
        y = [sum((a*v for a, v in zip(row, z)), F()) for row in rows]
        work2 = sum((v*v for v in y), F())
        self.assertEqual(y[1], F(1)); self.assertEqual(y[5], F(1)); self.assertEqual(y[8], F(-1))
        self.assertEqual(z[7], F(23, 8)); self.assertEqual(b[7], F(23, 8))
        self.assertGreater(z[7]**2, work2)  # old b[7]=1 fails the claimed global L2 bound
        for value, bound in zip(z, b): self.assertLessEqual(value**2, bound**2*work2)
        MEASUREMENTS['native_reconstruction_counterexample'] = {'right_y': str(z[7]),
            'old_bound': '1', 'new_bound': str(b[7]), 'total_work_squared': str(work2)}

    def test_10_source_uncertainty_point_discriminator(self):
        point = self.result['midpoint_source_error_certificate']
        self.assertLess(point['contraction_upper'], 1.)
        self.assertEqual(point['status'], 'CERTIFIED_NONSINGULAR_DECLARED_INTERVAL')
        MEASUREMENTS['midpoint_source_uncertainty_contraction'] = point['contraction_upper']
        MEASUREMENTS['midpoint_diagnostic_scope'] = 'single point t=1/4, no uniform half-margin claim'


if __name__ == '__main__': unittest.main()
