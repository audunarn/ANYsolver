"""Whole two-cell native beam distributed contact across a shared junction."""

import numpy as np
import pytest
from scipy.integrate import quad
from scipy.optimize import brentq
from scipy.spatial.transform import Rotation

from anysolver._ge_beam3_centered_reference import (
    CenteredCurvedBeam3ReferenceGeometry,
)
from anysolver.general_contact.native_retained_whole_pair import (
    NativeRetainedWholeCurvePair,
    _straight_join_owner,
    _straight_join_partitions,
    _straight_support_partitions,
    _piecewise_straight_support_partitions,
    _tiny_cell_omission_bound,
)


def _reference(y):
    points = np.array(((0.0, y, 0.0),
                       (1.0, y, 0.0),
                       (2.0, y, 0.0)))
    return CenteredCurvedBeam3ReferenceGeometry(
        points, np.tile(np.eye(3), (3, 1, 1)),
    )


def _kernel(a, b, *, max_intervals=1000):
    return NativeRetainedWholeCurvePair(
        11, a, (1, 2, 3), 0.05,
        12, b, (4, 5, 6), 0.05,
        line_stiffness_n_per_m2=100.0,
        distance_tolerance_m=1e-10,
        feature_tolerance_m=1e-9,
        search_parameter_tolerance=1e-3,
        maximum_search_depth=20,
        maximum_search_cells=10000,
        energy_tolerance_j=1e-8,
        force_tolerance_n=1e-7,
        tangent_tolerance_n_per_m=1e-6,
        maximum_integration_intervals=max_intervals,
    )


def _pose(reference):
    return (reference.coordinates.copy(), np.zeros((3, 3)),
            np.tile(np.eye(3), (2, 1, 1)))


def test_parallel_two_cell_contact_crosses_target_junction():
    a, b = _reference(0.0), _reference(0.08)
    kernel = _kernel(a, b)
    result = kernel.evaluate(*_pose(a), *_pose(b))
    assert result.potential_j == pytest.approx(0.04, rel=1e-7)
    assert result.unresolved_search_intervals > 0
    assert result.conservative_lower_gap_m <= -0.02
    np.testing.assert_allclose(result.beam_a_force_n,
                               (0.0, -4.0, 0.0), atol=1e-6)
    np.testing.assert_allclose(result.beam_b_force_n,
                               (0.0, 4.0, 0.0), atol=1e-6)
    np.testing.assert_allclose(result.beam_a_force_n+result.beam_b_force_n,
                               0.0, atol=1e-8)
    np.testing.assert_allclose(result.beam_a_moment_nm+result.beam_b_moment_nm,
                               0.0, atol=1e-8)


def test_whole_pair_open_and_bounded_integration():
    a, b = _reference(0.0), _reference(0.3)
    result = _kernel(a, b).evaluate(*_pose(a), *_pose(b))
    assert result.potential_j == 0.0
    np.testing.assert_array_equal(result.residual, 0.0)
    a, b = _reference(0.0), _reference(0.08)
    with pytest.raises(MemoryError, match="integration interval budget"):
        _kernel(a, b, max_intervals=1).evaluate(*_pose(a), *_pose(b))


