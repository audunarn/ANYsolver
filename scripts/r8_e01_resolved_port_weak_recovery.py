"""Small-strain, element-side weak work for the inert E01 resolved-port deck.

Development diagnostic only. FRD displacements are rounded; reconstructed
element forces and section-print stresses need independent balance checks.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from scripts.b3_e4_f03_c3d20r_bond_force_recovery import element_forces
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_frd_u


def read_deck(path: Path) -> dict:
    """Read exactly the E01 two-domain, six-port C3D20R source contract."""
    nodes: dict[int, tuple[float, float, float]] = {}
    elements: dict[str, list[list[int]]] = {"Plate": [], "BeamSolid": []}
    sets: dict[str, set[int]] = {}
    ports: dict[str, tuple[int, int]] = {}
    loads: list[tuple[int, int, float]] = []
    section = None
    pending: list[int] = []
    name = None
    for raw in path.read_text(encoding="ascii").splitlines():
        line = raw.strip()
        if line.startswith("*"):
            if pending:
                raise ValueError("incomplete Q20 connectivity")
            head = line.upper()
            if head == "*NODE":
                section = "nodes"
            elif head.startswith("*ELEMENT,TYPE=C3D20R,ELSET="):
                section = head.split("ELSET=", 1)[1].title()
                if section == "Beamsolid":
                    section = "BeamSolid"
                if section not in elements:
                    raise ValueError("unexpected E01 element domain")
            elif head.startswith("*NSET,NSET="):
                name = line.split("NSET=", 1)[1]
                if name in sets:
                    raise ValueError("duplicate E01 node set")
                sets[name] = set()
                section = "set"
            elif head.startswith("*RIGID BODY,NSET="):
                fields = dict(part.strip().split("=", 1) for part in line.split(",")[1:])
                ports[fields["NSET"]] = (int(fields["REF NODE"]), int(fields["ROT NODE"]))
                section = None
            elif head == "*CLOAD":
                section = "load"
            else:
                section = None
            continue
        if not line or section is None:
            continue
        parts = [part.strip() for part in line.split(",") if part.strip()]
        if section == "nodes":
            number = int(parts[0])
            if number in nodes or len(parts) != 4:
                raise ValueError("invalid E01 node")
            nodes[number] = tuple(float(value) for value in parts[1:])
        elif section in elements:
            pending.extend(int(value) for value in parts)
            if len(pending) == 21:
                elements[section].append(pending[1:])
                pending = []
            elif len(pending) > 21:
                raise ValueError("invalid Q20 connectivity")
        elif section == "set":
            sets[name].update(int(value) for value in parts)
        elif section == "load":
            if len(parts) != 3:
                raise ValueError("E01 point load needs node, DOF, value")
            loads.append((int(parts[0]), int(parts[1]), float(parts[2])))
    if (len(elements["Plate"]), len(elements["BeamSolid"]), len(ports), len(loads)) != (120, 48, 6, 1):
        raise ValueError("incomplete E01 two-domain port inventory")
    if set(nodes) != set(range(1, max(nodes)+1)):
        raise ValueError("E01 node IDs must be contiguous")
    for side in ("Shell", "Beam"):
        for station in (0, 1000, 2000):
            name = f"{side}Port{station}"
            if name not in ports or name not in sets or not sets[name]:
                raise ValueError("missing E01 port")
    if "PlateRootFree" not in sets or sets["PlateRootFree"] & sets["ShellPort0"]:
        raise ValueError("root support overlaps rigid slave")
    return dict(x=np.array([[0., 0., 0.]]+[nodes[n] for n in range(1, len(nodes)+1)]),
                elements={name: np.asarray(cells, dtype=np.int32)
                          for name, cells in elements.items()},
                sets=sets, ports=ports, loads=loads)


def port_wrench(x: np.ndarray, f: np.ndarray, ids: set[int], ref: int) -> np.ndarray:
    """Internal nodal covectors pulled to a physical reference translation/rotation."""
    rows = np.array(sorted(ids), dtype=np.int32)
    arm = x[rows]-x[ref]
    return np.r_[f[rows].sum(axis=0), np.cross(arm, f[rows]).sum(axis=0)]


def rigid_fit(x: np.ndarray, u: np.ndarray, ids: set[int], ref: int) -> tuple[np.ndarray, float]:
    """Independent least-squares rigid displacement and maximum pointwise gap."""
    rows = np.array(sorted(ids), dtype=np.int32)
    arm = x[rows]-x[ref]
    design = np.zeros((3*len(rows), 6))
    for i, (rx, ry, rz) in enumerate(arm):
        design[3*i:3*i+3, :3] = np.eye(3)
        design[3*i:3*i+3, 3:] = ((0., rz, -ry), (-rz, 0., rx), (ry, -rx, 0.))
    if np.linalg.matrix_rank(design) != 6:
        raise ValueError("degenerate E01 rigid port")
    q = np.linalg.lstsq(design, u[rows].reshape(-1), rcond=None)[0]
    gap = float(np.max(np.abs(design@q-u[rows].reshape(-1))))
    return q, gap


def station_contract(model: dict, actions: dict, station: int) -> dict:
    """Physical six-row gap, signed port work and free-station wrench balance."""
    if station not in (0, 1000, 2000):
        raise ValueError("undeclared E01 station")
    shell = actions[f"ShellPort{station}"]
    beam = actions[f"BeamPort{station}"]
    shell_ref = model["ports"][f"ShellPort{station}"][0]
    beam_ref, beam_rot = model["ports"][f"BeamPort{station}"]
    arm = model["x"][beam_ref]-model["x"][shell_ref]
    ext_beam = np.zeros(6)
    for node, dof, value in model["loads"]:
        if node == beam_ref and dof <= 3:
            ext_beam[dof-1] += value
        elif node == beam_rot and dof <= 3:
            ext_beam[dof+2] += value
    sw, bw = np.asarray(shell["wrench"]), np.asarray(beam["wrench"])
    qs, qb = np.asarray(shell["fitted_pose"]), np.asarray(beam["fitted_pose"])
    ext_shell = ext_beam.copy()
    ext_shell[3:] += np.cross(arm, ext_beam[:3])
    balance = sw+bw+np.r_[np.zeros(3), np.cross(arm, bw[:3])]-ext_shell
    gap = np.r_[qb[:3]-qs[:3]-np.cross(qs[3:], arm), qb[3:]-qs[3:]]
    work = float(sw@qs+bw@qb-ext_beam@qb)
    return dict(status=("GROUNDED_PORT_DIAGNOSTIC" if station == 0 else
                        "FREE_PORT_BALANCE_DIAGNOSTIC"),
                gap_m_rad=gap.tolist(),
                residual_n_nm=balance.tolist(),
                signed_internal_minus_external_work_j=work,
                external_shell_reference_n_nm=ext_shell.tolist())


def recover_from_displacements(model: dict, vectors: dict[int, np.ndarray]) -> dict:
    """Reconstruct each constituent force and test coupled station work balance."""
    x = model["x"]
    physical = {int(n) for conn in model["elements"].values() for n in conn.ravel()}
    if not physical <= set(vectors) or any(not np.isfinite(vectors[n]).all() for n in physical):
        raise ValueError("complete finite physical-node displacement required")
    u = np.zeros_like(x)
    for node in physical:
        u[node] = vectors[node]
    fint = {}
    minimum_jacobian = float("inf")
    for name, conn in model["elements"].items():
        field = np.zeros_like(x)
        for start in range(0, len(conn), 64):
            ids = conn[start:start+64]
            f, det = element_forces(x[ids], u[ids])
            np.add.at(field, ids.ravel(), f.reshape(-1, 3))
            minimum_jacobian = min(minimum_jacobian, float(det.min()))
        fint[name] = field
    actions = {}
    for side, domain in (("Shell", "Plate"), ("Beam", "BeamSolid")):
        for station in (0, 1000, 2000):
            name = f"{side}Port{station}"
            ids = model["sets"][name]
            ref, _ = model["ports"][name]
            wrench = port_wrench(x, fint[domain], ids, ref)
            q, gap = rigid_fit(x, u, ids, ref)
            actual_work = float(sum(fint[domain][n]@u[n] for n in ids))
            actions[name] = dict(wrench=wrench.tolist(), fitted_pose=q.tolist(),
                                 maximum_rigid_gap_m=gap,
                                 work_discrepancy_j=actual_work-float(wrench@q))
    stations = {str(station): station_contract(model, actions, station)
                for station in (0, 1000, 2000)}
    free = sorted(physical-model["sets"]["PlateRootFree"]-
                  set().union(*(model["sets"][name] for name in model["ports"])))
    if not free:
        raise ValueError("no independent physical-node equilibrium controls")
    free_residual = (fint["Plate"]+fint["BeamSolid"])[free]
    direct = np.array(sorted(model["sets"]["PlateRootFree"]), dtype=np.int32)
    direct_force = fint["Plate"][direct]
    support = np.r_[direct_force.sum(axis=0),
                    np.cross(x[direct], direct_force).sum(axis=0)]
    for side in ("Shell", "Beam"):
        name = f"{side}Port0"
        ref = model["ports"][name][0]
        w = np.asarray(actions[name]["wrench"])
        support += w+np.r_[np.zeros(3), np.cross(x[ref], w[:3])]
    applied = np.zeros(6)
    for node, dof, value in model["loads"]:
        if dof <= 3 and node in {model["ports"][f"BeamPort{station}"][0]
                                  for station in (0, 1000, 2000)}:
            f = np.eye(3)[dof-1]*value
            applied += np.r_[f, np.cross(x[node], f)]
        elif dof <= 3 and node in {model["ports"][f"BeamPort{station}"][1]
                                    for station in (0, 1000, 2000)}:
            applied[dof+2] += value
        else:
            raise ValueError("undeclared E01 point-load node or DOF")
    return dict(classification="development weak residual; not accepted E01 reference",
                minimum_jacobian_m3=minimum_jacobian,
                ports=actions, stations=stations,
                independent_node_max_residual_n=float(np.max(np.abs(free_residual))),
                independent_node_rms_residual_n=float(np.sqrt(np.mean(free_residual**2))),
                root_support_n_nm=support.tolist(), applied_n_nm=applied.tolist(),
                root_plus_applied_n_nm=(support+applied).tolist())


def recover(deck: Path, frd: Path, manifest: Path) -> dict:
    """Bind an executed displacement field to one immutable generated deck."""
    document = json.loads(manifest.read_text(encoding="utf-8"))
    if document.get("identity") != "R8_E01_RESOLVED_PORT_INERT_V1":
        raise ValueError("wrong E01 source-manifest identity")
    matches = [case for case in document["cases"] if case["deck"] == deck.name]
    if len(matches) != 1 or sha256(deck.read_bytes()).hexdigest() != matches[0]["sha256"]:
        raise ValueError("E01 deck differs from saved source manifest")
    if frd.stem != deck.stem:
        raise ValueError("E01 displacement file does not match deck stem")
    result = recover_from_displacements(read_deck(deck), _read_frd_u(frd))
    result["input_sha256"] = {path.name: sha256(path.read_bytes()).hexdigest()
                              for path in (deck, frd, manifest)}
    return result
