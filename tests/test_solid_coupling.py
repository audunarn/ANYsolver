"""Research connector algebra; these are not a stability/convergence campaign."""
import numpy as np
import pytest
from skfem import MeshTet

from anysolid import SolidMesh, prepare
from anysolid.coupling import build_weak_connector
from anysolver import FEModel, BoundaryCondition, LoadCase, solve_linear, solve_linear_many
from anysolver.elements import create_shell_element
from anysolver.solid_trace import ShellEdgeTrace
from anysolver.solids import SolidModel, SolidAnalysisNotSupported, ResidualScales


def specimen(nshell=1,nsolid=1,offset=0.,nu=0.):
    thickness=.2
    native=FEModel('controlled-shell-solid-shell')
    native.add_material('m',1000.,nu)
    left=[]; right=[]; clamp=[]; tip=[]
    for side,xs in enumerate(((-1.,0.),(1.,2.))):
        nodes={}
        for j,y in enumerate(np.linspace(0,1,nshell+1)):
            for i,x in enumerate(xs):
                nid=len(native.mesh.nodes)+1
                native.add_node(nid,float(x),float(y),0.)
                nodes[i,j]=nid
                if side==0 and i==0: clamp.append(nid)
                if side==1 and i==1: tip.append(nid)
        for j in range(nshell):
            eid=len(native.mesh.elements)+1
            ids=[nodes[0,j],nodes[1,j],nodes[1,j+1],nodes[0,j+1]]
            native.add_element(eid,create_shell_element(eid,ids,'m',thickness=thickness,reference_normal=(0.,0.,1.)))
            (left if side==0 else right).append((eid,1 if side==0 else 3))
    right.reverse()
    raw=MeshTet.init_tensor(np.linspace(0,1,nsolid+1),np.linspace(0,1,nsolid+1),
                            np.linspace(-thickness/2+offset,thickness/2+offset,3)).oriented()
    first=SolidMesh(raw.p.T,raw.t.T)
    x=first.coordinates[first.boundary_facets][:,:,0]
    groups={'left':first.boundary_ids[np.all(abs(x)<1e-12,axis=1)],
            'right':first.boundary_ids[np.all(abs(x-1)<1e-12,axis=1)]}
    mesh=SolidMesh(first.coordinates,first.cells,boundary_groups=groups)
    backend=prepare(mesh,{'elastic_modulus':1000.,'poisson_ratio':nu})
    return native,backend,ShellEdgeTrace(native,left,offset=offset),ShellEdgeTrace(native,right,offset=offset),clamp,tip


def native_rigid(native,translation,omega):
    values=np.zeros(native.mesh.dof_manager.total_dofs)
    for node in native.mesh.nodes.values():
        values[node.dofs[:3]]=translation+np.cross(omega,node.coords())
        values[node.dofs[3:]]=omega
    return values


@pytest.mark.parametrize('offset',[0.,.07,-.04])
def test_common_rigid_modes_and_virtual_work(offset):
    native,backend,left,_,_,_=specimen(offset=offset)
    op=build_weak_connector(left,backend,'left',multiplier_breakpoints=[0,1])
    assert op.metadata['status']=='NO_GO_PRODUCTION_UNQUALIFIED'
    assert abs(op.metadata['quadrature_area']-.2)<1e-13
    for axis in range(6):
        v=np.zeros(6);v[axis]=1
        q=native_rigid(native,v[:3],v[3:])
        coordinates=backend.coefficient_coordinates
        displacements=v[:3]+np.cross(v[3:],coordinates)
        a=displacements[np.arange(backend.ndof),backend.coefficient_components]
        np.testing.assert_allclose(op.C_shell@q,op.C_solid@a,atol=2e-13)
    rng=np.random.default_rng(742)
    q=rng.normal(size=left.ndof); a=rng.normal(size=backend.ndof); lam=rng.normal(size=10)
    fs,fv=op.interface_forces(lam)
    np.testing.assert_allclose(q@fs+a@fv,lam@(op.C_shell@q-op.C_solid@a),atol=1e-12)
    force=np.zeros(3);moment=np.zeros(3)
    for node in native.mesh.nodes.values():
        f=fs[node.dofs[:3]]
        force+=f
        moment+=np.cross(node.coords(),f)+fs[node.dofs[3:]]
    for i in range(backend.ndof):
        f=np.eye(3)[backend.coefficient_components[i]]*fv[i]
        force+=f;moment+=np.cross(backend.coefficient_coordinates[i],f)
    np.testing.assert_allclose(force,0,atol=1e-12)
    np.testing.assert_allclose(moment,0,atol=1e-12)


