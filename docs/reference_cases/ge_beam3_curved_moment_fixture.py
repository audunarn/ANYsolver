"""Declared curved end-couple family, shared input data not shared mechanics."""
from fractions import Fraction
import numpy as np

HEIGHT=.15
MOMENT=(.8,.9,.6)
TARGETS=(.25,.5,1.)
FIBRES=((-0.5,-0.5),(-0.5,0.5),(0.5,-0.5),(0.5,0.5))


def background():
    return np.array([[.2,np.sqrt(10.),0.,0.,0.,0.],
        [0.,0.,np.sqrt(12.),0.,.3,0.],[0.,0.,0.,np.sqrt(2.),0.,-.2]])


def reference_section():
    # Exact dyadic assembly of declared fixture inputs, rounded once for the
    # binary64 reference IVP. Do not inspect a native tangent or compliance.
    f=[[Fraction(float(v)) for v in row] for row in background()]
    c=[[sum((row[i]*row[j] for row in f),Fraction(0)) for j in range(6)] for i in range(6)]
    for y,z in FIBRES:
        b=list(map(Fraction,(1.,0.,0.,0.,z,-y)))
        for i in range(6):
            for j in range(6): c[i][j]+=4*b[i]*b[j]
    return np.array(c,dtype=float)


def model(macros):
    if type(macros) is not int or macros not in (1,2,4): raise ValueError('registered 1/2/4 curved-moment macros')
    from anysolver.fe_core import FEModel
    from anysolver.boundary import BoundaryCondition
    from anysolver._ge_beam3_centered_reference import CenteredCurvedBeam3ReferenceGeometry as Reference
    from anysolver._ge_beam3_retained_fibre_element import NativeRetainedFibreElement
    from anysolver._ge_beam3_fibre_section import PhysicalFibreSection,Fibre,FlowCurve
    made=FEModel('curved-spatial-moment-cantilever'); frames=[]
    for i,t in enumerate(np.linspace(-1.,1.,2*macros+1),1):
        made.add_node(i,float(t),float(HEIGHT*(1-t*t)),0.)
        tangent=np.array([1.,-2*HEIGHT*t,0.]); tangent/=np.linalg.norm(tangent)
        frames.append(np.column_stack((tangent,[0.,0.,1.],np.cross(tangent,[0.,0.,1.]))))
    section=PhysicalFibreSection(tuple(Fibre(str(i),y,z,.25,16.,FlowCurve.linear(1e6,2.))
        for i,(y,z) in enumerate(FIBRES)),background())
    for eid in range(1,macros+1):
        nodes=(2*eid-1,2*eid,2*eid+1)
        reference=Reference(np.array([made.mesh.nodes[i].coords() for i in nodes]),np.array([frames[i-1] for i in nodes]))
        element=NativeRetainedFibreElement(eid,nodes,reference,section,order=4)
        made.add_element(eid,element); made.materials[element.material_name]=section
    made.add_boundary_condition(BoundaryCondition('root',[1],{k:0. for k in ('ux','uy','uz','rx','ry','rz')}))
    return made
