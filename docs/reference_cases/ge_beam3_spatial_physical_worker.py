"""Bounded saved-state physical-mode workers and cross-field comparison."""
import argparse
from hashlib import sha256
import os
from pathlib import Path
import traceback
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,ROOT
from docs.reference_cases.ge_beam3_retained_prestress_protocol import strict_bytes,canonical
from docs.reference_cases.ge_beam3_retained_prestress_wave import write
from docs.reference_cases.e4_pl_s3_v2_bounded_process import THREAD_ENVIRONMENT

ARCHIVE=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-next-native-a4a7230-20260909')
MANIFEST='4ac11c904afd59613a8e74056594de6bfd9172bd68c1c295ba2d2509e70c6a13'
PACKETS={'plus':'889aca7681298fdb426736fd5d5ab3ef009b84ac9347fb4f54741dabb30ff75b',
         'minus':'ab91b219f750421bf5a90b85aec62e74cc97d541477e1a84b429f857c4d4bcf9'}


def inputs(sign):
    from docs.reference_cases.ge_beam3_next_spatial_native import member,source,validate
    if sign not in PACKETS:raise ValueError('registered signed spectral endpoint')
    raw=member(ARCHIVE,MANIFEST,'wave/'+sign+'-capture-a/output/packet.json',PACKETS[sign])
    wrapper=strict_bytes(raw);seed,checkpoint,_=source(sign)
    if wrapper['revision']!='a4a723010155e25bc511d483d081cee64d377d42' or wrapper['sign']!=sign:
        raise ValueError('frozen native spectral source')
    validate(wrapper['packet'],sign,seed,checkpoint)
    return wrapper['packet'],strict_bytes(checkpoint)['records'][0]['mechanical']


def run(revision,sign,mode,digits,output):
    guard(revision)
    if any(os.environ.get(k)!=v for k,v in THREAD_ENVIRONMENT.items()):raise ValueError('one numerical thread')
    if (mode=='native' and digits not in (80,100)) or (mode=='reference' and digits is not None):raise ValueError('registered profile')
    root=Path(output).resolve()
    if root.is_relative_to(ROOT):raise ValueError('exclusive external output required')
    root.mkdir(exist_ok=False)
    def progress(row):print(row,flush=True)
    progress(dict(stage='spectral-authority-complete',sign=sign,mode=mode,digits=digits))
    try:
        if mode=='native':
            packet,_=inputs(sign)
            from docs.reference_cases.ge_beam3_spatial_physical_pencil import spectrum
            result=spectrum(packet,digits,6,progress)
            inputs(sign);digest=PACKETS[sign]
        elif mode=='reference':
            from docs.reference_cases.ge_beam3_spatial_ritz_worker import source,INPUTS
            from docs.reference_cases.ge_beam3_spatial_physical_reference import solve,validate_reference
            source_value=source(sign);profiles=[]
            def save(row):write(root/('profile-'+str(len(profiles))+'.json'),row);profiles.append(row)
            result=solve(source_value,progress,save)
            write(root/'reference-diagnostic.json',result)
            refinement,quadrature=validate_reference(result)
            result.update(refinement_rate_error=refinement,quadrature_rate_error=quadrature)
            source(sign);digest=INPUTS[sign][1]
        else:raise ValueError('registered worker mode')
        guard(revision)
        value=dict(schema='GE_BEAM3_SAVED_PHYSICAL_SPECTRUM_V1',revision=revision,sign=sign,mode=mode,digits=digits,
            source_sha256=digest,result=result,production_qualified=False,independent_author_review=False)
        write(root/'spectrum.json',value)
        progress(dict(stage='physical-spectrum-complete',sign=sign,mode=mode))
    except BaseException:
        write(root/'failure.json',dict(revision=revision,sign=sign,mode=mode,digits=digits,error=traceback.format_exc(),
            production_qualified=False))
        raise


