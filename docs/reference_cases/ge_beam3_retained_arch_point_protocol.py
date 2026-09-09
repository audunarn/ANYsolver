"""Standard-library-only authority and ordering for unchanged retained arch steps."""
from hashlib import sha256
import math
from docs.reference_cases.ge_beam3_retained_prestress_protocol import canonical, strict_bytes, read, bind, bound, digest

SCHEMA = 'GE_BEAM3_RETAINED_ARCH_POINT_ASSIGNMENT_V1'
TRANSCRIPT = 'GE_BEAM3_RETAINED_ARCH_POINT_TRANSCRIPT_V1'
MESHES = (2, 4, 8, 12)
ROW_KEYS = {'step','drop','load','reference_load','load_error','slope','reference_slope',
    'crown_direction','parameter_direction','recovery_error','energy','energy_error','material_error',
    'position_error','frame_error','force_balance','moment_balance','work_error','stations','geometry',
    'reference_errors','metrics','arc_gap','correction'}
REFERENCE_KEYS = {'height','displacement','axial','shear','bending','load','load_slope','force','parameter','fields',
    'iterations','callbacks','nodes','sensitivity_nodes','profile','boundary_error','differential_error',
    'sensitivity_error','strain_energy','work_error','production_qualified'}
GEOMETRY_KEYS = {'position_reflection_error','out_of_plane_position','nodal_frame_reflection_error',
    'cell_rotation_reflection_error','physical_second_director_error'}

def extent(macros):
    if type(macros) is not int or macros not in MESHES: raise ValueError('registered arch mesh')

def finite(value):
    if type(value) is not float or not math.isfinite(value): raise ValueError('finite binary64 field')
    return value

def identity_errors(row):
    if type(row) is not dict or set(row) != ROW_KEYS: raise ValueError('exact arch row schema')
    for key in ROW_KEYS-{'step','stations','geometry','reference_errors','metrics'}: finite(row[key])
    for key, keys in (('geometry',GEOMETRY_KEYS),('reference_errors',{'boundary','differential','sensitivity','work'})):
        if type(row[key]) is not dict or set(row[key]) != keys: raise ValueError('exact diagnostics schema')
        if any(finite(v)<0. for v in row[key].values()): raise ValueError('nonnegative diagnostics')
    if type(row['metrics']) is not list or len(row['metrics']) != 2: raise ValueError('two equilibrium metrics')
    errors = [*map(finite,row['metrics']),abs(row['arc_gap']),row['correction'],row['material_error'],
        row['force_balance'],row['moment_balance'],row['work_error'],*row['geometry'].values()]
    if any(v<0. or v>1e-11 for v in errors): raise ValueError('accepted arch identity failed')
    for key in ('load_error','recovery_error','energy_error','position_error','frame_error'):
        if row[key] < 0.: raise ValueError('nonnegative engineering error')
    if row['crown_direction'] <= 1e-12 or not 0. < row['drop'] <= .2: raise ValueError('registered crown branch')

def checkpoint(value, index):
    keys = {'schema','formulation','geometry','model_sha256','program','initial','records',
        'completed_steps','checkpoint_sha256'}
    if type(value) is not dict or set(value)!=keys: raise ValueError('checkpoint schema')
    if (type(value['completed_steps']) is not int or value['completed_steps']!=index
            or type(value['records']) is not list or len(value['records'])!=index):
        raise ValueError('complete checkpoint prefix')
    if value['checkpoint_sha256'] != sha256(canonical({k:v for k,v in value.items() if k!='checkpoint_sha256'})).hexdigest():
        raise ValueError('checkpoint inner hash')
    previous=value['initial']
    for j,row in enumerate([previous,*value['records']]):
        if (type(row) is not dict or type(row.get('step')) is not int or row['step']!=j
                or row.get('record_sha256')!=sha256(canonical({k:v for k,v in row.items() if k!='record_sha256'})).hexdigest()):
            raise ValueError('checkpoint record hash/order')
        if j:
            if row['previous_sha256']!=previous['record_sha256'] or canonical(row['origins'])!=canonical(previous['histories']):
                raise ValueError('checkpoint predecessor/history')
            if row['step_size']!=.01: raise ValueError('unchanged arch step size')
        previous=row
    return value

def outputs(pairs, macros):
    extent(macros)
    if type(pairs) is not list or len(pairs)>12: raise ValueError('bounded complete output list')
    rows=[]; previous=None
    for index,pair in enumerate(pairs,1):
        if type(pair) is not dict or set(pair)!={'state','point'}: raise ValueError('output pair schema')
        state=checkpoint(bound(pair['state']),index); proof=bound(pair['point'])
        if type(proof) is not dict or set(proof)!={'row','reference','recovered'}: raise ValueError('point schema')
        row=proof['row']; identity_errors(row)
        if (type(row['step']) is not int or row['step']!=index or type(row['stations']) is not int
                or row['stations']!=8*macros): raise ValueError('point/station coverage')
        if row['load']!=state['records'][-1]['parameter'] or row['metrics']!=state['records'][-1]['metrics']:
            raise ValueError('point differs from accepted state')
        reference=proof['reference']
        if (type(reference) is not dict or set(reference)!=REFERENCE_KEYS or reference['profile']!='BVP9'
                or reference['production_qualified'] is not False or reference['displacement']!=row['drop']
                or reference['load']!=row['reference_load'] or reference['load_slope']!=row['reference_slope']):
            raise ValueError('reference identity')
        if previous is not None:
            if (state['records'][:-1]!=previous['records'] or state['initial']!=previous['initial']
                    or state['model_sha256']!=previous['model_sha256'] or state['program']!=previous['program']):
                raise ValueError('complete immutable predecessor prefix')
            if not rows[-1]['drop']<row['drop']: raise ValueError('ordered crown displacements')
        rows.append(row); previous=state
    return rows

def assignment(value):
    if type(value) is not dict or set(value)!={'schema','revision','macros','index','prior'} or value['schema']!=SCHEMA:
        raise ValueError('exact assignment schema')
    digest(value['revision'],40); extent(value['macros'])
    if type(value['index']) is not int or not 1<=value['index']<=12: raise ValueError('registered point index')
    prior=bound(value['prior'])
    if type(prior) is not dict or set(prior)!={'schema','revision','macros','outputs'} or prior['schema']!=TRANSCRIPT:
        raise ValueError('prior transcript schema')
    if prior['revision']!=value['revision'] or type(prior['macros']) is not int or prior['macros']!=value['macros']:
        raise ValueError('prior source/mesh identity')
    rows=outputs(prior['outputs'],value['macros'])
    if len(rows)!=value['index']-1: raise ValueError('next point only, never retry or skip')
    return prior

def finish(pairs, macros):
    rows=outputs(pairs,macros)
    if len(rows)!=12: raise ValueError('twelve complete points required')
    if not rows[0]['slope']>0.>rows[-1]['slope'] or not rows[0]['reference_slope']>0.>rows[-1]['reference_slope']:
        raise ValueError('post-limit slope traversal required')
    if not any(b['load']<a['load'] for a,b in zip(rows,rows[1:])): raise ValueError('descending load traversal')
    maximums={key:max(row[key] for row in rows) for key in ('load_error','recovery_error','energy_error')}
    return dict(macros=macros,rows=rows,maximums=maximums,
        engineering_2_percent_pass=all(v<.02 for v in maximums.values()),actual_arc_from_virgin=True,
        post_limit_traversed=True,replay_identical=True,full_spatial_stability=False,
        independent_review='PENDING',production_qualified=False)
