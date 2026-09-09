"""Source/evidence authority and closed lifecycle inventory; standard library."""
from hashlib import sha256
from pathlib import Path
from docs.reference_cases.ge_beam3_retained_prestress_protocol import canonical,strict_bytes,read,bind,bound,digest
from docs.reference_cases.ge_beam3_fine_upper_protocol import receipt
from docs.reference_cases.ge_beam3_plastic_arc_fixture import fixture

ROOT=Path(__file__).resolve().parents[2]
ARCHIVE=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-plastic-arc-smoke-334d872-20260909')
STATUS_SHA='54d334c0f2f626d69d9bd3f926792e479971484f311e4b8d7ed8520135cd4476'
MANIFEST_SHA='6f329cfcd4e9422c9863edc1912d2a1298b69ace599977b050fb659025595002'
MODES=('full','prefix','resume','capture','check','cancel-assembly','cancel-trial','cancel-commit','mutations')
INPUTS={'full':set(),'prefix':{'full'},'resume':{'prefix','full'},'capture':{'full'},'check':{'full','capture'},
    'cancel-assembly':{'prefix','full'},'cancel-trial':{'prefix','full'},'cancel-commit':{'prefix','full'},'mutations':{'full'}}
MUTATIONS=('origins','histories','accumulated','predictor','program','work','recovery','cursor','predecessor','record','external-hash','duplicate','nonfinite')

def authority():
    raw=read(ROOT/'docs/reference_cases/ge_beam3_plastic_arc_smoke_status.json')
    if sha256(raw).hexdigest()!=STATUS_SHA:raise ValueError('smoke status authority')
    status=strict_bytes(raw)
    if status['terminal']!='PRIVATE_ACTIVE_PLASTIC_ARC_MATERIAL_SMOKE_PASS' or status['production_qualified'] is not False:
        raise ValueError('accepted private smoke required')
    raw=read(ARCHIVE/'archive-manifest.json')
    if sha256(raw).hexdigest()!=MANIFEST_SHA:raise ValueError('smoke archive authority')
    manifest=strict_bytes(raw)
    for name in ('runs/aggregate.json','runs/full/output/checkpoint.json','runs/capture/output/capture.json'):
        raw=read(ARCHIVE/name)
        if manifest[name]!=[len(raw),sha256(raw).hexdigest().upper()]:raise ValueError('smoke scientific binding')
    if sha256(canonical(fixture(1))).hexdigest()!=status['fixture_sha256']:raise ValueError('unchanged one-macro fixture')
    return dict(smoke_status_sha256=STATUS_SHA,archive_manifest_sha256=MANIFEST_SHA,
        one_macro_checkpoint_sha256=status['checkpoint'][1].lower(),fixtures={str(n):sha256(canonical(fixture(n))).hexdigest() for n in (1,2)})

def request(v):
    if type(v) is not dict or set(v)!={'schema','revision','macros','mode','inputs'} or v['schema']!='GE_BEAM3_PLASTIC_ARC_LIFECYCLE_REQUEST_V1':
        raise ValueError('exact lifecycle request')
    digest(v['revision'],40)
    if type(v['macros']) is not int or v['macros'] not in (1,2) or type(v['mode']) is not str or v['mode'] not in MODES:
        raise ValueError('registered lifecycle case')
    if type(v['inputs']) is not dict or set(v['inputs'])!=INPUTS[v['mode']]:raise ValueError('exact preceding inputs')
    return {k:bound(b) for k,b in v['inputs'].items()}

def validate_report(report,revision,n,mode,full_sha,prefix_sha):
    if type(report) is not dict or set(report)!={'schema','revision','macros','mode','checkpoint_sha256','reference_full_sha256','checks','production_qualified'}:
        raise ValueError('exact lifecycle report')
    if (report['schema']!='GE_BEAM3_PLASTIC_ARC_LIFECYCLE_REPORT_V1' or report['revision']!=revision
            or type(report['macros']) is not int or report['macros']!=n or report['mode']!=mode or report['production_qualified'] is not False):
        raise ValueError('lifecycle report identity')
    expected=prefix_sha if mode=='prefix' or mode.startswith('cancel-') else full_sha
    if report['checkpoint_sha256']!=expected or report['reference_full_sha256']!=full_sha:raise ValueError('actual checkpoint consistency')
    checks=report['checks']
    required={'full':{'full_completed'},'prefix':{'paused_after_plastic_step'},'resume':{'resumed_equals_full'},
        'capture':{'original_histories_replayed'},'check':{'all_stations_independently_checked'},
        'cancel-assembly':{'injection_reached','preceding_checkpoint_preserved','resumed_equals_full'},
        'cancel-trial':{'injection_reached','preceding_checkpoint_preserved','resumed_equals_full'},
        'cancel-commit':{'injection_reached','preceding_checkpoint_preserved','resumed_equals_full'},
        'mutations':set(MUTATIONS)}[mode]
    if type(checks) is not dict or set(checks)!=required or any(v is not True for v in checks.values()):
        raise ValueError('complete actual lifecycle checks required')
    return report

