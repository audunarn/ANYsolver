"""Source-only identity controls for the proposed external K/KKT capture."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import json
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "scripts/r8_bl5_external_operator_dev.py"
MODULE_SPEC = importlib.util.spec_from_file_location("r8_bl5_external_operator_dev", SOURCE)
operator = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(operator)


TOY_RAW = SOURCE.parents[1] / ".development/r8-bl5-opensees-matrix-api-20261009-v1/raw.json"
FY_RAW = (SOURCE.parents[1] / "docs/agent_plans/development"
          / "r8-bl5-external-operator-20261009/fy-fullgeneral-v3/raw.json")
skip_without_toy_raw = unittest.skipUnless(
    TOY_RAW.exists(),
    "local OpenSees toy fullgeneral capture evidence "
    "(.development/r8-bl5-opensees-matrix-api-20261009-v1/raw.json) is absent")
skip_without_fy_raw = unittest.skipUnless(
    FY_RAW.exists(),
    "local fy fullgeneral capture evidence "
    "(docs/agent_plans/development/r8-bl5-external-operator-20261009/"
    "fy-fullgeneral-v3/raw.json) is absent")


def saved_three_case_helper_binding_host_parsable():
    """The saved helper_sources binding must be parsable on this host."""
    summary = json.loads((operator.FIXTURE / "fy" / "summary.json").read_text())
    bound = summary.get("helper_sources", {})
    return all(Path(key).name != key or ("\\" not in key and "/" not in key)
               for key in bound)


def small_bundle():
    spec = {"dof_order": [(1, 1), (2, 1)], "fixed_dofs": [(1, 1)],
            "rows": [[1, 1, 1.0, 2, 1, -1.0]], "physical_dimension": 2,
            "sp_dimension": 1, "mp_dimension": 1, "kkt_dimension": 4,
            "alpha_sp": 10.0, "alpha_mp": 20.0,
            "recipe_sha256": "source", "binary_sha256": "binary",
            "mechanics_sha256": "mechanics",
            "cases": {"fy": {"response_sha256": "saved", "displacement": [0.0, 0.0],
                              "load_factor": 1.0, "applied_load": [0.0, 10.0]}}}
    capture = {"recipe_sha256": "source", "binary_sha256": "binary",
               "mechanics_sha256": "mechanics", "dof_order": [[1, 1], [2, 1]],
               "constraint_order": [["SP", 1, 1], ["MP", 0]],
               "alpha_sp": 10.0, "alpha_mp": 20.0,
               "K": [[2.0, -1.0], [-1.0, 2.0]],
               "KKT": [[2.0, -1.0, 10.0, 20.0],
                       [-1.0, 2.0, 0.0, -20.0],
                       [10.0, 0.0, 0.0, 0.0],
                       [20.0, -20.0, 0.0, 0.0]],
               "responses": {"fy": {"saved_response_sha256": "saved",
                                    "kkt_solution": [0.0, 0.0, 1.0, -0.5],
                                    "rhs": [0.0, 10.0, 0.0, 0.0]}}}
    return spec, capture


def small_nonzero_bundle():
    spec, capture = small_bundle()
    spec["rows"] = []
    spec["mp_dimension"] = 0
    spec["kkt_dimension"] = 3
    spec["cases"]["fy"].update(displacement=[0.0, 1e-6], applied_load=[0.0, 2e-6])
    capture["constraint_order"] = [["SP", 1, 1]]
    capture["KKT"] = [[2.0, -1.0, 10.0], [-1.0, 2.0, 0.0], [10.0, 0.0, 0.0]]
    capture["responses"]["fy"].update(kkt_solution=[0.0, 1e-6, 1e-7],
                                       rhs=[0.0, 2e-6, 0.0])
    return spec, capture


def saved_toy_bundle():
    raw = json.loads((SOURCE.parents[1] / ".development/r8-bl5-opensees-matrix-api-20261009-v1/raw.json").read_text())
    spec = {"dof_order": [(1, 1), (2, 1), (3, 1)], "ndf": 1,
            "fixed_dofs": [(1, 1)], "rows": [[2, 1, 1.0, 3, 1, -1.0]],
            "physical_dimension": 3, "sp_dimension": 1, "mp_dimension": 1,
            "kkt_dimension": 5, "alpha_sp": 1e9, "alpha_mp": 1e9,
            "recipe_sha256": "toy-source", "binary_sha256": raw["binary_sha256"],
            "capture_commands_sha256": "toy-commands",
            "cases": {"fy": {"displacement": [0.0, 0.05, 0.05]}}}
    capture = {**raw, "recipe_sha256": "toy-source",
               "capture_commands_sha256": "toy-commands", "poses": raw["node_disp"],
               "case": "fy"}
    return spec, capture


class CaptureIdentityTests(unittest.TestCase):
    @skip_without_toy_raw
    def test_saved_toy_fullgeneral_permutation_and_analytic_k(self):
        spec, capture = saved_toy_bundle()
        raw = capture
        mapped = operator.validate_fullgeneral_capture(spec, capture)
        self.assertEqual([(row["equation_id"], row["kind"], row["source_row"])
                          for row in mapped["constraint_equations"]],
                         [(0, "MP", 0), (1, "SP", 0)])
        self.assertEqual(raw["node_dofs"], {"1": [4], "2": [3], "3": [2]})
        a = [raw["printA"][i*5:(i+1)*5] for i in range(5)]
        equation_order = [4, 3, 2]
        k = [[a[i][j] for j in equation_order] for i in equation_order]
        self.assertEqual(k, [[200.0, -100.0, -100.0],
                             [-100.0, 100.0, 0.0], [-100.0, 0.0, 100.0]])
        self.assertEqual([sum(x*y for x, y in zip(row, [0.0, 0.05, 0.05])) for row in k],
                         [-10.0, 5.0, 5.0])

    @skip_without_toy_raw
    def test_permuted_capture_refuses_wrong_map_and_rows(self):
        spec, good = saved_toy_bundle()
        bads = []
        wrong_map = deepcopy(good)
        wrong_map["node_dofs"]["2"] = [2]
        bads.append(wrong_map)
        missing_fixed = deepcopy(good)
        missing_fixed["node_dofs"].pop("1")
        bads.append(missing_fixed)
        wrong_scale = deepcopy(good)
        wrong_scale["printA"][1*5+4] = 1e8
        wrong_scale["printA"][4*5+1] = 1e8
        bads.append(wrong_scale)
        wrong_block = deepcopy(good)
        wrong_block["printA"][0] = 1e-6
        bads.append(wrong_block)
        wrong_response = deepcopy(good)
        wrong_response["poses"]["3"][0] += 1e-5
        bads.append(wrong_response)
        wrong_identity = deepcopy(good)
        wrong_identity["capture_commands_sha256"] = "different"
        bads.append(wrong_identity)
        for i, bad in enumerate(bads):
            with self.subTest(mutation=i), self.assertRaises(operator.IdentityError):
                operator.validate_fullgeneral_capture(spec, bad)

    @skip_without_toy_raw
    def test_mp_dependent_coefficient_normalization(self):
        spec, capture = saved_toy_bundle()
        spec["rows"] = [[2, 1, 0.5, 3, 1, -0.5]]
        mapped = operator.validate_fullgeneral_capture(spec, capture)
        self.assertEqual(mapped["constraint_equations"][0]["kind"], "MP")
        bad = deepcopy(spec)
        bad["rows"] = [[2, 1, 0.5, 3, 1, -0.4]]
        with self.assertRaises(operator.IdentityError):
            operator.validate_fullgeneral_capture(bad, capture)

    @skip_without_fy_raw
    def test_saved_fy_fullgeneral_capture_maps_all_constraints(self):
        spec = operator.fixture_preflight()
        raw = json.loads((SOURCE.parents[1] / "docs/agent_plans/development"
                          / "r8-bl5-external-operator-20261009/fy-fullgeneral-v3/raw.json").read_text())
        mapped = operator.validate_fullgeneral_capture(spec, raw)
        self.assertEqual(len(mapped["constraint_equations"]), 75)
        self.assertEqual(sum(x["kind"] == "SP" for x in mapped["constraint_equations"]), 35)
        self.assertEqual(sum(x["kind"] == "MP" for x in mapped["constraint_equations"]), 40)
        self.assertEqual(mapped["fixed_free_coupling_entries"], 230)
        self.assertEqual(mapped["max_pose_difference"], 0.0)

    def test_crosscase_force_assembly_refuses_k_pose_and_force_mutations(self):
        k = [[200.0, -100.0, -100.0], [-100.0, 100.0, 0.0],
             [-100.0, 0.0, 100.0]]
        pose = [0.0, 0.05, 0.05]
        element_force = [-10.0, 5.0, 5.0]
        dofs = [(1, 1), (2, 1), (3, 1)]
        operator.validate_physical_force_assembly(k, pose, element_force, dofs)
        bad_k = deepcopy(k)
        bad_k[0][1] = -99.0
        bad_pose = [0.0, 0.06, 0.05]
        bad_force = [-10.0, 6.0, 5.0]
        for a, b, c in ((bad_k, pose, element_force),
                        (k, bad_pose, element_force),
                        (k, pose, bad_force)):
            with self.assertRaises(operator.IdentityError):
                operator.validate_physical_force_assembly(a, b, c, dofs)

    def test_saved_three_case_preflight(self):
        if not (operator.FIXTURE / "fy" / "summary.json").exists():
            self.skipTest("saved three-case fixture evidence "
                "(docs/agent_plans/development/r8-bl5-matched-comparison-20261001/"
                "refinement-v1-raw/external/n16) is absent")
        if not saved_three_case_helper_binding_host_parsable():
            self.skipTest("saved three-case helper_sources record Windows "
                "path strings whose basenames this host cannot recover; the "
                "source-bound preflight refuses them here")
        spec = operator.fixture_preflight()
        self.assertEqual((spec["physical_dimension"], spec["sp_dimension"],
                          spec["mp_dimension"], spec["kkt_dimension"]),
                         (708, 35, 40, 783))
        self.assertEqual(set(spec["cases"]), {"fy", "mx", "mz"})

    def test_control_bundle_passes(self):
        spec, capture = small_bundle()
        self.assertEqual(operator.validate_capture(spec, capture)["status"],
                         "capture_algebra_validated_development_only")

    def test_identity_and_mechanics_mutations_rejected(self):
        spec, good = small_bundle()
        mutations = [
            ("dof_order", [[2, 1], [1, 1]]),
            ("constraint_order", [["MP", 0], ["SP", 1, 1]]),
            ("recipe_sha256", None),
            ("binary_sha256", None),
            ("mechanics_sha256", "altered"),
            ("alpha_mp", 1.0),
            ("KKT", good["KKT"][:-1]),
        ]
        for key, value in mutations:
            with self.subTest(key=key):
                bad = deepcopy(good)
                bad[key] = value
                with self.assertRaises(operator.IdentityError):
                    operator.validate_capture(spec, bad)

    def test_coupling_kkt_and_response_mutations_rejected(self):
        spec, good = small_bundle()
        bads = []
        no_coupling = deepcopy(good)
        no_coupling["K"][0][1] = no_coupling["K"][1][0] = 0.0
        no_coupling["KKT"][0][1] = no_coupling["KKT"][1][0] = 0.0
        bads.append(no_coupling)
        wrong_scale = deepcopy(good)
        wrong_scale["KKT"][0][3] = 19.0
        bads.append(wrong_scale)
        changed_mechanics = deepcopy(good)
        changed_mechanics["KKT"][0][0] = 3.0
        bads.append(changed_mechanics)
        response = deepcopy(good)
        response["responses"]["fy"]["kkt_solution"][0] = 0.01
        bads.append(response)
        bound = deepcopy(good)
        bound["responses"]["fy"]["saved_response_sha256"] = "other"
        bads.append(bound)
        residual = deepcopy(good)
        residual["responses"]["fy"]["rhs"][1] = 11.0
        bads.append(residual)
        for i, bad in enumerate(bads):
            with self.subTest(mutation=i), self.assertRaises(operator.IdentityError):
                operator.validate_capture(spec, bad)

    def test_small_nonzero_response_mutation_rejected_on_response_scale(self):
        spec, good = small_nonzero_bundle()
        operator.validate_capture(spec, good)
        bad = deepcopy(good)
        bad["responses"]["fy"]["kkt_solution"][1] += 1e-9
        with self.assertRaisesRegex(operator.IdentityError, "physical response mismatch"):
            operator.validate_capture(spec, bad)

    def test_self_reported_rhs_cannot_fabricate_load(self):
        spec, good = small_bundle()
        fabricated = deepcopy(good)
        fabricated["responses"]["fy"]["kkt_solution"][2] += 1.0
        fabricated["responses"]["fy"]["rhs"][0] += 10.0
        with self.assertRaisesRegex(operator.IdentityError, "RHS differs from frozen"):
            operator.validate_capture(spec, fabricated)
        constraint_load = deepcopy(good)
        constraint_load["responses"]["fy"]["rhs"][3] = 1e-6
        with self.assertRaisesRegex(operator.IdentityError, "RHS differs from frozen"):
            operator.validate_capture(spec, constraint_load)

    def test_multiplier_block_does_not_inherit_stiffness_scale(self):
        spec, good = small_bundle()
        bad = deepcopy(good)
        bad["K"][0][0] = 1e12
        bad["KKT"][0][0] = 1e12
        bad["K"][0][1] = bad["K"][1][0] = -1e5
        bad["KKT"][0][1] = bad["KKT"][1][0] = -1e5
        bad["KKT"][2][2] = 1e-6
        with self.assertRaisesRegex(operator.IdentityError, "constraint block must be zero"):
            operator.validate_capture(spec, bad)


if __name__ == "__main__":
    unittest.main()
