"""Independent bounded checker for Q1C locking diagnostics.

The checker imports the accepted Q1B independent affine reconstruction, never
the Q1C producer or Q1B producer.  It rebuilds every response used for a
scientific decision and treats the ultra-thin binary64 row as conditioning
evidence when its equilibrated condition estimate exceeds the frozen limit.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
import sys
from typing import Any, Sequence

import numpy as np
from scipy import linalg

import e4_pl_q1b_assembled_checker as independent
import e4_pl_q1b_common as common


STUDY_ID = "study_e4_pl_q1c.q1b_locking_diagnosis_and_conditioning_repair_v1"
CANDIDATE_ID = "candidate_e4_pl_q1c.wg2020_locking_diagnosis_physical_block_scaling_v1"
PROOF_SCHEMA = "anysolver.s4.e4-pl-q1c-diagnostic-proof-v1"
CHECK_SCHEMA = "anysolver.s4.e4-pl-q1c-diagnostic-check-v1"
CHECKER_ID = "Q1C_INDEPENDENT_AFFINE_CONDITIONING_CHECKER"
Q1B_COMMIT = "3df23199893eb136b2682c5190d1405b52dbdd58"
SHARDS = ("SPATIAL_DISCRETIZATION", "THICKNESS_LOCKING", "CONDITIONING_SEPARATION")
DIVISIONS = (4, 8, 16, 32)
THICKNESSES = (1e-2, 1e-3, 1e-4, 1e-5, 1e-6)
ROW_KEYS = {
    "backward_error", "condition_equilibrated", "condition_unscaled",
    "displacement", "division", "drill_treatment", "eb_reference",
    "relative_error_eb", "relative_error_rm", "response_ratio_eb",
    "rm_reference", "thickness_ratio",
}


def _number(token: Any) -> float:
    if not isinstance(token, str):
        raise common.Q1BError("diagnostic number is not hexadecimal text")
    try:
        value = float.fromhex(token)
    except ValueError as exc:
        raise common.Q1BError("invalid diagnostic hexadecimal number") from exc
    if not math.isfinite(value) or value.hex() != token:
        raise common.Q1BError("noncanonical or nonfinite diagnostic number")
    return value


def _row(row: Any, *, division: int, thickness: float, treatment: str) -> dict[str, float]:
    if not isinstance(row, dict) or set(row) != ROW_KEYS:
        raise common.Q1BError("diagnostic row schema mismatch")
    if row["division"] != division or row["drill_treatment"] != treatment:
        raise common.Q1BError("diagnostic row identity mismatch")
    values = {key: _number(row[key]) for key in ROW_KEYS if key not in {"division", "drill_treatment"}}
    if values["thickness_ratio"] != thickness:
        raise common.Q1BError("diagnostic thickness mismatch")
    eb = 1.0 / (15.0 * (0.1 * thickness**3 / 12.0) * 3.0)
    rm = eb + 1.0 / ((5.0 / 6.0) * 6.0 * 0.1 * thickness)
    displacement = values["displacement"]
    derived = {
        "eb_reference": eb,
        "rm_reference": rm,
        "relative_error_eb": abs(displacement / eb - 1.0),
        "relative_error_rm": abs(displacement / rm - 1.0),
        "response_ratio_eb": abs(displacement / eb),
    }
    for key, expected in derived.items():
        if values[key] != expected:
            raise common.Q1BError(f"diagnostic derived value mismatch: {key}")
    if values["backward_error"] > 1e-12:
        raise common.Q1BError("diagnostic backward error exceeds frozen bound")
    return values


def _independent_response(divisions: int, thickness: float) -> tuple[float, float]:
    """Rebuild the physical strip operator without importing producer mechanics."""
    dx, dy = 1.0 / divisions, 0.1
    element = independent._affine_element(dx, dy, thickness)
    node_count = 2 * (divisions + 1)
    stride = divisions + 1
    stiffness = np.zeros((6 * node_count, 6 * node_count))
    for index in range(divisions):
        nodes = (index, index + 1, stride + index + 1, stride + index)
        dofs = np.array([6 * node + component for node in nodes for component in range(6)])
        stiffness[np.ix_(dofs, dofs)] += element
    physical = np.array([
        6 * node + component
        for node in range(node_count)
        if node not in (0, stride)
        for component in range(5)
    ])
    load = np.zeros(6 * node_count)
    load[6 * divisions + 2] = 0.5
    load[6 * (stride + divisions) + 2] = 0.5
    reduced = stiffness[np.ix_(physical, physical)]
    diagonal = np.abs(np.diag(reduced))
    scale = np.sqrt(np.maximum(diagonal, max(float(np.max(diagonal)) * 1e-30, np.finfo(float).tiny)))
    equilibrated = reduced / (scale[:, None] * scale[None, :])
    solution = np.zeros_like(load)
    solution[physical] = linalg.solve(equilibrated, load[physical] / scale, assume_a="sym") / scale
    displacement = float((solution[6 * divisions + 2] + solution[6 * (stride + divisions) + 2]) / 2.0)
    eb = 1.0 / (15.0 * (0.1 * thickness**3 / 12.0) * 3.0)
    return abs(displacement / eb - 1.0), float(np.linalg.cond(equilibrated))


def _close(observed: float, expected: float, tolerance: float = 5e-10) -> bool:
    return abs(observed - expected) <= tolerance * max(1.0, abs(observed), abs(expected))


def verify(proof_path: Path) -> dict[str, Any]:
    raw, proof = common.read_json(proof_path)
    proof_keys = {"candidate_id", "payload", "payload_sha256", "production", "q1b_commit", "schema", "study_id"}
    if not isinstance(proof, dict) or set(proof) != proof_keys:
        raise common.Q1BError("Q1C proof wrapper schema mismatch")
    if proof["schema"] != PROOF_SCHEMA or proof["candidate_id"] != CANDIDATE_ID or proof["study_id"] != STUDY_ID:
        raise common.Q1BError("Q1C proof identity mismatch")
    if proof["q1b_commit"] != Q1B_COMMIT or proof["production"] != "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED":
        raise common.Q1BError("Q1C proof authority mismatch")
    payload = proof["payload"]
    if not isinstance(payload, dict) or set(payload) != {"rows", "shard"} or payload["shard"] not in SHARDS:
        raise common.Q1BError("Q1C proof payload schema mismatch")
    if proof["payload_sha256"] != common.sha256(common.canonical_bytes(payload)):
        raise common.Q1BError("Q1C proof payload hash mismatch")

    shard = payload["shard"]
    rows = payload["rows"]
    contradictions: list[str] = []
    disagreements: list[str] = []
    conditioning_unresolved = False
    facts: dict[str, Any]

    if shard == "SPATIAL_DISCRETIZATION":
        if not isinstance(rows, list) or len(rows) != len(DIVISIONS):
            raise common.Q1BError("spatial coverage mismatch")
        errors = []
        for row, division in zip(rows, DIVISIONS, strict=True):
            values = _row(row, division=division, thickness=1e-4, treatment="SCHUR_CONDENSED")
            expected_error, _ = _independent_response(division, 1e-4)
            if not _close(values["relative_error_eb"], expected_error):
                disagreements.append(f"SPATIAL_RESPONSE_{division}")
            errors.append(values["relative_error_eb"])
        if any(current >= previous for previous, current in zip(errors, errors[1:])):
            contradictions.append("SPATIAL_CONVERGENCE")
        if errors[-1] >= 2e-2:
            contradictions.append("FINEST_MESH_ANALYTICAL_ERROR")
        facts = {"coarse_rows_are_convergence_evidence": True, "finest_error_below_two_percent": errors[-1] < 2e-2, "monotone_spatial_convergence": all(current < previous for previous, current in zip(errors, errors[1:]))}
    elif shard == "THICKNESS_LOCKING":
        if not isinstance(rows, list) or len(rows) != len(THICKNESSES):
            raise common.Q1BError("thickness coverage mismatch")
        values_by_thickness = []
        for row, thickness in zip(rows, THICKNESSES, strict=True):
            values = _row(row, division=32, thickness=thickness, treatment="SCHUR_CONDENSED")
            expected_error, expected_condition = _independent_response(32, thickness)
            if not _close(values["relative_error_eb"], expected_error):
                disagreements.append(f"THICKNESS_RESPONSE_{thickness:.0e}")
            if (values["condition_equilibrated"] > 1e14) != (expected_condition > 1e14):
                disagreements.append(f"CONDITION_CLASS_{thickness:.0e}")
            values_by_thickness.append(values)
        resolved = values_by_thickness[:4]
        ratios = [row["response_ratio_eb"] for row in resolved]
        if any(row["relative_error_eb"] >= 2e-2 for row in resolved):
            contradictions.append("RESOLVED_THICKNESS_ANALYTICAL_ERROR")
        if max(ratios) - min(ratios) > 5e-3:
            contradictions.append("RESOLVED_THICKNESS_RESPONSE_SPREAD")
        ultra = values_by_thickness[-1]
        conditioning_unresolved = ultra["condition_equilibrated"] > 1e14
        if not conditioning_unresolved and ultra["relative_error_eb"] >= 2e-2:
            contradictions.append("ULTRATHIN_ANALYTICAL_ERROR")
        facts = {"resolved_error_below_two_percent": all(row["relative_error_eb"] < 2e-2 for row in resolved), "resolved_response_spread_below_limit": max(ratios) - min(ratios) <= 5e-3, "ultrathin_conditioning_resolved": not conditioning_unresolved}
    else:
        if not isinstance(rows, list) or len(rows) != len(THICKNESSES):
            raise common.Q1BError("conditioning coverage mismatch")
        improvement = False
        for row, thickness in zip(rows, THICKNESSES, strict=True):
            if not isinstance(row, dict) or set(row) != {"condensed", "direct_full", "thickness_ratio"} or _number(row["thickness_ratio"]) != thickness:
                raise common.Q1BError("conditioning comparison schema mismatch")
            condensed = _row(row["condensed"], division=32, thickness=thickness, treatment="SCHUR_CONDENSED")
            direct = _row(row["direct_full"], division=32, thickness=thickness, treatment="DIRECT_FULL")
            expected_error, expected_condition = _independent_response(32, thickness)
            if not _close(condensed["relative_error_eb"], expected_error):
                disagreements.append(f"CONDENSED_RESPONSE_{thickness:.0e}")
            if (condensed["condition_equilibrated"] > 1e14) != (expected_condition > 1e14):
                disagreements.append(f"CONDENSED_CONDITION_CLASS_{thickness:.0e}")
            if thickness in THICKNESSES[:4] and abs(condensed["relative_error_eb"] - direct["relative_error_eb"]) > 5e-5:
                contradictions.append("RESOLVED_FORMULATION_PARITY")
            if thickness == 1e-6 and condensed["relative_error_eb"] < direct["relative_error_eb"]:
                improvement = True
            conditioning_unresolved |= condensed["condition_equilibrated"] > 1e14
        facts = {"resolved_full_equation_parity": "RESOLVED_FORMULATION_PARITY" not in contradictions, "ultrathin_condensation_improves_error": improvement, "ultrathin_conditioning_resolved": not conditioning_unresolved}

    return {
        "candidate_id": CANDIDATE_ID,
        "checker_id": CHECKER_ID,
        "classification_facts": facts,
        "conditioning_unresolved": conditioning_unresolved,
        "contradictions": sorted(set(contradictions)),
        "disagreements": sorted(set(disagreements)),
        "production": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "proof_sha256": common.sha256(raw),
        "schema": CHECK_SCHEMA,
        "shard": shard,
        "study_id": STUDY_ID,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-diagnostic", action="store_true", required=True)
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        common.write_exclusive(args.output, verify(args.proof))
        return 0
    except (OSError, ValueError, np.linalg.LinAlgError, common.Q1BError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
