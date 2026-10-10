"""Root-callable static B2 v5 preflight; never imports numerical/installed code.

Only root may invoke --transfer-slot after explicitly transferring the sole slot.
Existing frozen manifests/grants are read only. New root records use exclusive
creation; --check-only cannot create execution authority or a scientific ledger.
"""
import argparse
import ast
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs/agent_plans/development/r8-b2-assembly-series-20261010'
OUT=BASE/'execution-v5'
PREPARED_SHA='a1ab90c5d1e3eb1ec927dc6bf2e25f84e54c43d7c3a563f8d20af57c59d7680a'
SELECTION_SHA='ff6ba34fd23bbe39580e69ebf509f727dafe782f8b30b05cb11d18cc00a78c38'
GRANT_SHA='bd0beb040647db769d838f2d5c42be6bf8d942e649225a969db3931a7a63bdf3'
MARKERS=('slot_status','ready_sha256','executable_prepared_sha256','root_preflight_sha256')
PHASES=('controls','install','validate-install','public-smoke','low','middle','full-1','full-2','full-3')

def require(ok,reason):
    if not ok:raise RuntimeError(reason)

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def workspace_path(name):
    require(type(name) is str and not Path(name).is_absolute() and '..' not in Path(name).parts,'unsafe manifest path')
    require('us3-modal-canary' not in name.casefold(),'protected canary path refused')
    path=ROOT/name;require(path.resolve().is_relative_to(ROOT),'manifest path outside worktree')
    return path

def check_manifest(path,expected_sha,expected_count):
    require(sha(path)==expected_sha,'manifest identity drift: '+str(path))
    m=read(path);require(len(m['files'])==expected_count,'manifest count drift')
    for n,item in m['files'].items():
        p=workspace_path(n);require(p.stat().st_size==item['bytes'] and sha(p)==item['sha256'],'manifest member drift: '+n)
    return dict(path=str(path.relative_to(ROOT)),sha256=expected_sha,files=expected_count)

def check_closed(path):
    ledger=read(path);require(ledger['status']=='CLOSED' and ledger['unused_discarded'] is True,'prior ledger not terminal/discarded')
    walls=[]
    for item in ledger['attempts']:
        wall=item['receipt']['elapsed_seconds'];require(type(wall) in (int,float) and math.isfinite(wall) and wall>=0.,'invalid process-wall evidence');walls.append(wall)
    require(sum(walls)==ledger['used_seconds'],'ledger/process-wall sum mismatch')
    require(ledger['unused_seconds']==3200.-ledger['used_seconds'],'ledger discarded remainder mismatch')
    return dict(path=str(path.relative_to(ROOT)),sha256=sha(path),used_seconds=ledger['used_seconds'],unused_discarded_seconds=ledger['unused_seconds'],status='CLOSED')

