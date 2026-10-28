import copy
import numpy as np
import pytest
from anysolver import FEModel, LoadCase, calculate_mass_properties, solve_inertia_relief, AnalysisSession
from anysolver.concentrated_mass import ConcentratedMass
from anysolver.matrix_assembly import assemble_mass_matrix
from test_inertia_relief import bar, rigid, load_vector


def test_spatial_mass_energy_gravity_and_properties():
    m=FEModel('mass'); m.add_node(1,3.,4.,5.)
    offset=np.array([2.,-1.,3.]); J=np.array([[5.,1.,0.],[1.,6.,.5],[0.,.5,7.]])
    m.add_concentrated_mass(1,10.,offset=offset,inertia_cg=J)
    M,_=assemble_mass_matrix(m)
    v=np.array([.2,.3,.4]); w=np.array([.5,-.2,.8]); q=np.r_[v,w]
    assert q@M@q == pytest.approx(10*np.dot(v+np.cross(w,offset),v+np.cross(w,offset))+w@J@w,rel=1e-13)
    props=calculate_mass_properties(m)
    assert props.total_mass == pytest.approx(10.)
    np.testing.assert_allclose(props.center_of_mass,[5.,3.,8.],atol=1e-13)
    np.testing.assert_allclose(props.inertia_tensor_center_of_mass,J,atol=1e-12)
    g=np.array([1.,2.,-9.81]); load=LoadCase('g'); load.gravity=g
    F=load.get_load_vector(m.mesh,m.mesh.dof_manager,m.get_material)
    np.testing.assert_allclose(F,np.r_[10*g,np.cross(offset,10*g)],atol=1e-12)
    np.testing.assert_array_equal(assemble_mass_matrix(copy.deepcopy(m))[0].toarray(),M.toarray())


@pytest.mark.parametrize('consistent',[True,False])
def test_eccentric_mass_relief_and_direct_mutation_cache(consistent):
    m=bar(consistent=consistent)
    m.add_concentrated_mass(4,10.,offset=(1.,2.,3.),inertia_cg=np.diag([2.,3.,4.]))
    session=AnalysisSession(m)
    M,_=assemble_mass_matrix(m); a=rigid(m,np.zeros(3))@np.array([.2,.1,-.3,.4,.5,-.2])
    result=solve_inertia_relief(m,load_vector(m,M@a),session=session)
    assert result.converged,result.to_dict()
    np.testing.assert_allclose(result.rigid_acceleration,a,atol=1e-10,rtol=1e-10)
    assert np.linalg.norm(result.displacements)<1e-12
    m.mesh.concentrated_masses[4][0]=ConcentratedMass(20.,(1.,2.,3.),np.diag([3.,4.,5.]))
    M,_=assemble_mass_matrix(m)
    result=solve_inertia_relief(m,load_vector(m,M@a),session=session)
    assert result.converged,result.to_dict()
    np.testing.assert_allclose(result.rigid_acceleration,a,atol=1e-10,rtol=1e-10)


@pytest.mark.parametrize('mass,J',[(1.,np.diag([-1.,2.,2.])),(1.,np.diag([1.,1.,3.])),(0.,np.eye(3)),(-1.,np.eye(3)),(1.,[[1,1,0],[0,1,0],[0,0,1]])])
def test_invalid_mass(mass,J):
    with pytest.raises(ValueError): ConcentratedMass(mass,inertia_cg=J)


def test_batch_matches_scalar_and_refuses_midstream_mass_mutation():
    from anysolver import iter_linear_batches, StaticCase, StaticBatchError
    m=bar(); m.add_concentrated_mass(4,5.,offset=(1.,2.,3.),inertia_cg=np.diag([2.,3.,4.]))
    M,_=assemble_mass_matrix(m)
    a=rigid(m,np.zeros(3))@np.array([.2,.1,-.3,.4,.5,-.2])
    load=load_vector(m,M@a)
    blocks=list(iter_linear_batches(m,[StaticCase('a',load)],inertia_relief=True))
    assert np.linalg.norm(blocks[0].displacements)<1e-12
    def cases():
        yield StaticCase('a',load)
        m.mesh.concentrated_masses[4][0]=ConcentratedMass(10.,(1.,2.,3.),np.diag([2.,3.,4.]))
        yield StaticCase('b',load)
    stream=iter_linear_batches(m,cases(),inertia_relief=True,batch_size=1)
    next(stream)
    with pytest.raises(StaticBatchError): next(stream)


def test_mesh_positional_constructor_stays_compatible():
    from anysolver.fe_core import FEMesh,DOFManager
    activity=object(); revisions={'mass':0}
    mesh=FEMesh({}, {}, DOFManager(), {}, activity, revisions)
    assert mesh.element_activity is activity and mesh.revisions is revisions
    assert mesh.concentrated_masses=={}
