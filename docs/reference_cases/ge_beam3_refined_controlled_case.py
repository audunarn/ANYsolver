"""Successor mesh extent; the previous registered arch cases stay immutable."""
import numpy as np
from anysolver._ge_beam3_centered_reference import CenteredCurvedBeam3ReferenceGeometry as Reference
from anysolver._ge_beam3_native_generalized_element import NativeGeneralizedStaticElement
from anysolver._ge_beam3_generalized_ellipsoid_section import EllipsoidalGeneralizedSection
from anysolver._ge_beam3_retained_translation_control import Program
from anysolver._ge_beam3_retained_nodal_loading import NodalDeadForces
from anysolver.fe_core import FEModel
from anysolver.boundary import BoundaryCondition


def model(macros, *, arithmetic_policy=None):
    if type(macros) is not int or macros not in (2,4,8,12,16,20,24):
        raise ValueError('registered bounded refinement mesh')
    made=FEModel('retained-full-spatial-crown-arch');frames=[]
    for node,t in enumerate(np.linspace(-1.,1.,2*macros+1),1):
        made.add_node(node,float(t),float(.1*(1-t*t)),0.)
        tangent=np.array((1.,-.2*t,0.));tangent/=np.linalg.norm(tangent)
        second=np.array((0.,0.,1.));frames.append(np.column_stack((tangent,second,np.cross(tangent,second))))
    section=EllipsoidalGeneralizedSection(np.diag([1000.,400.,400.,.02,.01,.02]),np.eye(6),1e6,1.)
    for i in range(macros):
        nodes=(2*i+1,2*i+2,2*i+3)
        reference=Reference(np.array([made.mesh.nodes[n].coords() for n in nodes]),np.array(frames[2*i:2*i+3]))
        element=NativeGeneralizedStaticElement(i+1,nodes,reference,section,order=4,arithmetic_policy=arithmetic_policy)
        made.add_element(i+1,element);made.materials[element.material_name]=section
    made.add_boundary_condition(BoundaryCondition('ends',[1,2*macros+1],{key:0. for key in ('ux','uy','uz','rx','ry','rz')}))
    return made


def program(macros,drop):
    if type(macros) is not int or macros not in (4,16,20,24):raise ValueError('registered controlled mesh')
    if type(drop) is not float or not np.isfinite(drop) or not .03<drop<=.055:raise ValueError('registered drop')
    return Program((.01,.02,.03,drop),macros+1,(0.,-1.,0.),NodalDeadForces(((macros+1,0.,-1.,0.),)))


def masses(m):return {i:np.diag([1.,1.,1.,3e-5,1e-5,2e-5]) for i in m.mesh.elements}
