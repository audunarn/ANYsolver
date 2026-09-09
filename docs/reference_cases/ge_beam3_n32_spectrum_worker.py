"""Bounded N32 saved-factor spectrum; no owner, equilibrium or BVP execution."""
import argparse,os,traceback
from pathlib import Path
from hashlib import sha256
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,ROOT
from docs.reference_cases.ge_beam3_retained_prestress_protocol import strict_bytes,canonical
from docs.reference_cases.ge_beam3_retained_prestress_wave import write
from docs.reference_cases.e4_pl_s3_v2_bounded_process import THREAD_ENVIRONMENT
from docs.reference_cases.ge_beam3_next_spatial_native import member
from docs.reference_cases.ge_beam3_n32_snapshot_capture import sources,validate_packet,GUARD_POLICY

ARCHIVE=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-n32-snapshot-ebdf602-20260909')
MANIFEST='c4d423901838d9b47f8b4273a2e69359abfc96eea102389d9fa597e35fc68343'
PACKETS={'plus':'2a9c2f6f8b3c454afbe7249b8a7372328cc96e544f1f5c82cb791fe0186a6e43',
         'minus':'d4b1f195fba00466a431b88e861f51a043996e5f56a481e05316487a769fe6f4'}

def inputs(sign,root=ARCHIVE):
    if sign not in PACKETS:raise ValueError('registered signed N32 factors')
    raw=member(root,MANIFEST,'wave/'+sign+'-a/output/packet.json',PACKETS[sign])
    if member(root,MANIFEST,'wave/'+sign+'-b/output/packet.json',PACKETS[sign])!=raw:
        raise ValueError('accepted factor replicas differ')
    wrapper=strict_bytes(raw);prefix,v=sources(sign)
    if (wrapper['schema']!='GE_BEAM3_N32_SNAPSHOT_FACTORS_V1' or wrapper['sign']!=sign
        or wrapper['revision']!='ebdf6025a4b2103e0f472cb72290069213a9669f'
        or wrapper['compliance_guard_policy']!=GUARD_POLICY or wrapper['production_qualified'] is not False):
        raise ValueError('accepted native factor authority')
    validate_packet(wrapper['packet'],sign,prefix['seed-input.json'],prefix['checkpoint.json'],v['load'])
    return wrapper['packet'],v['mechanical']

def validate_result(r,digits):
    from math import isfinite
    if any(type(r[k]) is not int for k in ('digits','physical_dimension','algebraic_dimension')) or r['digits']!=digits or r['physical_dimension']!=381 or r['algebraic_dimension']!=189:
        raise ValueError('complete N32 physical spectrum dimensions')
    if len(r['full_modes'])!=6 or any(len(row)!=582 or any(type(x) is not float or not isfinite(x) for x in row) for row in r['full_modes']):
        raise ValueError('six complete finite original-coordinate modes')
    values=r['eigenvalues'];errors=r['original_residuals']
    if len(values)!=6 or any(type(x) is not float or not isfinite(x) or x==0 for x in values) or any(a>=b for a,b in zip(values,values[1:])):
        raise ValueError('six ordered signed roots')
    checks=[*errors,r['mass_orthogonality'],r['original_ritz_error']]
    if len(errors)!=6 or any(type(x) is not float or not isfinite(x) or not 0<=x<=1e-11 for x in checks):
        raise ValueError('original residual/mass/Ritz identity')
    if len(r['trace_pivots'])!=189:raise ValueError('all algebraic trace pivots')
    from decimal import Decimal
    if any(type(x) is not str or not Decimal(x).is_finite() or Decimal(x)<=0 for x in r['trace_pivots']):raise ValueError('positive algebraic pivots')
    if any(not Decimal(r[k]).is_finite() or not 0<=Decimal(r[k])<=Decimal('1e-60') for k in ('trace_residual','schur_skew')):
        raise ValueError('original high-precision trace/Schur identity')
    for key in ('negative_modes_retained','original_factors_used','physical_current_rest_mass'):
        if r[key] is not True:raise ValueError('physical spectrum policy')
    for key in ('production_qualified','interval_certified'):
        if r[key] is not False:raise ValueError('spectrum scope')

def run(revision,sign,digits,output):
    guard(revision)
    if type(digits) is not int or digits not in (80,100):raise ValueError('registered precision')
    if any(os.environ.get(k)!=v for k,v in THREAD_ENVIRONMENT.items()):raise ValueError('one numerical thread')
    packet,mechanical=inputs(sign)
    from docs.reference_cases.ge_beam3_modal_work_worker import source as reference_source,HASHES
    from docs.reference_cases.ge_beam3_spatial_ritz_worker import source as continuum_source,INPUTS
    reference=reference_source(sign);continuum=continuum_source(sign)
    root=Path(output).resolve()
    if root.is_relative_to(ROOT):raise ValueError('exclusive external output')
    root.mkdir(exist_ok=False)
    def progress(row):print(dict(sign=sign,digits=digits,**row),flush=True)
    progress(dict(stage='saved-N32-spectrum-authority-complete'))
    try:
        from docs.reference_cases.ge_beam3_n32_physical_pencil import spectrum
        from docs.reference_cases.ge_beam3_n32_spectral_compare import compare
        result=spectrum(packet,digits,6,progress);validate_result(result,digits)
        # Preserve a complete native spectrum if subsequent comparison fails.
        spectral=dict(schema='GE_BEAM3_N32_SAVED_PHYSICAL_SPECTRUM_V1',revision=revision,sign=sign,digits=digits,
            packet_sha256=PACKETS[sign],result=result,production_qualified=False,independent_author_review=False)
        write(root/'spectrum.json',spectral)
        comparison=compare(result,reference['result'],continuum,mechanical)
        progress(dict(stage='six-mode-physical-comparison-complete',comparison=comparison))
        guard(revision);inputs(sign);reference_source(sign);continuum_source(sign)
        write(root/'comparison.json',dict(schema='GE_BEAM3_N32_SAVED_SPECTRAL_COMPARISON_V1',revision=revision,
            sign=sign,digits=digits,spectrum_sha256=sha256(canonical(spectral)).hexdigest(),packet_sha256=PACKETS[sign],
            reference_sha256=HASHES[sign],continuum_sha256=INPUTS[sign][1],comparison=comparison,
            equilibrium_rerun=False,reference_spectrum_rerun=False,history_advanced=False,
            production_qualified=False,independent_author_review=False))
        progress(dict(stage='N32-spectral-worker-complete'))
    except BaseException:
        write(root/'failure.json',dict(revision=revision,sign=sign,digits=digits,error=traceback.format_exc(),production_qualified=False))
        raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);p.add_argument('--sign',choices=('plus','minus'),required=True)
    p.add_argument('--digits',type=int,choices=(80,100),required=True);p.add_argument('--output',required=True)
    a=p.parse_args();run(a.revision,a.sign,a.digits,a.output)
