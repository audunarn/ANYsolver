"""Reconstruct exact linear 12-row split-law response from capped solid runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from scripts.b3_e4_f03_ccx_split_six_channel import (
    EXE_SHA, REFERENCE, _element_domain_nodes, _source, preflight, split_rows,
)
from scripts.b3_e4_f03_ccx_six_channel_compliance import ACTION_SCALES
from scripts.b3_e4_f03_ccx_six_channel_reconstruct import (
    _gaps, _same_stiffness_deck, _support_reactions, _wrench,
)
from scripts.b3_e4_f03_ccx_solid_bond_screen import digest
from scripts.b3_e4_f03_solid_bond_pose_projection import (
    _read_deck_nodes, _read_frd_u,
)


def evaluate(source_root: Path, response_root: Path) -> dict:
    reference = json.loads(REFERENCE.read_text())
    runner_hash = digest(Path(__file__).with_name(
        "b3_e4_f03_ccx_split_six_channel.py"))
    tip_mx = source_root / "tip_mx"
    deck, meta, coords, _, _, _ = _source(tip_mx)
    plate_nodes, bar_nodes = _element_domain_nodes(deck)
    rows = split_rows(coords, plate_nodes, bar_nodes)
    audit = preflight(coords, rows, set(meta["boundary_node_ids"]),
                      plate_nodes, bar_nodes)
    if (digest(deck) !=
            reference["cases"]["tip_mx"]["source_deck_sha256"] or
            digest(tip_mx / "model.json") !=
            reference["cases"]["tip_mx"]["source_model_sha256"]):
        raise ValueError("split source differs from global-six reference")
    unit, unit_records = [], []
    run_identity = None
    for channel in range(12):
        folder = response_root / f"channel-{channel}"
        result_path = folder / "result.json"
        result = json.loads(result_path.read_text())
        stem = f"split-six-channel-{channel}"
        frd_path = folder / f"{stem}.frd"
        identity = (result["source_commit"], result["runner_sha256"],
                    result["reference_sha256"])
        if (result["status"] != "EXPLORATORY_COMPLETE" or
                result["failure"] is not None or
                result["channel"] != channel or
                result["applied_dual_scale"] != ACTION_SCALES[channel % 6] or
                result["source_deck_sha256"] != digest(deck) or
                result["source_model_sha256"] != digest(tip_mx / "model.json") or
                result["solver_sha256"] != EXE_SHA or
                result["runner_sha256"] != runner_hash or
                result["generated_deck_sha256"] != digest(folder / f"{stem}.inp") or
                result["reference_sha256"] != digest(REFERENCE) or
                result["preflight"] != audit):
            raise ValueError("split unit-action identity or completion changed")
        if run_identity is None:
            run_identity = identity
        elif identity != run_identity:
            raise ValueError("split action runs used different source versions")
        field = _read_frd_u(frd_path)
        if set(field) != set(coords):
            raise ValueError("incomplete split unit-action displacement")
        np.testing.assert_allclose(_gaps(rows, field),
                                   result["gap_response"],
                                   rtol=2e-12, atol=5e-15)
        unit.append(field)
        unit_records.append({"channel": channel,
                             "result_sha256": digest(result_path),
                             "frd_sha256": digest(frd_path)})
    scale = np.tile(np.asarray(ACTION_SCALES), 2)
    compliance = np.array([_gaps(rows, field) for field in unit]).T
    work_compliance = scale[:, None]*compliance
    skew = float(np.linalg.norm(work_compliance-work_compliance.T) /
                 np.linalg.norm(work_compliance))
    eigen = np.linalg.eigvalsh((work_compliance+work_compliance.T)/2)
    if (skew > 1e-6 or eigen[0] <= 0 or
            not np.isfinite(compliance).all()):
        raise ArithmeticError("split-law compliance fails work or positivity")
    common_stiffness = None
    cases = {}
    support_unit = [_support_reactions(
        response_root / f"channel-{j}", f"split-six-channel-{j}", meta)
        for j in range(12)]
    for label in ("tip_mx", "tip_fz"):
        folder = source_root / label
        source_meta = json.loads((folder / "model.json").read_text())
        decks = list(folder.glob("*.inp"))
        frds = list(folder.glob("*.frd"))
        if len(decks) != 1 or len(frds) != 1:
            raise ValueError("one complete source case required")
        if (digest(decks[0]) != reference["cases"][label]["source_deck_sha256"] or
                digest(folder / "model.json") !=
                reference["cases"][label]["source_model_sha256"] or
                digest(frds[0]) != reference["cases"][label]["source_frd_sha256"]):
            raise ValueError("matched loaded source identity changed")
        if label == "tip_fz":
            common_stiffness = _same_stiffness_deck(deck, decks[0])
            if common_stiffness != reference["common_stiffness_sha256"]:
                raise ValueError("source stiffness identity changed")
        other_coords = _read_deck_nodes(decks[0])
        if (set(other_coords) != set(coords) or any(
                not np.array_equal(other_coords[node], coords[node])
                for node in coords)):
            raise ValueError("loaded source geometry changed")
        base = _read_frd_u(frds[0])
        if set(base) != set(coords):
            raise ValueError("incomplete loaded source displacement")
        initial_gap = _gaps(rows, base)
        coefficient = np.linalg.solve(compliance, initial_gap)
        state = {node: base[node]-sum(coefficient[j]*unit[j][node]
                                      for j in range(12))
                 for node in coords}
        gap = _gaps(rows, state)
        if np.linalg.norm(scale*gap) > 1e-8:
            raise ArithmeticError("reconstructed split joint has nonzero gap")
        support_base = _support_reactions(folder, decks[0].stem, source_meta)
        support = {node: support_base[node]-sum(
            coefficient[j]*support_unit[j][node] for j in range(12))
                   for node in support_base}
        applied = {int(node): np.asarray(value, dtype=float)
                   for node, value in source_meta["applied_nodal_forces_N"].items()}
        balance = _wrench(coords, support)+_wrench(coords, applied)
        dual = scale*coefficient
        forces = {}
        for j, row in enumerate(rows):
            for (node, axis), value in row.items():
                forces.setdefault(node, np.zeros(3))[axis] -= dual[j]*value
        joint_wrench = _wrench(coords, forces)
        if np.linalg.norm(joint_wrench) > 1e-7:
            raise ArithmeticError("split joint action has nonzero global wrench")
        plate_action = {node: force for node, force in forces.items()
                        if node in plate_nodes}
        bar_action = {node: force for node, force in forces.items()
                      if node in bar_nodes}
        if len(plate_action)+len(bar_action) != len(forces):
            raise ArithmeticError("split joint action has unowned nodes")
        plate_work = float(sum(force@state[node]
                               for node, force in plate_action.items()))
        bar_work = float(sum(force@state[node]
                             for node, force in bar_action.items()))
        if abs(plate_work+bar_work) > 1e-8:
            raise ArithmeticError("split joint side work does not cancel")
        load_work = float(sum(force@state[node]
                              for node, force in applied.items()))
        tip_nodes = [int(node) for node in source_meta["bar_station_nodes"]["1000"]]
        tip_mean = np.mean([state[node] for node in tip_nodes], axis=0)
        cases[label] = {
            "source_deck_sha256": digest(decks[0]),
            "source_model_sha256": digest(folder / "model.json"),
            "source_frd_sha256": digest(frds[0]),
            "unconstrained_gap": initial_gap.tolist(),
            "constrained_gap": gap.tolist(),
            "dual_physical": dual.tolist(),
            "tip_section_mean_displacement_m": tip_mean.tolist(),
            "applied_load_work_J": load_work,
            "tip_work_conjugate_displacement": (
                load_work/(100. if label == "tip_mx" else 1000.)),
            "plate_interface_wrench_N_Nm": _wrench(coords, plate_action).tolist(),
            "bar_interface_wrench_N_Nm": _wrench(coords, bar_action).tolist(),
            "plate_interface_work_J": plate_work,
            "bar_interface_work_J": bar_work,
            "global_external_support_balance": balance.tolist(),
            "joint_global_wrench": joint_wrench.tolist(),
            "algebraic_gap_defect": float(np.linalg.norm(
                compliance@coefficient-initial_gap)),
            "global_six_load_work_J": reference["cases"][label]["applied_load_work_J"],
        }
    return {
        "classification": "matched detached-solid linear exact 12-row split-KKT reconstruction; development only",
        "status": "EXPLORATORY_COMPLETE", "source_root": str(source_root),
        "response_root": str(response_root), "unit_records": unit_records,
        "unit_source_commit": run_identity[0],
        "unit_runner_sha256": run_identity[1],
        "global_six_reference_sha256": run_identity[2],
        "common_stiffness_sha256": common_stiffness,
        "preflight": audit,
        "work_compliance_relative_skew": skew,
        "work_compliance_eigenvalues_J": eigen.tolist(),
        "work_compliance_condition": float(np.linalg.cond(work_compliance)),
        "cases": cases,
        "source_sha256": digest(Path(__file__)),
        "limitations": ["linear detached solid with no contact",
                        "two exact half-patch mean laws; not a selected native multiplier space",
                        "one grid, no physical fidelity or F03/G0B acceptance"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--responses", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve previous split reconstruction")
    report = evaluate(args.source_root.resolve(), args.responses.resolve())
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True,
                                      allow_nan=False)+"\n")
    print(json.dumps({"status": report["status"],
                      "relative_skew": report["work_compliance_relative_skew"],
                      "min_work_eigenvalue_J": report["work_compliance_eigenvalues_J"][0],
                      "cases": {key: {"gap_norm": float(np.linalg.norm(value["constrained_gap"])),
                                      "balance_norm": float(np.linalg.norm(value["global_external_support_balance"])),
                                      "load_work_J": value["applied_load_work_J"]}
                                for key, value in report["cases"].items()}},
                     sort_keys=True))


if __name__ == "__main__":
    main()
