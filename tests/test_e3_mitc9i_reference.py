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
REPORT = ROOT / "docs/E3_MITC9I_REFERENCE.md"
SOURCE_MAP = ROOT / "docs/reference_cases/e3_mitc9i_source_map.json"
CASES = ROOT / "docs/reference_cases/e3_mitc9i_cases.json"
ORACLE = ROOT / "docs/reference_cases/e3_mitc9i_oracle.py"
CONTRACT = ROOT / "docs/reference_cases/e3_mitc9i_contract.json"
OUTPUT = ROOT / "docs/reference_cases/e3_mitc9i_output.json"
REPORT_IDENTITY = (6539, "F5115FB1EF1E41C6FA101E5C89918E15A1B8D493C5E377D21507BA1BBAF20CAA")
SOURCE_MAP_IDENTITY = (3655, "7E3679EE0BD25245C26EF4D4C259CA3F8B838FD9ED98F6D053A1B3E4B35C039E")
CASES_IDENTITY = (2153, "B25F0F7787DC8B56B08E4FAA0B1DE6E7AE6D34B80E9BE68E2B202BD4926D33E5")
ORACLE_IDENTITY = (24718, "1DB0E4C9A882E1250C596DA63118EBD835F57AC054104F8196BCE9F90F63ED6B")
CONTRACT_IDENTITY = (2116, "86824E91A460AEAC9F67B213048E471AF968C7AA9FE2C43E6B61B148A5C8FBED")
OUTPUT_IDENTITY = (2475, "00A6603A7B163CBC4A25B7FDF74647DDC1BDA300D478598F1403E4582AF5B575")
REFERENCE_ID = "reference_e3_q9.mitc9i_open_theory_extraction_v1"
STATUS = "GO_REFERENCE_E3_Q9_MITC9I_PARTIAL_PACKET"


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        assert key not in value
        value[key] = item
    return value


def _raw(path: Path, identity: tuple[int, str]) -> bytes:
    raw = path.read_bytes()
    assert (len(raw), _sha(raw)) == identity
    assert not raw.startswith(b"\xef\xbb\xbf") and b"\r" not in raw and raw.endswith(b"\n")
    return raw


def _json(path: Path, identity: tuple[int, str]) -> dict[str, object]:
    raw = _raw(path, identity)
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(AssertionError(token)),
    )
    assert raw == (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode("utf-8")
    return value


def _run() -> subprocess.CompletedProcess[bytes]:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [
            sys.executable, str(ORACLE), "--run", "--contract", str(CONTRACT),
            "--contract-sha256", CONTRACT_IDENTITY[1],
        ],
        cwd=ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30,
    )


def test_e3_mitc9i_source_identity_and_copyright_boundary() -> None:
    source_map = _json(SOURCE_MAP, SOURCE_MAP_IDENTITY)
    cases = _json(CASES, CASES_IDENTITY)
    report = _raw(REPORT, REPORT_IDENTITY).decode("utf-8")
    assert source_map["reference_id"] == cases["reference_id"] == REFERENCE_ID
    assert source_map["classification"] == {
        "B": "background_or_benchmark_context_not_used_to_define_oracle_equations",
        "D": "independently_derived_exact_or_outward_certified_consequence",
        "P": "printed_in_open_primary_source",
    }
    source = source_map["source"]
    assert source["doi"] == "10.1007/s00466-017-1510-4"
    assert source["bytes"] == 1302612
    assert source["pages"] == 25
    assert source["raw_sha256"] == "5C66A76D39682F71C13208E71AFFA585FD3CD1E284185360B825572DC8BA048B"
    assert source["license"] == "CC-BY-4.0"
    assert source_map["copyright_boundary"] == {
        "committed_pdf": False,
        "committed_quoted_passages": False,
        "committed_tables_or_figures": False,
        "permitted_record": "bibliographic_identity_equation_map_and_independent_derivation_only",
    }
    statement_classes = [statement["class"] for statement in source_map["statements"]]
    assert statement_classes.count("P") == 6
    assert statement_classes.count("D") == 4
    assert statement_classes.count("B") == 1
    assert STATUS in report
    assert "They are not an" in report and "exact covariance statement away" in report
    assert "This status has no bearing on HW29" in report


