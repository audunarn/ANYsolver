"""Source-only refusal controls for native case load provenance."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import r8_bl5_external_operator_crosscase_dev as crosscase


class NativeLoadBindingTests(unittest.TestCase):
    def test_three_archived_native_loads_bind(self):
        bindings = {case: crosscase.bound_native_load(case) for case in ("fy", "mx", "mz")}
        self.assertEqual(set(bindings), {"fy", "mx", "mz"})
        self.assertEqual(len({item["raw_state_sha256"] for item in bindings.values()}), 3)

    def test_wrong_case_status_hash_and_absent_hash_refuse(self):
        good = {"case": "mx", "status": "completed", "raw_state_sha256": "a" * 64}
        crosscase.check_native_load_binding("mx", good, "a" * 64)
        mutations = [
            ("mx", {**good, "case": "fy"}, "a" * 64),
            ("mx", {**good, "status": "failed"}, "a" * 64),
            ("mx", {**good, "raw_state_sha256": "b" * 64}, "a" * 64),
            ("mx", {**good, "raw_state_sha256": None}, "a" * 64),
            ("mx", good, "b" * 64),
        ]
        for case, record, actual in mutations:
            with self.subTest(record=record, actual=actual), self.assertRaises(
                crosscase.identity.IdentityError
            ):
                crosscase.check_native_load_binding(case, deepcopy(record), actual)


if __name__ == "__main__":
    unittest.main()
