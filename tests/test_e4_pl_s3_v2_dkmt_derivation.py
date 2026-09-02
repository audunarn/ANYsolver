from __future__ import annotations

import hashlib
import json
import math
from fractions import Fraction as F
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "docs" / "reference_cases"
CONTRACT = REFERENCE / "e4_pl_s3_v2_source_equation_contract.json"
LEDGER = REFERENCE / "e4_pl_s3_v2_dkmt_source_ledger.json"
EQUATION_MAP = REFERENCE / "e4_pl_s3_v2_dkmt_equation_map.md"
PAPER = ROOT / ".research-downloads" / "katili_2019_dkmt_review.pdf"


def _reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> object:
    raise ValueError(f"nonfinite JSON value: {value}")


def _load_canonical(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_reject_duplicates,
        parse_constant=_reject_nonfinite,
    )
    assert isinstance(value, dict)
    assert raw == (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _transpose(a: list[list[F]]) -> list[list[F]]:
    return [list(row) for row in zip(*a)]


def _matmul(a: list[list[F]], b: list[list[F]]) -> list[list[F]]:
    return [
        [sum((a[i][k] * b[k][j] for k in range(len(b))), F(0)) for j in range(len(b[0]))]
        for i in range(len(a))
    ]


def _scale(a: list[list[F]], scale: F) -> list[list[F]]:
    return [[scale * value for value in row] for row in a]


def _inverse(a: list[list[F]]) -> list[list[F]]:
    n = len(a)
    work = [row[:] + [F(int(i == j)) for j in range(n)] for i, row in enumerate(a)]
    for column in range(n):
        pivot = next(row for row in range(column, n) if work[row][column])
        work[column], work[pivot] = work[pivot], work[column]
        divisor = work[column][column]
        work[column] = [value / divisor for value in work[column]]
        for row in range(n):
            if row == column:
                continue
            factor = work[row][column]
            work[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(work[row], work[column])
            ]
    return [row[n:] for row in work]


def _dot(a: list[F], b: list[F]) -> F:
    return sum((left * right for left, right in zip(a, b)), F(0))


def _quadratic(matrix: list[list[F]], x: list[F]) -> F:
    return _dot(x, [sum((row[j] * x[j] for j in range(len(x))), F(0)) for row in matrix])


def test_public_bytes_equation_map_and_ledger_are_exactly_bound() -> None:
    contract = _load_canonical(CONTRACT)
    ledger = _load_canonical(LEDGER)
    assert ledger["schema"] == "anysolver.e4-pl-s3-v2-dkmt-source-ledger-v1"
    assert ledger["equation_map"] == {
        "bytes": 15885,
        "path": "docs/reference_cases/e4_pl_s3_v2_dkmt_equation_map.md",
        "sha256": "B527729C2F3AF482722ECB2D4635FB0FB165FB35F2EE952833D06740A68E0C4A",
    }
    assert EQUATION_MAP.stat().st_size == ledger["equation_map"]["bytes"]
    assert _sha256(EQUATION_MAP) == ledger["equation_map"]["sha256"]
    assert ledger["paper"]["bytes"] == 1_350_803
    assert ledger["paper"]["sha256"] == (
        "CAACAB9E0DF9B4F8B55887E84FAFA923899677F7D0F285EB2EEB46FBDFF8D17A"
    )
    if PAPER.exists():
        assert PAPER.stat().st_size == ledger["paper"]["bytes"]
        assert _sha256(PAPER) == ledger["paper"]["sha256"]

    groups = {(item["equations"], item["printed_page"]) for item in ledger["printed_equation_groups"]}
    assert groups == {
        ("12-16", 529),
        ("20-23", 529),
        ("24-31", 530),
        ("32-35", 530),
        ("36-41", 531),
        ("TEXT_FOLLOWING_41", 531),
    }
    sources = {item["id"]: item for item in contract["sources"]}
    assert sources["katili_2019_dkmt_review"]["classification"] == "P"
    assert sources["katili_2019_dkmt_review"]["equation_bytes_bound"] is True
    assert sources["s3_v2_dkmt_equation_map"]["sha256"] == _sha256(EQUATION_MAP)
    assert sources["s3_v2_dkmt_source_ledger"]["sha256"] == _sha256(LEDGER)


def test_flat_gate_is_closed_only_for_the_strict_supported_scope() -> None:
    contract = _load_canonical(CONTRACT)
    requirements = {item["id"]: item for item in contract["equation_requirements"]}
    flat = [item for item in requirements.values() if item["phase"] == "FLAT_LINEAR"]
    assert flat
    assert all(item["current_authority"] in {"P", "D"} for item in flat)
    assert requirements["dkmt_midside_rotation_enhancements"]["current_authority"] == "P"
    assert "AFFINE_BETA_SUBSTITUTE" in requirements["dkmt_midside_rotation_enhancements"]["excluded_scope"]
    assert requirements["physical_quadrature_and_generalized_section_work"]["status"] == (
        "FLAT_ISOTROPIC_ONLY_GENERALIZED_COUPLED_BLOCKED"
    )
    for requirement in (
        "curved_reference_director_and_pseudocurvature_mapping",
        "consistent_mass_and_zero_drill_inertia",
        "total_lagrangian_residual_and_consistent_tangent",
    ):
        assert requirements[requirement]["current_authority"] == "NONE"
    assert contract["gate"] == {
        "current_terminal": "BLOCKED_E4_PL_S3_V2_PUBLIC_SOURCE_OR_DERIVATION",
        "flat_linear_gate": "PASS_E4_PL_S3_V2A_STRICT_FLAT_ISOTROPIC_EQUATION_AUTHORITY",
        "flat_linear_production_allowed": True,
        "overall_qualification": False,
        "passes": False,
        "reason": "FLAT_LINEAR_STRICT_ISOTROPIC_SUBSET_IS_AUTHORIZED_BUT_CURVED_DYNAMIC_NONLINEAR_AND_GENERALIZED_SECTION_AUTHORITY_REMAINS_OPEN",
        "unclosed_phases": ["CURVED_LINEAR", "DYNAMIC", "NONLINEAR", "ARBITRARY_GENERALIZED_SECTION"],
    }


def test_edge_cycle_and_a_u_match_the_printed_side_kinematics_exactly() -> None:
    # This 3-4-5 triangle makes every edge direction an exact rational.
    nodes = [(F(0), F(0)), (F(3), F(0)), (F(0), F(4))]
    edges = ((0, 1), (1, 2), (2, 0))
    lengths = (F(3), F(5), F(4))
    directions: list[tuple[F, F]] = []
    for (i, j), length in zip(edges, lengths):
        directions.append(((nodes[j][0] - nodes[i][0]) / length, (nodes[j][1] - nodes[i][1]) / length))
    assert directions == [(F(1), F(0)), (F(-3, 5), F(4, 5)), (F(0), F(-1))]

    c12, c23, c31 = (item[0] for item in directions)
    s12, s23, s31 = (item[1] for item in directions)
    assert (
        c12 * s31 - c31 * s12,
        c23 * s12 - c12 * s23,
        c31 * s23 - c23 * s31,
    ) == (F(-1), F(-4, 5), F(-3, 5))

    u = [F(value) for value in (2, 3, 5, 7, 11, 13, 17, 19, 23)]
    direct: list[F] = []
    for (i, j), length, (c, s) in zip(edges, lengths, directions):
        direct.append(
            (u[3 * j] - u[3 * i]) / length
            + F(1, 2)
            * (c * u[3 * i + 1] + s * u[3 * i + 2] + c * u[3 * j + 1] + s * u[3 * j + 2])
        )

    a_u = [[F(0) for _ in range(9)] for _ in range(3)]
    for row, ((i, j), length, (c, s)) in enumerate(zip(edges, lengths, directions)):
        a_u[row][3 * i] = -F(1, 1) / length
        a_u[row][3 * j] = F(1, 1) / length
        for node in (i, j):
            a_u[row][3 * node + 1] = c / 2
            a_u[row][3 * node + 2] = s / 2
    assert [sum((coefficient * value for coefficient, value in zip(row, u)), F(0)) for row in a_u] == direct


def test_phi_rigidity_identity_and_positive_elimination_ratio_are_exact() -> None:
    e = F(210)
    nu = F(3, 10)
    h = F(2, 5)
    kappa = F(5, 6)
    length = F(7, 3)
    bending = e * h**3 / (12 * (1 - nu**2))
    shear = kappa * e * h / (2 * (1 + nu))
    printed_phi = 2 * h**2 / (kappa * (1 - nu) * length**2)
    assert printed_phi == 12 * bending / (shear * length**2)
    assert printed_phi > 0
    a_phi = -F(2, 3) * printed_phi
    a_delta = -F(2, 3) * (1 + printed_phi)
    assert a_phi / a_delta == printed_phi / (1 + printed_phi)
    assert F(0) < a_phi / a_delta < F(1)


def test_three_point_hammer_rule_integrates_all_degree_two_barycentric_monomials() -> None:
    points = ((F(2, 3), F(1, 6), F(1, 6)), (F(1, 6), F(2, 3), F(1, 6)), (F(1, 6), F(1, 6), F(2, 3)))
    weight = F(1, 6)  # A/3 on the reference triangle, where A=1/2.
    for a in range(3):
        for b in range(3 - a):
            for c in range(3 - a - b):
                exact = F(math.factorial(a) * math.factorial(b) * math.factorial(c), math.factorial(a + b + c + 2))
                rule = weight * sum((l1**a * l2**b * l3**c for l1, l2, l3 in points), F(0))
                assert rule == exact


def test_pl_schur_completion_and_isotropic_drill_scale_are_exact() -> None:
    area = F(3)
    mass = _scale([[F(2), F(1), F(1)], [F(1), F(2), F(1)], [F(1), F(1), F(2)]], area / 12)
    # The last three columns represent the three independent drill coordinates;
    # the first column is a shared constant continuum spin contribution.
    c = [[F(-1), F(1), F(0), F(0)], [F(-1), F(0), F(1), F(0)], [F(-1), F(0), F(0), F(1)]]
    k_d = F(7, 5)
    k_q_tau = _matmul(_transpose(c), mass)
    k_tau_q = _matmul(mass, c)
    k_tau_tau = _scale(mass, -F(1) / k_d)
    schur = _scale(_matmul(_matmul(k_q_tau, _inverse(k_tau_tau)), k_tau_q), F(-1))
    assert schur == _scale(_matmul(_matmul(_transpose(c), mass), c), k_d)

    e = F(200)
    h = F(1, 4)
    nu = F(1, 4)
    a = e * h / (1 - nu**2)
    b = nu * a
    g = e * h / (2 * (1 + nu))
    # P^T A P is diag(2(a-b), g); relative to G=diag(2,1/2)
    # both generalized eigenvalues equal 2g.
    generalized_eigenvalues = (2 * (a - b) / 2, g / F(1, 2))
    assert generalized_eigenvalues == (2 * g, 2 * g)
    assert min(generalized_eigenvalues) / 2 == g


def test_beta_embedding_and_variational_resultant_work_are_sign_consistent() -> None:
    theta = [F(2), F(-3), F(5)]
    director = [F(0), F(0), F(1)]
    theta_cross_director = [
        theta[1] * director[2] - theta[2] * director[1],
        theta[2] * director[0] - theta[0] * director[2],
        theta[0] * director[1] - theta[1] * director[0],
    ]
    assert theta_cross_director[:2] == [theta[1], -theta[0]]

    stiffness = [[F(5), F(1)], [F(1), F(4)]]
    strain = [F(2, 3), F(-1, 5)]
    variation = [F(7, 11), F(3, 8)]
    resultants = [sum((row[j] * strain[j] for j in range(2)), F(0)) for row in stiffness]
    work = _dot(resultants, variation)
    plus = [value + delta for value, delta in zip(strain, variation)]
    minus = [value - delta for value, delta in zip(strain, variation)]
    energy_derivative = (_quadratic(stiffness, plus) / 2 - _quadratic(stiffness, minus) / 2) / 2
    assert work == energy_derivative

    # A uniform dead pressure is exactly work-conjugate to the linear w field.
    area = F(9, 2)
    pressure = F(7, 3)
    nodal_w_variation = [F(2), F(-1), F(4)]
    nodal_force = pressure * area / 3
    discrete_work = nodal_force * sum(nodal_w_variation, F(0))
    integrated_work = pressure * area * sum(nodal_w_variation, F(0)) / 3
    assert discrete_work == integrated_work


def test_equation_map_keeps_rank_proof_and_unclosed_scope_explicit() -> None:
    text = EQUATION_MAP.read_text(encoding="utf-8")
    for required in (
        "A_\\phi=-\\frac23\\operatorname{diag}",
        "A_\\Delta=-\\frac23\\operatorname{diag}",
        "\\beta_x=\\theta_y,\\qquad \\beta_y=-\\theta_x",
        "General flat-flexure rank proof",
        "`beta=c+a(-y,x)`",
        "signed triangle area times `a`",
        "full 21-variable PL saddle matrix has rank 15",
        "consistent dead transverse pressure work only",
        "arbitrary anisotropic shear",
        "curved, dynamic, nonlinear",
    ):
        assert required in text