def test_one_sided_multiplier_kernel_rejected():
    _,backend,left,_,_,_=specimen(nshell=5)
    with pytest.raises(ValueError,match='one-sided solid multiplier kernel'):
        build_weak_connector(left,backend,'left',multiplier_breakpoints=np.linspace(0,1,6))
    op=build_weak_connector(left,backend,'left',multiplier_breakpoints=[0,1])
    assert op.C_shell.shape[0]==10


def test_stale_geometry_and_explicit_production_refusal():
    native,backend,left,_,_,_=specimen()
    op=build_weak_connector(left,backend,'left',multiplier_breakpoints=[0,1])
    model=SolidModel(native)
    model.add_region('solid',prepared=backend)
    with pytest.raises(SolidAnalysisNotSupported,match='NO_GO'):
        model.add_interface('solid',op)
    native.mesh.get_node(1).x-=.1
    with pytest.raises(ValueError,match='stale'):
        op.validate(native,backend)


def test_mutated_operator_and_dof_layout_are_rejected():
    native,backend,left,_,_,_=specimen()
    op=build_weak_connector(left,backend,'left',multiplier_breakpoints=[0,1])
    with pytest.raises(ValueError):
        op.affine.setflags(write=True)
    op.C_shell.data[0]+=1
    with pytest.raises(ValueError,match='mutated'):
        op.validate(native,backend)
    op=build_weak_connector(left,backend,'left',multiplier_breakpoints=[0,1])
    dofs=native.mesh.dof_manager.get_node_dofs(1)
    dofs[0],dofs[1]=dofs[1],dofs[0]
    with pytest.raises(ValueError,match='stale'):
        op.validate(native,backend)


@pytest.mark.parametrize('entry',['model','single','many'])
def test_coupled_membrane_analytic_limit(entry):
    native,backend,left,right,clamp,tip=specimen()
    native.add_boundary_condition(BoundaryCondition(name='clamp',node_ids=clamp,
        dof_constraints={k:0. for k in ('ux','uy','uz','rx','ry','rz')}))
    load=LoadCase('extension')
    for nid in tip: load.add_nodal_load(nid,forces=[1/len(tip),0.,0.])
    references={'extension':ResidualScales(length=1.,force=1.,displacement=.015,
                                          interface_displacements=(.015,.015))}
    model=SolidModel(native,research_coupling=True,residual_scales=references)
    model.add_region('solid',prepared=backend)
    model.add_interface('solid',build_weak_connector(left,backend,'left',multiplier_breakpoints=[0,1]))
    model.add_interface('solid',build_weak_connector(right,backend,'right',multiplier_breakpoints=[0,1]))
    # Prospective registered v2: refs from F=1, Lspan=3, E=1000, A=.2;
    # these are analytical inputs, never fitted to the observed residual.
    if entry=='model':
        result=model.solve_static(('extension',),native_load_cases={'extension':load})
    elif entry=='single':
        _,info=solve_linear(model,load)
        result=info['solid_result']
    else:
        _,info=solve_linear_many(model,[load,load])
        result=info['solid_result']
        np.testing.assert_array_equal(result.coefficients[:,0],result.coefficients[:,1])
    dofs=[native.mesh.dof_manager.get_node_dofs(n)[0] for n in tip]
    # E=1000, cross section=0.2, length=3, axial force=1, nu=0.
    np.testing.assert_allclose(result.coefficients[dofs,0],3/(1000*.2),rtol=1e-10,atol=1e-12)
    assert result.diagnostics['matrix_class']=='symmetric_indefinite'
    assert result.diagnostics['qualification']=='research_only'
    assert result.diagnostics['residual_policy']=='registered_physical_v2'
    assert result.diagnostics['registered_residual_report']['passed']
    # The original rejection remains visible; no historical failure is erased.
    assert result.diagnostics['legacy_componentwise_constraint_error']>1e-9
