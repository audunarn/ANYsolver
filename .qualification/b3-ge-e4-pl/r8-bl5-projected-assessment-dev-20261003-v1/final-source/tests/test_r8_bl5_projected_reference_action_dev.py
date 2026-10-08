"""Complete prescribed-density reference work, not external solver acceptance."""
from fractions import Fraction as F
import numpy as np
import pytest
from scripts.r8_bl5_projected_reference_action_dev import integrated_projected_weights,common_rows
from scripts.r8_bl5_external_affine_reference_dev import integrated_affine_weights
from scripts import r8_bl5_external_affine_reference_dev as external


def test_exact_endpoint_terms_and_moment_reject_old_affine_action():
    weights,_=integrated_projected_weights(0,1,4,4)
    affine,_=integrated_affine_weights(0,1,4,0,[F(i,4) for i in range(5)])
    assert tuple(weights[1][i] for i in range(5))==(-F(3,32),-F(1,8),F(0),F(1,8),F(3,32))
    assert weights[1][0]-affine[1][0]==F(1,96)
    assert weights[1][4]-affine[1][4]==-F(1,96)
    assert all(weights[1][i]==affine[1][i] for i in (1,2,3))
    x=[F(i,4) for i in range(5)]
    assert sum(weights[1][i]*x[i] for i in range(5))==F(5,32)
    assert sum(affine[1][i]*x[i] for i in range(5))==F(1,6)
    # Same inferred interior density does not produce the same complete work.
    assert sum((weights[1][i]-affine[1][i])*x[i] for i in range(5))==-F(1,96)


@pytest.mark.parametrize('intervals,halfcells',((4,32),(8,32),(16,32),(32,32),(64,32),(128,32),(256,32)))
def test_nonmatching_hat_weights_against_independent_piecewise_gauss(intervals,halfcells):
    left,right=F(1,4),F(3,4)
    weights,_=integrated_projected_weights(left,right,intervals,halfcells,20)
    nodes=np.linspace(0.,1.,intervals+1);expected=np.zeros((2,intervals+1))
    knots=sorted({float(left),float(right)}|set(nodes)|set(np.linspace(0.,1.,halfcells+1)))
    gauss,quad=np.polynomial.legendre.leggauss(2)
    for a,b in zip(knots,knots[1:]):
        if a<float(left) or b>float(right):continue
        cell=int(((a+b)/2)*halfcells)
        coefficient=2*((cell+.5)/halfcells-float(left))/float(right-left)-1
        for xi,w in zip(gauss,quad):
            position=(a+b)/2+(b-a)*xi/2
            for node in range(intervals+1):
                field=np.zeros(intervals+1);field[node]=1.
                expected[:,node]+=(b-a)*w/2*np.interp(position,nodes,field)*np.array((1.,coefficient))
    actual=np.array([[float(row.get(20+i,0)) for i in range(intervals+1)] for row in weights])
    np.testing.assert_allclose(actual,expected,rtol=1e-13,atol=1e-16)


def test_coarse_shell_weights_have_complete_end_actions():
    weights,_=integrated_projected_weights(0,1,2,4)
    assert tuple(weights[1][i] for i in range(3))==(-F(5,32),F(0),F(5,32))


def test_native_sign_map_nonzero_force_arms_and_director_torque():
    rows=common_rows(2,4,1,F(1,5),-F(1,3)).toarray()
    # Common constant nodal fields; each test independently exercises one side.
    field=np.zeros(rows.shape[1]);field[4:18:6]=1.  # shell Ry
    np.testing.assert_allclose(rows@field,(.2,0,0,0,0,0,1,0,0,0),atol=1e-15,rtol=0)
    field[:]=0;field[18+4::6]=1.  # beam Ry
    np.testing.assert_allclose(rows@field,(1/3,0,0,0,0,0,-1,0,0,0),atol=1e-15,rtol=0)
    field[:]=0;field[18+3::6]=1.  # beam Rx
    np.testing.assert_allclose(rows@field,(0,0,-1/3,0,0,0,0,0,1,0),atol=1e-15,rtol=0)