def prior(phase,path,revision):
    if phase not in ('rehearsal','formal-a','formal-b'):raise ValueError('registered phase')
    if phase=='rehearsal':
        if path is not None:raise ValueError('rehearsal has no prior')
        return None
    if path is None:raise ValueError('accepted predecessor required')
    v=bound(bind(path))
    if (set(v)!={'schema','revision','phase','wave','aggregate','predecessor'} or v['schema']!='GE_BEAM3_PLASTIC_ARC_LIFECYCLE_ACCEPTANCE_V1'
            or v['revision']!=revision or v['phase']!=('rehearsal' if phase=='formal-a' else 'formal-a')):
        raise ValueError('predecessor phase authority')
    wave=bound(v['wave']);agg=bound(v['aggregate'])
    if wave['success'] is not True or wave['all_children_terminal'] is not True or len(wave['receipts'])!=19 or not 0<wave['elapsed']<1800:
        raise ValueError('complete bounded predecessor required')
    if agg['revision']!=revision or agg['terminal']!='PRIVATE_ACTIVE_PLASTIC_ARC_LIFECYCLE_PASS' or agg['production_qualified'] is not False:
        raise ValueError('accepted predecessor science')
    for r in wave['receipts'].values():receipt(r)
    validate_wave(wave,agg,revision)
    if v['phase']=='formal-a':
        bound(v['predecessor']);prior('formal-a',v['predecessor']['path'],revision)
    elif v['predecessor'] is not None:raise ValueError('rehearsal predecessor must be absent')
    return v

def validate_wave(wave,aggregate,revision):
    if (set(aggregate)!={'schema','revision','authority','cases','terminal','independent_review','production_qualified'}
            or aggregate['schema']!='GE_BEAM3_PLASTIC_ARC_LIFECYCLE_AGGREGATE_V1' or aggregate['revision']!=revision
            or aggregate['terminal']!='PRIVATE_ACTIVE_PLASTIC_ARC_LIFECYCLE_PASS'
            or aggregate['independent_review']!='PENDING' or aggregate['production_qualified'] is not False):
        raise ValueError('exact aggregate scope')
    if set(wave['cases'])!={'1','2'} or aggregate['authority']!=authority():raise ValueError('full two-case authority')
    reports=[]
    for n in (1,2):
        case=wave['cases'][str(n)];full=case['full'];prefix=case['prefix']
        bound(full);bound(prefix);capture=bound(case['capture']);material=bound(case['material'])
        if n==1 and full['sha256']!=authority()['one_macro_checkpoint_sha256']:raise ValueError('unchanged smoke checkpoint')
        if (capture['checkpoint_sha256']!=full['sha256'] or capture['fixture']!=fixture(n)
                or material['checkpoint_sha256']!=full['sha256'] or material['fixture_sha256']!=authority()['fixtures'][str(n)]
                or material['production_qualified'] is not False or material['restart_cancellation_qualified'] is not False
                or material['revision']!=revision or material['macros']!=n or material['terminal']!='PRIVATE_ACTIVE_PLASTIC_ARC_MATERIAL_SMOKE_PASS'
                or len(material['steps'])!=3 or any(r['stations']!=8*n or r['active_stations']<=0 for r in material['steps'])):
            raise ValueError('complete independent material coverage')
        if set(case['reports'])!=set(MODES) or set(case['requests'])!=set(MODES):raise ValueError('complete lifecycle inventory')
        rows=[]
        for mode in MODES:
            r=bound(case['requests'][mode]);request(r)
            if (r['revision'],r['macros'],r['mode'])!=(revision,n,mode):raise ValueError('original request identity')
            expected={'full':full,'prefix':prefix,'capture':case['capture']}
            for key,b in r['inputs'].items():
                if b!=expected[key]:raise ValueError('original predecessor mismatch')
            receipt(wave['receipts'][f'n{n}/{mode}'])
            rows.append(validate_report(bound(case['reports'][mode]),revision,n,mode,full['sha256'],prefix['sha256']))
        reports.append(dict(macros=n,full_sha256=full['sha256'],prefix_sha256=prefix['sha256'],
            capture_sha256=case['capture']['sha256'],material=material,reports=rows))
    if aggregate['cases']!=reports:raise ValueError('canonical lifecycle assembly')
    return reports
