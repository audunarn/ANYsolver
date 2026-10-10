"""Focused source and refusal controls for the saved detached comparator."""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest import mock

import numpy as np
from scipy import sparse

SOURCE = Path(__file__).resolve().parents[1] / "scripts/r8_bl5_five_channel_mz_reference_dev.py"
spec = importlib.util.spec_from_file_location("r8_bl5_five_channel_mz_reference_dev", SOURCE)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class ComparatorSourceTests(unittest.TestCase):
    def test_saved_preflight_binds_detached_mechanics(self):
        result = module.preflight()
        self.assertEqual(result["status"], "source_preflight_passed")
        self.assertEqual(result["physical_layout"]["nodes"], 118)
        self.assertEqual(set(result["cases"]), {"fy", "mz"})

    def test_altered_archived_native_result_refuses(self):
        original = module.sha
        def changed(path):
            if path.name == "raw-state.npz" and path.parent.name == "mz":
                return "0"*64
            return original(path)
        with mock.patch.object(module, "sha", side_effect=changed):
            with self.assertRaisesRegex(module.identity.IdentityError, "native raw state unbound"):
                module.preflight()

    def test_wrong_section_or_arm_refuses(self):
        original = module.json.loads
        def changed(blob, *args, **kwargs):
            parsed = original(blob, *args, **kwargs)
            if isinstance(parsed, dict) and parsed.get("line", {}).get("law") == \
                    "BL5_PHYSICAL_DIRECTOR_WEAK_LINE_DEV_V1":
                parsed["line"]["expected_beam_arm"] = [0.0, 0.0, 0.0]
            return parsed
        with mock.patch.object(module.json, "loads", side_effect=changed):
            with self.assertRaisesRegex(module.identity.IdentityError, "line/arm changed"):
                module.preflight()

    def test_missing_or_changed_five_channel_row_refuses(self):
        dofs = [(1, d) for d in range(1, 7)]*118
        rows = [[1, 1, 1.0]]*40
        rows[0] = [1000000, 1, 1.0]
        with self.assertRaisesRegex(module.identity.IdentityError, "absent"):
            module.row_matrix(rows, dofs, np, sparse)

    def test_wrong_wrench_and_work_refuse(self):
        with self.assertRaisesRegex(module.identity.IdentityError, "wrench mismatch"):
            module.close_vector([1.0], [0.0], relative=0, floor=1e-10, name="wrench")
        with self.assertRaisesRegex(module.identity.IdentityError, "work mismatch"):
            module.close_vector([1e-4], [0.0], relative=1e-10, floor=1e-12, name="work")

    def test_rigid_fields_have_correct_lever_arm(self):
        nodes = {1: (1.0, 0.0, 0.0)}
        dofs = [(1, d) for d in range(1, 7)]
        fields = module.rigid_fields(nodes, dofs, np.zeros(3), np)
        self.assertEqual(fields[5][1], 1.0)  # unit yaw -> +uy at x=1
        self.assertEqual(fields[5][5], 1.0)  # same nodal yaw


if __name__ == "__main__":
    unittest.main()
