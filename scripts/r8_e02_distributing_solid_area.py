"""Independent linear area observable on resolved Cartesian C3D20(R) solids.

This is a work map, not a deck, solver, weld or rigid-patch constraint. The
director is a top/bottom displacement secant; it is not the 3D polar rotation.
Normal spin is half the midsurface in-plane curl. Transposed actions can act
on midsurface, perimeter and top/bottom interpolation nodes. No native solver
operator, finite pose, external accuracy or qualification is supplied here.
"""
from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass
from hashlib import sha256
import json
import math
from collections.abc import Mapping

import numpy as np


LAW = "RESOLVED_CARTESIAN_C3D20_AREA_SECANT_DIRECTOR_POLAR_YAW_LINEAR_V1_DEV"
MAX_ELEMENTS = 4096
MAX_NODES = 30_000
MAX_PARTITIONS = 100_000
_GEOMETRY_RELATIVE_TOLERANCE = 64 * np.finfo(float).eps
_CORNERS = ((-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
            (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1))
_EDGES = ((0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6),
          (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7))
_REFERENCE = _CORNERS + tuple(tuple((a + b) // 2 for a, b in
                                   zip(_CORNERS[i], _CORNERS[j]))
                             for i, j in _EDGES)
_GAUSS = ((-math.sqrt(3 / 5), 5 / 9), (0., 8 / 9),
          (math.sqrt(3 / 5), 5 / 9))


def _vector(value, count, name):
    try:
        entries = tuple(value)
        if any(isinstance(v, (bool, np.bool_)) or
               not (type(v) in (int, float) or isinstance(v, (np.integer, np.floating)))
               for v in entries):
            raise ValueError(f"finite real scalar entries required for {name}")
        result = tuple(float(v) for v in entries)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"finite {name} required") from exc
    if len(result) != count or not all(math.isfinite(v) for v in result):
        raise ValueError(f"finite {name} of length {count} required")
    return result


def _identifier(value):
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or value <= 0:
        raise ValueError("positive integer node/element identities required")
    return int(value)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _sum(values):
    try:
        result = math.fsum(values)
    except (OverflowError, ValueError) as exc:
        raise ValueError("finite representable work-map accumulation required") from exc
    if not math.isfinite(result):
        raise ValueError("finite representable work-map accumulation required")
    return result


def _shape(reference):
    """Independent 20-node serendipity shape and reference derivatives."""
    r = _vector(reference, 3, "reference position")
    shape, derivative = np.zeros(20), np.zeros((20, 3))
    for i, signs in enumerate(_REFERENCE):
        if i < 8:
            factors = tuple(1 + s * x for s, x in zip(signs, r))
            tail = sum(s * x for s, x in zip(signs, r)) - 2
            product = math.prod(factors)
            shape[i] = product * tail / 8
            for axis in range(3):
                derivative[i, axis] = signs[axis] * (
                    math.prod(factors[j] for j in range(3) if j != axis) * tail
                    + product) / 8
        else:
            active = signs.index(0)
            others = tuple(j for j in range(3) if j != active)
            factors = {j: 1 + signs[j] * r[j] for j in others}
            product = math.prod(factors.values())
            shape[i] = (1 - r[active] ** 2) * product / 4
            derivative[i, active] = -r[active] * product / 2
            for axis in others:
                derivative[i, axis] = ((1 - r[active] ** 2) * signs[axis]
                                      * factors[next(j for j in others if j != axis)] / 4)
    return shape, derivative


