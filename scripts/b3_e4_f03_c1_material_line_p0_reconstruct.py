"""Reconstruct two matched-law linear solid responses from 24 unit actions.

Uses the measured unsymmetrized compliance. The symmetric part is examined
only for positivity; it is never substituted into the KKT reconstruction.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from scripts.b3_e4_f03_c1_material_line_p0_reference import integrated_rows
from scripts.b3_e4_f03_ccx_six_channel_compliance import _source
from scripts.b3_e4_f03_ccx_six_channel_preflight import _element_domain_nodes
from scripts.b3_e4_f03_ccx_six_channel_reconstruct import (
    _same_stiffness_deck, _support_reactions, _wrench,
)
from scripts.b3_e4_f03_ccx_solid_bond_screen import EXE_SHA, digest
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_frd_u


def evaluate(source_root: Path, response_root: Path) -> dict:
    tip_mx = source_root / "tip_mx"
    deck, meta, coords, _, _, _ = _source(tip_mx)
    plate, bar = _element_domain_nodes(deck)
    nodes, rows, _ = integrated_rows(coords, plate, bar)
    all_nodes = tuple(sorted(coords))
    indices = {node: i for i, node in enumerate(all_nodes)}
    action_indices = np.array([indices[node] for node in nodes])
    scale = np.array([40000. if j % 6 < 3 else 4000.
                      for j in range(len(rows))])
    unit = []
    records = []
    source_commit = None
    for channel in range(len(rows)):
        folder = response_root / f"channel-{channel}"
        path = folder / "result.json"
        record = json.loads(path.read_text())
        stem = f"material-line-p0-{channel}"
        frd = folder / f"{stem}.frd"
        if (record["status"] != "EXPLORATORY_COMPLETE" or
                record["channel"] != channel or
                record["applied_density_scale"] != scale[channel] or
                record["source_deck_sha256"] != digest(deck) or
                record["source_model_sha256"] != digest(tip_mx / "model.json") or
                record["solver_sha256"] != EXE_SHA or
                record["generated_deck_sha256"] != digest(folder / f"{stem}.inp") or
                record["failure"] is not None):
            raise ValueError("unit-action identity or completion changed")
        if source_commit is None:
            source_commit = record["source_commit"]
        elif source_commit != record["source_commit"]:
            raise ValueError("unit-action source commits differ")
        field = _read_frd_u(frd)
        if set(field) != set(coords):
            raise ValueError("incomplete unit displacement")
        array = np.array([field[node] for node in all_nodes])
        gaps = rows @ array[action_indices].ravel()
        np.testing.assert_allclose(gaps, record["gap_response"],
                                   rtol=2e-12, atol=5e-15)
        unit.append(array)
        records.append({"channel": channel, "result_sha256": digest(path),
                        "frd_sha256": digest(frd)})
    unit_array = np.stack(unit)
    G = np.array([rows @ array[action_indices].ravel()
                  for array in unit_array]).T
    W = scale[:, None]*G
    skew = float(np.linalg.norm(W-W.T)/np.linalg.norm(W))
    eigen = np.linalg.eigvalsh((W+W.T)/2.)
    if (not np.isfinite(G).all() or skew > 5e-6 or eigen[0] <= 0.):
        raise ArithmeticError("measured solid work compliance is unsuitable for diagnostic reconstruction")
    source_stiffness = None
    cases = {}
    for label in ("tip_mx", "tip_fz"):
        folder = source_root / label
        source_meta = json.loads((folder / "model.json").read_text())
        source_decks = list(folder.glob("*.inp"))
        source_frds = list(folder.glob("*.frd"))
        if len(source_decks) != 1 or len(source_frds) != 1:
            raise ValueError("one complete source case required")
        if label == "tip_fz":
            source_stiffness = _same_stiffness_deck(deck, source_decks[0])
        field = _read_frd_u(source_frds[0])
        if set(field) != set(coords):
            raise ValueError("source field geometry changed")
        base = np.array([field[node] for node in all_nodes])
        gap_before = rows@base[action_indices].ravel()
        coefficient = np.linalg.solve(G, gap_before)
        constrained = base-np.tensordot(coefficient, unit_array, axes=(0, 0))
        gap_after = rows@constrained[action_indices].ravel()
        if np.linalg.norm(scale*gap_after) > 1e-8:
            raise ArithmeticError("matched-law weak constraints did not close")
        support_base = _support_reactions(folder, source_decks[0].stem, source_meta)
        support_unit = [_support_reactions(
            response_root / f"channel-{j}", f"material-line-p0-{j}", meta)
            for j in range(len(rows))]
        if any(set(support) != set(support_base) for support in support_unit):
            raise ValueError("support inventory changed across action cases")
        support = {node: support_base[node] - sum(
            coefficient[j]*support_unit[j][node] for j in range(len(rows)))
                   for node in support_base}
        applied = {int(node): np.asarray(value, dtype=float)
                   for node, value in source_meta["applied_nodal_forces_N"].items()}
        balance = _wrench(coords, support)+_wrench(coords, applied)
        dual = scale*coefficient
        action = -(rows.T@dual).reshape(-1, 3)
        line_forces = {node: action[i] for i, node in enumerate(nodes)}
        plate_forces = {node: action[i] for i, node in enumerate(nodes) if node in plate}
        bar_forces = {node: action[i] for i, node in enumerate(nodes) if node in bar}
        if len(plate_forces)+len(bar_forces) != len(nodes):
            raise ArithmeticError("unowned line action node")
        interface_wrench = _wrench(coords, line_forces)
        plate_work = float(sum(force@constrained[indices[node]]
                               for node, force in plate_forces.items()))
        bar_work = float(sum(force@constrained[indices[node]]
                             for node, force in bar_forces.items()))
        if (np.linalg.norm(interface_wrench) > 1e-7 or
                abs(plate_work+bar_work) > 1e-8):
            raise ArithmeticError("joint physical wrench/work does not cancel")
        load_work = float(sum(force@constrained[indices[node]]
                              for node, force in applied.items()))
        tip_nodes = [int(node) for node in source_meta["bar_station_nodes"]["1000"]]
        tip_mean = np.mean(constrained[[indices[node] for node in tip_nodes]], axis=0)
        cases[label] = {
            "source_deck_sha256": digest(source_decks[0]),
            "source_model_sha256": digest(folder / "model.json"),
            "source_frd_sha256": digest(source_frds[0]),
            "weak_gap_before": gap_before.tolist(),
            "weak_gap_after": gap_after.tolist(),
            "maximum_absolute_weak_gap_after": float(np.max(np.abs(gap_after))),
            "dual_physical_line_density": dual.tolist(),
            "tip_section_mean_displacement_m": tip_mean.tolist(),
            "applied_load_work_J": load_work,
            "tip_work_conjugate_displacement": load_work / (100. if label == "tip_mx" else 1000.),
            "plate_interface_wrench_N_Nm": _wrench(coords, plate_forces).tolist(),
            "bar_interface_wrench_N_Nm": _wrench(coords, bar_forces).tolist(),
            "plate_interface_work_J": plate_work,
            "bar_interface_work_J": bar_work,
            "global_external_support_balance": balance.tolist(),
            "joint_global_wrench": interface_wrench.tolist(),
            "algebraic_gap_defect": float(np.linalg.norm(G@coefficient-gap_before)),
        }
    return {
        "status": "EXPLORATORY_COMPLETE",
        "classification": "matched detached-solid linear exact P0 material-line KKT reconstruction",
        "source_root": str(source_root),
        "response_root": str(response_root),
        "unit_source_commit": source_commit,
        "unit_records": records,
        "common_stiffness_sha256": source_stiffness,
        "work_compliance_relative_skew": skew,
        "work_compliance_minimum_symmetric_eigenvalue_J": float(eigen[0]),
        "work_compliance_condition": float(np.linalg.cond(W)),
        "cases": cases,
        "limitations": [
            "5e-6 skew is a bounded FRD-precision diagnostic allowance, not a changed scientific acceptance limit",
            "measured unsymmetrized compliance used in reconstruction",
            "linear contact-free detached solid and provisional P0 m4 weak law",
            "no native/solid accuracy, mesh convergence, F03 or G0B acceptance",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--responses", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve prior matched-law reconstruction")
    report = evaluate(args.source_root.resolve(), args.responses.resolve())
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True,
                                      allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps({"status": report["status"],
                      "relative_skew": report["work_compliance_relative_skew"],
                      "minimum_eigenvalue_J": report["work_compliance_minimum_symmetric_eigenvalue_J"],
                      "cases": {name: value["tip_work_conjugate_displacement"]
                                for name, value in report["cases"].items()}}))


if __name__ == "__main__":
    main()
