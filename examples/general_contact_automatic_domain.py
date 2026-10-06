"""Declared Q4 skin and two fixed tools compiled once for ordinary static solve."""
from anysolver import BoundaryCondition,FEModel,LoadCase,create_shell_element,solve_static_nonlinear
from anysolver.general_contact import (ContactSurface,RigidContactBody,ContactSolverSettings,
    AutomaticContactParticipant,AutomaticContactDefaults,AutomaticContactDomain,
    resolve_automatic_contact_domain,verify_automatic_contact_resolution)


def build():
    model=FEModel('declared-automatic-q4-two-tools')
    model.add_material('elastic',1e5,.3,density=1.)
    for node,(x,y) in enumerate(((0.,0.),(1.,0.),(1.,1.),(0.,1.)),1):
        model.add_node(node,x,y,0.)
    model.add_element(1,create_shell_element(1,[1,2,3,4],'elastic',thickness=.05))
    model.add_boundary_condition(BoundaryCondition('normal-guide',(1,2,3,4),
        {name:0. for name in ('ux','uy','rx','ry','rz')}))
    load=LoadCase('press')
    for node in (1,2,3,4):load.add_nodal_load(node,forces=(0.,0.,-.1))
    domain=AutomaticContactDomain('two-tools',(
        AutomaticContactParticipant(ContactSurface('skin',(1,),side='bottom'),'panel-body'),
        AutomaticContactParticipant(RigidContactBody('floor','plane',(0.,0.,-.025),(0.,0.,1.)),'floor-body'),
        AutomaticContactParticipant(RigidContactBody('second-floor','plane',(0.,0.,-.0250001),(0.,0.,1.)),'second-tool-body'),
    ),AutomaticContactDefaults(1e6,1e-6),maximum_pairs=2)
    settings=ContactSolverSettings()
    resolution=resolve_automatic_contact_domain(model,domain,settings)
    return model,load,domain,settings,resolution


def solve(model,load,domain,settings,resolution,**controls):
    definition=verify_automatic_contact_resolution(model,domain,resolution,settings)
    return solve_static_nonlinear(model,load,contact=definition,contact_settings=settings,
        kinematics='von_karman',num_steps=1,max_iterations=12,**controls)


def build_shell_pair(*,deformable_target=True):
    """Nonmatching Q4/two-S3 physical skins with a fixed reference role.

    The geometry, material, 50 um gap and penalty stiffness follow the
    admitted Q4/S3 path example. One target translation is free by default.
    """
    from anysolver import ContactPathControl,ContactPathProgram
    model=FEModel('declared-automatic-q4-s3-path')
    model.add_material('elastic',1e5,.3,density=1.)
    points=((.1,.1,.055),(1.1,.1,.055),(1.1,1.1,.055),(.1,1.1,.055),
            (0.,0.,0.),(1.,0.,0.),(1.,1.,0.),(0.,1.,0.))
    for node,position in enumerate(points,1):model.add_node(node,*position)
    model.add_element(1,create_shell_element(1,(1,2,3,4),'elastic',thickness=.05,
                                           reference_normal=(0.,0.,1.)))
    for element,nodes in ((2,(5,6,8)),(3,(6,7,8))):
        model.add_element(element,create_shell_element(element,nodes,'elastic',thickness=.05,
            formulation='e4-pl-s3-v2d',reference_normal=(0.,0.,1.),reference_surface_offset=.01))
    model.add_boundary_condition(BoundaryCondition('source-guide',(1,2,3,4),
        {name:0. for name in ('uy','rx','ry','rz')}))
    model.add_boundary_condition(BoundaryCondition('target-guide',(5,6,7,8),
        {name:0. for name in ('ux','uy','rx','ry','rz')}))
    model.add_boundary_condition(BoundaryCondition('target-support',
        (5,6,8) if deformable_target else (5,6,7,8),{'uz':0.}))
    domain=AutomaticContactDomain('nonmatching-two-shells',(
        AutomaticContactParticipant(ContactSurface('q4_source',(1,),'bottom'),'q4-body'),
        AutomaticContactParticipant(ContactSurface('s3_target',(2,3),'top'),'s3-body')),
        AutomaticContactDefaults(1000.,5e-5),maximum_pairs=1)
    settings=ContactSolverSettings(pair_motion='general',normal_discretization='primal_mortar',
        general_s3_difference_step=2e-6,
        q4_source_area_tolerance=1e-9,q4_source_weighted_gap_tolerance=1e-10,
        maximum_q4_source_integration_triangles=128)
    resolution=resolve_automatic_contact_domain(model,domain,settings,analysis_control='displacement')
    path=ContactPathProgram(controls=(ContactPathControl.node(1,'ux'),ContactPathControl.node(1,'uz')),
        waypoints=((0.,0.),(0.,-.01502),(0.,0.),(0.,-.01502)),steps_per_segment=1)
    return model,domain,settings,resolution,path


