"""Source-only refusal tests for support-order and signed shell-work parity."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

import numpy as np

SOURCE = Path(__file__).resolve().parents[1] / "scripts/r8_bl5_five_channel_mz_stationwise_dev.py"
spec = importlib.util.spec_from_file_location("r8_bl5_five_channel_mz_stationwise_dev", SOURCE)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class StationwiseSourceTests(unittest.TestCase):
    def test_exact_saved_40_basis_shell_measure(self):
        crosscase = module.base.crosscase
        if not (crosscase.CAPTURE / "receipt.json").exists():
            self.skipTest("saved external capture evidence absent")
        # Genuine drift refusal: the saved Fy raw capture matches its
        # receipt but the executed capture source bytes do not, so the
        # source-bound measure preflight must refuse instead of
        # accepting the saved capture.
        with self.assertRaisesRegex(module.base.identity.IdentityError,
                                    "unchanged source-bound Fy capture required"):
            module.measure_preflight()
        receipt = json.loads((crosscase.CAPTURE / "receipt.json").read_text())
        self.assertEqual(crosscase.sha(crosscase.CAPTURE / "raw.json"),
                         receipt["raw_sha256"])
        self.assertNotEqual(
            crosscase.sha(crosscase.CAPTURE / "executed-capture-source.py"),
            receipt["source_sha256"])

    def test_signed_support_channel_permutation(self):
        matrix = module.source_to_native_matrix(np)
        self.assertEqual(matrix[0, 0], -1)
        self.assertEqual(matrix[24, 4], -1)
        self.assertEqual(matrix[32, 3], 1)
        self.assertTrue(np.array_equal(matrix.T@matrix, np.eye(40)))

    def test_wrong_sign_or_support_swap_refuses(self):
        crosscase = module.base.crosscase
        if not (crosscase.CAPTURE / "receipt.json").exists():
            self.skipTest("saved external capture evidence absent")
        original = module.source_to_native_matrix
        cross_original = crosscase.sha
        receipt = json.loads((crosscase.CAPTURE / "receipt.json").read_text())
        def changed(np_module):
            matrix = original(np_module)
            matrix[0, 0] = 1.0
            return matrix
        # Synthetic source binding: bypass only the known capture-source
        # drift (asserted explicitly above) so this signed-permutation
        # mutation control reaches its own work check.
        def bound_source(path):
            if path.name == "executed-capture-source.py":
                return receipt["source_sha256"]
            return cross_original(path)
        with mock.patch.object(module, "source_to_native_matrix", side_effect=changed), \
             mock.patch.object(crosscase, "sha", side_effect=bound_source):
            with self.assertRaisesRegex(module.base.identity.IdentityError,
                                        "40-basis per-support shell covector work mismatch"):
                module.measure_preflight()

    def test_wrong_predecessor_hash_refuses(self):
        crosscase = module.base.crosscase
        if not (crosscase.CAPTURE / "receipt.json").exists():
            self.skipTest("saved external capture evidence absent")
        original = module.sha
        cross_original = crosscase.sha
        receipt = json.loads((crosscase.CAPTURE / "receipt.json").read_text())
        def changed(path):
            if path.name == "result.json" and path.parent.name == "saved-adjudication-v1":
                return "0"*64
            return original(path)
        # Synthetic source binding: bypass only the known capture-source
        # drift (asserted explicitly above) so this predecessor-hash
        # mutation control reaches its own binding check.
        def bound_source(path):
            if path.name == "executed-capture-source.py":
                return receipt["source_sha256"]
            return cross_original(path)
        with mock.patch.object(module, "sha", side_effect=changed), \
             mock.patch.object(crosscase, "sha", side_effect=bound_source):
            with self.assertRaisesRegex(module.base.identity.IdentityError,
                                        "prior saved comparator bytes/status changed"):
                module.measure_preflight()

    def test_invalid_support_index_and_zero_shape_refuse(self):
        with self.assertRaisesRegex(module.base.identity.IdentityError, "support index"):
            module.native_support_rows(8)
        with self.assertRaisesRegex(module.base.identity.IdentityError, "zero shell-side"):
            module.normalize_shape([0.0]*8, np)

    def test_existing_output_refuses_before_launch(self):
        if not module.V1.exists():
            self.skipTest("saved stationwise output evidence "
                "(docs/agent_plans/development/r8-bl5-five-channel-mz-20261010/"
                "saved-adjudication-v1) is absent; the existing-output "
                "refusal control requires the exact saved output bytes")
        with self.assertRaisesRegex(module.base.identity.IdentityError, "fresh stationwise output"):
            module.supervise(module.V1)

    def test_saved_preflight_is_semantic_and_refuses_change(self):
        current = {"source": "abc", "rows": [1, 2]}
        saved = __import__("json").loads(__import__("json").dumps(current, indent=2).replace("\n", "\r\n"))
        module.validate_saved_preflight(saved, current)
        saved["rows"][1] = 3
        with self.assertRaisesRegex(module.base.identity.IdentityError, "preflight changed"):
            module.validate_saved_preflight(saved, current)


if __name__ == "__main__":
    unittest.main()
