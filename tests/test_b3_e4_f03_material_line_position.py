"""Bounded G0 material-line position and value-only orientation checks."""

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from scripts._b3_e4_f03_native_fixture import build
from scripts.b3_e4_f03_distributed_surface_finite import FiniteSurfaceLineHybrid
from scripts.b3_e4_f03_material_line_position import MaterialLinePosition
from scripts.b3_e4_f03_plate_patch_work import local_grid, raw_e4_tangent
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


def _fixture(patch_cells=4):
    xs, ys = local_grid(patch_cells, transverse_cells=4)
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um", assemble=False)
    line = MaterialLinePosition(xs, ys, beam)
    return xs, ys, beam, line


def test_material_line_detects_even_slip_invisible_to_reduced_strip_pose():
    xs, ys, beam, line = _fixture()
    hybrid = FiniteSurfaceLineHybrid(xs, ys, beam, thickness=.035)
    y2 = line.reference_nodes[:, 1]**2
    mean_y2 = sum(point.weight*(point.shape@y2[point.nodes])
                  for point in hybrid.points)
    step = np.zeros((line.shell_count, 6))
    terminal = ((line.reference_nodes[:, 0] >= .9-1e-12) &
                (np.abs(line.reference_nodes[:, 1]) <= .05+1e-12))
    step[terminal, 2] = .01*(y2[terminal]-mean_y2)
    beam_step = np.zeros(beam.context.count)
    direction = np.r_[step.ravel(), beam_step]
    assert np.max(np.abs(hybrid.reference_trace()@direction)) < 1e-12
    detected = line.reference_jacobian()@direction
    assert np.max(np.abs(detected)) > 1e-6
    physical_tangent, physical = raw_e4_tangent(xs, ys, thickness=.035)
    assert .5*step.ravel()@physical@step.ravel() > 0.
    assert np.max(np.abs(step[line.reference_nodes[:, 0] <= -.5+1e-12])) == 0.
    assert np.isfinite(physical_tangent).all()


def test_material_line_reference_rigid_translation_and_shear_patch():
    xs, ys, beam, line = _fixture()
    state = beam.context.initial.mechanical
    identity = np.broadcast_to(np.eye(3), (line.shell_count, 3, 3))
    assert np.max(np.abs(line.evaluate(line.reference_nodes, identity, state))) < 1e-12
    assert np.max(np.abs(line.orientation_gap(
        line.reference_nodes, identity, state))) < 1e-12
    jacobian = line.reference_jacobian()
    shell = np.zeros((line.shell_count, 6))
    beam_step = np.zeros(beam.context.count)
    shell[:, :3] = (.01, -.02, .03)
    for node in range(len(beam.abscissae)):
        beam_step[6*node:6*node+3] = (.01, -.02, .03)
    assert np.max(np.abs(jacobian@np.r_[shell.ravel(), beam_step])) < 1e-12
    shell[:] = 0.
    beam_step[:] = 0.
    slope = 1e-4
    shell[:, 2] = slope*np.maximum(line.reference_nodes[:, 0], 0.)
    for node, x in enumerate(beam.abscissae):
        beam_step[6*node+2] = slope*x
    assert np.max(np.abs(jacobian@np.r_[shell.ravel(), beam_step])) < 1e-12
    assert np.max(np.abs(shell[line.reference_nodes[:, 0] <= -.5+1e-12])) == 0.
    assert beam_step[2] == 0.
    shell_coordinates = line.reference_nodes+shell[:, :3]
    candidate = beam.context.advance(state, beam_step)
    assert np.max(np.abs(line.orientation_gap(
        shell_coordinates, identity, candidate))) < 1e-10


def test_material_line_jacobian_uses_actual_native_chart():
    _, _, beam, line = _fixture()
    rng = np.random.default_rng(231)
    shell = rng.normal(size=(line.shell_count, 6))*.1
    beam_step = rng.normal(size=beam.context.count)*.1
    shell[line.reference_nodes[:, 0] <= -.5+1e-12] = 0.
    beam_step[list(beam.context.fixed)] = 0.
    direction = np.r_[shell.ravel(), beam_step]
    predicted = (line.reference_jacobian()@direction).reshape(-1, 3)
    h = 1e-6
    def trial(sign):
        coordinates = line.reference_nodes+sign*h*shell[:, :3]
        frames = Rotation.from_rotvec(sign*h*shell[:, 3:]).as_matrix()
        candidate = beam.context.advance(
            beam.context.initial.mechanical, sign*h*beam_step)
        return line.evaluate(coordinates, frames, candidate)
    finite_difference = (trial(1)-trial(-1))/(2*h)
    assert np.max(np.abs(finite_difference-predicted)) < 2e-8


