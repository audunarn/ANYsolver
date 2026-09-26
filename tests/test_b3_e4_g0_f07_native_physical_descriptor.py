"""F07 development check of physical coupled inertia and algebraic coordinates.

This is one supported, straight Q4 current-rest state.  It does not admit a
coupled modal range or change the G0/G1 qualification status.
"""

import numpy as np
from scipy import linalg

from anysolver._ge_beam3_coupled_modes import capture, modes
from test_ge_beam3_coupled_modes import arguments, fixture


def test_native_beam_shell_mass_survives_exact_joint_and_descriptor():
    owner = fixture("Q4", curved=False)
    solved = owner.solve(stop_after=0)
    assert solved.status == "paused", solved.failure
    state = solved.state
    inertias = arguments(owner)
    packet = capture(owner, state, **inertias)
    assembly = owner.assembly

    # An independent rigid-translation kinetic-work oracle: unit shell area,
    # thickness 0.2, density 2; beam length 2, sectional mass/length 2.
    rigid_x = np.zeros(len(packet.full_kinematic_dofs))
    for node in range(assembly.shell_count // 6):
        rigid_x[6 * node] = 1.
    for node in range(assembly.beam.nodal_count // 6):
        rigid_x[assembly.shell_count + 6 * node] = 1.
    np.testing.assert_allclose(packet.constraints @ rigid_x, 0., atol=1e-13)
    np.testing.assert_allclose(rigid_x @ packet.full_mass @ rigid_x, 4.4,
                               rtol=1e-12, atol=1e-12)
    assert packet.internal_cell_coordinates == 6
    assert packet.shell_mass_rank == 24

    # The retained physical cell has inertia, but geometric nodal rotations
    # and the six exact-joint multipliers have none.  No mass is patched into
    # either algebraic block to make a generalized eigenproblem nonsingular.
    cell = np.arange(assembly.shell_count + assembly.beam.nodal_count,
                     len(rigid_x))
    assert np.linalg.norm(packet.full_mass[np.ix_(cell, cell)]) > 0.
    assert packet.algebraic_dofs
    reduced_mass = packet.lift.T @ packet.full_mass @ packet.lift
    np.testing.assert_allclose(packet.kinetic.T @ packet.kinetic,
                               reduced_mass, rtol=1e-11, atol=1e-11)
    np.testing.assert_array_equal(packet.kinetic[:, packet.algebraic_dofs], 0.)
    np.testing.assert_allclose(reduced_mass[:, packet.algebraic_dofs], 0.,
                               atol=1e-13)

    free = [i for i, dof in enumerate(packet.full_kinematic_dofs)
            if dof in owner.free]
    k = packet.full_stiffness[np.ix_(free, free)]
    m = packet.full_mass[np.ix_(free, free)]
    c = packet.constraints[:, free]
    saddle = np.block([[k, c.T], [c, np.zeros((6, 6))]])
    descriptor_mass = linalg.block_diag(m, np.zeros((6, 6)))
    np.testing.assert_array_equal(descriptor_mass[-6:, :], 0.)
    np.testing.assert_array_equal(descriptor_mass[:, -6:], 0.)
    eigenvalues = linalg.eigvals(saddle, descriptor_mass)
    finite = np.sort(eigenvalues[np.isfinite(eigenvalues)].real)
    assert np.all(np.abs(eigenvalues[np.isfinite(eigenvalues)].imag) < 1e-8)
    # For this supported fixture, 24 physical finite directions remain;
    # six algebraic retained directions plus six exact constraints and six
    # multiplier rows account for the 18 infinite descriptor roots.
    assert len(finite) == 24
    assert np.count_nonzero(~np.isfinite(eigenvalues)) == 18

    _, actual = modes(owner, state, **inertias, bounds=(-100., 10000.),
                      num_modes=3)
    np.testing.assert_allclose(actual.eigenvalues, finite[:3],
                               rtol=1e-10, atol=1e-10)
