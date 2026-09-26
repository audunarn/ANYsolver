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
            patch_x1: float = 1.,
            patch_grid: tuple[float, ...] = (.9, .925, .95, .975, 1.)
            ) -> dict:
    """Evaluate a declared mesh-aligned 35 mm, factor-four bond patch."""
    if set(coords) != set(u) or not all(np.isfinite(v).all() for v in u.values()):
        raise ValueError("complete finite solid displacement inventory required")
    grid = np.asarray(patch_grid, dtype=float)
    if (grid.ndim != 1 or len(grid) < 2 or
            not np.isfinite(grid).all() or not np.all(np.diff(grid) > 0.) or
            grid[0] < 0. or grid[-1] > 1. or
            not np.isfinite(section_x) or
            not any(abs(section_x-x) < 1e-12 for x in grid) or
            not patch_x0 <= section_x <= patch_x1 or
            not any(abs(patch_x0-x) < 1e-12 for x in grid) or
            not any(abs(patch_x1-x) < 1e-12 for x in patch_grid) or
            patch_x1 <= patch_x0):
        raise ValueError("mesh-aligned solid section and bond patch required")
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

    xcuts = np.array([x for x in grid
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
            "patch_grid_x_m":grid.tolist(),
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


def project_surface_position_moments(
        coords: dict[int, np.ndarray], u: dict[int, np.ndarray], *,
        stations: tuple[float, ...] = (.9, .925, .95, .975, 1.)
        ) -> dict:
    """Read-only solid projection onto a mesh-aligned finite moment patch.

    The shell side is the *actual* loaded solid top face. The beam side is a
    piecewise-interpolated rigid fit to complete solid bar sections at the
    registered stations. Their difference measures the reduction to a B3
    section; the solid's actual shared bond face has zero positional gap.
    Material arms, actual area and inertia turn the difference into three
    translations and three rotation-like moments. The default 100 mm patch
    is the native candidate; 125 mm interior patches only compare positions
    within the saved full-bond solid. This is not a constitutive, contact or
    E4-state comparison.
    """
    grid = np.asarray(stations, dtype=float)
    if (grid.ndim != 1 or len(grid) not in (3, 5) or
            not np.isfinite(grid).all() or
            not np.all(np.diff(grid) > 0.) or
            not (len(grid) == 5 and
                 np.allclose(np.diff(grid), .025, rtol=0., atol=1e-12) or
                 len(grid) == 3 and
                 np.allclose(np.diff(grid), .0625, rtol=0., atol=1e-12)) or
            grid[0] < 0. or grid[-1] > 1.):
        raise ValueError("mesh-aligned solid section stations required")
    patch_x0, patch_x1 = float(grid[0]), float(grid[-1])
    patch_center_x = (patch_x0+patch_x1)/2.
    fitted = [project(coords, u, section_x=float(x),
                      patch_x0=patch_x0, patch_x1=patch_x1,
                      patch_grid=tuple(grid)) for x in grid]
    lookup: dict[tuple[float, float, float], list[int]] = {}
    for node, xyz in coords.items():
        lookup.setdefault(tuple(np.round(xyz, 9)), []).append(node)

    def top_face(x0, x1, y0, y1):
        xm, ym = (x0+x1)/2, (y0+y1)/2
        points = ((x0,y0),(x1,y0),(x1,y1),(x0,y1),
                  (xm,y0),(x1,ym),(xm,y1),(x0,ym))
        result = []
        for x, y in points:
            ids = lookup.get(tuple(np.round((x, y, .0175), 9)), ())
            if len(ids) != 1:
                raise ValueError("ambiguous shared solid bond node")
            result.append(coords[ids[0]]+u[ids[0]])
        return np.array(result)

    center_frame = Rotation.from_rotvec(
        fitted[len(grid)//2]["beam_rotation_vector_rad"]).as_matrix()
    mean = np.zeros(3)
    moment = np.zeros(3)
    inertia = np.zeros((3, 3))
    squared_gap = 0.
    squared_face_interpolation = 0.
    squared_endpoint_section_fit = 0.
    squared_pose_interpolation = 0.
    max_gap = 0.
    area = 0.
    ycuts = np.linspace(-.05, .05, 9)
    roots, weights = np.polynomial.legendre.leggauss(3)
    for station, (x0, x1) in enumerate(zip(grid[:-1], grid[1:])):
        c0 = np.array(fitted[station]["beam_center_m"])
        c1 = np.array(fitted[station+1]["beam_center_m"])
        r0 = np.array(fitted[station]["beam_rotation_vector_rad"])
        r1 = np.array(fitted[station+1]["beam_rotation_vector_rad"])
        q0 = Rotation.from_rotvec(r0).as_matrix()
        q1 = Rotation.from_rotvec(r1).as_matrix()
        for y0, y1 in zip(ycuts[:-1], ycuts[1:]):
            face = top_face(float(x0), float(x1), float(y0), float(y1))
            jac = (x1-x0)*(y1-y0)/4
            for xi, wx in zip(roots, weights):
                x = (x0+x1)/2+xi*(x1-x0)/2
                fraction = (x-x0)/(x1-x0)
                beam_center = (1-fraction)*c0+fraction*c1
                beam_frame = Rotation.from_rotvec(
                    (1-fraction)*r0+fraction*r1).as_matrix()
                for eta, wy in zip(roots, weights):
                    y = (y0+y1)/2+eta*(y1-y0)/2
                    shell_point = _quad8_shape(float(xi), float(eta))@face
                    section_arm = np.array((0., y, -.05))
                    beam_point = beam_center+beam_frame@section_arm
                    shell_left = _quad8_shape(-1., float(eta))@face
                    shell_right = _quad8_shape(1., float(eta))@face
                    linear_shell = (1-fraction)*shell_left+fraction*shell_right
                    linear_beam = ((1-fraction)*(c0+q0@section_arm)+
                                   fraction*(c1+q1@section_arm))
                    face_interpolation = shell_point-linear_shell
                    endpoint_section_fit = linear_shell-linear_beam
                    pose_interpolation = linear_beam-beam_point
                    if np.linalg.norm(shell_point-beam_point-
                                      face_interpolation-endpoint_section_fit-
                                      pose_interpolation) > 1e-12:
                        raise ArithmeticError("solid section residual split failed")
                    gap = center_frame.T@(shell_point-beam_point)
                    arm = np.array((x-patch_center_x, y, 0.))
                    weight = float(wx*wy*jac)
                    area += weight
                    mean += weight*gap
                    moment += weight*np.cross(arm, gap)
                    inertia += weight*((arm@arm)*np.eye(3)-np.outer(arm, arm))
                    squared_gap += weight*float(gap@gap)
                    squared_face_interpolation += (
                        weight*float(face_interpolation@face_interpolation))
                    squared_endpoint_section_fit += (
                        weight*float(endpoint_section_fit@endpoint_section_fit))
                    squared_pose_interpolation += (
                        weight*float(pose_interpolation@pose_interpolation))
                    max_gap = max(max_gap, float(np.linalg.norm(gap)))
    expected_area = (patch_x1-patch_x0)*.1
    if abs(area-expected_area) > 1e-12:
        raise ArithmeticError("physical bond patch area changed")
    mean /= area
    moment /= area
    inertia /= area
    if np.linalg.eigvalsh(inertia)[0] <= 1e-8:
        raise ArithmeticError("degenerate footprint inertia")
    rotation_like = np.linalg.solve(inertia, moment)
    return {
        "status": "EXPLORATORY_NOT_G0_ACCEPTANCE",
        "patch_interval_x_m": [patch_x0, patch_x1],
        "patch_width_y_m": .1,
        "section_stations_x_m": grid.tolist(),
        "area_m2": float(area),
        "inertia_eigenvalues_m2": np.linalg.eigvalsh(inertia).tolist(),
        "surface_position_moment_gap_m_rad": np.r_[mean, rotation_like].tolist(),
        "reduced_section_gap_rms_m": float(np.sqrt(squared_gap/area)),
        "reduced_section_gap_max_m": max_gap,
        "face_interpolation_rms_m": float(np.sqrt(
            squared_face_interpolation/area)),
        "endpoint_section_fit_rms_m": float(np.sqrt(
            squared_endpoint_section_fit/area)),
        "beam_pose_interpolation_rms_m": float(np.sqrt(
            squared_pose_interpolation/area)),
        "beam_section_fit_rms_by_station_m": [
            row["beam_section_rms_fit_residual_m"] for row in fitted],
        "tip_lumped_pose_gap_m_rad": (
            fitted[-1]["distributing_translation_gap_m"]+
            fitted[-1]["distributing_rotation_gap_rad"]),
        "interpretation": "solid top face versus fitted rigid B3-like sections, not actual shared-face opening, E4 reconstruction, native multiplier work or external accuracy acceptance",
    }


def bound_c1_unbonded_vertical_gap(
        coords: dict[int, np.ndarray], u: dict[int, np.ndarray],
        face_pairs: list[list[list[int]]]) -> dict:
    """Sufficient continuous underside/top gap bound for saved C1 Q8 fields.

    The result applies where the two deformed XY face unions overlap. It
    concerns the interpolated displacement output, not solver truncation,
    side-face contact, mesh convergence, or native coupling accuracy.
    """
    if set(coords) != set(u) or not all(np.isfinite(v).all() for v in u.values()):
        raise ValueError("complete finite C1 displacement inventory required")
    pairs = np.asarray(face_pairs, dtype=int)
    if pairs.shape not in ((32, 8, 2), (128, 8, 2)) or not set(pairs.flat).issubset(coords):
        raise ValueError("complete 128-face or 32-face paired C1 inventory required")
    expected_grid = {32: (9, 5), 128: (17, 9)}[len(pairs)]
    transform = np.array(((1., 0., 0.), (-.5, 2., -.5), (0., 0., 1.)))
    sample = (-1., 0., 1.)

    def coefficients(nodes: np.ndarray) -> np.ndarray:
        values = np.array([[_quad8_shape(x, y) @ nodes for y in sample]
                           for x in sample])
        return np.stack([transform @ values[:, :, k] @ transform.T
                         for k in range(3)], axis=2)

    rows = []
    cells = set()
    for index, face in enumerate(pairs):
        plate_ref = np.array([coords[int(i)] for i in face[:, 0]])
        plate = np.array([coords[int(i)]+u[int(i)] for i in face[:, 0]])
        bar = np.array([coords[int(j)]+u[int(j)] for j in face[:, 1]])
        x0, x1 = float(plate_ref[0, 0]), float(plate_ref[1, 0])
        y0, y1 = float(plate_ref[0, 1]), float(plate_ref[3, 1])
        if (x1 <= x0 or y1 <= y0 or
                np.max(np.abs(plate_ref[:, 2]-.0175)) > 1e-12):
            raise ValueError("invalid C1 plate-top reference face")
        cell = tuple(round(v, 10) for v in (x0, x1, y0, y1))
        if cell in cells:
            raise ValueError("duplicate C1 unbonded face")
        cells.add(cell)
        pcoef, bcoef = coefficients(plate), coefficients(bar)
        delta = pcoef-bcoef
        gap = bcoef[:, :, 2]-pcoef[:, :, 2]
        ax, ay = (x1-x0)/2, (y1-y0)/2
        dx = bcoef[1:, :, :]-bcoef[:-1, :, :]
        dy = bcoef[:, 1:, :]-bcoef[:, :-1, :]
        perturbation = np.array((
            (np.max(np.abs(dx[:, :, 0]/ax-1.)),
             np.max(np.abs(dy[:, :, 0]/ay))),
            (np.max(np.abs(dx[:, :, 1]/ax)),
             np.max(np.abs(dy[:, :, 1]/ay-1.)))))
        epsilon = float(np.linalg.norm(perturbation))
        vertical_lipschitz = float(np.hypot(
            np.max(np.abs(dx[:, :, 2]/ax)),
            np.max(np.abs(dy[:, :, 2]/ay))))
        seam = abs(x1-.9) <= 1e-10
        if seam:
            if max(np.max(np.abs(delta[2, :, :])),
                   np.max(np.abs(gap[2, :]))) > 2e-12:
                raise ValueError("C1 seam is not exactly shared")
            # The shared edge is t=1; both gap and horizontal mismatch
            # factor by (1-t), with degree-one quotient controls below.
            gap_controls = np.stack((gap[0, :], 2*gap[1, :]))
            mismatch_controls = np.stack((delta[0, :, :2],
                                          2*delta[1, :, :2]))
        else:
            gap_controls = gap
            mismatch_controls = delta[:, :, :2]
        rows.append((index, seam, epsilon, vertical_lipschitz,
                     float(np.min(gap_controls)),
                     float(np.max(np.linalg.norm(
                         mismatch_controls, axis=2)))))

    xs = sorted({x for x0, x1, _, _ in cells for x in (x0, x1)})
    ys = sorted({y for _, _, y0, y1 in cells for y in (y0, y1)})
    expected = {(xs[i], xs[i+1], ys[j], ys[j+1])
                for i in range(len(xs)-1) for j in range(len(ys)-1)}
    if ((len(xs), len(ys)) != expected_grid or cells != expected or
            sum(row[1] for row in rows) != len(ys)-1 or
            abs(xs[0]) > 1e-10 or abs(xs[-1]-.9) > 1e-10 or
            abs(ys[0]+.05) > 1e-10 or abs(ys[-1]-.05) > 1e-10):
        raise ValueError("C1 unbonded reference rectangle is incomplete")
    epsilon = max(row[2] for row in rows)
    if epsilon >= 1.:
        raise ValueError("C1 deformed horizontal map is not bounded injective")
    vertical_lipschitz = max(row[3] for row in rows)
    margins = [(g-vertical_lipschitz*h/(1.-epsilon), index, seam)
               for index, seam, _, _, g, h in rows]
    return {
        "status": ("POSITIVE_SAVED_FIELD_FACE_GAP_BOUND" if
                   min(margin for margin, _, _ in margins) > 0. else
                   "INCONCLUSIVE_FACE_GAP_BOUND"),
        "face_count": len(rows),
        "seam_face_count": sum(row[1] for row in rows),
        "horizontal_map_perturbation_frobenius_bound": epsilon,
        "bar_vertical_lipschitz_bound": vertical_lipschitz,
        "maximum_horizontal_mismatch_m": max(row[5] for row in rows),
        "maximum_vertical_reprojection_correction_m": max(
            vertical_lipschitz*row[5]/(1.-epsilon) for row in rows),
        "minimum_nonseam_gap_bound_m": min(
            margin for margin, _, seam in margins if not seam),
        "minimum_seam_factored_gap_bound_m": min(
            margin for margin, _, seam in margins if seam),
        "minimum_margin_face_index": min(margins)[1],
        "meaning": "sufficient vertical gap bound for overlapping deformed XY on the saved C1 unbonded underside/top face unions; the seam gap is zero",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--stem", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--station-series", action="store_true")
    parser.add_argument("--face-gap-bound", action="store_true")
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
    if args.face_gap_bound:
        model = json.loads((folder/"model.json").read_text())
        result["unbonded_face_gap_bound"] = bound_c1_unbonded_vertical_gap(
            coords, u, model["unbonded_face_pairs"])
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
