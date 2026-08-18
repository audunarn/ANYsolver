from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess

import pytest


ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE = "ad90068a7ee78c3390dfe1b651f28be035094f41"
BASE_TREE = "e4cbb750ade5f2a160525e12b4c47afc5733a36a"
PRESERVED_ROOTS = {
    ".s4_candidate_a_pinned/",
    ".s4_stage_m_execution/",
    ".s4_stage_m_mpmath/",
    ".s4_stage_m_mpmath_clean/",
    ".s4_stage_m_patch_tools/",
    "tmp/",
}


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _load_json(path: str) -> dict[str, object]:
    raw = (ROOT / path).read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf") is False
    assert b"\r" not in raw
    assert raw.endswith(b"\n")
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_pairs,
        parse_constant=_reject_constant,
    )
    assert isinstance(value, dict)
    canonical = (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )
    assert raw == canonical
    return value


def _identity(path: str) -> tuple[int, str]:
    raw = (ROOT / path).read_bytes()
    return len(raw), hashlib.sha256(raw).hexdigest().upper()


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-c", "core.excludesFile=/dev/null", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _commit_with_subject(subject: str) -> str | None:
    matches = [
        line.split("\t", 1)[0]
        for line in _git("log", "--format=%H%x09%s", "HEAD").splitlines()
        if "\t" in line and line.split("\t", 1)[1] == subject
    ]
    assert len(matches) <= 1
    return matches[0] if matches else None


def _path_lines(value: str) -> set[str]:
    return {line.replace("\\", "/") for line in value.splitlines() if line}


def test_q1r_exact_baseline_and_q1a_blocked_closeout() -> None:
    baseline = _load_json("docs/reference_cases/e4_pl_q1r_baseline.json")
    assert baseline["authority"] == {
        "branch": "codex/s4-e4-pl-q1r-numbered-frame",
        "commit": BASE,
        "parent": "0435fae39d02e6f3c946deba0b74f29522f90137",
        "parent_subject": "docs: preserve aborted E4 PL Q1A authority record",
        "parent_tree": "13be1c75de0ae058b30e5e0d41188769d71df638",
        "subject": "docs: close E4 PL Q1A plan-authority block",
        "tree": BASE_TREE,
    }
    assert _git("rev-parse", f"{BASE}^{{tree}}") == BASE_TREE
    assert _git("rev-parse", f"{BASE}^") == baseline["authority"]["parent"]
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASE, "HEAD"],
        cwd=ROOT,
        check=True,
    )
    expected = {
        "docs/E4_PL_Q1A_PLAN_REVIEW.md": (
            9561,
            "342148665F7CA735335DC8BE7E824B2A98D9A5FACFEC2158BFEF8195926AC310",
        ),
        "docs/reference_cases/e4_pl_q1a_status.json": (
            2756,
            "97BC2D3F20D5D6B0DC2A8C7273CAB7A3BFAF97672FD3385B656843F2617233F9",
        ),
        "docs/E4_PL_Q1A_QUALIFICATION_REPORT.md": (
            4294,
            "0F8527F6B10E22E7A4226F73355F0DD94BA9673F0C3B6D977D07D56BE93B1F59",
        ),
        "docs/E4_PL_Q1A_INDEPENDENT_REVIEW.md": (
            5143,
            "22F4B1F781FB40DB4AEEFA4C57BF433B2EAF8506D9410A12FAC85ECACE69329D",
        ),
    }
    assert {row["path"]: (row["bytes"], row["sha256"]) for row in baseline["q1a_blocked_closeout"]["files"]} == expected
    for path, identity in expected.items():
        assert _identity(path) == identity
    assert baseline["q1a_blocked_closeout"]["terminal"] == "BLOCKED_E4_PL_Q1A_PLAN_AUTHORITY"
    assert baseline["q1a_blocked_closeout"]["mechanics_history"] == "NONCLASSIFYING_NOT_AN_EXECUTION_INPUT"
    for path in baseline["mandatory_absences"]:
        assert not (ROOT / path).exists()


