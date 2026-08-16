from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "docs/reference_cases/s4_stage_m_candidate_a_discretization_cases.json"
DERIVATION = ROOT / "docs/S4_STAGE_M_CANDIDATE_A_DISCRETIZATION_DERIVATION.md"
CERTIFICATE = ROOT / "docs/reference_cases/s4_candidate_a_open_a2_certificate.json"
REPORT = ROOT / "docs/S4_CANDIDATE_A_OPEN_A2_INF_SUP_CERTIFICATE.md"

CASES_CANONICAL_LF_SHA256 = "BB29F6AE7AE53E961C992BBC2EA764D50B73F935C9B5F9C21C1E21462DCC3E9C"
DERIVATION_CANONICAL_LF_SHA256 = "A8E012E69E3FCFCDAF94E73C97C413B4715CE51A6A1DA8FDA3A50C0467580BF8"
CERTIFICATE_SHA256 = "68691E4F1F23E23ED7DF00C4210436BDD1A730ADB58ED3E755E15CC01ECC5F3B"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _strict_json(path: Path, expected_sha256: str) -> dict[str, object]:
    data = path.read_bytes()
    assert _sha(data) == expected_sha256
    assert not data.startswith(b"\xef\xbb\xbf")
    assert b"\r" not in data
    assert data.endswith(b"\n")

    def no_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            assert key not in result
            result[key] = value
        return result

    value = json.loads(
        data.decode("utf-8"),
        object_pairs_hook=no_duplicates,
        parse_constant=lambda token: (_ for _ in ()).throw(AssertionError(token)),
    )
    canonical = (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    ).encode("utf-8")
    assert data == canonical
    return value


def _fractions(values: list[str]) -> list[Fraction]:
    return [Fraction(value) for value in values]


def _canonical_lf_bytes(path: Path) -> bytes:
    data = path.read_bytes()
    without_crlf = data.replace(b"\r\n", b"")
    assert b"\r" not in without_crlf
    if b"\r\n" in data:
        assert b"\n" not in without_crlf
    return data.replace(b"\r\n", b"\n")


def test_a2_certificate_binds_registered_exact_rows() -> None:
    cases_data = CASES.read_bytes()
    canonical_lf_cases = _canonical_lf_bytes(CASES)
    assert _sha(canonical_lf_cases) == CASES_CANONICAL_LF_SHA256
    assert _sha(_canonical_lf_bytes(DERIVATION)) == DERIVATION_CANONICAL_LF_SHA256
    cases = json.loads(cases_data)
    certificate = _strict_json(CERTIFICATE, CERTIFICATE_SHA256)
    assert certificate["authority"] == {
        "base_commit": "148ccb45ba79266d48dae1a84c4c500bdc1b4d85",
        "candidate_cases_sha256": CASES_CANONICAL_LF_SHA256,
    }

    a2 = cases["candidate_pairs"][1]
    assert a2["id"] == certificate["candidate_id"] == "candidate_a.d4.span_1_rs"
    assert [mode["polynomial"] for mode in a2["multiplier_basis"]] == ["1", "rs"]
    one_coefficient = a2["multiplier_basis"][0]["coefficient"]
    rs_coefficient = a2["multiplier_basis"][1]["coefficient"]
    assert Fraction(
        f"{one_coefficient['numerator']}/{one_coefficient['denominator']}"
    ) == Fraction(1, 2)
    assert Fraction(
        f"{rs_coefficient['numerator']}/{rs_coefficient['denominator']}"
    ) == Fraction(3, 2)

    raw = cases["constraint"]["moment_rows_raw"]
    expected_one = [Fraction(1, 2) * Fraction(value) for value in raw["1"]]
    expected_rs = [Fraction(3, 2) * Fraction(value) for value in raw["rs"]]
    local_rows = certificate["counterexample"]["local_rows"]
    assert _fractions(local_rows["normalized_1_full"]) == expected_one
    assert _fractions(local_rows["normalized_rs_full"]) == expected_rs
    assert _fractions(local_rows["normalized_rs_drill"]) == [
        expected_rs[5],
        expected_rs[11],
        expected_rs[17],
        expected_rs[23],
    ] == [Fraction(1, 3), Fraction(-1, 3), Fraction(1, 3), Fraction(-1, 3)]


