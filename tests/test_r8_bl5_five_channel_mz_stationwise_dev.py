"""Source-only refusal tests for support-order and signed shell-work parity."""
import importlib.util
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
        result = module.measure_preflight()
        self.assertEqual(result["status"], "stationwise_measure_preflight_passed")
        self.assertEqual(result["shell_dofs"], 510)
        self.assertLessEqual(result["max_40_basis_shell_covector_error"], 1e-13)

    def test_signed_support_channel_permutation(self):
        matrix = module.source_to_native_matrix(np)
        self.assertEqual(matrix[0, 0], -1)
        self.assertEqual(matrix[24, 4], -1)
        self.assertEqual(matrix[32, 3], 1)
        self.assertTrue(np.array_equal(matrix.T@matrix, np.eye(40)))

    def test_wrong_sign_or_support_swap_refuses(self):
        original = module.source_to_native_matrix
        def changed(np_module):
            matrix = original(np_module)
            matrix[0, 0] = 1.0
            return matrix
        with mock.patch.object(module, "source_to_native_matrix", side_effect=changed):
            with self.assertRaisesRegex(module.base.identity.IdentityError,
                                        "40-basis per-support shell covector work mismatch"):
                module.measure_preflight()

    def test_wrong_predecessor_hash_refuses(self):
        original = module.sha
        def changed(path):
            if path.name == "result.json" and path.parent.name == "saved-adjudication-v1":
                return "0"*64
            return original(path)
        with mock.patch.object(module, "sha", side_effect=changed):
            with self.assertRaisesRegex(module.base.identity.IdentityError,
                                        "prior saved comparator bytes/status changed"):
                module.measure_preflight()

    def test_invalid_support_index_and_zero_shape_refuse(self):
        with self.assertRaisesRegex(module.base.identity.IdentityError, "support index"):
            module.native_support_rows(8)
        with self.assertRaisesRegex(module.base.identity.IdentityError, "zero shell-side"):
            module.normalize_shape([0.0]*8, np)

    def test_existing_output_refuses_before_launch(self):
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
