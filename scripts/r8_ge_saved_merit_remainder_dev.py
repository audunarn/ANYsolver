"""Prepared stdlib saved-data remainder accounting; never calls mechanics or a solver."""
from pathlib import Path
import argparse,ast,json,math,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts import r8_ge_saved_compliance_dev as saved
DOC=saved.previous.DOC/'saved-merit-remainder-v1'
INPUT=DOC/'MERIT_INPUT.json'
SOURCE_NAMES=('test_source_exact_linear_and_signed_load','test_source_nonlinear_remainder_identity',
              'test_source_complete_roles_and_refusal','test_source_inventory_no_mechanics')
def sha(p):return saved.sha(p)
def write(p,v):saved.write(p,v)
def dot(a,b):
    if len(a)!=len(b):raise ValueError('complete matching row vectors required')
    return math.fsum(x*y for x,y in zip(a,b))
def norm(a):return math.sqrt(dot(a,a))
def mv(matrix,x):
    n=matrix['shape'][0]
    if matrix['shape']!=[len(x),len(x)]:raise ValueError('complete saved square operator required')
    rows=[[] for _ in range(n)]
    for i,j,v in zip(matrix['row'],matrix['col'],matrix['data']):rows[i].append(v*x[j])
    return [math.fsum(row) for row in rows]
def scatter_force(parts,n):
    rows=[[] for _ in range(n)]
    for part in parts:
        if len(part['slots'])!=len(part['force']):raise ValueError('complete actual local residual required')
        for i,v in zip(part['slots'],part['force']):rows[i].append(v)
    return [math.fsum(row) for row in rows]
def scatter_action(parts,x):
    rows=[[] for _ in x]
    for part in parts:
        slots=part['slots'];K=part['tangent']
        if len(K)!=len(slots) or any(len(row)!=len(slots) for row in K):raise ValueError('complete actual mapped local tangent required')
        for i,row in zip(slots,K):rows[i].append(math.fsum(v*x[j] for v,j in zip(row,slots)))
    return [math.fsum(row) for row in rows]
def merit_identity(r,a,e,t):
    if not len(r)==len(a)==len(e):raise ValueError('complete merit rows required')
    linear=2*t*dot(r,a);quadratic=t*t*dot(a,a)
    cross=2*dot([math.fsum((x,t*y)) for x,y in zip(r,a)],e);remainder=dot(e,e)
    actual=[math.fsum((x,t*y,z)) for x,y,z in zip(r,a,e)]
    change=dot(actual,actual)-dot(r,r)
    return dict(phi0=dot(r,r),phi_trial=dot(actual,actual),derivative0=2*dot(r,a),
        linear_term=linear,linear_model_quadratic=quadratic,remainder_cross=cross,remainder_squared=remainder,
        measured_change=change,decomposition_error=math.fsum((linear,quadratic,cross,remainder,-change)))
def validate(v):
    if v['amount']!=1/256 or v['current']['evaluation']!=14 or v['trial']['evaluation']!=23 or v['solve']['solve']!=5:raise ValueError('exact saved14/23/solve5 pair required')
    if len(v['weights'])!=132 or len(v['solve']['full_correction'])!=132:raise ValueError('complete mixed layout required')
    roles=[i for rows in v['roles'].values() for i in rows]
    if sorted(roles)!=list(range(132)) or len(v['free'])!=120:raise ValueError('complete disjoint132 roles/free120 required')
    if len(set(v['free']))!=120 or sorted(set(range(132))-set(v['free']))!=v['roles']['fixed_shell_support_rows']:raise ValueError('exact free/support partition required')
    if v['current']['state']['values']['shell_anchors']!=v['trial']['state']['values']['shell_anchors']:raise ValueError('saved shell anchor changed: representation refusal')
    for key in ('predecessor_shell_id','predecessor_beam_id'):
        if v['current_assembly'][key]!=v['trial_assembly'][key]:raise ValueError('same accepted constitutive parent required')
    if len(v['current_assembly']['local_contributions'])!=7 or len(v['trial_assembly']['local_contributions'])!=7:raise ValueError('complete seven local records required')
    for side in ('current','trial'):
        record=v[side]
        if len(record['residual'])!=132 or record['tangent']['shape']!=[132,132] or record['state']['unavailable']:raise ValueError('complete saved evaluation/state required')
        parts=v[side+'_assembly']['local_contributions']
        if [(x['kind'],len(x['slots'])) for x in parts]!=[('shell',24),('native',42),('native',42),('POINT',18),('POINT',18),('POINT',18),('POINT',18)]:raise ValueError('exact mixed local inventory required')
        maps=v[side+'_q4_maps']['maps']
        if maps['unavailable'] or any(key not in maps['values'] for key in ('u','differential','second','residual','spatial_tangent','rotation_anchors')):raise ValueError('Q4 representation evidence incomplete')