def check():
    current=check_manifest(OUT/'SELECTED_PATHS.json',SELECTION_SHA,9)
    require(sha(OUT/'EXECUTABLE_PREPARED.json')==PREPARED_SHA and sha(OUT/'ROOT_DEVELOPMENT_AUTHORITY.json')==GRANT_SHA,'v5 input/grant identity drift')
    p=read(OUT/'EXECUTABLE_PREPARED.json');grant=read(OUT/'ROOT_DEVELOPMENT_AUTHORITY.json')
    require(grant['slot_status']=='NOT_TRANSFERRED','original grant must remain frozen NOT_TRANSFERRED')
    require((grant['cumulative_seconds'],grant['reserve_seconds'],grant['process_cap_seconds'],grant['controls_cap_seconds'],grant['install_cap_seconds'],grant['tree_rss_limit_bytes'])==(3200,120,600,30,30,2147483648),'resource contract drift')
    require(grant['cpu_affinity']==[0] and grant['numerical_threads']==1 and grant['jit_disabled'] is True and grant['python_optimize']==0 and grant['one_numerical_job'] is True,'runtime contract drift')
    require(len(p['source'])==19,'source count drift')
    for n,h in p['source'].items():require(sha(workspace_path(n))==h,'prepared source drift: '+n)
    tests=ast.parse((ROOT/'tests/test_r8_b2_assembly_series_v5_dev.py').read_text())
    nodes=[c.name+'.'+n.name for c in tests.body if isinstance(c,ast.ClassDef) for n in c.body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
    require(len(nodes)==len(set(nodes))==20 and p['expected_controls']==20,'exact20 AST inventory drift')
    runner=ast.parse((ROOT/'scripts/r8_b2_assembly_series_v5_dev.py').read_text())
    phases=next(n.value for n in runner.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PHASES' for t in n.targets))
    require(ast.literal_eval(phases)==PHASES,'actual phase ordering drift')
    require(p['public_smoke']==dict(shells=3,members=3,pads=1,rows=20,dofs=72,fixed_dofs=12,loaded_dof=20,selected_dofs=[20,18],pad='pad-0-1',member='b2-0-0'),'actual smoke inventory drift')
    for field in ('solver_wheel','consumer_wheel'):require(sha(p[field])==p[field.replace('_wheel','_sha256')],'frozen wheel drift')
    require(sha(p['full_fixture']['path'])==p['full_fixture']['sha256'],'full fixture drift')
    gui=p['launcher_provenance']['gui_executable'];require(gui==grant['gui_interpreter'] and Path(gui['path']).is_file() and sha(gui['path'])==gui['sha256'],'GUI sibling drift')
    historical=[check_manifest(workspace_path(n),v['sha256'],v['files']) for n,v in read(OUT/'HISTORICAL_BINDINGS.json')['manifests'].items()]
    ledgers=[check_closed(base/'SERIES_LEDGER.json') for base in (BASE,BASE/'execution-v2',BASE/'execution-v3',BASE/'execution-v4')]
    v3=BASE/'execution-v3';handoff=read(v3/'EXECUTION_HANDOFF.json');terminal=read(v3/'EXECUTION_TERMINAL_TREE.json')
    require(all(handoff[n]==0 for n in ('owner_constructions','assembly_samples','factors','primaries','corrections')),'v3 zero-owner/counter evidence drift')
    require(handoff['ledger']==read(v3/'SERIES_LEDGER.json'),'v3 handoff ledger mismatch')
    observed=sorted({pid for a in handoff['ledger']['attempts'] for pid in a['receipt']['observed_pids']})
    require(sorted(terminal['observed_pids'])==observed and terminal['terminal'] is True and terminal['alive_pids']==[],'saved v3 terminal PID evidence mismatch')
    require(handoff['controls']==dict(errors=0,executed=20,failures=0,skips=0,status='PASS_CONTROLS') and handoff['validation']['status']=='PASS_REUSED_INSTALL_VALIDATION','v3 controls/validation evidence mismatch')
    site=Path(p['package_site']).resolve()
    require(grant['reuse_install'] is False and site==Path(grant['package_site']).resolve()==(OUT/'package/site').resolve() and not site.exists(),'fresh isolated target must not exist')
    require(p['installation']==dict(fresh=True,no_compile=True,no_deps=True,no_index=True,bytecode_disabled=True),'installation policy drift')
    functions={n.name:n for n in runner.body if isinstance(n,ast.FunctionDef)}
    require(len(functions)==sum(isinstance(n,ast.FunctionDef) for n in runner.body),'duplicate effective functions')
    flags=[n.value for n in ast.walk(functions['install_fresh']) if isinstance(n,ast.Constant) and type(n.value) is str]
    require(all(x in flags for x in ('--no-deps','--no-compile','--no-index','--target')),'installer flags missing')
    for caller,callee in (('run','_supervised_run'),('child','_execute_child_body'),('_execute_child_body','adjudicate_controls'),('install_fresh','fresh_site'),('install_fresh','pip_main'),('basic_runtime','bytecode_guard'),('public_runtime','bytecode_guard')):
        require(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id==callee for n in ast.walk(functions[caller])),'effective caller missing '+caller+' to '+callee)
    require(sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='verify_site' for n in ast.walk(functions['installed_samples']))==2,'pre/post-close strict validation missing')
    proof=p['launcher_provenance']
    require(sha(proof['template_source_path'])==proof['template_source_sha256'] and sha(proof['alternate_source']['path'])==proof['alternate_source']['sha256'],'installer source drift')
    for item in proof['resources'].values():require(sha(item['path'])==item['sha256'],'PE resource drift')
    v4=BASE/'execution-v4';prior=read(v4/'EXECUTION_HANDOFF.json');tree=read(v4/'EXECUTION_TERMINAL_TREE.json')
    require(all(prior[n]==0 for n in ('owners','factors','primaries','corrections','public_smokes_executed')),'v4 zero-owner evidence drift')
    require(prior['ledger']==read(v4/'SERIES_LEDGER.json'),'v4 ledger mismatch')
    v4pids=sorted({pid for item in prior['ledger']['attempts'] for pid in item['receipt']['observed_pids']})
    require(sorted(tree['observed_pids'])==v4pids and tree['terminal'] is True and tree['alive_pids']==[],'v4 saved PID evidence mismatch')
    oldsite=Path(read(v4/'EXECUTABLE_PREPARED.json')['package_site']).resolve()
    expected=read(v3/'attempt-validate-install-01/installed-inventory.json')['files'];diagnosis=read(v4/'EXECUTION_INSTALL_DIAGNOSIS.json')
    require(len(expected)==761 and len(diagnosis['extras'])==321 and diagnosis['missing']==diagnosis['changed']==[] and diagnosis['caches_accepted'] is False,'v4 diagnosis drift')
    oldfiles=dict(expected);oldfiles.update({n:item['sha256'] for n,item in diagnosis['extras'].items()});actual=set()
    for path in oldsite.rglob('*'):
        require(not path.is_symlink() and not getattr(path,'is_junction',lambda:False)(),'old site reparse refused')
        if path.is_file():actual.add(path.relative_to(oldsite).as_posix())
    require(actual==set(oldfiles) and len(actual)==1082,'old site evidence namespace drift')
    for n,h in oldfiles.items():require('..' not in Path(n).parts and (oldsite/n).resolve().is_relative_to(oldsite) and sha(oldsite/n)==h,'old site evidence drift: '+n)
    require(not (OUT/'SERIES_LEDGER.json').exists(),'v5 already consumed')
    return dict(status='SUPPORTING_STATIC_PREFLIGHT_PASS',prepared_sha256=PREPARED_SHA,selection_sha256=SELECTION_SHA,grant_sha256=GRANT_SHA,selected_files=9,source_bindings=19,controls_prepared=20,controls_executed=0,public_smokes_executed=0,phases=PHASES,historical_manifests=historical,prior_ledgers=ledgers,v3_observed_terminal_pids=observed,v3_owners_factors_solves=0,v4_observed_terminal_pids=v4pids,v4_owners_factors_solves=0,old_site_evidence_files_preserved=1082,fresh_site=str(site),installation_executed=0,root_callable_source_sha256=sha(__file__),independent_review='MISTRAL_PENDING',scope='Static hash/AST/saved-evidence inspection only; not installed validation replay or numerical qualification.')

