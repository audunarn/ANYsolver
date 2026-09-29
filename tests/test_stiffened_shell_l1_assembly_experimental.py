"""Bounded sparse-owner exercise of unqualified exact weak L1 work."""

from dataclasses import replace
import json

import numpy as np
import pytest

from anysolver import b3_ge, stiffened_shell
from anysolver._ge_beam3_retained_generalized_state import Mechanical
from anysolver._stiffened_shell_ge_checkpoint_binary import encode
from anysolver._stiffened_shell_ge_experimental import FINITE_CHECKPOINT
from anysolver._stiffened_shell_l1_assembly_experimental import SPACE_A, SPACE_B


def _definition(space=SPACE_A, *, expected_offset=(0., 0., 0.)):
    e, nu = 210e9, .3
    g = e/(2*(1+nu))
    section = b3_ge.EllipsoidalGeneralizedSection(
        np.diag((e*.01, g*.008, g*.008, g*1.6666666666666667e-5,
                 e*8.333333333333333e-6, e*8.333333333333333e-6)),
        np.eye(6), 1e20, 1e9)
    points = [(x, 0., .0675) for x in (0., .25, .5, .75, 1.)]
    beams = tuple(b3_ge.define_beam(
        "b3-ge", i+1, (101+2*i, 102+2*i, 103+2*i),
        np.array(points[2*i:2*i+3]), np.tile(np.eye(3), (3, 1, 1)),
        section, np.eye(6)) for i in range(2))
    xs = (0., .25, .5, .75, 1.)
    shell = stiffened_shell.ShellPanel(
        tuple(range(1, 11)),
        tuple((x, 0., 0.) for x in xs)+
        tuple((x, .2, 0.) for x in xs),
        tuple((i, i+1, i+6, i+5) for i in range(1, 5)),
        .035, e, nu, 7850.)
    line = stiffened_shell.ExperimentalL1Line(
        (1, 2, 3, 4, 5), ((0, 0), (0, 1), (1, 0), (1, 1)),
        space, expected_shell_offset=expected_offset)
    fixed = tuple(stiffened_shell.FixedCoordinate("shell", node, axis)
                  for node in (1, 6) for axis in range(6))
    return stiffened_shell.LinearDefinition(
        stiffened_shell.B3_GE_E4_PL_STIFFENED_SHELL_V1,
        shell, beams, (), fixed, (line,))


@pytest.mark.parametrize("space,rows", ((SPACE_A, 28), (SPACE_B, 20)))
def test_sparse_weak_line_matches_independent_dense_solution_and_restart(
        space, rows):
    definition = _definition(space)
    owner = stiffened_shell.create_analysis(definition=definition)
    assert owner.capabilities["status"] == "EXPERIMENTAL_NOT_QUALIFIED"
    assert owner.capabilities["attachment"] == (
        "experimental L1 weak-line candidate",)
    assert owner.capabilities["analysis"] == ("reference_linear",)
    assert owner.capabilities["experimental_line_spaces"] == (space,)
    assert owner.preflight()["experimental_line_samples"] == 8
    assert owner._C.shape[0] == rows
    assert len(owner._line_samples) == 8
    assert owner._C.nnz < owner._C.shape[0]*owner._C.shape[1]
    assert all(sample[0].port.retained_count == owner._beam_count
               for sample in owner._line_samples)
    action = (stiffened_shell.NodalAction(
        "beam", 105, (0., 0., 100., 0., 0., 0.)),)
    result = owner.solve_linear(action)
    assert result.status == "completed"
    assert result.free_equilibrium_ratio < 1e-8
    assert result.constraint_max < 1e-9
    load = owner._accepted[1]
    rhs = np.r_[load[owner._free], np.zeros(rows)]
    dense = np.linalg.solve(owner._A.toarray(), rhs)
    q = np.r_[result.shell_displacement, result.beam_coordinates]
    np.testing.assert_allclose(q[owner._free], dense[:len(owner._free)],
                               rtol=2e-8, atol=1e-11)
    np.testing.assert_allclose(result.multipliers, dense[len(owner._free):],
                               rtol=2e-8, atol=1e-7)
    np.testing.assert_allclose((owner._C@q), 0., atol=1e-9)
    support = result.reactions[:owner._shell_count].reshape(-1, 6)
    support_force = support[:, :3].sum(axis=0)
    support_moment = (support[:, 3:].sum(axis=0)+
                      np.cross(np.asarray(definition.shell.coordinates_m),
                               support[:, :3]).sum(axis=0))
    np.testing.assert_allclose(support_force, (0., 0., -100.), atol=1e-6)
    np.testing.assert_allclose(support_moment, (0., 100., 0.), atol=1e-5)
    saved = owner.checkpoint()
    fresh = stiffened_shell.create_analysis(definition=definition)
    recovered = fresh.restore(saved)
    np.testing.assert_array_equal(recovered.shell_displacement,
                                  result.shell_displacement)
    np.testing.assert_array_equal(recovered.beam_coordinates,
                                  result.beam_coordinates)
    with pytest.raises(ValueError, match="reference-linear"):
        fresh.solve(action, (1.,))
    assert fresh.recover().generation == result.generation


