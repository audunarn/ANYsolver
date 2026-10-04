"""Private two-Q4 distributing derivative/work controls; no solver campaign."""
from dataclasses import replace

import numpy as np
import pytest

from anysolver import _stiffened_shell_distributing_footprint as footprint
from anysolver._stiffened_shell_b2_nodal_footprint import reference_shell_matrix


def fixture():
    xyz = [(0., 0., 0.), (1., 0., 0.), (2., 0., 0.),
           (0., 1., 0.), (1., 1., 0.), (2., 1., 0.)]
    nodes = tuple(footprint.FlatQ4Node(i+1, p, 6*i) for i, p in enumerate(xyz))
    hosts = (footprint.CartesianQ4Host(21, (1, 2, 5, 4)),
             footprint.CartesianQ4Host(22, (2, 3, 6, 5)))
    beam = footprint.PhysicalBeamNodePort(101, (1.3, .3, .5), 36, footprint.IDENTITY_AXES)
    definition = footprint.DistributingFootprintDefinition("patch", (21, 22), 101, (.5, 1.5, .25, .75))
    return definition, nodes, hosts, beam


def compiled():
    return footprint.compile_footprint(*fixture())


def test_two_actual_hosts_integrate_frozen_partition_and_linear_fields():
    c = compiled()
    np.testing.assert_allclose(c.area_mean, [1/16, 3/8, 1/16, 1/16, 3/8, 1/16], rtol=0., atol=0.)
    assert c.area_m2 == .5
    np.testing.assert_array_equal(c.centroid_m, [1., .5, 0.])
    np.testing.assert_allclose(c.area_mean@c.shell_positions_m, c.centroid_m, atol=1e-15)
    np.testing.assert_allclose(c.planar_gradients@np.ones(6), 0., atol=1e-15)
    np.testing.assert_allclose(c.planar_gradients@c.shell_positions_m[:, :2], np.eye(2), atol=1e-15)
    assert np.linalg.matrix_rank(c.constraint_matrix) == 6
    assert c.constraint_matrix.shape == (6, 42)


def test_asymmetric_clips_reproduce_exact_bilinear_area_mean_and_gradients():
    definition, nodes, hosts, beam = fixture()
    definition = replace(definition, bounds_xy_m=(.25, 1.25, .125, .625))
    c = footprint.compile_footprint(definition, nodes, hosts, beam)
    xy = c.shell_positions_m[:, 0]*c.shell_positions_m[:, 1]
    # x*y is Q4-exact on both hosts; rectangular integrals factor independently.
    assert c.area_mean@xy == pytest.approx(.75*.375, abs=1e-15)
    np.testing.assert_allclose(c.planar_gradients@xy, [.375, .75], atol=1e-15)
    np.testing.assert_allclose(c.area_mean@c.shell_positions_m, [.75, .375, 0.], atol=1e-15)


def test_vertical_adjacency_with_asymmetric_clips_has_independent_axis_parity():
    definition, nodes, hosts, beam = fixture()
    nodes = tuple(replace(n, coordinates_m=(n.coordinates_m[1], n.coordinates_m[0], 0.)) for n in nodes)
    hosts = tuple(replace(h, node_ids=tuple(reversed(h.node_ids))) for h in hosts)
    definition = replace(definition, bounds_xy_m=(.125, .625, .25, 1.25))
    beam = replace(beam, coordinates_m=(.3, 1.3, .5))
    c = footprint.compile_footprint(definition, nodes, hosts, beam)
    xy = c.shell_positions_m[:, 0]*c.shell_positions_m[:, 1]
    assert c.area_mean@xy == pytest.approx(.375*.75, abs=1e-15)
    np.testing.assert_allclose(c.planar_gradients@xy, [.75, .375], atol=1e-15)
    np.testing.assert_allclose(c.area_mean@c.shell_positions_m, [.375, .75, 0.], atol=1e-15)


@pytest.mark.parametrize("axis", (3, 4))
def test_director_only_roll_pitch_remains_an_independent_port_channel(axis):
    c = compiled()
    shell = np.zeros((6, 6))
    shell[:, axis] = .7
    expected = np.zeros(6)
    expected[axis] = .7
    np.testing.assert_allclose(c.shell_trace@shell.ravel(), expected, atol=1e-15)
    # Keep translations fixed: director changes must reach eccentric translation rows.
    local = np.r_[shell.ravel(), np.zeros(6)]
    np.testing.assert_allclose(c.gap(local)[:3], np.cross(c.eccentricity_m, expected[3:]), atol=1e-15)
    np.testing.assert_allclose(c.gap(local)[3:], -expected[3:], atol=1e-15)


@pytest.mark.parametrize("kind,yaw", (("simple_shear", .5), ("symmetric_shear", 0.),
                                      ("isotropic_extension", 0.)))
def test_polar_yaw_is_half_curl_and_not_symmetric_strain(kind, yaw):
    c = compiled()
    shell = np.zeros((6, 6))
    x, y = c.shell_positions_m[:, :2].T
    if kind == "isotropic_extension":
        shell[:, 0], shell[:, 1] = x, y
    else:
        shell[:, 1] = x
        if kind == "symmetric_shear":
            shell[:, 0] = y
    trace = c.shell_trace@shell.ravel()
    np.testing.assert_array_equal(trace[3:5], [0., 0.])
    assert trace[5] == pytest.approx(yaw, abs=1e-15)


