"""Single-macro finite-inertia checks; not a transient/qualification wave."""

import numpy as np
import pytest

from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import rotation,T6
from docs.reference_cases.ge_beam3_curved_p5_finite_inertia_probe import FiniteInertiaProbe
from docs.reference_cases.ge_beam3_curved_p5_mass_probe import reference_kinetic_factors
from test_ge_beam3_curved_p5_algebra_probe import reference,section
from test_ge_beam3_curved_p5_mass_probe import section_mass


def close(a,b,tolerance=1e-11):
    assert np.linalg.norm(np.asarray(a)-np.asarray(b)) <= tolerance*max(1.,np.linalg.norm(b))


def state(ref):
    x=ref.coordinates+np.array([[.1,-.2,.3],[-.03,.2,.04],[.15,.1,-.12]])
    cells=np.array([rotation([.8,-.7,.6]),rotation([-.4,.9,.7])])
    speed=np.sin(np.arange(24)+.4);accel=np.cos(np.arange(24)-.2)/2
    return x,cells,speed,accel


@pytest.fixture(scope='module',params=[0.,.4])
def sample(request):
    ref=reference(request.param,.1,.15);model=FiniteInertiaProbe(ref,section_mass(),order=8)
    x,cells,v,a=state(ref)
    return ref,model,(x,cells,v,a),model.evaluate(x,cells,v,a)


def direct_energy_and_momentum(ref,inertia,x,cells,speed,order=32):
    # Explicit physical velocity field, never uses the probe map or matrices.
    energy=0.;linear=np.zeros(3);angular=np.zeros(3)
    points,weights=np.polynomial.legendre.leggauss(order)
    for cell in (0,1):
        spin=speed[18+3*cell:21+3*cell]
        for point,weight in zip(points,weights):
            t=(point+1)/2;xi=cell-1+t
            d=cells[cell]@(ref.position(xi)-(1-t)*ref.coordinates[cell]-t*ref.coordinates[cell+1])
            r=(1-t)*x[cell]+t*x[cell+1]+d
            v=(1-t)*speed[6*cell:6*cell+3]+t*speed[6*(cell+1):6*(cell+1)+3]+np.cross(spin,d)
            frame=cells[cell]@ref.frame(xi)
            body=np.r_[frame.T@v,frame.T@spin];p,h=np.split(inertia@body,2)
            measure=weight*ref.jacobian(xi)/2
            energy+=measure*(body@(inertia@body))/2
            linear+=measure*(frame@p)
            angular+=measure*(np.cross(r,frame@p)+frame@h)
    return energy,linear,angular


def test_finite_kinetic_field_and_momenta_match_direct_integration(sample):
    ref,model,args,result=sample;x,cells,v,a=args
    # Order comparison is separate from exact same-order derivative identities.
    higher=FiniteInertiaProbe(ref,section_mass(),order=32).evaluate(*args)
    energy,p,h=direct_energy_and_momentum(ref,section_mass(),x,cells,v)
    close(higher.kinetic_energy,energy);close(higher.linear_momentum,p);close(higher.angular_momentum,h)
    close(result.generalized_momentum,result.mass@v)
    close(result.kinetic_energy,.5*v@result.mass@v)
    close(result.mass,result.mass.T)
    assert np.linalg.matrix_rank(result.mass)==15


def test_original_reference_full_mass_not_guyan_or_trace_mass(sample):
    ref,_,_,_=sample
    old=reference_kinetic_factors(ref,section(),section_mass(),order=8)
    made=FiniteInertiaProbe(ref,section_mass(),order=8).evaluate(ref.coordinates,np.tile(np.eye(3),(2,1,1)),np.zeros(24),np.zeros(24))
    close(made.mass,old.full.T@old.full)
    assert np.array_equal(made.inertia,np.zeros(24))
    assert np.array_equal(made.velocity_derivative,np.zeros((24,24)))
    assert np.array_equal(made.configuration_derivative,np.zeros((24,24)))


def test_affine_acceleration_and_nonzero_convective_force(sample):
    _,model,(x,cells,v,a),made=sample
    convective=model.evaluate(x,cells,v,np.zeros(24))
    close(made.inertia-convective.inertia,made.mass@a)
    assert np.linalg.norm(convective.inertia)>.01
    direction=np.cos(np.arange(24)+.7)
    changed=model.evaluate(x,cells,v,a+direction)
    close(changed.inertia-made.inertia,made.mass@direction)
    # Since convective inertia is quadratic, Euler's homogeneity identity holds.
    close(made.velocity_derivative@v,2*convective.inertia)


