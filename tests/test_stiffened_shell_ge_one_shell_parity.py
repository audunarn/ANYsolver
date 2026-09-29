"""V01 development parity for equivalent legacy and sparse one-shell models."""

import numpy as np
import pytest
from scipy import sparse

from anysolver._ge_beam3_native_definition import NativeBeamDefinition
from anysolver._stiffened_shell_ge_experimental import (
    PROFILE, ExperimentalGEAnalysis, FixedCoordinate, LinearDefinition,
    NodalAction, PointConnection, ShellPanel,
)

from test_ge_beam3_coupled_modes import fixture as legacy_fixture
from test_ge_beam3_native_generalized_modal import inertia


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
def test_matching_one_shell_reference_tangent_solution_and_reactions(topology):
    legacy = legacy_fixture(topology, False)
    assembly = legacy.assembly
    node_ids = tuple(range(1, len(assembly.coordinates)+1))
    panel = ShellPanel(
        node_ids, tuple(map(tuple, assembly.coordinates)),
        ((1, 2, 3, 4),) if topology == "Q4" else (),
        .2, 1000., .3, 2.,
        ((1, 2, 3),) if topology == "S3-V2D" else ())
    beams = tuple(NativeBeamDefinition.capture(element, inertia())
                  for _eid, element in assembly.beam.elements)
    supports = tuple(FixedCoordinate("shell", row//6+1, row%6)
                     for row in legacy.shell_fixed)
    current = ExperimentalGEAnalysis(LinearDefinition(
        PROFILE, panel, beams,
        (PointConnection(assembly.shell_node+1, assembly.beam_node),),
        supports))

    state = legacy.initial
    response, old_residual, _, _ = legacy._evaluate(
        state, state.mechanical, state.shell_u, state.multipliers, 0)
    full = sparse.bmat([[current._K, current._C.T],
                        [current._C, None]], format="csr").toarray()
    assert full.shape == response.tangent.shape
    assert np.max(np.abs(old_residual)) == 0.
    assert current.preflight()["stress_free_scaled_max"] < 1e-12
    tangent_error = np.linalg.norm(full-response.tangent) / np.linalg.norm(
        response.tangent)
    assert tangent_error <= 1e-10

    load = np.zeros(assembly.count)
    load[:len(legacy.forces)] = legacy.forces
    old_solution = np.zeros(assembly.count)
    old_solution[list(legacy.free)] = np.linalg.solve(
        response.tangent[np.ix_(legacy.free, legacy.free)],
        load[list(legacy.free)])
    result = current.solve_linear((
        NodalAction("beam", 3, (0., .0001, .0002, 0., 0., 0.)),))
    new_solution = np.r_[result.shell_displacement,
                         result.beam_coordinates, result.multipliers]
    np.testing.assert_array_equal(current._accepted[1],
                                  load[:current._K.shape[0]])
    solution_error = np.linalg.norm(new_solution-old_solution) / np.linalg.norm(
        old_solution)
    assert solution_error <= 1e-10
    old_reactions = response.tangent@old_solution-load
    np.testing.assert_allclose(result.reactions[current._fixed],
                               old_reactions[current._fixed],
                               rtol=1e-10, atol=1e-14)
