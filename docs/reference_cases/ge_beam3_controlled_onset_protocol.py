"""Standard-library-only fixed cold-start search and immutable authority."""
from fractions import Fraction
from hashlib import sha256
from math import isfinite
from pathlib import Path
from docs.reference_cases.ge_beam3_retained_prestress_protocol import canonical,strict_bytes,read,bind,bound,digest

ARCHIVE=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-arch-repeats-307c48d-20260908')
MANIFEST_SHA='14d83c2b09cce8acf04649ce5e4f4d09fbbb500986ad2bac949ad0a0cb9dd4aa'
REF=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-p5-lateral-knot-20260906-e10841364c644b29b60f7c057c20a41e')
ROOTS={1:(29126,'64c47952dacd030d81ec3a631744179c300c33052551e1ebe5c16a9e191019fc'),
       2:(29139,'a7917c813953d181df20748c5e54179e0f84597585650b641fbd46b90e8f073c')}
ROW_KEYS={'index','drop','load','planar_negative','lateral_negative','checkpoint_sha256','packet_sha256','anchor_error'}


def extent(n):
    if type(n) is not int or n not in (4,8,12):raise ValueError('registered mesh')


def anchor(n):
    extent(n);mr=read(ARCHIVE/'archive-manifest.json')
    if sha256(mr).hexdigest()!=MANIFEST_SHA:raise ValueError('anchor archive authority')
    manifest=strict_bytes(mr);name=f'cycle-a/n{n}/step-07/science/state-07.json';raw=read(ARCHIVE/name)
    if manifest[name]!=[len(raw),sha256(raw).hexdigest().upper()]:raise ValueError('anchor checkpoint changed')
    value=strict_bytes(raw)
    if value['completed_steps']!=7:raise ValueError('anchor step')
    record=value['records'][-1];m=record['mechanical']
    drop=float(Fraction(.1)-Fraction(m['positions'][n][1])-Fraction(m['position_low'][n][1]))
    return record,drop,dict(bytes=len(raw),sha256=sha256(raw).hexdigest(),relative_path=name)


def reference():
    results={}
    for stride,(size,h) in ROOTS.items():
        raw=read(REF/f'root-stride-{stride}.json')
        if len(raw)!=size or sha256(raw).hexdigest()!=h:raise ValueError('continuum root authority')
        v=strict_bytes(raw)
        if v['schema']!='GE_BEAM3_P5_KNOT_RESOLVED_LATERAL_REFERENCE_V1' or v['production_qualified'] is not False:
            raise ValueError('continuum root schema')
        result=v['result']
        for side in ('left','right'):
            r=result[side]['reference']
            if (r['height'],r['axial'],r['shear'],r['bending'])!=(.1,1000.,400.,.01):raise ValueError('continuum model')
        lo=result['left'];hi=result['right']
        if not lo['normalized_determinant']>0>hi['normalized_determinant'] or not 0<hi['displacement']-lo['displacement']<=1e-8:
            raise ValueError('registered reference bracket')
        results[str(stride)]=dict(bytes=size,sha256=h,left=dict(drop=lo['displacement'],load=lo['load']),
            right=dict(drop=hi['displacement'],load=hi['load']))
    return results


def targets(drop):
    if type(drop) is not float or not isfinite(drop) or not .03<=drop<=.055:raise ValueError('registered point drop')
    return (.01,.02,.03) if drop==.03 else (.01,.02,.03,drop)


def search(rows,anchor_drop):
    if type(rows) is not list or len(rows)>11:raise ValueError('bounded complete search rows')
    low,high=.03,.055;left=right=None
    for i,r in enumerate(rows):
        if type(r) is not dict or set(r)!=ROW_KEYS or type(r['index']) is not int or r['index']!=i:raise ValueError('exact ordered row')
        for key in ('drop','load'):
            if type(r[key]) is not float or not isfinite(r[key]):raise ValueError('finite actual point')
        for key in ('planar_negative','lateral_negative'):
            if type(r[key]) is not int or r[key]<0:raise ValueError('exact negative count')
        for key in ('checkpoint_sha256','packet_sha256'):digest(r[key])
        expected=(anchor_drop,.03,.055)[i] if i<3 else float((low+high)/2)
        if r['drop']!=expected:raise ValueError('deterministic search target changed')
        if i==0:
            if type(r['anchor_error']) is not float or not 0<=r['anchor_error']<=1e-11:raise ValueError('actual branch anchor')
        elif r['anchor_error'] is not None:raise ValueError('unregistered anchor claim')
        c=r['lateral_negative']
        if i==1:
            if c!=0:raise ValueError('registered lower point must have no lateral negative direction')
            left=r
        elif i==2:
            if c!=1:raise ValueError('registered upper point must have one lateral negative direction')
            right=r
        elif i>=3:
            if c==0:low=expected;left=r
            elif c==1:high=expected;right=r
            else:raise ValueError('unregistered multiple lateral count in search')
    next_drop=(anchor_drop,.03,.055)[len(rows)] if len(rows)<3 else float((low+high)/2) if len(rows)<11 else None
    return next_drop,left,right


def finish(rows,n,anchor_drop,ref):
    extent(n);nxt,left,right=search(rows,anchor_drop)
    if nxt is not None:raise ValueError('eleven completed actual points required')
    if not 0<right['drop']-left['drop']<=.000098:raise ValueError('eight-step bracket width')
    refs=[v[s] for v in ref.values() for s in ('left','right')]
    errors={key:max(abs(p[key]/r[key]-1.) for p in (left,right) for r in refs) for key in ('drop','load')}
    passed=max(errors.values())<.02
    return dict(macros=n,rows=rows,reference=ref,endpoint_errors=errors,bracket=[left,right],
        finest_engineering_gate=(n==12),finest_engineering_pass=(passed if n==12 else None),
        disposition='NO_GO_FINEST_CONTROLLED_ONSET_COMPARISON' if n==12 and not passed else 'PRIVATE_OBSERVED_ONSET_BRACKET',
        first_root_proven=False,root_uniqueness_established=False,production_qualified=False,independent_review='PENDING')


def assignment(v):
    if type(v) is not dict or set(v)!={'schema','revision','macros','index','drop','prior'} or v['schema']!='GE_BEAM3_CONTROLLED_ONSET_ASSIGNMENT_V1':
        raise ValueError('exact controlled onset assignment')
    extent(v['macros']);digest(v['revision'],40)
    prior=bound(v['prior'])
    if type(prior) is not dict or set(prior)!={'revision','macros','rows','outputs'} or prior['revision']!=v['revision'] or prior['macros']!=v['macros']:
        raise ValueError('prior authority')
    if len(prior['rows'])!=len(prior['outputs']) or type(v['index']) is not int or v['index']!=len(prior['rows']):raise ValueError('exact prior extent')
    for row,b in zip(prior['rows'],prior['outputs']):
        result=bound(b)
        if result['row']!=row or result['revision']!=v['revision'] or result['macros']!=v['macros'] or result['production_qualified'] is not False:
            raise ValueError('prior scientific identity')
    _,drop,_=anchor(v['macros']);reference();expected,_,_=search(prior['rows'],drop)
    if expected is None or v['drop']!=expected:raise ValueError('next point assignment')
    targets(v['drop']);return prior
