"""Hash-bound next-endpoint comparison, no ANYsolver mechanics imports."""
import argparse,os
from pathlib import Path
from hashlib import sha256
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,ROOT
from docs.reference_cases.ge_beam3_retained_prestress_protocol import strict_bytes,read,canonical
from docs.reference_cases.ge_beam3_retained_prestress_wave import write
from docs.reference_cases.e4_pl_s3_v2_bounded_process import THREAD_ENVIRONMENT
from docs.reference_cases.ge_beam3_spatial_continuum_worker import source as guess_source

ARCHIVE=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-precise-continuation-43f18e3-20260909')
MANIFEST='b7bcc4a9e513050a42b1542b081ba3c8ed22ff108044a6b5cdbb15586746cfac'
HASHES={'plus':('b1c74d0ff21bb4bc6e8bfc4f038bca16ebfc6eba4e1eecce5cd317cf0ea0702a',
                '395f582692631e7fffc4ce150e22fd552724aa03b9e3daa9f5f6146f6921b071'),
        'minus':('602241bee7a56edd7834ba5dc613873a2c52ae42d840807ad098dcf569586c5d',
                 '3befe087da0c88456ec649cc74dc4b05580a9ec4efb04d041745c39f99d4a988')}
REFERENCE_SHA='2f3c960cf0dfda2b62d2e3e0073533ee390e1c5e3af993758aa808f64401f1b9'


def inputs(sign,archive=ARCHIVE):
    if sign not in HASHES:raise ValueError('registered signed reference')
    raw=read(archive/'manifest.json')
    if sha256(raw).hexdigest()!=MANIFEST:raise ValueError('accepted continuation manifest')
    entries={r['path']:r for r in strict_bytes(raw)['entries']};records=[]
    for name,digest in zip(('checkpoint.json','recovery.json'),HASHES[sign]):
        path='wave/'+sign+'-a/output/'+name;data=read(archive/path)
        if len(data)!=entries[path]['bytes'] or sha256(data).hexdigest()!=digest or entries[path]['sha256']!=digest:
            raise ValueError('immutable native endpoint binding')
        records.append(strict_bytes(data))
    checkpoint,recovery=records;target=.0065 if sign=='plus' else -.0065
    if (checkpoint['schema']!='GE_BEAM3_ELASTIC_SEED_CONTINUATION_CHAIN_V1' or len(checkpoint['records'])!=1
            or checkpoint['completed_targets']!=1 or checkpoint['records'][0]['displacement_target']!=target
            or checkpoint['physical_loading_path_from_rest'] is not False or checkpoint['elastic_only'] is not True):
        raise ValueError('actual continued endpoint required')
    row=checkpoint['records'][0]
    if len(row['mechanical']['positions'])!=49 or len(recovery)!=24 or max(*row['metrics'],row['correction'])>1e-11:
        raise ValueError('N24 converged field coverage')
    return row,recovery


def station_data(recovery):
    import numpy as np
    if len(recovery)!=24:raise ValueError('24 recovered elements')
    locations=[];weights=[];stress=[];strain=[]
    for eid,element in enumerate(recovery,1):
        if element['element_id']!=eid or len(element['stations'])!=8:raise ValueError('ordered eight-station elements')
        for j,row in enumerate(element['stations']):
            if row['cell']!=j//4 or row['station']!=j%4 or not -1.<row['xi']<1. or row['measure']<=0:
                raise ValueError('interior station identity/measure')
            locations.append(-1.+(eid-1)/12.+(row['xi']+1.)/24.);weights.append(row['measure'])
            stress.append(np.array(row['resultants'])+row['resultants_low']);strain.append(np.array(row['strain'])+row['strain_low'])
    arrays=tuple(map(np.asarray,(locations,weights,stress,strain)))
    if arrays[2].shape!=(192,6) or arrays[3].shape!=(192,6) or any(not np.isfinite(a).all() for a in arrays):
        raise ValueError('finite complete engineering fields')
    return arrays