@pytest.mark.parametrize('arguments',((0,1,4,1),(F(1,16),F(9,16),4,8),(0,F(1,4),4,4),(0,1,0,4),(0,1,True,4)))
def test_invalid_or_collapsed_projection_is_rejected(arguments):
    with pytest.raises(ValueError):integrated_projected_weights(*arguments)


@pytest.mark.parametrize('intervals', (16,32,64))
def test_external_preparation_has_independently_checked_complete_weights(intervals):
    expected,_=integrated_projected_weights(F(1,4),F(3,8),intervals,32,100)
    actual,pieces=external.integrated_projected_weights(F(1,4),F(3,8),intervals,32,100)
    assert actual==expected
    assert all('xi_halfcell_mean_rational' in piece for piece in pieces)


@pytest.fixture(scope='module')
def projected_external():
    refinement,p0,frozen,service,reference=external.services()
    model=refinement.geometry(16,reference);model['support_count']=8
    pairing=external.aggregate_rows(model,reference,basis=external.PROJECTED_BASIS)
    return refinement,p0,frozen,service,reference,model,pairing


def test_projected_external_actual_objective_work_and_invertible_emission(projected_external):
    refinement,p0,frozen,service,reference,model,pairing=projected_external
    result=external.preparation_controls(model,pairing,refinement,p0,frozen,service,reference)
    assert result['normal_spin_columns_zero']
    assert max(result['six_common_rigid_field_average_gap_scaled'])<1e-9
    assert max(result['objective_average_gap_scaled'].values())<1e-9
    assert max(result['actual_left_exp_derivative_relative'])<1e-6
    assert result['row_transform_max_abs']<1e-8
    assert external.aggregate_rows(model,reference)['basis']==external.BASIS
    assert pairing['basis']==external.PROJECTED_BASIS


@pytest.mark.parametrize('channel,degree',[(c,d) for c in range(5) for d in (0,1)])
def test_each_projected_density_channel_has_complete_nodal_wrench_and_moment(projected_external,channel,degree):
    *_,service,reference,model,pairing=projected_external
    density=np.zeros(80);density[10*3+2*channel+degree]=7.
    resisting=external.transpose_action(pairing['physical_rows'],density,model['nodes'])
    exerted={n:-np.asarray(resisting[n]) for n in model['beam_node_ids']}
    origin=model['moment_origin_m']
    shifted={n:tuple(x-origin[d] for d,x in enumerate(model['nodes'][n])) for n in exerted}
    nodal=service._wrench(exerted,shifted)
    measures=external.density_measures(pairing['supports'],density,reference)
    np.testing.assert_allclose(measures['polynomial_x_moments']['0'],nodal,rtol=1e-13,atol=1e-15)
    # Independently integrate the cellwise physical beam-exerted wrench,
    # including its actual eccentric arm and x-cross-force, not affine xi(x).
    expected=np.zeros((4,6));gauss,weights=np.polynomial.legendre.leggauss(3)
    left,right=3/8,4/8;arm=reference.BEAM_BOTTOM_ARM_M
    for cell in range(12,16):
        a,b=cell/32,(cell+1)/32
        xi=2*((a+b)/2-left)/(right-left)-1
        coefficients=np.zeros(5);coefficients[channel]=7*(1 if degree==0 else xi)
        force=-coefficients[:3]
        local=np.array((arm*coefficients[1]-coefficients[3],
                        -arm*coefficients[0]-coefficients[4],0.))
        for station,weight in zip(gauss,weights):
            x=(a+b)/2+(b-a)*station/2
            wrench=np.r_[force,local+np.cross((x,0.,0.),force)]
            for k in range(4):expected[k]+=(b-a)*weight/2*x**k*wrench
    np.testing.assert_allclose([measures['polynomial_x_moments'][str(k)] for k in range(4)],
                               expected,rtol=2e-13,atol=1e-15)
