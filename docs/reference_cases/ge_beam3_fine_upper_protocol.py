"""Standard-library authority for one fixed fine-mesh upper-endpoint probe."""
from hashlib import sha256
from pathlib import Path
from docs.reference_cases.ge_beam3_retained_prestress_protocol import canonical,strict_bytes,read,bind,bound,digest

ROOT=Path(__file__).resolve().parents[2]
DROP=.0456
TARGETS=(.01,.02,.03,DROP)
CAPACITY_SHA='37db04ffd069474085fd4cadad557959fe0d43d57c1a4626a83c7aa0eba7a181'
SCHEMA='GE_BEAM3_FINE_UPPER_REQUEST_V1'

GUARD_SHA='d43a7194a14686907df72f3ab75e0f63a407707dc5353ff2f69e4966ecbf5df9'
LOWER=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-loaded-refinement-820e70d-20260909')
LOWER_MANIFEST='7acfda1331528d3bae77810147a40c817ad4cf4d4e4d16968fd76417e959f3f2'
LOWER_HASHES={20:('cf2efd7c34571d56f56a0dbd5cc777be072362823cf030a035867bfa97ed6ebb','509b7a0ce2eeb49ff203cb847ded54676677a40d657e936a49f4a82eb5fd4064'),
              24:('2525a7aa58e83b5414a089b88d4d2c8345f85815863d6f906e2ee854d07a1ced','2e4e441d62dd3422f00b80564e1607652512b4a475b945d11137cc758514c59d')}

def authority():
    from docs.reference_cases.ge_beam3_loaded_refinement_protocol import authority as capacity
    from docs.reference_cases.ge_beam3_controlled_onset_protocol import reference
    capacity()
    raw=read(ROOT/'docs/reference_cases/ge_beam3_capture_guard_status.json')
    if sha256(raw).hexdigest()!=GUARD_SHA:raise ValueError('guard source authority')
    v=strict_bytes(raw)
    if (v['candidate_commit']!='fec94ba119f9efbbfb93bee4828d975a553db1bf'
            or v['production_qualified'] is not False or v['packets_match_historical_bytes'] is not True):
        raise ValueError('bounded guard validation required')
    raw=read(LOWER/'archive-manifest.json')
    if sha256(raw).hexdigest()!=LOWER_MANIFEST:raise ValueError('lower archive authority')
    manifest=strict_bytes(raw);points={}
    for n,hashes in LOWER_HASHES.items():
        name=f'runs/n{n}/result.json';raw=read(LOWER/name)
        if manifest[name]!=[len(raw),sha256(raw).hexdigest().upper()]:raise ValueError('lower science authority')
        row=strict_bytes(raw)
        if (row['macros']!=n or row['drop']!=.045 or row['negative_counts']!={'planar':1,'lateral':0}
                or row['production_qualified'] is not False or row['exact_factor_decoupling'] is not True
                or (row['checkpoint_sha256'],row['packet_sha256'])!=hashes):
            raise ValueError('registered lower evidence')
        for family,count in row['negative_counts'].items():
            audits=row['families'][family]
            if [a['digits'] for a in audits]!=[80,100] or any(a['rows'][0]['negative']!=count or a['mass_positive'] is not True or a['trace_positive'] is not True for a in audits):
                raise ValueError('lower factor precision/mass')
        points[str(n)]=dict(drop=row['drop'],load=row['load'],negative_counts=row['negative_counts'],
            checkpoint_sha256=hashes[0],packet_sha256=hashes[1],science_sha256=sha256(raw).hexdigest())
    return dict(lower=points,reference=reference())


def receipt(v):
    if (type(v) is not dict or v.get('reason')!='COMPLETED' or v.get('success') is not True
            or type(v.get('exit_code')) is not int or v['exit_code']!=0
            or v.get('error') is not None or v.get('cleanup_error') is not None
            or type(v.get('elapsed')) not in (int,float) or not 0<v['elapsed']<=600):
        raise ValueError('successful bounded process receipt required')
    for name in ('before','after'):
        x=v.get(name)
        if type(x) is not list or len(x)!=3 or any(type(i) is not int or i<0 for i in x) or x[1]!=0 or x[2]>24*1024**3:
            raise ValueError('empty bounded process tree required')

def request(v):
    if type(v) is not dict or set(v)!={'schema','revision','macros','stage','previous'} or v['schema']!=SCHEMA:
        raise ValueError('exact matched-drop request')
    digest(v['revision'],40)
    if type(v['macros']) is not int or v['macros'] not in (20,24):raise ValueError('registered refinement mesh')
    if type(v['stage']) is not int or not 1<=v['stage']<=6:raise ValueError('registered prefix/capture/audit stage')
    if v['stage']==1:
        if v['previous'] is not None:raise ValueError('first prefix must start virgin')
        return None
    return completion(v['previous'],v['revision'],v['macros'],v['stage']-1)

def completion(binding,revision,macros,stage):
    v=bound(binding)
    if type(v) is not dict or set(v)!={'request','ready','receipt'}:raise ValueError('exact completed worker authority')
    r=bound(v['request'])
    if (r.get('revision'),r.get('macros'),r.get('stage'))!=(revision,macros,stage):raise ValueError('previous worker identity')
    request(r);receipt(bound(v['receipt']));ready=bound(v['ready'])
    if type(ready) is not dict or set(ready)!={'schema','revision','macros','stage','request_sha256','checkpoint','packet','science','production_qualified'}:
        raise ValueError('exact ready fields')
    if (ready['schema']!='GE_BEAM3_FINE_UPPER_READY_V1' or ready['production_qualified'] is not False
            or any(ready[k]!=r[k] for k in ('revision','macros','stage')) or ready['request_sha256']!=v['request']['sha256']):
        raise ValueError('ready/request identity')
    capsule=bound(ready['checkpoint'])
    programme=dict(control_node=macros+1,direction=[0.,-1.,0.],max_backtracks=8,max_iterations=24,
        nodal_forces=dict(rows=[[macros+1,0.,-1.,0.]]),targets=list(TARGETS))
    if (capsule.get('schema')!='GE_BEAM3_RETAINED_GENERALIZED_TRANSLATION_ACCEPTED_CHAIN_V1'
            or canonical(capsule.get('program'))!=canonical(programme)
            or type(capsule.get('completed_targets')) is not int or capsule['completed_targets']!=min(stage,4)
            or len(capsule.get('records',()))!=min(stage,4)):
        raise ValueError('same complete native Programme prefix required')
    if stage<5:
        if ready['packet'] is not None or ready['science'] is not None:raise ValueError('premature physical evidence')
    else:
        packet=bound(ready['packet'])
        if (packet['checkpoint_sha256']!=ready['checkpoint']['sha256'] or packet['completed_targets']!=4
                or packet['displacement_target']!=DROP or packet['production_qualified'] is not False):raise ValueError('captured state identity')
        if stage==5 and ready['science'] is not None:raise ValueError('premature audit')
        if stage==6:
            science=bound(ready['science'])
            if (science['revision']!=revision or science['macros']!=macros or science['drop']!=DROP
                    or science['checkpoint_sha256']!=ready['checkpoint']['sha256'] or science['packet_sha256']!=ready['packet']['sha256']
                    or science['production_qualified'] is not False):raise ValueError('science state binding')
    return ready
