"""Actual half-point certificate and explicit target/structure refusal controls."""
from copy import deepcopy
from fractions import Fraction as F
import unittest

from scripts import r8_f03_halfpoint_dev as half
from scripts.r8_f03_finite_local_dev import ExactBudget, Unresolved
from scripts.r8_f03_finite_sparse_dev import Caps

ASSESSMENT = None
MEASUREMENTS = {}


class HalfpointControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global ASSESSMENT
        ASSESSMENT = half.assess(); cls.r = ASSESSMENT

    def test_01_actual_halfpoint_pipeline_and_literal_claims(self):
        r = self.r
        self.assertEqual(r['status'], 'CERTIFIED_LITERAL_HALFPOINT_BOX')
        self.assertEqual(r['reference']['dim'], 66)
        self.assertEqual(r['stored']['adapter'], 'UNCHANGED_ACTUAL_REFERENCE_LOCAL_COMPILERS')
        self.assertEqual(r['stored']['source_native_local_shape'], (42, 42))
        self.assertEqual((r['stored']['native_physical_coordinates'],r['stored']['native_resultants']), (24,18))
        self.assertEqual((r['stored']['owner_factorizations'], r['stored']['owner_solves']), (0,0))
        self.assertEqual(r['symmetric_admissible_inertia'], (43,23,0))
        self.assertEqual(r['symmetric_admissible_C_rank'], 5)
        for key in ('raw_stored_coercivity','raw_stored_inertia','physical_acceptance','scientific_floor_comparison'):
            self.assertIsNone(r[key])
        self.assertFalse(r['qualification'])
        MEASUREMENTS.update(status=r['status'], contraction=r['certificate']['contraction_upper'],
            kappa=str(r['reference']['kappa']), literal_reserve=r['literal_numerical_reserve_N_per_m'])

    def test_02_all_four_exact_targets_independently_enclosed(self):
        r = self.r; ref = r['reference']; j = r['congruence']; count = 0
        self.assertEqual(set(r['targets']['entries']), half.REQUIRED_TARGETS)
        for entries in r['targets']['entries'].values():
            half.assert_enclosed(entries, r['box']); count += len(entries)
        target = r['targets']['entries']['raw_stored_exact_shift']
        for key in set(ref['G']) | set(r['stored']['entries']):
            i,k = key
            expected = (F(r['stored']['entries'].get(key,0.))-ref['kappa']*ref['G'].get(key,F())/2)*F(j[i])*F(j[k])
            self.assertEqual(target.get(key,F()), expected)
        self.assertGreater(count,100)
        MEASUREMENTS['target_sparse_entry_total'] = count

    def test_03_symmetric_family_nonempty_and_D_local_positive(self):
        r = self.r
        self.assertTrue(half.admit_symmetric_target(r['targets']['entries']['ideal_half'],r['box'],r['family']))
        self.assertTrue(r['family']['exact_p_lambda_and_lambda_lambda_zeros'])
        self.assertGreater(r['family']['D_min_lower_bound'],0)
        self.assertEqual(len(r['family']['D_row_lower_bounds']),18)
        self.assertEqual(r['reference']['proof']['literal_scaled_P0_row_rank'],5)
        self.assertTrue(r['reference']['proof']['native']['B_minor_identity'])
        MEASUREMENTS['D_min_coordinate_Gershgorin_lower_bound'] = str(r['family']['D_min_lower_bound'])

    def test_04_raw_stored_skew_is_not_symmetrized(self):
        r = self.r
        entries = r['targets']['entries']['raw_stored_exact_shift']
        skew = max(abs(v-entries.get((k,i),F())) for (i,k),v in entries.items())
        self.assertGreater(skew,0)
        self.assertTrue(r['target_nonsingularity']['raw_stored_exact_shift'])
        with self.assertRaises(Unresolved): half.admit_symmetric_target(entries,r['box'],r['family'])
        MEASUREMENTS['raw_target_scaled_skew'] = float(skew)

    def test_05_cancellation_sensitive_target_gets_its_own_radius(self):
        targets = {'dimension':66,'entries':{name:{(0,0):F(1)} for name in half.REQUIRED_TARGETS},
            'provenance':{name:'explicit exact synthetic target' for name in half.REQUIRED_TARGETS}}
        targets['entries']['raw_stored_exact_shift'][0,0] += F(1,2**100)
        targets['entries']['rounded_unshifted_exact_shift'][0,0] += F(1,2**99)
        box = half.target_box(targets,{(0,0):1.},ExactBudget(),Caps())
        self.assertEqual(F(box['radius_entries'][0,0]),F(1,2**99))
        for target in targets['entries'].values(): half.assert_enclosed(target,box)
        MEASUREMENTS['cancellation_sensitive_radius'] = str(F(box['radius_entries'][0,0]))

    def test_06_missing_target_or_provenance_refuses(self):
        for field in ('entries','provenance'):
            targets = deepcopy(self.r['targets']); targets[field].pop('raw_stored_exact_shift')
            with self.assertRaises(Unresolved): half.target_box(targets,self.r['box']['center_entries'],ExactBudget(),Caps())

    def test_07_zero_role_contamination_refuses_exactly(self):
        r = self.r; nx=r['reference']['nx']
        for key in ((nx,nx+18),(nx+18,nx),(nx+18,nx+19)):
            box=deepcopy(r['box']); box['center_entries'][key]=1e-30
            with self.assertRaises(Unresolved): half.signed_family_certificate(r['reference'],r['congruence'],box,ExactBudget())

    def test_08_negative_D_and_uncertain_D_refuse(self):
        r = self.r; nx=r['reference']['nx']; key=(nx,nx)
        for field,value in (('center_entries',abs(r['box']['center_entries'][key])),
                            ('radius_entries',2*abs(r['box']['center_entries'][key]))):
            box=deepcopy(r['box']); box[field][key]=value
            with self.assertRaises(Unresolved): half.signed_family_certificate(r['reference'],r['congruence'],box,ExactBudget())

    def test_09_missing_enclosure_and_float_provenance_refuse(self):
        r = self.r; entries=r['targets']['entries']['raw_stored_exact_shift']
        key=next(k for k,v in entries.items() if v!=F(r['box']['center_entries'].get(k,0.)))
        box=deepcopy(r['box']); box['radius_entries'].pop(key)
        with self.assertRaises(Unresolved): half.assert_enclosed(entries,box)
        with self.assertRaises(Unresolved): half.assert_enclosed({(0,0):1.},r['box'])

    def test_10_caps_roles_and_unmodified_scientific_norm(self):
        r = self.r
        self.assertEqual(r['family']['roles'],{'physical':43,'resultants':18,'multipliers':5})
        self.assertLess(r['exact_operations'],half.CAPS['exact_operations'])
        self.assertLess(r['certificate']['factor_fill'],half.CAPS['factor_fill'])
        self.assertLess(r['certificate']['operations_used'],half.CAPS['interval_operations'])
        self.assertEqual(r['reference']['kappa'],F(540225000000000000,63581390321668817))
        MEASUREMENTS.update(exact_operations=r['exact_operations'],interval_operations=r['certificate']['operations_used'],
            fill=r['certificate']['factor_fill'])

    def test_11_box_scalar_dimension_and_bit_caps_refuse(self):
        for field,value in (('center_entries',2**53+1),('radius_entries',F(1,2))):
            box=deepcopy(self.r['box']); box[field][0,0]=value
            with self.assertRaises(Unresolved): half.assert_enclosed({},box)
        box=deepcopy(self.r['box']); box['dimension']=10**9
        with self.assertRaises(Unresolved): half.assert_enclosed({},box)
        with self.assertRaises(Unresolved): half.validate_entries({(0,0):F(2**4096)},66)

    def test_12_xp_transpose_and_missing_D_assumption_refuse(self):
        r=self.r; entries=deepcopy(r['targets']['entries']['ideal_half'])
        key=next((i,k) for (i,k),v in entries.items() if i<43 and 43<=k<61 and v and r['box']['radius_entries'].get((i,k),0.)>0)
        # Stay inside the box; symmetry is an independent structural requirement.
        distance=F(r['box']['center_entries'].get(key,0.))-entries[key]
        delta=distance/2 if distance else F(r['box']['radius_entries'][key])/4
        self.assertNotEqual(delta,0)
        entries[key]+=delta
        half.assert_enclosed(entries,r['box'])
        with self.assertRaises(Unresolved): half.admit_symmetric_target(entries,r['box'],r['family'])
        family=deepcopy(r['family']); family['D_uniform_positive']=False
        with self.assertRaises(Unresolved): half.admit_symmetric_target(r['targets']['entries']['ideal_half'],r['box'],family)


if __name__ == '__main__': unittest.main()
