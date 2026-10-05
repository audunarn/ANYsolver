"""Consequences of the independent resolved-solid area work map; no CCX run."""
from dataclasses import FrozenInstanceError
import math

import numpy as np
import pytest

from scripts.r8_e02_distributing_solid_area import LAW, _REFERENCE, _shape, compile_area_map
from scripts.r8_e02_rigid_tip_reference import build_deck


def _cross(a, b):
    return np.cross(a, b)


@pytest.fixture(scope="module")
def geometry():
    # Inert existing geometry generation only. Its rigid constraints are never
    # imported into this observable or treated as distributing-law equivalence.
    _, record = build_deck(10, 4, 1, "Mx")
    return record["physical_nodes"], record["elements"]


@pytest.fixture(scope="module")
def prepared(geometry):
    nodes, elements = geometry
    # Clip within cells in both x/y directions; z=0 is a shared layer boundary.
    return compile_area_map(nodes, elements, (.613, .947, -.083, .061), .02,
                            (.9, 0., .05))


def _field(area, function):
    return {node: function(*point) for node, point in zip(area.node_ids, area.coordinates_m)}


@pytest.mark.parametrize("channel", range(6))
def test_six_rigid_fields_reproduce_centroid_and_eccentric_port(prepared, channel):
    translation, spin = np.zeros(3), np.zeros(3)
    (translation if channel < 3 else spin)[channel % 3] = 1.
    field = _field(prepared, lambda x, y, z: translation + _cross(spin, (x, y, z)))
    observed = prepared.recover(field)
    np.testing.assert_allclose(observed.mean_translation_m,
                               translation + _cross(spin, prepared.centroid_m), atol=3e-13, rtol=0)
    np.testing.assert_allclose(observed.rotation_components_rad, spin, atol=3e-13, rtol=0)
    np.testing.assert_allclose(observed.port_translation_m,
                               translation + _cross(spin, prepared.port_m), atol=3e-13, rtol=0)


@pytest.mark.parametrize("channel", range(6))
def test_all_six_transpose_actions_preserve_work_and_resultant(prepared, channel):
    load = np.eye(6)[channel]
    force, moment = load[:3], load[3:]
    # Nonrigid independent nodal field; transpose must preserve its work too.
    field = _field(prepared, lambda x, y, z:
                   (math.sin(7 * x) + z * y, x * y - 2 * z, y * y + x * z))
    observed = prepared.recover(field)
    action = prepared.action(force, moment)
    expected = np.dot(force, observed.port_translation_m) + np.dot(moment, observed.rotation_components_rad)
    assert action.work(field) == pytest.approx(expected, abs=5e-13, rel=2e-13)
    for origin in ((0., 0., 0.), (.37, -.23, .41)):
        actual_force, actual_moment = action.resultant(origin)
        np.testing.assert_allclose(actual_force, force, atol=5e-13, rtol=0)
        np.testing.assert_allclose(actual_moment,
                                   moment + _cross(np.subtract(prepared.port_m, origin), force),
                                   atol=5e-13, rtol=0)


def test_shell_subspace_reproduces_independent_physical_directors(prepared):
    xbar, ybar, _ = prepared.centroid_m
    def field(x, y, z):
        theta_x, theta_y = .2 + .3 * x - .4 * y, -.1 + .7 * x + .6 * y
        return (1 + 2 * x + 3 * y + z * theta_y,
                -.4 + 4 * x + 5 * y - z * theta_x,
                .7 - 6 * x + 2 * y)
    observed = prepared.recover(_field(prepared, field))
    np.testing.assert_allclose(observed.mean_translation_m,
                               (1 + 2 * xbar + 3 * ybar, -.4 + 4 * xbar + 5 * ybar,
                                .7 - 6 * xbar + 2 * ybar), atol=2e-13, rtol=0)
    np.testing.assert_allclose(observed.rotation_components_rad,
                               (.2 + .3 * xbar - .4 * ybar,
                                -.1 + .7 * xbar + .6 * ybar, .5), atol=3e-13, rtol=0)


def test_transverse_slope_does_not_become_a_director(prepared):
    observed = prepared.recover(_field(prepared, lambda x, y, z: (0., 0., 2 * x - 3 * y)))
    np.testing.assert_allclose(observed.rotation_components_rad, (0., 0., 0.), atol=1e-14, rtol=0)


