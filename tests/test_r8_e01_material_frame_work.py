"""Analytic linear port-map controls; no structural or external solves."""
from hashlib import sha256
import json

import numpy as np
import pytest

from scripts import r8_e01_material_frame_work as work


XY = np.array(((0., -.5), (2., -.5), (2., .5), (0., .5)))
STATION = np.array((.8, -.2))


def rigid_field(translation, rotation):
    xyz = np.column_stack((XY, np.zeros(4)))
    return np.column_stack((translation+np.cross(rotation, xyz),
                            np.tile(rotation, (4, 1))))


@pytest.mark.parametrize('offset', ((0., 0., .125), (0., 0., -.125), (.25, -.125, .375)))
def test_rigid_translation_rotation_and_offset_work(offset):
    # Binary-exact rigid patch isolates the zero-shear identity from subtraction
    # of rounded decimal translations. The assertion threshold stays unchanged.
    t = np.array((.03125, -.0625, .125))
    omega = np.array((.015625, -.03125, .0625))
    station = np.array((.5, -.25))
    q = rigid_field(t, omega)
    matrix = work.shell_material_frame_map(XY, station, offset)
    expected = np.r_[t+np.cross(omega, np.r_[station, 0.]+offset), omega]
    np.testing.assert_allclose(matrix @ q.ravel(), expected, rtol=0., atol=2e-17)
    channels = work.shell_channels(XY, station, q)
    np.testing.assert_allclose(channels['transverse_shear'], 0., atol=1e-17)


def test_origin_transfer_and_analytic_unit_wrenches():
    base = work.shell_material_frame_map(XY, STATION)
    offset = np.array((.2, -.3, .1))
    shifted = work.shell_material_frame_map(XY, STATION, offset)
    for j in range(6):
        load = np.eye(6)[j]
        # Independent force/moment origin rule M_station = M_port + e cross F.
        at_station = np.r_[load[:3], load[3:]+np.cross(offset, load[:3])]
        np.testing.assert_allclose(work.adjoint_wrench(shifted, load),
                                   base.T @ at_station, rtol=0., atol=2e-16)
    # A unit yaw moment is a pure translational couple, not nodal drilling.
    force = work.adjoint_wrench(base, (0., 0., 0., 0., 0., 1.)).reshape(4, 6)
    np.testing.assert_array_equal(force[:, 3:], 0.)
    np.testing.assert_allclose(force[:, :3].sum(axis=0), 0., atol=1e-16)
    xyz = np.column_stack((XY, np.zeros(4)))
    np.testing.assert_allclose(np.cross(xyz-np.r_[STATION, 0.], force[:, :3]).sum(axis=0),
                               (0., 0., 1.), rtol=0., atol=1e-16)


def test_symmetric_shear_and_independent_director_counterexamples():
    q = np.zeros((4, 6))
    q[:, 0] = .03*XY[:, 1]
    q[:, 1] = .03*XY[:, 0]
    channels = work.shell_channels(XY, STATION, q)
    assert channels['material_rotation'][2] == pytest.approx(0., abs=1e-17)
    # A line-tangent triad would rotate .03 rad: not the in-plane polar spin.
    _, dx, _ = work.rectangular_patch(XY, STATION)
    assert dx @ q[:, 1] == pytest.approx(.03)
    q = np.zeros((4, 6))
    q[:, 2] = .02*XY[:, 0]
    q[:, 4] = .04
    channels = work.shell_channels(XY, STATION, q)
    np.testing.assert_allclose(channels['independent_director_xy'], (.04, 0.))
    np.testing.assert_allclose(channels['surface_normal_xy'], (-.02, 0.))
    np.testing.assert_allclose(channels['transverse_shear'], (.06, 0.))
    assert work.shell_material_frame_map(XY, STATION)[4] @ q.ravel() == pytest.approx(.04)


def test_native_nodal_yaw_is_a_different_law():
    q = np.zeros((4, 6)); q[0, 5] = .02
    native = work.native_nodal_pose_map(4, 0, (0., 0., .1))
    recovered = work.shell_material_frame_map(XY, XY[0], (0., 0., .1))
    assert (native @ q.ravel())[5] == .02
    np.testing.assert_array_equal(recovered @ q.ravel(), 0.)
    np.testing.assert_array_equal(work.adjoint_wrench(native, (0., 0., 0., 0., 0., 1.))[5], 1.)


