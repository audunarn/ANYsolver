"""Successor reference and comparison; authentic native spectra are read-only."""
import argparse
from hashlib import sha256
from pathlib import Path
import os,traceback
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,ROOT
from docs.reference_cases.ge_beam3_retained_prestress_protocol import strict_bytes
from docs.reference_cases.ge_beam3_retained_prestress_wave import write
from docs.reference_cases.e4_pl_s3_v2_bounded_process import THREAD_ENVIRONMENT

NATIVE_ARCHIVE=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-physical-spectrum-10f79f3-20260909')
NATIVE_MANIFEST='57b4cc84c8b26961ccda851d09d454dab706984ce41c0339a3f05318498aadad'
NATIVE={'plus':'9b4fcbc0f3f0243ad0af8e73eb3ed3d9cb04d672c021bf811ab886e53c217132',
        'minus':'e47a7031226e527313433bee3761c7f626b85e09954612aef2ca7c4580cbb01f'}


def native_source(sign,archive=NATIVE_ARCHIVE):
    from docs.reference_cases.ge_beam3_next_spatial_native import member
    from docs.reference_cases.ge_beam3_spatial_physical_worker import PACKETS
    if sign not in NATIVE:raise ValueError('registered signed native spectrum')
    raw=member(archive,NATIVE_MANIFEST,'wave/'+sign+'-100-a/output/spectrum.json',NATIVE[sign]);v=strict_bytes(raw)
    if (v['schema']!='GE_BEAM3_SAVED_PHYSICAL_SPECTRUM_V1' or v['revision']!='10f79f3c5a96c4e45dd1dc44cd83ea253deba9e4'
            or v['sign']!=sign or v['mode']!='native' or v['digits']!=100 or v['source_sha256']!=PACKETS[sign]
            or v['production_qualified'] is not False):raise ValueError('authentic native spectrum authority')
    r=v['result']
    if (r['physical_dimension']!=285 or r['algebraic_dimension']!=141 or len(r['eigenvalues'])!=6
            or len(r['full_modes'])!=6 or any(len(row)!=438 for row in r['full_modes'])
            or max(*r['original_residuals'],r['mass_orthogonality'],r['original_ritz_error'])>1e-11):raise ValueError('accepted native spectrum extent/accuracy')
    return r


