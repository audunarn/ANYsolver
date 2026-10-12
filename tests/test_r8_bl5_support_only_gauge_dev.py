"""Source-only refusal controls for the saved BL5 support-only gauge diagnostic."""
from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
gauge = importlib.import_module("r8_bl5_support_only_gauge_dev")


SYNTHETIC_CONTEXT = {
    "head": "75a185b2" + "0"*32,
    "native_dimension": 1092, "external_dimension": 708,
    "native_fixed": 35, "external_fixed": 35,
    "cases": ["fy", "mx", "mz"],
    "native_operator_sha256": "a"*64,
    "external_raw_sha256": "b"*64,
    "crosscase_arrays_sha256": "c"*64,
    "crosscase_result_sha256": "d"*64,
    "native_layout_sha256": "e"*64,
    "native_fixed_indices": list(range(35)),
    "native_layout_fixed_indices": list(range(35)),
    "helper_sources_sha256": {name: "f"*64 for name in gauge.HELPERS},
}


class SavedGaugeIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.capture_present = (gauge.CAPTURE / "receipt.json").exists()
        cls.bound = None
        cls.refusal = None
        if cls.capture_present:
            try:
                cls.bound = gauge.preflight()
            except gauge.identity.IdentityError as error:
                cls.refusal = str(error)

    def test_saved_source_preflight(self):
        if not self.capture_present:
            self.skipTest("saved external capture evidence absent")
        if self.refusal is not None:
            # Genuine drift refusal: the saved raw capture still matches its
            # receipt, but the executed capture source bytes do not, so the
            # source-bound preflight must refuse drift instead of accepting
            # the saved capture.
            self.assertIn("executed capture source SHA-256 missing or changed",
                          self.refusal)
            receipt = json.loads((gauge.CAPTURE / "receipt.json").read_text())
            self.assertEqual(gauge.sha(gauge.CAPTURE / "raw.json"),
                             receipt.get("raw_sha256"))
            self.assertNotEqual(
                gauge.sha(gauge.CAPTURE / "executed-capture-source.py"),
                receipt.get("source_sha256"))
        else:
            self.assertEqual(self.bound["status"], "saved_input_preflight_passed")
            self.assertEqual(self.bound["native_dimension"], 1092)
            self.assertEqual(self.bound["external_dimension"], 708)
            self.assertEqual(self.bound["native_fixed"], 35)

    def test_validate_saved_context_synthetic_positive_control(self):
        gauge.validate_saved_context(copy.deepcopy(SYNTHETIC_CONTEXT))

    def test_reject_wrong_commit_or_layout(self):
        for key, bad in (("head", "deadbeef"), ("native_dimension", 1091),
                         ("external_fixed", 34), ("cases", ["fy", "mx"])):
            with self.subTest(key=key):
                modified = copy.deepcopy(SYNTHETIC_CONTEXT)
                modified[key] = bad
                with self.assertRaises(gauge.identity.IdentityError):
                    gauge.validate_saved_context(modified)

    def test_reject_absent_identity(self):
        for key in ("native_operator_sha256", "external_raw_sha256",
                    "crosscase_arrays_sha256", "crosscase_result_sha256",
                    "native_layout_sha256"):
            with self.subTest(key=key):
                modified = copy.deepcopy(SYNTHETIC_CONTEXT)
                modified[key] = None
                with self.assertRaises(gauge.identity.IdentityError):
                    gauge.validate_saved_context(modified)

    def test_reject_changed_bytes(self):
        with self.assertRaises(gauge.identity.IdentityError):
            gauge.require_exact_binding("0" * 64,
                                        SYNTHETIC_CONTEXT["native_operator_sha256"],
                                        "operator")
        with self.assertRaises(gauge.identity.IdentityError):
            gauge.require_exact_binding("0" * 64, None, "operator")
        gauge.require_exact_binding(SYNTHETIC_CONTEXT["native_operator_sha256"],
                                    SYNTHETIC_CONTEXT["native_operator_sha256"],
                                    "operator")

    def test_reject_changed_fixed_index(self):
        modified = copy.deepcopy(SYNTHETIC_CONTEXT)
        modified["native_fixed_indices"][0] += 1
        with self.assertRaises(gauge.identity.IdentityError):
            gauge.validate_saved_context(modified)

    def test_reject_mutated_imported_helper(self):
        import subprocess
        root = SCRIPTS.parent
        probe = None
        if (root / ".git").exists():
            probe = subprocess.run(
                ["git", "show", "HEAD:scripts/r8_bl5_external_operator_dev.py"],
                cwd=root, capture_output=True)
        if probe is None or probe.returncode != 0:
            self.skipTest("actual immutable git history is absent from this "
                "source export; the mutated-imported-helper refusal compares "
                "current helper bytes with the committed HEAD blob")
        bound = gauge.helper_source_binding()
        self.assertEqual(set(bound), set(gauge.HELPERS))
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
