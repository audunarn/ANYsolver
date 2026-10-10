"""Root-callable static V8 preflight; does not import scientific libraries."""
import argparse,ast,hashlib,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/agent_plans/development/r8-b2-assembly-series-20261010/execution-v8'
RUNNER=ROOT/'scripts/r8_b2_assembly_series_v8_dev.py'

def require(ok,message):
    if not ok:raise RuntimeError(message)

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())

def runner():
    spec=importlib.util.spec_from_file_location('v8_preflight_runner',RUNNER)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def verify_manifest(path):
    entries=read(path)['files']
    for name,value in entries.items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts,'unsafe selected path')
        target=ROOT/name;expected=value['sha256'] if isinstance(value,dict) else value
        require(sha(target)==expected,'selected evidence drift: '+name)
        if isinstance(value,dict):require(target.stat().st_size==value['bytes'],'selected byte size drift: '+name)
    return len(entries)

def check():
    m=runner();p=read(OUT/'EXECUTABLE_PREPARED.json');selection=read(OUT/'SELECTED_PATHS.json')
    require(p['status']=='EXECUTABLE_DEVELOPMENT_SCREEN' and not (OUT/'SERIES_LEDGER.json').exists(),'unconsumed executable preparation required')
    selected=verify_manifest(OUT/'SELECTED_PATHS.json')
    require(selection['prepared_sha256']==sha(OUT/'EXECUTABLE_PREPARED.json'),'selection/executable identity')
    require(all(sha(ROOT/n)==h for n,h in p['source'].items()),'source/input drift')
    a=read(OUT/'ROOT_DEVELOPMENT_AUTHORITY.json');m.authority_gate(a,p,'controls',require_slot=False)
    require(a.get('slot_status')=='NOT_TRANSFERRED','original frozen grant must remain untransferred')
    m.immutable_inputs(p);caller=m.public_caller_contract(p)
    require(caller==p['caller_contract'],'actual frozen-wheel caller/signature drift')
    require(not Path(p['package_site']).exists(),'fresh candidate site already exists')
    for path in (p['solver_wheel'],p['consumer_wheel']):require(Path(path).is_file(),'wheel missing')
    for n,h in p['solver_package'].items():
        if n.endswith('.py'):require(sha(ROOT/'src'/n)==h,'candidate source-to-wheel mismatch: '+n)
    previous=m.PREVIOUS;life=m.LIFETIME
    for name,h in p['historical_v6'].items():require(sha(previous/name)==h,'V6 reference drift')
    for name,h in p['verified_lifetime'].items():require(sha(life/name)==h,'lifetime reference drift')
    for name,h in p['historical_v7'].items():require(sha(m.BASE/'execution-v7'/name)==h,'V7 immutable failure reference drift')
    require(read(m.BASE/'execution-v7/SERIES_LEDGER.json')['status']=='CLOSED','V7 ledger must remain closed')
    prior=read(previous/'SERIES_LEDGER.json');repair=read(life/'ledger.json')
    require(prior['status']==repair['status']=='CLOSED' and prior['unused_discarded'] and repair['unused_discarded'],'closed predecessor/repair ledgers required')
    require(read(previous/'EXECUTION_HANDOFF.json')['status']=='PARTIAL_SCREEN_TERMINAL_RESOURCE_FAILURE','V6 failed scope preserved')
    require(read(life/'HANDOFF.json')['controls']==dict(source=48,installed=48,skipped=0),'verified repaired-candidate small controls')
    manifests={'V6':verify_manifest(previous/'EXECUTION_SELECTED_PATHS.json'),'lifetime':verify_manifest(life/'SELECTED_PATHS.json')}
    tests=ast.parse((ROOT/'tests/test_r8_b2_assembly_series_v8_dev.py').read_text());nodes=[c.name+'.'+n.name for c in tests.body if isinstance(c,ast.ClassDef) for n in c.body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
    require(len(nodes)==len(set(nodes))==p['expected_controls']==20,'exact20 control inventory')
    tree=ast.parse(RUNNER.read_text());functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    require(len(functions)==sum(isinstance(n,ast.FunctionDef) for n in tree.body),'duplicate effective definitions')
    for caller_name,callee in (('run','_supervised_run'),('child','_execute_child_body'),('_execute_child_body','adjudicate_controls'),('authority_gate','_contract_authority_gate')):
        require(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id==callee for n in ast.walk(functions[caller_name])),'effective caller drift')
    patterns=[k.value.value for n in ast.walk(functions['_execute_child_body']) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='discover' for k in n.keywords if k.arg=='pattern']
    require(patterns==['test_r8_b2_assembly_series_v8_dev.py'],'production control selector drift')
    require(m.PHASES==('controls','install','validate-install','public-smoke','low','middle','full-1','full-2','full-3'),'fixed serial phase inventory')
    require('gc' not in {n.id for n in ast.walk(functions['installed_samples']) if isinstance(n,ast.Name)},'no GC warm shortcut')
    return dict(status='SUPPORTING_STATIC_PREFLIGHT_PASS',selected_files=selected,source_bindings=len(p['source']),prepared_sha256=sha(OUT/'EXECUTABLE_PREPARED.json'),selection_sha256=sha(OUT/'SELECTED_PATHS.json'),grant_sha256=sha(OUT/'ROOT_DEVELOPMENT_AUTHORITY.json'),controls_prepared=20,controls_executed=0,models_executed=0,phase_inventory=m.PHASES,prior_manifests=manifests,prior_ledgers_closed=True,root_callable_source_sha256=sha(__file__),question=p['question'],independent_review='MISTRAL_PENDING')

def transfer(report,expected_self_sha):
    require(expected_self_sha==sha(__file__),'root-reviewed preflight SHA required')
    pre=OUT/'ROOT_PREFLIGHT.json';live=OUT/'ROOT_EXECUTION_AUTHORITY.json'
    require(not pre.exists() and not live.exists(),'root records already exist, no overwrite')
    grant=read(OUT/'ROOT_DEVELOPMENT_AUTHORITY.json');m=runner()
    with pre.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2,sort_keys=True);f.write('\n')
    a=dict(grant,slot_status='TRANSFERRED',executable_prepared_sha256=sha(OUT/'EXECUTABLE_PREPARED.json'),root_preflight_sha256=sha(pre))
    require(m.authority_contract_sha(a)==m.authority_contract_sha(grant),'transfer changes stable contract')
    with live.open('x',encoding='utf-8') as f:json.dump(a,f,indent=2,sort_keys=True);f.write('\n')
    return sha(live)

if __name__=='__main__':
    q=argparse.ArgumentParser();q.add_argument('--check-only',action='store_true');q.add_argument('--transfer-slot',action='store_true',help='ROOT ONLY after exclusive numerical-slot transfer');q.add_argument('--expected-preflight-sha256');a=q.parse_args();require(a.check_only != a.transfer_slot,'choose exactly one root action');report=check()
    if a.transfer_slot:report['new_execution_authority_sha256']=transfer(report,a.expected_preflight_sha256)
    print(json.dumps(report,indent=2,sort_keys=True))
