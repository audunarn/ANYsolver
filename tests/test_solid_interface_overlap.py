"""Actual production trace/solid overlap guard constructions; no FE solves."""
import numpy as np
import pytest
from skfem import MeshTet
from anysolid import SolidMesh,prepare
from anysolid.coupling import build_weak_connector
from anysolver import FEModel
from anysolver.elements import create_shell_element
from anysolver.solid_trace import ShellEdgeTrace


def native():
    model=FEModel('overlap-geometry-regression')
    model.add_material('m',1000.,0.)
    for i,x in enumerate([[-1.,0.,0.],[0.,0.,0.],[0.,1.,0.],[-1.,1.,0.],
                          [1.,0.,0.],[2.,0.,0.],[2.,1.,0.],[1.,1.,0.]],1):
        model.add_node(i,*x)
    model.add_element(1,create_shell_element(1,[1,2,3,4],'m',thickness=.2,reference_normal=(0.,0.,1.)))
    model.add_element(2,create_shell_element(2,[5,6,7,8],'m',thickness=.2,reference_normal=(0.,0.,1.)))
    return model


@pytest.mark.parametrize('side,eid,edge',[(0,1,1),(1,2,3)])
def test_actual_frozen_ratio_1_8_interface_constructs_without_false_overlap(side,eid,edge):
    raw=MeshTet.init_tensor([0.,1.],np.linspace(0.,1.,9),[-.1,0.,.1]).oriented()
    first=SolidMesh(raw.p.T,raw.t.T)
    facets=first.boundary_facets
    ids=first.boundary_ids[np.all(first.coordinates[facets,0]==side,axis=1)]
    mesh=SolidMesh(first.coordinates,first.cells,boundary_groups={'face':ids})
    prepared=prepare(mesh,{'elastic_modulus':1000.,'poisson_ratio':0.})
    trace=ShellEdgeTrace(native(),[(eid,edge)])
    op=build_weak_connector(trace,prepared,'face',multiplier_breakpoints=[0.,1.])
    assert op.C_shell.shape==(10,48)
    assert op.C_solid.shape==(10,765)
    assert op.metadata['area']==pytest.approx(.2)
    assert op.metadata['status']=='NO_GO_PRODUCTION_UNQUALIFIED'


def test_real_positive_overlap_is_rejected_even_when_total_area_matches_rectangle():
    # The two x=0 faces share their bottom edge on the SAME side. Their area
    # sum is .2, but overlap .05 and missing area .05 compensate. Volume
    # self-intersection is not certified by SolidMesh; the connector must fail.
    x=np.array([[0.,0.,-.1],[0.,1.,-.1],[0.,0.,.1],[.5,.25,0.],
                [0.,1.,.1],[1.,.75,0.]])
    t=np.array([[0,1,2,3],[0,1,4,5]])
    first=SolidMesh(x,t)
    ids=first.boundary_ids[np.all(first.coordinates[first.boundary_facets,0]==0.,axis=1)]
    mesh=SolidMesh(x,t,boundary_groups={'face':ids})
    prepared=prepare(mesh,{'elastic_modulus':1000.,'poisson_ratio':0.})
    with pytest.raises(ValueError,match='overlapping'):
        build_weak_connector(ShellEdgeTrace(native(),[(1,1)]),prepared,'face',multiplier_breakpoints=[0.,1.])
