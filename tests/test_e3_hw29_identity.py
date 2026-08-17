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
CASES = ROOT / "docs/reference_cases/e3_hw29_cases.json"
COVERAGE = ROOT / "docs/reference_cases/e3_hw29_source_coverage.json"
ORACLE = ROOT / "docs/reference_cases/e3_hw29_oracle.py"
CONTRACT = ROOT / "docs/reference_cases/e3_hw29_contract.json"
OUTPUT = ROOT / "docs/reference_cases/e3_hw29_output.json"
IDENTITY = ROOT / "docs/E3_HW29_SOURCE_IDENTITY.md"
IDENTITIES = {
    IDENTITY: (5586, "50A3A953E31758B301A28906AF677236C9959DB04DA0F99F2CF8C02A8B07550C"),
    COVERAGE: (5509, "5469057E9038ADDC904D4115B7C332B6E7D7488396A9C7C7DEB933D09D4D5AFE"),
    CASES: (1874, "1A6A3960DEC3E9E806B24E4CEF9531EC45DD8858A22F684013D8A7F81097F2DE"),
    ORACLE: (21342, "CFDB4B762E641C3958D7B67373AABD745A591AFF5EE79FA27E0BD9EC8B53369F"),
    CONTRACT: (2331, "E07C60EDE72DDD6D19D686F79978C3F0D1826DA91B1D2552534063BD28C394A0"),
    OUTPUT: (2441, "3D9E9C858CAD14CB3BDEBFC8866E971658F02E71B16573A320BAF0B08DFE9806"),
}


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        assert key not in result
        result[key] = value
    return result


def _json(path: Path) -> dict[str, object]:
    raw = _raw(path) if path in IDENTITIES else path.read_bytes()
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
    assert isinstance(value, dict)
    return value


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _raw(path: Path) -> bytes:
    raw = path.read_bytes()
    assert (len(raw), _sha(raw)) == IDENTITIES[path]
    assert not raw.startswith(b"\xef\xbb\xbf") and b"\r" not in raw and raw.endswith(b"\n")
    return raw


def _run() -> subprocess.CompletedProcess[bytes]:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, str(ORACLE), "--certificate"],
        cwd=ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30,
    )


def _run_bound(contract_sha: str) -> subprocess.CompletedProcess[bytes]:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [
            sys.executable, str(ORACLE), "--run", "--contract", str(CONTRACT),
            "--contract-sha256", contract_sha,
        ],
        cwd=ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30,
    )


def test_hw29_public_source_gate_is_total_and_fail_closed() -> None:
    cases = _json(CASES)
    coverage = _json(COVERAGE)
    assert cases["candidate_id"] == coverage["candidate_id"] == (
        "study_e3_p.hw29_linear_isotropic_identity_v1"
    )
    assert cases["source_gate"]["terminal"] == coverage["component_terminal"] == (
        "BLOCKED_E3_P_HW29_PUBLIC_SOURCE"
    )
    rows = {row["id"]: row["status"] for row in coverage["mandatory_rows"]}
    assert len(rows) == len(coverage["mandatory_rows"]) == 14
    assert rows["standard_q1_24_external_dofs"] == "CLOSED_PUBLIC_SOURCE"
    assert rows["membrane_7_9_2_counts"] == "CLOSED_PUBLIC_SOURCE"
    assert rows["gamma_PL_equals_G"] == "CLOSED_PUBLIC_SOURCE"
    assert rows["geometry_dependent_gamma_HG"] == "CLOSED_PUBLIC_SOURCE"
    assert rows["alpha_HG_1e_minus_3"] == "CLOSED_PUBLIC_SOURCE"
    assert rows["exact_local_condensation"] == "MISSING_PRINTED_EQUATIONS"
    missing = sorted(row_id for row_id, status in rows.items() if status.startswith("MISSING_"))
    assert cases["source_gate"]["missing_indispensable_rows"] == missing
    assert coverage["material_scope"] == {
        "claim": "compatible with DNV analysis workflows",
        "gamma_from_existing_inputs": "G=E/[2(1+nu)]",
        "new_public_inputs": [],
        "status": "NOT_RUN_REMAINING_SOURCE_BLOCK",
    }
    assert all(source["committed"] is False for source in coverage["sources"] if "committed" in source)
    sources = {source["id"]: source for source in coverage["sources"]}
    assert sources["wt2011_detailed_chapter"]["raw_sha256"] == (
        "E6AFAADE32B33D710D3C038635FE2AD2729E32FB952C5EC6706E68A93A3B1860"
    )
    assert sources["wt2011_detailed_chapter"]["pages"] == 22
    assert sources["adam_mohamed_hassaballa_2013"]["raw_sha256"] == (
        "B67AF5A43CB36FEC9E0D8CDAD745B391F9F5FC1861C842A249E2B982BDACD5E8"
    )
    assert sources["adam_mohamed_hassaballa_2013"]["role"] == (
        "BACKGROUND_ONLY_INCOMPATIBLE_ABSOLUTE_PENALTY_IDENTITY"
    )


