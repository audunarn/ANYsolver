"""Bounded G0 translational material-line feasibility; no full pose claim."""

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