def solve_shell_pair(model,domain,settings,resolution,path,**controls):
    """Check the compiled reference contract immediately before execution."""
    definition=verify_automatic_contact_resolution(model,domain,resolution,settings)
    return solve_static_nonlinear(model,contact=definition,contact_settings=settings,
        contact_path_program=path,max_iterations=15,**controls)


def build_projected_shell_pair():
    """Separate refined projected-penalty development fixture; one press."""
    from anysolver import ContactPathControl,ContactPathProgram
    model=FEModel('declared-automatic-refined-projected-q4-s3')
    model.add_material('elastic',1e5,.3,density=1.)
    source=((.1,.1,.055),(.6,.1,.055),(1.1,.1,.055),
            (.1,1.1,.055),(.6,1.1,.055),(1.1,1.1,.055))
    target=((0.,0.,0.),(1.,0.,0.),(1.,1.,0.),(0.,1.,0.))
    for node,point in enumerate((*source,*target),1):model.add_node(node,*point)
    for element,nodes in ((1,(1,2,5,4)),(2,(2,3,6,5))):
        model.add_element(element,create_shell_element(element,nodes,'elastic',thickness=.05,
            reference_normal=(0.,0.,1.)))
    for element,nodes in ((3,(7,8,10)),(4,(8,9,10))):
        model.add_element(element,create_shell_element(element,nodes,'elastic',thickness=.05,
            formulation='e4-pl-s3-v2d',reference_normal=(0.,0.,1.),reference_surface_offset=.01))
    model.add_boundary_condition(BoundaryCondition('source-guide',(1,2,3,4,5,6),
        {name:0. for name in ('uy','rx','ry','rz')}))
    model.add_boundary_condition(BoundaryCondition('target-guide',(7,8,9,10),
        {name:0. for name in ('ux','uy','rx','ry','rz')}))
    model.add_boundary_condition(BoundaryCondition('target-support',(7,8,10),{'uz':0.}))
    domain=AutomaticContactDomain('refined-projected-two-shells',(
        AutomaticContactParticipant(ContactSurface('q4_source',(1,2),'bottom'),'q4-body'),
        AutomaticContactParticipant(ContactSurface('s3_target',(3,4),'top'),'s3-body')),
        AutomaticContactDefaults(1000.,5e-5,normal_law='projected_penalty'),maximum_pairs=1)
    settings=ContactSolverSettings(pair_motion='general',normal_discretization='primal_mortar',
        general_s3_differentiation='jet2_q4_s3_dev',general_s3_difference_step=2e-5,
        q4_source_gap_certificate='overlap_local_dev',augmentation_support_resolution='exact',
        q4_source_area_tolerance=1e-9,q4_source_weighted_gap_tolerance=1e-10,
        q4_source_support_gradient_tolerance=1e-5,q4_source_support_hessian_tolerance=1e-5,
        q4_source_weighted_gap_gradient_tolerance=1e-5,q4_source_weighted_gap_hessian_tolerance=1e-5,
        maximum_q4_source_integration_triangles=128)
    resolution=resolve_automatic_contact_domain(model,domain,settings,analysis_control='displacement')
    path=ContactPathProgram(controls=(ContactPathControl.node(1,'ux'),ContactPathControl.node(1,'uz')),
        waypoints=((0.,0.),(0.,-.01502)),steps_per_segment=1)
    return model,domain,settings,resolution,path


if __name__=='__main__':
    import json
    model,load,domain,settings,resolution=build()
    result=solve(model,load,domain,settings,resolution,emit_restart_checkpoint=True)
    if result.status!='completed':raise RuntimeError(result.failure_reason)
    print(json.dumps(dict(domain=resolution.to_dict(),status=result.status,
                         contact=result.info['general_contact']),indent=2))