def _brick(connectivity, nodes):
    try:
        ids = tuple(_identifier(v) for v in connectivity)
    except TypeError as exc:
        raise ValueError("ordered 20-node brick required") from exc
    if len(ids) != 20 or len(set(ids)) != 20 or any(v not in nodes for v in ids):
        raise ValueError("distinct existing ordered 20-node brick required")
    xyz = tuple(nodes[v] for v in ids)
    low = tuple(min(p[j] for p in xyz) for j in range(3))
    high = tuple(max(p[j] for p in xyz) for j in range(3))
    span = tuple(b - a for a, b in zip(low, high))
    if not all(math.isfinite(v) and v > 0 for v in span):
        raise ValueError("positive Cartesian brick lengths required")
    # World-coordinate rounding must be negligible relative to the actual
    # cell lengths. A large origin cannot make a distorted midside admissible.
    if any(max(math.ulp(a), math.ulp(b)) / h > _GEOMETRY_RELATIVE_TOLERANCE
           for a, b, h in zip(low, high, span)):
        raise ValueError("unresolved Cartesian world-ULP/span conditioning")
    centre = tuple(a + h / 2 for a, h in zip(low, span))
    tolerance = tuple(_GEOMETRY_RELATIVE_TOLERANCE * h for h in span)
    if not all(math.isfinite(tol) and tol > 0 for tol in tolerance):
        raise ValueError("representable Cartesian geometric residual scale required")
    for point, reference in zip(xyz, _REFERENCE):
        expected = tuple(c + h * r / 2 for c, h, r in zip(centre, span, reference))
        if any(abs(a - b) > tol for a, b, tol in zip(point, expected, tolerance)):
            raise ValueError("C3D20 Cartesian geometry/order mismatch or distorted brick")
    # Coordinate reproduction is checked against the actual submitted nodes,
    # including derivatives; local tables only, never a global dense operator.
    actual = np.asarray(xyz) - np.asarray(centre)
    for reference in ((0., 0., 0.), (.31, -.23, .47)):
        shape, gradient = _shape(reference)
        expected = np.asarray(span) * reference / 2
        if (np.any(np.abs(shape @ actual - expected) > np.asarray(tolerance) * 2)
                or np.any(np.abs(gradient.T @ actual - np.diag(np.asarray(span) / 2))
                          > np.asarray(tolerance)[None, :] * 2)):
            raise ValueError("actual brick coordinate reproduction failed")
    return ids, low, high, centre, span


def _conforming_faces(coverage, bricks):
    """Check only adjacent clipped partitions; cache each shared donor face."""
    checked = set()
    for partition, element in coverage.items():
        for axis in range(3):
            neighbour = list(partition)
            neighbour[axis] += 1
            other = coverage.get(tuple(neighbour))
            if other is None or other == element:
                continue
            pair = (min(element, other), max(element, other), axis)
            if pair in checked:
                continue
            left, right = bricks[element], bricks[other]
            if (left[2][axis] != right[1][axis] or
                    any(left[1][j] != right[1][j] or left[2][j] != right[2][j]
                        for j in range(3) if j != axis)):
                raise ValueError("nonconforming solid face extents across pad partition")
            left_ids = frozenset(node for node, reference in zip(left[0], _REFERENCE)
                                 if reference[axis] == 1)
            right_ids = frozenset(node for node, reference in zip(right[0], _REFERENCE)
                                  if reference[axis] == -1)
            if len(left_ids) != 8 or left_ids != right_ids:
                raise ValueError("nonconforming shared solid face-node identities")
            checked.add(pair)


def _field(displacements, node_ids):
    if not isinstance(displacements, Mapping):
        raise ValueError("node-indexed physical displacement mapping required")
    try:
        return tuple(_vector(displacements[n], 3, "nodal displacement") for n in node_ids)
    except KeyError as exc:
        raise ValueError("complete area displacement inventory required") from exc


@dataclass(frozen=True)
class AreaIncrement:
    mean_translation_m: tuple
    rotation_components_rad: tuple
    port_translation_m: tuple
    map_identity: str


@dataclass(frozen=True)
class SolidAreaAction:
    """Applied forces, owned immutable tuples; no rotational solid DOFs."""
    node_ids: tuple
    coordinates_m: tuple
    forces_n: tuple
    map_identity: str

    def work(self, displacements):
        values = _field(displacements, self.node_ids)
        return _sum(f * u for force, value in zip(self.forces_n, values)
                    for f, u in zip(force, value))

    def resultant(self, origin_m=(0., 0., 0.)):
        origin = _vector(origin_m, 3, "moment origin")
        force = tuple(_sum(f[j] for f in self.forces_n) for j in range(3))
        moments = tuple(_cross(tuple(x - o for x, o in zip(point, origin)), f)
                        for point, f in zip(self.coordinates_m, self.forces_n))
        moment = tuple(_sum(m[j] for m in moments) for j in range(3))
        return (_vector(force, 3, "resultant force"),
                _vector(moment, 3, "resultant moment"))