def test_weak_line_rejects_mismatched_reference_correspondence():
    definition = _definition(expected_offset=(0., 0., .01))
    with pytest.raises(ValueError, match="reference correspondence"):
        stiffened_shell.create_analysis(definition=definition)


def test_weak_line_rejects_repeated_material_connection():
    definition = _definition()
    repeated = replace(definition, lines=definition.lines*2)
    with pytest.raises(ValueError, match="repeated experimental L1"):
        stiffened_shell.create_analysis(definition=repeated)


def test_line_owner_rejects_finite_checkpoint_before_point_driver():
    definition = _definition()
    owner = stiffened_shell.create_analysis(definition=definition)
    payload = json.dumps({"schema": FINITE_CHECKPOINT,
                          "model": owner._identity}).encode("ascii")
    with pytest.raises(ValueError, match="reference-linear checkpoints"):
        owner.restore(payload)
    binary = encode("finite", owner._identity, 1, ())
    with pytest.raises(ValueError, match="reference-linear checkpoints"):
        owner.restore(binary)
    assert owner._accepted is None and owner._finite_driver is None


def test_supported_endpoint_point_overlapping_line_is_rejected():
    definition = replace(_definition(), points=(
        stiffened_shell.PointConnection(1, 101),))
    with pytest.raises(ValueError, match="line 0 shell=1..5"):
        stiffened_shell.create_analysis(definition=definition)


