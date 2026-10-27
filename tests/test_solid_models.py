"""Explicit solid-block integration with independent matrix and affine oracles."""
from types import SimpleNamespace
import numpy as np
import pytest
from scipy import sparse

from anysolver import SolidModel, solve_linear, solve_linear_many
from anysolver.solids import SolidModelError, SolidAnalysisNotSupported
from anysolver.control import CancellationToken, SolveCancelled


class FakeRegion:
    ndof = 3
    coefficient_coordinates = np.zeros((3, 3))
    coefficient_components = np.arange(3)
    def assemble_linear(self):
        return sparse.diags([2., 3., 4.], format='csr')


def test_block_layout_affine_and_multiple_rhs():
    model = SolidModel()
    first = model.add_region('one', prepared=FakeRegion())
    second = model.add_region('two', prepared=FakeRegion())
    first.prescribe_dofs([0], 1.)
    first.set_load('a', [0, 6, 8])
    first.set_load('b', [0, 12, 16])
    second.set_load('a', [2, 3, 4])
    second.set_load('b', [4, 6, 8])
    result = model.solve_static(('a', 'b'))
    np.testing.assert_allclose(result.coefficients, [[1,1],[2,4],[2,4],[1,2],[1,2],[1,2]])
    np.testing.assert_allclose(result.reactions[0], [2,2])
    assert result.layout.native_dofs == 0 and result.layout.primary_dofs == 6
    assert result.layout.multiplier_dofs == 0
    assert result.diagnostics['factorization_count'] == 1
    assert result.diagnostics['solve_count'] == 2
    assert not result.coefficients.flags.writeable


def test_public_dispatch_and_no_dummy_rotations():
    model = SolidModel()
    region = model.add_region('r', prepared=FakeRegion())
    region.set_load('default', [2,3,4])
    u, info = solve_linear(model)
    np.testing.assert_allclose(u, np.ones(3))
    assert info['solid_result'].layout.primary_dofs == 3
    many, _ = solve_linear_many(model, [None, None])
    np.testing.assert_allclose(many, np.ones((3,2)))


def test_mutations_are_copied_and_conflicts_atomic():
    model = SolidModel()
    r = model.add_region('r', prepared=FakeRegion())
    load = np.array([2.,3.,4.])
    r.set_load('default', load)
    load[:] = 99
    r.prescribe_dofs([0], 1)
    with pytest.raises(SolidModelError, match='conflicting'):
        r.prescribe_dofs([0,1], [2,3])
    assert dict(r.prescribed) == {0:1.}
    np.testing.assert_allclose(model.solve_static().coefficients[:,0], [1,1,1])
    r.prescribe_dofs([1], 2)
    np.testing.assert_allclose(model.solve_static().coefficients[:,0], [1,2,1])


def test_cancel_and_unsupported_paths():
    model = SolidModel()
    model.add_region('r', prepared=FakeRegion())
    token = CancellationToken()
    token.cancel('test')
    with pytest.raises(SolveCancelled):
        model.solve_static(cancellation_token=token)
    with pytest.raises(SolidAnalysisNotSupported):
        solve_linear(model, constraint_mode='nullspace')
    with pytest.raises(SolidAnalysisNotSupported):
        _ = model.mesh
    with pytest.raises(SolidModelError):
        model.add_region('r', prepared=FakeRegion())


@pytest.mark.parametrize('order',[1,2])
def test_real_backend_affine_prescription_and_recovery(order):
    from anysolid import SolidMesh, prepare
    mesh = SolidMesh([[0,0,0],[1,0,0],[0,1,0],[0,0,1]], [[0,1,2,3]])
    backend = prepare(mesh, {'elastic_modulus':1000., 'poisson_ratio':.3}, order=order)
    model = SolidModel()
    r = model.add_region('r', prepared=backend)
    A = np.array([[.01,.002,0],[0,-.003,0],[0,0,.004]])
    expected = np.einsum('ij,ij->i', backend.coefficient_coordinates @ A.T,
                         np.eye(3)[backend.coefficient_components])
    r.prescribe_dofs(np.arange(backend.ndof), expected)
    solved = model.solve_static()
    np.testing.assert_allclose(solved.region_coefficients('r')[:,0], expected)
    stress = backend.recover(solved.region_coefficients('r')[:,0]).stress
    strain = (A + A.T)/2
    mu = 1000/2.6
    lam = 1000*.3/(1.3*.4)
    np.testing.assert_allclose(stress, np.broadcast_to(2*mu*strain+lam*np.trace(strain)*np.eye(3), stress.shape), atol=1e-12)


def test_free_solid_is_rejected_before_factorization():
    from anysolid import SolidMesh
    model = SolidModel()
    model.add_region('free', SolidMesh([[0,0,0],[1,0,0],[0,1,0],[0,0,1]], [[0,1,2,3]]),
                     {'elastic_modulus':1000.,'poisson_ratio':.3})
    with pytest.raises(SolidModelError, match='rigid modes'):
        model.solve_static()


def test_empty_native_does_not_bypass_free_solid_refusal():
    from anysolver import FEModel
    from anysolid import SolidMesh
    model = SolidModel(FEModel('empty-native'))
    model.add_region('free', SolidMesh([[0,0,0],[1,0,0],[0,1,0],[0,0,1]], [[0,1,2,3]]),
                     {'elastic_modulus':1000.,'poisson_ratio':.3})
    with pytest.raises(SolidModelError, match='rigid modes'):
        model.solve_static()


def test_ambiguous_repeated_native_names_are_rejected():
    from anysolver import LoadCase
    model=SolidModel()
    model.add_region('r',prepared=FakeRegion())
    with pytest.raises(SolidModelError,match='distinct names'):
        solve_linear_many(model,[LoadCase('same'),LoadCase('same')])
    with pytest.raises(SolidModelError,match='distinct names'):
        solve_linear_many(model,[None,LoadCase('default')])


