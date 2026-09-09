"""Frozen three-bisection, actual-state search; standard-library authority."""
from hashlib import sha256
from math import isfinite
from pathlib import Path
from docs.reference_cases.ge_beam3_retained_prestress_protocol import canonical,strict_bytes,read,bind,bound,digest
from docs.reference_cases.ge_beam3_fine_upper_protocol import receipt

ROOT=Path(__file__).resolve().parents[2]
STATUS_SHA='e200322ff23ff2d4b2649d550f4f1435d906b64ac984da47e533823cba16f99d'
ARCHIVE=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-fine-upper-66a8d3d-20260909')
MANIFEST_SHA='675f9266e1f289b869c8f83c354387f8b2f37b054321d81afc1ec2346d13cee3'
SCHEMA='GE_BEAM3_FINE_ONSET_REQUEST_V1'
ROW_KEYS={'drop','load','planar_negative','lateral_negative','checkpoint_sha256','packet_sha256'}

def extent(n):
    if type(n) is not int or n not in (20,24):raise ValueError('registered fine mesh')

def row(v):
    r=dict(drop=v['drop'],load=v['load'],planar_negative=v['negative_counts']['planar'],lateral_negative=v['negative_counts']['lateral'],
        checkpoint_sha256=v['checkpoint_sha256'],packet_sha256=v['packet_sha256'])
    validate_row(r);return r

def validate_row(r):
    if type(r) is not dict or set(r)!=ROW_KEYS:raise ValueError('exact actual-point fields')
    for k in ('drop','load'):
        if type(r[k]) is not float or not isfinite(r[k]):raise ValueError('finite actual point')
    for k in ('planar_negative','lateral_negative'):
        if type(r[k]) is not int or r[k]<0:raise ValueError('plain negative count')
    if r['lateral_negative'] not in (0,1):raise ValueError('multiple lateral direction in registered search')
    for k in ('checkpoint_sha256','packet_sha256'):digest(r[k])

def authority():
    from docs.reference_cases.ge_beam3_fine_upper_protocol import authority as inherited
    old=inherited();raw=read(ROOT/'docs/reference_cases/ge_beam3_fine_upper_status.json')
    if sha256(raw).hexdigest()!=STATUS_SHA:raise ValueError('fine upper status authority')
    s=strict_bytes(raw)
    if s['terminal']!='PRIVATE_FINE_ONSET_BRACKETS_OBSERVED' or s['production_qualified'] is not False:raise ValueError('observed upper authority')
    raw=read(ARCHIVE/'archive-manifest.json')
    if sha256(raw).hexdigest()!=MANIFEST_SHA:raise ValueError('fine upper archive authority')
    manifest=strict_bytes(raw);points={}
    for n in (20,24):
        name=f'runs/n{n}/result.json';raw=read(ARCHIVE/name)
        if manifest[name]!=[len(raw),sha256(raw).hexdigest().upper()]:raise ValueError('upper science hash')
        upper=strict_bytes(raw)
        if (upper['schema']!='GE_BEAM3_FINE_UPPER_LOADED_V1' or upper['revision']!=s['candidate_commit'] or upper['macros']!=n
                or upper['drop']!=.0456 or upper['negative_counts']['lateral']!=1 or upper['production_qualified'] is not False):raise ValueError('upper actual point identity')
        points[str(n)]=dict(left=row(old['lower'][str(n)]),right=row(upper))
    return dict(points=points,reference=old['reference'],upper_manifest_sha256=MANIFEST_SHA,upper_status_sha256=STATUS_SHA)

def search(rows,seed):
    if type(rows) is not list or len(rows)>3 or type(seed) is not dict or set(seed)!={'left','right'}:raise ValueError('bounded search extent')
    left,right=seed['left'],seed['right'];validate_row(left);validate_row(right)
    if (left['drop'],right['drop'],left['lateral_negative'],right['lateral_negative'])!=(.045,.0456,0,1):raise ValueError('registered initial bracket')
    for r in rows:
        validate_row(r)
        if r['drop']!=float((left['drop']+right['drop'])/2):raise ValueError('registered midpoint order')
        if r['lateral_negative']==0:left=r
        else:right=r
    return (float((left['drop']+right['drop'])/2) if len(rows)<3 else None),left,right

def science(v,revision,n,index):
    expected={'schema','revision','macros','index','drop','load','negative_counts','families','geometry','checkpoint_sha256','packet_sha256',
        'exact_factor_decoupling','critical_point_agreement_established','same_branch_uniqueness_proved','production_qualified','independent_review'}
    if type(v) is not dict or set(v)!=expected:raise ValueError('exact point science schema')
    if (v['schema']!='GE_BEAM3_FINE_ONSET_POINT_V1' or v['revision']!=revision or type(v['macros']) is not int or v['macros']!=n
            or type(v['index']) is not int or v['index']!=index or v['production_qualified'] is not False
            or v['critical_point_agreement_established'] is not False or v['same_branch_uniqueness_proved'] is not False
            or v['exact_factor_decoupling'] is not True or v['independent_review']!='PENDING'):raise ValueError('point science identity/claims')
    if set(v['families'])!={'planar','lateral'} or set(v['negative_counts'])!={'planar','lateral'}:raise ValueError('exact two physical families')
    for family,audits in v['families'].items():
        if [a['digits'] for a in audits]!=[80,100]:raise ValueError('two ordered independent precisions')
        for a in audits:
            if (a['mass_positive'] is not True or a['trace_positive'] is not True or len(a['rows'])!=1
                    or a['rows'][0]['shift']!=0. or a['rows'][0]['negative']!=v['negative_counts'][family]):raise ValueError('actual factor audit disagreement')
    if type(v['geometry']) is not list or len(v['geometry'])!=4:raise ValueError('all four owned records')
    keys={'cell_rotation_reflection_error','nodal_frame_reflection_error','out_of_plane_position','physical_second_director_error','position_reflection_error'}
    if any(set(g)!=keys or any(type(x) is not float or not isfinite(x) or not 0<=x<=1e-11 for x in g.values()) for g in v['geometry']):raise ValueError('actual planar reflection')
    return row(v)

