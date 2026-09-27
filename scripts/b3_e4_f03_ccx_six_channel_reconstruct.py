"""Reconstruct an exact linear six-constraint solid response from unit actions.

For the same supported linear solid, U_j = K^-1 C_j^T s_j and
G_ij = C_i U_j. Solving G mu = C U_0 gives U = U_0 - sum_j mu_j U_j.
This is algebraically the exact KKT response of the declared six-row solid
work law, without a broad MPC passed to CalculiX. It is still a development
reference, not a nonlinear/contact or G0 qualification result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from scripts.b3_e4_f03_ccx_six_channel_compliance import (
    ACTION_SCALES, _source,
)
from scripts.b3_e4_f03_ccx_six_channel_preflight import _element_domain_nodes
from scripts.b3_e4_f03_ccx_solid_bond_screen import (
    EXE_SHA, digest, parse_nodal_vectors,
)
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_frd_u


def _gaps(rows, displacement):
    return np.array([sum(value * displacement[node][axis]
                         for (node, axis), value in row.items())
                     for row in rows])


def _wrench(coords, forces):
    force = sum((np.asarray(value) for value in forces.values()), np.zeros(3))
    moment = sum((np.cross(coords[node], value)
                  for node, value in forces.items()), np.zeros(3))
    return np.r_[force, moment]


def _support_reactions(folder, stem, meta):
    data = (folder / f"{stem}.dat").read_text()
    return parse_nodal_vectors(data, set(meta["boundary_node_ids"]),
                               "forces", meta["support_set"])


def _same_stiffness_deck(torque_deck: Path, opening_deck: Path) -> str:
    """Bind geometry, connectivity, material, supports and static controls."""
    torque = torque_deck.read_text().splitlines()
    opening = opening_deck.read_text().splitlines()
    geometry_t = torque[2:torque.index("*MATERIAL,NAME=Isotropic")]
    geometry_o = opening[2:opening.index("*NSET,NSET=UnbondedInterface")]
    material_t = torque[torque.index("*MATERIAL,NAME=Isotropic"):
                        torque.index("*NSET,NSET=Probe")]
    material_o = opening[opening.index("*MATERIAL,NAME=Isotropic"):
                          opening.index("*NSET,NSET=Probe")]
    static_t = torque[torque.index("*BOUNDARY"):torque.index("*CLOAD")]
    static_o = opening[opening.index("*BOUNDARY"):opening.index("*CLOAD")]
    if (geometry_t != geometry_o or material_t != material_o or
            static_t != static_o):
        raise ValueError("source load cases do not share a stiffness operator")
    return hashlib.sha256("\n".join((*geometry_t, *material_t,
                                      *static_t)).encode()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--responses", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source_root = args.source_root.resolve()
    response_root = args.responses.resolve()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError("preserve previous six-channel reconstruction")
    tip_mx = source_root / "tip_mx"
    deck, meta, coords, rows, geometry, preflight = _source(tip_mx)
    plate_nodes, bar_nodes = _element_domain_nodes(deck)
    source_deck_hash = digest(deck)
    source_model_hash = digest(tip_mx / "model.json")
    unit, records = [], []
    unit_source_commit = None
    for channel in range(6):
        folder = response_root / f"channel-{channel}"
        path = folder / "result.json"
        record = json.loads(path.read_text())
        if (record["status"] != "EXPLORATORY_COMPLETE" or
                record["channel"] != channel or
                record["applied_dual_scale"] != ACTION_SCALES[channel] or
                record["source_deck_sha256"] != source_deck_hash or
                record["source_model_sha256"] != source_model_hash or
                record["solver_sha256"] != EXE_SHA or
                record["generated_deck_sha256"] !=
                digest(folder / f"six-channel-{channel}.inp") or
                not record["source_commit"]):
            raise ValueError("unit-action identity or completion changed")
        if unit_source_commit is None:
            unit_source_commit = record["source_commit"]
        elif unit_source_commit != record["source_commit"]:
            raise ValueError("unit-action source commits differ")
        displacement = _read_frd_u(folder / f"six-channel-{channel}.frd")
        if set(displacement) != set(coords):
            raise ValueError("incomplete unit-action displacement")
        recalculated = _gaps(rows, displacement)
        np.testing.assert_allclose(recalculated, record["gap_response"],
                                   rtol=2e-12, atol=5e-15)
        unit.append(displacement)
        records.append({"channel": channel, "result_sha256": digest(path),
                        "frd_sha256": digest(folder / f"six-channel-{channel}.frd")})
    scale = np.array(ACTION_SCALES)
    G = np.array([_gaps(rows, u) for u in unit]).T
    work_compliance = scale[:, None] * G
    skew = float(np.linalg.norm(work_compliance-work_compliance.T) /
                 np.linalg.norm(work_compliance))
    eigen = np.linalg.eigvalsh((work_compliance+work_compliance.T)/2)
    if skew > 1e-6 or eigen[0] <= 0 or not np.isfinite(G).all():
        raise ArithmeticError("external six-channel compliance fails work/positivity")
    cases = {}
    common_stiffness_sha256 = None
    for label in ("tip_mx", "tip_fz"):
        folder = source_root / label
        source_meta = json.loads((folder / "model.json").read_text())
        if (source_meta["node_count"] != meta["node_count"] or
                source_meta["bond_policy"] != "detached" or
                source_meta["bar_reference_profile"] !=
                meta["bar_reference_profile"]):
            raise ValueError("baseline case has a different solid model")
        source_decks = list(folder.glob("*.inp"))
        source_frds = list(folder.glob("*.frd"))
        if len(source_decks) != 1 or len(source_frds) != 1:
            raise ValueError("one complete source case required")
        if label == "tip_fz":
            common_stiffness_sha256 = _same_stiffness_deck(
                deck, source_decks[0])
        from scripts.b3_e4_f03_solid_bond_pose_projection import _read_deck_nodes
        other_coords = _read_deck_nodes(source_decks[0])
        if set(other_coords) != set(coords) or any(
                not np.array_equal(other_coords[node], coords[node])
                for node in coords):
            raise ValueError("baseline case geometry/numbering differs")
        base = _read_frd_u(source_frds[0])
        if set(base) != set(coords):
            raise ValueError("incomplete source displacement")
        initial_gap = _gaps(rows, base)
        coefficient = np.linalg.solve(G, initial_gap)
        constrained = {node: base[node] - sum(
            coefficient[j] * unit[j][node] for j in range(6))
                       for node in coords}
        final_gap = _gaps(rows, constrained)
        if np.linalg.norm(scale * final_gap) > 1e-8:
            raise ArithmeticError("reconstructed solid does not satisfy constraints")
        source_stem = source_decks[0].stem
        support_base = _support_reactions(folder, source_stem, source_meta)
        support_unit = [_support_reactions(
            response_root / f"channel-{j}", f"six-channel-{j}", meta)
            for j in range(6)]
        support = {node: support_base[node] - sum(
            coefficient[j] * support_unit[j][node] for j in range(6))
                   for node in support_base}
        applied = {int(node): np.asarray(value, dtype=float)
                   for node, value in source_meta["applied_nodal_forces_N"].items()}
        balance = _wrench(coords, support) + _wrench(coords, applied)
        # The KKT body force is -C^T lambda for C u = 0. Its two
        # physical sides carry opposite total spatial wrenches.
        dual = scale * coefficient
        line_forces = {}
        for j, row in enumerate(rows):
            for (node, axis), value in row.items():
                line_forces.setdefault(node, np.zeros(3))[axis] -= dual[j]*value
        interface_wrench = _wrench(coords, line_forces)
        if np.linalg.norm(interface_wrench) > 1e-7:
            raise ArithmeticError("joint action has a nonzero global wrench")
        plate_action = {node: value for node, value in line_forces.items()
                        if node in plate_nodes}
        bar_action = {node: value for node, value in line_forces.items()
                      if node in bar_nodes}
        if len(plate_action) + len(bar_action) != len(line_forces):
            raise ArithmeticError("joint action has unowned solid nodes")
        plate_work = float(sum(force @ constrained[node]
                               for node, force in plate_action.items()))
        bar_work = float(sum(force @ constrained[node]
                             for node, force in bar_action.items()))
        applied_work = float(sum(force @ constrained[node]
                                 for node, force in applied.items()))
        if abs(plate_work + bar_work) > 1e-8:
            raise ArithmeticError("solid-side joint work does not cancel")
        tip_nodes = [int(node) for node in source_meta["bar_station_nodes"]["1000"]]
        tip_mean = np.mean([constrained[node] for node in tip_nodes], axis=0)
        cases[label] = {
            "source_deck_sha256": digest(source_decks[0]),
            "source_model_sha256": digest(folder / "model.json"),
            "source_frd_sha256": digest(source_frds[0]),
            "unconstrained_gap": initial_gap.tolist(),
            "constrained_gap": final_gap.tolist(),
            "dual_physical": dual.tolist(),
            "tip_section_mean_displacement_m": tip_mean.tolist(),
            "applied_load_work_J": applied_work,
            "tip_work_conjugate_displacement": (
                applied_work / (100. if label == "tip_mx" else 1000.)),
            "plate_interface_wrench_N_Nm": _wrench(coords, plate_action).tolist(),
            "bar_interface_wrench_N_Nm": _wrench(coords, bar_action).tolist(),
            "plate_interface_work_J": plate_work,
            "bar_interface_work_J": bar_work,
            "global_external_support_balance": balance.tolist(),
            "joint_global_wrench": interface_wrench.tolist(),
            "algebraic_gap_defect": float(np.linalg.norm(G@coefficient-initial_gap)),
        }
    report = {
        "classification": "matched detached-solid linear six-channel exact-KKT reconstruction; development evidence only",
        "status": "EXPLORATORY_COMPLETE", "source_root": str(source_root),
        "response_root": str(response_root), "unit_records": records,
        "unit_source_commit": unit_source_commit,
        "common_stiffness_sha256": common_stiffness_sha256,
        "geometry": geometry, "preflight": preflight,
        "work_compliance_relative_skew": skew,
        "work_compliance_eigenvalues_J": eigen.tolist(),
        "work_compliance_condition": float(np.linalg.cond(work_compliance)),
        "cases": cases,
        "limitations": ["linear detached solid model with no contact",
                        "linear face-mean position/moment and through-thickness pitch idealization",
                        "no native matching, mesh convergence or F03/G0B acceptance"],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True,
                                 allow_nan=False) + "\n")
    print(json.dumps({"status": report["status"],
                      "relative_skew": skew,
                      "minimum_work_eigenvalue_J": float(eigen[0]),
                      "cases": {key: {"gap_norm": float(np.linalg.norm(
                          value["constrained_gap"])),
                          "balance_norm": float(np.linalg.norm(
                          value["global_external_support_balance"]))}
                                for key, value in cases.items()}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
