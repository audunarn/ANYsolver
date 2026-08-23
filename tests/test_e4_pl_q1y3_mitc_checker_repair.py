from __future__ import annotations

import ast
from fractions import Fraction
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_CASES = ROOT / "docs" / "reference_cases"
sys.path.insert(0, str(REFERENCE_CASES))

import e4_pl_q1y3_algebra_checker as checker
import e4_pl_q1y3_bounded_runner as runner
import e4_pl_q1y_common as common


CONTRACT = REFERENCE_CASES / "e4_pl_q1y3_local_algebra_contract.json"
CONTRACT_SHA = common.sha256(CONTRACT.read_bytes())
RESULT = REFERENCE_CASES / "e4_pl_q1y3_bounded_result.json"


class FractionField:
    @staticmethod
    def exact(value: object) -> Fraction:
        return Fraction(value)


class FractionGeometry:
    def __init__(self, nodes: list[tuple[Fraction, Fraction]]) -> None:
        self.field = FractionField()
        self.local_nodes = nodes
        x = [node[0] for node in nodes]
        y = [node[1] for node in nodes]
        self.coefficients = {
            "xr": (-x[0] + x[1] + x[2] - x[3]) / 4,
            "xs": (-x[0] - x[1] + x[2] + x[3]) / 4,
            "yr": (-y[0] + y[1] + y[2] - y[3]) / 4,
            "ys": (-y[0] - y[1] + y[2] + y[3]) / 4,
            "xrs": (x[0] - x[1] + x[2] - x[3]) / 4,
            "yrs": (y[0] - y[1] + y[2] - y[3]) / 4,
        }


def _rejected_pointwise_rows(geometry: FractionGeometry, r: Fraction, s: Fraction) -> tuple[list[Fraction], list[Fraction]]:
    field = geometry.field
    f0 = [Fraction(1, 4)] * 4
    fr = [Fraction(-1, 4), Fraction(1, 4), Fraction(1, 4), Fraction(-1, 4)]
    fs = [Fraction(-1, 4), Fraction(-1, 4), Fraction(1, 4), Fraction(1, 4)]
    frs = [Fraction(1, 4), Fraction(-1, 4), Fraction(1, 4), Fraction(-1, 4)]
    tr = [field.exact(0) for _ in range(20)]
    ts = [field.exact(0) for _ in range(20)]
    c = geometry.coefficients
    xr = c["xr"] + c["xrs"] * s
    xs = c["xs"] + c["xrs"] * r
    yr = c["yr"] + c["yrs"] * s
    ys = c["ys"] + c["yrs"] * r
    determinant = xr * ys - xs * yr
    for index in range(4):
        base = 5 * index
        tr[base + 2] = fr[index] + s * frs[index]
        ts[base + 2] = fs[index] + r * frs[index]
        tr[base + 4] = xr * (f0[index] + s * fs[index])
        tr[base + 3] = -yr * (f0[index] + s * fs[index])
        ts[base + 4] = xs * (f0[index] + r * fr[index])
        ts[base + 3] = -ys * (f0[index] + r * fr[index])
    gx = [(ys * tr[index] - yr * ts[index]) / determinant for index in range(20)]
    gy = [(-xs * tr[index] + xr * ts[index]) / determinant for index in range(20)]
    return gx, gy


def test_q1y3_contract_incident_and_boundary_are_exact() -> None:
    raw, value = common.read_json(CONTRACT)
    assert raw == common.canonical_bytes(value)
    checked = runner.validate_successor_contract(ROOT, CONTRACT, CONTRACT_SHA)
    assert checked["base_commit"] == "c7ca8791819742cb424789038392ce908369a3b1"
    incident = checked["checker"]["incident"]
    assert incident["classification"] == "INDEPENDENT_CHECKER_MITC_TYING_DEFECT"
    assert incident["affected_stress_rows"] == [6, 7, 12, 13]
    assert incident["affected_physical_columns"] == [4, 10, 16, 22]
    assert incident["verified_q2_repair"] == {"c_core_exact": True, "k_core_exact": True}
    changed = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=ROOT, text=True, stdout=subprocess.PIPE, check=True,
    ).stdout.splitlines()
    changed_paths = [row[3:].replace("\\", "/") for row in changed]
    assert not any(path == "pyproject.toml" or path == ".gitattributes" or path.startswith(("src/", ".github/")) for path in changed_paths)


def test_q1y3_tying_formula_preserves_affine_and_repairs_nonaffine_order() -> None:
    affine = FractionGeometry([
        (Fraction(-1), Fraction(-1)), (Fraction(1), Fraction(-1)),
        (Fraction(1), Fraction(1)), (Fraction(-1), Fraction(1)),
    ])
    nonaffine = FractionGeometry([
        (Fraction(-1), Fraction(-1)), (Fraction(1), Fraction(-1)),
        (Fraction(2), Fraction(1)), (Fraction(-1), Fraction(1)),
    ])
    r, s = Fraction(1, 3), Fraction(-1, 4)
    assert checker._mitc_shear_rows(affine, r, s) == _rejected_pointwise_rows(affine, r, s)
    corrected = checker._mitc_shear_rows(nonaffine, r, s)
    rejected = _rejected_pointwise_rows(nonaffine, r, s)
    assert corrected != rejected
    differing = [(row, column) for row in range(2) for column in range(20) if corrected[row][column] != rejected[row][column]]
    assert differing
    assert {column % 5 for _, column in differing} <= {3, 4}


