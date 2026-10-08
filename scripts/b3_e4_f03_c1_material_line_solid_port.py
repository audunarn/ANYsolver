"""Flat-reference solid material-line pose and work map for G0 development.

This uses actual two-sided Q8 face geometry. The beam section pose is a
declared width-integrated rigid least-squares observable, not a claim that a
solid section is rigid or that the native B3 port has the same kinematics.
No external solve, multiplier policy, or production attachment is defined.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from scripts.b3_e4_f03_ccx_solid_bond_screen import _quad8_shape


def _skew(vector):
    x, y, z = vector
    return np.array(((0., -z, y), (z, 0., -x), (-y, x, 0.)))


def _quad8_dx(xi: float, eta: float, span: float) -> np.ndarray:
    """Analytic physical-x derivative in the existing Q8 node order."""
    corners = ((-1., -1.), (1., -1.), (1., 1.), (-1., 1.))
    derivative = [
        .25*sx*(1.+sy*eta)*(2.*sx*xi+sy*eta)
        for sx, sy in corners
    ] + [
        -xi*(1.-eta),
        .5*(1.-eta*eta),
        -xi*(1.+eta),
        -.5*(1.-eta*eta),
    ]
    return 2.*np.asarray(derivative)/span


@dataclass(frozen=True)
class FlatSolidLinePort:
    station_x_m: float
    node_ids: tuple[int, ...]
    gap_jacobian: np.ndarray
    shell_top_jacobian: np.ndarray
    shell_orientation_jacobian: np.ndarray
    beam_bottom_jacobian: np.ndarray
    beam_orientation_jacobian: np.ndarray
    reference_point_m: tuple[float, float, float]
    unscaled_section_normal_condition: float

    def gap(self, displacement: dict[int, np.ndarray]) -> np.ndarray:
        values = np.array([displacement[node] for node in self.node_ids],
                          dtype=float).ravel()
        if values.shape != (3*len(self.node_ids),) or not np.isfinite(values).all():
            raise ValueError("complete finite solid line displacement required")
        return self.gap_jacobian@values

    def nodal_actions(self, dual: np.ndarray) -> dict[int, np.ndarray]:
        physical = np.asarray(dual, dtype=float)
        if physical.shape != (6,) or not np.isfinite(physical).all():
            raise ValueError("six finite physical line duals required")
        values = (self.gap_jacobian.T@physical).reshape(-1, 3)
        return {node: values[i].copy() for i, node in enumerate(self.node_ids)}


def build_flat_solid_line_port(coords: dict[int, np.ndarray],
                               plate_nodes: set[int], bar_nodes: set[int],
                               station_x_m: float, *,
                               x_edges=(.9, .925, .95, .975, 1.),
                               y_edges=tuple(np.linspace(-.05, .05, 9)),
                               shell_thickness_m=.035,
                               beam_depth_m=.1) -> FlatSolidLinePort:
    """Construct a reference-linear six-channel map at one straight station.

    The Q8 face sampling uses a fixed x cell. The bar cross-section's
    width-integrated rigid pose is a physical observable; its transpose
    distributes a dual through the same least-squares map.
    """
    x_grid = np.asarray(x_edges, dtype=float)
    y_grid = np.asarray(y_edges, dtype=float)
    if (x_grid.ndim != 1 or y_grid.ndim != 1 or
            len(x_grid) < 2 or len(y_grid) < 2 or
            not np.isfinite(x_grid).all() or not np.isfinite(y_grid).all() or
            np.any(np.diff(x_grid) <= 0.) or np.any(np.diff(y_grid) <= 0.) or
            not np.isfinite(station_x_m) or
            not x_grid[0] < station_x_m < x_grid[-1] or
            0. not in y_grid or
            shell_thickness_m <= 0. or beam_depth_m <= 0.):
        raise ValueError("bounded flat material-line face grid required")
    if plate_nodes & bar_nodes:
        raise ValueError("detached solid sides required")
    cell_x = int(np.searchsorted(x_grid, station_x_m, side="right")-1)
    if not x_grid[cell_x] < station_x_m < x_grid[cell_x+1]:
        raise ValueError("station must be inside one solid face x cell")
    x0, x1 = x_grid[cell_x:cell_x+2]
    xi = 2.*(station_x_m-x0)/(x1-x0)-1.
    center_cell = int(np.searchsorted(y_grid, 0., side="left")-1)
    if center_cell < 0:
        raise ValueError("material center line left face grid")

    def lookup(domain):
        found = {}
        for node in domain:
            key = tuple(np.round(coords[node], 9))
            if key in found:
                raise ValueError("duplicate solid face coordinate")
            found[key] = node
        return found

    plate_lookup = lookup(plate_nodes)
    bar_lookup = lookup(bar_nodes)

    def face(known, z, y0, y1, y):
        ym = (y0+y1)/2.
        locations = ((x0, y0), (x1, y0), (x1, y1), (x0, y1),
                     ((x0+x1)/2., y0), (x1, ym),
                     ((x0+x1)/2., y1), (x0, ym))
        ids = []
        for px, py in locations:
            key = tuple(np.round((px, py, z), 9))
            if key not in known:
                raise ValueError("missing Q8 solid face node")
            ids.append(known[key])
        eta = 2.*(y-y0)/(y1-y0)-1.
        return tuple(ids), _quad8_shape(xi, eta), _quad8_dx(xi, eta, x1-x0)

    yc0, yc1 = y_grid[center_cell:center_cell+2]
    top = face(plate_lookup, shell_thickness_m/2., yc0, yc1, 0.)
    bottom = face(plate_lookup, -shell_thickness_m/2., yc0, yc1, 0.)
    roots, gauss = np.polynomial.legendre.leggauss(3)
    samples = []
    for side, z in (("bottom", shell_thickness_m/2.),
                    ("top", shell_thickness_m/2.+beam_depth_m)):
        for y0, y1 in zip(y_grid[:-1], y_grid[1:]):
            for eta, weight in zip(roots, gauss):
                y = (y0+y1)/2.+(y1-y0)*float(eta)/2.
                ids, shape, _ = face(bar_lookup, z, y0, y1, y)
                offset = np.array((0., y,
                                   -beam_depth_m/2. if side == "bottom"
                                   else beam_depth_m/2.))
                samples.append((ids, shape, (y1-y0)*float(weight)/2., offset))
    nodes = tuple(sorted(set(top[0]) | set(bottom[0]) |
                         {node for ids, _, _, _ in samples for node in ids}))
    index = {node: i for i, node in enumerate(nodes)}
    width = 3*len(nodes)

    def interpolation(ids, shape):
        result = np.zeros((3, width))
        for node, value in zip(ids, shape):
            result[:, 3*index[node]:3*index[node]+3] += value*np.eye(3)
        return result

    shell_top = interpolation(top[0], top[1])
    shell_bottom = interpolation(bottom[0], bottom[1])
    top_dx = interpolation(top[0], top[2])
    shell_rotation = np.zeros((3, width))
    shell_rotation[0] = -(shell_top[1]-shell_bottom[1])/shell_thickness_m
    shell_rotation[1] = (shell_top[0]-shell_bottom[0])/shell_thickness_m
    shell_rotation[2] = top_dx[1]

    normal = np.zeros((6, 6))
    right = np.zeros((6, width))
    for ids, shape, weight, offset in samples:
        rigid = np.column_stack((np.eye(3), -_skew(offset)))
        sample = interpolation(ids, shape)
        normal += weight*rigid.T@rigid
        right += weight*rigid.T@sample
    singular = np.linalg.svd(normal, compute_uv=False)
    if singular[-1] <= 0. or singular[0]/singular[-1] > 1e12:
        raise ValueError("solid bar section fit is degenerate")
    beam_pose = np.linalg.solve(normal, right)
    bottom_offset = np.array((0., 0., -beam_depth_m/2.))
    beam_bottom = np.column_stack((np.eye(3), -_skew(bottom_offset)))@beam_pose
    beam_rotation = beam_pose[3:]
    gap = np.vstack((shell_top-beam_bottom,
                     beam_rotation-shell_rotation))
    reference = (float(station_x_m), 0., float(shell_thickness_m/2.))
    plate_coordinates = np.array([coords[node] for node in top[0]])
    bar_coordinates = np.array([coords[node] for node in samples[0][0]])
    if (np.linalg.norm(top[1]@plate_coordinates-np.array(reference)) > 1e-10 or
            abs(bar_coordinates[:, 2].mean()-reference[2]) > 1e-10):
        raise ValueError("solid reference material-line position changed")
    for array in (gap, shell_top, shell_rotation, beam_bottom, beam_rotation):
        array.setflags(write=False)
    return FlatSolidLinePort(float(station_x_m), nodes, gap, shell_top,
                             shell_rotation, beam_bottom, beam_rotation,
                             reference, float(singular[0]/singular[-1]))


def evaluate_saved_reference() -> dict:
    """Check the new observable against the pinned detached F4 geometry."""
    from hashlib import sha256
    import json
    from pathlib import Path
    import subprocess

    from scripts.b3_e4_f03_c1_solid_trace_residual import RECON, SOURCE
    from scripts.b3_e4_f03_ccx_six_channel_compliance import _source
    from scripts.b3_e4_f03_ccx_six_channel_preflight import _element_domain_nodes
    from scripts.b3_e4_f03_ccx_solid_bond_screen import digest

    root = Path(__file__).resolve().parents[1]
    reconstruction = json.loads(RECON.read_text())
    if reconstruction["status"] != "EXPLORATORY_COMPLETE":
        raise ValueError("completed detached solid reference required")
    deck, _, coords, _, _, _ = _source(SOURCE / "tip_mx")
    if digest(deck) != reconstruction["cases"]["tip_mx"]["source_deck_sha256"]:
        raise ValueError("detached solid source deck changed")
    plate, bar = _element_domain_nodes(deck)
    examples = []
    for station in (.9125, .9375, .9875):
        port = build_flat_solid_line_port(coords, plate, bar, station)
        rigid_gap = 0.
        for direction in np.eye(6):
            displacement = {
                node: direction[:3]+np.cross(direction[3:], coords[node])
                for node in port.node_ids
            }
            rigid_gap = max(rigid_gap, float(np.max(np.abs(port.gap(displacement)))))
        dual = np.array((4., -6., 8., 100., -70., 30.))
        actions = port.nodal_actions(dual)
        total_force = sum(actions.values(), np.zeros(3))
        center = np.asarray(port.reference_point_m)
        total_moment = sum((np.cross(coords[node]-center, value)
                            for node, value in actions.items()), np.zeros(3))
        plate_force = sum((value for node, value in actions.items()
                           if node in plate), np.zeros(3))
        bar_force = sum((value for node, value in actions.items()
                         if node in bar), np.zeros(3))
        displacement = {node: np.array((.01*np.sin(node), .02*np.cos(node),
                                        .005*np.sin(2*node)))
                        for node in port.node_ids}
        work = sum(float(force@displacement[node])
                   for node, force in actions.items())
        work_defect = abs(work-dual@port.gap(displacement))
        if (rigid_gap > 1e-10 or np.linalg.norm(total_force) > 1e-9 or
                np.linalg.norm(total_moment) > 1e-9 or
                np.linalg.norm(plate_force+bar_force) > 1e-9 or
                work_defect > 1e-11 or
                np.linalg.matrix_rank(port.gap_jacobian, tol=1e-10) != 6):
            raise ArithmeticError("actual solid material-line work preflight failed")
        examples.append({
            "station_x_m": station,
            "active_face_nodes": len(port.node_ids),
            "six_row_rank": 6,
            "unscaled_section_normal_condition": port.unscaled_section_normal_condition,
            "maximum_common_rigid_gap": rigid_gap,
            "global_force_imbalance_n": float(np.linalg.norm(total_force)),
            "global_moment_imbalance_nm": float(np.linalg.norm(total_moment)),
            "side_force_imbalance_n": float(np.linalg.norm(plate_force+bar_force)),
            "transpose_work_defect_j": float(work_defect),
        })
    sources = ("scripts/b3_e4_f03_c1_material_line_solid_port.py",
               "scripts/b3_e4_f03_ccx_solid_bond_screen.py",
               "scripts/b3_e4_f03_ccx_six_channel_compliance.py",
               "scripts/b3_e4_f03_ccx_six_channel_preflight.py")
    return {
        "classification": "flat-reference solid material-line pose/work preflight",
        "status": "DEVELOPMENT_PREFLIGHT_PASSED",
        "source_commit": subprocess.check_output(
            ("git", "rev-parse", "HEAD"), cwd=root, text=True).strip(),
        "source_sha256": {name: sha256((root/name).read_bytes()).hexdigest()
                          for name in sources},
        "reference_reconstruction_sha256": digest(RECON),
        "source_deck_sha256": digest(deck),
        "stations": examples,
        "limitations": [
            "no external action solve or native/solid accuracy comparison",
            "beam section uses a declared width-integrated rigid projection",
            "unscaled section normal condition mixes SI translation/rotation units and is not a stability measure",
            "flat small-motion pose; finite rotation and material-line multiplier space remain open",
            "not F03 or G0B acceptance",
        ],
    }


if __name__ == "__main__":
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve existing material-line solid preflight")
    result = evaluate_saved_reference()
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True,
                                      allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps({"status": result["status"],
                      "stations": len(result["stations"]),
                      "output": str(args.output)}))