def compare(sign,native,reference):
    import numpy as np
    from scipy.optimize import linear_sum_assignment
    from docs.reference_cases.ge_beam3_spatial_ritz_worker import source
    from docs.reference_cases.ge_beam3_spatial_next_reference import unpack
    from docs.reference_cases.ge_beam3_spatial_continuum import matrix
    from docs.reference_cases.ge_beam3_spatial_second_variation import skew
    from docs.reference_cases.ge_beam3_spatial_physical_reference import density,rates
    from docs.reference_cases.ge_beam3_spatial_physical_worker import inputs
    from docs.reference_cases.ge_beam3_piecewise_physical_reference import basis,validate
    refinement,quad=validate(reference);_,mechanical=inputs(sign);poly=unpack(source(sign)['polynomial'])
    ref=reference['profiles'][2]['result'];a=np.array(native['full_modes']).T;b=np.array(ref['full_modes']).T
    if a.shape!=(438,6) or b.shape!=(306,6):raise ValueError('complete native/polynomial modal fields')
    rotations=np.array(mechanical['cell_rotations']);cross=np.zeros((6,6));nn=np.zeros(6);rr=np.zeros(6)
    points,weights=np.polynomial.legendre.leggauss(32)
    for half in range(48):
        for point,weight in zip(points,weights):
            t=(point+1)/2;x=-1.+(half+t)/24;jac=np.sqrt(1+.04*x*x)
            segment=min(int((x+1)*2),3);y=poly(2*(x-(-1+.5*segment)))[13*segment:13*(segment+1)]
            metric=density(matrix(y[3:7]));theta=a[294+3*half:297+3*half]
            offset=rotations[half//2,half%2]@np.array([0.,.1/24**2*t*(1-t),0.])
            velocity=(1-t)*a[6*half:6*half+3]+t*a[6*(half+1):6*(half+1)+3]-skew(offset)@theta
            q=np.vstack((velocity,theta));r=basis(x,jac,12)[0]@b;measure=float(weight*jac/48)
            cross+=measure*q.T@metric@r
            nn+=measure*np.sum(q*(metric@q),axis=0);rr+=measure*np.sum(r*(metric@r),axis=0)
    if np.any(nn<=0) or np.any(rr<=0):raise ValueError('positive physical field norms')
    mac=cross*cross/(nn[:,None]*rr[None,:])
    if not np.isfinite(mac).all() or np.any(mac>1+1e-11):raise ValueError('physical MAC range')
    i,j=linear_sum_assignment(-mac);nr=rates(native['eigenvalues']);rrates=rates(ref['eigenvalues'])[j]
    errors=abs(nr/rrates-1);matched=mac[i,j]
    passed=bool(np.all(np.sign(nr)==np.sign(rrates)) and np.max(errors)<.02 and np.min(matched)>=.95)
    return dict(native_eigenvalues=native['eigenvalues'],reference_eigenvalues=ref['eigenvalues'],
        matched_reference_indices=j.tolist(),signed_rate_errors=errors.tolist(),physical_mac=mac.tolist(),matched_mac=matched.tolist(),
        reference_refinement_error=refinement,reference_quadrature_error=quad,
        matched_signed_rates_below_two_percent_and_mac_at_least_095=passed,
        native_negative_count=int(np.sum(np.array(native['eigenvalues'])<0)),
        reference_ritz_negative_count=int(np.sum(np.array(ref['eigenvalues'])<0)),
        full_continuum_inertia_proved=False,finite_velocity_dynamics_qualified=False,production_qualified=False)


def run(revision,sign,output):
    guard(revision)
    if any(os.environ.get(k)!=v for k,v in THREAD_ENVIRONMENT.items()):raise ValueError('one numerical thread')
    # All authority checks precede reference numerical imports/evaluation.
    native=native_source(sign)
    from docs.reference_cases.ge_beam3_spatial_ritz_worker import source,INPUTS
    data=source(sign);root=Path(output).resolve()
    if root.is_relative_to(ROOT):raise ValueError('fresh exclusive external output')
    root.mkdir(exist_ok=False)
    def progress(row):print(row,flush=True)
    progress(dict(stage='piecewise-authority-complete',sign=sign))
    try:
        from docs.reference_cases.ge_beam3_piecewise_physical_reference import solve,validate
        profiles=[]
        def save(row):write(root/('profile-'+str(len(profiles))+'.json'),row);profiles.append(row)
        result=solve(data,progress,save);write(root/'reference-diagnostic.json',result)
        refinement,quad=validate(result);comparison=compare(sign,native,result)
        value=dict(schema='GE_BEAM3_PIECEWISE_PHYSICAL_REFERENCE_COMPARISON_V1',revision=revision,sign=sign,
            native_sha256=NATIVE[sign],continuum_sha256=INPUTS[sign][1],result=result,comparison=comparison,
            reference_refinement_error=refinement,reference_quadrature_error=quad,
            native_workers_rerun=False,production_qualified=False,independent_author_review=False)
        guard(revision);native_source(sign);source(sign)
        write(root/'comparison.json',value)
        progress(dict(stage='piecewise-comparison-complete',sign=sign,comparison=comparison))
    except BaseException:
        write(root/'failure.json',dict(revision=revision,sign=sign,error=traceback.format_exc(),production_qualified=False))
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--revision',required=True)
    parser.add_argument('--sign',choices=('plus','minus'),required=True);parser.add_argument('--output',required=True)
    a=parser.parse_args();run(a.revision,a.sign,a.output)