def test_q1r_plan_contracts_are_static_complete_and_nonmechanical() -> None:
    source = _load_json("docs/reference_cases/e4_pl_q1r_source_map.json")
    frame = _load_json("docs/reference_cases/e4_pl_q1r_frame_contract.json")
    geometry = _load_json("docs/reference_cases/e4_pl_q1r_geometry_contract.json")
    material = _load_json("docs/reference_cases/e4_pl_q1r_material_contract.json")
    support = _load_json("docs/reference_cases/e4_pl_q1r_support_contract.json")
    cases = _load_json("docs/reference_cases/e4_pl_q1r_cases.json")
    assert source["identity_boundary"] == {
        "caller_bound_qualification_registered": False,
        "mechanics_executed": False,
        "production_registered": False,
        "q1b_authorized": False,
        "reference_or_oracle_present": False,
    }
    ops = frame["d4"]["operations"]
    assert [(x["id"], x["node_tuple"], x["det"]) for x in ops] == [
        ("E", [1, 2, 3, 4], 1),
        ("R90", [2, 3, 4, 1], 1),
        ("R180", [3, 4, 1, 2], 1),
        ("R270", [4, 1, 2, 3], 1),
        ("MR", [4, 3, 2, 1], -1),
        ("MS", [2, 1, 4, 3], -1),
        ("MD", [1, 4, 3, 2], -1),
        ("MA", [3, 2, 1, 4], -1),
    ]
    assert frame["d4"]["complete_orientation_reversal"] == {
        "id": "MD",
        "node_tuple": [1, 4, 3, 2],
        "rule": "NAMED_COMPLETE_REVERSAL_NO_NINTH_ACTION",
    }
    assert frame["frame"]["theorem"]["statement"] == "T(X^(g))=T(X)*Ahat_g"
    assert frame["frame"]["theorem"]["independent_reflection_repair"] == "FORBIDDEN"
    assert frame["field_transport"]["engineering_extraction"]["strain_order"] == ["11", "22", "2*12"]
    assert frame["field_transport"]["engineering_extraction"]["resultant_order"] == ["11", "22", "12"]
    assert frame["pl_transport"]["coefficient_map"] == "lambda_0=delta*S_g*lambda_g"
    assert frame["residual_mode"]["source_anchor"] == "WT2011_EQUATIONS_26.44_26.45"
    assert frame["residual_mode"]["vectors"] == {
        "eta": [-1, -1, 1, 1],
        "h4": [1, -1, 1, -1],
        "xi": [-1, 1, 1, -1],
    }
    assert frame["residual_mode"]["formula"]["gamma"] == "(h4-(h4^T*S1)*b1-(h4^T*S2)*b2)/4"
    assert material["exact_parameters"] == {
        "E": "15",
        "G": "6",
        "density": "UNUSED",
        "epsilon_hg": "1/1000",
        "gamma_PL": "6",
        "k_s": "5/6",
        "nu": "1/4",
        "t": "2/3",
    }
    assert [x["id"] for x in geometry["geometries"]] == [
        "Q0_SQUARE",
        "Q1_AFFINE_SKEW",
        "Q2_TRAPEZOID",
        "Q3_TAPERED_SKEW",
        "Q4_HOSTILE_ASYMMETRIC_1",
        "Q5_HOSTILE_ASYMMETRIC_2",
    ]
    assert geometry["global_transform"]["proper_rotation_certificates"] == [
        "R_star^T*R_star=I_3",
        "det(R_star)=1",
    ]
    assert len(cases["rigid_fields"]) == 6
    assert cases["hostile_geometry_provenance"]["origin"] == "EXPLICIT_USER_MANDATE_IN_THE_APPROVED_Q1R_REQUEST"
    assert cases["hostile_geometry_provenance"]["old_q1a_outcomes"] == "MUST_NOT_BE_IMPORTED_PREDICTED_OR_USED_TO_CLASSIFY_Q1R"
    assert cases["rigid_fields"][-1]["matched_spin_identity"] == "theta_D=(v_x-u_y)/2=1"
    assert cases["physical_load"]["p_f_node_major"] == [
        ["1", "2", "3", "4", "5"],
        ["-1", "1/2", "-2", "3/2", "-3"],
        ["2", "-1", "4", "-2", "1"],
        ["-2", "3", "-1", "1/3", "-1/2"],
    ]
    assert "DRILL_SUPPORT_ROW" in support["forbidden"]
    assert support["support_admissibility"]["condition"] == "A_bc*QD=0"
    if not (ROOT / "docs/reference_cases/e4_pl_q1r_implementation_manifest.json").exists():
        for forbidden in (
            "docs/reference_cases/e4_pl_q1r_reference.py",
            "docs/reference_cases/e4_pl_q1r_oracle.py",
            "docs/reference_cases/e4_pl_q1r_contract.json",
            "docs/reference_cases/e4_pl_q1r_output.json",
        ):
            assert not (ROOT / forbidden).exists()