def test_expanded_face_pair_reproduces_independent_director_not_surface_normal():
    h = .07
    q = np.zeros((4, 6))
    q[:, :3] = np.column_stack((.02*XY[:, 0], -.01*XY[:, 1], .03*XY[:, 0]))
    q[:, 3:5] = (.04, -.05)
    director_delta = np.column_stack((q[:, 4], -q[:, 3], np.full(4, .06)))
    pairs = np.column_stack((q[:, :3]-h/2*director_delta,
                             q[:, :3]+h/2*director_delta))
    offset = (0., 0., .1)
    matrix = work.expanded_material_frame_map(XY, STATION, h, offset)
    port = matrix @ pairs.ravel()
    np.testing.assert_allclose(port[:6], work.shell_material_frame_map(XY, STATION, offset) @ q.ravel(),
                               rtol=0., atol=1e-16)
    assert port[6] == pytest.approx(.06, abs=1e-16)
    # Thickness-channel forces do no net force/moment work, but remain nonzero.
    force = work.adjoint_wrench(matrix, (0., 0., 0., 0., 0., 0., 1.)).reshape(4, 2, 3)
    np.testing.assert_allclose(force.sum(axis=(0, 1)), 0., atol=1e-15)
    xyz = np.stack((np.column_stack((XY, np.full(4, -h/2))),
                    np.column_stack((XY, np.full(4, h/2)))), axis=1)
    np.testing.assert_allclose(np.cross(xyz, force).sum(axis=(0, 1)), 0., atol=1e-15)
    assert float(np.sum(force*pairs.reshape(4, 2, 3))) == pytest.approx(.06, abs=1e-16)


@pytest.mark.parametrize('expanded', (False, True))
def test_actual_linear_derivative_and_adjoint_with_supported_columns(expanded):
    matrix = (work.expanded_material_frame_map(XY, STATION, .07, (.1, .2, .3)) if expanded
              else work.shell_material_frame_map(XY, STATION, (.1, .2, .3)))
    q = np.arange(24, dtype=float)*.001
    dq = np.cos(np.arange(24))*.01
    load = np.arange(matrix.shape[0], dtype=float)+1.
    for eps in (1e-2, 1e-3, 1e-4):
        numerical = (matrix @ (q+eps*dq)-matrix @ (q-eps*dq))/(2*eps)
        np.testing.assert_allclose(numerical, matrix @ dq, rtol=0., atol=2e-12)
    dq[:6] = 0.  # Preserve supported force entries; zero their virtual motion.
    nodal = work.adjoint_wrench(matrix, load)
    assert load @ (matrix @ dq) == pytest.approx(nodal @ dq, abs=1e-15)
    assert np.any(nodal[:6] != 0.)


def test_unit_scaling_preserves_rotations_and_port_translation():
    scale = 1000.
    q = rigid_field(np.array((.02, -.03, .04)), np.array((.01, -.02, .03)))
    large_q = q.copy(); large_q[:, :3] *= scale
    original = work.shell_material_frame_map(XY, STATION, (0., 0., .1)) @ q.ravel()
    scaled = work.shell_material_frame_map(XY*scale, STATION*scale, (0., 0., .1*scale)) @ large_q.ravel()
    np.testing.assert_allclose(scaled[:3], scale*original[:3], rtol=0., atol=1e-14)
    np.testing.assert_allclose(scaled[3:], original[3:], rtol=0., atol=1e-17)


@pytest.mark.parametrize('xy,station', ((XY[[0, 2, 1, 3]], STATION), (XY, (3., 0.)),
                                        (XY*np.nan, STATION)))
def test_reject_unsupported_geometry(xy, station):
    with pytest.raises(ValueError):
        work.shell_material_frame_map(xy, station)


def capture():
    return dict(shell_intervals=8, transverse_intervals=4,
                native_coupled_shell_displacements={str(i): [0.]*6 for i in range(1, 46)})


