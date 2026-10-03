"""Development checks for one complete affine-density BL5 pairing.

Rank/residual checks do not qualify transfer accuracy, locking or stability.
"""
from dataclasses import replace

import numpy as np
import pytest

from anysolver import b3_ge, stiffened_shell as api
from anysolver._ge_beam3_retained_generalized_state import Mechanical
from anysolver._stiffened_shell_l1_assembly_experimental import _sample_rows
from test_stiffened_shell_l1_assembly_experimental import _bl5_joint_mesh_definition


def candidate(shell_edges, halfcells):
    base = _bl5_joint_mesh_definition(shell_edges, halfcells, 1)
    span = 2*max(1, int(np.ceil(halfcells/shell_edges)))
    if halfcells % span:
        raise ValueError("complete affine-support rule cannot infer a partial support")
    line = replace(base.lines[0], basis="discontinuous_p1", multiplier_span=span)
    fixed = base.fixed+tuple(api.FixedCoordinate("beam", 101, i) for i in range(5))
    return replace(base, lines=(line,), fixed=fixed)


@pytest.mark.parametrize("shell_edges,halfcells", ((8, 8), (8, 16), (8, 32),
    (8, 64), (16, 8), (32, 8), (64, 8)))
def test_complete_development_rule_covers_ratio_inventory(shell_edges, halfcells):
    from scripts.b3_e4_bl5_coherent_aggregation_dev import model
    definition, policy = model(shell_edges, shell_edges//4, halfcells, 2,
                               basis="discontinuous_p1")
    line = definition.lines[0]
    assert line.multiplier_span % 2 == 0
    assert line.multiplier_span*policy["beam_spacing_m"] >= 2*policy["shell_spacing_m"]
    assert policy["qualification"] == "EXPERIMENTAL_NOT_QUALIFIED"
    assert len(policy["support_membership"]) == halfcells//line.multiplier_span
    with pytest.raises(ValueError, match="one complete"):
        model(shell_edges, shell_edges//4, halfcells, 1, basis="discontinuous_p1")


def test_distinct_basis_and_complete_member_admission():
    base = _bl5_joint_mesh_definition(4, 4, 1)
    line = replace(base.lines[0], basis="discontinuous_p1", multiplier_span=2)
    assert line.multiplier_space == "BL5_P1_discontinuous_span_2"
    assert line.descriptor()["basis"] == "discontinuous_p1"
    assert "basis" not in base.lines[0].descriptor()
    with pytest.raises(ValueError, match="complete native members"):
        replace(line, multiplier_span=1)
    with pytest.raises(ValueError, match="complete native members"):
        replace(line, beam_halfcells=((0, 1), (1, 0), (1, 1), (2, 0)))
    with pytest.raises(ValueError, match="support coordinate"):
        _sample_rows(line, 0, .4, 0, .4, 0)
    with pytest.raises(ValueError, match="partial support"):
        candidate(4, 6)


def test_nonuniform_support_coordinate_and_all_channel_work():
    definition = candidate(4, 8)
    # Each quadratic member has its true midpoint. Different member lengths
    # make the affine support coordinate differ from half-cell index averaging.
    xs = np.array((0., .1, .2, .35, .5, .6, .7, .85, 1.))
    beams = []
    for i, old in enumerate(definition.beams):
        element, inertia = old.instantiate()
        points = np.column_stack((xs[2*i:2*i+3], np.zeros(3), np.full(3, .0675)))
        beams.append(b3_ge.define_beam("b3-ge", i+1,
            (101+2*i, 102+2*i, 103+2*i), points, np.tile(np.eye(3), (3, 1, 1)),
            element.section, inertia))
    owner = api.create_analysis(definition=replace(definition, beams=tuple(beams)))
    try:
        positions = np.array([owner._beam_nodes[n][0] for n in owner._beam_ids])
        frames = np.array([owner._beam_nodes[n][1] for n in owner._beam_ids])
        state = Mechanical(positions, np.zeros_like(positions), frames,
            np.tile(np.eye(3), (len(owner._beam_parts), 2, 1, 1)),
            np.zeros((len(owner._beam_parts), 18)))
        expected = np.zeros(owner._C.shape)
        supports = 2
        integrals = np.zeros((supports, 2))
        for sample, (rows, basis) in zip(owner._line_samples, owner._line_terms):
            local, slots, weight, edge, alpha = sample
            x = (1.-alpha)*xs[edge]+alpha*xs[edge+1]
            support = edge//4
            left, right = xs[4*support], xs[4*support+4]
            xi = 2.*(x-left)/(right-left)-1.
            integrals[support] += weight*np.array((1., xi))
            evaluation = local.evaluate(np.zeros((2, 6)), state, np.zeros(5))
            interpolation = np.zeros((5, 10))
            expected_rows = []
            for channel in range(5):
                for degree, value in enumerate((1., xi)):
                    row = 2*(channel*supports+support)+degree
                    expected[row, slots] += weight*value*evaluation.gap_jacobian[channel]
                    interpolation[channel, 2*channel+degree] = value
                    expected_rows.append(row)
            np.testing.assert_array_equal(rows, expected_rows)
            np.testing.assert_allclose(basis, interpolation, rtol=0., atol=2e-15)
        np.testing.assert_allclose(integrals, ((.5, 0.), (.5, 0.)), atol=2e-16)
        np.testing.assert_allclose(owner._C.toarray(), expected, rtol=0., atol=4e-14)
        rng = np.random.default_rng(734)
        q = rng.normal(size=owner._C.shape[1])
        multiplier = rng.normal(size=owner._C.shape[0])
        work = sum(weight*np.dot(basis@multiplier[rows],
            local.evaluate(np.zeros((2, 6)), state, np.zeros(5)).gap_jacobian@q[slots])
            for (local, slots, weight, _, _), (rows, basis)
            in zip(owner._line_samples, owner._line_terms))
        np.testing.assert_allclose(multiplier@owner._C@q, work, rtol=2e-14, atol=1e-14)
    finally:
        owner.close()


@pytest.mark.parametrize("shell_edges,halfcells", ((4, 8), (8, 4)))
def test_supported_off_ratio_full_mixed_work_and_restart(shell_edges, halfcells):
    definition = candidate(shell_edges, halfcells)
    owner = api.create_analysis(definition=definition)
    try:
        assert owner.capabilities["status"] == "EXPERIMENTAL_NOT_QUALIFIED"
        scaled = (owner._C[:, owner._free].toarray()*
            owner._coordinate_scale[owner._free][None, :]/owner._constraint_scale[:, None])
        assert np.linalg.matrix_rank(scaled) == owner._C.shape[0]
        for wrench in ((0., 100., 0., 0., 0., 0.),
                       (0., 0., 0., 10., 0., 0.),
                       (0., 0., 0., 0., 0., 10.)):
            result = owner.solve_linear((api.NodalAction("beam", 101+halfcells, wrench),))
            assert result.status == "completed"
            assert result.free_equilibrium_ratio < 1e-8
            assert result.constraint_max < 1e-9
            q = np.r_[result.shell_displacement, result.beam_coordinates]
            load = owner._accepted[1]
            work = float(q@load)
            assert work > 0.
            assert abs(float(q@owner._K@q)-work)/work < 1e-8
            assert abs(float(q@owner._C.T@result.multipliers))/work < 1e-8
        restored = api.create_analysis(definition=definition)
        try:
            resumed = restored.restore(owner.checkpoint())
            np.testing.assert_array_equal(resumed.shell_displacement, result.shell_displacement)
            np.testing.assert_array_equal(resumed.multipliers, result.multipliers)
        finally:
            restored.close()
    finally:
        owner.close()


def test_same_row_count_cannot_restore_p0_checkpoint_as_affine():
    base = _bl5_joint_mesh_definition(4, 4, 1)
    first = api.create_analysis(definition=base)
    second = api.create_analysis(definition=candidate(4, 4))
    try:
        first.solve_linear((api.NodalAction("beam", 105, (0., 0., 1., 0., 0., 0.)),))
        assert first._C.shape == second._C.shape
        with pytest.raises(ValueError, match="incompatible mixed linear checkpoint"):
            second.restore(first.checkpoint())
    finally:
        first.close(); second.close()


def test_affine_multiplier_curvature_through_actual_state_update():
    from anysolver._stiffened_shell_ge_finite_experimental import FinitePointDriver
    definition = replace(candidate(4, 4), q4_pullback_policy=api.Q4_ALGORITHMIC_PULLBACK_V1)
    owner = api.create_analysis(definition=definition)
    try:
        driver = FinitePointDriver(owner)
        count = owner._K.shape[0]
        rng = np.random.default_rng(192)
        delta = rng.normal(size=count+owner._C.shape[0])*.002
        delta[count:] = rng.normal(size=owner._C.shape[0])*50000.
        state = driver._advance(driver._state, delta, 1.)
        zero = replace(state, multipliers=np.zeros_like(state.multipliers))
        pattern = np.zeros(count)
        def evaluate(s):
            return driver._assemble(s, 0., driver._shell_origins,
                                    driver._beam_origins, pattern=pattern)[:2]
        r, k = evaluate(state)
        r0, k0 = evaluate(zero)
        direction = rng.normal(size=len(r)); direction[count:] = 0.
        expected = (k-k0)@direction
        assert np.linalg.norm(expected) > 1.
        errors = []
        for step in (1e-5, 3e-6, 1e-6):
            residuals = []
            for sign in (-1., 1.):
                moved = driver._advance(state, direction, sign*step)
                moved0 = replace(moved, multipliers=np.zeros_like(moved.multipliers))
                residuals.append(evaluate(moved)[0]-evaluate(moved0)[0])
            numerical = (residuals[1]-residuals[0])/(2.*step)
            errors.append(np.linalg.norm(numerical-expected)/np.linalg.norm(expected))
        assert min(errors) < 1e-6, errors
    finally:
        owner.close()


def test_accepted_finite_station_density_checkpoint_and_continuation():
    definition = replace(candidate(4, 4), q4_pullback_policy=api.Q4_ALGORITHMIC_PULLBACK_V1)
    owner = api.create_analysis(definition=definition)
    restored = api.create_analysis(definition=definition)
    action = (api.NodalAction("beam", 105, (0., 0., 1., 0., 0., 0.)),)
    try:
        result = owner.solve(action, targets=(.5, 1.))
        assert result.status == "completed" and result.accepted_factors == (.5, 1.)
        assert result.free_equilibrium_ratio < 1e-8 and result.constraint_max < 1e-9
        for sample, record in zip(owner._line_samples, result.beam_shell_line_work):
            _, _, _, edge, alpha = sample
            support = edge//2
            x = (edge+alpha)/4.
            xi = 2.*(x-.5*support)/.5-1.
            expected = np.array([result.multipliers[2*(channel*2+support)]+
                xi*result.multipliers[2*(channel*2+support)+1] for channel in range(5)])
            np.testing.assert_allclose(record.multiplier_density, expected, rtol=1e-14, atol=1e-13)
        saved = owner.checkpoint()
        repeated = restored.restore(saved)
        assert restored.checkpoint() == saved
        np.testing.assert_array_equal(repeated.beam_positions, result.beam_positions)
        for a, b in zip(repeated.beam_shell_line_work, result.beam_shell_line_work):
            np.testing.assert_array_equal(a.multiplier_density, b.multiplier_density)
        direct = owner.solve(action, targets=(.75,))
        continued = restored.solve(action, targets=(.75,))
        np.testing.assert_array_equal(continued.beam_positions, direct.beam_positions)
        assert restored.checkpoint() == owner.checkpoint()
    finally:
        owner.close(); restored.close()
