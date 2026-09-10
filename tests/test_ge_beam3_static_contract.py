"""Pure stdlib design-contract tests; no mechanics or Git execution on import."""

import ast
from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "static_contract_audit", ROOT / "scripts/audit_ge_beam3_static_contract.py")
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class StaticContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = AUDIT.text_bytes(AUDIT.MANIFEST)
        cls.frozen = AUDIT.strict_load(cls.raw)

    def test_canonical_round_trip(self):
        self.assertEqual(AUDIT.canonical(self.frozen), self.raw)

    def test_duplicate_keys_rejected(self):
        with self.assertRaises(ValueError):
            AUDIT.strict_load(b'{"schema":1,"schema":2}\n')

    def test_nonfinite_and_overflow_rejected(self):
        for value in (b"NaN", b"Infinity", b"-Infinity", b"1e9999"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                AUDIT.strict_load(b'{"value":' + value + b'}\n')

    def test_noncanonical_rejected(self):
        for raw in (self.raw.rstrip(), b" " + self.raw,
                    self.raw.replace(b"\n", b"\r\n")):
            with self.assertRaises(ValueError):
                AUDIT.strict_load(raw)

    def test_every_top_level_field_is_frozen(self):
        for key in self.frozen:
            with self.subTest(key=key):
                changed = deepcopy(self.frozen)
                del changed[key]
                with self.assertRaises(ValueError):
                    AUDIT.validate(AUDIT.canonical(changed), self.frozen)

    def test_policy_and_hash_mutations_rejected(self):
        mutations = [
            ("ownership", "acceptance", "ELEMENT_LOCAL_COMMIT"),
            ("internal_variables", "internal", 0),
            ("internal_variables", "static_mass_substitution", True),
            ("execution", "automatic_retry", True),
            ("execution", "child_seconds", 3600),
            ("acceptance", "normalized_invariant_error", "1e-2"),
        ]
        for group, key, value in mutations:
            changed = deepcopy(self.frozen)
            changed[group][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                AUDIT.validate(AUDIT.canonical(changed), self.frozen)
        for group in ("source_bindings", "text_bindings"):
            changed = deepcopy(self.frozen)
            changed[group][0]["sha256"] = "0" * 64
            with self.assertRaises(ValueError):
                AUDIT.validate(AUDIT.canonical(changed), self.frozen)

    def test_restart_constraints_and_precedence_mutations_rejected(self):
        for key in ("restart_required_groups", "constraint_kinds", "terminal_precedence"):
            changed = deepcopy(self.frozen)
            changed[key] = changed[key][::-1]
            with self.subTest(key=key), self.assertRaises(ValueError):
                AUDIT.validate(AUDIT.canonical(changed), self.frozen)

    def test_extra_keys_and_boolean_coercion_rejected(self):
        for key, value in (("unregistered", True), ("qualification_claim", 0)):
            changed = deepcopy(self.frozen)
            changed[key] = value
            with self.assertRaises(ValueError):
                AUDIT.validate(AUDIT.canonical(changed), self.frozen)

    def test_exact_case_coverage_and_document_rows(self):
        cases = [case for rows in self.frozen["gates"].values() for case in rows]
        self.assertEqual(cases, [f"S{i:02d}" for i in range(1, 27)])
        document = AUDIT.text_bytes(AUDIT.DOCUMENT).decode()
        for case in cases:
            self.assertEqual(document.count("| " + case + " |"), 1)

    def test_planning_does_not_claim_execution(self):
        for key in ("implementation_started", "qualification_claim", "default_changes", "mechanics_changes"):
            self.assertIs(self.frozen[key], False)
        self.assertEqual(self.frozen["case_status"], "PREREGISTERED_OBLIGATIONS_NOT_EXECUTED")

    def test_document_script_and_test_hashes(self):
        for row in self.frozen["text_bindings"]:
            self.assertEqual(AUDIT.digest(AUDIT.text_bytes(row["path"])),
                             {key: row[key] for key in ("bytes", "sha256")})

    def test_stdlib_only_auditor_and_no_dynamic_import(self):
        tree = ast.parse(AUDIT.text_bytes(AUDIT.AUDITOR))
        allowed = {"argparse", "hashlib", "json", "pathlib", "subprocess", "sys"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self.assertTrue(all(alias.name in allowed for alias in node.names))
            if isinstance(node, ast.ImportFrom):
                self.assertIn(node.module, allowed)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, {"eval", "exec", "__import__"})

    def test_planning_extent_only(self):
        self.assertEqual(set(self.frozen["allowed_extent"]), set(AUDIT.EXTENT))
        self.assertFalse(any(p.startswith(("src/", ".github/")) for p in AUDIT.EXTENT))


if __name__ == "__main__":
    unittest.main()