def test_q1y3_tying_stations_and_interpolation_weights_are_exact() -> None:
    geometry = FractionGeometry([
        (Fraction(-1), Fraction(-1)), (Fraction(1), Fraction(-1)),
        (Fraction(2), Fraction(1)), (Fraction(-1), Fraction(1)),
    ])
    field = geometry.field
    zero, one = field.exact(0), field.exact(1)
    gr_a = checker._natural_shear_row(geometry, zero, -one, 0)
    gr_c = checker._natural_shear_row(geometry, zero, one, 0)
    gs_b = checker._natural_shear_row(geometry, one, zero, 1)
    gs_d = checker._natural_shear_row(geometry, -one, zero, 1)
    assert gr_a != gr_c and gs_b != gs_d
    midpoint_r = [(left + right) / 2 for left, right in zip(gr_a, gr_c, strict=True)]
    midpoint_s = [(left + right) / 2 for left, right in zip(gs_b, gs_d, strict=True)]
    xr, xs, yr, ys, determinant = __import__("e4_pl_q1v_oracle")._jacobian(geometry, zero, zero)
    expected_x = [(ys * midpoint_r[index] - yr * midpoint_s[index]) / determinant for index in range(20)]
    expected_y = [(-xs * midpoint_r[index] + xr * midpoint_s[index]) / determinant for index in range(20)]
    assert checker._mitc_shear_rows(geometry, zero, zero) == (expected_x, expected_y)


def test_q1y3_checker_is_independent_and_mutation_sensitive() -> None:
    path = REFERENCE_CASES / "e4_pl_q1y3_algebra_checker.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = {
        alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names
    } | {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    assert "e4_pl_q1y_algebra_producer" not in imports
    assert not any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in {"evalf", "simplify"}
        for node in ast.walk(tree)
    )
    geometry = FractionGeometry([
        (Fraction(-1), Fraction(-1)), (Fraction(1), Fraction(-1)),
        (Fraction(2), Fraction(1)), (Fraction(-1), Fraction(1)),
    ])
    original = checker._mitc_shear_rows(geometry, Fraction(1, 3), Fraction(-1, 4))
    geometry.local_nodes[2] = (Fraction(5, 2), Fraction(1))
    geometry.__init__(geometry.local_nodes)
    assert checker._mitc_shear_rows(geometry, Fraction(1, 3), Fraction(-1, 4)) != original


def test_q1y3_terminal_precedence_and_bounds_are_unchanged() -> None:
    contract = runner.validate_successor_contract(ROOT, CONTRACT, CONTRACT_SHA)
    assert runner.select_terminal(contract, blocked=True, local=True, covariance=True, unresolved=True) == contract["terminals"]["blocked"]
    assert runner.select_terminal(contract, blocked=False, local=True, covariance=True, unresolved=True) == contract["terminals"]["local_algebra"]
    assert runner.select_terminal(contract, blocked=False, local=False, covariance=True, unresolved=True) == contract["terminals"]["operator_covariance"]
    assert runner.select_terminal(contract, blocked=False, local=False, covariance=False, unresolved=True) == contract["terminals"]["ordered_sign"]
    assert runner.select_terminal(contract, blocked=False, local=False, covariance=False, unresolved=False) == contract["terminals"]["success"]
    assert contract["parallelism"]["global_timeout_seconds"] == 600
    assert contract["parallelism"]["producer_workers"] == 7
    assert contract["parallelism"]["checker_workers"] == 4
    assert contract["production"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    assert contract["q1b_execution"] == "UNAUTHORIZED"
    raw, result = common.read_json(RESULT)
    assert raw == common.canonical_bytes(result)
    assert result["contract_sha256"] == CONTRACT_SHA
    assert result["terminal"] == contract["terminals"]["success"]
    assert result["coverage"] == {"case_count": 56, "geometry_count": 7, "rigid_mode_count": 6}
    assert len(result["shards"]) == 7
    assert all(row["producer_status"] == "COMPLETE" for row in result["shards"])
    assert all(row["checker_statuses"] == ["COMPLETE", "COMPLETE"] for row in result["shards"])
    assert all(row["checker_byte_identical"] for row in result["shards"])
    assert not any(row["proof_disagreement"] for row in result["shards"])
    assert not any(row["local_contradiction"] or row["operator_contradiction"] for row in result["shards"])
    assert result["q3_proper_global_local_identity"]
    assert not result["local_algebra_contradiction"]
    assert not result["operator_covariance_contradiction"]
    assert not result["ordered_sign_unresolved"]
