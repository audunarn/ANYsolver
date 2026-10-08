"""Adjudicate the executed 8x4x2 CalculiX deck against its physical-row KKT oracle.

Development-only same-law comparison. It neither selects BL5 nor consumes F03.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu

from scripts import r8_bl5_ccx_matched_mx_deck_dev as specimen
from scripts import r8_bl5_mx_coupled_shell_refinement_dev as shell_ref
from scripts import r8_bl5_mx_matched_refinement_dev as matched
from scripts import r8_bl5_mx_torsion_refinement_dev as beam_ref
from scripts import r8_bl5_weak_continuum_reference as continuum
from scripts.r8_e02_double_output import read_double_output


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def wrench(model: dict, order: tuple[int, ...], values: np.ndarray) -> np.ndarray:
    result = np.zeros(6)
    for i, node in enumerate(order):
        force = values[3*i:3*i+3]
        result[:3] += force
        result[3:] += np.cross(model["physical_nodes"][node], force)
    return result


def compare(case: Path, independent: Path) -> dict:
    metadata = json.loads((case / "metadata.json").read_text(encoding="utf-8"))
    execution = json.loads((case / "ccx.receipt.json").read_text(encoding="utf-8"))
    prepared = json.loads((case.parent / "receipt.json").read_text(encoding="utf-8"))
    expected_deck, expected_metadata = specimen.deck(independent)
    if (execution["status"] != "EXITED" or execution["exit_code"] != 0 or
            execution["executable_sha256"] !=
            "27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f" or
            execution["deck_sha256"] != sha256(expected_deck).hexdigest() or
            (case / "weak.inp").read_bytes() != expected_deck or
            metadata != json.loads(json.dumps(expected_metadata)) or
            digest(case / "metadata.json") != prepared["case_file_sha256"]["metadata.json"] or
            digest(case.parent / "receipt.json") != execution["prep_receipt_sha256"] or
            any(digest(case / name) != value for name, value in execution["file_sha256"].items())):
        raise ValueError("executed external inputs or outputs differ from frozen identities")
    if "     1          1     1     1  0.100000E+01" not in (
            case / "weak.sta").read_text(encoding="ascii"):
        raise ValueError("one complete accepted external increment required")

    nx, ny, nz = specimen.LEVEL
    shell_nodes, shell_elements = shell_ref._shell_mesh(nx, ny, nz)
    beam_nodes, beam_elements = beam_ref._mesh(nx, ny, nz)
    model = shell_ref._combined(shell_nodes, shell_elements, beam_nodes, beam_elements)
    if ({str(k): list(v) for k, v in model["physical_nodes"].items()} != metadata["physical_nodes"] or
            {str(k): list(v) for k, v in model["elements"].items()} != metadata["elements"]):
        raise ValueError("independent geometry does not match executed deck")
    shell = shell_ref._shell_body(shell_nodes, shell_elements, specimen.LEVEL)
    beam = beam_ref._body(beam_nodes, beam_elements, specimen.LEVEL)
    k = sparse.block_diag((shell, beam), format="csr")
    c, scale = matched._weak_rows(model, nx)
    order, index, fixed, free, _ = continuum.layout(model)
    load = np.asarray(metadata["physical_tip_load_N"], dtype=float)
    if k.shape != (len(load), len(load)) or c.shape != (40, len(load)):
        raise ValueError("independent operator dimensions changed")

    # Physical rows are scaled numerically, never replaced by CalculiX pivot rows.
    physical = k[free, :][:, free].tocsc()
    cf = c[:, free].tocsc()
    dq = 1. / np.sqrt(physical.diagonal())
    dl = 1. / np.sqrt(np.asarray((cf @ sparse.diags(dq)).power(2).sum(axis=1)).ravel())
    if not np.isfinite(dq).all() or not np.isfinite(dl).all():
        raise ValueError("nonfinite KKT scaling")
    dp, dm = sparse.diags(dq), sparse.diags(dl)
    system = sparse.bmat([[dp @ physical @ dp, dp @ cf.T @ dm],
                          [dm @ cf @ dp, None]], format="csc")
    rhs = np.r_[dq * load[free], np.zeros(c.shape[0])]
    factor = splu(system)
    state = factor.solve(rhs)
    for _ in range(3):
        state += factor.solve(rhs - system @ state)
    reference = np.zeros(len(load))
    reference[free] = dq * state[:len(free)]
    lagrange = dl * state[len(free):]
    observed, reactions = read_double_output((case / "weak.frd").read_bytes(), metadata)
    actual = np.array([v for node in order for v in observed[node]])
    raw_root = np.array([v for node in model["root_nodes"] for v in reactions[node]])
    gap = np.asarray(c @ actual).ravel()
    residual = np.asarray(k @ actual - load).ravel()
    fitted = np.linalg.lstsq(cf.T.toarray(), -residual[free], rcond=None)[0]
    force = np.asarray(c.T @ fitted).ravel()
    root_support = raw_root + force[fixed]
    reference_augmented = np.asarray(k @ reference - load + c.T @ lagrange).ravel()
    support_full = np.zeros(len(load))
    support_full[fixed] = root_support
    tip_wrench = wrench(model, order, load)
    support_wrench = wrench(model, order, support_full)
    work = float(load @ actual)
    strain_work = float(actual @ (k @ actual))
    independent_work = float(load @ reference)
    independent_record = json.loads(independent.read_text(encoding="utf-8"))
    result = {
        "identity": "R8_BL5_CCX_MATCHED_MX_8X4X2_COMPARISON_DEV_V1",
        "status": "DEVELOPMENT_PARITY_FAILED",
        "source_sha256": digest(Path(__file__)),
        "independent_sha256": digest(independent),
        "metadata_sha256": digest(case / "metadata.json"),
        "deck_sha256": digest(case / "weak.inp"),
        "ccx_receipt_sha256": digest(case / "ccx.receipt.json"),
        "frd_sha256": digest(case / "weak.frd"),
        "nodes": len(order), "elements": len(model["elements"]),
        "physical_dofs": len(load), "physical_weak_rows": c.shape[0],
        "kkt_nnz": system.nnz,
        "ccx_applied_work_J": work,
        "independent_applied_work_J": independent_work,
        "saved_independent_applied_work_J": independent_record["resolved"]["applied_work_J"],
        "ccx_tip_spin_x_rad": work / specimen.TORQUE_NM,
        "ccx_root_support_wrench": support_wrench.tolist(),
        "ccx_tip_wrench": tip_wrench.tolist(),
        "ccx_global_wrench_balance": (support_wrench + tip_wrench).tolist(),
        "ccx_interface_work_J": float((-force) @ actual),
        "ccx_raw_root_rf_norm_N": float(np.linalg.norm(raw_root)),
        "ccx_corrected_root_support_norm_N": float(np.linalg.norm(root_support)),
    }
    checks = {
        "displacement_parity": float(np.linalg.norm(actual-reference)/max(np.linalg.norm(reference), 1e-14)),
        "saved_independent_work": abs(independent_work-result["saved_independent_applied_work_J"])/max(abs(independent_work), 1e-12),
        "independent_equation": float(np.linalg.norm(system @ state-rhs)/max(np.linalg.norm(load), 1.)),
        "weak_gap": float(np.max(np.abs(gap / scale))),
        "free_equilibrium": float(np.linalg.norm(residual[free]+force[free])/max(np.linalg.norm(load), 1.)),
        "raw_reaction": float(np.linalg.norm(raw_root-residual[fixed])/max(np.linalg.norm(load), 1.)),
        "physical_support": float(np.linalg.norm(root_support-reference_augmented[fixed])/max(np.linalg.norm(load), 1.)),
        "force_balance": float(np.max(np.abs((support_wrench+tip_wrench)[:3]))/max(np.linalg.norm(tip_wrench[:3]), 1.)),
        "moment_balance": float(np.max(np.abs((support_wrench+tip_wrench)[3:]))/max(np.linalg.norm(tip_wrench[3:]), 1.)),
        "work_balance": abs(strain_work-work)/max(abs(work), 1e-12),
    }
    limits = {name: (1e-9 if name == "weak_gap" else 1e-6) for name in checks}
    result["development_parity_checks"] = checks
    result["development_parity_limits"] = limits
    if all(np.isfinite(value) and value <= limits[name] for name, value in checks.items()):
        result["status"] = "DEVELOPMENT_COMPARISON_NOT_QUALIFIED"
    result["limitation"] = ("Same-law executed C3D20 deck parity only; resolved-work refinement "
                            "and native BL5/F03 connection acceptance remain open")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--independent", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("comparison evidence already exists")
    result = compare(args.case, args.independent)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "checks": result["development_parity_checks"],
                      "ccx_applied_work_J": result["ccx_applied_work_J"]}))
    if result["status"] != "DEVELOPMENT_COMPARISON_NOT_QUALIFIED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