def test_unsupported_public_entries_refuse_before_native_observation():
    from anysolver.modal import solve_free_vibration
    from anysolver.dynamics import solve_transient_newmark
    from anysolver.nonlinear_static import solve_static_nonlinear
    native=SimpleNamespace()
    model=SolidModel(native)
    for operation in (lambda:solve_free_vibration(model),lambda:solve_transient_newmark(model,None),
                      lambda:solve_static_nonlinear(model)):
        with pytest.raises(SolidAnalysisNotSupported):
            operation()
    assert vars(native)=={}


@pytest.mark.parametrize('registered',[False,True])
def test_native_affine_mpc_is_reconstructed_with_external_block(registered):
    from anysolver import FEModel, BoundaryCondition
    from anysolver.elements import create_shell_element
    native=FEModel('affine-native-mpc')
    native.add_material('m',1000.,.3)
    for node,coordinate in enumerate(((0.,0.,0.),(1.,0.,0.),(1.,1.,0.),(0.,1.,0.)),1):
        native.add_node(node,*coordinate)
    native.add_element(1,create_shell_element(1,[1,2,3,4],'m',thickness=.2))
    names=('ux','uy','uz','rx','ry','rz')
    for node in range(1,5):
        values={name:0. for name in names if node!=3 or name!='ux'}
        if node==2: values['ux']=.002
        native.add_boundary_condition(BoundaryCondition(name=f'fixed-{node}',node_ids=[node],dof_constraints=values))
    a=native.mesh.dof_manager.get_node_dofs(2)[0]
    b=native.mesh.dof_manager.get_node_dofs(3)[0]
    native.add_constraint_equation(terms=((b,1.),(a,-1.)),rhs=.001,dependent_dof=b,source_id='affine-test')
    from anysolver import ResidualScales
    model=SolidModel(native,residual_scales={'default':ResidualScales(1.,4.,1.)} if registered else None)
    region=model.add_region('external',prepared=FakeRegion())
    region.set_load('default',[2.,3.,4.])
    result=model.solve_static()
    assert result.coefficients[a,0]==pytest.approx(.002)
    assert result.coefficients[b,0]==pytest.approx(.003)
    np.testing.assert_allclose(result.region_coefficients('external')[:,0],1.)
    assert result.layout.native_dofs==24 and result.layout.primary_dofs==27


def test_registered_multimaster_refuses_before_factorization_without_legacy_fallback(monkeypatch):
    import anysolver.assembly as assembly
    import anysolver.solids as solids
    from anysolver import FEModel, ResidualScales
    from anysolver.elements import create_shell_element
    native=FEModel('multimaster-policy-routing')
    native.add_material('m',1000.,.3)
    for node,coordinate in enumerate(((0.,0.,0.),(1.,0.,0.),(1.,1.,0.),(0.,1.,0.)),1):
        native.add_node(node,*coordinate)
    native.add_element(1,create_shell_element(1,[1,2,3,4],'m',thickness=.2))
    P=sparse.csr_matrix(([1.,1.,1e12,1e12],([0,1,2,2],[0,1,0,1])),shape=(24,2))
    monkeypatch.setattr(assembly,'build_constraint_transformation',lambda K,F,model:
        (P.T@K@P,P.T@F,P,np.zeros(24),np.array([0,1]),{}))
    calls=[]
    def factorization_sentinel(*args,**kwargs):
        calls.append(True)
        raise RuntimeError('factorization sentinel')
    monkeypatch.setattr(solids,'factorize_cached',factorization_sentinel)
    registered=SolidModel(native,residual_scales={'default':ResidualScales(1.,1.,1.)})
    registered.add_region('external',prepared=FakeRegion())
    with pytest.raises(SolidAnalysisNotSupported,match='multi-master'):
        registered.solve_static()
    assert calls==[]
    legacy=SolidModel(native)
    legacy.add_region('external',prepared=FakeRegion())
    with pytest.raises(RuntimeError,match='factorization sentinel'):
        legacy.solve_static()
    assert calls==[True]


def test_registered_disjoint_free_single_master_column(monkeypatch):
    import anysolver.assembly as assembly
    from anysolver import FEModel, LoadCase, ResidualScales
    from anysolver.elements import create_shell_element
    native=FEModel('single-master-policy-routing')
    native.add_material('m',1000.,.3)
    for node,coordinate in enumerate(((0.,0.,0.),(1.,0.,0.),(1.,1.,0.),(0.,1.,0.)),1):
        native.add_node(node,*coordinate)
    native.add_element(1,create_shell_element(1,[1,2,3,4],'m',thickness=.2))
    a=native.mesh.dof_manager.get_node_dofs(2)[0]
    b=native.mesh.dof_manager.get_node_dofs(3)[0]
    P=sparse.csr_matrix((np.ones(2),([a,b],[0,0])),shape=(24,1))
    monkeypatch.setattr(assembly,'build_constraint_transformation',lambda K,F,model:
        (P.T@K@P,P.T@F,P,np.zeros(24),np.array([a]),{}))
    load=LoadCase('tied')
    load.add_nodal_load(2,forces=[1.,0.,0.])
    model=SolidModel(native,residual_scales={'tied':ResidualScales(1.,4.,1.)})
    region=model.add_region('external',prepared=FakeRegion())
    region.set_load('tied',[2.,3.,4.])
    result=model.solve_static(('tied',),native_load_cases={'tied':load})
    assert result.coefficients[a,0]>0
    assert result.coefficients[a,0]==pytest.approx(result.coefficients[b,0])
    assert result.diagnostics['registered_residual_report']['passed']