def run(revision,sign,output):
    guard(revision)
    if any(os.environ.get(k)!=v for k,v in THREAD_ENVIRONMENT.items()):raise ValueError('one numerical thread')
    if sha256(read(ROOT/'docs/reference_cases/ge_beam3_spatial_continuum.py')).hexdigest()!=REFERENCE_SHA:
        raise ValueError('unchanged continuum equations required')
    row,recovery=inputs(sign);guess_bytes,guess=guess_source(sign+'-large')
    root=Path(output).resolve()
    if root.is_relative_to(ROOT):raise ValueError('fresh external reference output')
    root.mkdir(exist_ok=False)
    import numpy as np
    from docs.reference_cases import ge_beam3_spatial_next_reference as reference
    from docs.reference_cases import ge_beam3_spatial_continuum as base
    solution,metadata=reference.solve(guess,row['displacement_target'],progress=lambda r:print(r,flush=True))
    x,w,stress,strain=station_data(recovery)
    _,_,expected=base.sample(solution,x);expected=expected.T
    norm=lambda a:float(np.sum(w[:,None]*a*a/base.C))
    if norm(expected)<=0:raise ValueError('nonzero reference field required')
    nodes=np.linspace(-1.,1.,49);nodal,_,_=base.sample(solution,nodes)
    displacement=float(np.linalg.norm(nodal[:3]-base.reference(nodes)[0]))
    if displacement<=0:raise ValueError('nonzero reference displacement')
    positions=np.array(row['mechanical']['positions'])+row['mechanical']['position_low']
    e64,e128=(base.energy(solution,n) for n in (64,128))
    if e128<=0 or abs(e64-e128)/e128>1e-8:raise ValueError('reference energy quadrature')
    energy=float(.5*np.sum(w[:,None]*stress*strain))
    errors=dict(load=abs(row['parameter']-metadata['load'])/abs(metadata['load']),
        position=float(np.linalg.norm(positions.T-nodal[:3]))/displacement,
        resultant_energy_norm=float(np.sqrt(norm(stress-expected)/norm(expected))),energy=abs(energy-e128)/e128)
    polynomial=reference.pack(solution.sol);copy=reference.unpack(polynomial)
    sites=base.validation_grid(solution.x)
    if not np.array_equal(copy(sites),solution.sol(sites)) or not np.array_equal(copy(sites,1),solution.sol(sites,1)):
        raise ValueError('saved continuum polynomial round trip')
    def plain(v):
        if isinstance(v,np.ndarray):return v.tolist()
        if isinstance(v,np.generic):return v.item()
        if isinstance(v,dict):return {k:plain(x) for k,x in v.items()}
        if isinstance(v,(tuple,list)):return [plain(x) for x in v]
        return v
    result=plain(dict(schema='GE_BEAM3_PRECISE_NEXT_SPATIAL_REFERENCE_V1',revision=revision,sign=sign,
        checkpoint_sha256=HASHES[sign][0],recovery_sha256=HASHES[sign][1],guess_sha256=sha256(guess_bytes).hexdigest(),
        reference_source_sha256=REFERENCE_SHA,reference=metadata,polynomial=polynomial,errors=errors,
        energy_orders=[e64,e128],native_energy=energy,native_load=row['parameter'],nodes=49,stations=192,
        station_x=x,station_weights=w,station_native=stress,station_strain=strain,station_expected=expected,
        native_positions=positions,nodal_expected=nodal,all_errors_below_two_percent=bool(max(errors.values())<.02),
        reference_only_uses_discrete_fields_as_initial_guess=True,saved_polynomial_exact_roundtrip=True,
        production_qualified=False,spatial_stability_qualified=False,physical_loading_path_from_rest=False,
        independent_author_review='PENDING',multiprecision_or_interval_certificate=False))
    write(root/'diagnostic.json',result)
    if not result['all_errors_below_two_percent']:raise ValueError('continued endpoint engineering comparison failed')
    guard(revision)
    if inputs(sign)!=(row,recovery) or guess_source(sign+'-large')[0]!=guess_bytes:raise ValueError('reference input changed')
    write(root/'comparison.json',result)
    print(dict(stage='continued-endpoint-compared',sign=sign,errors=errors),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);p.add_argument('--sign',choices=('plus','minus'),required=True)
    p.add_argument('--output',required=True);a=p.parse_args();run(a.revision,a.sign,a.output)
