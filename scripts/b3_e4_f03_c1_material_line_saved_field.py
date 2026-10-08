"""Read-only material-line pose on the saved, differently tied F4 solid.

This distinguishes the six-channel area-mean law solved in F4 from the
candidate local material-line law. It does not create a matched reference.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from scripts.b3_e4_f03_c1_material_line_solid_port import build_flat_solid_line_port
from scripts.b3_e4_f03_c1_solid_trace_residual import (
    EVIDENCE, RECON, SCALES, SOURCE, _bound_field,
)
from scripts.b3_e4_f03_ccx_six_channel_compliance import _source
from scripts.b3_e4_f03_ccx_six_channel_preflight import _element_domain_nodes
from scripts.b3_e4_f03_ccx_solid_bond_screen import digest


def evaluate() -> dict:
    reconstruction = json.loads(RECON.read_text())
    if reconstruction["status"] != "EXPLORATORY_COMPLETE":
        raise ValueError("completed pinned F4 reconstruction required")
    deck, _, coords, rows, _, _ = _source(SOURCE / "tip_mx")
    if digest(deck) != reconstruction["cases"]["tip_mx"]["source_deck_sha256"]:
        raise ValueError("saved F4 source deck changed")
    plate, bar = _element_domain_nodes(deck)
    ports = tuple(build_flat_solid_line_port(coords, plate, bar, x)
                  for x in (.9125, .9375, .9875))
    required = set().union(*(port.node_ids for port in ports))
    required.update(node for row in rows for node, _ in row)
    units = [_bound_field(EVIDENCE / f"channel-{i}",
                          reconstruction["unit_records"][i]["frd_sha256"])
             for i in range(6)]
    if any(not required <= set(field) for field in units):
        raise ValueError("incomplete saved unit field")

    cases = {}
    for label in ("tip_mx", "tip_fz"):
        source_decks = list((SOURCE / label).glob("*.inp"))
        record = reconstruction["cases"][label]
        if len(source_decks) != 1 or digest(source_decks[0]) != record["source_deck_sha256"]:
            raise ValueError("saved F4 load deck changed")
        base = _bound_field(SOURCE / label, record["source_frd_sha256"])
        if not required <= set(base):
            raise ValueError("incomplete saved loaded field")
        multiplier = np.asarray(record["dual_physical"], dtype=float) / SCALES
        state = {node: base[node] - sum(multiplier[i]*units[i][node]
                                        for i in range(6))
                 for node in required}
        old_gap = np.array([sum(value*state[node][axis]
                                for (node, axis), value in row.items())
                            for row in rows])
        if np.max(np.abs(old_gap)) > 1e-10:
            raise ArithmeticError("saved F4 six-channel area-mean gap changed")
        stations = []
        for port in ports:
            shell_position = port.shell_top_jacobian @ np.array(
                [state[node] for node in port.node_ids]).ravel()
            shell_rotation = port.shell_orientation_jacobian @ np.array(
                [state[node] for node in port.node_ids]).ravel()
            beam_position = port.beam_bottom_jacobian @ np.array(
                [state[node] for node in port.node_ids]).ravel()
            beam_rotation = port.beam_orientation_jacobian @ np.array(
                [state[node] for node in port.node_ids]).ravel()
            gap = port.gap(state)
            np.testing.assert_allclose(gap, np.r_[shell_position-beam_position,
                                                   beam_rotation-shell_rotation],
                                       rtol=1e-11, atol=1e-12)
            stations.append({
                "x_m": port.station_x_m,
                "shell_top_translation_m": shell_position.tolist(),
                "shell_orientation_rad": shell_rotation.tolist(),
                "beam_bottom_translation_m": beam_position.tolist(),
                "beam_orientation_rad": beam_rotation.tolist(),
                "material_line_gap": gap.tolist(),
            })
        cases[label] = {
            "old_six_channel_area_mean_gap": old_gap.tolist(),
            "stations": stations,
        }
    return {
        "status": "DEVELOPMENT_DIAGNOSTIC_COMPLETE",
        "classification": "saved F4 solid response under a different exact six-channel area-mean tie",
        "source_deck_sha256": digest(deck),
        "reference_reconstruction_sha256": digest(RECON),
        "cases": cases,
        "limitations": [
            "old F4 area-mean solution is not an external solve of the candidate material-line law",
            "these gaps do not allocate native/solid accuracy or select a multiplier space",
            "flat small-motion pose and three interior stations only",
            "not F03 or G0B acceptance",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve prior diagnostic")
    result = evaluate()
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True,
                                      allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "output": str(args.output)}))


if __name__ == "__main__":
    main()
