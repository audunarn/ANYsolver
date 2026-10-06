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


if __name__=='__main__':
    import json
    model,load,domain,settings,resolution=build()
    result=solve(model,load,domain,settings,resolution,emit_restart_checkpoint=True)
    if result.status!='completed':raise RuntimeError(result.failure_reason)
    print(json.dumps(dict(domain=resolution.to_dict(),status=result.status,
                         contact=result.info['general_contact']),indent=2))