def test_mixed_s3_material_line_detects_centerline_slip():
    xs, ys, beam, _ = _fixture(patch_cells=2)
    line = MaterialLinePosition(xs, ys, beam, mixed_s3=True)
    step = np.zeros((line.shell_count, 6))
    terminal = line.reference_nodes[:, 0] >= .9-1e-12
    step[terminal, 2] = 1e-5
    direction = np.r_[step.ravel(), np.zeros(beam.context.count)]
    assert np.max(np.abs(line.reference_jacobian()@direction)) > 9e-6
    frames = np.broadcast_to(np.eye(3), (line.shell_count, 3, 3))
    assert np.max(np.abs(line.evaluate(
        line.reference_nodes, frames, beam.context.initial.mechanical))) < 1e-12
    assert np.max(np.abs(line.orientation_gap(
        line.reference_nodes, frames, beam.context.initial.mechanical))) < 1e-12
    tilted = frames.copy()
    tilted[terminal] = Rotation.from_rotvec((0., 1e-3, 0.)).as_matrix()
    assert np.max(np.abs(line.orientation_gap(
        line.reference_nodes, tilted, beam.context.initial.mechanical))) > 5e-4


def test_material_line_rejects_unexplained_reference_gap():
    xs, ys = local_grid(2, transverse_cells=4)
    beam = build(12, z_offset=.0675,
                 reference_profile="c1_tangent_2um", assemble=False)
    with pytest.raises(ValueError, match="reference geometry is not coincident"):
        MaterialLinePosition(xs, ys, beam, beam_depth=.09)


def test_material_line_finite_common_rigid_motion_is_objective():
    _, _, beam, line = _fixture(patch_cells=2)
    rotation_vector = np.array((.2, -.15, .1))
    rotation = Rotation.from_rotvec(rotation_vector).as_matrix()
    translation = np.array((.03, -.02, .04))
    shell_coordinates = line.reference_nodes.copy()
    shell_frames = np.broadcast_to(np.eye(3), (line.shell_count, 3, 3)).copy()
    shell_bond = line.reference_nodes[:, 0] >= .9-1e-12
    shell_coordinates[shell_bond] = (
        line.reference_nodes[shell_bond]@rotation.T+translation)
    shell_frames[shell_bond] = rotation
    base = beam.context.initial.mechanical
    step = np.zeros(beam.context.count)
    for node, x in enumerate(beam.abscissae):
        if x < .9-1e-12:
            continue
        reference = base.positions[node]+base.position_low[node]
        step[6*node:6*node+3] = rotation@reference+translation-reference
        step[6*node+3:6*node+6] = rotation_vector
    for element in range(len(beam.context.elements)):
        for cell in (0, 1):
            if beam.abscissae[2*element+cell] < .9-1e-12:
                continue
            first = beam.context.nodal_count+24*element+3*cell
            step[first:first+3] = rotation_vector
    candidate = beam.context.advance(base, step)
    assert np.max(np.abs(line.evaluate(
        shell_coordinates, shell_frames, candidate))) < 1e-10
    assert np.max(np.abs(line.orientation_gap(
        shell_coordinates, shell_frames, candidate))) < 1e-10


def test_material_line_orientation_uses_director_without_drilling():
    _, _, beam, line = _fixture(patch_cells=2)
    identity = np.broadcast_to(np.eye(3), (line.shell_count, 3, 3)).copy()
    bond = line.reference_nodes[:, 0] >= .9-1e-12
    pitch = identity.copy()
    pitch[bond] = Rotation.from_rotvec((0., 1e-3, 0.)).as_matrix()
    state = beam.context.initial.mechanical
    assert np.max(np.abs(line.orientation_gap(
        line.reference_nodes, pitch, state))) > 5e-4
    drilling = identity.copy()
    drilling[bond] = Rotation.from_rotvec((0., 0., 1e-3)).as_matrix()
    assert np.max(np.abs(line.orientation_gap(
        line.reference_nodes, drilling, state))) < 1e-12