@pytest.mark.parametrize("axis", range(6))
def test_six_common_rigid_fields_reproduce_reference_spatial_port(axis):
    c = compiled()
    t, omega = np.zeros(3), np.zeros(3)
    (t if axis < 3 else omega)[axis % 3] = 1.
    local = np.zeros((7, 6))
    local[:6, :3] = t+np.cross(omega, c.shell_positions_m)
    local[:6, 3:] = omega
    local[6, :3] = t+np.cross(omega, c.beam_position_m)
    local[6, 3:] = omega
    np.testing.assert_allclose(c.gap(local.ravel()), 0., rtol=0., atol=2e-15)
    np.testing.assert_allclose(c.shell_trace@local[:6].ravel(),
                               np.r_[t+np.cross(omega, c.centroid_m), omega], atol=2e-15)


def test_transpose_force_moment_and_work_include_eccentric_signs():
    c = compiled()
    multiplier = np.array([2., -3., 5., 7., -11., 13.])
    covectors = c.transpose_work(multiplier).reshape(7, 6)
    xyz = np.vstack((c.shell_positions_m, c.beam_position_m))
    np.testing.assert_allclose(covectors[:, :3].sum(axis=0), 0., atol=1e-14)
    moment = (np.cross(xyz, covectors[:, :3])+covectors[:, 3:]).sum(axis=0)
    np.testing.assert_allclose(moment, 0., atol=2e-14)
    np.testing.assert_array_equal(covectors[6], multiplier)
    np.testing.assert_allclose(covectors[:6, :3].sum(axis=0), -multiplier[:3], atol=1e-14)
    np.testing.assert_allclose((np.cross(c.shell_positions_m-c.centroid_m, covectors[:6, :3])+
                               covectors[:6, 3:]).sum(axis=0),
                              -np.cross(c.eccentricity_m, multiplier[:3])-multiplier[3:], atol=2e-14)
    q = np.linspace(-.4, .6, 42)
    assert float(q@c.transpose_work(multiplier)) == pytest.approx(float(multiplier@c.gap(q)), abs=2e-14)


def test_nonrigid_transverse_shear_mode_is_admitted_but_rigid_node_law_rejects():
    c = compiled()
    q = np.zeros((7, 6))
    q[:6, 2] = c.shell_positions_m[:, 0]-c.centroid_m[0]
    np.testing.assert_allclose(c.gap(q.ravel()), 0., atol=1e-15)
    np.testing.assert_allclose(c.planar_gradients@q[:6, 2], [1., 0.], atol=1e-15)
    # A transverse slope changes no director: the law must not manufacture pitch.
    np.testing.assert_array_equal((c.shell_trace@q[:6].ravel())[3:], np.zeros(3))
    gaps = [reference_shell_matrix(x, c.beam_position_m)@row+q[6]
            for x, row in zip(c.shell_positions_m, q[:6])]
    assert np.linalg.norm(gaps) > 1.


def test_shell_drilling_coordinates_have_no_port_work():
    c = compiled()
    np.testing.assert_array_equal(c.constraint_matrix[:, 5:36:6], np.zeros((6, 6)))
    q = np.zeros(42)
    q[5:36:6] = np.arange(1., 7.)
    np.testing.assert_array_equal(c.gap(q), np.zeros(6))
    lam = np.array([0., 0., 0., 0., 0., 1.])
    actions = c.transpose_work(lam).reshape(7, 6)
    np.testing.assert_array_equal(actions[:6, 3:], np.zeros((6, 3)))
    assert np.linalg.norm(actions[:6, :3]) > 0.
    # Independent rigid boundary field u=(-y,x,0) gives unit yaw. Its work is
    # the force-couple moment about the centroid, without a shell rz coordinate.
    x, y = (c.shell_positions_m-c.centroid_m)[:, :2].T
    shell_force = actions[:6, :3]
    assert x@shell_force[:, 1]-y@shell_force[:, 0] == pytest.approx(-1., abs=1e-15)
    boundary_displacement = np.column_stack((-y, x, np.zeros(6)))
    assert np.sum(boundary_displacement*shell_force) == pytest.approx(-1., abs=1e-15)


def test_inventory_reordering_and_reidentified_elements_preserve_physical_map():
    definition, nodes, hosts, beam = fixture()
    first = footprint.compile_footprint(definition, nodes, hosts, beam)
    reordered = footprint.compile_footprint(definition, tuple(reversed(nodes)), tuple(reversed(hosts)), beam)
    assert first.identity == reordered.identity
    np.testing.assert_array_equal(first.constraint_matrix, reordered.constraint_matrix)
    renamed = {n.node_id: n.node_id+200 for n in nodes}
    nodes = tuple(replace(n, node_id=renamed[n.node_id]) for n in reversed(nodes))
    hosts = tuple(footprint.CartesianQ4Host(h.element_id+100, tuple(renamed[n] for n in h.node_ids)) for h in reversed(hosts))
    definition = replace(definition, host_element_ids=(121, 122))
    changed = footprint.compile_footprint(definition, nodes, hosts, beam)
    assert first.identity != changed.identity
    np.testing.assert_array_equal(first.gather_slots, changed.gather_slots)
    np.testing.assert_array_equal(first.constraint_matrix, changed.constraint_matrix)