def test_bilinear_q4_fields_and_through_thickness_xy_directors(prepared):
    xbar, ybar, _ = prepared.centroid_m
    def field(x, y, z):
        return (2*x*y + z*(.3+x*y), -3*x*y-z*(-.2+2*x*y), 4*x*y)
    observed = prepared.recover(_field(prepared, field))
    np.testing.assert_allclose(observed.mean_translation_m,
        (2*xbar*ybar, -3*xbar*ybar, 4*xbar*ybar), atol=3e-13, rtol=0)
    np.testing.assert_allclose(observed.rotation_components_rad,
        (-.2+2*xbar*ybar, .3+xbar*ybar, .5*(-3*ybar-2*xbar)), atol=3e-13, rtol=0)


def test_symmetric_three_dimensional_shear_has_secant_director_not_polar_spin(prepared):
    # ux=gamma*z, uz=gamma*x: 3D infinitesimal polar spin_y is zero,
    # while the independently declared top/bottom secant director_y is gamma.
    gamma = .37
    observed = prepared.recover(_field(prepared, lambda x, y, z: (gamma * z, 0., gamma * x)))
    np.testing.assert_allclose(observed.rotation_components_rad, (0., gamma, 0.), atol=2e-13, rtol=0)


def test_warped_nonrigid_field_has_zero_area_pose(prepared):
    centre = prepared.centroid_m[0]
    width = prepared.bounds_xy_m[1] - prepared.bounds_xy_m[0]
    field = _field(prepared, lambda x, y, z: (0., 0., (x - centre) ** 2 - width ** 2 / 12))
    assert max(abs(value[2]) for value in field.values()) > 1e-3
    observed = prepared.recover(field)
    np.testing.assert_allclose(observed.mean_translation_m + observed.rotation_components_rad,
                               np.zeros(6), atol=5e-16, rtol=0)
    np.testing.assert_allclose(observed.port_translation_m, np.zeros(3), atol=5e-16, rtol=0)
    assert abs(prepared.action((0., 0., 1.), (0., 0., 0.)).work(field)) < 5e-16


def test_shape_cardinality_partition_and_polynomial_gradient_reproduction():
    xyz = np.asarray(_REFERENCE, dtype=float)
    for i, position in enumerate(_REFERENCE):
        shape, _ = _shape(position)
        np.testing.assert_array_equal(shape, np.eye(20)[i])
    for position in ((.31, -.23, .47), (0., 0., 0.), (-.7, .6, -.3)):
        shape, derivative = _shape(position)
        assert math.fsum(shape) == pytest.approx(1., abs=3e-16)
        np.testing.assert_allclose(shape @ xyz, position, atol=4e-16, rtol=0)
        np.testing.assert_allclose(derivative.T @ xyz, np.eye(3), atol=5e-16, rtol=0)
        # The exact polynomial identity is zero; its binary64 accumulation is
        # bounded by gamma_n times the sum of absolute terms, not an arbitrary
        # sub-epsilon absolute floor. This is a shape-function control only.
        eps = np.finfo(float).eps
        gamma_n = len(derivative) * eps / (1 - len(derivative) * eps)
        assert np.all(np.abs(derivative.sum(axis=0)) <=
                      gamma_n * np.abs(derivative).sum(axis=0))


def test_owned_immutable_geometry_and_map(prepared, geometry):
    nodes, elements = geometry
    mutable_nodes = {n: list(p) for n, p in nodes.items()}
    mutable_elements = {e: list(ids) for e, ids in elements.items()}
    bounds, port = list(prepared.bounds_xy_m), list(prepared.port_m)
    owned = compile_area_map(mutable_nodes, mutable_elements, bounds, .02, port)
    assert owned == prepared and owned.law == LAW
    mutable_nodes[owned.node_ids[0]][0] += 10
    mutable_elements.clear()
    bounds[0], port[0] = -100., -100.
    assert owned == prepared
    with pytest.raises(FrozenInstanceError):
        owned.port_m = (0., 0., 0.)
    with pytest.raises(TypeError):
        owned.weights[0][0][0] = 1.
    force = [1., 2., 3.]
    action = owned.action(force, (4., 5., 6.))
    force[0] = 1000.
    np.testing.assert_allclose(action.resultant()[0], (1., 2., 3.), atol=2e-12, rtol=0)
    with pytest.raises(FrozenInstanceError):
        action.forces_n = ()