def test_analytic_velocity_and_configuration_derivatives(sample):
    _,model,(x,cells,v,a),made=sample
    direction=np.cos(np.arange(24)+.3);epsilon=2e-6
    plus=model.evaluate(x,cells,v+epsilon*direction,a)
    minus=model.evaluate(x,cells,v-epsilon*direction,a)
    close((plus.inertia-minus.inertia)/(2*epsilon),made.velocity_derivative@direction,1e-7)
    shifted=[]
    for sign in (1,-1):
        new_cells=np.array([rotation(sign*epsilon*direction[18+3*c:21+3*c])@cells[c] for c in (0,1)])
        shifted.append(model.evaluate(x+sign*epsilon*direction[:18].reshape(3,6)[:,:3],new_cells,v,a))
    close((shifted[0].inertia-shifted[1].inertia)/(2*epsilon),made.configuration_derivative@direction,1e-7)


def test_power_and_spatial_momentum_balance(sample):
    ref,model,(x,cells,v,a),made=sample
    epsilon=1e-6;history=[]
    for time in (epsilon,-epsilon):
        new_x=x+time*v[:18].reshape(3,6)[:,:3]+.5*time*time*a[:18].reshape(3,6)[:,:3]
        new_cells=np.array([rotation(time*v[18+3*c:21+3*c]+.5*time*time*a[18+3*c:21+3*c])@cells[c] for c in (0,1)])
        history.append(direct_energy_and_momentum(ref,section_mass(),new_x,new_cells,v+time*a,order=8))
    energy_rate=(history[0][0]-history[1][0])/(2*epsilon)
    linear_rate=(history[0][1]-history[1][1])/(2*epsilon)
    angular_rate=(history[0][2]-history[1][2])/(2*epsilon)
    nodal=made.inertia[:18].reshape(3,6)
    close(v@made.inertia,energy_rate,1e-7)
    close(nodal[:,:3].sum(axis=0),linear_rate,1e-7)
    torque=np.cross(x,nodal[:,:3]).sum(axis=0)+made.inertia[18:].reshape(2,3).sum(axis=0)
    close(torque,angular_rate,1e-7)


def test_general_virtual_kinetic_action_not_only_rigid_momentum(sample):
    ref,model,(x,cells,v,a),_=sample
    # Arbitrary nodal/cell variations with zero temporal endpoints. The
    # perturbing cell rotations have fixed axes, so their spatial angular
    # velocities below are exact, including the noncommuting base rotation.
    # No probe inertia/mass/derivative is used for the perturbed kinetic action.
    a=a.copy();a[18:]=0.
    direction=np.cos(np.arange(24)+.35);duration=.2;epsilon=2e-6
    points,weights=np.polynomial.legendre.leggauss(16)
    actions=np.zeros(2);predicted=0.;acceleration_only=0.
    for point,weight in zip(points,weights):
        time=(point+1)*duration/2;measure=weight*duration/2
        shape=np.sin(np.pi*time/duration);slope=np.pi/duration*np.cos(np.pi*time/duration)
        positions=x+time*v[:18].reshape(3,6)[:,:3]+.5*time*time*a[:18].reshape(3,6)[:,:3]
        frames=np.array([rotation(time*v[18+3*c:21+3*c])@cells[c] for c in (0,1)])
        velocity=v+time*a;eta=shape*direction
        response=model.evaluate(positions,frames,velocity,a)
        predicted-=measure*(response.inertia@eta)
        acceleration_only-=measure*((response.mass@a)@eta)
        for i,sign in enumerate((1.,-1.)):
            perturbed_x=positions+sign*epsilon*eta[:18].reshape(3,6)[:,:3]
            perturbed_v=velocity+sign*epsilon*slope*direction
            perturbed_cells=[]
            for c in (0,1):
                sl=slice(18+3*c,21+3*c);change=rotation(sign*epsilon*eta[sl])
                perturbed_cells.append(change@frames[c])
                perturbed_v[sl]=sign*epsilon*slope*direction[sl]+change@velocity[sl]
            actions[i]+=measure*direct_energy_and_momentum(ref,section_mass(),perturbed_x,
                np.array(perturbed_cells),perturbed_v,order=8)[0]
    close((actions[0]-actions[1])/(2*epsilon),predicted,1e-7)
    assert abs(predicted-acceleration_only)>1e-4  # This fixture detects omitted convective terms.