def prepare():
    if INPUT.exists():raise ValueError('preserve already prepared input')
    DOC.mkdir(parents=True,exist_ok=True)
    trace=saved.previous.DOC/'attempt-installed-fixed1/trace.jsonl'
    old=json.loads((saved.DERIVATIVE/'DERIVATIVE_INPUT.json').read_text())
    if sha(trace)!=old['trace_sha256']:raise ValueError('historical trace drift')
    pair={};assembly=None;q4=None;merits={}
    with trace.open() as stream:
        for line in stream:
            record=json.loads(line);kind=record['kind']
            if kind=='Q4_actual_maps':q4=record
            elif kind=='assembly':assembly=record
            elif kind=='evaluation' and record['evaluation'] in (14,23):pair[record['evaluation']]=(record,assembly,q4)
            elif kind=='merit' and ((record.get('evaluation')==14 and record['role']=='current') or (record.get('evaluation')==23 and record['role']=='trial')):merits[record['evaluation']]=record
    c,cparts,cmap=pair[14];b,bparts,bmap=pair[23]
    if c!=old['evaluation'] or cparts!=old['assembly']:raise ValueError('saved pair current drift')
    scale=json.loads(saved.INPUT.read_text());roles=scale['roles'].copy()
    roles['fixed_shell_support_rows']=sorted(set(range(132))-set(scale['free']))
    value=dict(current=c,trial=b,current_assembly=cparts,trial_assembly=bparts,current_q4_maps=cmap,trial_q4_maps=bmap,
        current_merit=merits[14],trial_merit=merits[23],amount=merits[23]['amount'],solve=old['solve'],
        weights=scale['W'],free=scale['free'],roles=roles,
        row_contract='common spatial wrench rows; native resultant reference dual rows and immutable POINT reference gap rows; no coordinate-support pullback; shell chart maps affect increment columns only',
        weight_contract='one original corrector frozen W at entry; same W across both merits, not recomputed at trial',
        source_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in (trace,saved.INPUT,saved.DERIVATIVE/'DERIVATIVE_INPUT.json',saved.DOC/'COMPLIANCE_TERMINAL_SELECTED.json')})
    validate(value);write(INPUT,value);write(DOC/'MERIT_INPUT_IDENTITY.json',dict(sha256=sha(INPUT)))
def input_data():
    if sha(INPUT)!=json.loads((DOC/'MERIT_INPUT_IDENTITY.json').read_text())['sha256']:raise ValueError('saved pair input drift')
    v=json.loads(INPUT.read_text());validate(v)
    for p,h in v['source_sha256'].items():
        if sha(ROOT/p)!=h:raise ValueError('prior saved evidence drift')
    return v
def analyze():
    v=input_data();c,b=v['current'],v['trial'];t=v['amount'];W=v['weights'];p=v['solve']['direction'];d=v['solve']['full_correction'];da=v['solve']['amplitude_delta']
    Kd0=mv(c['tangent'],d);Kdt=mv(b['tangent'],d)
    D0=[math.fsum((x,-y*da)) for x,y in zip(Kd0,p)];Dt=[math.fsum((x,-y*da)) for x,y in zip(Kdt,p)]
    remainder=[math.fsum((y,-x,-t*z)) for x,y,z in zip(c['residual'],b['residual'],D0)]
    trap=[t/2*math.fsum((y,-x)) for x,y in zip(D0,Dt)]
    force0=scatter_force(v['current_assembly']['local_contributions'],132);forcet=scatter_force(v['trial_assembly']['local_contributions'],132)
    local0=scatter_action(v['current_assembly']['local_contributions'],d);localt=scatter_action(v['trial_assembly']['local_contributions'],d)
    inferred_load_change=[math.fsum((ft,-f0,-rt,r0,-t*pp*da)) for ft,f0,rt,r0,pp in zip(forcet,force0,b['residual'],c['residual'],p)]
    role={}
    for name,rows in v['roles'].items():
        wn=lambda values:norm([W[i]*values[i] for i in rows])
        role[name]=dict(current_residual=wn(c['residual']),trial_residual=wn(b['residual']),linear_action=wn(D0),
            finite_remainder=wn(remainder),endpoint_tangent_trapezoid_remainder=wn(trap),
            trapezoid_defect=norm([W[i]*math.fsum((remainder[i],-trap[i])) for i in rows]),
            current_local_assembled_action_difference=norm([W[i]*math.fsum((local0[i],-Kd0[i])) for i in rows]),
            trial_local_assembled_action_difference=norm([W[i]*math.fsum((localt[i],-Kdt[i])) for i in rows]),
            inferred_dead_load_change_defect=wn(inferred_load_change))
    free=v['free'];r=[W[i]*c['residual'][i] for i in free];a=[W[i]*D0[i] for i in free];e=[W[i]*remainder[i] for i in free]
    identity=merit_identity(r,a,e,t)
    report=dict(status='SAVED_DATA_REMAINDER_OBSERVATION',new_physical_evaluations=0,new_solves=0,new_fd=0,
        no_acceptance_threshold_change=True,amount=t,roles=role,merit_identity=identity,
        recorded_merits=dict(current=v['current_merit']['value'],trial=v['trial_merit']['value']),
        merit_readout_difference=dict(current=norm(r)-v['current_merit']['value'],trial=norm([W[i]*b['residual'][i] for i in free])-v['trial_merit']['value']),
        actual_amplitude_change=b['value']-c['value'],predicted_amplitude_change=t*da,
        row_contract=v['row_contract'],weight_contract=v['weight_contract'],
        limitation='one finite pair/trapezoid cannot prove O(t^2) or tangent correctness; derivative cancellation limitations remain inherited',
        product_question='If compatible linear prediction decreases merit but finite remainder reverses it, propose experimental safeguarded work-merit backtracking within original20/8 and adaptive4/96, preserving target/history/acceptance and fixed default. Root adoption required; no sign repair or increased backtrack/depth.')
    write(DOC/'MERIT_SAVED_OBSERVATION.json',report);return report
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');parser.add_argument('--analyze',action='store_true');args=parser.parse_args()
    if args.prepare:prepare()
    elif args.analyze:analyze()
    else:parser.error('choose prepared source-only input extraction or separately authorised saved-data analysis')
