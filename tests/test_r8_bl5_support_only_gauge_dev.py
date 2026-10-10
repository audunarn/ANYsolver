"""Source-only refusal controls for the saved BL5 support-only gauge diagnostic."""
from __future__ import annotations

import copy
import importlib
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
gauge = importlib.import_module("r8_bl5_support_only_gauge_dev")


class SavedGaugeIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bound = gauge.preflight()

    def test_saved_source_preflight(self):
        self.assertEqual(self.bound["status"], "saved_input_preflight_passed")
        self.assertEqual(self.bound["native_dimension"], 1092)
        self.assertEqual(self.bound["external_dimension"], 708)
        self.assertEqual(self.bound["native_fixed"], 35)

    def test_reject_wrong_commit_or_layout(self):
        for key, bad in (("head", "deadbeef"), ("native_dimension", 1091),
                         ("external_fixed", 34), ("cases", ["fy", "mx"])):
            with self.subTest(key=key):
                modified = copy.deepcopy(self.bound)
                modified[key] = bad
                with self.assertRaises(gauge.identity.IdentityError):
                    gauge.validate_saved_context(modified)

    def test_reject_absent_identity(self):
        for key in ("native_operator_sha256", "external_raw_sha256",
                    "crosscase_arrays_sha256", "crosscase_result_sha256",
                    "native_layout_sha256"):
            with self.subTest(key=key):
                modified = copy.deepcopy(self.bound)
                modified[key] = None
                with self.assertRaises(gauge.identity.IdentityError):
                    gauge.validate_saved_context(modified)

    def test_reject_changed_bytes(self):
        with self.assertRaises(gauge.identity.IdentityError):
            gauge.require_exact_binding("0" * 64, self.bound["native_operator_sha256"], "operator")
        with self.assertRaises(gauge.identity.IdentityError):
            gauge.require_exact_binding("0" * 64, None, "operator")

    def test_reject_changed_fixed_index(self):
        modified = copy.deepcopy(self.bound)
        modified["native_fixed_indices"][0] += 1
        with self.assertRaises(gauge.identity.IdentityError):
            gauge.validate_saved_context(modified)

    def test_reject_mutated_imported_helper(self):
        original_sha = gauge.sha

        def changed_helper(path):
            if path.name == "r8_bl5_external_operator_crosscase_dev.py":
                return "0" * 64
            return original_sha(path)

        with patch.object(gauge, "sha", side_effect=changed_helper):
            with self.assertRaises(gauge.identity.IdentityError):
                gauge.helper_source_binding()


if __name__ == "__main__":
    unittest.main()
