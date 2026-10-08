"""Offline work and parsing controls; no external-solver acceptance claim."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

_path = Path(__file__).resolve().parents[1] / 'scripts/r8_e04_ccx_rigid_pose_control.py'
_spec = importlib.util.spec_from_file_location('pose_control', _path)
pose = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pose)


def test_free_carrier_energy_stationarity_and_rigid_metric():
    oracle = pose.free_spring_expected()
    matrix = Rotation.from_rotvec(oracle['rotation_coordinate']).as_matrix()
    translation = np.array(oracle['reference_displacement'])

    def energy(v):
        current = pose.MARKERS @ (Rotation.from_rotvec(v[3:]).as_matrix() @ matrix).T
        displacement = current + translation + v[:3] - pose.MARKERS
        return .5 * pose.SPRING_STIFFNESS * np.sum(displacement**2) - pose.FORCE @ displacement[0]

    np.testing.assert_allclose(energy(np.zeros(6)), oracle['energy'], atol=1e-15)
    for axis in np.eye(6):
        h = 1e-6
        assert abs((energy(h*axis)-energy(-h*axis))/(2*h)) < 1e-9
        # This closed-form control selects the energy minimum, not merely any
        # incremental stationary branch an external solver might find.
        assert energy(1e-3*axis) > oracle['energy']
    displacement = np.array(oracle['marker_displacements'])
    for i in range(3):
        for j in range(i):
            np.testing.assert_allclose(np.linalg.norm(pose.MARKERS[i]+displacement[i]-
                pose.MARKERS[j]-displacement[j]), np.linalg.norm(pose.MARKERS[i]-pose.MARKERS[j]),
                rtol=1e-13, atol=1e-15)
    singular = oracle['singular_values']
    assert singular[1] > 1e-5 and singular[2] < 1e-14


def test_prescribed_coordinate_dual_reaction_has_correct_work():
    oracle = pose.expected()
    reaction = np.array(oracle['rotation_coordinate_reaction'])
    for axis in np.eye(3):
        h = 1e-6
        def work(w):
            return pose.FORCE @ (Rotation.from_rotvec(w).apply(pose.BEAM_POSITION))
        derivative = (work(pose.ROTATION+h*axis)-work(pose.ROTATION-h*axis))/(2*h)
        np.testing.assert_allclose(reaction @ axis, -derivative, atol=2e-11)


def fixture(folder, *, time=1., newline=b'\n'):
    folder.mkdir()
    (folder/'pose.inp').write_bytes(pose.deck().encode('ascii').replace(b'\n', newline))
    (folder/'stdout.log').write_text('Job finished')
    (folder/'stderr.log').write_text('')
    oracle = pose.expected()
    values = {i+1:p for i,p in enumerate(oracle['marker_displacements'])}
    values.update({100:oracle['reference_displacement'],101:oracle['rotation_coordinate'],200:[.001,0.,0.]})
    lines = [f'displacements (vx,vy,vz) for set PORTS and time {time:.7E}', '']
    lines += [str(node)+' '+' '.join(f'{v:.7E}' for v in row) for node,row in values.items()]
    (folder/'pose.dat').write_text('\n'.join(lines)+'\n')


def test_output_contract_accepts_only_transport_newline_change(tmp_path):
    folder = tmp_path/'good'; fixture(folder,newline=b'\r\n')
    report = pose.report(folder)
    assert report['oracle_print_rounding_bounds_compatible']
    assert report['programme_tolerance_pass'] is None
    assert report['port_rf_is_not_validated_wrench']
    assert len(report['executed_deck_sha256']) == 64
    # Change a literal mechanical load regardless of the current text spelling.
    (folder/'pose.inp').write_bytes((folder/'pose.inp').read_bytes()+b'*CLOAD\r\n1,1,1.\r\n')
    with pytest.raises(ValueError,match='deck differs'):pose.report(folder)


def test_output_contract_rejects_unfinished_or_failed_execution(tmp_path):
    folder = tmp_path/'short'; fixture(folder,time=.02135127)
    with pytest.raises(ValueError,match='load time'):pose.report(folder)
    fixture(tmp_path/'failed')
    (tmp_path/'failed/stdout.log').write_text('*ERROR: limit reached\nJob finished')
    with pytest.raises(ValueError,match='cleanly'):pose.report(tmp_path/'failed')