def test_constant_observer_frame_covariance(sample):
    ref,_,(x,cells,v,a),made=sample
    g=rotation([1.8,-1.4,2.]);shift=np.array([2.,-3.,4.]);transform=np.kron(np.eye(8),g)
    other=FiniteInertiaProbe(ref.rigidly_transformed(g,shift),section_mass(),order=8)
    moved=other.evaluate(x@g.T+shift,g@cells@g.T,transform@v,transform@a)
    close(moved.kinetic_energy,made.kinetic_energy)
    for name in ('mass','velocity_derivative','configuration_derivative'):
        close(getattr(moved,name),transform@getattr(made,name)@transform.T)
    for name in ('inertia','generalized_momentum'): close(getattr(moved,name),transform@getattr(made,name))
    close(moved.linear_momentum,g@made.linear_momentum)
    close(moved.angular_momentum,g@made.angular_momentum+np.cross(shift,g@made.linear_momentum))


def test_reversal_preserves_material_inertia_and_physical_cell_spins(sample):
    ref,_,(x,cells,v,a),made=sample
    slots=np.r_[np.arange(12,18),np.arange(6,12),np.arange(6),np.arange(21,24),np.arange(18,21)]
    other=FiniteInertiaProbe(ref.reversed(),T6@section_mass()@T6.T,order=8)
    reversed_result=other.evaluate(x[::-1],cells[::-1],v[slots],a[slots])
    close(reversed_result.kinetic_energy,made.kinetic_energy)
    close(reversed_result.inertia,made.inertia[slots])
    close(reversed_result.generalized_momentum,made.generalized_momentum[slots])
    for name in ('mass','velocity_derivative','configuration_derivative'):
        close(getattr(reversed_result,name),getattr(made,name)[np.ix_(slots,slots)])


def test_trace_rates_are_exactly_algebraic_not_silently_mass_regularized(sample):
    _,model,(x,cells,v,a),made=sample
    traces=np.array([6*i+j for i in range(3) for j in (3,4,5)])
    changed_v=v.copy();changed_a=a.copy();changed_v[traces]=1e40;changed_a[traces]=-1e40
    changed=model.evaluate(x,cells,changed_v,changed_a)
    assert changed.kinetic_energy==made.kinetic_energy
    for name in ('inertia','generalized_momentum'):
        assert np.array_equal(getattr(changed,name),getattr(made,name))
        assert np.array_equal(getattr(made,name)[traces],np.zeros(9))
    for name in ('mass','velocity_derivative','configuration_derivative'):
        assert np.array_equal(getattr(made,name)[traces],np.zeros((9,24)))
        assert np.array_equal(getattr(made,name)[:,traces],np.zeros((24,9)))


def test_invalid_inputs_and_read_only_outputs(sample):
    ref,model,args,made=sample
    for order in (True,1,65):
        with pytest.raises(ValueError): FiniteInertiaProbe(ref,section_mass(),order=order)
    with pytest.raises(ValueError): FiniteInertiaProbe(ref,-np.eye(6))
    x,cells,v,a=args
    for index in range(4):
        bad=[item.copy() for item in args];bad[index].flat[0]=np.nan
        with pytest.raises(ValueError): model.evaluate(*bad)
    with pytest.raises(ValueError): model.evaluate(x,-cells,v,a)
    with pytest.raises(ValueError): model.evaluate(x,cells,v[:18],a)
    for name in ('mass','inertia','velocity_derivative','configuration_derivative'):
        assert not getattr(made,name).flags.writeable


def test_repeatability_and_input_ownership(sample):
    _,model,args,made=sample
    original=[value.copy() for value in args]
    repeated=model.evaluate(*args)
    assert repeated.kinetic_energy==made.kinetic_energy
    for name in ('mass','inertia','generalized_momentum','velocity_derivative','configuration_derivative'):
        assert getattr(repeated,name).tobytes()==getattr(made,name).tobytes()
    for before,after in zip(original,args): assert np.array_equal(before,after)