def test_kinked_two_segment_support_matches_finite_segment_oracle():
    a, b = _reference(0.0), _reference(0.102)
    source = np.array(((1.0, 0.0, 0.0), (1.5, 0.0, 0.0),
                       (2.0, 0.0, 0.0)))
    nodes = np.array(((0.0, 0.102, 0.0),
                      (1.0, 0.1006061111111111, 0.0),
                      (2.0, 0.09754555555555555, 0.0)))
    targets = tuple(np.array((nodes[i], 0.5*(nodes[i]+nodes[i+1]),
                              nodes[i+1])) for i in (0, 1))
    pieces = _piecewise_straight_support_partitions(
        source, targets, ((4, 5), (5, 6)), 0.1, 1e-10,
    )
    assert pieces is not None
    assert len(pieces) == 2

    def segment_distance(point, first, second):
        vector = second-first
        station = np.clip(np.dot(point-first, vector)/np.dot(vector, vector),
                          0.0, 1.0)
        return float(np.linalg.norm(point-first-station*vector))

    for station in np.linspace(0.0, 1.0, 257):
        point = source[0]+station*(source[2]-source[0])
        distances = tuple(segment_distance(point, nodes[i], nodes[i+1])
                          for i in (0, 1))
        if abs(min(distances)-0.1) < 1e-8:
            continue
        owning = next((owner for left, right, owner in pieces
                       if left <= station <= right), None)
        assert (owning is not None) == (min(distances) < 0.1)
        if owning is not None:
            assert owning == int(np.argmin(distances))

    pose_a = _pose(a)
    pose_b = list(_pose(b))
    pose_b[0][:] = nodes
    result = _kernel(a, b).evaluate(*pose_a, *pose_b)

    def directional_integral(source_nodes, target_nodes, index):
        first, second = source_nodes[index:index+2]

        def gap(station):
            point = first+station*(second-first)
            distance = min(segment_distance(point, target_nodes[j],
                                            target_nodes[j+1])
                           for j in (0, 1))
            return distance-0.1

        stations = np.linspace(0.0, 1.0, 513)
        crossings = [brentq(gap, left, right, xtol=1e-14)
                     for left, right in zip(stations[:-1], stations[1:])
                     if gap(left)*gap(right) < 0.0]
        projection_cuts = []
        for target in (0, 1):
            origin, end = target_nodes[target:target+2]
            vector = end-origin
            squared_length = float(vector@vector)
            first_projection = float((first-origin)@vector)/squared_length
            slope = float((second-first)@vector)/squared_length
            if slope != 0.0:
                projection_cuts.extend(
                    cut for level in (0.0, 1.0)
                    if 0.0 < (cut := (level-first_projection)/slope) < 1.0
                )
        return quad(lambda station: min(gap(station), 0.0)**2,
                    0.0, 1.0, epsabs=1e-14, epsrel=1e-12,
                    points=sorted(set((*crossings, *projection_cuts))),
                    limit=500)[0]

    oracle = 25.0*sum(
        directional_integral(source_nodes, target_nodes, index)
        for source_nodes, target_nodes in ((a.coordinates, nodes),
                                           (nodes, a.coordinates))
        for index in (0, 1)
    )
    assert result.potential_j == pytest.approx(oracle, rel=1e-8, abs=1e-12)
    assert result.integration_cells_checked <= 8
    assert result.conservative_lower_gap_m <= -0.0024

    step = 1e-6
    plus, minus = pose_b[0].copy(), pose_b[0].copy()
    plus[2, 1] += step
    minus[2, 1] -= step
    right = _kernel(a, b).evaluate(*pose_a, plus, *pose_b[1:])
    left = _kernel(a, b).evaluate(*pose_a, minus, *pose_b[1:])
    column = 42+6*2+1
    assert ((right.potential_j-left.potential_j)/(2.0*step)
            == pytest.approx(result.residual[column], rel=1e-5, abs=1e-8))
    assert ((right.residual[column]-left.residual[column])/(2.0*step)
            == pytest.approx(result.tangent[column, column],
                             rel=1e-5, abs=1e-7))


def test_shared_junction_owner_requires_persistent_node_identity():
    target_nodes = np.array(((0.0, 0.0, 0.0),
                             (0.9999999983139424, -0.0003613274401141717, 0.0),
                             (1.9999999966905053, -0.0011550345541511337, 0.0)))
    targets = tuple(np.array((target_nodes[i],
                              0.5*(target_nodes[i]+target_nodes[i+1]),
                              target_nodes[i+1])) for i in (0, 1))
    source = np.array(((0.9999995263354753, 0.10096751256433002, 0.0),
                       (1.4999983797836682, 0.09983418723760443, 0.0),
                       (1.9999972332318612, 0.09870086191087882, 0.0)))
    admitted = _piecewise_straight_support_partitions(
        source, targets, ((1, 2), (2, 3)), 0.1, 1e-10,
    )
    assert admitted is not None
    assert admitted[-1][2] == 1
    assert _piecewise_straight_support_partitions(
        source, targets, ((1, 2), (7, 3)), 0.1, 1e-10,
    ) is None


def test_straight_junction_owner_is_certified_only_on_one_side():
    a, b = _reference(0.0), _reference(0.08)
    kernel = _kernel(a, b)
    target = kernel.reference_curves[2:4]
    assert _straight_join_owner(kernel.reference_curves[0], target,
                                0.98, 1.0, 1e-9) == 0
    assert _straight_join_owner(kernel.reference_curves[1], target,
                                0.0, 0.02, 1e-9) == 1
    spanning = np.array(((0.9, 0.0, 0.0),
                         (1.0, 0.0, 0.0),
                         (1.1, 0.0, 0.0)))
    assert _straight_join_owner(spanning, target, 0.0, 1.0,
                                1e-9) is None
    curved = (target[0].copy(), target[1].copy())
    curved[0][1, 1] += 0.01
    assert _straight_join_owner(kernel.reference_curves[0], curved,
                                0.98, 1.0, 1e-9) is None
    partitions = _straight_join_partitions(spanning, target, 0.0, 1.0,
                                            1e-9)
    assert partitions is not None
    assert tuple(piece[2] for piece in partitions) == (0, 1)
    assert partitions[0][1] == pytest.approx(0.5)
    assert partitions[1][0] == pytest.approx(0.5)
    assert _straight_join_partitions(spanning, curved, 0.0, 1.0,
                                      1e-9) is None


