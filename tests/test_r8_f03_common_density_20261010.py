"""Prospective development controls; not executed under source-only authority."""
from fractions import Fraction
import unittest

import numpy as np
from scripts import r8_f03_common_density_dev as contract


def layout():
    return {"counts": {"physical_dofs": 708, "full_q": 1092, "members": 16,
                       "retained_dofs": 384, "retained_cell_rotations": 96,
                       "retained_resultants": 288},
            "retained_members": [{"member_index": j, "retained_24_offset": 708+24*j,
                                   "cell_rotation_slots": list(range(708+24*j, 714+24*j)),
                                   "resultant_slots": list(range(714+24*j, 732+24*j))}
                                  for j in range(16)]}


def mixed():
    k = np.zeros((1092, 1092))
    x, blocks = contract.role_indices(layout())
    p = [i for block in blocks for i in block]
    k[x, x] = 3
    k[p, p] = -2
    # A beam nodal rotation and a cell rotation both couple to a resultant.
    k[515, 714] = k[714, 515] = 4
    k[708, 715] = k[715, 708] = 5
    return k, np.zeros((40, 1092))


class Controls(unittest.TestCase):
    def test_roundoff_asymmetry_certified_without_tangent_repair(self):
        local = np.eye(18)
        local[0, 1] = 1e-12
        before = local.copy()
        certificate = contract.local_complementary_certificate(local)
        self.assertFalse(certificate["represented_exact_symmetry"])
        self.assertGreater(certificate["quadratic_lower_bound"], 0)
        np.testing.assert_array_equal(local, before)
        k, c = mixed()
        k[714, 715] = -1e-12
        lifted = contract.ResultantStationarity(k, c, layout())
        self.assertEqual(lifted.local_d[0][0, 1], 1e-12)
        self.assertEqual(lifted.local_d[0][1, 0], 0)
        np.testing.assert_array_equal(lifted.k, k)

    def test_nonconservative_asymmetry_refused(self):
        local = np.eye(18)
        local[0, 1] = 1e-4
        with self.assertRaisesRegex(contract.ContractRefusal, "normalized1e-9"):
            contract.local_complementary_certificate(local)

    def test_small_defect_does_not_certify_negative_quadratic(self):
        local = np.eye(18)
        local[0, 0] = 1e-26
        local[0, 1] = 1e-12
        # v=(1,-5e-13,0,...) gives negative quadratic, despite small defect.
        v = np.zeros(18)
        v[0], v[1] = 1, -5e-13
        self.assertLess(v @ local @ v, 0)
        with self.assertRaisesRegex(contract.ContractRefusal, "positivity not certified"):
            contract.local_complementary_certificate(local)

    def test_balanced_perturbation_basis_has_constructive_range(self):
        basis = contract.balanced_perturbation_basis()
        self.assertEqual(len(basis), 39)
        free = [i for i in range(40) if i != 36]
        for j, column in enumerate(basis):
            self.assertEqual(contract.exact_yaw_balance(column, 0)["remainder_Nm"], 0)
            self.assertEqual([column[i] for i in free], [int(j == k) for k in range(39)])
        arbitrary = [Fraction(i-17, 7) for i in range(40)]
        arbitrary[36] = -sum((Fraction(2*j+1, 15)*arbitrary[5*j+1]
                              for j in range(7)), Fraction())
        recovered = [sum((arbitrary[free[j]]*basis[j][i] for j in range(39)), Fraction())
                     for i in range(40)]
        self.assertEqual(recovered, arbitrary)

    def test_column_major_unsymmetric_capture(self):
        raw = {"system_size": 783, "printA": [0.]*(783*783)}
        raw["printA"][783] = 7
        a = contract.decode_fullgeneral(raw)
        self.assertEqual(a[0, 1], 7)
        self.assertEqual(a[1, 0], 0)

    def test_actual_role_corruption_refused(self):
        bad = layout()
        bad["retained_members"][0]["resultant_slots"][0] = 708
        with self.assertRaises(contract.ContractRefusal):
            contract.role_indices(bad)

    def test_nodal_and_cell_rotations_remain_mechanical(self):
        k, c = mixed()
        lift = contract.ResultantStationarity(k, c, layout())
        self.assertIn(515, lift.x)
        self.assertIn(708, lift.x)
        self.assertNotIn(714, lift.x)
        x = np.zeros(804)
        x[lift.x.index(515)] = 2
        x[lift.x.index(708)] = 3
        q = lift.lift(x)
        self.assertEqual(q[714], 4)
        self.assertEqual(q[715], 7.5)
        np.testing.assert_array_equal(k[np.ix_(lift.p, range(1092))] @ q, np.zeros(288))
        np.testing.assert_array_equal(lift.action(x), (k @ q)[list(lift.x)])

    def test_resultant_source_and_cell_load_kept(self):
        k, c = mixed()
        lift = contract.ResultantStationarity(k, c, layout())
        rhs = np.zeros(1092)
        rhs[708] = 11
        rhs[714] = 6
        effective = lift.effective_rhs(rhs)
        self.assertEqual(effective[lift.x.index(708)], 11)
        self.assertEqual(effective[lift.x.index(515)], 12)
        q = lift.lift(np.zeros(804), rhs[list(lift.p)])
        self.assertEqual(q[714], -3)
        np.testing.assert_array_equal((k @ q)[list(lift.p)], rhs[list(lift.p)])

    def test_nonlocal_or_trace_active_resultants_refused(self):
        k, c = mixed()
        c[0, 714] = 1
        with self.assertRaises(contract.ContractRefusal):
            contract.ResultantStationarity(k, c, layout())
        c[0, 714] = 0
        k[714, 738] = k[738, 714] = 1
        with self.assertRaises(contract.ContractRefusal):
            contract.ResultantStationarity(k, c, layout())

    def test_invalid_complementary_block_refused(self):
        k, c = mixed()
        k[714, 714] = 1
        with self.assertRaises(contract.ContractRefusal):
            contract.ResultantStationarity(k, c, layout())

    def test_signed_dual_map_and_transpose_work(self):
        cn = np.zeros((40, 1092))
        ce = np.zeros((40, 708))
        cn[0, 708] = 2
        cn[32, 515] = 3
        ce[0, 0] = 4
        maps = contract.common_actions(cn, ce)
        density = np.zeros(40)
        density[0], density[3] = 5, 7
        rn, re = maps.loads(density)
        self.assertEqual(rn[708], 10)
        self.assertEqual(rn[515], -21)
        self.assertEqual(re[0], -20)
        qn = np.arange(1092, dtype=float)
        self.assertEqual(float(qn @ rn), float(-np.asarray(contract.native_density(density)) @ (cn @ qn)))

    def test_unbalanced_load_refused_without_gauge(self):
        source = [0]*40
        for j in range(8):
            source[5*j+1] = 200
        self.assertEqual(contract.exact_yaw_balance(source, 100)["remainder_Nm"], 0)
        with self.assertRaises(contract.ContractRefusal):
            contract.exact_yaw_balance(source, 0)
        with self.assertRaises(contract.ContractRefusal):
            contract.exact_yaw_balance([float(v) for v in source], 100)


if __name__ == "__main__":
    unittest.main()