def test_q1r_stage_barrier_extent_and_production_boundary() -> None:
    extent = _load_json("docs/reference_cases/e4_pl_q1r_allowed_extent.json")
    allowed = {row["path"] for row in extent["paths"]}
    stage_sets = {
        stage: {row["path"] for row in extent["paths"] if row["stage"] == stage}
        for stage in ("PLAN", "IMPLEMENTATION", "CONTRACT", "OUTCOME")
    }
    stages = ["PLAN"]
    prereg = _commit_with_subject("docs: preregister E4 PL Q1R numbered-frame qualification")
    implementation = _commit_with_subject("docs: freeze E4 PL Q1R independent implementations")
    execution = _commit_with_subject("docs: authorize E4 PL Q1R scientific execution")
    closeout = _commit_with_subject("docs: close E4 PL Q1R local qualification")
    frozen_boundaries: list[tuple[str, set[str]]] = []
    if prereg is not None:
        assert _git("rev-parse", f"{prereg}^") == BASE
        assert _path_lines(_git("diff-tree", "--no-commit-id", "--name-only", "-r", prereg)) == stage_sets["PLAN"]
        frozen_boundaries.append((prereg, set(stage_sets["PLAN"])))
        stages.append("IMPLEMENTATION")
    if implementation is not None:
        assert prereg is not None
        assert _git("rev-parse", f"{implementation}^") == prereg
        assert _path_lines(_git("diff-tree", "--no-commit-id", "--name-only", "-r", implementation)) == stage_sets["IMPLEMENTATION"]
        frozen_boundaries.append((implementation, stage_sets["PLAN"] | stage_sets["IMPLEMENTATION"]))
        stages.append("CONTRACT")
    if execution is not None:
        assert implementation is not None
        assert _git("rev-parse", f"{execution}^") == implementation
        assert _path_lines(_git("diff-tree", "--no-commit-id", "--name-only", "-r", execution)) == stage_sets["CONTRACT"]
        frozen_boundaries.append((execution, stage_sets["PLAN"] | stage_sets["IMPLEMENTATION"] | stage_sets["CONTRACT"]))
        stages.append("OUTCOME")
    if closeout is not None:
        assert execution is not None
        assert _git("rev-parse", f"{closeout}^") == execution
        assert _path_lines(_git("diff-tree", "--no-commit-id", "--name-only", "-r", closeout)) == stage_sets["OUTCOME"]
        frozen_boundaries.append((closeout, set(allowed)))
    for boundary, frozen in frozen_boundaries:
        assert _git("diff", "--name-only", boundary, "HEAD", "--", *sorted(frozen)) == ""
    if frozen_boundaries:
        latest_frozen = frozen_boundaries[-1][1]
        assert _git("diff", "--name-only", "--", *sorted(latest_frozen)) == ""
        assert _git("diff", "--cached", "--name-only", "--", *sorted(latest_frozen)) == ""
    stage_paths = {row["path"] for row in extent["paths"] if row["stage"] in stages}
    tracked_delta = _path_lines(_git("diff", "--name-only", BASE, "--"))
    untracked = _path_lines(_git("ls-files", "--others", "--exclude-standard"))
    untracked_candidate = {
        path
        for path in untracked
        if not any(path == root.rstrip("/") or path.startswith(root) for root in PRESERVED_ROOTS)
    }
    observed = tracked_delta | untracked_candidate
    assert observed <= allowed
    assert observed <= stage_paths
    if stages == ["PLAN"]:
        assert stage_paths - observed <= {"docs/E4_PL_Q1R_PLAN_REVIEW.md"}
    assert _git("diff", "--cached", "--name-only") == ""
    assert _git("diff", "--name-only", BASE, "--", ".gitattributes", ".github", "pyproject.toml", "setup.cfg", "setup.py", "src") == ""
    assert extent["sole_existing_file_modifications"] == []
    assert extent["q1b_paths_permitted"] is False
    assert not any("Q1B" in path for path in observed)
    roots = {
        line.replace("\\", "/")
        for line in _git("status", "--short").splitlines()
        if line[3:].replace("\\", "/") in PRESERVED_ROOTS
    }
    assert len(roots) == 6


