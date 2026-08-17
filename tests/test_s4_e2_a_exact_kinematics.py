from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "docs/reference_cases/s4_e2_a_cases.json"
ORACLE = ROOT / "docs/reference_cases/s4_e2_a_oracle.py"
CONTRACT = ROOT / "docs/reference_cases/s4_e2_a_contract.json"
OUTPUT = ROOT / "docs/reference_cases/s4_e2_a_output.json"
CASES_SHA256 = "61ED18EDB32B0DAF288E3EB66FEA522D5D4588542F11D8881B5B7762FCAC3729"
ORACLE_SHA256 = "A1796D466DF6DDCDB420987F8FAFC3787B563C16F0B8AEC58C716C0EF194D151"
CONTRACT_SHA256 = "E3AA3BC6AD8FAD7EB64564851FC558B0D1B2ACB533B292EEBA580EBA47B02D3E"
OUTPUT_SHA256 = "37C803C565602E1AF983AA8374C3DA090EFD1CC73F2B672F2C815CC6A56B623D"


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        assert key not in result
        result[key] = value
    return result


def _json(path: Path, sha256: str) -> dict[str, object]:
    raw = path.read_bytes()
    assert _sha(raw) == sha256
    assert not raw.startswith(b"\xef\xbb\xbf") and b"\r" not in raw and raw.endswith(b"\n")
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(AssertionError(token)),
    )
    canonical = (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode("utf-8")
    assert raw == canonical
    return value


def _run(*arguments: str) -> subprocess.CompletedProcess[bytes]:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, str(ORACLE), *arguments],
        cwd=ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30,
    )


def test_e2_a_exact_identity_nonuniqueness_certificate() -> None:
    cases = _json(CASES, CASES_SHA256)
    namespace = runpy.run_path(str(ORACLE))
    certificate = namespace["_certificate"](cases)
    ambiguity = certificate["nonuniqueness"]
    assert ambiguity["status"] == "TWO_NON_EQUIVALENT_AFFINE_COVARIANT_DISPLACEMENT_LIFTS"
    assert ambiguity["members"] == [
        "cubic_boundary_lift",
        "cubic_boundary_lift_plus_interior_mode",
    ]
    assert ambiguity["boundary_trace_difference_zero"] == {
        "r=-1": True,
        "r=1": True,
        "s=-1": True,
        "s=1": True,
    }
    assert cases["schema"] == "anysolver.s4.e2-a-cases-v2"
    family = cases["nonuniqueness_family"]
    assert family["mapping"] == "P_physical=chi*abs(det(A))*A_inverse_transpose*P_natural"
    assert family["common_factor"]["omega_definition"] == (
        "omega_D_center=a3_sign*(G_21-G_12)/2; G=U_xi*A_inverse"
    )

    geometries = certificate["affine_geometry_witnesses"]
    assert set(geometries) == {"square", "skew_rational"}
    boundary = {"r=-1": True, "r=1": True, "s=-1": True, "s=1": True}
    eta_states = {
        "combined_rigid_r": "0",
        "pure_common_drill_g": "1",
        "translation_spin_s": "-1",
    }
    for witness in geometries.values():
        assert witness["a3_sign"] == witness["chi"] == 1
        assert witness["affine_patch_lift_activation"] == ["0"] * 5
        assert witness["eta_states"] == eta_states
        assert witness["same_boundary_trace"] == boundary
        assert all(
            values == [["0", "0"]] * 4
            for values in witness["same_vertices"].values()
        )
        for energies in witness["member_state_strain_energies"].values():
            assert energies["combined_rigid_r"] == "0"
            assert energies["pure_common_drill_g"] == energies["translation_spin_s"]
            assert energies["pure_common_drill_g"] != "0"
        covariance = witness["covariance"]
        records = covariance["d4_reparameterizations"]
        assert len(records) == 8
        assert {record["determinant"] for record in records} == {-1, 1}
        assert all(record["chi"] == 1 for record in records)
        assert all(record["a3_sign"] == record["determinant"] for record in records)
        assert all(
            record["eta_pseudoscalar"] and record["physical_lift_invariant"]
            for record in records
        )
        assert covariance == {
            "d4_reparameterizations": records,
            "frame_rotation": True,
            "normal_reversal": True,
            "origin_shift": True,
            "unit_scale": "7/3",
        }

    square = geometries["square"]
    assert square["determinant"] == "1"
    assert square["cofactor_map"] == [["1", "0"], ["0", "1"]]
    assert square["cofactor_pairing"] == [["1", "0"], ["0", "1"]]
    assert square["difference_engineering_strain_at_r_1_2_s_1_3"] == [
        "8/27",
        "-1/4",
        "-5/18",
    ]
    assert square["difference_strain_energy"] == "128/35"
    assert square["member_state_strain_energies"] == {
        "cubic_boundary_lift": {
            "combined_rigid_r": "0",
            "pure_common_drill_g": "32/5",
            "translation_spin_s": "32/5",
        },
        "cubic_boundary_lift_plus_interior_mode": {
            "combined_rigid_r": "0",
            "pure_common_drill_g": "1952/105",
            "translation_spin_s": "1952/105",
        },
    }

    skew = geometries["skew_rational"]
    assert skew["determinant"] == "16"
    assert skew["cofactor_map"] == [["12", "-4"], ["-5", "3"]]
    assert skew["cofactor_pairing"] == [["16", "0"], ["0", "16"]]
    assert skew["difference_engineering_strain_at_r_1_2_s_1_3"] == [
        "13/4",
        "1007/1728",
        "-203/72",
    ]
    assert skew["difference_strain_energy"] == "305584/175"
    assert skew["member_state_strain_energies"] == {
        "cubic_boundary_lift": {
            "combined_rigid_r": "0",
            "pure_common_drill_g": "2266",
            "translation_spin_s": "2266",
        },
        "cubic_boundary_lift_plus_interior_mode": {
            "combined_rigid_r": "0",
            "pure_common_drill_g": "3692602/525",
            "translation_spin_s": "3692602/525",
        },
    }
    assert certificate["scope_invariants"] == {
        "center_curl": "EXACT_U_XI_TIMES_A_INVERSE",
        "physical_mapping": "CHI_J_A_A_G_INVERSE_EQ_CHI_ABS_DET_A_A_INVERSE_TRANSPOSE",
        "production_mechanics": "NOT_RUN_IDENTITY_AMBIGUOUS",
    }
    assert certificate["hostile_e1_a"] == {
        "common_image": ["0", "0", "0", "0"],
        "drill_rank": 3,
        "full_rank_upper_bound": 17,
        "immutable_terminal": "NO_GO_CANDIDATE_E1_A_RANK_DEFICIENCY",
    }


