"""N24 fields against unchanged continuum equations and frozen N20 errors."""
from pathlib import Path
from hashlib import sha256
import argparse,sys,json
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,ROOT
from docs.reference_cases.ge_beam3_retained_prestress_protocol import strict_bytes,read
from docs.reference_cases.ge_beam3_spatial_continue24 import seed_input
from docs.reference_cases.ge_beam3_spatial_continuum_worker import source

COARSE=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-spatial-continuum-e40cc66-20260909')
MANIFEST_SHA='43279d1c2ab2f76cf53f1aa3b15015b7475d15832f9751913b3bc62b486e5992'
HASHES={'plus-small':'93f9f209b979cdce8b040d41fbb5fb8a070c41f390e0464fcb4862a0bee9a152',
        'minus-small':'0d5057d49d0fe98476759a98a1dfd57f78a6242314f71e87ccbf6e2bcd766c26',
        'plus-large':'085a2df8dae9ee5a4cc16600edaec32cf20f800af604f6575ca8b17b09d840d9',
        'minus-large':'0e14cfaa21d88b449700710424c76278a1157d3810182314f8db4badd3a694af'}

def coarse(case,archive=COARSE):
    if case not in HASHES:raise ValueError('registered coarse case')
    manifest=read(archive/'manifest.json')
    if sha256(manifest).hexdigest()!=MANIFEST_SHA:raise ValueError('coarse manifest')
    name='wave/first/'+case+'-BVP9/output/comparison.json'
    entries={r['path']:r for r in strict_bytes(manifest)['entries']};raw=read(archive/name)
    if sha256(raw).hexdigest()!=HASHES[case] or entries[name]['sha256']!=HASHES[case] or len(raw)!=entries[name]['bytes']:raise ValueError('coarse evidence binding')
    return raw,strict_bytes(raw)

def location(element_id,xi):
    if type(element_id) is not int or not 1<=element_id<=24 or type(xi) is not float or not -1.<xi<1.:
        raise ValueError('exact N24 interior station identity')
    return -1.+(element_id-1)/12.+(xi+1.)/24.

def fields(kind,path,digest,recovery_path=None,recovery_sha256=None):
    raw=read(path)
    if sha256(raw).hexdigest()!=digest:raise ValueError('N24 comparison input hash')
    value=strict_bytes(raw);bindings=dict(input_sha256=digest)
    if kind=='seed':
        if recovery_path is not None or recovery_sha256 is not None:raise ValueError('seed contains its recovery')
        _,value=seed_input(path,digest)
        mechanical,recovery,amplitude,load=value['mechanical'],value['recovery'],value['amplitude'],value['load']
    elif kind=='endpoint':
        if recovery_path is None or recovery_sha256 is None:raise ValueError('endpoint recovery required')
        if (value['schema']!='GE_BEAM3_ELASTIC_SEED_CONTINUATION_CHAIN_V1'
                or type(value['completed_targets']) is not int or value['completed_targets']!=2
                or len(value['records'])!=2 or value['elastic_only'] is not True or value['physical_loading_path_from_rest'] is not False):
            raise ValueError('actual complete elastic endpoint required')
        row=value['records'][-1];mechanical=row['mechanical'];amplitude=row['displacement_target'];load=row['parameter']
        if amplitude not in (-.006,.006):raise ValueError('registered endpoint amplitude')
        rec=read(recovery_path)
        if sha256(rec).hexdigest()!=recovery_sha256:raise ValueError('endpoint recovery hash')
        recovery=strict_bytes(rec);bindings['recovery_sha256']=recovery_sha256
    else:raise ValueError('registered N24 comparison kind')
    if len(mechanical['positions'])!=49 or len(recovery)!=24:raise ValueError('N24 geometry/recovery extent')
    for i,element in enumerate(recovery,1):
        if element['element_id']!=i or len(element['stations'])!=8:raise ValueError('24 ordered eight-station elements')
        for j,row in enumerate(element['stations']):
            if row['cell']!=j//4 or row['station']!=j%4:raise ValueError('station half ordering')
            location(i,row['xi'])
    return mechanical,recovery,amplitude,load,bindings

