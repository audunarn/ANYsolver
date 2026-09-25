"""Project one saved C3D20R terminal bond onto the candidate patch pose.

This is a bounded development diagnostic. Solid through-thickness kinematics
infer a shell director; they are not an E4 material-state reconstruction.
The section pose is the area-weighted rigid fit to the deformed solid end face.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

from scripts._b3_e4_ccx_3d_tip_work_parser import _values
from scripts.b3_e4_f03_ccx_solid_bond_screen import _quad8_shape


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_deck_nodes(path: Path) -> dict[int, np.ndarray]:
    nodes: dict[int, np.ndarray] = {}
    inside = False
    for line in path.read_text().splitlines():
        if line.startswith("*NODE,NSET=AllNodes"):
            inside = True
            continue
        if inside and line.startswith("*ELEMENT"):
            break
        if inside:
            parts = line.split(",")
            node = int(parts[0])
            if node in nodes:
                raise ValueError("duplicate deck node")
            nodes[node] = np.array([float(v) for v in parts[1:4]])
    if not nodes:
        raise ValueError("no deck nodes")
    return nodes


def _read_frd_u(path: Path) -> dict[int, np.ndarray]:
    vectors: dict[int, np.ndarray] = {}
    inside = False
    blocks = 0
    for line in path.open(errors="replace"):
        if line.startswith(" -4  DISP"):
            inside = True
            blocks += 1
            continue
        if inside and line.startswith(" -3"):
            inside = False
            continue
        if inside and line.startswith(" -1"):
            node, value = _values(line)
            if node in vectors:
                raise ValueError("duplicate FRD displacement")
            vectors[node] = np.array(value)
    if blocks != 1:
        raise ValueError("one completed FRD DISP block required")
    return vectors


def _frame(a: np.ndarray, b: np.ndarray,
           d: np.ndarray) -> np.ndarray:
    d = d / np.linalg.norm(d)
    cosine = float(d[2])
    if cosine <= -.95:
        raise ValueError("antipodal inferred director")
    v = np.cross((0., 0., 1.), d)
    skew = np.array(((0., -v[2], v[1]),
                     (v[2], 0., -v[0]),
                     (-v[1], v[0], 0.)))
    chart = np.eye(3) + skew + skew @ skew / (1. + cosine)
    projected = chart[:, :2].T @ np.column_stack((a, b))
    if np.linalg.det(projected) <= 0.:
        raise ValueError("inverted inferred shell patch")
    trace = float(np.trace(projected))
    spin = float(projected[1, 0] - projected[0, 1])
    length = float(np.hypot(trace, spin))
    if length <= 1e-10:
        raise ValueError("singular inferred shell yaw")
    c, s = trace / length, spin / length
    return chart @ np.array(((c, -s, 0.), (s, c, 0.), (0., 0., 1.)))


def project(coords: dict[int, np.ndarray],
            u: dict[int, np.ndarray], *,
            section_x: float = 1.,
            patch_x0: float = .9,
            patch_x1: float = 1.) -> dict:
    """Evaluate the declared 35 mm, factor-four, 0.1 m terminal patch."""
    if set(coords) != set(u) or not all(np.isfinite(v).all() for v in u.values()):
        raise ValueError("complete finite solid displacement inventory required")
    if not any(abs(section_x-x) < 1e-12 for x in (.9,.925,.95,.975,1.)):
        raise ValueError("section station must be on the bounded solid bond grid")
    patch_grid = (.9,.925,.95,.975,1.)
    if (not any(abs(patch_x0-x) < 1e-12 for x in patch_grid) or
            not any(abs(patch_x1-x) < 1e-12 for x in patch_grid) or
            patch_x1 <= patch_x0):
        raise ValueError("patch must be a nonempty solid bond subinterval")
    lookup: dict[tuple[float, float, float], list[int]] = {}
    for node, xyz in coords.items():
        lookup.setdefault(tuple(np.round(xyz, 9)), []).append(node)

    def node(x: float, y: float, z: float) -> int:
        ids = lookup.get(tuple(np.round((x, y, z), 9)), ())
        if len(ids) != 1:
            raise ValueError(f"ambiguous solid sample ({x}, {y}, {z}): {len(ids)}")
        return ids[0]

    def face_xy(x0: float, x1: float, y0: float, y1: float,
                z: float) -> np.ndarray:
        xm, ym = (x0 + x1) / 2., (y0 + y1) / 2.
        points = ((x0,y0),(x1,y0),(x1,y1),(x0,y1),
                  (xm,y0),(x1,ym),(xm,y1),(x0,ym))
        return np.array([coords[node(x,y,z)] + u[node(x,y,z)]
                         for x,y in points])

    def face_yz(x: float, y0: float, y1: float,
                z0: float, z1: float) -> np.ndarray:
        ym, zm = (y0 + y1) / 2., (z0 + z1) / 2.
        points = ((y0,z0),(y1,z0),(y1,z1),(y0,z1),
                  (ym,z0),(y1,zm),(ym,z1),(y0,zm))
        return np.array([coords[node(x,y,z)] + u[node(x,y,z)]
                         for y,z in points])

    xcuts = np.array([x for x in patch_grid
                      if patch_x0-1e-12 <= x <= patch_x1+1e-12])
    ycuts = np.linspace(-.05, .05, 9)
    zcuts = np.linspace(.0175, .1175, 9)
    roots, gauss = np.polynomial.legendre.leggauss(3)
    h = 1e-5
    area = 0.
    shell_center = np.zeros(3)
    gradient_x = np.zeros(3)
    gradient_y = np.zeros(3)
    director = np.zeros(3)
    for x0, x1 in zip(xcuts[:-1], xcuts[1:]):
        for y0, y1 in zip(ycuts[:-1], ycuts[1:]):
            mid = face_xy(x0, x1, y0, y1, 0.)
            top = face_xy(x0, x1, y0, y1, .0175)
            bottom = face_xy(x0, x1, y0, y1, -.0175)
            jac = (x1 - x0) * (y1 - y0) / 4.
            for xi, wx in zip(roots, gauss):
                for eta, wy in zip(roots, gauss):
                    shape = _quad8_shape(float(xi), float(eta))
                    weight = float(wx * wy * jac)
                    d = shape @ (top - bottom)
                    d /= np.linalg.norm(d)
                    dx = ((_quad8_shape(xi+h,eta)-_quad8_shape(xi-h,eta))
                          @ mid) / (h * (x1-x0))
                    dy = ((_quad8_shape(xi,eta+h)-_quad8_shape(xi,eta-h))
                          @ mid) / (h * (y1-y0))
                    area += weight
                    shell_center += weight * (shape @ mid)
                    gradient_x += weight * dx
                    gradient_y += weight * dy
                    director += weight * d
    expected_area = (patch_x1-patch_x0)*.1
    if abs(area - expected_area) > 1e-12:
        raise AssertionError("solid patch area changed")
    shell_center /= area
    gradient_x /= area
    gradient_y /= area
    shell_frame = _frame(gradient_x, gradient_y, director)

    section_ref = np.array((section_x, 0., .0675))
    rows = []
    values = []
    weights = []
    for z0, z1 in zip(zcuts[:-1], zcuts[1:]):
        for y0, y1 in zip(ycuts[:-1], ycuts[1:]):
            face = face_yz(section_x, y0, y1, z0, z1)
            jac = (y1 - y0) * (z1 - z0) / 4.
            for xi, wx in zip(roots, gauss):
                for eta, wy in zip(roots, gauss):
                    y = (y0 + y1) / 2. + xi * (y1 - y0) / 2.
                    z = (z0 + z1) / 2. + eta * (z1 - z0) / 2.
                    relative = np.array((0., y, z - section_ref[2]))
                    skew = np.array(((0., -relative[2], relative[1]),
                                     (relative[2], 0., 0.),
                                     (-relative[1], 0., 0.)))
                    design = np.column_stack((np.eye(3), -skew))
                    point = _quad8_shape(float(xi),float(eta)) @ face
                    displacement = point - np.array((section_x,y,z))
                    rows.append(design)
                    values.append(displacement)
                    weights.append(float(wx * wy * jac))
    design = np.vstack(rows)
    displacement = np.concatenate(values)
    factors = np.repeat(np.sqrt(weights), 3)
    motion, _, rank, _ = np.linalg.lstsq(
        factors[:,None] * design, factors * displacement, rcond=None)
    if rank != 6:
        raise ValueError("solid tip section has deficient rigid fit")
    error = (design @ motion - displacement).reshape(-1,3)
    section_rms = float(np.sqrt(np.dot(weights,
                  np.sum(error**2,axis=1)) / sum(weights)))
    beam_center = section_ref + motion[:3]
    beam_frame = Rotation.from_rotvec(motion[3:]).as_matrix()
    patch_center_x = (patch_x0+patch_x1)/2.
    reference_offset = np.array((section_x-patch_center_x,0.,.0675))
    translation_gap = shell_frame.T @ (beam_center-shell_center) - reference_offset
    rotation_gap = Rotation.from_matrix(shell_frame.T @ beam_frame).as_rotvec()
    corner_gaps = []
    for x,y in ((patch_x0,-.05),(patch_x1,-.05),
                (patch_x1,.05),(patch_x0,.05)):
        shell_point = coords[node(x,y,0.)] + u[node(x,y,0.)]
        predicted = beam_center + beam_frame @ (np.array((x,y,0.))-section_ref)
        corner_gaps.append(shell_point-predicted)
    corner_gaps = np.array(corner_gaps)
    return {"section_station_x_m":section_x,
            "patch_interval_x_m":[patch_x0,patch_x1],
            "shell_center_m":shell_center.tolist(),
            "shell_midplane_gradient_x":gradient_x.tolist(),
            "shell_midplane_gradient_y":gradient_y.tolist(),
            "solid_inferred_director":(director/np.linalg.norm(director)).tolist(),
            "shell_rotation_vector_rad":Rotation.from_matrix(shell_frame).as_rotvec().tolist(),
            "beam_center_m":beam_center.tolist(),
            "beam_rotation_vector_rad":motion[3:].tolist(),
            "beam_section_rms_fit_residual_m":section_rms,
            "beam_section_max_sample_fit_residual_m":float(np.max(np.linalg.norm(error,axis=1))),
            "distributing_translation_gap_m":translation_gap.tolist(),
            "distributing_rotation_gap_rad":rotation_gap.tolist(),
            "rigid_corner_gap_m":corner_gaps.tolist(),
            "rigid_corner_gap_max_norm_m":float(np.max(np.linalg.norm(corner_gaps,axis=1))),
            "meaning":"area-integrated solid-inferred midsurface/director patch pose versus area-weighted solid tip section fit; not an E4 state or accepted contact/reference comparison"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--stem", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--station-series", action="store_true")
    args = parser.parse_args()
    folder = args.case.resolve()
    inp,frd = (folder/(args.stem+suffix) for suffix in (".inp",".frd"))
    coords = _read_deck_nodes(inp)
    u = _read_frd_u(frd)
    zero = project(coords,{node:np.zeros(3) for node in coords})
    if (np.max(np.abs(zero["distributing_translation_gap_m"])) > 1e-12 or
            np.max(np.abs(zero["distributing_rotation_gap_rad"])) > 1e-12 or
            zero["rigid_corner_gap_max_norm_m"] > 1e-12):
        raise AssertionError("projected solid reference is not stress-free")
    rigid_matrix = Rotation.from_rotvec((4e-5,-3e-5,2e-5)).as_matrix()
    shift = np.array((1e-4,-2e-4,3e-4))
    rigid_u = {node:rigid_matrix@xyz+shift-xyz
               for node,xyz in coords.items()}
    rigid = project(coords,rigid_u)
    rigid_error = max(
        np.max(np.abs(rigid["distributing_translation_gap_m"])),
        np.max(np.abs(rigid["distributing_rotation_gap_rad"])),
        rigid["rigid_corner_gap_max_norm_m"])
    if rigid_error > 1e-9:
        raise AssertionError("projected solid pose is not objective at physical rotation scale")
    result = project(coords,u)
    if args.station_series:
        whole = [project(coords,u,section_x=station)
                 for station in (.9,.925,.95,.975,1.)]
        local = [project(coords,u,section_x=station,
                         patch_x0=left,patch_x1=right)
                 for station,left,right in ((.925,.9,.95),
                                            (.95,.925,.975),
                                            (.975,.95,1.))]
        result["whole_patch_station_series"] = whole
        result["local_patch_station_series"] = local
    result.update({"status":"EXPLORATORY_NOT_G0_ACCEPTANCE",
                   "case":str(folder),
                   "deck_sha256":_sha(inp),"frd_sha256":_sha(frd),
                   "source_sha256":_sha(Path(__file__)),
                   "common_rigid_gap_max_m_rad":rigid_error,
                   "reference_zero_gap_max_m_rad":max(
                       np.max(np.abs(zero["distributing_translation_gap_m"])),
                       np.max(np.abs(zero["distributing_rotation_gap_rad"])),
                       zero["rigid_corner_gap_max_norm_m"])})
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({key:result[key] for key in (
        "distributing_translation_gap_m","distributing_rotation_gap_rad",
        "rigid_corner_gap_max_norm_m","beam_section_rms_fit_residual_m")}))


if __name__ == "__main__":
    main()