def test_shared_midsurface_uses_lower_layer_and_is_input_order_independent(prepared, geometry):
    nodes, elements = geometry
    ordered = compile_area_map(dict(reversed(tuple(nodes.items()))),
                               dict(reversed(tuple(elements.items()))),
                               prepared.bounds_xy_m, .02, prepared.port_m)
    assert ordered == prepared
    for element in prepared.midsurface_owner_elements:
        z = tuple(nodes[n][2] for n in elements[element])
        assert max(z) == 0. and min(z) < 0.


@pytest.mark.parametrize("defect", ("order", "distortion", "nonfinite", "missing_node"))
def test_actual_geometry_and_connectivity_guards(geometry, prepared, defect):
    nodes, elements = geometry
    nodes, elements = dict(nodes), dict(elements)
    element = prepared.midsurface_owner_elements[0]
    ids = list(elements[element])
    if defect == "order":
        ids[8], ids[9] = ids[9], ids[8]
        elements[element] = ids
    elif defect == "distortion":
        point = list(nodes[ids[8]])
        point[0] += .001
        nodes[ids[8]] = point
    elif defect == "nonfinite":
        nodes[ids[8]] = (math.nan, 0., 0.)
    else:
        del nodes[ids[8]]
    with pytest.raises(ValueError):
        compile_area_map(nodes, elements, prepared.bounds_xy_m, .02, prepared.port_m)


@pytest.mark.parametrize("defect", ("missing", "overlap", "outside", "thickness"))
def test_complete_unambiguous_clipped_pad_coverage(geometry, prepared, defect):
    nodes, elements = geometry
    elements = dict(elements)
    bounds, thickness = prepared.bounds_xy_m, .02
    selected = prepared.midsurface_owner_elements[0]
    if defect == "missing":
        del elements[selected]
    elif defect == "overlap":
        elements[max(elements) + 1] = elements[selected]
    elif defect == "outside":
        bounds = (.9, 1.1, -.05, .05)
    else:
        thickness = .021
    with pytest.raises(ValueError, match="coverage"):
        compile_area_map(nodes, elements, bounds, thickness, prepared.port_m)


@pytest.mark.parametrize("bounds,thickness,port", (
    ((.8, .8, -.1, .1), .02, (.9, 0., .05)),
    ((.9, .8, -.1, .1), .02, (.9, 0., .05)),
    ((.8, 1., -.1, .1), 0., (.9, 0., .05)),
    ((.8, 1., -.1, .1), math.inf, (.9, 0., .05)),
    ((.8, 1., -.1, .1), .02, (.9, math.nan, .05)),
))
def test_positive_finite_observable_inputs(geometry, bounds, thickness, port):
    with pytest.raises(ValueError):
        compile_area_map(*geometry, bounds, thickness, port)


def test_recovery_and_action_inputs_fail_closed(prepared):
    field = _field(prepared, lambda x, y, z: (0., 0., 0.))
    missing = dict(field)
    missing.pop(prepared.node_ids[0])
    invalid = dict(field)
    invalid[prepared.node_ids[0]] = (0., 0., math.inf)
    for displacements in (missing, invalid, np.zeros(3)):
        with pytest.raises(ValueError):
            prepared.recover(displacements)
        with pytest.raises(ValueError):
            prepared.action((1., 0., 0.), (0., 0., 0.)).work(displacements)
    for force, moment in (((math.nan, 0., 0.), (0., 0., 0.)),
                          ((0., 0.), (0., 0., 0.)),
                          ((0., 0., 0.), (0., 0., math.inf))):
        with pytest.raises(ValueError):
            prepared.action(force, moment)


