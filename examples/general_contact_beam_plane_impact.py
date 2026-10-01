"""Development example: explicit round B2/B3 impact against a fixed plane."""
import argparse

import numpy as np

from anysolver import (
    BoundaryCondition,ContactDefinition,ContactInteraction,ContactSolverSettings,
    ContactSurface,RigidContactBody,
)
from anysolver.dynamics import TransientConfig
from anysolver.elements import BeamElement,QuadraticBeamElement
from anysolver.fe_core import FEModel
from anysolver.general_contact.transient import ContactTransientSolverControls,solve_transient_contact


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quadratic',action='store_true',help='Use a straight-reference B3 beam')
    parser.add_argument('--deformable',action='store_true',help='Excite nonuniform bending and retain free ry inertia')
    args = parser.parse_args()
    if args.deformable and not args.quadratic:
        parser.error('--deformable example requires --quadratic')
    model = FEModel('round_beam_plane_impact_dev')
    model.add_material('elastic',1e3,.3,density=1.)
    positions = (-.5,0.,.5) if args.quadratic else (-.5,.5)
    for node,x in enumerate(positions,1):
        model.add_node(node,x,0.,.015)
    nodes = list(model.mesh.nodes)
    section = dict(area=1e-3,Iy=1e-4,Iz=1e-4,J=1e-4)
    model.add_element(1,(QuadraticBeamElement if args.quadratic else BeamElement)(
        1,nodes,'elastic',section))
    fixed = ('ux','uy','rx','rz') if args.deformable else ('ux','uy','rx','ry','rz')
    model.add_boundary_condition(BoundaryCondition('guide',nodes,{name:0. for name in fixed}))
    initial = np.zeros(model.mesh.dof_manager.total_dofs)
    speeds = (-.1,-.35,-.1) if args.deformable else (-.5,)*len(nodes)
    for node,speed in zip(nodes,speeds):
        initial[model.mesh.dof_manager.get_node_dofs(node)[2]] = speed
    definition = ContactDefinition(
        surfaces=(ContactSurface('round_line',(1,),beam_radius=.01,beam_end_caps='none'),),
        rigid_bodies=(RigidContactBody('plane','plane',(0.,0.,0.),normal=(0.,0.,1.)),),
        interactions=(ContactInteraction('line_plane','round_line','plane',None,.002,
                                         line_stiffness=1e4),),
    )
    result = solve_transient_contact(model,definition,
        TransientConfig(.0001,.023 if args.deformable else .013,initial_velocity=initial),
        contact_settings=ContactSolverSettings(pair_motion='general'),
        solver_controls=ContactTransientSolverControls(allow_classical_beam_dev=True))
    print(dict(profile=result.profile,accepted_steps=len(result.newton_iterations),
        cutbacks=result.cutbacks,minimum_swept_gap_m=float(np.min(result.swept_minimum_gaps)),
        maximum_residual_n=float(np.max(result.equilibrium_residuals)),
        maximum_line_force_n=max(c.beam_force[2] for c in result.contact),
        partial_line_contact=any(0. < c.active_line_length < .99 for c in result.contact),
        final_line_active=result.contact[-1].active_line_cells))


if __name__ == '__main__':
    main()
