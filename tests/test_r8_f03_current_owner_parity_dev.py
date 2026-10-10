"""Source-only identity and refusal checks for frozen c2/P0 owner parity."""
from __future__ import annotations

import importlib
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
parity = importlib.import_module("r8_f03_current_owner_parity_dev")


class FrozenOwnerSourceTests(unittest.TestCase):
    def test_both_representative_preflights(self):
        for level in (32, 64):
            with self.subTest(level=level):
                found = parity.preflight(level)
                self.assertEqual(found["status"], "source_preflight_passed")
                self.assertEqual(found["expected_span"], 2)
                self.assertEqual(found["expected_rows"], 5*level//2)
                self.assertEqual(found["frozen_case"]["frozen_norm_rows"],
                                 1632 if level == 32 else 5824)

    def test_wrong_level_refused(self):
        with self.assertRaises(ValueError):
            parity.preflight(16)

    def test_changed_reference_function_refused(self):
        source = (ROOT / "scripts/b3_e4_bl5_reference_actions_dev.py").read_bytes()
        changed = source.replace(b"return np.r_[beam_u.reshape(-1)",
                                 b"return np.r_[beam_u.reshape(-1)*2", 1)
        self.assertNotEqual(parity.function_ast_hash(source, "physical_loads"),
                            parity.function_ast_hash(changed, "physical_loads"))

    def test_changed_frozen_result_bytes_refused(self):
        original = parity.sha

        def changed(path):
            if path.name == "family-result.json":
                return "0"*64
            return original(path)

        with patch.object(parity, "sha", side_effect=changed):
            with self.assertRaises(ValueError):
                parity.preflight(32)

    def test_signed_swap_basis_and_false_map_refusal(self):
        import numpy as np
        from scipy import sparse
        current = sparse.csc_matrix([[0., -1.], [1., 0.]])
        frozen = sparse.eye(2, format="csc")
        p = parity.signed_physical_basis_map(current, frozen, np, sparse)
        self.assertEqual(parity.max_sparse_abs(current@p-frozen), 0.0)
        current_h = sparse.diags([2., 3.], format="csc")
        expected_h = sparse.diags([3., 2.], format="csc")
        self.assertEqual(parity.max_sparse_abs(p.T@current_h@p-expected_h), 0.0)
        wrong = sparse.csc_matrix([[0., -2.], [1., 0.]])
        with self.assertRaises(ValueError):
            parity.signed_physical_basis_map(wrong, frozen, np, sparse)

    def test_existing_failed_output_preserved_and_versioned_target_fresh(self):
        existing = parity.OUT / "run-nx32-ny8-half32"
        self.assertTrue(existing.exists())
        with self.assertRaises(ValueError):
            parity.require_fresh_output(existing)
        self.assertEqual(parity.campaign_folder(32, "v2").name,
                         "run-v2-nx32-ny8-half32")
        with self.assertRaises(ValueError):
            parity.campaign_folder(32, "../v2")

    def test_wrong_predecessor_campaign_or_identity_refused(self):
        binding = parity.preflight(64)
        receipt = {"campaign": "v2", "status": "completed", "exit_code": 0,
                   "source_dependencies_sha256": binding["current_sources_sha256"],
                   "process_wall_seconds": 7.0}
        outcome = {"campaign": "v2",
                   "status": "current_owner_frozen_c2_work_parity_passed_development_only",
                   "level": 32, "nx": 32, "ny": 8, "halfcells": 32,
                   "bound_inputs": {"family_result_sha256": parity.FAMILY_SHA}}
        self.assertEqual(parity.validate_prior_32(receipt, outcome, binding, "v2"), 7.0)
        for changed_receipt, changed_outcome in (
            ({**receipt, "campaign": "v1"}, outcome),
            (receipt, {**outcome, "level": 64}),
            ({**receipt, "source_dependencies_sha256": {}}, outcome)):
            with self.assertRaises(ValueError):
                parity.validate_prior_32(changed_receipt, changed_outcome, binding, "v2")


if __name__ == "__main__":
    unittest.main()
