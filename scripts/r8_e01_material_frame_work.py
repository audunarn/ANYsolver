"""Source-only E01 linear material-frame/work-map feasibility diagnostic.

This distinct recovered-frame law is NOT the native six-row nodal-pose law,
an adopted connection, a finite-rotation map or an external accuracy oracle.
No solver is imported or executed. Coordinates are SI in the global XY frame.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np


IDENTITY = "R8_E01_LINEAR_POLAR_SPIN_INDEPENDENT_DIRECTOR_WORK_V1_DEV"


def _finite(value, shape, label):
    if np.iscomplexobj(value):
        raise ValueError(f"real {label} required")
    array = np.asarray(value, dtype=float)
    if array.shape != shape or not np.isfinite(array).all():
        raise ValueError(f"finite {label} with shape {shape} required")
    return array


def cross_matrix(vector):
    """Matrix [v]x with [v]x @ a = v cross a."""
    x, y, z = _finite(vector, (3,), "vector")
    return np.array(((0., -z, y), (z, 0., -x), (-y, x, 0.)))


def rectangular_patch(xy, station):
    """Q4 N and physical derivatives at an explicitly chosen host/station.

    Corner order is lower-left, lower-right, upper-right, upper-left. An edge
    station uses this host's one-sided derivative; no incident-host averaging.
    """
    xy = _finite(xy, (4, 2), "XY rectangle corners")
    x0, y0 = xy[0]
    x1, y1 = xy[2]
    if not (x1 > x0 and y1 > y0) or not np.array_equal(
            xy, np.array(((x0, y0), (x1, y0), (x1, y1), (x0, y1)))):
        raise ValueError("ordered nondegenerate Cartesian XY rectangle required")
    x, y = _finite(station, (2,), "station")
    if not (x0 <= x <= x1 and y0 <= y <= y1):
        raise ValueError("station outside declared host")
    a, b = (x-x0)/(x1-x0), (y-y0)/(y1-y0)
    n = np.array(((1-a)*(1-b), a*(1-b), a*b, (1-a)*b))
    dx = np.array((-(1-b), 1-b, b, -b))/(x1-x0)
    dy = np.array((-(1-a), -a, a, 1-a))/(y1-y0)
    return n, dx, dy


def _port_shift(offset):
    shift = np.eye(6)
    # u_port = u_station + omega cross offset.
    shift[:3, 3:] = -cross_matrix(offset)
    return shift


def shell_material_frame_map(xy, station, offset=(0., 0., 0.)):
    """6x24 linear map for [u(3), theta(3)] at four shell corners.

    Director tilt is interpolated from independent theta_x/theta_y. Yaw is
    the infinitesimal polar spin of the in-plane displacement gradient.
    Nodal theta_z is deliberately absent; this is a different connection law.
    """
    n, dx, dy = rectangular_patch(xy, station)
    matrix = np.zeros((6, 24))
    for i in range(4):
        matrix[:3, 6*i:6*i+3] = n[i]*np.eye(3)
        matrix[3, 6*i+3] = n[i]
        matrix[4, 6*i+4] = n[i]
        matrix[5, 6*i] = -.5*dy[i]
        matrix[5, 6*i+1] = .5*dx[i]
    return _port_shift(offset) @ matrix


def native_nodal_pose_map(node_count, station_node, offset=(0., 0., 0.)):
    """Unchanged reference rigid-arm map using the selected nodal rotation."""
    if type(node_count) is not int or type(station_node) is not int or not (
            node_count > 0 and 0 <= station_node < node_count):
        raise ValueError("valid node count and zero-based station node required")
    matrix = np.zeros((6, 6*node_count))
    matrix[:, 6*station_node:6*station_node+6] = _port_shift(offset)
    return matrix


def expanded_material_frame_map(xy, station, thickness, offset=(0., 0., 0.)):
    """7x24 map for four explicitly paired lower/upper face translations.

    Input order: [lower u(3), upper u(3)] at each Q4 corner. Output is port
    translation, independent director tilt/polar spin, and thickness strain.
    This accepts prescribed pairs, not a claim that CCX expansion supplies
    these degrees of freedom independently or matches the shell stiffness.
    """
    if (isinstance(thickness, (bool, np.bool_)) or not np.isscalar(thickness) or
            np.iscomplexobj(thickness) or not np.isfinite(thickness) or thickness <= 0):
        raise ValueError("positive finite reference thickness required")
    n, dx, dy = rectangular_patch(xy, station)
    matrix = np.zeros((7, 24))
    for i in range(4):
        for face, sign in ((0, -1.), (1, 1.)):
            j = 6*i+3*face
            matrix[:3, j:j+3] = .5*n[i]*np.eye(3)
            matrix[3, j+1] = -sign*n[i]/thickness
            matrix[4, j] = sign*n[i]/thickness
            matrix[5, j] = -.25*dy[i]
            matrix[5, j+1] = .25*dx[i]
            matrix[6, j+2] = sign*n[i]/thickness
    matrix[:6] = _port_shift(offset) @ matrix[:6]
    return matrix


def adjoint_wrench(matrix, wrench):
    """Exact linear transpose; preserves all entries, including support work.

    A 7-vector's final entry is conjugate to dimensionless thickness strain,
    hence has units joules. No multiplier is interpreted as a physical wrench.
    """
    matrix = np.asarray(matrix, dtype=float)
    if matrix.ndim != 2 or not np.isfinite(matrix).all():
        raise ValueError("finite two-dimensional work map required")
    return matrix.T @ _finite(wrench, (matrix.shape[0],), "port wrench")


def shell_channels(xy, station, shell_q):
    """Report independent director minus surface normal, and yaw mismatch."""
    q = _finite(shell_q, (4, 6), "shell corner field")
    n, dx, dy = rectangular_patch(xy, station)
    rotation = shell_material_frame_map(xy, station)[3:] @ q.ravel()
    director_xy = np.array((rotation[1], -rotation[0]))
    normal_xy = -np.array((dx @ q[:, 2], dy @ q[:, 2]))
    return dict(material_rotation=rotation.tolist(),
                independent_director_xy=director_xy.tolist(),
                surface_normal_xy=normal_xy.tolist(),
                transverse_shear= (director_xy-normal_xy).tolist(),
                nodal_yaw_minus_material_spin=float(n @ q[:, 5]-rotation[2]))


def diagnose_e01_capture(capture):
    """Apply explicit 8x4 E01 lower-edge hosts to an existing captured field.

    The caller supplies the capture; absent source fields are never synthesized
    from the retained cross-work summary. No physical comparison is scored.
    """
    if (type(capture.get("shell_intervals")) is not int or
            type(capture.get("transverse_intervals")) is not int or
            capture["shell_intervals"] != 8 or capture["transverse_intervals"] != 4):
        raise ValueError("explicit 8x4 E01 capture identity required")
    fields = [(key, capture[key]) for key in (
        "native_coupled_shell_displacements", "external_coupled_shell_displacements")
        if key in capture]
    if len(fields) != 1:
        raise ValueError("exactly one originating coupled shell field required")
    label, field = fields[0]
    expected = {str(i) for i in range(1, 46)}
    if set(field) != expected:
        raise ValueError("complete explicitly identified 8x4 E01 field required")
    q = {int(i): _finite(v, (6,), "captured shell coordinate") for i, v in field.items()}
    roots = tuple(1+9*j for j in range(5))
    root_max = max(float(np.max(np.abs(q[i]))) for i in roots)
    # Existing saved cross-work discriminator uses this bound for root fields;
    # it is not a new support/equilibrium acceptance threshold.
    if root_max >= 1e-12:
        raise ValueError("saved E01 root-field guard failed")
    samples = []
    for station in range(9):
        host = min(station, 7)
        ids = (host+1, host+2, host+11, host+10)
        xy = ((host/4, -.5), ((host+1)/4, -.5),
              ((host+1)/4, -.25), (host/4, -.25))
        samples.append(dict(shell_node=station+1, host_nodes=list(ids),
            **shell_channels(xy, (station/4, -.5), np.array([q[i] for i in ids]))))
    return dict(originating_field=label, samples=samples,
                root_nodes=list(roots), root_coordinate_max=root_max,
                classification="KINEMATIC_MISMATCH_DIAGNOSTIC_ONLY",
                limitation="Saved nodal coordinates do not identify physical CCX director/spin or sided forces.")


def read_bound_capture(path, expected_sha256):
    path = Path(path)
    if any("us3-modal-canary" in part.lower() for part in path.parts):
        raise ValueError("protected evidence is outside this diagnostic")
    if (len(expected_sha256) != 64 or
            any(c not in "0123456789abcdef" for c in expected_sha256)):
        raise ValueError("canonical expected SHA256 required")
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("originating capture hash mismatch")
    return dict(path=str(path), sha256=expected_sha256,
                diagnostic=diagnose_e01_capture(json.loads(raw)))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="append", type=Path, required=True)
    parser.add_argument("--expected-sha256", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        raise FileExistsError("preserve existing diagnostic output")
    if len(args.capture) != len(args.expected_sha256):
        raise ValueError("one expected SHA256 per capture, in the same order, required")
    records = [read_bound_capture(path, expected) for path, expected in
               zip(args.capture, args.expected_sha256, strict=True)]
    record = dict(identity=IDENTITY, qualified=False,
                  source_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
                  captures=records, external_accuracy_scored=False)
    args.output.write_text(json.dumps(record, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    return record


if __name__ == "__main__":
    record = main()
    print(json.dumps(dict(identity=record["identity"], captures=len(record["captures"]),
                          qualified=False, external_accuracy_scored=False)))