@dataclass(frozen=True)
class SolidAreaMap:
    """Sparse node -> six-by-three immutable weights for one area observable."""
    law: str
    identity: str
    bounds_xy_m: tuple
    thickness_m: float
    area_m2: float
    centroid_m: tuple
    port_m: tuple
    node_ids: tuple
    coordinates_m: tuple
    weights: tuple
    midsurface_owner_elements: tuple

    def recover(self, displacements):
        values = _field(displacements, self.node_ids)
        result = _vector(tuple(_sum(w[row][j] * value[j]
                                    for w, value in zip(self.weights, values)
                                    for j in range(3)) for row in range(6)),
                         6, "area observable")
        arm = tuple(p - c for p, c in zip(self.port_m, self.centroid_m))
        spin = _cross(result[3:], arm)
        port = _vector(tuple(a + b for a, b in zip(result[:3], spin)),
                       3, "port translation")
        return AreaIncrement(result[:3], result[3:], port, self.identity)

    def action(self, force_n, moment_nm):
        force = _vector(force_n, 3, "port force")
        moment = _vector(moment_nm, 3, "port moment")
        arm = tuple(p - c for p, c in zip(self.port_m, self.centroid_m))
        eccentric = _cross(arm, force)
        wrench = _vector(force + tuple(a + b for a, b in zip(moment, eccentric)),
                         6, "centroid wrench")
        forces = tuple(_vector(tuple(_sum(w[row][j] * wrench[row]
                                         for row in range(6)) for j in range(3)),
                               3, "transposed nodal force") for w in self.weights)
        return SolidAreaAction(self.node_ids, self.coordinates_m, forces, self.identity)


