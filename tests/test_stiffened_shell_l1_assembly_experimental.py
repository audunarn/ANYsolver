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
    definition = replace(_definition(), points=(
        stiffened_shell.PointConnection(1, 101),))
    owner = stiffened_shell.create_analysis(definition=definition)
    payload = json.dumps({"schema": FINITE_CHECKPOINT,
                          "model": owner._identity}).encode("ascii")
    with pytest.raises(ValueError, match="reference-linear checkpoints"):
        owner.restore(payload)
    binary = encode("finite", owner._identity, 1, ())
    with pytest.raises(ValueError, match="reference-linear checkpoints"):
        owner.restore(binary)
    assert owner._accepted is None and owner._finite_driver is None


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
