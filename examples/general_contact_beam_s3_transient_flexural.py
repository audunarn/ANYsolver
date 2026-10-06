"""Actual B3 bending against a deforming S3: explicit constrained development case."""
import numpy as np
from examples.general_contact_beam_s3_transient import run


def run_flexural(*,end=.0018,dt=1.e-5,restart=None):
    """Free physical B3 ry inertia; exact zero model-constrained S3 rotations."""
    return run(end=end,dt=dt,restart=restart,quadratic=True,unequal=True,flexural=True)


def summary(model,result):
    dof=lambda node,axis:model.mesh.dof_manager.get_node_dofs(node)[axis]
    curve=result.displacements[:,dof(6,2)]-.5*(result.displacements[:,dof(1,2)]+result.displacements[:,dof(2,2)])
    mean_curvature=(result.displacements[:,dof(2,4)]-result.displacements[:,dof(1,4)])/.5
    return dict(profile=result.profile,states=len(result.times),active=sum(x.active_line_length>0 for x in result.contact),
        minimum_gap=float(min(x.minimum_gap for x in result.contact)),final_gap=float(result.contact[-1].minimum_gap),
        maximum_midpoint_chord_difference=float(np.max(abs(curve))),maximum_beam_mean_curvature=float(np.max(abs(mean_curvature))))


if __name__=='__main__':
    import json
    model,result=run_flexural()
    print(json.dumps(summary(model,result),indent=2))