def create_execution_authority(report,expected_self_sha):
    require(expected_self_sha==sha(__file__),'root-reviewed preflight source SHA required')
    authority_path=OUT/'ROOT_EXECUTION_AUTHORITY.json';preflight_path=OUT/'ROOT_PREFLIGHT.json'
    require(not authority_path.exists() and not preflight_path.exists(),'new root records already exist; no overwrite')
    grant=read(OUT/'ROOT_DEVELOPMENT_AUTHORITY.json')
    with preflight_path.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2,sort_keys=True);f.write('\n')
    authority=dict(grant,slot_status='TRANSFERRED',executable_prepared_sha256=PREPARED_SHA,root_preflight_sha256=sha(preflight_path))
    stable=lambda a:json.dumps({k:v for k,v in a.items() if k not in MARKERS},sort_keys=True,separators=(',',':'),allow_nan=False)
    require(stable(authority)==stable(grant),'transfer changes stable grant contract')
    with authority_path.open('x',encoding='utf-8') as f:json.dump(authority,f,indent=2,sort_keys=True);f.write('\n')
    return sha(authority_path)

if __name__=='__main__':
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check-only',action='store_true');group.add_argument('--transfer-slot',action='store_true',help='ROOT ONLY: invoke only after explicit exclusive slot transfer')
    parser.add_argument('--expected-preflight-sha256');args=parser.parse_args();report=check()
    if args.transfer_slot:report['new_execution_authority_sha256']=create_execution_authority(report,args.expected_preflight_sha256)
    print(json.dumps(report,indent=2,sort_keys=True))