@pytest.mark.parametrize("space", (SPACE_A, SPACE_B))
def test_sparse_line_rows_match_independent_sampled_weak_work(space):
    owner = stiffened_shell.create_analysis(definition=_definition(space))
    n = 4
    row_count = owner._C.shape[0]
    sample_count = len(owner._line_samples)
    samples = np.zeros((6*sample_count, row_count))
    gaps = np.zeros((6*sample_count, owner._K.shape[0]))
    weights = np.empty(6*sample_count)
    positions = np.array([owner._beam_nodes[node][0] for node in owner._beam_ids])
    frames = np.array([owner._beam_nodes[node][1] for node in owner._beam_ids])
    state = Mechanical(positions, np.zeros_like(positions), frames,
                       np.tile(np.eye(3), (len(owner._beam_parts), 2, 1, 1)),
                       np.zeros((len(owner._beam_parts), 18)))
    for sample, (operator, slots, weight, edge, alpha) in enumerate(
            owner._line_samples):
        expected_alpha = .5+(-.5 if sample % 2 == 0 else .5)/np.sqrt(3.)
        shell_points = np.asarray(owner._definition.shell.coordinates_m)
        length = np.linalg.norm(shell_points[edge+1]-shell_points[edge])
        np.testing.assert_allclose(alpha, expected_alpha, rtol=0., atol=1e-15)
        np.testing.assert_allclose(weight, .5*length, rtol=0., atol=1e-15)
        local = operator.evaluate(np.zeros((2, 6)), state, np.zeros(6))
        rows = slice(6*sample, 6*sample+6)
        gaps[rows, slots] = local.gap_jacobian
        weights[rows] = weight
        for channel in range(6):
            row = 6*sample+channel
            if space == SPACE_A:
                if channel < 4:
                    start = channel*(n+1)
                    samples[row, start+edge:start+edge+2] = (1.-alpha, alpha)
                else:
                    samples[row, 4*(n+1)+(channel-4)*n+edge] = 1.
            elif channel < 4:
                samples[row, channel*n+edge] = 1.
            else:
                samples[row, 4*n+(channel-4)*(n//2)+edge//2] = 1.
    expected = samples.T@(weights[:, None]*gaps)
    np.testing.assert_allclose(owner._C.toarray(), expected, rtol=0., atol=3e-14)
    shell_drill = np.arange(5, owner._shell_count, 6)
    resultants = np.concatenate(tuple(
        owner._shell_count+6*len(owner._beam_ids)+24*i+np.arange(6, 24)
        for i in range(len(owner._beam_parts))))
    np.testing.assert_allclose(owner._C[:, shell_drill].toarray(), 0., atol=1e-12)
    np.testing.assert_array_equal(owner._C[:, resultants].toarray(), 0.)
    rng = np.random.default_rng(23)
    q = rng.normal(size=owner._K.shape[0])
    multiplier = rng.normal(size=row_count)
    np.testing.assert_allclose(multiplier@(owner._C@q),
                               (samples@multiplier)@(weights*(gaps@q)),
                               rtol=0., atol=1e-11)


@pytest.mark.parametrize("span,rows", ((1, 20), (2, 10)))
def test_bl5_sparse_rows_work_reaction_and_restart(span, rows):
    base = _definition()
    line = stiffened_shell.ExperimentalBL5Line(
        base.lines[0].shell_nodes, base.lines[0].beam_halfcells,
        multiplier_span=span)
    definition = replace(base, lines=(line,))
    owner = stiffened_shell.create_analysis(definition=definition)
    assert owner._C.shape[0] == rows
    assert owner.capabilities["attachment"] == (
        "experimental BL5 director-bond candidate",)
    assert owner.capabilities["analysis"] == ("reference_linear",)
    assert owner.capabilities["experimental_line_spaces"] == (
        f"BL5_P0_span_{span}",)
    assert "curved/reversed BL5 line mapping" in owner.capabilities["excluded"]
    action = (stiffened_shell.NodalAction(
        "beam", 105, (0., 0., 100., 0., 0., 0.)),)
    result = owner.solve_linear(action)
    assert result.status == "completed"
    assert result.free_equilibrium_ratio < 1e-8
    assert result.constraint_max < 1e-9
    q = np.r_[result.shell_displacement, result.beam_coordinates]
    load = owner._accepted[1]
    rhs = np.r_[load[owner._free], np.zeros(rows)]
    scale = np.r_[owner._coordinate_scale[owner._free],
                  1./owner._constraint_scale]
    dense = scale*np.linalg.solve(
        scale[:, None]*owner._A.toarray()*scale[None, :], scale*rhs)
    # The BL5 span-1 fixture has an ill-conditioned retained resultant;
    # compare physical coordinates and complete KKT residuals separately.
    physical = owner._free < owner._shell_count+6*len(owner._beam_ids)
    np.testing.assert_allclose(q[owner._free][physical],
                               dense[:len(owner._free)][physical],
                               rtol=2e-8, atol=1e-11)
    assert np.max(np.abs(owner._A@dense-rhs)) < 1e-8
    assert np.max(np.abs(owner._A@np.r_[q[owner._free], result.multipliers]-rhs)) < 1e-8
    np.testing.assert_allclose(owner._C@q, 0., atol=1e-9)
    support = result.reactions[:owner._shell_count].reshape(-1, 6)
    np.testing.assert_allclose(support[:, :3].sum(axis=0),
                               (0., 0., -100.), atol=1e-6)
    support_moment = (support[:, 3:].sum(axis=0)+
                      np.cross(np.asarray(definition.shell.coordinates_m),
                               support[:, :3]).sum(axis=0))
    np.testing.assert_allclose(support_moment, (0., 100., 0.), atol=1e-5)
    saved = owner.checkpoint()
    restored = stiffened_shell.create_analysis(definition=definition)
    np.testing.assert_array_equal(restored.restore(saved).beam_coordinates,
                                  result.beam_coordinates)


def test_bl5_line_rejects_wrong_reference_arm_and_duplicate():
    base = _definition()
    with pytest.raises(ValueError, match="ordered even-edge"):
        stiffened_shell.ExperimentalBL5Line(
            base.lines[0].shell_nodes, base.lines[0].beam_halfcells,
            expected_beam_arm=(0., 0., "invalid"))
    line = stiffened_shell.ExperimentalBL5Line(
        base.lines[0].shell_nodes, base.lines[0].beam_halfcells,
        expected_beam_arm=(0., 0., .05))
    with pytest.raises(ValueError, match="reference correspondence"):
        stiffened_shell.create_analysis(definition=replace(base, lines=(line,)))
    line = replace(line, expected_beam_arm=(0., 0., -.05))
    with pytest.raises(ValueError, match="repeated experimental BL5"):
        stiffened_shell.create_analysis(
            definition=replace(base, lines=(line, line)))


def test_bl5_multiplier_span_changes_checkpoint_identity():
    base = _definition()
    first = stiffened_shell.ExperimentalBL5Line(
        base.lines[0].shell_nodes, base.lines[0].beam_halfcells,
        multiplier_span=1)
    second = replace(first, multiplier_span=2)
    owner = stiffened_shell.create_analysis(
        definition=replace(base, lines=(first,)))
    owner.solve_linear((stiffened_shell.NodalAction(
        "beam", 105, (0., 0., 100., 0., 0., 0.)),))
    other = stiffened_shell.create_analysis(
        definition=replace(base, lines=(second,)))
    assert owner.preflight()["identity"] != other.preflight()["identity"]
    with pytest.raises(ValueError, match="incompatible mixed linear checkpoint"):
        other.restore(owner.checkpoint())


@pytest.mark.parametrize("span", (1, 2))
def test_bl5_sparse_rows_equal_sampled_weak_work(span):
    base = _definition()
    line = stiffened_shell.ExperimentalBL5Line(
        base.lines[0].shell_nodes, base.lines[0].beam_halfcells,
        multiplier_span=span)
    owner = stiffened_shell.create_analysis(
        definition=replace(base, lines=(line,)))
    positions = np.array([owner._beam_nodes[node][0] for node in owner._beam_ids])
    frames = np.array([owner._beam_nodes[node][1] for node in owner._beam_ids])
    state = Mechanical(positions, np.zeros_like(positions), frames,
                       np.tile(np.eye(3), (len(owner._beam_parts), 2, 1, 1)),
                       np.zeros((len(owner._beam_parts), 18)))
    independently_scattered = np.zeros(owner._C.shape)
    for operator, slots, weight, edge, _alpha in owner._line_samples:
        local = operator.evaluate(np.zeros((2, 6)), state, np.zeros(5))
        for channel in range(5):
            row = channel*(len(line.beam_halfcells)//span)+edge//span
            independently_scattered[row, slots] += weight*local.gap_jacobian[channel]
    np.testing.assert_allclose(owner._C.toarray(), independently_scattered,
                               rtol=0., atol=3e-14)
    rng = np.random.default_rng(913)
    multiplier = rng.normal(size=owner._C.shape[0])
    direction = rng.normal(size=owner._K.shape[0])
    np.testing.assert_allclose(
        multiplier@(owner._C@direction),
        (owner._C.T@multiplier)@direction, rtol=0., atol=1e-11)


def _bl5_nonmatching_definition(shell_edges, span=1):
    base = _definition()
    xs = np.linspace(0., 1., shell_edges+1)
    row = shell_edges+1
    shell = replace(
        base.shell,
        node_ids=tuple(range(1, 2*row+1)),
        coordinates_m=(tuple((float(x), 0., 0.) for x in xs)+
                       tuple((float(x), .2, 0.) for x in xs)),
        q4_elements=tuple((i, i+1, i+row+1, i+row)
                          for i in range(1, row)))
    line = stiffened_shell.ExperimentalBL5Line(
        tuple(range(1, row+1)), base.lines[0].beam_halfcells,
        multiplier_span=span)
    fixed = tuple(stiffened_shell.FixedCoordinate("shell", node, axis)
                  for node in (1, row+1) for axis in range(6))
    return replace(base, shell=shell, fixed=fixed, lines=(line,))


def _bl5_joint_mesh_definition(shell_edges, beam_halfcells, span):
    base = _bl5_nonmatching_definition(shell_edges, span)
    element, inertia = base.beams[0].instantiate()
    xs = np.linspace(0., 1., beam_halfcells+1)
    points = np.column_stack((xs, np.zeros_like(xs),
                              np.full_like(xs, .0675)))
    beams = tuple(b3_ge.define_beam(
        "b3-ge", index+1,
        (101+2*index, 102+2*index, 103+2*index),
        points[2*index:2*index+3], np.tile(np.eye(3), (3, 1, 1)),
        element.section, inertia)
        for index in range(beam_halfcells//2))
    line = replace(base.lines[0], beam_halfcells=tuple(
        (element_index, cell)
        for element_index in range(len(beams)) for cell in (0, 1)))
    return replace(base, beams=beams, lines=(line,))


def test_bl5_single_p0_support_misses_a_free_beam_yaw():
    """One five-row mean support cannot anchor all six beam rigid motions."""
    for span in (1, 2):
        owner = stiffened_shell.create_analysis(definition=
            _bl5_joint_mesh_definition(2, 2, span))
        q = np.zeros(owner._K.shape[0])
        beam_start = owner._shell_count
        nodal = 6*len(owner._beam_ids)
        # Rotate the complete free native beam about shell-normal z through
        # x=0.5. The reference tangent must perform zero element work.
        for node in owner._beam_ids:
            slot = beam_start+6*owner._beam_index[node]
            q[slot+1] = owner._beam_nodes[node][0][0]-.5
            q[slot+5] = 1.
        for index in range(len(owner._beam_parts)):
            slot = beam_start+nodal+24*index
            q[slot+2] = q[slot+5] = 1.
        internal = np.asarray(owner._K@q).reshape(-1)
        scale = np.asarray(abs(owner._K)@abs(q)).reshape(-1)
        relative = np.divide(abs(internal), scale, out=np.zeros_like(internal),
                             where=scale > 0.)
        assert np.max(relative) <= 1e-12
        gap = np.asarray(owner._C@q).reshape(-1)
        if span == 2:
            # The sole P0 support averages antisymmetric y displacement to
            # zero; its two director rows also miss this physical yaw.
            np.testing.assert_allclose(gap, 0., rtol=0., atol=1e-13)
            assert owner.preflight()["unsupported_modes"] == (
                "single-support BL5 leaves a free native beam rigid mode",)
            with pytest.raises(ValueError, match="free native beam rigid mode"):
                owner.solve_linear((stiffened_shell.NodalAction(
                    "beam", 103, (0., 100., 0., 0., 0., 0.)),))
            assert owner.preflight()["reference_linear_factorizations"] == 0
        else:
            assert np.max(abs(gap)) >= .1
            assert owner.preflight()["unsupported_modes"] == ()


def test_bl5_single_p0_support_with_beam_yaw_restraint_is_admitted():
    model = _bl5_joint_mesh_definition(2, 2, 2)
    model = replace(model, fixed=model.fixed+(
        stiffened_shell.FixedCoordinate("beam", 101, 5),))
    owner = stiffened_shell.create_analysis(definition=model)
    assert owner.preflight()["unsupported_modes"] == ()
    result = owner.solve_linear((stiffened_shell.NodalAction(
        "beam", 103, (0., 100., 0., 0., 0., 0.)),))
    assert result.status == "completed"


@pytest.mark.parametrize("shell_edges", (2, 8))
@pytest.mark.parametrize("span", (1, 2))
def test_bl5_supported_p0_rows_match_dropped_yaw_l1_locally(
        shell_edges, span):
    """Bounded straight/flat reference identity for one complete P0 rule.

    This verifies the supported row space for the *same* five-channel P0
    resolution. It does not compare the existing asymmetric L1 spaces or
    establish stability, locking, or physical fidelity of either policy.
    """
    from anysolver._stiffened_shell_l1_local_experimental import L1LocalOperator

    definition = _bl5_nonmatching_definition(shell_edges, span)
    owner = stiffened_shell.create_analysis(definition=definition)
    positions = np.array([owner._beam_nodes[node][0] for node in owner._beam_ids])
    frames = np.array([owner._beam_nodes[node][1] for node in owner._beam_ids])
    state = Mechanical(positions, np.zeros_like(positions), frames,
                       np.tile(np.eye(3), (len(owner._beam_parts), 2, 1, 1)),
                       np.zeros((len(owner._beam_parts), 18)))
    projected = np.zeros(owner._C.shape)
    for bl5, slots, weight, beam_edge, _ in owner._line_samples:
        l1 = L1LocalOperator.at_reference(
            bl5.reference, np.zeros((2, 6)), bl5.thickness,
            bl5.port, state, offset=(0., 0., -.05), station=bl5.station)
        l1_rows = l1.evaluate(
            np.zeros((2, 6)), state, np.zeros(6)).gap_jacobian
        five = np.vstack((-l1_rows[:3], -l1_rows[4], l1_rows[3]))
        for channel in range(5):
            row = channel*(4//span)+beam_edge//span
            projected[row, slots] += weight*five[channel]
    np.testing.assert_allclose(owner._C[:, owner._free].toarray(),
                               projected[:, owner._free],
                               rtol=0., atol=4e-14)


@pytest.mark.parametrize("shell_edges,span,segments", (
    (2, 1, 4), (2, 2, 4), (3, 1, 6), (3, 2, 6),
    (8, 1, 8), (8, 2, 8)))
def test_bl5_fixed_reference_nonmatching_segmentation_and_work(
        shell_edges, span, segments):
    definition = _bl5_nonmatching_definition(shell_edges, span)
    owner = stiffened_shell.create_analysis(definition=definition)
    assert len(owner._line_samples) == 2*segments
    np.testing.assert_allclose(
        sum(sample[2] for sample in owner._line_samples), 1.,
        rtol=0., atol=2e-15)
    positions = np.array([owner._beam_nodes[node][0] for node in owner._beam_ids])
    frames = np.array([owner._beam_nodes[node][1] for node in owner._beam_ids])
    state = Mechanical(positions, np.zeros_like(positions), frames,
                       np.tile(np.eye(3), (len(owner._beam_parts), 2, 1, 1)),
                       np.zeros((len(owner._beam_parts), 18)))
    scattered = np.zeros(owner._C.shape)
    for operator, slots, weight, beam_edge, _ in owner._line_samples:
        local = operator.evaluate(np.zeros((2, 6)), state, np.zeros(5))
        np.testing.assert_allclose(local.gap, 0., atol=2e-13)
        for channel in range(5):
            row = channel*(4//span)+beam_edge//span
            scattered[row, slots] += weight*local.gap_jacobian[channel]
    np.testing.assert_allclose(owner._C.toarray(), scattered,
                               rtol=0., atol=4e-14)
    spin = np.array((.17, -.11, .09))
    rigid = np.zeros(owner._K.shape[0])
    for i, point in enumerate(owner._shell_xyz):
        rigid[6*i:6*i+3] = np.cross(spin, point)
        rigid[6*i+3:6*i+6] = spin
    beam_nodal = 6*len(owner._beam_ids)
    for i, point in enumerate(positions):
        start = owner._shell_count+6*i
        rigid[start:start+3] = np.cross(spin, point)
        rigid[start+3:start+6] = spin
    for i in range(len(owner._beam_parts)):
        start = owner._shell_count+beam_nodal+24*i
        rigid[start:start+3] = spin
        rigid[start+3:start+6] = spin
    np.testing.assert_allclose(owner._C@rigid, 0., atol=2e-12)
    result = owner.solve_linear((stiffened_shell.NodalAction(
        "beam", 105, (0., 0., 100., 0., 0., 0.)),))
    assert result.status == "completed"
    assert result.free_equilibrium_ratio < 1e-8
    assert result.constraint_max < 1e-9
    support = result.reactions[:owner._shell_count].reshape(-1, 6)
    np.testing.assert_allclose(support[:, :3].sum(axis=0),
                               (0., 0., -100.), atol=1e-6)
    support_moment = (support[:, 3:].sum(axis=0)+
                      np.cross(np.asarray(definition.shell.coordinates_m),
                               support[:, :3]).sum(axis=0))
    np.testing.assert_allclose(support_moment, (0., 100., 0.), atol=1e-5)
    restored = stiffened_shell.create_analysis(definition=definition)
    np.testing.assert_array_equal(
        restored.restore(owner.checkpoint()).shell_displacement,
        result.shell_displacement)


def test_bl5_nonmatching_rejects_reversed_and_incomplete_reference():
    definition = _bl5_nonmatching_definition(2)
    line = definition.lines[0]
    reversed_cells = replace(line, beam_halfcells=line.beam_halfcells[::-1])
    with pytest.raises(ValueError, match="contiguous ordered"):
        stiffened_shell.create_analysis(
            definition=replace(definition, lines=(reversed_cells,)))
    longer = _bl5_nonmatching_definition(8)
    short_shell = replace(longer.lines[0],
                          shell_nodes=longer.lines[0].shell_nodes[:5])
    with pytest.raises(ValueError, match="aligned straight BL5"):
        stiffened_shell.create_analysis(
            definition=replace(longer, lines=(short_shell,)))