def test_a2_exact_patch_assembly_has_nonzero_multiplier_annihilator() -> None:
    certificate = _strict_json(CERTIFICATE, CERTIFICATE_SHA256)
    counterexample = certificate["counterexample"]
    topology = counterexample["topology"]
    local_rows = {
        "1": _fractions(counterexample["local_rows"]["normalized_1_full"]),
        "rs": _fractions(counterexample["local_rows"]["normalized_rs_full"]),
    }
    dofs = topology["dofs_per_node"]
    assert dofs == ["u", "v", "w", "theta_x", "theta_y", "psi"]
    assert topology["orientation"] == "counter_clockwise_q4_local_nodes_0_1_2_3"

    elements = topology["elements"]
    assert [element["id"] for element in elements] == topology["element_order"]
    coordinates = {
        node: _fractions(value) for node, value in topology["node_coordinates"].items()
    }
    for element in elements:
        p0, p1, _p2, p3 = [coordinates[node] for node in element["nodes"]]
        edge_01 = [p1[axis] - p0[axis] for axis in range(2)]
        edge_03 = [p3[axis] - p0[axis] for axis in range(2)]
        signed_corner_area = edge_01[0] * edge_03[1] - edge_01[1] * edge_03[0]
        assert signed_corner_area == 4
        assert signed_corner_area / 4 == 1  # Exact affine surface Jacobian.
    centre = topology["interior_nodes"]
    assert centre == ["n11"]
    boundary = set(topology["boundary_nodes"])
    assert boundary.isdisjoint(centre)
    assert len(boundary) == 8

    assembled_rows: list[dict[str, object]] = []
    for element in elements:
        local_index = element["nodes"].index("n11")
        for mode in ("1", "rs"):
            row = local_rows[mode]
            values = row[6 * local_index : 6 * (local_index + 1)]
            assembled_rows.append(
                {"element_id": element["id"], "mode": mode, "values": values}
            )

    recorded_rows = counterexample["admissible_matrix"]["rows"]
    assert len(recorded_rows) == len(assembled_rows) == 8
    for actual, recorded in zip(assembled_rows, recorded_rows, strict=True):
        assert actual["element_id"] == recorded["element_id"]
        assert actual["mode"] == recorded["mode"]
        assert actual["values"] == _fractions(recorded["values"])

    coefficients: list[Fraction] = []
    for row in counterexample["multiplier"]["coefficients_by_element"]:
        coefficients.extend([Fraction(row["one"]), Fraction(row["rs"])])
    assert coefficients == [Fraction(0), Fraction(1)] * 4
    assert any(coefficients)

    transpose_product = [
        sum(
            coefficients[row_index] * assembled_rows[row_index]["values"][column]
            for row_index in range(len(assembled_rows))
        )
        for column in range(6)
    ]
    assert transpose_product == [Fraction(0)] * 6
    assert transpose_product == _fractions(
        counterexample["assembly"]["c_adm_transpose_mu"]
    )


def test_a2_boundary_removal_and_zero_inf_sup_are_exact() -> None:
    certificate = _strict_json(CERTIFICATE, CERTIFICATE_SHA256)
    counterexample = certificate["counterexample"]
    topology = counterexample["topology"]
    rs_drill = _fractions(counterexample["local_rows"]["normalized_rs_drill"])

    global_drill = {node: Fraction(0) for node in topology["node_coordinates"]}
    contributions_at_centre: list[Fraction] = []
    for element in topology["elements"]:
        for local_index, node in enumerate(element["nodes"]):
            global_drill[node] += rs_drill[local_index]
            if node == "n11":
                contributions_at_centre.append(rs_drill[local_index])

    recorded_global = {
        node: Fraction(value)
        for node, value in counterexample["assembly"][
            "global_drill_transpose_before_clamp"
        ].items()
    }
    assert global_drill == recorded_global
    assert contributions_at_centre == _fractions(
        counterexample["assembly"]["interior_cancellation"]["contributions"]
    ) == [Fraction(1, 3), Fraction(-1, 3), Fraction(-1, 3), Fraction(1, 3)]
    assert sum(contributions_at_centre) == Fraction(
        counterexample["assembly"]["interior_cancellation"]["sum"]
    ) == 0

    boundary = set(topology["boundary_nodes"])
    assert all(value == 0 for node, value in global_drill.items() if node not in boundary)
    assert counterexample["assembly"]["boundary_columns_removed"] == len(boundary) * len(
        topology["dofs_per_node"]
    ) == 48
    assert counterexample["assembly"]["retained_columns"] == 6

    integral_r_squared = Fraction(2, 3)
    normalized_rs_norm_squared = (
        Fraction(3, 2) ** 2 * integral_r_squared * integral_r_squared
    )
    assert normalized_rs_norm_squared == 1
    witness_norm_squared = normalized_rs_norm_squared * len(topology["elements"])
    assert witness_norm_squared == Fraction(
        counterexample["multiplier"]["l2_norm_squared"]
    ) == 4

    assert certificate["exclusions"] == {
        "multiplier_quotient": False,
        "production_activation": False,
        "production_source_edit": False,
        "regularization": False,
        "topology_dependent_row_removal": False,
    }
    assert certificate["terminal"] == {
        "beta": "0/1",
        "scope": "full_unquotiented_discontinuous_element_local_multiplier_space",
        "terminal": "PROVEN_FAIL_CANDIDATE_A2_INF_SUP",
    }
    assert Fraction(certificate["terminal"]["beta"]) == 0
    assert CERTIFICATE_SHA256 in REPORT.read_text(encoding="utf-8")