def test_e2_a_source_gate_stops_before_outcome_selected_mechanics() -> None:
    contract = _json(CONTRACT, CONTRACT_SHA256)
    output = _json(OUTPUT, OUTPUT_SHA256)
    expected_terminal = "BLOCKED_E2_A_SOURCE_OR_FORMULATION_IDENTITY"
    assert contract["scientific_terminal"] == {
        "reason": "RANK_SUFFICIENT_DISPLACEMENT_ENRICHMENT_NONUNIQUE",
        "value": expected_terminal,
    }
    assert output["candidate_terminal"] == expected_terminal
    assert output["contract_sha256"] == CONTRACT_SHA256
    assert contract["mechanics_execution"] == "FORBIDDEN_AFTER_SOURCE_IDENTITY_BLOCK"
    assert set(output["downstream_gates"].values()) == {"NOT_RUN_IDENTITY_AMBIGUOUS"}
    assert set(output["certificate"]) == {
        "affine_geometry_witnesses",
        "hostile_e1_a",
        "nonuniqueness",
        "scope_invariants",
    }
    assert output["e1_rh"] == "DEFERRED_NOT_RUN"
    assert output["overall_release_terminal"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    assert output["production"] == {
        "legacy_shell_default": True,
        "public_api_changed": False,
        "selector_available": False,
        "serialization_changed": False,
    }
    assert contract["production_paths"] == []


def test_e2_a_oracle_is_stdlib_only_and_repeats_canonical_bytes() -> None:
    tree = ast.parse(ORACLE.read_text(encoding="utf-8"), filename=str(ORACLE))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.module is not None
            imports.add(node.module.split(".")[0])
    assert imports <= {
        "__future__",
        "argparse",
        "fractions",
        "hashlib",
        "json",
        "pathlib",
        "sys",
    }
    assert _sha(ORACLE.read_bytes()) == ORACLE_SHA256
    emitted = _run("--emit-contract")
    assert emitted.returncode == 0 and emitted.stderr == b"" and emitted.stdout == CONTRACT.read_bytes()
    arguments = ("--run", "--contract", str(CONTRACT), "--contract-sha256", CONTRACT_SHA256)
    first, second = _run(*arguments), _run(*arguments)
    assert first.returncode == second.returncode == 0
    assert first.stderr == second.stderr == b""
    assert first.stdout == second.stdout == OUTPUT.read_bytes()


def test_e2_a_oracle_fails_closed_on_contract_or_baseline_drift(tmp_path: Path) -> None:
    before = OUTPUT.read_bytes()
    wrong_hash = _run("--run", "--contract", str(CONTRACT), "--contract-sha256", "0" * 64)
    assert wrong_hash.returncode == 2 and wrong_hash.stderr == b""
    assert json.loads(wrong_hash.stdout)["terminal"] == "BLOCKED_E2_A_ORACLE_OR_REVIEW"
    malformed = tmp_path / "contract.json"
    malformed.write_bytes(b'{"x":1,"x":2}\n')
    namespace = runpy.run_path(str(ORACLE))
    try:
        namespace["_decode"](malformed.read_bytes())
    except namespace["BaselineMismatch"]:
        pass
    else:
        raise AssertionError("duplicate-key JSON did not fail closed")
    function_globals = namespace["build_contract"].__globals__
    original = function_globals["_load_inputs"]

    def drift() -> dict[str, object]:
        raise namespace["BaselineMismatch"]("synthetic baseline drift")

    function_globals["_load_inputs"] = drift
    try:
        namespace["build_contract"]()
    except namespace["BaselineMismatch"]:
        pass
    else:
        raise AssertionError("baseline drift did not retain its terminal class")
    finally:
        function_globals["_load_inputs"] = original
    assert OUTPUT.read_bytes() == before