def test_parallel_interior_cell_motion_crosses_target_junction():
    a, b = _reference(0.0), _reference(0.08)
    moved = b.coordinates.copy()
    moved[1, 0] += 0.2
    result = _kernel(a, b).evaluate(*_pose(a), moved,
                                     np.zeros((3, 3)),
                                     np.tile(np.eye(3), (2, 1, 1)))
    assert result.potential_j == pytest.approx(0.04, rel=1e-7)
    assert result.integration_intervals > 0
    np.testing.assert_allclose(result.beam_a_force_n,
                               (0.0, -4.0, 0.0), atol=1e-6)
    np.testing.assert_allclose(result.beam_b_force_n,
                               (0.0, 4.0, 0.0), atol=1e-6)
    exchanged = _kernel(b, a).evaluate(
        moved, np.zeros((3, 3)), np.tile(np.eye(3), (2, 1, 1)),
        *_pose(a),
    )
    assert exchanged.potential_j == pytest.approx(result.potential_j,
                                                   rel=1e-10)
    np.testing.assert_allclose(result.beam_a_force_n+result.beam_b_force_n,
                               0.0, atol=1e-8)
    np.testing.assert_allclose(result.beam_a_moment_nm+result.beam_b_moment_nm,
                               0.0, atol=1e-8)


def test_translated_parallel_beams_have_certified_partial_endpoint_support():
    a, b = _reference(0.0), _reference(0.08)
    shifted = b.coordinates.copy()
    shifted[:, 0] += 0.2
    target = tuple(cell.copy() for cell in _kernel(a, b).reference_curves[2:4])
    target = tuple(cell+np.array((0.2, 0.0, 0.0)) for cell in target)
    source = _kernel(a, b).reference_curves[0]
    pieces = _straight_support_partitions(source, target, 0.1,
                                           0.0, 1.0, 1e-9)
    assert pieces is not None
    assert pieces[0][0] == pytest.approx(0.14)
    result = _kernel(a, b).evaluate(
        *_pose(a), shifted, np.zeros((3, 3)),
        np.tile(np.eye(3), (2, 1, 1)),
    )
    def scalar_energy(x):
        distance = np.hypot(0.08, max(0.2-x, 0.0))
        return min(distance-0.1, 0.0)**2
    oracle, _ = quad(scalar_energy, 0.0, 2.0,
                     points=(0.14, 0.2), epsabs=1e-12)
    assert result.potential_j == pytest.approx(50.0*oracle,
                                               rel=1e-5, abs=1e-8)
    np.testing.assert_allclose(result.beam_a_force_n+result.beam_b_force_n,
                               0.0, atol=1e-8)
    np.testing.assert_allclose(result.beam_a_moment_nm+result.beam_b_moment_nm,
                               0.0, atol=1e-8)
    exchanged = _kernel(b, a).evaluate(
        shifted, np.zeros((3, 3)), np.tile(np.eye(3), (2, 1, 1)),
        *_pose(a),
    )
    assert exchanged.potential_j == pytest.approx(result.potential_j,
                                                   rel=1e-10)

    direction = np.zeros(84)
    direction[[1, 7, 13]] = -0.001
    direction[[43, 49, 55]] = 0.002
    def perturbed(fraction):
        moved_a = a.coordinates.copy()
        moved_b = shifted.copy()
        moved_a[:, 1] -= fraction*0.001
        moved_b[:, 1] += fraction*0.002
        return _kernel(a, b).evaluate(
            moved_a, np.zeros((3, 3)), np.tile(np.eye(3), (2, 1, 1)),
            moved_b, np.zeros((3, 3)), np.tile(np.eye(3), (2, 1, 1)),
        )
    step = 1e-2
    plus, minus = perturbed(step), perturbed(-step)
    first = (plus.potential_j-minus.potential_j)/(2.0*step)
    second = (plus.potential_j-2.0*result.potential_j
              +minus.potential_j)/step**2
    assert first == pytest.approx(result.residual@direction,
                                  rel=1e-5, abs=1e-7)
    assert second == pytest.approx(direction@result.tangent@direction,
                                   rel=1e-5, abs=1e-6)


