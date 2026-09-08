"""Standard-library-only exact scheduling of the frozen 22-point Euler search."""
from hashlib import sha256
import json
import math
from pathlib import Path
import stat

EULER=float(math.pi**2/16)
ROW_KEYS={'index','compression','lambda_min','axial_error','reaction_error','checkpoint_sha256','full_partition_root_error'}

def canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode('ascii')

def _pairs(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('duplicate JSON key')
        result[key]=value
    return result

def _nonfinite(value):raise ValueError('nonfinite JSON value')

def strict_bytes(raw):
    value=json.loads(raw,object_pairs_hook=_pairs,parse_constant=_nonfinite)
    if canonical(value)!=raw:raise ValueError('strict canonical JSON required')
    return value

def read(path):
    path=Path(path);st=path.lstat()
    if not stat.S_ISREG(st.st_mode) or getattr(st,'st_file_attributes',0)&1024:
        raise ValueError('regular non-reparse evidence file required')
    if not 0<st.st_size<=128*1024**2:raise ValueError('bounded nonempty evidence')
    return path.read_bytes()

def bind(path):
    raw=read(path)
    return dict(path=str(Path(path).resolve()),bytes=len(raw),sha256=sha256(raw).hexdigest())

def bound(binding):
    if type(binding) is not dict or set(binding)!={'path','bytes','sha256'}:raise ValueError('exact file binding')
    if type(binding['path']) is not str or not Path(binding['path']).is_absolute():raise ValueError('absolute evidence path')
    if type(binding['bytes']) is not int:raise ValueError('plain byte count')
    digest(binding['sha256'])
    raw=read(binding['path'])
    if len(raw)!=binding['bytes'] or sha256(raw).hexdigest()!=binding['sha256']:raise ValueError('bound evidence changed')
    return strict_bytes(raw)

def digest(value,length=64):
    if type(value) is not str or len(value)!=length or any(c not in '0123456789abcdef' for c in value):
        raise ValueError('exact lowercase digest')

def _float(value):
    if type(value) is not float or not math.isfinite(value):raise ValueError('finite binary64 required')

def search(rows,macros):
    if type(macros) is not int or macros not in (1,2,4,8):raise ValueError('registered mesh count')
    if type(rows) is not list or len(rows)>22:raise ValueError('bounded ordered transcript')
    low,high=0.,2*EULER;lv=hv=None
    starts=(-.5*EULER,0.,.5*EULER,2*EULER)
    for index,row in enumerate(rows):
        if type(row) is not dict or set(row)!=ROW_KEYS:raise ValueError('exact point row')
        if type(row['index']) is not int or row['index']!=index:raise ValueError('contiguous point indices')
        for key in ('compression','lambda_min','axial_error','reaction_error'):_float(row[key])
        if any(not 0.<=row[k]<=1e-11 for k in ('axial_error','reaction_error')):raise ValueError('actual preload identity')
        digest(row['checkpoint_sha256'])
        error=row['full_partition_root_error']
        if macros==1 and index<4:
            _float(error)
            if not 0.<=error<=1e-11:raise ValueError('full paired partition check')
        elif error is not None:raise ValueError('unregistered full-paired check')
        expected=starts[index] if index<4 else float((low+high)/2)
        if row['compression']!=expected:raise ValueError('registered preload sequence changed')
        value=row['lambda_min']
        if index==1:lv=value
        if index==2 and not rows[0]['lambda_min']>rows[1]['lambda_min']>value>0.:
            raise ValueError('signed preload monotonicity')
        if index==3:
            if not value<0.:raise ValueError('negative upper bracket required')
            hv=value
        if index>=4:
            if value>0.:low,lv=expected,value
            else:high,hv=expected,value
    next_load=starts[len(rows)] if len(rows)<4 else (float((low+high)/2) if len(rows)<22 else None)
    return next_load,(low,high,lv,hv)

def finish(rows,macros):
    next_load,(low,high,lv,hv)=search(rows,macros)
    if next_load is not None:raise ValueError('complete 22-point evidence required')
    critical=float((low+high)/2);error=abs(critical/EULER-1.)
    if not lv>0.>=hv or not (high-low)/EULER<1e-5:raise ValueError('exact final bracket required')
    if macros==8 and not error<.02:raise ValueError('finest Euler engineering gate')
    return dict(macros=macros,rows=rows,critical_bracket=[low,high],bracket_eigenvalues=[lv,hv],
        critical_midpoint=critical,euler_reference=EULER,relative_euler_error=error,finest_engineering_gate=(macros==8),
        search='18_BISECTIONS_OF_ACTUAL_NODAL_NEWTON_PRELOADED_SIGNED_FACTOR_FAMILIES',
        current_frequency_is_not_a_load_factor=True,production_qualified=False,full_spatial_postbuckling_qualified=False)

def assignment(value):
    if type(value) is not dict or set(value)!={'schema','revision','macros','index','compression','prior'}:
        raise ValueError('exact assignment keys')
    if value['schema']!='GE_BEAM3_EULER_POINT_ASSIGNMENT_V1':raise ValueError('assignment schema')
    digest(value['revision'],40)
    prior=bound(value['prior'])
    if type(prior) is not dict or set(prior)!={'revision','macros','rows','outputs'}:raise ValueError('prior transcript schema')
    if prior['revision']!=value['revision'] or type(prior['macros']) is not int or prior['macros']!=value['macros']:
        raise ValueError('prior source/mesh authority')
    expected,_=search(prior['rows'],value['macros'])
    if type(prior['outputs']) is not list or len(prior['outputs'])!=len(prior['rows']):raise ValueError('complete prior output bindings')
    if type(value['index']) is not int or value['index']!=len(prior['rows']) or expected is None:raise ValueError('point index authority')
    _float(value['compression'])
    if value['compression']!=expected:raise ValueError('point load authority')
    for output in prior['outputs']:
        if type(output) is not dict or set(output)!={'state','point'}:raise ValueError('exact prior output pair')
        for binding in output.values():
            if type(binding) is not dict or set(binding)!={'path','bytes','sha256'}:raise ValueError('exact output binding')
            digest(binding['sha256'])
            if type(binding['bytes']) is not int or binding['bytes']<=0:raise ValueError('output bytes')
            if type(binding['path']) is not str or not Path(binding['path']).is_absolute():raise ValueError('output path')
    return prior
