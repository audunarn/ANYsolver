"""Physical six-mode N32 comparison to the preserved resolved continuum field."""
def match(native_values,reference_values,mac):
    import numpy as np
    from scipy.optimize import linear_sum_assignment
    from docs.reference_cases.ge_beam3_spatial_physical_reference import rates
    mac=np.asarray(mac,dtype=float)
    if mac.shape!=(6,6) or not np.isfinite(mac).all() or np.any(mac<0) or np.any(mac>1+1e-11):
        raise ValueError('physical MAC range')
    i,j=linear_sum_assignment(-mac)
    nr=rates(native_values);rr=rates(reference_values)[j]
    errors=abs(nr/rr-1);matched=mac[i,j]
    passed=bool(np.all(np.sign(nr)==np.sign(rr)) and np.max(errors)<.02 and np.min(matched)>=.95)
    return j,errors,matched,passed

def velocity(modes,rotations,half,t):
    import numpy as np
    from docs.reference_cases.ge_beam3_spatial_second_variation import skew
    if type(half) is not int or not 0<=half<64 or not 0<=t<=1:
        raise ValueError('N32 half-cell point')
    if modes.shape!=(582,6) or rotations.shape!=(32,2,3,3) or not np.isfinite(t):
        raise ValueError('N32 full vector/rotation extent')
    theta=modes[390+3*half:393+3*half]
    offset=rotations[half//2,half%2]@np.array([0.,.1/32**2*t*(1-t),0.])
    v=(1-t)*modes[6*half:6*half+3]+t*modes[6*(half+1):6*(half+1)+3]-skew(offset)@theta
    return np.vstack((v,theta))

def compare(native,reference,continuum,mechanical):
    import numpy as np
    from docs.reference_cases.ge_beam3_spatial_next_reference import unpack
    from docs.reference_cases.ge_beam3_spatial_continuum import matrix
    from docs.reference_cases.ge_beam3_spatial_physical_reference import density
    from docs.reference_cases.ge_beam3_piecewise_physical_reference import basis,validate
    ref=reference['profiles'][2]['result'];refinement,quad=validate(reference)
    a=np.array(native['full_modes']).T;b=np.array(ref['full_modes']).T
    rotations=np.array(mechanical['cell_rotations']);poly=unpack(continuum['polynomial'])
    if a.shape!=(582,6) or b.shape!=(306,6) or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('all six saved native/reference modes')
    cross=np.zeros((6,6));nn=np.zeros(6);rr=np.zeros(6)
    points,weights=np.polynomial.legendre.leggauss(32)
    for half in range(64):
        for point,weight in zip(points,weights):
            t=(point+1)/2;x=-1.+(half+t)/32;jac=np.sqrt(1+.04*x*x)
            segment=min(int((x+1)*2),3)
            y=poly(2*(x-(-1+.5*segment)))[13*segment:13*(segment+1)]
            metric=density(matrix(y[3:7]));q=velocity(a,rotations,half,t);r=basis(x,jac,12)[0]@b
            measure=float(weight*jac/64)
            cross+=measure*q.T@metric@r;nn+=measure*np.sum(q*(metric@q),axis=0);rr+=measure*np.sum(r*(metric@r),axis=0)
    if np.any(nn<=0) or np.any(rr<=0):raise ValueError('positive physical field norms')
    mac=cross*cross/(nn[:,None]*rr[None,:])
    if not np.isfinite(mac).all() or np.any(mac>1+1e-11):raise ValueError('physical MAC range')
    j,errors,matched,passed=match(native['eigenvalues'],ref['eigenvalues'],mac)
    return dict(native_eigenvalues=native['eigenvalues'],reference_eigenvalues=ref['eigenvalues'],
        matched_reference_indices=j.tolist(),signed_rate_errors=errors.tolist(),physical_mac=mac.tolist(),matched_mac=matched.tolist(),
        reference_refinement_error=refinement,reference_quadrature_error=quad,
        matched_signed_rates_below_two_percent_and_mac_at_least_095=passed,
        native_negative_count=int(np.sum(np.array(native['eigenvalues'])<0)),
        reference_ritz_negative_count=int(np.sum(np.array(ref['eigenvalues'])<0)),
        production_qualified=False,full_continuum_inertia_proved=False,finite_velocity_dynamics_qualified=False)