def test_saved_field_identity_and_hash_guards(tmp_path):
    value = capture()
    value['native_coupled_shell_displacements']['2'][5] = .01
    path = tmp_path/'capture.json'; raw = json.dumps(value).encode(); path.write_bytes(raw)
    result = work.read_bound_capture(path, sha256(raw).hexdigest())
    assert len(result['diagnostic']['samples']) == 9
    assert result['diagnostic']['samples'][1]['nodal_yaw_minus_material_spin'] == .01
    assert result['diagnostic']['maximum_abs_incident_spin_jump_rad'] == 0.
    assert (result['diagnostic']['samples'][-1]['material_rotation'][2] ==
            result['diagnostic']['samples'][-1]['material_spin_left_rad'])
    with pytest.raises(ValueError, match='hash mismatch'):
        work.read_bound_capture(path, '0'*64)
    value['shell_intervals'] = 4
    with pytest.raises(ValueError, match='identity'):
        work.diagnose_e01_capture(value)
    external = capture()
    field = external.pop('native_coupled_shell_displacements')
    external['external_coupled_shell_displacements'] = field
    assert (work.diagnose_e01_capture(external)['originating_field'] ==
            'external_coupled_shell_displacements')
    field['1'][0] = .01
    with pytest.raises(ValueError, match='root-field guard'):
        work.diagnose_e01_capture(external)


def test_incident_material_spin_reports_both_host_sides_and_affine_control():
    value = capture()
    field = value['native_coupled_shell_displacements']
    field['2'][1] = .1
    diagnostic = work.diagnose_e01_capture(value)
    station = diagnostic['samples'][1]
    assert station['material_spin_left_rad'] == pytest.approx(.2)
    assert station['material_spin_right_rad'] == pytest.approx(-.2)
    assert station['incident_spin_jump_rad'] == pytest.approx(-.4)
    assert station['material_rotation'][2] == station['material_spin_right_rad']
    assert diagnostic['maximum_abs_incident_spin_jump_rad'] == pytest.approx(.4)
    assert diagnostic['samples'][0]['material_spin_left_rad'] is None
    assert diagnostic['samples'][-1]['material_spin_right_rad'] is None

    for row in range(5):
        for column in range(9):
            field[str(1+9*row+column)] = [0., .02*column/4, 0., 0., 0., 0.]
    affine = work.diagnose_e01_capture(value)
    assert affine['maximum_abs_incident_spin_jump_rad'] < 1e-16
    assert all(sample['material_rotation'][2] == pytest.approx(.01)
               for sample in affine['samples'])


def test_pure_x_torque_work_at_shared_vertex_is_independent_of_incident_yaw_host():
    left_xy = np.array(((0., -.5), (1., -.5), (1., 0.), (0., 0.)))
    right_xy = left_xy + np.array((1., 0.))
    station = np.array((1., -.5))
    left_q = np.zeros((4, 6))
    right_q = np.zeros((4, 6))
    # The same physical corner has one director rotation in both incident hosts.
    left_q[1, 3] = right_q[0, 3] = 2.e-5
    # Continuous shared displacement with different one-sided polar gradients.
    left_q[1, 1] = right_q[0, 1] = .1
    left_map = work.shell_material_frame_map(left_xy, station)
    right_map = work.shell_material_frame_map(right_xy, station)
    left_pose = left_map @ left_q.ravel()
    right_pose = right_map @ right_q.ravel()
    assert left_pose[5] == pytest.approx(.05)
    assert right_pose[5] == pytest.approx(-.05)
    assert left_pose[3] == right_pose[3] == 2.e-5
    wrench = np.array((0., 0., 0., 100., 0., 0.))
    for mapping, field in ((left_map, left_q), (right_map, right_q)):
        nodal = work.adjoint_wrench(mapping, wrench)
        assert nodal @ field.ravel() == pytest.approx(.002)
        # A pure x-torque has no force work or polar-yaw work in this map.
        np.testing.assert_array_equal(nodal.reshape(4, 6)[:, :3], 0.)


def test_cli_never_overwrites_and_requires_hash_per_input(tmp_path):
    path = tmp_path/'capture.json'; raw = json.dumps(capture()).encode(); path.write_bytes(raw)
    out = tmp_path/'diagnostic.json'
    argv = ['--capture', str(path), '--expected-sha256', sha256(raw).hexdigest(), '--output', str(out)]
    record = work.main(argv)
    assert not record['qualified'] and not record['external_accuracy_scored']
    with pytest.raises(FileExistsError):
        work.main(argv)