def test_q1r_transport_environment_and_terminal_precedence_are_fail_closed() -> None:
    environment = _load_json("docs/reference_cases/e4_pl_q1r_environment.json")
    tolerances = _load_json("docs/reference_cases/e4_pl_q1r_tolerances.json")
    terminals = _load_json("docs/reference_cases/e4_pl_q1r_terminal_table.json")
    inventory = _load_json("docs/reference_cases/e4_pl_q1r_test_inventory.json")
    assert environment["execution"]["python_executable"] == "C:/Python/Python313/python.exe"
    assert environment["execution"]["python_version"] == "3.13.9"
    assert environment["execution"]["standard_library_only"] is True
    assert environment["execution"]["mpmath_forbidden"] is True
    assert environment["arithmetic"]["precision_bits"] == [256, 512, 1024]
    assert tolerances["precision_bits"] == [256, 512, 1024]
    assert tolerances["categorical_rules"]["covariance"]["pass"] == "STRUCTURAL_OR_ALGEBRAIC_EXACT_ZERO_ONLY"
    expected = [
        "BLOCKED_E4_PL_Q1R_BASELINE_MISMATCH",
        "BLOCKED_E4_PL_Q1R_PLAN_AUTHORITY",
        "BLOCKED_E4_PL_Q1R_FRAME_IDENTITY",
        "NO_GO_E4_PL_Q1R_FRAME_IDENTITY",
        "BLOCKED_E4_PL_Q1R_IMPLEMENTATION_IDENTITY",
        "BLOCKED_E4_PL_Q1R_CONTRACT_OR_NONDETERMINISM",
        "BLOCKED_E4_PL_Q1R_ORACLE_OR_REVIEW",
        "NO_GO_E4_PL_Q1R_LOCAL_ALGEBRA",
        "NO_GO_E4_PL_Q1R_PATCH_OR_COVARIANCE",
        "UNCLASSIFIED_E4_PL_Q1R_LOCAL_PLANAR_IDENTITY",
        "PROVISIONAL_GO_E4_PL_Q1R_Q1B_PLAN",
    ]
    assert [row["id"] for row in terminals["terminals"]] == expected
    assert [row["precedence"] for row in terminals["terminals"]] == list(range(1, 12))
    assert terminals["observed_outcome"] is None
    assert terminals["global_effect"]["production"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    assert inventory["inventories_must_not_be_combined"] is True
    assert inventory["q1r_preregistration"]["count"] == 4
    raw = b'{"a":1,"a":2}\n'
    with pytest.raises(ValueError, match="duplicate"):
        json.loads(raw, object_pairs_hook=_pairs, parse_constant=_reject_constant)
    with pytest.raises(ValueError, match="non-finite"):
        json.loads(b'{"x":NaN}', object_pairs_hook=_pairs, parse_constant=_reject_constant)
    attachment = pathlib.Path("C:/Users/AudunArnesenNyhus/Downloads/S4_E4_PL_Q1R_NUMBERED_FRAME_PLAN.md")
    assert len(attachment.read_bytes()) == 27001
    assert hashlib.sha256(attachment.read_bytes()).hexdigest().upper() == "3D8FE3ACF79B7C78B4B1D22E1DF40792B04603BAF88C99A390A0B499A97D27CA"