def run(revision,kind,input_path,input_sha256,output,recovery_path=None,recovery_sha256=None):
    guard(revision)
    mechanical,recovery,amplitude,load,bindings=fields(kind,input_path,input_sha256,recovery_path,recovery_sha256)
    case=('plus' if amplitude>0 else 'minus')+('-small' if kind=='seed' else '-large')
    coarse_raw,coarse_value=coarse(case);guess_raw,guess=source(case)
    root=Path(output).resolve()
    if root.exists() or root.is_relative_to(ROOT):raise ValueError('fresh external N24 comparison output')
    root.mkdir()
    import numpy as np
    from docs.reference_cases import ge_beam3_spatial_continuum as continuum
    result,metadata=continuum.solve(guess,'BVP9',progress=lambda row:print(row,flush=True))
    locations=[];weights=[];stress=[];strain=[]
    for element in recovery:
        for row in element['stations']:
            locations.append(location(element['element_id'],row['xi']));weights.append(row['measure'])
            stress.append(np.array(row['resultants'])+np.array(row['resultants_low']))
            strain.append(np.array(row['strain'])+np.array(row['strain_low']))
    x=np.array(locations);w=np.array(weights);actual=np.array(stress)
    _,_,expected=continuum.sample(result,x);expected=expected.T
    norm=lambda v:float(np.sum(w[:,None]*v*v/continuum.C))
    error_recovery=float(np.sqrt(norm(actual-expected)/norm(expected)))
    node_x=np.linspace(-1.,1.,49);nodal,_,_=continuum.sample(result,node_x)
    original=continuum.reference(node_x)[0];positions=np.array(mechanical['positions'])+np.array(mechanical['position_low'])
    error_position=float(np.linalg.norm(positions.T-nodal[:3])/np.linalg.norm(nodal[:3]-original))
    e64=continuum.energy(result,64);e128=continuum.energy(result,128)
    if abs(e64-e128)/abs(e128)>1e-8:raise ValueError('reference energy quadrature')
    energy=float(.5*np.sum(w[:,None]*actual*np.array(strain)))
    errors=dict(load=abs(load-metadata['load'])/abs(metadata['load']),position=error_position,
        resultant_energy_norm=error_recovery,energy=abs(energy-e128)/abs(e128))
    ratios={k:errors[k]/coarse_value['errors'][k] for k in errors}
    # Compare reference construction at shared sites to the preserved result;
    # N24 station resampling does not change the reference equation or solution.
    shared_values,shared_frames,shared_stress=continuum.sample(result,np.array(coarse_value['sample_x']))
    if (metadata!=coarse_value['reference'] or shared_values.tolist()!=coarse_value['state']
            or shared_frames.tolist()!=coarse_value['frames'] or shared_stress.tolist()!=coarse_value['resultants']):
        raise ValueError('reference changed during N24 resampling')
    record=dict(schema='GE_BEAM3_N24_SPATIAL_REFINEMENT_COMPARISON_V1',revision=revision,case=case,
        kind=kind,macros=24,nodes=49,stations=192,amplitude=amplitude,load=load,reference=metadata,
        input_bindings=bindings,coarse_sha256=sha256(coarse_raw).hexdigest(),reference_guess_sha256=sha256(guess_raw).hexdigest(),
        errors=errors,coarse_errors=coarse_value['errors'],refinement_ratios=ratios,
        all_errors_below_two_percent=bool(max(errors.values())<.02),all_errors_decrease=bool(max(ratios.values())<1.),
        shared_reference_exactly_unchanged=True,energy_orders=[e64,e128],discrete_energy=energy,
        station_x=x,station_expected=expected,nodal_expected=nodal,production_qualified=False,
        physical_loading_path_from_rest=False,independent_authorship_review='PENDING',
        multiprecision_or_interval_certificate=False)
    def plain(v):
        if isinstance(v,np.ndarray):return plain(v.tolist())
        if isinstance(v,np.generic):return v.item()
        if isinstance(v,dict):return {k:plain(x) for k,x in v.items()}
        if isinstance(v,(list,tuple)):return [plain(x) for x in v]
        return v
    encoded=(json.dumps(plain(record),sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode('ascii')
    strict_bytes(encoded);guard(revision)
    if fields(kind,input_path,input_sha256,recovery_path,recovery_sha256)[-1]!=bindings or coarse(case)[0]!=coarse_raw or source(case)[0]!=guess_raw:raise ValueError('N24 comparison input changed')
    with (root/'comparison.json').open('xb') as f:f.write(encoded)
    print(dict(stage='N24-refinement-compared',case=case,errors=errors,ratios=ratios),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);p.add_argument('--kind',required=True)
    p.add_argument('--input',required=True);p.add_argument('--input-sha256',required=True);p.add_argument('--output',required=True)
    p.add_argument('--recovery');p.add_argument('--recovery-sha256');a=p.parse_args()
    run(a.revision,a.kind,a.input,a.input_sha256,a.output,a.recovery,a.recovery_sha256)
