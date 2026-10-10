"""Translating S3 source, elastic in-plane target and material-anchor friction.

Explicit physical sides use the normal owner's fixed material atlas. Target
normal motion is constrained; this example does not demonstrate target bending.
"""
import argparse
import json
from pathlib import Path

from anysolver import BoundaryCondition, FEModel, create_shell_element, solve_static_nonlinear
from anysolver.general_contact import (ContactDefinition, ContactInteraction,
    ContactSurface, ContactSolverSettings, ContactPathControl, ContactPathProgram)
from anysolver.general_contact.s3_sliding_friction import S3SlidingFrictionSettings


def build_case(source_polarity=1, target_polarity=1):
    model=FEModel('s3-physical-material-friction')
    model.add_material('elastic',1e5,.3,density=1.)
    points=((.2,.19,.055),(.4,.19,.055),(.6,.19,.055),
            (.2,.59,.055),(.4,.59,.055),(.6,.59,.055),
            (0.,0.,0.),(1.,0.,0.),(1.,1.,0.),(0.,1.,0.))
    for node,point in enumerate(points,1):model.add_node(node,*point)
    faces=((1,2,5),(1,5,4),(2,3,6),(2,6,5),(7,8,10),(8,9,10))
    for element,nodes in enumerate(faces,1):
        sign=source_polarity if element<=4 else target_polarity
        if sign not in (-1,1):raise ValueError('polarity must be +1 or -1')
        if sign<0:nodes=(nodes[0],nodes[2],nodes[1])
        model.add_element(element,create_shell_element(element,nodes,'elastic',
            thickness=.05,formulation='e4-pl-s3-v2d',reference_normal=(0.,0.,sign),
            reference_surface_offset=sign*.01 if element>4 else 0.))
    model.add_boundary_condition(BoundaryCondition('source-guide',tuple(range(1,7)),
        {d:0. for d in ('uy','rx','ry','rz')}))
    model.add_boundary_condition(BoundaryCondition('target-plane',(7,8,9,10),
        {d:0. for d in ('uy','uz','rx','ry','rz')}))
    model.add_boundary_condition(BoundaryCondition('target-left',(7,10),{'ux':0.}))
    for axis in (0,2):
        actuator=model.mesh.dof_manager.get_node_dofs(1)[axis]
        for node in range(2,7):
            dependent=model.mesh.dof_manager.get_node_dofs(node)[axis]
            model.add_constraint_equation(terms=((dependent,1.),(actuator,-1.)),
                source_id=f'translating-source-{axis}-{node}',dependent_dof=dependent)
    definition=ContactDefinition((
        ContactSurface('source',(1,2,3,4),'bottom' if source_polarity>0 else 'top'),
        ContactSurface('target',(5,6),'top' if target_polarity>0 else 'bottom')),(),
        (ContactInteraction('material-pair','source','target',1000.,5e-5,
                            normal_law='projected_penalty'),))
    settings=ContactSolverSettings(pair_motion='general',normal_discretization='primal_mortar',
        general_s3_differentiation='jet2_s3_dev',general_s3_difference_step=2e-5,
        q4_source_gap_certificate='whole_face',augmentation_support_resolution='exact',
        q4_source_area_tolerance=1e-9,q4_source_weighted_gap_tolerance=1e-10,
        q4_source_support_gradient_tolerance=1e-5,q4_source_support_hessian_tolerance=1e-5,
        q4_source_weighted_gap_gradient_tolerance=1e-5,q4_source_weighted_gap_hessian_tolerance=1e-5,
        maximum_q4_source_integration_triangles=128,
        shell_pair_orientation='physical_sides_dev',path_predictor='control_projection_dev')
    friction=S3SlidingFrictionSettings(.3,1000.,(2e-7,)*60,145)
    program=ContactPathProgram((ContactPathControl.node(1,'ux'),ContactPathControl.node(1,'uz')),
        ((0.,0.),(0.,-.015005),(1e-7,-.015005),(.39,-.015005),
         (.3899995,-.015005),(.388,-.015005),(.388,0.),(.388,-.015005)),1)
    return model,definition,settings,friction,program


def solve_case(case, *, through_step=7, restart=None):
    model,definition,settings,friction,program=case
    return solve_static_nonlinear(model,contact=definition,contact_settings=settings,
        contact_friction=friction,contact_path_program=program,max_iterations=18,
        tolerance=1e-12,max_load_factor=through_step/7,
        emit_restart_checkpoint=True,record_increment_snapshots=True,
        restart_checkpoint=restart)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--through-step',type=int,default=7,choices=range(1,8))
    parser.add_argument('--restart',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    restart=json.loads(args.restart.read_text()) if args.restart else None
    result=solve_case(build_case(),through_step=args.through_step,restart=restart)
    args.output.write_text(json.dumps(dict(status=result.status,
        physical_scope='translating_source_normal_constrained_elastic_target',
        phases=result.info.get('force_displacement_history'),
        checkpoint=result.to_restart_checkpoint()),default=lambda x:x.tolist() if hasattr(x,'tolist') else x.item(),indent=2))
    if result.status!='completed':raise RuntimeError(result.info)


if __name__=='__main__':main()
