"""Independent flat-field checks for the two-sided solid line observable."""

import numpy as np

from scripts.b3_e4_f03_c1_material_line_solid_port import (
    _quad8_dx, build_flat_solid_line_port,
)
from scripts.b3_e4_f03_ccx_solid_bond_screen import _quad8_shape
from scripts._b3_e4_f03_native_fixture import build
from scripts.b3_e4_f03_local_footprint_work import structured_q4_point_shape
from scripts.b3_e4_f03_material_line_position import MaterialLinePosition
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


def _faces():
    x = np.linspace(.9, 1., 9)
    y = np.linspace(-.05, .05, 17)
    x_even, y_even = x[::2], y[::2]
    sites = ({(float(a), float(b)) for a in x_even for b in y_even} |
             {(float(a), float(b)) for a in x[1::2] for b in y_even} |
             {(float(a), float(b)) for a in x_even for b in y[1::2]})
    coords = {}
    plate, bar = set(), set()
    for domain, heights in ((plate, (-.0175, .0175)),
                            (bar, (.0175, .1175))):
        for z in heights:
            for a, b in sorted(sites):
                node = len(coords)+1
                coords[node] = np.array((a, b, z))
                domain.add(node)
    return coords, plate, bar


def _wrench(actions, coords, center):
    force = sum(actions.values(), np.zeros(3))
    moment = sum((np.cross(coords[node]-center, value)
                  for node, value in actions.items()), np.zeros(3))
    return force, moment


def test_quad8_longitudinal_derivative_is_analytic():
    for xi, eta in ((-.65, -.7), (.3, .2), (.8, .9)):
        h = 1e-30
        derivative = np.imag(_quad8_shape(xi+1j*h, eta))/h
        np.testing.assert_allclose(_quad8_dx(xi, eta, .025),
                                   2*derivative/.025, rtol=1e-13, atol=1e-12)


def test_solid_line_pose_preserves_rigid_work_and_physical_shear():
    coords, plate, bar = _faces()
    port = build_flat_solid_line_port(coords, plate, bar, .9375)
    assert np.linalg.matrix_rank(port.gap_jacobian, tol=1e-10) == 6
    origin = np.asarray(port.reference_point_m)

    translation = np.array((.02, -.03, .04))
    rotation = np.array((.003, -.004, .005))
    common = {node: translation+np.cross(rotation, xyz)
              for node, xyz in coords.items()}
    np.testing.assert_allclose(port.gap(common), 0., atol=2e-12)

    gamma = .002
    shear = {node: np.array((0., 0., gamma*xyz[0])) if node in plate
             else np.zeros(3) for node, xyz in coords.items()}
    np.testing.assert_allclose(port.gap(shear),
                               (0., 0., gamma*.9375, 0., 0., 0.),
                               atol=2e-12)
    lateral = {node: np.array((0., gamma*xyz[0], 0.)) if node in plate
               else np.zeros(3) for node, xyz in coords.items()}
    np.testing.assert_allclose(port.gap(lateral),
                               (0., gamma*.9375, 0., 0., 0., -gamma),
                               atol=2e-12)
    pitch = {node: np.array((gamma*xyz[2], 0., 0.)) if node in plate
             else np.zeros(3) for node, xyz in coords.items()}
    np.testing.assert_allclose(port.gap(pitch),
                               (gamma*.0175, 0., 0., 0., -gamma, 0.),
                               atol=2e-12)
    roll = {node: gamma*np.cross(np.array((1., 0., 0.)),
                                  xyz-np.array((xyz[0], 0., .0675)))
            if node in bar else np.zeros(3)
            for node, xyz in coords.items()}
    np.testing.assert_allclose(port.gap(roll),
                               (0., -.05*gamma, 0., gamma, 0., 0.),
                               atol=2e-12)

    dual = np.array((4., -6., 8., 100., -70., 30.))
    actions = port.nodal_actions(dual)
    total_force, total_moment = _wrench(actions, coords, origin)
    np.testing.assert_allclose(total_force, 0., atol=2e-12)
    np.testing.assert_allclose(total_moment, 0., atol=2e-11)
    random = {node: np.array((.01*np.sin(node), .02*np.cos(node),
                              .005*np.sin(2*node))) for node in coords}
    work = sum(float(value@random[node]) for node, value in actions.items())
    np.testing.assert_allclose(work, dual@port.gap(random), atol=2e-12)


