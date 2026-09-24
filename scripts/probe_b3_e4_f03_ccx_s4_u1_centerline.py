"""Bounded S4/B31 or S4/U1 centerline execution probe, not F03 acceptance.

The geometry, end supports, center material line and declared loads match
the native diagnostic. The executable S4/B31 route uses a different beam
torsion/shear section, a different shell and nodal collocation. Its beam
rotation output has not been validated. These differences prevent a matched
F03 reference claim even when an exploratory displacement is parsed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

import numpy as np

from scripts.probe_b3_ge_e4_pl_g0_f03_ccx_u1_smoke import EXPECTED_EXE_SHA256
from scripts._b3_e4_f03_shell_trace import make_shell


def _number(value: float) -> str:
    return f"{value:.17g}"


def _pose_rows(panel, station: float, beam_node: int):
    center_ids, center_weights = panel._shape(station, 0.)
    sample_weights = panel.sample_weights(station)
    mean = sample_weights.mean(axis=0)
    yaw = panel.trace(station)[2]
    rows = []
    for component in range(1, 4):
        rows.append([(beam_node, component, 1.)] +
                    [(int(node)+1, component, -float(weight))
                     for node, weight in zip(center_ids, center_weights)
                     if abs(weight) > 1e-14])
    for component in (4, 5):
        rows.append([(beam_node, component, 1.)] +
                    [(node+1, component, -float(weight))
                     for node, weight in enumerate(mean) if abs(weight) > 1e-14])
    yaw_row = [(beam_node, 6, 1.)]
    for node in range(panel.node_count):
        for component in (1, 2):
            weight = float(yaw[2*node+component-1])
            if abs(weight) > 1e-14:
                yaw_row.append((node+1, component, -weight))
    rows.append(yaw_row)
    return rows


def deck(n_s: int, n_y: int, n_beam: int, load_kind: str,
         beam_type: str = "B31"):
    if (n_s not in (2, 4, 8) or n_y not in (2, 4, 8) or
            n_beam not in (4, 8, 16, 32) or
            load_kind not in ("torsion", "transverse_force_z",
                              "shell_force_couple_x") or
            beam_type not in ("B31", "U1")):
        raise ValueError("bounded centerline comparison inventory required")
    panel = make_shell(n_s, "Q4", n_y=n_y)
    nx = 2*n_s
    shell_nodes = panel.node_count
    beam_first = shell_nodes+1
    tip = beam_first+n_beam
    monitor = tip+1
    lines = ["** Exploratory S4/U1 centerline collocation; not F03 qualification",
             "*NODE,NSET=AllNodes"]
    for j, y in enumerate(np.linspace(-.5, .5, n_y+1)):
        for i, x in enumerate(np.linspace(-.5, 1.5, nx+1)):
            lines.append(f"{1+j*(nx+1)+i},{_number(x)},{_number(y)},0")
    for i in range(n_beam+1):
        lines.append(f"{beam_first+i},{_number(i/n_beam)},0,0")
    lines.append(f"{monitor},1,0,0")
    lines.append("*ELEMENT,TYPE=S4,ELSET=Panel")
    eid = 0
    for j in range(n_y):
        for i in range(nx):
            a = 1+j*(nx+1)+i
            eid += 1
            lines.append(f"{eid},{a},{a+1},{a+nx+2},{a+nx+1}")
    lines.append(f"*ELEMENT,TYPE={beam_type},ELSET=Beam")
    for i in range(n_beam):
        eid += 1
        lines.append(f"{eid},{beam_first+i},{beam_first+i+1}")
    if beam_type == "U1":
        lines.append("*USER ELEMENT,TYPE=U1,NODES=2,INTEGRATION POINTS=2,MAXDOF=6")
    lines += ["*NSET,NSET=PanelLeft",
              ",".join(str(1+j*(nx+1)) for j in range(n_y+1)),
              "*NSET,NSET=TipAndMonitor", f"{tip},{monitor}",
              "*BOUNDARY", "PanelLeft,1,6", f"{beam_first},1,6",
              f"{monitor},1,2", f"{monitor},4,6",
              "*MATERIAL,NAME=Steel", "*ELASTIC", "210.e9,.3",
              "*SHELL SECTION,ELSET=Panel,MATERIAL=Steel", ".07"]
    if beam_type == "U1":
        lines += ["*BEAM SECTION,ELSET=Beam,MATERIAL=Steel,SECTION=GENERAL",
                  ".01,8.333333333333333e-6,0.,8.333333333333333e-6,.8"]
    else:
        lines += ["*BEAM SECTION,ELSET=Beam,MATERIAL=Steel,SECTION=RECT",
                  ".1,.1"]
    lines.append("0.,1.,0.")
    rows = []
    dependent_shell_rx = set()
    for i in range(1, n_beam+1):
        station_rows = _pose_rows(panel, i/n_beam, beam_first+i)
        # Keep beam rx independent so a physical tip torque can be loaded.
        # Equation pivoting does not change the six-channel connection law.
        candidates = sorted(station_rows[3][1:], key=lambda term: -abs(term[2]))
        pivot = next((term for term in candidates
                      if term[0] not in dependent_shell_rx and
                      (term[0]-1) % (nx+1) != 0), None)
        if pivot is None:
            raise ValueError("no distinct free shell-rx equation pivot")
        dependent_shell_rx.add(pivot[0])
        station_rows[3] = [(pivot[0], 4, 1.)] + [
            (node, dof, coefficient/pivot[2])
            for node, dof, coefficient in station_rows[3] if node != pivot[0]]
        rows.extend(station_rows)
    # A massless, unloaded output coordinate reads tip twist from the same
    # four-sample physical director trace. Its equation is not a connection.
    monitor_lever_m = .1
    monitor_row = [(monitor, 3, 1.), (tip, 4, -monitor_lever_m)]
    rows.append(monitor_row)
    for row in rows:
        lines += ["*EQUATION", str(len(row))]
        for start in range(0, len(row), 4):
            lines.append(",".join(f"{node},{dof},{_number(coefficient)}"
                                  for node, dof, coefficient in row[start:start+4]))
    # Beam rx is independent after equation pivoting. Beam z remains a
    # dependent coordinate, so its force uses the shell-trace pullback.
    tip_rows = _pose_rows(panel, 1., tip)
    if load_kind == "torsion":
        load_terms = [(tip, 4, 100.)]
        load_application = "independent_beam_tip_rx"
    elif load_kind == "shell_force_couple_x":
        y = np.array([-.23, -.23, .23, .23])
        nodal_load = 100.*(y/(y@y))@panel.sample_weights(1.)
        load_terms = [(node+1, 3, float(force))
                      for node, force in enumerate(nodal_load)
                      if abs(force) > 1e-12]
        load_application = "four_sample_shell_transverse_force_couple"
    else:
        row = tip_rows[2]
        load_terms = [(node, dof, -1000.*coefficient)
                      for node, dof, coefficient in row[1:]]
        load_application = "independent_shell_tip_trace_transpose"
    lines += ["*STEP", "*STATIC", "*CLOAD"]
    lines += [f"{node},{dof},{_number(load)}" for node, dof, load in load_terms]
    lines += ["*NODE PRINT,NSET=AllNodes", "U", "*END STEP"]
    metadata = {"shell_type": "S4", "beam_type": beam_type, "n_s": n_s,
                "n_y": n_y, "n_beam": n_beam,
                "shell_elements": nx*n_y, "beam_elements": n_beam,
                "connection_equations": 6*n_beam,
                "monitor_equations": 1,
                "equations": len(rows), "shell_thickness_m": .07,
                "beam_area_m2": .01, "beam_shear_area_m2": .008,
                "beam_Iy_Iz_m4": 8.333333333333333e-6,
                "beam_section": ("generalized" if beam_type == "U1" else "rectangular"),
                "native_torsion_and_shear_match": beam_type == "U1",
                "beam_root_fixed": True, "shell_left_edge_fixed": True,
                "center_position": True, "four_sample_director_tilts": True,
                "four_sample_physical_yaw": True,
                "enforcement": "six_channel_nodal_collocation",
                "load_kind": load_kind,
                "load_application": load_application,
                "load_terms": len(load_terms), "tip_node": tip,
                "monitor_node": monitor, "monitor_lever_m": monitor_lever_m}
    return "\n".join(lines)+"\n", metadata, rows


def parse_displacement(content: str, node_id: int):
    blocks = re.findall(r"displacements .*? for set ALLNODES .*?\n(.*?)(?:\n\s*\n|$)",
                        content, re.IGNORECASE | re.DOTALL)
    for block in reversed(blocks):
        for line in block.splitlines():
            fields = line.split()
            if len(fields) in (4, 7) and fields[0] == str(node_id):
                return [float(field.replace("D", "E")) for field in fields[1:]]
    raise ValueError(f"node {node_id} displacement was not parsed")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable", required=True, type=Path)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--n-shell", type=int, required=True)
    parser.add_argument("--n-y", type=int, required=True)
    parser.add_argument("--n-beam", type=int, required=True)
    parser.add_argument("--load", required=True,
                        choices=("torsion", "transverse_force_z",
                                 "shell_force_couple_x"))
    parser.add_argument("--beam-type", choices=("B31", "U1"), default="B31")
    args = parser.parse_args()
    exe = args.executable.resolve(strict=True)
    exe_hash = hashlib.sha256(exe.read_bytes()).hexdigest()
    if exe_hash != EXPECTED_EXE_SHA256:
        raise ValueError("CalculiX executable identity mismatch")
    content, model, rows = deck(args.n_shell, args.n_y, args.n_beam,
                                args.load, args.beam_type)
    # The dependent beam DOF is unique in every equation, and rigid-body
    # translations/rotations must satisfy the shell trace used in the deck.
    dependent = [(row[0][0], row[0][1]) for row in rows]
    if len(dependent) != len(set(dependent)):
        raise AssertionError("repeated dependent beam coordinate")
    args.root.mkdir(parents=True, exist_ok=False)
    (args.root/"centerline.inp").write_text(content, encoding="ascii")
    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = "1"
    try:
        run = subprocess.run([str(exe), "-i", "centerline"], cwd=args.root,
                             env=env, capture_output=True, text=True,
                             timeout=120, check=False)
        (args.root/"stdout.log").write_text(run.stdout, encoding="utf-8")
        (args.root/"stderr.log").write_text(run.stderr, encoding="utf-8")
        status = {"exit_code": run.returncode, "failure": None}
    except subprocess.TimeoutExpired as exc:
        (args.root/"stdout.log").write_bytes(exc.stdout or b"")
        (args.root/"stderr.log").write_bytes(exc.stderr or b"")
        status = {"exit_code": None, "failure": "TIMEOUT_120_SECONDS"}
    dat = args.root/"centerline.dat"
    if status["exit_code"] == 0:
        try:
            output = dat.read_text(encoding="ascii", errors="replace")
            status["tip_displacement"] = parse_displacement(output, model["tip_node"])
            status["monitor_displacement"] = parse_displacement(
                output, model["monitor_node"])
            status["unverified_rx_monitor_proxy_rad"] = (
                status["monitor_displacement"][2]/model["monitor_lever_m"])
            status["beam_rx_monitor_validated"] = False
            panel = make_shell(model["n_s"], "Q4", n_y=model["n_y"])
            weights = panel.sample_weights(1.)
            used = np.flatnonzero(np.any(weights != 0., axis=0))
            nodal_z = np.zeros(panel.node_count)
            for node in used:
                nodal_z[node] = parse_displacement(output, int(node)+1)[2]
            sample_z = weights@nodal_z
            y = np.array([-.23, -.23, .23, .23])
            status["shell_tip_z_antisymmetric_slope_rad"] = float(
                y@sample_z/(y@y))
            if (args.load == "torsion" and
                    abs(status["unverified_rx_monitor_proxy_rad"]) < 1e-15):
                status["failure"] = "ZERO_TORQUE_RESPONSE_ON_THIS_CCX_ROUTE"
        except (OSError, ValueError) as exc:
            status["failure"] = f"TIP_PARSE_FAILED: {exc}"
    record = {"purpose": "UNREGISTERED_PARTIAL_IDEALIZATION_COLLLOCATION_DIAGNOSTIC",
              "not_exact_weak_line": True, "not_native_e4_shell": True,
              "executable_sha256": exe_hash,
              "deck_sha256": hashlib.sha256(content.encode("ascii")).hexdigest(),
              "model": model, **status,
              "files": sorted(path.name for path in args.root.iterdir())}
    (args.root/"result.json").write_text(json.dumps(record, sort_keys=True, indent=2)+"\n",
                                         encoding="utf-8")
    print(json.dumps(record, sort_keys=True))
    return 0 if status["exit_code"] == 0 and not status["failure"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
