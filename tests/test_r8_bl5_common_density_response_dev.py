"""Source-bound refusals for the saved BL5 common-density response experiment."""
from __future__ import annotations

import ast
import copy
import importlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import zipfile
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
mod = importlib.import_module("r8_bl5_common_density_response_dev")


class CommonDensitySourceTests(unittest.TestCase):
    def committed_input_state_available(self):
        """The committed c64d189e state is reachable in this checkout."""
        if not (ROOT / ".git").exists():
            return False
        probe = subprocess.run(["git", "cat-file", "-e", "c64d189e^{commit}"],
                               cwd=ROOT, capture_output=True)
        return probe.returncode == 0

    def committed_head_helper_blob_available(self):
        """The committed HEAD helper blob is reachable in this checkout."""
        if not (ROOT / ".git").exists():
            return False
        probe = subprocess.run(
            ["git", "show", "HEAD:scripts/r8_bl5_external_operator_dev.py"],
            cwd=ROOT, capture_output=True)
        return probe.returncode == 0

    def test_bound_saved_preflight(self):
        # Historical refusal: the saved preflight binds the committed
        # c64d189e input state and current HEAD has moved past it, so
        # the source-bound preflight must refuse fail-closed. A git-free
        # source export refuses the same preflight without the objects.
        if self.committed_input_state_available():
            with self.assertRaises(mod.identity.IdentityError) as raised:
                mod.preflight()
            self.assertIn("committed c64d189e input state required",
                          str(raised.exception))
        else:
            with self.assertRaises((mod.identity.IdentityError,
                                    subprocess.CalledProcessError,
                                    FileNotFoundError)):
                mod.preflight()

    def test_binding_helper_synthetic_positive_and_mutation_controls(self):
        digest = "a"*64
        mod.require_binding(digest, digest, "synthetic binding")
        for wrong in ("b"*64, "a"*63, None, 123):
            with self.assertRaises(mod.identity.IdentityError):
                mod.require_binding(digest, wrong, "synthetic binding")

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
        if not self.committed_head_helper_blob_available():
            self.skipTest("actual immutable git history is absent from this "
                "source export; the changed-helper-bytes refusal compares "
                "current helper bytes with the committed HEAD blob")
        original = mod.sha

        def mutated(path):
            if path.name == "r8_bl5_support_only_gauge_dev.py":
                return "0"*64
            return original(path)

        with patch.object(mod, "sha", side_effect=mutated):
            with self.assertRaises(mod.identity.IdentityError):
                mod.helper_binding()

    @staticmethod
    def write_synthetic_npz(path, arrays):
        """Tiny valid NPY members, stdlib only; no saved evidence authority."""
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as bundle:
            for name, (dtype, values) in arrays.items():
                header = repr({"descr": dtype, "fortran_order": False,
                               "shape": (len(values),)})
                padding = (-(10 + len(header) + 1)) % 64
                encoded = (header + " "*padding + "\n").encode("ascii")
                code = "q" if dtype == "<i8" else "d"
                raw = (b"\x93NUMPY\x01\x00" + struct.pack("<H", len(encoded)) + encoded
                       + struct.pack(f"<{len(values)}{code}", *values))
                bundle.writestr(name + ".npy", raw)

    def synthetic_support_archive(self, root):
        archive = root / "synthetic-support.npz"
        layout = {"shell_node_ids": list(range(1, 7)), "beam_node_ids": [],
                  "fixed_coordinates": [("shell", 1+i//6, i % 6) for i in range(35)]}
        self.write_synthetic_npz(archive, {"fixed": ("<i8", list(range(35)))})
        return layout, archive

    def synthetic_load_archives(self, root):
        source = root / "synthetic-crosscase.npz"
        native = root / "synthetic-native.npz"
        load = [0.0]*708; load[100] = 1.0
        extended = load + [0.0]*384
        self.write_synthetic_npz(source, {"fy_frozen_load": ("<f8", load),
                                          "fy_native_load": ("<f8", extended)})
        self.write_synthetic_npz(native, {"load": ("<f8", extended)})
        return {"cases": {"fy": {"applied_load": load}}}, source, native

    def test_synthetic_archive_guard_positives(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            layout, archive = self.synthetic_support_archive(root)
            self.assertEqual(mod.validate_archived_fixed_indices(layout, archive), list(range(35)))
            spec, source, native = self.synthetic_load_archives(root)
            self.assertIsNone(mod.validate_saved_native_load("fy", spec, source, native))

    def test_changed_archived_fixed_index_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            layout, archive = self.synthetic_support_archive(Path(folder))
            self.assertEqual(mod.validate_archived_fixed_indices(layout, archive), list(range(35)))
            original = mod.gauge.archived_integer_array; touched = []
            def mutated(path, key):
                values = original(path, key)
                self.assertEqual((path, key), (archive, "fixed"))
                touched.append((path, key)); values[0] += 1
                return values
            with patch.object(mod.gauge, "archived_integer_array", side_effect=mutated):
                with self.assertRaisesRegex(mod.identity.IdentityError,
                                            "^native archived support indices changed$"):
                    mod.validate_archived_fixed_indices(layout, archive)
            self.assertEqual(touched, [(archive, "fixed")])

    def test_changed_native_load_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            spec, source, native = self.synthetic_load_archives(Path(folder))
            self.assertIsNone(mod.validate_saved_native_load("fy", spec, source, native))
            original = mod.npz_vector; touched = []; reads = []
            def mutated(path, key):
                values = original(path, key); reads.append((path, key))
                if (path, key) == (source, "fy_native_load"):
                    touched.append((path, key)); values[100] += 1.0
                return values
            with patch.object(mod, "npz_vector", side_effect=mutated):
                with self.assertRaisesRegex(mod.identity.IdentityError,
                                            "^fy physical load/retained load changed$"):
                    mod.validate_saved_native_load("fy", spec, source, native)
            self.assertEqual(touched, [(source, "fy_native_load")])
            self.assertEqual(reads, [(source, "fy_frozen_load"),
                                     (source, "fy_native_load"), (native, "load")])

    def test_preflight_calls_same_extracted_guards(self):
        """Source integration only; does not claim a historical full-preflight positive."""
        tree = ast.parse(Path(mod.__file__).read_bytes())
        preflight = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "preflight")
        calls = [n for n in ast.walk(preflight) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Name) and n.func.id in
                 ("validate_archived_fixed_indices", "validate_saved_native_load")]
        self.assertEqual(len(calls), 2)
        rendered = {n.func.id: [ast.unparse(a) for a in n.args] for n in calls}
        self.assertEqual(rendered["validate_archived_fixed_indices"],
                         ["layout", "NATIVE / 'operators.npz'"])
        self.assertEqual(rendered["validate_saved_native_load"],
                         ["case", "spec", "CROSSCASE / 'arrays.npz'", "NATIVE / case / 'raw-state.npz'"])
        self.assertLess(calls[0].lineno, calls[1].lineno)

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
        fixture_summary = mod.identity.FIXTURE / "fy" / "summary.json"
        if not fixture_summary.exists():
            self.skipTest("saved three-case fixture evidence "
                "(docs/agent_plans/development/r8-bl5-matched-comparison-20261001/"
                "refinement-v1-raw/external/n16) is absent")
        bound = json.loads(fixture_summary.read_text()).get("helper_sources", {})
        if any(Path(key).name == key and ("\\" in key or "/" in key)
               for key in bound):
            self.skipTest("saved three-case helper_sources record Windows "
                "path strings whose basenames this host cannot recover; the "
                "source-bound fixture preflight refuses them here")
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
