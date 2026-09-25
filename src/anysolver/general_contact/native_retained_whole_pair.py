"""Internal two-cell native beam pair distributed potential and work map."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

import numpy as np

from anysolver._ge_beam3_centered_reference import (
    CenteredCurvedBeam3ReferenceGeometry,
)
from anysolver._ge_beam3_p5_seeded.core import sha

from .beam_curve_pair import (
    _GAUSS_8, _GAUSS_16, _bezier_controls, _curve,
    b3_distance_jet,
)
from .native_curve_union import NativeTwoCellUnionSearch
from .native_retained_curve_cell import NativeRetainedCurveCell
from .native_retained_station import _readonly


def _straight_join_owner(source: np.ndarray,
                         targets: tuple[np.ndarray, np.ndarray],
                         left: float, right: float,
                         accuracy_m: float) -> int | None:
    """Certify a target owner by the shared-junction Voronoi half-space.

    For collinear, forward-ordered straight cells, a source point on one
    side of the junction is at least as close to that side's cell as to
    the opposite cell. The Bezier hull encloses the whole source interval.
    """
    first, second = targets
    start, junction, end = first[0], first[2], second[2]
    span = end-start
    length = float(np.linalg.norm(span))
    roundoff = 256.0*np.finfo(float).eps*max(
        1.0, float(np.max(np.abs(source))),
        float(np.max(np.abs(first))), float(np.max(np.abs(second))),
    )
    if roundoff > accuracy_m or length <= roundoff:
        return None
    axis = span/length
    if (float(np.dot(junction-start, axis)) <= roundoff
            or float(np.dot(end-junction, axis)) <= roundoff):
        return None
    for cell in targets:
        if (float(np.linalg.norm(cell[1]-0.5*(cell[0]+cell[2]))) > roundoff
                or any(float(np.linalg.norm(
                    point-start-np.dot(point-start, axis)*axis,
                )) > roundoff for point in cell)):
            return None
    projections = [float(np.dot(point-junction, axis))
                   for point in _bezier_controls(source, left, right)]
    if max(projections) <= roundoff and min(projections) < -roundoff:
        return 0
    if min(projections) >= -roundoff and max(projections) > roundoff:
        return 1
    return None


def _straight_join_partitions(source: np.ndarray,
                              targets: tuple[np.ndarray, np.ndarray],
                              left: float, right: float,
                              accuracy_m: float,
                              ) -> tuple[tuple[float, float, int], ...] | None:
    """Split a Q2 source interval at its exact straight-target Voronoi crossings."""
    start, end = targets[0][0], targets[1][2]
    span = end-start
    length = float(np.linalg.norm(span))
    if length == 0.0:
        return None
    axis = span/length
    junction = targets[0][2]
    ordinates = np.array([float(np.dot(point-junction, axis))
                          for point in source])
    quadratic = 2.0*(ordinates[0]-2.0*ordinates[1]+ordinates[2])
    linear = -3.0*ordinates[0]+4.0*ordinates[1]-ordinates[2]
    constant = ordinates[0]
    scale = max(1.0, float(np.max(np.abs(ordinates))))
    roundoff = 256.0*np.finfo(float).eps*scale
    if roundoff > accuracy_m:
        return None
    if abs(quadratic) > roundoff:
        candidates = np.roots((quadratic, linear, constant))
    elif abs(linear) > roundoff:
        candidates = (-constant/linear,)
    else:
        candidates = ()
    boundaries = [left]
    for root in candidates:
        if abs(complex(root).imag) > roundoff:
            continue
        value = float(complex(root).real)
        if left+roundoff < value < right-roundoff:
            boundaries.append(value)
    boundaries.extend((right,))
    boundaries.sort()
    pieces = []
    for begin, stop in zip(boundaries[:-1], boundaries[1:]):
        if stop-begin <= roundoff:
            return None
        owner = _straight_join_owner(source, targets, begin, stop,
                                     accuracy_m)
        if owner is None:
            return None
        pieces.append((begin, stop, owner))
    return tuple(pieces)


def _straight_support_partitions(
    source: np.ndarray, targets: tuple[np.ndarray, np.ndarray],
    radius: float, left: float, right: float, accuracy_m: float,
) -> tuple[tuple[float, float, int], ...] | None:
    """Certify active line intervals for straight finite target geometry.

    The source is affine in station. Its squared distance to either physical
    endpoint or the target line is quadratic. Split first at the axial
    feature changes, then at every real activation root within each feature.
    A returned empty tuple proves this interval open. ``None`` means this
    exact straight profile does not apply and the caller must use its
    conservative general search route.
    """
    start, junction, end = targets[0][0], targets[0][2], targets[1][2]
    span = end-start
    length = float(np.linalg.norm(span))
    roundoff = 256.0*np.finfo(float).eps*max(
        1.0, float(np.max(np.abs(source))),
        *(float(np.max(np.abs(target))) for target in targets),
        radius,
    )
    if roundoff > accuracy_m or length <= roundoff:
        return None
    axis = span/length
    junction_axial = float(np.dot(junction-start, axis))
    if not roundoff < junction_axial < length-roundoff:
        return None
    for cell in targets:
        if (float(np.linalg.norm(cell[1]-0.5*(cell[0]+cell[2]))) > roundoff
                or any(float(np.linalg.norm(
                    point-start-np.dot(point-start, axis)*axis,
                )) > roundoff for point in cell)):
            return None
    if float(np.linalg.norm(source[1]-0.5*(source[0]+source[2]))) > roundoff:
        return None

    origin = source[0]
    direction = source[2]-source[0]
    axial_origin = float(np.dot(origin-start, axis))
    axial_direction = float(np.dot(direction, axis))
    boundaries = [left, right]
    if abs(axial_direction) > roundoff:
        for threshold in (0.0, junction_axial, length):
            root = (threshold-axial_origin)/axial_direction
            if left+roundoff < root < right-roundoff:
                boundaries.append(float(root))
    boundaries.sort()

    def add_roots(begin: float, stop: float) -> list[float]:
        middle = 0.5*(begin+stop)
        axial_middle = axial_origin+axial_direction*middle
        if axial_middle < 0.0:
            relative = origin-start
            slope = direction
        elif axial_middle > length:
            relative = origin-end
            slope = direction
        else:
            relative = origin-start-axial_origin*axis
            slope = direction-axial_direction*axis
        coefficients = (
            float(np.dot(slope, slope)),
            2.0*float(np.dot(relative, slope)),
            float(np.dot(relative, relative))-radius*radius,
        )
        if abs(coefficients[0]) > roundoff*roundoff:
            candidates = np.roots(coefficients)
        elif abs(coefficients[1]) > roundoff*roundoff:
            candidates = (-coefficients[2]/coefficients[1],)
        else:
            candidates = ()
        roots = []
        for candidate in candidates:
            if abs(complex(candidate).imag) > roundoff:
                continue
            root = float(complex(candidate).real)
            if begin+roundoff < root < stop-roundoff:
                roots.append(root)
        return roots

    activation = []
    for begin, stop in zip(boundaries[:-1], boundaries[1:]):
        activation.extend(add_roots(begin, stop))
    boundaries.extend(activation)
    boundaries.sort()
    pieces = []
    for begin, stop in zip(boundaries[:-1], boundaries[1:]):
        if stop-begin <= roundoff:
            return None
        middle = 0.5*(begin+stop)
        point = origin+middle*direction
        axial = axial_origin+middle*axial_direction
        nearest = start+np.clip(axial, 0.0, length)*axis
        difference = float(np.dot(point-nearest, point-nearest))-radius*radius
        if abs(difference) <= roundoff*roundoff:
            return None
        if difference < 0.0:
            owner = _straight_join_owner(source, targets, begin, stop,
                                         accuracy_m)
            if owner is None:
                return None
            pieces.append((begin, stop, owner))
    return tuple(pieces)


@dataclass(frozen=True)
class NativeRetainedWholePairResult:
    potential_j: float
    residual: np.ndarray
    tangent: np.ndarray
    beam_a_force_n: np.ndarray
    beam_b_force_n: np.ndarray
    beam_a_moment_nm: np.ndarray
    beam_b_moment_nm: np.ndarray
    conservative_lower_gap_m: float
    minimum_sampled_gap_m: float
    energy_error_j: float
    force_error_n: float
    tangent_error_n_per_m: float
    search_cells: int
    integration_intervals: int
    integration_evaluations: int
    unresolved_search_intervals: int


class NativeRetainedWholeCurvePair:
    """Symmetric distributed line contact over both cells of two native beams."""

    def __init__(self, element_a: int,
                 reference_a: CenteredCurvedBeam3ReferenceGeometry,
                 node_ids_a: tuple[int, int, int], radius_a_m: float,
                 element_b: int,
                 reference_b: CenteredCurvedBeam3ReferenceGeometry,
                 node_ids_b: tuple[int, int, int], radius_b_m: float, *,
                 line_stiffness_n_per_m2: float,
                 distance_tolerance_m: float,
                 feature_tolerance_m: float,
                 search_parameter_tolerance: float,
                 maximum_search_depth: int,
                 maximum_search_cells: int,
                 energy_tolerance_j: float,
                 force_tolerance_n: float,
                 tangent_tolerance_n_per_m: float,
                 maximum_integration_intervals: int):
        if (type(element_a) is not int or type(element_b) is not int
                or element_a <= 0 or element_b <= 0 or element_a == element_b):
            raise ValueError("native whole pair needs distinct beam identities")
        for label, ids in (("A", node_ids_a), ("B", node_ids_b)):
            if (type(ids) is not tuple or len(ids) != 3
                    or len(set(ids)) != 3
                    or any(type(value) is not int or value <= 0 for value in ids)):
                raise ValueError(f"native whole pair needs exact {label} node identities")
        if set(node_ids_a) & set(node_ids_b):
            raise ValueError("native whole pair does not admit shared material nodes")
        controls = (radius_a_m, radius_b_m, line_stiffness_n_per_m2,
                    distance_tolerance_m, feature_tolerance_m,
                    search_parameter_tolerance, energy_tolerance_j,
                    force_tolerance_n, tangent_tolerance_n_per_m)
        if any(type(value) not in (int, float) or not isfinite(value) or value <= 0.0
               for value in controls):
            raise ValueError("native whole pair needs positive dimensional controls")
        if (type(maximum_search_depth) is not int or maximum_search_depth < 0
                or type(maximum_search_cells) is not int or maximum_search_cells < 1
                or type(maximum_integration_intervals) is not int
                or maximum_integration_intervals < 1):
            raise ValueError("native whole pair needs finite resource budgets")
        self.cells_a = tuple(NativeRetainedCurveCell(element_a, reference_a, c)
                             for c in (0, 1))
        self.cells_b = tuple(NativeRetainedCurveCell(element_b, reference_b, c)
                             for c in (0, 1))
        self.node_ids_a = node_ids_a
        self.node_ids_b = node_ids_b
        self.radius_a = float(radius_a_m)
        self.radius_b = float(radius_b_m)
        self.radius = self.radius_a+self.radius_b
        self.stiffness = float(line_stiffness_n_per_m2)
        self.distance_tolerance = float(distance_tolerance_m)
        self.feature_tolerance = float(feature_tolerance_m)
        self.search_parameter_tolerance = float(search_parameter_tolerance)
        self.maximum_search_depth = maximum_search_depth
        self.maximum_search_cells = maximum_search_cells
        self.energy_tolerance = float(energy_tolerance_j)
        self.force_tolerance = float(force_tolerance_n)
        self.tangent_tolerance = float(tangent_tolerance_n_per_m)
        self.maximum_integration_intervals = maximum_integration_intervals
        identity = np.tile(np.eye(3), (2, 1, 1))
        self.reference_curves = tuple(
            cell.evaluate(reference.coordinates, np.zeros((3, 3)), identity).positions
            for cells, reference in ((self.cells_a, reference_a),
                                     (self.cells_b, reference_b))
            for cell in cells
        )
        self.identity = self._fingerprint()

    def _fingerprint(self) -> str:
        return sha(dict(
            profile="NATIVE_RETAINED_WHOLE_Q2_PAIR_DEV_V0",
            cells_a=[(cell.element_id, cell.cell,
                      cell.reference.canonical_data()) for cell in self.cells_a],
            cells_b=[(cell.element_id, cell.cell,
                      cell.reference.canonical_data()) for cell in self.cells_b],
            node_ids_a=self.node_ids_a, node_ids_b=self.node_ids_b,
            radius_a_m=self.radius_a, radius_b_m=self.radius_b,
            line_stiffness_n_per_m2=self.stiffness,
            distance_tolerance_m=self.distance_tolerance,
            feature_tolerance_m=self.feature_tolerance,
            search_parameter_tolerance=self.search_parameter_tolerance,
            maximum_search_depth=self.maximum_search_depth,
            maximum_search_cells=self.maximum_search_cells,
            energy_tolerance_j=self.energy_tolerance,
            force_tolerance_n=self.force_tolerance,
            tangent_tolerance_n_per_m=self.tangent_tolerance,
            maximum_integration_intervals=self.maximum_integration_intervals,
            reference_curves=self.reference_curves,
        ))

    def evaluate(self, positions_a: np.ndarray, position_low_a: np.ndarray,
                 cell_rotations_a: np.ndarray,
                 positions_b: np.ndarray, position_low_b: np.ndarray,
                 cell_rotations_b: np.ndarray) -> NativeRetainedWholePairResult:
        if self._fingerprint() != self.identity:
            raise ValueError("native whole pair definition changed")
        states = tuple(
            cell.evaluate(positions, low, rotations)
            for cells, positions, low, rotations in (
                (self.cells_a, positions_a, position_low_a, cell_rotations_a),
                (self.cells_b, positions_b, position_low_b, cell_rotations_b),
            )
            for cell in cells
        )
        current = tuple(state.positions for state in states)
        total = np.zeros(1+36+36*36)
        error = np.zeros(3)
        search_cells = intervals = evaluations = unresolved = visited = 0
        minimum_sampled = conservative_lower = float("inf")

        for source_beam, target_beam in ((0, 1), (1, 0)):
            source_base, target_base = 2*source_beam, 2*target_beam
            target_positions = (current[target_base], current[target_base+1])
            ids = self.node_ids_b if target_beam else self.node_ids_a
            target_ids = ((ids[0], ids[1]), (ids[1], ids[2]))
            for source_cell in (0, 1):
                source_index = source_base+source_cell
                search = NativeTwoCellUnionSearch(
                    current[source_index], target_positions, target_ids,
                    combined_radius_m=self.radius,
                    distance_tolerance_m=self.distance_tolerance,
                    feature_tolerance_m=self.feature_tolerance,
                    parameter_tolerance=self.search_parameter_tolerance,
                    maximum_depth=self.maximum_search_depth,
                    maximum_cells=self.maximum_search_cells,
                )
                scan = search.scan()
                search_cells += scan.visited_cells
                unresolved += scan.unresolved_intervals
                minimum_sampled = min(minimum_sampled,
                                      scan.minimum_sampled_gap_m)
                conservative_lower = min(conservative_lower,
                                         scan.conservative_lower_gap_m)

                def integrand(station: float, owner: int | None) -> tuple[np.ndarray, bool]:
                    nonlocal evaluations
                    chosen = (search.nearest(station).target_cell
                              if owner is None else owner)
                    target_index = target_base+chosen
                    jet = b3_distance_jet(
                        current[source_index], current[target_index],
                        station, self.radius, source_is_a=True,
                    )
                    evaluations += 1
                    if jet.gap >= 0.0:
                        return np.zeros_like(total), False
                    measure = float(np.linalg.norm(
                        _curve(self.reference_curves[source_index], station)[1]
                    ))
                    factor = self.stiffness*measure
                    gradient = factor*jet.gap*jet.gradient
                    hessian = factor*(np.outer(jet.gradient, jet.gradient)
                                      + jet.gap*jet.hessian)
                    index = np.r_[np.arange(9*source_index, 9*source_index+9),
                                  np.arange(9*target_index, 9*target_index+9)]
                    value = np.zeros_like(total)
                    value[0] = 0.5*factor*jet.gap*jet.gap
                    value[1+index] += gradient
                    matrix = value[37:].reshape(36, 36)
                    matrix[np.ix_(index, index)] += hessian
                    return value, True

                def quadrature(left: float, right: float, rule, owner: int | None):
                    points, weights = rule
                    result = np.zeros_like(total)
                    active = False
                    scale = 0.5*(right-left)
                    midpoint = 0.5*(left+right)
                    for point, weight in zip(points, weights):
                        value, on = integrand(midpoint+scale*float(point), owner)
                        result += scale*float(weight)*value
                        active = active or on
                    return result, active

                def integrate(left: float, right: float, owner: int | None,
                              budget: np.ndarray) -> np.ndarray:
                    nonlocal visited, intervals
                    visited += 1
                    if visited > self.maximum_integration_intervals:
                        raise MemoryError("native whole pair integration interval budget exhausted")
                    coarse, coarse_active = quadrature(left, right, _GAUSS_8, owner)
                    refined, refined_active = quadrature(left, right, _GAUSS_16, owner)
                    difference = np.abs(refined-coarse)
                    measured = np.array((
                        difference[0], float(np.max(difference[1:37])),
                        float(np.max(difference[37:])),
                    ))
                    if not (coarse_active or refined_active):
                        raise MemoryError("possible native whole-pair contact missed by quadrature")
                    if np.all(measured <= budget):
                        intervals += 1
                        error[:] += measured
                        return refined
                    midpoint = 0.5*(left+right)
                    return (integrate(left, midpoint, owner, 0.5*budget)
                            + integrate(midpoint, right, owner, 0.5*budget))

                for interval in scan.intervals:
                    if interval.status == "open":
                        continue
                    pieces = _straight_support_partitions(
                        current[source_index], target_positions,
                        self.radius, interval.left, interval.right,
                        min(self.distance_tolerance, self.feature_tolerance),
                    )
                    if pieces is None and interval.target_cell is None:
                        pieces = _straight_join_partitions(
                            current[source_index], target_positions,
                            interval.left, interval.right,
                            min(self.distance_tolerance, self.feature_tolerance),
                        )
                        if pieces is None:
                            raise ValueError("native whole pair target ownership is unresolved")
                    elif pieces is None:
                        pieces = ((interval.left, interval.right,
                                   interval.target_cell),)
                    for begin, stop, certified_owner in pieces:
                        share = 0.25*(stop-begin)
                        budget = np.array((self.energy_tolerance*share,
                                           self.force_tolerance*share,
                                           self.tangent_tolerance*share))
                        total += 0.5*integrate(
                            begin, stop, certified_owner, budget,
                        )

        jacobian = np.zeros((36, 84))
        for global_cell, state in enumerate(states):
            side = 0 if global_cell < 2 else 1
            jacobian[9*global_cell:9*global_cell+9,
                     42*side:42*side+42] = state.geometric_jacobian
        gradient = total[1:37]
        hessian = total[37:].reshape(36, 36)
        residual = jacobian.T @ gradient
        tangent = jacobian.T @ hessian @ jacobian
        for global_cell, state in enumerate(states):
            _, curvature = state.pullback(
                gradient[9*global_cell:9*global_cell+9],
                np.zeros((9, 9)),
            )
            side = 0 if global_cell < 2 else 1
            tangent[42*side:42*side+42,
                    42*side:42*side+42] += curvature
        physical = -gradient.reshape(4, 3, 3)
        force_a = np.sum(physical[:2], axis=(0, 1))
        force_b = np.sum(physical[2:], axis=(0, 1))
        moment = np.array([
            np.sum(np.cross(current[cell], physical[cell]), axis=0)
            for cell in range(4)
        ])
        return NativeRetainedWholePairResult(
            float(total[0]), _readonly(residual), _readonly(tangent),
            _readonly(force_a), _readonly(force_b),
            _readonly(np.sum(moment[:2], axis=0)),
            _readonly(np.sum(moment[2:], axis=0)),
            conservative_lower, minimum_sampled,
            float(error[0]), float(error[1]), float(error[2]),
            search_cells, intervals, evaluations, unresolved,
        )
