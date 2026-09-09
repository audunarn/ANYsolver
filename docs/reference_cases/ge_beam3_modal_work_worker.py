"""Hash-bound saved-work diagnostics only; no native mechanics import."""
import argparse,os,traceback
from pathlib import Path
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,ROOT
from docs.reference_cases.ge_beam3_retained_prestress_protocol import strict_bytes
from docs.reference_cases.ge_beam3_retained_prestress_wave import write
from docs.reference_cases.e4_pl_s3_v2_bounded_process import THREAD_ENVIRONMENT
ARCHIVE=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-piecewise-spectrum-a6914e6-20260909')
MANIFEST='78cf530f830e7dd24e13bba1732a0f6947b7897293505b006d12154ba0e8a92f'
HASHES={'plus':'77bc4a8ba552571452cd27c1878fdfa1289fc4c037c1dce9b90d58fe79ad8586',
        'minus':'f850a1507bd9117f13bc108d12a77ee65e861a6eef1a886e7b21fcc2da1cf1e9'}
def source(sign,root=ARCHIVE):
    from docs.reference_cases.ge_beam3_next_spatial_native import member
    if sign not in HASHES:raise ValueError('registered signed endpoint')
    v=strict_bytes(member(root,MANIFEST,'wave/'+sign+'-a/output/comparison.json',HASHES[sign]))
    if v['sign']!=sign or v['revision']!='a6914e6111e595f6a0874ac8bd8cf7d04780a8c6' or v['comparison']['matched_signed_rates_below_two_percent_and_mac_at_least_095'] is not False:raise ValueError('preserved failed comparison authority')
    return v
def run(revision,sign,output):
    guard(revision)
    if any(os.environ.get(k)!=v for k,v in THREAD_ENVIRONMENT.items()):raise ValueError('one numerical thread')
    from docs.reference_cases.ge_beam3_spatial_physical_worker import inputs,PACKETS
    from docs.reference_cases.ge_beam3_piecewise_physical_worker import native_source,NATIVE
    from docs.reference_cases.ge_beam3_spatial_ritz_worker import source as continuum_source,INPUTS
    comparison=source(sign);packet,_=inputs(sign);modes=native_source(sign);continuum=continuum_source(sign)
    root=Path(output).resolve()
    if root.is_relative_to(ROOT):raise ValueError('exclusive external output')
    root.mkdir(exist_ok=False)
    def progress(row):print(row,flush=True)
    progress(dict(stage='saved-work-authority-complete',sign=sign))
    try:
        from docs.reference_cases.ge_beam3_modal_work_diagnostic import native,reference,differences
        n=native(packet,modes,progress)
        r=reference(continuum,comparison['result']['profiles'][2],progress)
        delta=differences(n,r['rows'])
        guard(revision);source(sign);inputs(sign);native_source(sign);continuum_source(sign)
        write(root/'diagnostic.json',dict(schema='GE_BEAM3_SAVED_MODAL_WORK_DIAGNOSTIC_V1',revision=revision,sign=sign,
            comparison_sha256=HASHES[sign],packet_sha256=PACKETS[sign],native_sha256=NATIVE[sign],continuum_sha256=INPUTS[sign][1],
            native=n,reference=r,differences=delta,comparison_gate_passed=False,production_qualified=False,
            native_workers_rerun=False,independent_author_review=False,causal_state_discretization_separation_proved=False))
        progress(dict(stage='saved-work-complete',sign=sign,differences=delta))
    except BaseException:
        write(root/'failure.json',dict(revision=revision,sign=sign,error=traceback.format_exc(),production_qualified=False))
        raise
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);p.add_argument('--sign',choices=('plus','minus'),required=True);p.add_argument('--output',required=True)
    a=p.parse_args();run(a.revision,a.sign,a.output)