def compare(sign,native,reference):
    import numpy as np
    from scipy.optimize import linear_sum_assignment
    from docs.reference_cases.ge_beam3_spatial_ritz_worker import source
    from docs.reference_cases.ge_beam3_spatial_next_reference import unpack
    from docs.reference_cases.ge_beam3_spatial_continuum import matrix
    from docs.reference_cases.ge_beam3_spatial_second_variation import variation_basis,skew
    from docs.reference_cases.ge_beam3_spatial_physical_reference import density,rates,validate_reference
    refinement,quad=validate_reference(reference)
    packet,mechanical=inputs(sign);poly=unpack(source(sign)['polynomial'])
    ref=reference['profiles'][2]['result'];a=np.array(native['full_modes']).T;b=np.array(ref['full_modes']).T
    if a.shape!=(438,6) or b.shape!=(192,6):raise ValueError('complete six native/reference modes')
    rotations=np.array(mechanical['cell_rotations']);cross=np.zeros((6,6));nn=np.zeros(6);rr=np.zeros(6)
    points,weights=np.polynomial.legendre.leggauss(32)
    for half in range(48):
        for point,weight in zip(points,weights):
            t=(point+1)/2;x=-1.+(half+t)/24;jac=np.sqrt(1+.04*x*x)
            segment=min(int((x+1)*2),3);y=poly(2*(x-(-1+.5*segment)))[13*segment:13*(segment+1)]
            physical_density=density(matrix(y[3:7]))
            theta=a[294+3*half:297+3*half]
            # Reference parabolic offset from the half-cell chord, transported
            # by the actual saved cell rotation, as in the physical velocity map.
            offset=rotations[half//2,half%2]@np.array([0.,.1/24**2*t*(1-t),0.])
            velocity=(1-t)*a[6*half:6*half+3]+t*a[6*(half+1):6*(half+1)+3]-skew(offset)@theta
            q=np.vstack((velocity,theta));r=variation_basis(x,jac,32)[0]@b
            measure=float(weight*jac/48)
            cross+=measure*q.T@physical_density@r
            nn+=measure*np.sum(q*(physical_density@q),axis=0);rr+=measure*np.sum(r*(physical_density@r),axis=0)
    if np.any(nn<=0) or np.any(rr<=0):raise ValueError('positive physical comparison norms')
    mac=cross*cross/(nn[:,None]*rr[None,:])
    if not np.isfinite(mac).all() or np.any(mac>1+1e-11):raise ValueError('physical MAC range')
    i,j=linear_sum_assignment(-mac)
    native_rates=rates(native['eigenvalues']);reference_rates=rates(ref['eigenvalues'])[j]
    errors=abs(native_rates/reference_rates-1);matched=mac[i,j]
    passed=bool(np.all(np.sign(native_rates)==np.sign(reference_rates)) and np.max(errors)<.02 and np.min(matched)>=.95)
    return dict(native_eigenvalues=native['eigenvalues'],reference_eigenvalues=ref['eigenvalues'],
        matched_reference_indices=j.tolist(),signed_rate_errors=errors.tolist(),physical_mac=mac.tolist(),
        matched_mac=matched.tolist(),reference_refinement_error=refinement,reference_quadrature_error=quad,
        matched_signed_rates_below_two_percent_and_mac_at_least_095=passed,
        native_negative_count=int(np.sum(np.array(native['eigenvalues'])<0)),
        reference_ritz_negative_count=int(np.sum(np.array(ref['eigenvalues'])<0)),
        full_continuum_inertia_proved=False,finite_velocity_dynamics_qualified=False,production_qualified=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--revision',required=True)
    parser.add_argument('--sign',choices=('plus','minus'),required=True);parser.add_argument('--mode',choices=('native','reference'),required=True)
    parser.add_argument('--digits',type=int,choices=(80,100));parser.add_argument('--output',required=True)
    a=parser.parse_args();run(a.revision,a.sign,a.mode,a.digits,a.output)