def test_owned_definition_and_compiled_arrays_cannot_alias_or_reenable_writes():
    xyz = [0., 0., 0.]
    node = footprint.FlatQ4Node(1, xyz, 0)
    xyz[0] = 99.
    assert node.coordinates_m == (0., 0., 0.)
    c = compiled()
    for array in (c.gather_slots, c.shell_positions_m, c.beam_position_m, c.centroid_m,
                  c.eccentricity_m, c.area_mean, c.planar_gradients, c.shell_trace, c.constraint_matrix):
        with pytest.raises(ValueError):
            array.setflags(write=True)
    q = np.arange(42., dtype=float)
    gathered = c.gather(q)
    q[:] = -1.
    np.testing.assert_array_equal(gathered, np.arange(42.))
    descriptor = c.descriptor()
    descriptor["host_element_ids"][0] = -1
    assert c.host_element_ids == (21, 22)


@pytest.mark.parametrize("change", (
    lambda d, n, h, b: (replace(d, bounds_xy_m=(-.1, 1.5, .25, .75)), n, h, b),
    lambda d, n, h, b: (replace(d, bounds_xy_m=(.1, .9, .25, .75)), n, h, b),
    lambda d, n, h, b: (d, (replace(n[0], q_offset=6),)+n[1:], h, b),
    lambda d, n, h, b: (d, (replace(n[0], coordinates_m=(.1, 0., 0.)),)+n[1:], h, b),
    lambda d, n, h, b: (d, (replace(n[0], coordinates_m=(0., 0., .01)),)+n[1:], h, b),
    lambda d, n, h, b: (d, tuple(replace(v, coordinates_m=(v.coordinates_m[0], v.coordinates_m[1], .1*v.coordinates_m[0])) for v in n), h, b),
    lambda d, n, h, b: (d, n, (h[0], h[0]), b),
    lambda d, n, h, b: (d, n, h, replace(b, q_offset=0)),
    lambda d, n, h, b: (d, n, h, replace(b, node_id=102)),
    lambda d, n, h, b: (d, n, (replace(h[0], node_ids=(1, 4, 5, 2)), h[1]), b),
    lambda d, n, h, b: (d, n, (replace(h[0], node_ids=(1, 3, 6, 4)), h[1]), b),
))
def test_unsupported_geometry_coverage_or_mapping_rejects(change):
    with pytest.raises(ValueError):
        footprint.compile_footprint(*change(*fixture()))


def test_axes_nonfinite_and_degenerate_declarations_reject_before_compilation():
    with pytest.raises(ValueError, match="identity"):
        footprint.PhysicalBeamNodePort(101, (1., .5, .2), 36,
                                       ((0., -1., 0.), (1., 0., 0.), (0., 0., 1.)))
    with pytest.raises(ValueError, match="finite"):
        footprint.FlatQ4Node(1, (np.nan, 0., 0.), 0)
    with pytest.raises(ValueError, match="positive rectangular"):
        footprint.DistributingFootprintDefinition("bad", (21, 22), 101, (1., 1., 0., 1.))
    with pytest.raises(ValueError, match="distinct"):
        footprint.DistributingFootprintDefinition("bad", (21, 21), 101, (0., 1., 0., 1.))


def test_finite_real_gather_gap_and_work_inputs_are_required():
    c = compiled()
    for call, bad in ((c.gather, np.zeros(41)), (c.gap, np.full(42, np.inf)),
                      (c.transpose_work, np.ones(6, dtype=complex))):
        with pytest.raises(ValueError):
            call(bad)
    assert c.descriptor()["public_admission"] is False
    assert c.descriptor()["production_qualified"] is False


def test_compiled_model_binding_and_local_shapes_cannot_be_replaced_inconsistently():
    c = compiled()
    with pytest.raises(ValueError, match="binding"):
        replace(c, beam_node_id=102)
    with pytest.raises(ValueError, match="compiled local map"):
        replace(c, shell_trace=np.zeros((6, 35)))
    with pytest.raises(ValueError, match="gather"):
        replace(c, gather_slots=np.zeros(42, dtype=np.int64))


def test_finite_inputs_with_unrepresentable_gap_or_work_results_reject():
    c = compiled()
    maximum = np.finfo(float).max
    q = np.zeros((7, 6))
    q[:6, 0], q[6, 0] = -maximum, maximum
    with pytest.raises(ValueError, match="representable local gap"):
        c.gap(q.ravel())
    definition, nodes, hosts, beam = fixture()
    eccentric = footprint.compile_footprint(definition, nodes, hosts,
                                            replace(beam, coordinates_m=(4., .3, .5)))
    with pytest.raises(ValueError, match="representable local work"):
        eccentric.transpose_work([0., maximum, 0., 0., 0., 0.])
