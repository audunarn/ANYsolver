"""Resolve solid interface work outside local E4/B3 section kinematics.

Use the already reconstructed supported solid displacement. The plate
comparison enforces one through-thickness director at each material (x,y)
site; the bar comparison fits one rigid cross-section motion at each x.
These are local kinematic diagnostics, not a projection onto a globally
compatible E4/B3 finite-element space and not a formulation acceptance.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path

import numpy as np

from scripts.b3_e4_f03_ccx_six_channel_compliance import _source
from scripts.b3_e4_f03_ccx_six_channel_preflight import _element_domain_nodes
from scripts.b3_e4_f03_ccx_solid_bond_screen import digest
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_frd_u


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / ".qualification/b3-ge-e4-pl"
SOURCE = BASE / "f03-c1-detached-port-dev-20260926-v2"
EVIDENCE = BASE / "f03-c1-six-channel-compliance-dev-20260927-v1"
RECON = EVIDENCE / "reconstruction_v5.json"
SCALES = np.array((1000., 1000., 1000., 100., 100., 100.))


def _bound_field(folder: Path, expected_sha256: str) -> dict[int, np.ndarray]:
    frds = list(folder.glob("*.frd"))
    if len(frds) != 1 or digest(frds[0]) != expected_sha256:
        raise ValueError("saved solid displacement identity changed")
    return _read_frd_u(frds[0])


def _plate_director_fit(coords, displacement, plate_nodes, action_nodes):
    by_site = defaultdict(dict)
    for node in plate_nodes:
        x, y, z = coords[node]
        if .9-1e-10 <= x <= 1.+1e-10 and abs(y) <= .05+1e-10 and (
                abs(abs(z)-.0175) < 1e-10):
            key = (round(float(x), 9), round(float(y), 9))
            side = "top" if z > 0 else "bottom"
            if side in by_site[key]:
                raise ValueError("ambiguous plate director surface site")
            by_site[key][side] = node
    fitted = {}
    for pair in by_site.values():
        if set(pair) != {"top", "bottom"}:
            raise ValueError("incomplete plate through-thickness pair")
        top, bottom = pair["top"], pair["bottom"]
        u_top, u_bottom = displacement[top], displacement[bottom]
        middle = (u_top + u_bottom) / 2
        fitted[top] = np.array((u_top[0], u_top[1], middle[2]))
        fitted[bottom] = np.array((u_bottom[0], u_bottom[1], middle[2]))
    if not action_nodes <= set(fitted):
        raise ValueError("plate action has no director-fit trace")
    return fitted, len(by_site)


def _bar_section_fit(coords, displacement, bar_nodes, action_nodes):
    action_x = {round(float(coords[node][0]), 9) for node in action_nodes}
    by_station = defaultdict(list)
    for node in bar_nodes:
        x = round(float(coords[node][0]), 9)
        if x in action_x:
            by_station[x].append(node)
    if set(by_station) != action_x:
        raise ValueError("bar action station inventory is incomplete")
    fitted = {}
    station_rms = {}
    for x, nodes in by_station.items():
        center = np.array((x, 0., .0675))
        design = np.zeros((3*len(nodes), 6))
        observed = np.array([displacement[node] for node in nodes]).ravel()
        for index, node in enumerate(nodes):
            _, y, z = coords[node]-center
            design[3*index:3*index+3, :3] = np.eye(3)
            design[3*index:3*index+3, 3:] = (
                (0., z, -y), (-z, 0., 0.), (y, 0., 0.))
        if np.linalg.matrix_rank(design) != 6:
            raise ValueError("bar cross-section fit is rank deficient")
        six, *_ = np.linalg.lstsq(design, observed, rcond=None)
        prediction = (design@six).reshape(-1, 3)
        station_rms[str(x)] = float(np.sqrt(np.mean(np.sum(
            (prediction-observed.reshape(-1, 3))**2, axis=1))))
        fitted.update(zip(nodes, prediction))
    if not action_nodes <= set(fitted):
        raise ValueError("bar action has no rigid-section-fit trace")
    return fitted, station_rms


def _side_work(forces, field):
    return float(sum(force@field[node] for node, force in forces.items()))


def evaluate() -> dict:
    recon = json.loads(RECON.read_text())
    if recon["status"] != "EXPLORATORY_COMPLETE":
        raise ValueError("complete six-channel external reconstruction required")
    deck, _, coords, rows, _, _ = _source(SOURCE / "tip_mx")
    plate_nodes, bar_nodes = _element_domain_nodes(deck)
    unit = [_bound_field(EVIDENCE / f"channel-{j}",
                         recon["unit_records"][j]["frd_sha256"])
            for j in range(6)]
    if any(set(field) != set(coords) for field in unit):
        raise ValueError("saved unit-action fields changed")
    records = {}
    for label in ("tip_mx", "tip_fz"):
        source_decks = list((SOURCE / label).glob("*.inp"))
        if (len(source_decks) != 1 or digest(source_decks[0]) !=
                recon["cases"][label]["source_deck_sha256"]):
            raise ValueError("saved solid source deck identity changed")
        base = _bound_field(
            SOURCE / label, recon["cases"][label]["source_frd_sha256"])
        if set(base) != set(coords):
            raise ValueError("saved loaded field changed")
        dual = np.asarray(recon["cases"][label]["dual_physical"])
        multiplier = dual/SCALES
        state = {node: base[node] - sum(multiplier[j]*unit[j][node]
                                        for j in range(6))
                 for node in coords}
        forces = defaultdict(lambda: np.zeros(3))
        for j, row in enumerate(rows):
            for (node, axis), value in row.items():
                forces[node][axis] -= dual[j]*value
        plate_force = {node: force for node, force in forces.items()
                       if node in plate_nodes}
        bar_force = {node: force for node, force in forces.items()
                     if node in bar_nodes}
        if len(plate_force)+len(bar_force) != len(forces):
            raise ValueError("unowned interface action node")
        plate_fit, plate_sites = _plate_director_fit(
            coords, state, plate_nodes, set(plate_force))
        bar_fit, station_rms = _bar_section_fit(
            coords, state, bar_nodes, set(bar_force))
        plate_actual = _side_work(plate_force, state)
        bar_actual = _side_work(bar_force, state)
        plate_representable = _side_work(plate_force, plate_fit)
        bar_representable = _side_work(bar_force, bar_fit)
        local_fit = {**plate_fit, **bar_fit}
        fitted_gap = np.array([
            sum(value * local_fit[node][axis]
                for (node, axis), value in row.items()) for row in rows])
        physical_gap = np.array([
            sum(value * state[node][axis]
                for (node, axis), value in row.items()) for row in rows])
        if np.linalg.norm(physical_gap) > 1e-10:
            raise ArithmeticError("saved exact solid joint gap changed")
        outside_work = (plate_actual-plate_representable +
                        bar_actual-bar_representable)
        np.testing.assert_allclose(outside_work, dual@fitted_gap,
                                   rtol=2e-9, atol=1e-10)
        np.testing.assert_allclose(
            [plate_actual, bar_actual],
            [recon["cases"][label]["plate_interface_work_J"],
             recon["cases"][label]["bar_interface_work_J"]],
            rtol=2e-12, atol=1e-12)
        records[label] = {
            "plate_director_site_count": plate_sites,
            "bar_station_count": len(station_rms),
            "bar_station_rms_warp_m": station_rms,
            "plate_actual_interface_work_J": plate_actual,
            "plate_local_director_fit_work_J": plate_representable,
            "plate_outside_director_work_J": plate_actual-plate_representable,
            "bar_actual_interface_work_J": bar_actual,
            "bar_local_rigid_section_fit_work_J": bar_representable,
            "bar_outside_rigid_section_work_J": bar_actual-bar_representable,
            "actual_six_channel_gap": physical_gap.tolist(),
            "local_section_fit_six_channel_gap": fitted_gap.tolist(),
            "outside_section_work_identity_defect_J": float(
                outside_work-dual@fitted_gap),
        }
    return {
        "classification": "supported solid interface local trace-residual work; development diagnostic only",
        "status": "EXPLORATORY_COMPLETE", "cases": records,
        "inputs_sha256": {str(path): digest(path) for path in (RECON,)},
        "source_sha256": digest(Path(__file__)),
        "limitations": ["pointwise local fits do not impose globally compatible E4/B3 fields",
                        "work residuals do not alone attribute the same-action difference to the connection law",
                        "one linear no-contact solid mesh; no F03/G0B acceptance"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve previous trace-residual result")
    report = evaluate()
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True,
                                      allow_nan=False) + "\n")
    print(json.dumps({"status": report["status"],
                      "work_residuals_J": {key: [
                          value["plate_outside_director_work_J"],
                          value["bar_outside_rigid_section_work_J"]]
                          for key, value in report["cases"].items()}},
                     sort_keys=True))


if __name__ == "__main__":
    main()