def assignment(v):
    extent(v['macros']);digest(v['revision'],40)
    if type(v['index']) is not int or not 0<=v['index']<3:raise ValueError('three registered midpoints')
    prior=bound(v['prior'])
    if (type(prior) is not dict or set(prior)!={'revision','macros','rows','outputs'} or prior['revision']!=v['revision']
            or type(prior['macros']) is not int or prior['macros']!=v['macros'] or type(prior['rows']) is not list
            or type(prior['outputs']) is not list or len(prior['rows'])!=len(prior['outputs']) or len(prior['rows'])!=v['index']):raise ValueError('ordered prior authority')
    for i,(r,b) in enumerate(zip(prior['rows'],prior['outputs'])):
        if science(bound(b),v['revision'],v['macros'],i)!=r:raise ValueError('prior scientific binding')
    seed=authority()['points'][str(v['macros'])];expected,_,_=search(prior['rows'],seed)
    if type(v['drop']) is not float or v['drop']!=expected:raise ValueError('actual registered next point')
    return prior

def request(v):
    if type(v) is not dict or set(v)!={'schema','revision','macros','index','drop','prior','stage','previous'} or v['schema']!=SCHEMA:raise ValueError('exact fine onset request')
    assignment(v)
    if type(v['stage']) is not int or not 1<=v['stage']<=6:raise ValueError('registered prefix/capture/audit stage')
    if v['stage']==1:
        if v['previous'] is not None:raise ValueError('new programme must start virgin')
        return None
    return completion(v['previous'],v['revision'],v['macros'],v['index'],v['drop'],v['prior'],v['stage']-1)

def completion(binding,revision,n,index,drop,prior,stage):
    v=bound(binding)
    if type(v) is not dict or set(v)!={'request','ready','receipt'}:raise ValueError('exact completion authority')
    r=bound(v['request'])
    if (r.get('revision'),r.get('macros'),r.get('index'),r.get('drop'),r.get('prior'),r.get('stage'))!=(revision,n,index,drop,prior,stage):raise ValueError('previous worker identity')
    request(r);receipt(bound(v['receipt']));ready=bound(v['ready'])
    if type(ready) is not dict or set(ready)!={'schema','revision','macros','index','drop','stage','request_sha256','checkpoint','packet','science','production_qualified'}:raise ValueError('exact ready schema')
    if (ready['schema']!='GE_BEAM3_FINE_ONSET_READY_V1' or ready['production_qualified'] is not False
            or any(ready[k]!=r[k] for k in ('revision','macros','index','drop','stage')) or ready['request_sha256']!=v['request']['sha256']):raise ValueError('ready request identity')
    capsule=bound(ready['checkpoint']);programme=dict(control_node=n+1,direction=[0.,-1.,0.],max_backtracks=8,max_iterations=24,
        nodal_forces=dict(rows=[[n+1,0.,-1.,0.]]),targets=[.01,.02,.03,drop])
    if (capsule.get('schema')!='GE_BEAM3_RETAINED_GENERALIZED_TRANSLATION_ACCEPTED_CHAIN_V1'
            or canonical(capsule.get('program'))!=canonical(programme) or type(capsule.get('completed_targets')) is not int
            or capsule['completed_targets']!=min(stage,4) or len(capsule.get('records',()))!=min(stage,4)):raise ValueError('same complete native Programme prefix required')
    if stage<5:
        if ready['packet'] is not None or ready['science'] is not None:raise ValueError('premature factors')
    else:
        packet=bound(ready['packet'])
        if (packet['checkpoint_sha256']!=ready['checkpoint']['sha256'] or packet['completed_targets']!=4
                or packet['displacement_target']!=drop or packet['production_qualified'] is not False):raise ValueError('actual factor identity')
        if stage==5 and ready['science'] is not None:raise ValueError('premature audit')
        if stage==6:
            s=science(bound(ready['science']),revision,n,index)
            if s['drop']!=drop or s['checkpoint_sha256']!=ready['checkpoint']['sha256'] or s['packet_sha256']!=ready['packet']['sha256']:raise ValueError('point factor binding')
    return ready

def finish(rows,n,auth):
    extent(n);next_drop,left,right=search(rows,auth['points'][str(n)])
    if next_drop is not None or not 0<right['drop']-left['drop']<=.000098:raise ValueError('complete three-bisection bracket required')
    refs=[v[s] for v in auth['reference'].values() for s in ('left','right')]
    errors={k:max(abs(r[k]/ref[k]-1.) for r in (left,right) for ref in refs) for k in ('drop','load')}
    passed=max(errors.values())<.02
    return dict(macros=n,rows=rows,bracket=[left,right],endpoint_errors=errors,engineering_pass=passed,
        disposition='PRIVATE_FINE_ONSET_ENGINEERING_PASS' if passed else 'NO_GO_FINE_CONTROLLED_ONSET_COMPARISON',
        first_root_proven=False,root_uniqueness_established=False,production_qualified=False,independent_review='PENDING')
