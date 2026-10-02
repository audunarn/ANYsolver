"""Development: guided planar Q4 physical skin and free isotropic sphere impact."""
import json

import numpy as np

from anysolver import (BoundaryCondition, ContactDefinition, ContactInteraction,
    ContactSolverSettings, ContactSurface, FEModel, RigidContactBody, create_shell_element)
from anysolver.dynamics import TransientConfig
from anysolver.general_contact.transient import (
    ContactFreeRigidBody, ContactTransientSolverControls, solve_transient_contact)


def run():
    model = FEModel('free_sphere_q4_impact_dev')
    model.add_material('elastic', 1e3, .3, density=7812.5)
    for node, (x, y) in enumerate(((-.004, -.004), (.004, -.004),
                                  (.004, .004), (-.004, .004)), 1):
        model.add_node(node, x, y, .025)
    model.add_element(1, create_shell_element(1, [1, 2, 3, 4], 'elastic', thickness=.002))
    model.add_boundary_condition(BoundaryCondition('guide', [1, 2, 3, 4],
        {name: 0. for name in ('ux', 'uy', 'rx', 'ry', 'rz')}))
    definition = ContactDefinition(
        surfaces=(ContactSurface('skin', (1,), side='bottom'),),
        rigid_bodies=(RigidContactBody('sphere', 'sphere', (0., 0., 0.), radius=.02),),
        interactions=(ContactInteraction('pair', 'skin', 'sphere', 1e6, .002),))
    initial = np.zeros(model.mesh.dof_manager.total_dofs)
    dofs = [model.mesh.dof_manager.get_node_dofs(node)[2] for node in model.mesh.nodes]
    initial[dofs] = -.2
    body = ContactFreeRigidBody('sphere', .002, 8e-8, (0., 0., .2), (2., -3., 4.))
    result = solve_transient_contact(model, definition,
        TransientConfig(.0005, .022, initial_velocity=initial),
        contact_settings=ContactSolverSettings(pair_motion='general', maximum_shell_tilt=.05),
        solver_controls=ContactTransientSolverControls(allow_free_sphere_dev=True,
            allow_free_shell_sphere_dev=True, equilibrium_tolerance=1e-10),
        free_rigid_bodies=(body,))
    momentum = [.001*float(np.mean(velocity[dofs]))+state['sphere'].linear_momentum_kg_m_s[2]
                for velocity, state in zip(result.velocities, result.free_rigid_bodies)]
    return dict(profile=result.profile, status='tested development; not independently accepted',
        accepted_steps=len(result.newton_iterations), cutbacks=result.cutbacks,
        maximum_residual_n=float(np.max(result.equilibrium_residuals)),
        minimum_swept_gap_m=float(np.min(result.swept_minimum_gaps)),
        maximum_contact_force_n=float(max(np.linalg.norm(contact.shell_force) for contact in result.contact)),
        normal_momentum_error_kg_m_s=float(np.max(np.abs(np.asarray(momentum)-momentum[0]))),
        final_sphere_velocity_m_s=result.free_rigid_bodies[-1]['sphere'].velocity_m_s,
        final_active_pressure_dofs=result.contact[-1].active_pressure_dofs)


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
