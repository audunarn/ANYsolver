"""Full original N32 stiffness sign audit from immutable captured factors."""
import argparse,os,traceback
from pathlib import Path
from decimal import Decimal
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,ROOT
from docs.reference_cases.ge_beam3_retained_prestress_protocol import strict_bytes
from docs.reference_cases.ge_beam3_retained_prestress_wave import write
from docs.reference_cases.e4_pl_s3_v2_bounded_process import THREAD_ENVIRONMENT
from docs.reference_cases.ge_beam3_n32_spectrum_worker import inputs,PACKETS,validate_result
from docs.reference_cases.ge_beam3_next_spatial_native import member

ARCHIVE=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-n32-spectrum-9559f66-20260909')
MANIFEST='05df67c233cd21d0f69340a88f3809b9758c3774718dbfa91dac38d3d202b067'
SPECTRA={'plus':'9a1c89d8ab13d0c6d2e4c0d44fe225de377fd8cfe9bc4672ab679d2cca69facc',
         'minus':'4e41d4da4b407b0ad6b8af7c11bb28fe210cd4a8987d8e0881e94c0e93e0dc45'}

def source(sign,root=ARCHIVE):
    if sign not in SPECTRA:raise ValueError('registered signed spectral source')
    raw=member(root,MANIFEST,'wave/'+sign+'-100-a/output/spectrum.json',SPECTRA[sign])
    v=strict_bytes(raw)
    if v['revision']!='9559f66a5dd57a5736f1bf7040bba95fc3cb19ef' or v['sign']!=sign or v['packet_sha256']!=PACKETS[sign]:
        raise ValueError('same original factor spectrum')
    validate_result(v['result'],100);return v['result']

def validate(r,digits):
    if r['digits']!=digits or r['physical_dimension']!=381 or r['algebraic_dimension']!=189 or len(r['rows'])!=1:
        raise ValueError('full N32 zero-shift inertia extent')
    for k in ('trace_positive','mass_positive','quadratic_form_preserved','symmetric_energy_representation'):
        if r[k] is not True:raise ValueError('actual positive trace/mass and energy form')
    for k in ('certified_intervals','mechanics_reconstructed'):
        if r[k] is not False:raise ValueError('honest numeric audit scope')
    row=r['rows'][0]
    if type(row['shift']) is not float or row['shift']!=0. or any(type(row[k]) is not int or row[k]<0 for k in ('negative','positive')) or row['negative']+row['positive']!=570:
        raise ValueError('all570 original free coordinates accounted')
    indices=row['pivot_indices'];sizes=row['pivot_sizes']
    if (sizes!=[len(x) for x in indices] or any(n not in (1,2) for n in sizes)
        or sorted(i for x in indices for i in x)!=list(range(570))
        or any(type(i) is not int for x in indices for i in x)):
        raise ValueError('complete unique original pivot partition')
    for k in ('reconstruction_relative','original_reconstruction_bound','coordinate_roundtrip_relative'):
        x=Decimal(row[k])
        if not x.is_finite() or not 0<=x<=Decimal('1e-60'):raise ValueError('original coordinate reconstruction')
    scales=row['coordinate_scales']
    if len(scales)!=570 or any(not Decimal(x).is_finite() or Decimal(x)<=0 for x in scales) or row['positive_diagonal_congruence'] is not True:
        raise ValueError('positive congruence not pivot modification')
    if type(row['max_front']) is not int or not 0<=row['max_front']<=96 or type(row['updates']) is not int or not 0<=row['updates']<=2000000:
        raise ValueError('original sparse work limits')
    skew=Decimal(r['raw_skew_normalized'])
    if not skew.is_finite() or not 0<=skew<=Decimal('1e-11') or r['raw_geometric_symmetric'] is not (skew==0):raise ValueError('raw symmetry disclosure')

def run(revision,sign,digits,output):
    guard(revision)
    if type(digits) is not int or digits not in (80,100):raise ValueError('registered precision')
    if any(os.environ.get(k)!=v for k,v in THREAD_ENVIRONMENT.items()):raise ValueError('one numerical thread')
    packet,_=inputs(sign);spectrum=source(sign)
    root=Path(output).resolve()
    if root.is_relative_to(ROOT):raise ValueError('exclusive external output')
    root.mkdir(exist_ok=False)
    print(dict(stage='full-N32-inertia-authority-complete',sign=sign,digits=digits),flush=True)
    try:
        from docs.reference_cases.ge_beam3_n32_energy_inertia import audit
        result=audit(packet['left'],packet['right'],packet['geometric'],packet['kinetic'],
            tuple(packet['free_dofs']),tuple(packet['algebraic_dofs']),(0.,),digits=digits)
        validate(result,digits);negative=result['rows'][0]['negative']
        seen=sum(x<0 for x in spectrum['eigenvalues'])
        # The full congruence counts all coordinates independently of the six-mode solver.
        agree=negative==seen
        guard(revision);inputs(sign);source(sign)
        write(root/'inertia.json',dict(schema='GE_BEAM3_N32_FULL_NATIVE_INERTIA_V1',revision=revision,sign=sign,digits=digits,
            packet_sha256=PACKETS[sign],spectrum_sha256=SPECTRA[sign],result=result,
            signed_spectrum_negative_count=seen,full_count_matches_saved_low_modes=agree,
            continuum_full_inertia_proved=False,interval_certified=False,production_qualified=False,
            independent_author_review=False,equilibrium_rerun=False,spectrum_rerun=False))
        print(dict(stage='full-N32-inertia-complete',sign=sign,digits=digits,negative=negative,positive=result['rows'][0]['positive'],agreement=agree),flush=True)
    except BaseException:
        write(root/'failure.json',dict(revision=revision,sign=sign,digits=digits,error=traceback.format_exc(),production_qualified=False))
        raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);p.add_argument('--sign',choices=('plus','minus'),required=True)
    p.add_argument('--digits',type=int,choices=(80,100),required=True);p.add_argument('--output',required=True)
    a=p.parse_args();run(a.revision,a.sign,a.digits,a.output)