def compile_area_map(nodes, elements, bounds_xy_m, thickness_m, port_m):
    """Compile one rectangle at z=0 with secants at z=+/-thickness/2.

    All input bricks must have the actual canonical C3D20 node order and
    axis-aligned affine Cartesian geometry. Clipped volume partitions prove
    unique complete coverage of the declared pad and thickness. At a shared
    face, full face extents and all eight node identities must match. At a shared
    thickness interface the lower brick owns the midsurface trace. Three-point
    Gauss quadrature in each in-plane direction integrates the admitted shape
    polynomials exactly. This does not admit distorted or curved bricks.
    """
    if (not isinstance(nodes, Mapping) or not 1 <= len(nodes) <= MAX_NODES
            or not isinstance(elements, Mapping) or not 1 <= len(elements) <= MAX_ELEMENTS):
        raise ValueError("bounded nonempty solid node/element mappings required")
    owned_nodes = {_identifier(n): _vector(p, 3, "node position") for n, p in nodes.items()}
    bounds = _vector(bounds_xy_m, 4, "pad bounds")
    thickness = _vector((thickness_m,), 1, "thickness")[0]
    port = _vector(port_m, 3, "port position")
    xmin, xmax, ymin, ymax = bounds
    area = (xmax - xmin) * (ymax - ymin)
    if (thickness <= 0 or xmax <= xmin or ymax <= ymin
            or not math.isfinite(area) or area <= 0 or thickness / 2 == 0):
        raise ValueError("positive representable pad area/thickness required")
    domain_low, domain_high = (xmin, ymin, -thickness / 2), (xmax, ymax, thickness / 2)
    bricks, clips = {}, {}
    cuts = [set((a, b)) for a, b in zip(domain_low, domain_high)]
    for element, incidence in sorted(elements.items(), key=lambda item: _identifier(item[0])):
        element = _identifier(element)
        brick = _brick(incidence, owned_nodes)
        low = tuple(max(a, b) for a, b in zip(brick[1], domain_low))
        high = tuple(min(a, b) for a, b in zip(brick[2], domain_high))
        if all(a < b for a, b in zip(low, high)):
            bricks[element], clips[element] = brick, (low, high)
            for j in range(3):
                cuts[j].update((low[j], high[j]))
    cuts = tuple(tuple(sorted(values)) for values in cuts)
    count = math.prod(len(values) - 1 for values in cuts)
    if count > MAX_PARTITIONS:
        raise ValueError("clipped coverage partition budget exceeded")
    indices = tuple({v: i for i, v in enumerate(values)} for values in cuts)
    coverage = {}
    for element, (low, high) in clips.items():
        ranges = tuple(range(indices[j][low[j]], indices[j][high[j]]) for j in range(3))
        for ix in ranges[0]:
            for iy in ranges[1]:
                for iz in ranges[2]:
                    key = (ix, iy, iz)
                    if key in coverage:
                        raise ValueError("overlapping/ambiguous solid pad coverage")
                    coverage[key] = element
    if len(coverage) != count:
        raise ValueError("incomplete solid pad/thickness coverage")
    _conforming_faces(coverage, bricks)
    midpoint_layer = bisect_left(cuts[2], 0.) - 1
    if midpoint_layer < 0 or not cuts[2][midpoint_layer] <= 0 <= cuts[2][midpoint_layer + 1]:
        raise ValueError("midsurface trace not covered")
    global_weights, owners = {}, set()
    for ix in range(len(cuts[0]) - 1):
        for iy in range(len(cuts[1]) - 1):
            donors = (coverage[ix, iy, midpoint_layer], coverage[ix, iy, 0],
                      coverage[ix, iy, len(cuts[2]) - 2])
            owners.add(donors[0])
            local = {element: np.zeros((6, 60)) for element in set(donors)}
            x0, x1 = cuts[0][ix:ix + 2]
            y0, y1 = cuts[1][iy:iy + 2]
            for gx, wx in _GAUSS:
                for gy, wy in _GAUSS:
                    x, y = x0 + (gx + 1) * (x1 - x0) / 2, y0 + (gy + 1) * (y1 - y0) / 2
                    weight = wx * wy * ((x1 - x0) / (xmax - xmin)) * ((y1 - y0) / (ymax - ymin)) / 4
                    for plane, element in enumerate(donors):
                        _, _, _, centre, span = bricks[element]
                        z = (0., -thickness / 2, thickness / 2)[plane]
                        reference = tuple(2 * (p - c) / h for p, c, h in zip((x, y, z), centre, span))
                        shape, gradient = _shape(reference)
                        gradient *= 2 / np.asarray(span)
                        table = local[element]
                        if plane == 0:
                            for axis in range(3):
                                table[axis, axis::3] += weight * shape
                            table[5, 0::3] -= .5 * weight * gradient[:, 1]
                            table[5, 1::3] += .5 * weight * gradient[:, 0]
                        else:
                            signed = (-1 if plane == 1 else 1) * weight / thickness
                            table[3, 1::3] -= signed * shape
                            table[4, 0::3] += signed * shape
            for element in sorted(local):
                for slot, node in enumerate(bricks[element][0]):
                    contribution = local[element][:, 3 * slot:3 * slot + 3]
                    if np.any(contribution):
                        global_weights.setdefault(node, np.zeros((6, 3)))[:] += contribution
    node_ids = tuple(sorted(global_weights))
    coordinates = tuple(owned_nodes[n] for n in node_ids)
    weights = tuple(tuple(_vector(row, 3, "area map weight") for row in global_weights[n]) for n in node_ids)
    centroid = (xmin + (xmax - xmin) / 2, ymin + (ymax - ymin) / 2, 0.)
    centroid = _vector(centroid, 3, "area centroid")
    _vector(tuple(p - c for p, c in zip(port, centroid)), 3, "port eccentricity")
    payload = (LAW, bounds, thickness, port, node_ids, coordinates, weights, tuple(sorted(owners)))
    identity = sha256(json.dumps(payload, separators=(",", ":"), allow_nan=False).encode("ascii")).hexdigest()
    return SolidAreaMap(LAW, identity, bounds, thickness, area, centroid, port,
                        node_ids, coordinates, weights, tuple(sorted(owners)))