@pytest.mark.parametrize("mixed_s3", (False, True))
def test_material_line_orientation_jacobian_uses_native_chart(mixed_s3):
    xs, ys, beam, _ = _fixture(patch_cells=2)
    line = MaterialLinePosition(xs, ys, beam, mixed_s3=mixed_s3)
    rng = np.random.default_rng(345 if mixed_s3 else 346)
    shell = rng.normal(size=(line.shell_count, 6))*.1
    beam_step = rng.normal(size=beam.context.count)*.1
    shell[line.reference_nodes[:, 0] <= -.5+1e-12] = 0.
    beam_step[list(beam.context.fixed)] = 0.
    direction = np.r_[shell.ravel(), beam_step]
    predicted = (line.reference_orientation_jacobian()@direction).reshape(-1, 3)
    step_size = 1e-6

    def trial(sign):
        coordinates = line.reference_nodes+sign*step_size*shell[:, :3]
        frames = Rotation.from_rotvec(
            sign*step_size*shell[:, 3:]).as_matrix()
        candidate = beam.context.advance(
            beam.context.initial.mechanical, sign*step_size*beam_step)
        return line.orientation_gap(coordinates, frames, candidate)

    finite_difference = (trial(1)-trial(-1))/(2*step_size)
    assert np.max(np.abs(finite_difference-predicted)) < 2e-8

    drilling = np.zeros_like(direction)
    bond = line.reference_nodes[:, 0] >= .9-1e-12
    drilling[:6*line.shell_count].reshape(-1, 6)[bond, 5] = 1.
    assert np.max(np.abs(line.reference_orientation_jacobian()@drilling)) < 1e-12


@pytest.mark.parametrize("mixed_s3", (False, True))
def test_material_line_orientation_jacobian_at_nonzero_gap(mixed_s3):
    xs, ys, beam, _ = _fixture(patch_cells=2)
    line = MaterialLinePosition(xs, ys, beam, mixed_s3=mixed_s3)
    rng = np.random.default_rng(349 if mixed_s3 else 350)
    shell_base = rng.normal(size=(line.shell_count, 6))*.02
    shell_direction = rng.normal(size=(line.shell_count, 6))*.1
    base_step = rng.normal(size=beam.context.count)*.02
    beam_direction = rng.normal(size=beam.context.count)*.1
    fixed_shell = line.reference_nodes[:, 0] <= -.5+1e-12
    shell_base[fixed_shell] = 0.
    shell_direction[fixed_shell] = 0.
    base_step[list(beam.context.fixed)] = 0.
    beam_direction[list(beam.context.fixed)] = 0.
    coordinates = line.reference_nodes+shell_base[:, :3]
    frames = Rotation.from_rotvec(shell_base[:, 3:]).as_matrix()
    state = beam.context.advance(beam.context.initial.mechanical, base_step)
    direction = np.r_[shell_direction.ravel(), beam_direction]
    predicted = (line.orientation_jacobian(
        coordinates, frames, state)@direction).reshape(-1, 3)
    assert np.max(np.abs(line.orientation_gap(coordinates, frames, state))) > 1e-4
    step_size = 1e-6

    def trial(sign):
        trial_coordinates = coordinates+sign*step_size*shell_direction[:, :3]
        update = Rotation.from_rotvec(
            sign*step_size*shell_direction[:, 3:]).as_matrix()
        trial_frames = update@frames
        trial_state = beam.context.advance(state, sign*step_size*beam_direction)
        return line.orientation_gap(trial_coordinates, trial_frames, trial_state)

    finite_difference = (trial(1)-trial(-1))/(2*step_size)
    assert np.max(np.abs(finite_difference-predicted)) < 2e-8


def test_material_line_orientation_couple_work_cancels_on_common_rigid_motion():
    _, _, beam, line = _fixture(patch_cells=2)
    shell_coordinates = line.reference_nodes.copy()
    shell_frames = np.broadcast_to(np.eye(3), (line.shell_count, 3, 3)).copy()
    beam_state = beam.context.initial.mechanical
    omega = np.array((.03, -.04, .05))
    translation = np.array((.002, -.003, .004))
    shell_step = np.zeros((line.shell_count, 6))
    shell_bond = line.reference_nodes[:, 0] >= .9-1e-12
    shell_step[shell_bond, :3] = (
        np.cross(omega, shell_coordinates[shell_bond])+translation)
    shell_step[shell_bond, 3:] = omega
    beam_step = np.zeros(beam.context.count)
    for node, x in enumerate(beam.abscissae):
        if x < .9-1e-12:
            continue
        position = beam_state.positions[node]+beam_state.position_low[node]
        beam_step[6*node:6*node+3] = np.cross(omega, position)+translation
        beam_step[6*node+3:6*node+6] = omega
    for element in range(len(beam.context.elements)):
        for cell in (0, 1):
            if beam.abscissae[2*element+cell] < .9-1e-12:
                continue
            first = beam.context.nodal_count+24*element+3*cell
            beam_step[first:first+3] = omega
    jacobian = line.reference_orientation_jacobian()
    weights = np.repeat([station.weight for station in line.stations], 3)
    multiplier = weights*np.tile((1.3, -2.1, 3.2), len(line.stations))
    split = 6*line.shell_count
    shell_work = shell_step.ravel()@(jacobian[:, :split].T@multiplier)
    beam_work = beam_step@(jacobian[:, split:].T@multiplier)
    assert abs(shell_work) > 1e-6
    assert abs(shell_work+beam_work) < 1e-10*abs(shell_work)
