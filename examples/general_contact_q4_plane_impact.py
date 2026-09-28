"""Run the opt-in fixed-plane Q4 impact development profile."""

import argparse
import numpy as np

from anysolver import (
    BoundaryCondition,
    ContactDefinition,
    ContactInteraction,
    ContactSurface,
    LoadCase,
    RigidContactBody,
    TransientConfig,
    create_shell_element,
    solve_transient_contact,
)
from anysolver.fe_core import FEModel


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--constant-downward-load-n", type=float, default=0.0)
    args = parser.parse_args()
    if not np.isfinite(args.constant_downward_load_n) or args.constant_downward_load_n < 0:
        parser.error("constant downward load must be finite and nonnegative")
    model = FEModel("guided_q4_impact")
    model.add_material("elastic", 1.0e5, 0.3, density=1.0)
    for node_id, xyz in enumerate(
        ((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)), 1,
    ):
        model.add_node(node_id, *xyz)
    model.add_element(1, create_shell_element(
        1, [1, 2, 3, 4], "elastic", thickness=0.05,
    ))
    model.add_boundary_condition(BoundaryCondition(
        "normal_guide", [1, 2, 3, 4],
        {name: 0.0 for name in ("ux", "uy", "rx", "ry", "rz")},
    ))
    contact = ContactDefinition(
        surfaces=(ContactSurface("skin", (1,)),),
        rigid_bodies=(RigidContactBody(
            "plane", "plane", (0, 0, -0.01), (0, 0, 1),
        ),),
        interactions=(ContactInteraction(
            "impact", "skin", "plane", 1.0e5, 0.001,
        ),),
    )
    initial_velocity = np.zeros(model.mesh.dof_manager.total_dofs)
    for node_id in (1, 2, 3, 4):
        initial_velocity[model.mesh.dof_manager.get_node_dofs(node_id)[2]] = -1.0
    load = None
    if args.constant_downward_load_n:
        load = LoadCase("constant_downward_nodal_force")
        for node_id in (1, 2, 3, 4):
            load.add_nodal_load(
                node_id, forces=(0.0, 0.0, -args.constant_downward_load_n/4),
            )
    result = solve_transient_contact(
        model,
        contact,
        TransientConfig(0.0002, 0.016, initial_velocity=initial_velocity),
        base_load_case=load,
    )
    print(f"profile: {result.profile}")
    print(f"constant downward load: {args.constant_downward_load_n:.9g} N")
    print(f"accepted steps: {len(result.times) - 1}; cutbacks: {result.cutbacks}")
    print(f"minimum swept gap: {min(result.swept_minimum_gaps):.9g} m")
    print(f"final normal velocity: {result.velocities[-1, 2]:.9g} m/s")
    print(f"peak compressive plane reaction: {-min(item.rigid_force[2] for item in result.contact):.9g} N")


if __name__ == "__main__":
    main()