def test_e3_mitc9i_exact_reference_certificate() -> None:
    cases = _json(CASES, CASES_IDENTITY)
    namespace = runpy.run_path(str(ORACLE))
    certificate = namespace["_certificate"](cases)

    shapes = certificate["corrected_shapes"]
    assert shapes["partition_of_unity"] is True
    assert shapes["nodal_kronecker"] is True
    assert shapes["central_m1_residual"] == ["0", "0"]
    assert shapes["edge_restrictions"] == {
        "bottom": True,
        "left": True,
        "right": True,
        "top": True,
    }
    assert len(shapes["q2_reproduction"]) == 9
    assert all(shapes["q2_reproduction"].values())

    covc = certificate["covc"]
    assert covc == {
        "category": "CENTRE_JACOBIAN_APPROXIMATION_NOT_EXACT_COVARIANCE",
        "covc": [["4", "14"], ["14", "58"]],
        "fixed_center_recovery": [["1", "2"], ["2", "5"]],
        "off_center_differs": True,
        "true_off_center_covariant": [["25/4", "95/6"], ["95/6", "425/9"]],
    }

    shift = certificate["shift_parameters"]
    assert shift["straight_side"] == {"arc_fraction": "1/4", "exact_alpha": "-1/2"}
    assert shift["curved_side"] == {
        "continuous_nonsingular_bracket": True,
        "f_at_lower_outward": ["0.000155579732", "0.000272851628"],
        "f_at_upper_outward": ["-0.000204771039", "-0.000087433858"],
        "printed_value_inside": True,
        "root_bracket": ["-53/200", "-33/125"],
        "subdivisions": 8192,
    }

    drilling = certificate["drilling"]
    assert drilling["complete_monomial_count"] == 9
    assert drilling["linked_term_count"] == 8
    assert drilling["rotation_only_monomials"] == [[2, 2]]
    assert drilling["highest_mode_rigid_row_sum"] == "0"
    assert drilling["c9_square_integral_factor"] == "4/25"
    assert drilling["highest_mode_node_row"] == [
        "1/4", "1/4", "1/4", "1/4", "-1/2", "-1/2", "-1/2", "-1/2", "1"
    ]

    assert certificate["benchmarks"] == {
        "membrane_tensor_strain": ["1/1000", "1/1000", "1/2000"],
        "reported_single_element_zero_eigenvalues": {
            "classification": "SOURCE_ATTRIBUTED_NOT_REPRODUCED",
            "value": 6,
        },
        "transverse_right_displacement": "3/500",
    }
    assert certificate["hw29_independence"] == {"affects_hw29": False, "route_gate": "NONE"}
    assert len(certificate["finite_rotation"]["missing_explicit_details"]) == 5


def test_e3_mitc9i_oracle_is_stdlib_deterministic_and_fails_closed() -> None:
    _raw(ORACLE, ORACLE_IDENTITY)
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
        "math",
        "json",
        "pathlib",
        "sys",
    }
    first, second = _run(), _run()
    assert first.returncode == second.returncode == 0
    assert first.stderr == second.stderr == b""
    assert first.stdout == second.stdout
    output = json.loads(first.stdout)
    assert output["reference_id"] == REFERENCE_ID
    assert output["status"] == STATUS
    assert output["certificate"]["hw29_independence"] == {
        "affects_hw29": False,
        "route_gate": "NONE",
    }
    assert first.stdout == _raw(OUTPUT, OUTPUT_IDENTITY)
    contract = _json(CONTRACT, CONTRACT_IDENTITY)
    assert output["contract_sha256"] == CONTRACT_IDENTITY[1]
    assert contract["hw29_route_gate"] == "NONE"
    emitted = subprocess.run(
        [sys.executable, str(ORACLE), "--emit-contract"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=30,
    )
    assert emitted.returncode == 0 and emitted.stderr == b""
    assert emitted.stdout == _raw(CONTRACT, CONTRACT_IDENTITY)
    wrong = subprocess.run(
        [
            sys.executable, str(ORACLE), "--run", "--contract", str(CONTRACT),
            "--contract-sha256", "0" * 64,
        ],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=30,
    )
    assert wrong.returncode == 2 and json.loads(wrong.stdout)["status"] == (
        "BLOCKED_REFERENCE_E3_Q9_MITC9I_SOURCE_IDENTITY"
    )

    namespace = runpy.run_path(str(ORACLE))
    try:
        namespace["_decode"](b'{"x":1,"x":2}\n')
    except namespace["IdentityError"]:
        pass
    else:
        raise AssertionError("duplicate-key JSON did not fail closed")
    load_globals = namespace["_load_cases"].__globals__
    original_size = load_globals["CASES_BYTES"]
    load_globals["CASES_BYTES"] = original_size + 1
    try:
        namespace["_load_cases"]()
    except namespace["IdentityError"]:
        pass
    else:
        raise AssertionError("case identity drift did not fail closed")
    finally:
        load_globals["CASES_BYTES"] = original_size