def test_pure_torque_has_opposite_plate_and_bar_moment():
    coords, plate, bar = _faces()
    port = build_flat_solid_line_port(coords, plate, bar, .9375)
    actions = port.nodal_actions(np.array((0., 0., 0., 100., 0., 0.)))
    center = np.asarray(port.reference_point_m)
    plate_force, plate_moment = _wrench(
        {node: value for node, value in actions.items() if node in plate},
        coords, center)
    bar_force, bar_moment = _wrench(
        {node: value for node, value in actions.items() if node in bar},
        coords, center)
    np.testing.assert_allclose(plate_force, 0., atol=2e-12)
    np.testing.assert_allclose(bar_force, 0., atol=2e-12)
    np.testing.assert_allclose(plate_moment, (-100., 0., 0.), atol=2e-11)
    np.testing.assert_allclose(bar_moment, (100., 0., 0.), atol=2e-11)


def test_section_warp_orthogonal_to_rigid_port_remains_free():
    coords, plate, bar = _faces()
    port = build_flat_solid_line_port(coords, plate, bar, .9375)
    half_width = .05
    warp = {node: np.array((xyz[1]**2-half_width**2/3., 0., 0.))
            if node in bar else np.zeros(3)
            for node, xyz in coords.items()}
    assert max(np.linalg.norm(value) for value in warp.values()) > 1e-3
    np.testing.assert_allclose(port.gap(warp), 0., atol=2e-15)


def test_solid_port_agrees_with_native_line_on_representable_fields():
    """A Q8 face and rigid section recover the declared native Q4/B3 trace."""
    coords, plate, bar = _faces()
    station_x = .9375
    port = build_flat_solid_line_port(coords, plate, bar, station_x)
    xs = np.linspace(.9, 1., 5)
    ys = np.linspace(-.05, .05, 5)
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um", assemble=False)
    line = MaterialLinePosition(xs, ys, beam)
    station_index = next(k for k, station in enumerate(line.stations)
                         if abs(station.x-station_x) < 1e-12)
    station = line.stations[station_index]
    native = np.vstack((
        line.reference_jacobian().reshape(len(line.stations), 3, -1)[station_index],
        line.reference_orientation_jacobian().reshape(len(line.stations), 3, -1)[station_index],
    ))
    beam_tangent = station.port.tangent(beam.context.initial.mechanical)
    rng = np.random.default_rng(733)
    for _ in range(3):
        shell_q = rng.normal(scale=1e-4, size=(line.shell_count, 6))
        beam_q = rng.normal(scale=1e-4, size=beam.context.count)
        spatial = beam_tangent@beam_q
        displacement = {}
        for node in port.node_ids:
            xyz = coords[node]
            if node in plate:
                support, shape = structured_q4_point_shape(xs, ys, xyz[0], xyz[1])
                displacement[node] = sum(
                    (weight*(shell_q[int(i), :3] +
                             np.cross(shell_q[int(i), 3:], (0., 0., xyz[2]))))
                    for i, weight in zip(support, shape)
                )
            else:
                assert node in bar
                displacement[node] = (spatial[:3] + np.cross(
                    spatial[3:], xyz-np.array((station_x, 0., .0675))))
        np.testing.assert_allclose(
            port.gap(displacement), native@np.r_[shell_q.ravel(), beam_q],
            rtol=1e-10, atol=2e-11)