def test_hw29_exact_constraint_and_e2_a_exclusion_certificate() -> None:
    namespace = runpy.run_path(str(ORACLE))
    certificate = namespace["build_certificate"]()
    assert certificate["component_terminal"] == "BLOCKED_E3_P_HW29_PUBLIC_SOURCE"
    constraint = certificate["constraint_certificate"]
    assert constraint == {
        "alternating_full_coefficients_1_r_s_rs": ["0", "0", "0", "1"],
        "alternating_retained_moments_1_r_s": ["0", "0", "0"],
        "coefficient_matrix_rank": 4,
        "highest_rs_translation_columns_zero": True,
        "retained_moment_matrix_rank": 3,
        "rs_drill_row": [
            "0", "0", "1/4", "0", "0", "-1/4",
            "0", "0", "1/4", "0", "0", "-1/4",
        ],
    }
    assert certificate["rigid_constraint"] == {
        "combined_physical_rigid": ["0", "0", "0", "0"],
        "pure_common_drill": ["1", "0", "0", "0"],
        "translation_only_spin": ["-1", "0", "0", "0"],
    }
    assert certificate["e2_a_exclusion"] == {
        "bubble_boundary_zero": True,
        "bubble_nonzero": True,
        "outside_q1": True,
    }


def test_hw29_count_and_schur_are_not_misrepresented_as_source_closure() -> None:
    namespace = runpy.run_path(str(ORACLE))
    certificate = namespace["build_certificate"]()
    assert certificate["field_count"] == {
        "arithmetic_sum": 29,
        "registered_total": 29,
        "source_closed": True,
    }
    assert certificate["generic_schur"] == {
        "D_determinant": "6",
        "condensed_A_minus_B_Dinv_BT": [["13/6", "1/3"], ["1/3", "8/3"]],
        "scope": "D_GENERIC_ALGEBRA_ONLY_NOT_HW29_IDENTITY",
    }
    gamma = certificate["gamma_stabilization"]
    assert gamma["alpha_HG"] == "1/1000"
    assert gamma["source_status"] == "PRINTED_EQUATIONS_26_43_TO_26_45"
    assert gamma["cases"]["square"] == {
        "b1": ["-1/4", "1/4", "1/4", "-1/4"],
        "b2": ["-1/4", "-1/4", "1/4", "1/4"],
        "constant_drill_theta": "0",
        "gamma": ["1/4", "-1/4", "1/4", "-1/4"],
        "hourglass_energy_over_GV": "1/1000",
        "hourglass_theta": "1",
        "rank_gamma_outer_gamma": 1,
        "zero_row_sum_ground_coupling": True,
    }
    assert gamma["cases"]["rational_trapezoid"]["gamma"] == [
        "3/14", "-3/14", "2/7", "-2/7",
    ]
    assert gamma["cases"]["rational_trapezoid"]["constant_drill_theta"] == "0"
    assert gamma["cases"]["rational_trapezoid"]["hourglass_theta"] == "1"
    assert set(certificate["unsupported_outcomes"].values()) == {
        "NOT_RUN_MISSING_PRINTED_BLOCKS",
        "NOT_RUN_MISSING_PRINTED_MAPS",
        "NOT_RUN_PUBLIC_SOURCE_BLOCK",
        "NOT_RUN_MISSING_SHELL_TRANSFORMATION",
    }
    identity = IDENTITY.read_text(encoding="utf-8")
    assert "not a mechanics failure" in identity
    assert "five indispensable" in identity


def test_hw29_oracle_is_stdlib_only_and_byte_deterministic() -> None:
    for path in IDENTITIES:
        _raw(path)
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
    first, second = _run(), _run()
    assert first.returncode == second.returncode == 0
    assert first.stderr == second.stderr == b""
    assert first.stdout == second.stdout
    output = json.loads(first.stdout)
    assert output["component_terminal"] == "BLOCKED_E3_P_HW29_PUBLIC_SOURCE"


def test_hw29_contract_output_and_caller_binding_are_exact() -> None:
    contract = _json(CONTRACT)
    output = _json(OUTPUT)
    assert contract["scientific_terminal"] == output["component_terminal"]
    assert output["contract_sha256"] == IDENTITIES[CONTRACT][1]
    emit = subprocess.run(
        [sys.executable, str(ORACLE), "--emit-contract"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=30,
    )
    assert emit.returncode == 0 and emit.stderr == b"" and emit.stdout == _raw(CONTRACT)
    first = _run_bound(IDENTITIES[CONTRACT][1])
    second = _run_bound(IDENTITIES[CONTRACT][1])
    assert first.returncode == second.returncode == 0
    assert first.stderr == second.stderr == b"" and first.stdout == second.stdout == _raw(OUTPUT)
    wrong = _run_bound("0" * 64)
    assert wrong.returncode == 2 and json.loads(wrong.stdout)["terminal"] == (
        "BLOCKED_E3_EVIDENCE_OR_REVIEW"
    )
