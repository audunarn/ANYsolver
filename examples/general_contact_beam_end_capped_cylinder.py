"""Opt-in axial B2 with separate line and hemispherical endpoint penalties."""
from anysolver import (BoundaryCondition, ContactDefinition, ContactInteraction,
    ContactSolverSettings, ContactSurface, RigidCappedCylinder, RigidContactBody, LoadCase,
    solve_static_nonlinear)
from anysolver.fe_core import FEModel
from anysolver.elements import BeamElement


def run(*,plane=False):
    model=FEModel('declared round physical beam end')
    model.add_material('elastic',1e3,.3,density=1.)
    model.add_node(1,.112,0.,0.);model.add_node(2,.312,0.,0.)
    model.add_element(1,BeamElement(1,(1,2),'elastic',
        {'area':1e-3,'Iy':1e-4,'Iz':1e-4,'J':1e-4}))
    model.add_boundary_condition(BoundaryCondition('fixed',(2,),
        {d:0. for d in ('ux','uy','uz','rx','ry','rz')}))
    model.add_boundary_condition(BoundaryCondition('axial guide',(1,),
        {d:0. for d in ('uy','uz','rx','ry','rz')}))
    load=LoadCase('press');load.add_nodal_load(1,forces=(-.2,0.,0.))
    definition=ContactDefinition(
        (ContactSurface('tube',(1,),beam_radius=.01,beam_end_caps='hemisphere'),),
        ((RigidContactBody('tool','plane',(.1,0.,0.),(1.,0.,0.)) if plane else
            RigidCappedCylinder('tool',(0.,0.,0.),(1.,0.,0.),.01,.1)),),
        (ContactInteraction('line_and_end','tube','tool',None,1e-5,
            line_stiffness=1e4,endpoint_stiffness=1e5),))
    settings=ContactSolverSettings(pair_motion='general',
        line_integration_relative_tolerance=1e-7)
    result=solve_static_nonlinear(model,load,contact=definition,contact_settings=settings,
        num_steps=4,max_iterations=20,tolerance=1e-10,emit_restart_checkpoint=True)
    if result.status!='completed':raise RuntimeError(result.failure_reason)
    return result


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plane',action='store_true',help='Use a fixed infinite plane instead of the finite cylinder')
    result=run(plane=parser.parse_args().plane);info=result.info['general_contact']
    print({'status':result.status,'profile':info['profile'],
        'physical_end_fields':info.get('endpoint_fields'),'beam_force_N':info['beam_force'],
        'gap_lower_m':info['minimum_gap'],'admitted_for_application':False})