def test_straight_support_finds_sub_gauss_narrow_pocket_and_open_interval():
    _, b = _reference(0.0), _reference(0.0999995)
    target = tuple(_kernel(_reference(0.0), b).reference_curves[2:4])
    source = np.array(((-0.02, 0.0, 0.0),
                       (-0.01015, 0.0, 0.0),
                       (-0.0003, 0.0, 0.0)))
    pieces = _straight_support_partitions(source, target, 0.1,
                                           0.0, 1.0, 1e-9)
    assert pieces is not None
    assert len(pieces) == 1
    assert 0.0 < 1.0-pieces[0][0] < 0.001
    assert _straight_support_partitions(source, target, 0.09,
                                        0.0, 1.0, 1e-9) == ()
    far_shift = np.array((1e9, 0.0, 0.0))
    distant_source = source+far_shift
    distant_target = tuple(cell+far_shift for cell in target)
    assert _straight_support_partitions(distant_source, distant_target,
                                        0.1, 0.0, 1.0, 1e-9) is None


def test_tiny_cell_bound_covers_parallel_line_work_and_rejects_roundoff():
    source = np.array(((0.0, 0.0, 0.0),
                       (0.5, 0.0, 0.0),
                       (1.0, 0.0, 0.0)))
    target = source+np.array((0.0, 0.08, 0.0))
    left = 0.5
    right = np.nextafter(left, 1.0)
    width = right-left
    bound = _tiny_cell_omission_bound(
        source, target, source, 0.1, 100.0,
        left, right, 1e-13, 1e-9,
    )
    assert bound is not None
    assert bound[0] >= 0.02*width
    assert bound[1] >= 2.0*width
    assert bound[2] >= 100.0*width
    assert np.all(bound <= (1e-8, 1e-7, 1e-6))
    assert _tiny_cell_omission_bound(
        source, target, source, 0.1, 100.0,
        left, right, 1e-5, 1e-9,
    ) is None
    turning_target = target.copy()
    turning_target[2] = turning_target[0]
    assert _tiny_cell_omission_bound(
        source, turning_target, source, 0.1, 100.0,
        left, right, 1e-13, 1e-9,
    ) is None


def test_whole_pair_energy_and_cross_beam_tangent_on_smooth_branch():
    a, b = _reference(0.0), _reference(0.08)
    kernel = _kernel(a, b)
    pa, la, ra = _pose(a)
    pb, lb, rb = _pose(b)
    result = kernel.evaluate(pa, la, ra, pb, lb, rb)
    direction = np.zeros(84)
    direction[[1, 7, 13]] = 0.003
    direction[[43, 49, 55]] = -0.002

    def energy(fraction):
        moved_a = pa.copy()
        moved_b = pb.copy()
        moved_a[:, 1] += fraction*0.003
        moved_b[:, 1] -= fraction*0.002
        return kernel.evaluate(moved_a, la, ra,
                               moved_b, lb, rb).potential_j

    step = 1e-4
    first = (energy(step)-energy(-step))/(2.0*step)
    second = (energy(step)-2.0*energy(0.0)+energy(-step))/step**2
    assert first == pytest.approx(result.residual@direction,
                                  rel=1e-7, abs=1e-8)
    assert second == pytest.approx(direction@result.tangent@direction,
                                   rel=1e-5, abs=1e-6)
    assert np.linalg.norm(result.tangent[:42, 42:]) > 0.0


def test_whole_pair_role_exchange_and_common_rigid_motion():
    a, b = _reference(0.0), _reference(0.08)
    base = _kernel(a, b).evaluate(*_pose(a), *_pose(b))
    exchanged = _kernel(b, a).evaluate(*_pose(b), *_pose(a))
    assert exchanged.potential_j == pytest.approx(base.potential_j,
                                                   rel=1e-11)
    np.testing.assert_allclose(exchanged.beam_a_force_n,
                               base.beam_b_force_n, atol=1e-8)
    np.testing.assert_allclose(exchanged.beam_b_force_n,
                               base.beam_a_force_n, atol=1e-8)
    turn = Rotation.from_rotvec((0.2, -0.1, 0.15)).as_matrix()
    shift = np.array((0.7, -0.4, 0.2))
    rotations = np.tile(turn, (2, 1, 1))
    transformed = _kernel(a, b).evaluate(
        a.coordinates@turn.T+shift, np.zeros((3, 3)), rotations,
        b.coordinates@turn.T+shift, np.zeros((3, 3)), rotations,
    )
    assert transformed.potential_j == pytest.approx(base.potential_j,
                                                     rel=1e-10)
    np.testing.assert_allclose(transformed.beam_a_force_n,
                               turn@base.beam_a_force_n, atol=1e-8)
    np.testing.assert_allclose(transformed.beam_b_force_n,
                               turn@base.beam_b_force_n, atol=1e-8)
