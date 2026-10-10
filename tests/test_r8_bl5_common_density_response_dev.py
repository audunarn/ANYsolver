"""Source-bound refusals for the saved BL5 common-density response experiment."""
from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
mod = importlib.import_module("r8_bl5_common_density_response_dev")


class CommonDensitySourceTests(unittest.TestCase):
    def test_bound_saved_preflight(self):
        found = mod.preflight()
        self.assertEqual(found["status"], "source_only_preflight_passed")
        self.assertEqual(len(found["fixed_indices"]), 35)
        self.assertEqual(set(found["cases"]), {"fy", "mx", "mz"})

    def test_changed_geometry_refused(self):
        inputs = json.loads((mod.NATIVE / "inputs.json").read_text())
        layout = json.loads((mod.NATIVE / "layout.json").read_text())
        model = mod.identity.import_recipe().geometry(16, mod.identity.import_recipe().services()[3])
        changed = copy.deepcopy(inputs)
        changed["xyz_m"][0][0] = 0.01
        with self.assertRaises(mod.identity.IdentityError):
            mod.validate_native_geometry(changed, layout, model)

    def test_changed_density_channel_refused(self):
        source = [float(i+1) for i in range(40)]
        native = [0.0]*40
        with self.assertRaises(mod.identity.IdentityError):
            mod.validate_density_mapping(source, native)

    def test_changed_helper_bytes_refused(self):
        original = mod.sha

        def mutated(path):
            if path.name == "r8_bl5_support_only_gauge_dev.py":
                return "0"*64
            return original(path)

        with patch.object(mod, "sha", side_effect=mutated):
            with self.assertRaises(mod.identity.IdentityError):
                mod.helper_binding()

    def test_changed_archived_fixed_index_refused(self):
        original = mod.gauge.archived_integer_array

        def mutated(path, key):
            values = original(path, key)
            values[0] += 1
            return values

        with patch.object(mod.gauge, "archived_integer_array", side_effect=mutated):
            with self.assertRaises(mod.identity.IdentityError):
                mod.preflight()

    def test_changed_native_load_refused(self):
        original = mod.npz_vector

        def mutated(path, key):
            values = original(path, key)
            if path == mod.CROSSCASE / "arrays.npz" and key == "fy_native_load":
                values[100] += 1.0
            return values

        with patch.object(mod, "npz_vector", side_effect=mutated):
            with self.assertRaises(mod.identity.IdentityError):
                mod.preflight()

    def test_nonzero_retained_rhs_enters_signed_schur_load(self):
        # A negative retained block is intentional: no SPD shortcut is valid.
        effective, inverse_retained = mod.schur_effective_rhs(
            3.0, 1.0, lambda value: 2.0*value, lambda value: value/(-2.0))
        self.assertEqual(inverse_retained, -0.5)
        self.assertEqual(effective, 4.0)
        zero_effective, _ = mod.schur_effective_rhs(
            3.0, 0.0, lambda value: 2.0*value, lambda value: value/(-2.0))
        self.assertEqual(zero_effective, 3.0)

    def test_free_beam_yaw_is_not_a_fixed_reaction(self):
        spec = mod.identity.fixture_preflight()
        fixed = [spec["dof_order"].index(pair) for pair in spec["fixed_dofs"]]
        self.assertEqual(mod.validate_fixed_support_map(fixed, spec),
                         spec["dof_order"].index((100001, 6)))
        wrong = fixed[:-1]+[spec["dof_order"].index((100001, 6))]
        with self.assertRaises(mod.identity.IdentityError):
            mod.validate_fixed_support_map(wrong, spec)

    def test_whole_signal_response_mutation_refused(self):
        zero = [0.0]*708
        shell = zero.copy()
        shell[0] = 1e-6
        with self.assertRaises(mod.identity.IdentityError):
            mod.response_closure(zero, shell, zero, zero)

    def test_mapped_work_subtotal_mutation_refused(self):
        terms = {"shell_body": 9e-9, "beam_body": 0.0,
                 "constraint_action_mapping": -1e-9,
                 "direct_action_work_J": -1e-9,
                 "retained_source_work_J": 2e-9}
        self.assertLess(mod.work_closure(9e-9, terms)["absolute_error_J"], 1e-20)
        changed = dict(terms)
        changed["constraint_action_mapping"] += 9e-9
        with self.assertRaises(mod.identity.IdentityError):
            mod.work_closure(9e-9, changed)


if __name__ == "__main__":
    unittest.main()
