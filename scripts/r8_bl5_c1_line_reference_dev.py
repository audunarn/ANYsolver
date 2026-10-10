"""Prepare a bounded C1 detached, zero-width five-channel solid reference.

This is a linear C3D20R development comparator. It is neither the native B3/E4
trace nor a qualified finite-width weld, and preparing decks does not execute
or validate an external solution.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from scripts import b3_e4_f03_ccx_solid_bond_screen as base


STATIONS_MM = (900., 925., 950., 975., 1000.)
PROFILE_CLEARANCE_MM = .002
PLATE_TOP_M = .0175
PLATE_BOTTOM_M = -.0175
BAR_TOP_M = .1175
BAR_AXIS_MM = 67.5


def _sha(payload: bytes) -> str:
    return sha256(payload).hexdigest()


def _split_deck(deck: str) -> tuple[list[str], dict[int, np.ndarray], set[int], set[int]]:
    lines = deck.splitlines()
    node_start = lines.index("*NODE,NSET=AllNodes") + 1
    node_end = next(j for j in range(node_start, len(lines)) if lines[j].startswith("*"))
    xyz = {}
    for line in lines[node_start:node_end]:
        values = line.split(",")
        xyz[int(values[0])] = np.asarray([float(v) for v in values[1:]], dtype=float)

    domains = []
    for name in ("Plate", "Stiffener"):
        start = lines.index(f"*ELEMENT,TYPE=C3D20R,ELSET={name}") + 1
        stop = next(j for j in range(start, len(lines)) if lines[j].startswith("*"))
        tokens = [int(v) for line in lines[start:stop] for v in line.split(",") if v]
        if len(tokens) % 21:
            raise ValueError(f"incomplete {name} C3D20R connectivity")
        domains.append({node for j in range(0, len(tokens), 21)
                        for node in tokens[j+1:j+21]})
    plate, bar = domains
    if plate & bar or plate | bar != set(xyz):
        raise ValueError("detached domains must own every physical node exactly once")
    return lines, xyz, plate, bar


def _c1_bar_position(original_m: np.ndarray) -> np.ndarray:
    x_mm, y_mm, z_mm = original_m * 1000.
    if x_mm >= 900.:
        return original_m.copy()
    if x_mm <= 750.:
        offset, slope = PROFILE_CLEARANCE_MM, 0.
    else:
        t = (x_mm - 750.) / 150.
        if t <= .5:
            offset = PROFILE_CLEARANCE_MM * (1. - 2.*t*t)
            slope = -4.*PROFILE_CLEARANCE_MM*t/150.
        else:
            offset = 2.*PROFILE_CLEARANCE_MM*(1.-t)**2
            slope = -4.*PROFILE_CLEARANCE_MM*(1.-t)/150.
    normalizer = np.sqrt(1. + slope*slope)
    local_z = z_mm - BAR_AXIS_MM
    return np.array(((x_mm-local_z*slope/normalizer)/1000., y_mm/1000.,
                     (BAR_AXIS_MM+offset+local_z/normalizer)/1000.))


def _node_at(xyz: dict[int, np.ndarray], domain: set[int], x: float, z: float) -> int:
    matches = [n for n in domain if np.max(np.abs(xyz[n] - (x, 0., z))) < 2e-12]
    if len(matches) != 1:
        raise ValueError(f"expected one node at x={x}, y=0, z={z}; found {len(matches)}")
    return matches[0]


def _five_channel_rows(xyz: dict[int, np.ndarray], plate: set[int], bar: set[int]) -> list[dict[tuple[int, int], float]]:
    rows = []
    for x_mm in STATIONS_MM:
        x = x_mm / 1000.
        ps = _node_at(xyz, plate, x, PLATE_TOP_M)
        pb = _node_at(xyz, plate, x, PLATE_BOTTOM_M)
        bs = _node_at(xyz, bar, x, PLATE_TOP_M)
        bt = _node_at(xyz, bar, x, BAR_TOP_M)
        if np.max(np.abs(xyz[ps]-xyz[bs])) > 1e-12:
            raise ValueError("terminal translation reference is not stress free")
        for axis in (1, 2, 3):
            rows.append({(bs, axis): 1., (ps, axis): -1.})
        for axis in (1, 2):
            rows.append({(bt, axis): 1./.1, (bs, axis): -1./.1,
                         (ps, axis): -1./.035, (pb, axis): 1./.035})
    return rows


def _deck_rows(physical: list[dict[tuple[int, int], float]]) -> list[dict[tuple[int, int], float]]:
    """Triangular equivalent basis: no equation references another pivot.

    For each director row D and same-axis translation T, Ddeck=0.1*D+T.
    The physical row basis remains authoritative for recovered multipliers.
    """
    encoded = []
    for station in range(len(STATIONS_MM)):
        group = physical[5*station:5*station+5]
        encoded.extend(dict(row) for row in group[:3])
        for axis in (0,1):
            row = {slot: .1*value for slot,value in group[3+axis].items()}
            for slot,value in group[axis].items():
                row[slot] = row.get(slot,0.)+value
            encoded.append({slot:value for slot,value in row.items() if abs(value)>1e-14})
    return encoded


def _fy_face_load(xyz: dict[int, np.ndarray], bar: set[int]) -> dict[int, np.ndarray]:
    end = {tuple(np.round(xyz[n][1:], 12)): n for n in bar
           if abs(xyz[n][0]-1.) < 1e-12}
    by = base._cuts(base.BAR_Y_MM, 2)
    bz = base._cuts((Fraction(17.5), Fraction(67.5), Fraction(117.5)), 2)
    roots, weights = np.polynomial.legendre.leggauss(3)
    forces = defaultdict(lambda: np.zeros(3))
    for z0, z1 in zip(bz[:-1], bz[1:]):
        for y0, y1 in zip(by[:-1], by[1:]):
            ym, zm = (y0+y1)/2, (z0+z1)/2
            points = ((y0,z0), (y1,z0), (y1,z1), (y0,z1),
                      (ym,z0), (y1,zm), (ym,z1), (y0,zm))
            ids = [end[(round(float(y)/1000., 12), round(float(z)/1000., 12))]
                   for y,z in points]
            jacobian = float((y1-y0)*(z1-z0))/4e6
            for xi, wx in zip(roots, weights):
                for eta, wy in zip(roots, weights):
                    shape = base._quad8_shape(float(xi), float(eta))
                    for n, value in zip(ids, shape):
                        forces[n][1] += float(wx*wy*jacobian*value*100./.01)
    if set(forces) != set(end.values()):
        raise ValueError("Fy traction omits a quadratic tip-face node")
    return dict(forces)


def _mx_load(meta: dict) -> dict[int, np.ndarray]:
    return {int(n): np.asarray(v, dtype=float)
            for n, v in meta["applied_nodal_forces_N"].items()}


def _remove_load_roundoff(forces: dict[int, np.ndarray]) -> tuple[dict[int, np.ndarray],dict]:
    """Drop only quadrature-zero components below the deck precision floor."""
    small = [abs(float(v)) for force in forces.values() for v in force
             if 0. < abs(float(v)) < 1e-10]
    if any(v>=1e-12 for v in small):
        raise ValueError("load component in unresolved roundoff band")
    clean = {n:np.where(np.abs(force)<1e-10,0.,force).copy()
             for n,force in forces.items()}
    return clean,{"removed_components":len(small),
                  "max_removed_absolute_N":max(small,default=0.)}


def _wrench(xyz: dict[int, np.ndarray], forces: dict[int, np.ndarray]) -> np.ndarray:
    result = np.zeros(6)
    for n, force in forces.items():
        result[:3] += force
        result[3:] += np.cross(xyz[n], force)
    return result


def _audits(rows: list[dict[tuple[int, int], float]], encoded: list[dict[tuple[int, int], float]],
            xyz: dict[int, np.ndarray],
            plate: set[int], bar: set[int], support: set[int]) -> dict:
    pivots = []
    for row in encoded:
        first = next(iter(row))
        if first[0] in support or first in pivots:
            raise ValueError("repeated or supported equation pivot")
        pivots.append(first)
    slots = sorted({slot for row in (*rows,*encoded) for slot in row})
    index = {slot: j for j, slot in enumerate(slots)}
    matrix = np.zeros((len(rows), len(slots)))
    deck_matrix = np.zeros_like(matrix)
    for i, row in enumerate(rows):
        for slot, coefficient in row.items():
            matrix[i, index[slot]] = coefficient
    for i, row in enumerate(encoded):
        for slot, coefficient in row.items():
            deck_matrix[i, index[slot]] = coefficient
    transform = np.eye(len(rows))
    for station in range(len(STATIONS_MM)):
        for axis in (0,1):
            j = 5*station+3+axis
            transform[j,j] = .1
            transform[j,5*station+axis] = 1.
    row_error = float(np.linalg.norm(deck_matrix-transform@matrix,ord=np.inf)
                      / max(np.linalg.norm(matrix,ord=np.inf),1e-30))
    pivot_matrix = deck_matrix[:,[index[pivot] for pivot in pivots]]
    if row_error > 1e-14 or np.max(np.abs(pivot_matrix-np.eye(len(rows)))) > 1e-14:
        raise ValueError("encoded deck basis changes the physical row space or pivot isolation")
    singular = np.linalg.svd(matrix, compute_uv=False)
    scale = max(singular)
    rank = int(np.count_nonzero(singular > scale*1e-12))
    if rank != len(rows):
        raise ValueError("five-channel terminal equations are dependent")
    # Work conjugacy is an identity for the encoded row map, not a physical
    # qualification; include nontrivial virtual fields and multipliers.
    rng = np.random.default_rng(7305)
    q = rng.standard_normal(len(slots))
    lam = rng.standard_normal(len(rows))
    work_error = abs(float(lam @ (matrix @ q) - q @ (matrix.T @ lam)))
    if work_error > 1e-10:
        raise ValueError("equation transpose work failure")
    gaps = []
    for x_mm in STATIONS_MM:
        x = x_mm/1000.
        ps = _node_at(xyz, plate, x, PLATE_TOP_M)
        pb = _node_at(xyz, plate, x, PLATE_BOTTOM_M)
        bs = _node_at(xyz, bar, x, PLATE_TOP_M)
        bt = _node_at(xyz, bar, x, BAR_TOP_M)
        gaps.extend(xyz[bs]-xyz[ps])
        gaps.extend((xyz[bt]-xyz[bs])/.1-(xyz[ps]-xyz[pb])/.035)
    max_initial_gap = float(np.max(np.abs(gaps)))
    if max_initial_gap > 1e-12:
        raise ValueError("five-channel geometric reference is not stress free")
    return {"physical_rows": len(rows), "physical_slots": len(slots),
            "rank": rank, "scaled_min_singular": float(min(singular)/scale),
            "pivot_count": len(pivots), "transpose_work_error": work_error,
            "deck_row_relative_error": row_error,
            "deck_pivot_identity_error": float(np.max(np.abs(pivot_matrix-np.eye(len(rows))))),
            "deck_basis": "Tdeck=T; Ddeck=0.1*Dphysical+T_same_axis; physical multipliers recovered through transpose basis map",
            "max_initial_gap": max_initial_gap}


def _deck(lines: list[str], xyz: dict[int, np.ndarray], bar: set[int],
          rows: list[dict[tuple[int, int], float]], loads: dict[int, np.ndarray],
          case: str) -> bytes:
    altered = list(lines)
    if case not in ("fy","mx") or "shear=tip_mx" not in altered[1]:
        raise ValueError("pinned Mx base fixture comment changed")
    altered[1] = altered[1].replace("shear=tip_mx",f"source_fixture=tip_mx; applied_case={case}")
    for j, line in enumerate(altered):
        if line.startswith("*NODE,NSET=AllNodes"):
            start = j+1
            break
    else:
        raise ValueError("node block missing")
    for j in range(start, start+len(xyz)):
        n = int(altered[j].split(",",1)[0])
        if n in bar:
            altered[j] = f"{n}," + ",".join(f"{v:.17g}" for v in xyz[n])
    equations = []
    for row in rows:
        terms = [f"{n},{dof},{coefficient:.17g}" for (n,dof), coefficient in row.items()]
        equations += ["*EQUATION", str(len(terms))]
        equations += [",".join(terms[j:j+3]) for j in range(0,len(terms),3)]
    step = altered.index("*STEP")
    altered[step:step] = equations
    cload = altered.index("*CLOAD")
    cload_end = next(j for j in range(cload+1,len(altered)) if altered[j].startswith("*"))
    altered[cload:cload_end] = ["*CLOAD"] + [
        f"{n},{axis},{value:.17g}" for n, force in sorted(loads.items())
        for axis, value in enumerate(force,1) if value != 0.]
    end = altered.index("*END STEP")
    altered[end:end] = ["*NODE OUTPUT,DOUBLE,NSET=AllNodes", "U",
                        "*NODE OUTPUT,DOUBLE,NSET=Supports", "RF"]
    return ("\n".join(altered)+"\n").encode("ascii")


def prepare() -> tuple[dict[str, bytes], dict]:
    raw, meta = base.build(2, "tip_mx", boundary_policy="left_root",
        bond_policy="detached", contact_policy="none", element_family="C3D20R",
        plate_thickness_mm=35, tip_load_map="quadratic_face",
        full_displacement_output=False, bar_clearance_um=0,
        bar_reference_profile="legacy_linear")
    lines, original, plate, bar = _split_deck(raw)
    xyz = {n: (_c1_bar_position(v) if n in bar else v.copy())
           for n,v in original.items()}
    support_start = lines.index("*NSET,NSET=Supports")+1
    support_end = next(j for j in range(support_start,len(lines)) if lines[j].startswith("*"))
    support = {int(v) for line in lines[support_start:support_end]
               for v in line.split(",") if v}
    if len(xyz)*3 > 100_000 or meta["shared_interface_nodes"] or not support:
        raise ValueError("size or detached ownership contract failed")
    rows = _five_channel_rows(xyz, plate, bar)
    encoded = _deck_rows(rows)
    audit = _audits(rows, encoded, xyz, plate, bar, support)
    fy, fy_roundoff = _remove_load_roundoff(_fy_face_load(xyz, bar))
    mx, mx_roundoff = _remove_load_roundoff(_mx_load(meta))
    expected = {"fy": np.array((0.,100.,0.,-6.75,0.,100.)),
                "mx": np.array((0.,0.,0.,100.,0.,0.))}
    cases = {}
    payloads = {}
    for name, forces, roundoff in (("fy", fy, fy_roundoff), ("mx", mx, mx_roundoff)):
        wrench = _wrench(xyz, forces)
        error = float(np.max(np.abs(wrench-expected[name])))
        if error > 1e-8:
            raise ValueError(f"{name} physical end wrench changed: {wrench}")
        payload = _deck(lines, xyz, bar, encoded, forces, name)
        payloads[name] = payload
        cases[name] = {"tip_wrench_about_origin": wrench.tolist(),
                       "wrench_absolute_error": error,
                       "load_roundoff":roundoff,
                       "quadratic_tip_face_nodes": len(forces),
                       "nonzero_loaded_nodes": int(sum(np.max(np.abs(v))>0. for v in forces.values())),
                       "deck_sha256": _sha(payload)}
    # The reference C1 lift is identically zero at x=.9; profile samples
    # check the two-micrometre normal transition independently of solve output.
    axis_node = _node_at(original, bar, .825, .0675)
    moved = xyz[axis_node]
    if abs(moved[2]-.067501) > 1e-12 or abs(moved[0]-.825) > 1e-12:
        raise ValueError("C1 midpoint profile does not match reference law")
    result = {"identity":"R8_BL5_C1_DETACHED_F2_FIVE_CHANNEL_DEV_V7",
              "status":"PREPARED_NOT_EXECUTED_NOT_QUALIFIED",
              "source_sha256":_sha(Path(__file__).read_bytes()),
              "base_builder_sha256":_sha(Path(base.__file__).read_bytes()),
              "base_deck_sha256":_sha(raw.encode("ascii")),
              "node_count":len(xyz), "physical_dofs":3*len(xyz),
              "plate_nodes":len(plate), "bar_nodes":len(bar),
              "plate_elements":meta["plate_elements"],
              "bar_elements":meta["bar_elements"],
              "supported_nodes":len(support),
              "beam_root_nodes":len(meta["beam_root_node_ids"]),
              "c1_midpoint_axis_z_m":float(moved[2]),
              "terminal_stations_m":[v/1000. for v in STATIONS_MM],
              "equations":audit, "cases":cases,
              "interpretation":"factor-2 detached C3D20R zero-width five-channel terminal solid proxy; neither native BL5 nor a finite-width weld; no solve or convergence claim"}
    return payloads, result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError("preserve prior reference preparation")
    payloads, result = prepare()
    args.output_dir.mkdir(parents=True)
    for name, payload in payloads.items():
        (args.output_dir/f"{name}.inp").write_bytes(payload)
    (args.output_dir/"metadata.json").write_text(
        json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"physical_dofs":result["physical_dofs"],
                      "equations":result["equations"],
                      "wrenches":{n:v["tip_wrench_about_origin"] for n,v in result["cases"].items()}}))


if __name__ == "__main__":
    main()
