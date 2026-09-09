"""Hash-bound saved-field comparison; imports the separate BVP after guard."""
from hashlib import sha256
from pathlib import Path
import argparse,json,sys
from docs.reference_cases.ge_beam3_retained_prestress_protocol import strict_bytes
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,ROOT

ARCHIVE=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-spatial-equilibrium-e43947c-20260909')
MANIFEST='ed4f312a75fd6f91e6e7ead0634235a376950aa750ba76bd8cfcfc36ec462d9c'
CASES={'plus-small':('successful-smoke/output/equilibrium.json','82c02d73d4a80b52a5cf5f7b08c474aaebe4c307f55220aa4d27e8d502ea1036'),
       'minus-small':('signed-amplitude-probes/minus-small/output/equilibrium.json','90c43f143023b5f3e372c9ee6cbd7d16c46d66e7b5f4255fd7786db760227ad6'),
       'plus-large':('signed-amplitude-probes/plus-large/output/equilibrium.json','0c30e4f199a62389406cd48982a8e4f6b9ade88a642255f0fa7876594c1124a5'),
       'minus-large':('signed-amplitude-probes/minus-large/output/equilibrium.json','09341803a0001dc5e452d0db7761bbf11c5f723b2902bd06da2340a382c3ff5c')}

def source(case):
    if case not in CASES:raise ValueError('registered spatial case')
    manifest=(ARCHIVE/'manifest.json').read_bytes()
    if sha256(manifest).hexdigest()!=MANIFEST:raise ValueError('spatial archive changed')
    entries={r['path']:r for r in strict_bytes(manifest)['entries']}
    path,digest=CASES[case];raw=(ARCHIVE/path).read_bytes()
    if entries[path]['sha256']!=digest or len(raw)!=entries[path]['bytes'] or sha256(raw).hexdigest()!=digest:raise ValueError('spatial input changed')
    value=strict_bytes(raw)
    if value['production_qualified'] is not False or value['elastic_origin_only'] is not True:raise ValueError('elastic diagnostic input only')
    return raw,value

def run(revision,case,profile,output):
    guard(revision);raw,record=source(case)
    if profile not in ('BVP7','BVP9'):raise ValueError('registered profile')
    output=Path(output).resolve()
    if output.exists() or output.is_relative_to(ROOT):raise ValueError('fresh external comparison directory')
    output.mkdir()
    import numpy as np
    from docs.reference_cases import ge_beam3_spatial_continuum as continuum
    result,metadata=continuum.solve(record,profile,progress=lambda row:print(row,flush=True))
    locations=[];weights=[];stress=[];strain=[];frames=[]
    for element in record['recovery']:
        for row in element['stations']:
            locations.append(-1.+(element['element_id']-1)*.1+.05*(row['xi']+1.));weights.append(row['measure'])
            stress.append(np.array(row['resultants'])+np.array(row['resultants_low']))
            strain.append(np.array(row['strain'])+np.array(row['strain_low']));frames.append(row['current_frame'])
    x=np.array(locations);w=np.array(weights);actual=np.array(stress)
    _,ref_frames,expected=continuum.sample(result,x);expected=expected.T
    energy_norm=lambda v:float(np.sum(w[:,None]*v*v/continuum.C))
    recovery_error=float(np.sqrt(energy_norm(actual-expected)/energy_norm(expected)))
    node_x=np.linspace(-1.,1.,41);nodal,_,_=continuum.sample(result,node_x)
    original=continuum.reference(node_x)[0];positions=np.array(record['mechanical']['positions'])+np.array(record['mechanical']['position_low'])
    position_error=float(np.linalg.norm(positions.T-nodal[:3])/np.linalg.norm(nodal[:3]-original))
    e64=continuum.energy(result,64);e128=continuum.energy(result,128)
    if abs(e64-e128)/max(abs(e128),np.finfo(float).tiny)>1e-8:raise RuntimeError('reference energy quadrature unresolved')
    discrete_energy=float(.5*np.sum(w[:,None]*actual*np.array(strain)))
    errors=dict(load=abs(record['load']-metadata['load'])/abs(metadata['load']),
        position=position_error,resultant_energy_norm=recovery_error,energy=abs(discrete_energy-e128)/abs(e128))
    sample_x=np.unique(np.r_[np.linspace(-1.,1.,161),node_x,x]);values,directors,resultants=continuum.sample(result,sample_x)
    record_out=dict(schema='GE_BEAM3_SPATIAL_CONTINUUM_COMPARISON_V1',revision=revision,case=case,
        input_sha256=sha256(raw).hexdigest(),amplitude=record['amplitude'],reference=metadata,
        sample_x=sample_x,state=values,frames=directors,resultants=resultants,
        energy_orders=[e64,e128],discrete_energy=discrete_energy,errors=errors,
        all_engineering_errors_below_two_percent=bool(max(errors.values())<.02),
        reference_only_used_discrete_fields_as_initial_guess=True,independent_authorship_review='PENDING',
        multiprecision_or_interval_certificate=False,production_qualified=False,
        postbuckled_branch_qualified=False,production_restriction='NO_GO_PRODUCTION_RESTRICTION_UNCHANGED')
    def plain(v):
        if isinstance(v,np.ndarray):return plain(v.tolist())
        if isinstance(v,np.generic):return v.item()
        if isinstance(v,dict):return {k:plain(x) for k,x in v.items()}
        if isinstance(v,(list,tuple)):return [plain(x) for x in v]
        return v
    encoded=(json.dumps(plain(record_out),sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode('ascii')
    strict_bytes(encoded);guard(revision)
    if source(case)[0]!=raw:raise ValueError('input changed during comparison')
    with (output/'comparison.json').open('xb') as f:f.write(encoded)
    print(dict(stage='spatial-comparison-complete',case=case,profile=profile,errors=errors),flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);p.add_argument('--case',required=True)
    p.add_argument('--profile',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    run(a.revision,a.case,a.profile,a.output)
if __name__=='__main__':main()