def test_coincident_duplicate_ids_are_not_a_continuous_shared_face(geometry, prepared):
    nodes, elements = dict(geometry[0]), dict(geometry[1])
    selected = prepared.midsurface_owner_elements[0]
    incidence = list(elements[selected])
    next_id = max(nodes) + 1
    for slot, reference in enumerate(_REFERENCE):
        if reference[2] == 1:
            nodes[next_id] = nodes[incidence[slot]]
            incidence[slot] = next_id
            next_id += 1
    elements[selected] = incidence
    with pytest.raises(ValueError, match="nonconforming shared solid face-node identities"):
        compile_area_map(nodes, elements, prepared.bounds_xy_m, .02, prepared.port_m)


def test_coarse_fine_face_traces_are_rejected_even_with_complete_box_coverage(geometry, prepared):
    nodes, elements = dict(geometry[0]), dict(geometry[1])
    selected = prepared.midsurface_owner_elements[0]
    incidence = elements.pop(selected)
    low = tuple(min(nodes[n][axis] for n in incidence) for axis in range(3))
    high = tuple(max(nodes[n][axis] for n in incidence) for axis in range(3))
    split = low[1] + (high[1] - low[1]) / 2
    by_position = {tuple(point): node for node, point in nodes.items()}
    next_node, next_element = max(nodes) + 1, max(elements) + 1
    for bottom, top in ((low[1], split), (split, high[1])):
        child_low, child_high = (low[0], bottom, low[2]), (high[0], top, high[2])
        span = tuple(b - a for a, b in zip(child_low, child_high))
        centre = tuple(a + h / 2 for a, h in zip(child_low, span))
        child = []
        for reference in _REFERENCE:
            # Preserve exact original/shared face coordinates; this must
            # isolate nonmatching traces rather than manufacture tiny gaps.
            point = tuple(child_low[j] if r == -1 else child_high[j] if r == 1 else centre[j]
                          for j, r in enumerate(reference))
            if point not in by_position:
                by_position[point] = next_node
                nodes[next_node] = point
                next_node += 1
            child.append(by_position[point])
        elements[next_element] = tuple(child)
        next_element += 1
    with pytest.raises(ValueError, match="nonconforming solid face extents"):
        compile_area_map(nodes, elements, prepared.bounds_xy_m, .02, prepared.port_m)


class _FloatCoercible:
    def __float__(self):
        return 1.


@pytest.mark.parametrize("invalid", (True, np.bool_(False), "1.0", _FloatCoercible(),
                                     1 + 0j, np.complex64(1), np.complex128(1)))
def test_nonreal_and_coercible_entries_are_rejected_before_float_conversion(prepared, geometry, invalid):
    with pytest.raises(ValueError):
        prepared.action((invalid, 0., 0.), (0., 0., 0.))
    field = _field(prepared, lambda x, y, z: (0., 0., 0.))
    field[prepared.node_ids[0]] = (invalid, 0., 0.)
    with pytest.raises(ValueError):
        prepared.recover(field)
    nodes = dict(geometry[0])
    nodes[prepared.node_ids[0]] = (invalid, 0., 0.)
    with pytest.raises(ValueError):
        compile_area_map(nodes, geometry[1], prepared.bounds_xy_m, .02, prepared.port_m)


def test_real_numpy_scalar_entries_remain_supported(prepared):
    action = prepared.action((np.float32(1), np.int64(2), np.float64(3)),
                             (np.int32(0), 0., np.float64(0)))
    np.testing.assert_allclose(action.resultant()[0], (1., 2., 3.), atol=2e-12, rtol=0)


@pytest.mark.parametrize("distorted", (False, True))
def test_large_origin_unresolved_cell_is_rejected_before_world_ulp_can_hide_distortion(distorted):
    origin = float(2 ** 52)
    nodes = {i + 1: (origin + 4 * (reference[0] + 1),
                     float(reference[1]), float(reference[2]))
             for i, reference in enumerate(_REFERENCE)}
    if distorted:
        # First edge is nominally origin+4; a one-metre midside defect was
        # below the former 32-world-ULP tolerance despite an eight-metre span.
        nodes[9] = (origin + 5, -1., -1.)
    with pytest.raises(ValueError, match="world-ULP/span conditioning"):
        compile_area_map(nodes, {1: tuple(range(1, 21))},
                         (origin, origin + 8, -1., 1.), 2., (origin + 4, 0., 0.))
