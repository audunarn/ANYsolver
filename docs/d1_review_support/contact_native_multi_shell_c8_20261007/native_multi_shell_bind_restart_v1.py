"""Stdlib-only authentic native/multiple-S3 restart artifact binder.

Never imports/executes solver, numerical libraries or runner. Prefix binding
precedes resumed dispatch; final binding precedes saved-record verification.
Inputs must be successful complete future guarded public producer jobs.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import zipfile

RAW=Path('C:/ANYworkspaceWork/contact_native_multi_shell_c8_20261007')
REPO=Path('C:/ANYworkspaceWork/ANYsolver-contact-main-reconcile-20261001')
SCOPE='C8_NATIVE_MULTI_SHELL_DEV'
BASIS='MEASURED_WRAPPER_WALL_CONSERVATIVE_WITH_PRECISE_CHILD_LAUNCH_TO_WAIT'
SOURCE_CHECKPOINT='6362bdfb'
PROFILE='NATIVE_MULTI_B3_GE_S3_TRAJECTORY_DEV_V1'
NATIVE_PROFILE='NATIVE_MULTI_B3_GE_S3_SMALL_MOTION_DESCRIPTOR_MIDPOINT_DEV_V1'
TRAJECTORY_SCHEMA='NATIVE_MULTI_B3_GE_S3_TRAJECTORY_CHECKPOINT_DEV_V1'
RUNTIME=dict(PYTHONDONTWRITEBYTECODE='1',PYTHONHASHSEED='0',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
 NUMBA_DISABLE_JIT='1',NUMBA_NUM_THREADS='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',
 MKL_NUM_THREADS='1',BLIS_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',PIP_NO_INDEX='1')


def require(ok,message):
    if not ok:raise ValueError(message)
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def canonical(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode('ascii')
def sha(value):return hashlib.sha256(canonical(value)).hexdigest()
def inside(path,root=RAW):
    path=Path(path).resolve();require(path.is_relative_to(root.resolve()),'path outside explicit root: '+str(path));return path

def read(path):
    def pairs(items):
        out={}
        for key,value in items:require(key not in out,'duplicate JSON field');out[key]=value
        return out
    def invalid(value):raise ValueError('nonfinite JSON value: '+value)
    path=Path(path);require(path.is_file() and path.stat().st_size<=16*1024**2,'missing/oversized evidence: '+str(path))
    return json.loads(path.read_text(encoding='utf-8-sig'),object_pairs_hook=pairs,parse_constant=invalid)

def finite(value):return type(value) in (int,float) and math.isfinite(value)
def validate_manifest(path):
    path=inside(path);m=read(path)
    require(m['scope']==SCOPE and finite(m['approved_seconds']) and m['approved_seconds']>0,'new explicit scope authority required')
    require((m['maximum_job_seconds'],m['memory_limit_mib'],m['reserve_seconds'])==(60,953,60),'resource controls changed')
    require(m.get('concurrent_jobs',1)==1 and m['accounting_basis']==BASIS,'serial measured accounting required')
    authority=inside(RAW/m['authority_file']);grant=read(authority)
    require(digest(authority)==m['authority_sha256'],'authority hash mismatch')
    required=dict(scope=SCOPE,status='USER_AUTHORIZED',approved_seconds=m['approved_seconds'],maximum_job_seconds=60,
                  memory_limit_mib=953,concurrent_jobs=1,reserve_seconds=60,accounting_basis=BASIS)
    require(all(grant.get(k)==v for k,v in required.items()),'exact immutable grant mismatch')
    runner=inside(RAW/m['runner_file']);require(digest(runner)==m['runner_sha256'],'runner identity mismatch')
    require(digest(m['python_executable'])==m['python_sha256'],'Python identity mismatch')
    for root,hashes,sizes in ((REPO,m['held_files'],m['held_sizes']),(inside(RAW/m['build_tree']),m['build_files'],m['build_sizes'])):
        for name,value in hashes.items():
            p=inside(root/name,root);require(p.stat().st_size==sizes[name] and digest(p)==value,'frozen source/build mismatch: '+name)
    for name,value in m['raw_inputs'].items():
        p=Path(name);require(p.stat().st_size==m['raw_sizes'][name] and digest(p)==value,'raw binding mismatch: '+name)
    return m,authority,runner

def payload(m):
    identity_path=inside(RAW/m['wheel_identity_file']);identity=read(identity_path)
    site=inside(RAW/m['site_directory']);wheel=inside(identity['wheel'])
    require(digest(wheel)==identity['wheel_sha256'],'wheel changed')
    with zipfile.ZipFile(wheel) as archive:
        files={n:hashlib.sha256(archive.read(n)).hexdigest() for n in archive.namelist() if n.startswith('anysolver/') and not n.endswith('/')}
        metadata={n:hashlib.sha256(archive.read(n)).hexdigest() for n in archive.namelist() if '.dist-info/' in n and not n.endswith('/')}
    require(files==identity['files'] and metadata==identity['metadata'],'wheel identity/payload/metadata mismatch')
    for name,value in m['build_files'].items():
        if name.startswith('src/anysolver/'):require(files.get(name[4:])==value,'wheel/source mismatch: '+name)
    for name,value in files.items():require(digest(inside(site/name,site))==value,'installed payload mismatch: '+name)
    for name,value in metadata.items():
        if not name.endswith('/RECORD'):require(digest(inside(site/name,site))==value,'installed wheel metadata mismatch: '+name)
    return identity_path,identity,site,wheel

def runtime(path,stage,site,identity):
    row=read(path)
    require(row['stage']==stage and row['errors']==[] and row['jit_disabled'] is True and row['numba_threads']==1
            and row['plugin_autoload_disabled'] is True,'effective runtime failure: '+stage)
    require(row['pools'] and all(p['num_threads']==1 for p in row['pools']),'observed pools must all be one')
    modules=row['modules'];require(modules,'missing private imported modules')
    for name,entry in modules.items():
        p=inside(entry['path'],site/'anysolver');relative='anysolver/'+p.relative_to((site/'anysolver').resolve()).as_posix()
        require(entry['wheel_relative']==relative and entry['sha256']==identity['files'].get(relative)==digest(p),'private import mismatch: '+name)
    for name,entry in row['dependencies'].items():require(digest(entry['path'])==entry['sha256'],'dependency drift: '+name)
    for name in ('anysolver','anysolver._ge_beam3_native_multi_shell_contact','anysolver.general_contact.native_transient_multi_shell'):
        require(name in modules,'new installed route absent: '+name)
    return row

def compatible(base,other):
    # raw_inputs/restart environment grow prospectively. All scientific, resource,
    # source/build/install and producer-group controls must remain unchanged.
    for key in ('scope','approved_seconds','authority_file','authority_sha256','runner_file','runner_sha256',
                'python_executable','python_sha256','candidate','maximum_job_seconds','memory_limit_mib','reserve_seconds',
                'accounting_basis','held_files','held_sizes','build_tree','build_files','build_sizes',
                'dist_directory','site_directory','wheel_identity_file','response_reference_force_n','response_reference_moment_nm'):
        require(base.get(key)==other.get(key),'producer source/install/controls mismatch: '+key)
    for key,value in base['groups'].items():
        if key!='RESTART_VERIFY':require(other['groups'].get(key)==value,'producer group changed: '+key)
    require(base['groups']['RESTART_VERIFY']['mode']==other['groups']['RESTART_VERIFY']['mode']=='TEST'
            and base['groups']['RESTART_VERIFY']['selectors']==other['groups']['RESTART_VERIFY']['selectors']
            and base['groups']['RESTART_VERIFY']['cap_seconds']==other['groups']['RESTART_VERIFY']['cap_seconds'],
            'restart verification criterion changed')

def shape_state(state,analysis):
    require(state['identity']==analysis,'state analysis identity mismatch')
    for name,length in (('positions',12),('position_low',12),('nodal_frames',12),('cell_rotations',4),
                        ('resultants',4),('velocity',210),('acceleration',210),('shell_displacement',42),('histories',4)):
        require(type(state[name]) is list and len(state[name])==length,'complete210 field coverage: '+name)
    require(all(len(row)==3 for row in state['positions']+state['position_low']),'position dimensions')
    require(all(len(row)==18 for row in state['resultants']),'exact retained18 resultants')

def records(result,capsule,count):
    require(result['status']=='completed' and result['profile']==PROFILE and result['contact']=='GLOBAL_NATIVE_MULTIPLE_S3_INTERIOR_CONTRIBUTORS'
            and result['production_qualified'] is False,'actual profile/status mismatch')
    body=capsule['body'];require(capsule['checkpoint_sha256']==sha(body),'trajectory checksum mismatch')
    require(body['schema']==TRAJECTORY_SCHEMA and body['production_qualified'] is False,'trajectory schema/claim mismatch')
    contract=body['contract'];settings=contract['settings'];analysis=contract['analysis_sha256']
    require(body['identity']==result['identity']==sha(contract),'actual trajectory identity mismatch')
    require(settings['profile']==PROFILE and settings['dt']==.003 and settings['max_steps']==64 and settings['max_cutbacks']==8
            and settings['minimum_dt']==.003/256 and settings['save_every']==1,'exact producer fixture settings required')
    require(len(contract['initial_velocity_physical'])==len(contract['initial_displacement_physical'])==81,'physical81 initial contract')
    controller=body['controller'];require(result['accepted_steps']==controller['accepted_steps']==count
        and result['accepted_time']==controller['time']==count*.003 and len(result['steps'])==count,'accepted producer count/time mismatch')
    require(controller['initial']==result['initial'] and controller['steps']==result['steps'] and controller['outputs']==result['outputs'],
            'result/controller correspondence mismatch')
    previous=result['initial'];require(previous['epoch']==0 and previous['time']==0.,'genesis mismatch')
    shape_state(previous['state'],analysis);require(previous['state_sha256']==sha(previous['state']),'genesis state digest')
    for index,step in enumerate(result['steps'],1):
        require(step['index']==index and step['predecessor_sha256']==previous['state_sha256'],'accepted prefix chain mismatch')
        require(step['start_time']==previous['time'] and step['end_time']==index*.003 and step['dt']==.003,'accepted fixed timestep mismatch')
        require(step['stage_residual_norm']<=1e-11 and step['endpoint_algebraic_norm']<=1e-11,'saved equilibrium gate failed')
        for name in ('stage','endpoint'):
            record=step[name];shape_state(record['state'],analysis)
            require(record['state_sha256']==sha(record['state']),'complete accepted state digest mismatch')
        previous=step['endpoint'];require(previous['epoch']==index and previous['time']==step['end_time'],'endpoint epoch/time mismatch')
    require(result['final']==previous,'final accepted endpoint correspondence')
    native_raw=body['native_checkpoint'].encode('ascii');native=read_json_bytes(native_raw)
    require(body['native_sha256']==hashlib.sha256(native_raw).hexdigest() and native['sha256']==sha(native['body']),'native capsule hash mismatch')
    require(native['body']['profile']==NATIVE_PROFILE and native['body']['identity']==analysis
            and native['body']['state']==previous['state'],'complete native capsule correspondence mismatch')
    return analysis,contract

def read_json_bytes(raw):
    value=json.loads(raw);require(canonical(value)==raw,'noncanonical native capsule');return value

def producer(label,path,base,identity,site,files):
    directory=inside(path);require(directory.name.startswith('nms8_'),'new-scope producer path required')
    inputs=read(directory/'inputs.json');resource=read(directory/'resource.json');outcome=read(directory/'child_outcome.json')
    command=inputs['command'];require(type(command) is list and len(command)==8 and command[4]=='--_child','exact guarded child command required')
    manifest_path=inside(command[5]);producer_manifest,authority,runner=validate_manifest(manifest_path);compatible(base,producer_manifest)
    group='RESTART_'+label.upper();require(inputs['scope']==SCOPE and inputs['mode']=='CLI' and inputs['group']==group and command[7]==group,'exact public producer group required')
    require(Path(command[0]).resolve()==Path(base['python_executable']).resolve() and command[1:3]==['-X','utf8'] and
            Path(command[3]).resolve()==runner and Path(command[6]).resolve()==directory and Path(inputs['cwd']).resolve()==REPO.resolve(),
            'producer command/path mismatch')
    require(inputs['manifest_sha256']==digest(manifest_path)==resource['manifest_sha256'] and inputs['runner_sha256']==base['runner_sha256']
            and inputs['authority_sha256']==base['authority_sha256'] and inputs['candidate']==base['candidate'],'producer dispatch identities mismatch')
    require(inputs['requested_runtime']==RUNTIME and inputs['memory_limit_mib']==953 and inputs['reserve_s']==60 and inputs['accounting_basis']==BASIS,'producer requested controls mismatch')
    require(resource['scope']==SCOPE and resource['status']=='completed' and resource['exit_code']==0 and resource['child_started'] is True
            and resource['accounting_complete'] is True and resource['ledger_error'] is None and resource['live_processes']==[],
            'unfinished/failed/unaccounted producer refused')
    require(resource['accounting_basis']==BASIS and resource['approved_seconds']==base['approved_seconds'] and resource['reserve_s']==60
            and resource['memory_limit_mib']==953 and resource['peak_tree_bytes']<=953*1024**2,'producer resource contract mismatch')
    for key in ('wrapper_wall_s','child_process_wall_s','tree_process_wall_s','charged_wall_s','total_spent_s','remaining_s'):
        require(finite(resource[key]) and resource[key]>=0,'missing/nonfinite measured duration: '+key)
    require(0<resource['child_process_wall_s']<=resource['tree_process_wall_s']<=resource['wrapper_wall_s']<=60
            and resource['charged_wall_s']==resource['wrapper_wall_s'],'precise child/wrapper accounting mismatch')
    require(resource['total_spent_s']==math.fsum((inputs['spent_before_s'],resource['charged_wall_s']))
            and resource['remaining_s']==base['approved_seconds']-resource['total_spent_s'] and resource['remaining_s']>=60,'cumulative/reserve mismatch')
    require(outcome['exit_code']==0 and outcome['runtime_errors']==[] and outcome['prepared_result_count']>=1,'complete child outcome required')
    pre=runtime(directory/'runtime_preflight.json','preflight',site,identity);post=runtime(directory/'runtime_final.json','final',site,identity)
    require(all(post['modules'].get(n)==v for n,v in pre['modules'].items()),'private runtime drift within producer')
    result_path=directory/'final.json';capsule_path=directory/'final.checkpoint';result=read(result_path);capsule=read(capsule_path)
    require(canonical(result)==result_path.read_bytes() and canonical(capsule)==capsule_path.read_bytes(),'canonical exported public artifacts required')
    count=1 if label=='prefix' else 2;analysis,contract=records(result,capsule,count)
    captures=list((directory/'prepared_results').glob('result_*.json'));require(len(captures)==outcome['prepared_result_count'],'prepared capture inventory incomplete')
    require(any(p.read_bytes()==result_path.read_bytes() and p.with_suffix('.checkpoint').is_file()
                and p.with_suffix('.checkpoint').read_bytes()==capsule_path.read_bytes() for p in captures),'exported final lacks authentic public-result capture')
    for p in (manifest_path,authority,runner,directory/'inputs.json',directory/'resource.json',directory/'child_outcome.json',
              directory/'runtime_preflight.json',directory/'runtime_final.json',directory/'process.json',directory/'stdout.log',directory/'stderr.log',result_path,capsule_path):
        files[str(p)]=digest(p)
    return dict(result=str(result_path),checkpoint=str(capsule_path),producer_manifest=str(manifest_path),
                producer_inputs=str(directory/'inputs.json'),resource=str(directory/'resource.json')),result,capsule,analysis,contract,producer_manifest


def build_install_provenance(base,identity,site,wheel,files):
    """Require actual guarded successful private BUILD/INSTALL, retain all charges."""
    manifests=list(RAW.glob('*manifest*.json'))
    require(len(manifests)<=128,'manifest inventory admission exhausted')
    by_sha={digest(p):p for p in manifests};builds=[];installs=[];charges=[]
    for directory in sorted(RAW.glob('nms8_*')):
        if not directory.is_dir():continue
        row=read(directory/'resource.json')
        require(row['scope']==SCOPE and row['accounting_basis']==BASIS and row['accounting_complete'] is True
                and row['live_processes']==[] and row['approved_seconds']==base['approved_seconds'],
                'all prior attempt accounting must be complete in same scope')
        require(finite(row['charged_wall_s']) and row['charged_wall_s']>=0,'invalid prior measured charge')
        charges.append(row['charged_wall_s'])
        input_path=directory/'inputs.json'
        if not input_path.exists():
            require(row['status']!='completed','successful attempt inputs missing');continue
        inputs=read(input_path)
        if inputs.get('mode') not in ('BUILD','INSTALL') or row['status']!='completed':continue
        require(row['exit_code']==0 and row['child_started'] is True and row['ledger_error'] is None
                and row['reserve_s']==60 and row['memory_limit_mib']==953 and row['peak_tree_bytes']<=953*1024**2,
                'successful package preparation resource controls required')
        require(all(finite(row[k]) and row[k]>=0 for k in ('wrapper_wall_s','child_process_wall_s','tree_process_wall_s'))
                and 0<row['child_process_wall_s']<=row['tree_process_wall_s']<=row['wrapper_wall_s']<=60
                and row['charged_wall_s']==row['wrapper_wall_s'],'package measured duration mismatch')
        require(inputs['manifest_sha256']==row['manifest_sha256'] and inputs['manifest_sha256'] in by_sha,'package manifest missing')
        manifest_path=by_sha[inputs['manifest_sha256']];past=read(manifest_path)
        require(inputs['authority_sha256']==base['authority_sha256'],'prior same-scope authority pooling refused')
        # Earlier candidate attempts remain charged/protected, not adopted as
        # preparation evidence for a changed current source or private artifact.
        if any(past.get(k)!=base.get(k) for k in ('held_files','build_files','build_tree','dist_directory','site_directory','wheel_identity_file','runner_sha256')):continue
        pm,authority,runner=validate_manifest(manifest_path);compatible(base,pm)
        require(inputs['scope']==SCOPE and inputs['candidate']==base['candidate'] and inputs['authority_sha256']==base['authority_sha256']
                and inputs['runner_sha256']==base['runner_sha256'] and inputs['requested_runtime']==RUNTIME,'package input identity/runtime mismatch')
        prefix=[base['python_executable'],'-X','utf8','-m','pip']
        actual=list(inputs['command']);actual[0]=str(Path(actual[0]).resolve());prefix[0]=str(Path(prefix[0]).resolve())
        if inputs['mode']=='BUILD':
            expected=prefix+['wheel','--no-deps','--no-build-isolation','--no-index','--wheel-dir',str(RAW/base['dist_directory']),'.']
            require(inputs['group']=='BUILD' and actual==expected and Path(inputs['cwd']).resolve()==(RAW/base['build_tree']).resolve(),
                    'exact private build command/source required')
            require(inputs['manifest_sha256']==identity['source_manifest_sha256'],'wheel producer source-manifest mismatch')
            builds.append(directory)
        else:
            expected=prefix+['install','--no-deps','--no-index','--no-compile','--target',str(site),str(wheel)]
            require(inputs['group']=='INSTALL' and actual==expected and Path(inputs['cwd']).resolve()==REPO.resolve(),'exact private install command required')
            installed=read(directory/'installation.json')
            require(Path(installed['site']).resolve()==site and installed['payload_errors']==[],'successful exact private installation record required')
            files[str(directory/'installation.json')]=digest(directory/'installation.json');installs.append(directory)
        for p in (input_path,directory/'resource.json',directory/'process.json',directory/'stdout.log',directory/'stderr.log',manifest_path,authority,runner):
            files[str(p)]=digest(p)
    require(len(builds)==1 and len(installs)==1,'one authentic matching successful build/install required')
    total=math.fsum(charges);require(total<=base['approved_seconds']-60,'current all-attempt allowance/reserve exhausted')
    return dict(build_attempt=str(builds[0]),install_attempt=str(installs[0]),all_attempts=len(charges),
                measured_consumed_s=total,measured_remaining_s=base['approved_seconds']-total,reserve_seconds=60)


def bind(args):
    require(not (RAW/'native_multi_shell_execution.lock').exists(),'owned numerical job still active')
    manifest_path=inside(args.manifest);base,authority,runner=validate_manifest(manifest_path)
    identity_path,identity,site,wheel=payload(base)
    output=inside(args.output_manifest);binding_path=inside(args.binding)
    require(output!=manifest_path and output!=binding_path and not output.exists() and not binding_path.exists(),'fresh immutable output names required')
    files={str(manifest_path):digest(manifest_path),str(identity_path):digest(identity_path),str(wheel):digest(wheel),
           str(Path(__file__).resolve()):digest(__file__)}
    installed_metadata=[p for d in site.glob('*.dist-info') for p in d.rglob('*') if p.is_file()]
    require(0<len(installed_metadata)<=64,'bounded installed metadata inventory required')
    for p in installed_metadata:files[str(inside(p,site))]=digest(p)
    preparation=build_install_provenance(base,identity,site,wheel,files)
    prefix=producer('prefix',args.prefix,base,identity,site,files);entries={'prefix':prefix[0]}
    if args.mode=='verify':
        require(args.full is not None and args.resumed is not None,'all three authentic producers required')
        full=producer('full',args.full,base,identity,site,files);resumed=producer('resumed',args.resumed,base,identity,site,files)
        require(prefix[3]==full[3]==resumed[3] and prefix[4]==full[4]==resumed[4],'same actual candidate/fixture contract required')
        require(prefix[1]['initial']==full[1]['initial']==resumed[1]['initial'] and prefix[1]['steps']==full[1]['steps'][:1]==resumed[1]['steps'][:1],
                'actual prefix/full/resumed accepted prefix correspondence mismatch')
        require(resumed[1]['steps'][1]['predecessor_sha256']==prefix[1]['final']['state_sha256'],'additional resumed stage predecessor mismatch')
        require(Path(full[0]['result']).read_bytes()==Path(resumed[0]['result']).read_bytes()
                and Path(full[0]['checkpoint']).read_bytes()==Path(resumed[0]['checkpoint']).read_bytes(),'fresh full2 versus fresh1+1 bytes mismatch')
        prefix_path=prefix[0]['checkpoint'];require(resumed[5]['raw_inputs'].get(prefix_path)==digest(prefix_path),'resumed input was not prospectively hash-bound')
        group=resumed[5]['groups']['RESTART_RESUMED'];require(group.get('requires_restart_input')==prefix_path and
                group['args'][group['args'].index('--checkpoint-file')+1]==prefix_path,'actual resumed public prefix input mismatch')
        entries.update(full=full[0],resumed=resumed[0])
    else:require(args.full is None and args.resumed is None,'prefix mode binds only actual prefix')
    # No job or allowance is renewed. Binder records metadata only.
    binding=dict(schema='NATIVE_MULTI_SHELL_AUTHENTIC_RESTART_BINDING_V1',mode=args.mode,scope=SCOPE,
        source_checkpoint=SOURCE_CHECKPOINT,candidate_identity=prefix[3],trajectory_identity=prefix[1]['identity'],
        actual_profile=PROFILE,records=entries,files=files,source_manifest_sha256=digest(manifest_path),
        wheel_sha256=identity['wheel_sha256'],site=str(site),approved_seconds=base['approved_seconds'],
        preparation_provenance=preparation,
        accounting_basis=BASIS,numerical_execution_by_binder=False,engineering_acceptance=False)
    binding_bytes=(json.dumps(binding,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
    revised=json.loads(json.dumps(base));revised['schema']='NATIVE_MULTI_SHELL_RESTART_BOUND_EXECUTION_MANIFEST_V1'
    revised['revision_provenance']=dict(previous_manifest=str(manifest_path),previous_sha256=digest(manifest_path),
        binder=str(Path(__file__).resolve()),binder_sha256=digest(__file__),mode=args.mode,source_checkpoint=SOURCE_CHECKPOINT)
    for name,value in files.items():revised['raw_inputs'][name]=value;revised['raw_sizes'][name]=Path(name).stat().st_size
    revised['raw_inputs'][str(binding_path)]=hashlib.sha256(binding_bytes).hexdigest();revised['raw_sizes'][str(binding_path)]=len(binding_bytes)
    if args.mode=='verify':
        revised['groups']['RESTART_VERIFY']['environment']=dict(NMS8_RESTART_REPLAY=str(binding_path),
            NMS8_RESTART_BINDING_SHA256=hashlib.sha256(binding_bytes).hexdigest())
        revised['restart_binding_status']='AUTHENTIC_PREFIX_FULL_RESUMED_BOUND_NO_NEW_SOLVE_CLAIM'
    else:
        resumed_group=revised['groups']['RESTART_RESUMED'];prefix_path=prefix[0]['checkpoint']
        require(resumed_group.get('requires_restart_input')==prefix_path and resumed_group['args'][resumed_group['args'].index('--checkpoint-file')+1]==prefix_path,
                'fixed prospective resumed path differs from supplied prefix')
        revised['restart_binding_status']='AUTHENTIC_PREFIX_BOUND_FOR_PUBLIC_RESUMED_PRODUCER'
    # Exclusive writes preserve every prior manifest/failure. Partial filesystem
    # failure leaves an identifiable binding, never overwrites an earlier record.
    with binding_path.open('xb') as stream:stream.write(binding_bytes)
    with output.open('x',encoding='utf-8') as stream:json.dump(revised,stream,indent=2,sort_keys=True,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(status='BOUND',mode=args.mode,binding=str(binding_path),binding_sha256=digest(binding_path),
                         manifest=str(output),manifest_sha256=digest(output),numerical_jobs=0),sort_keys=True))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('prefix','verify'),required=True)
    parser.add_argument('--manifest',required=True);parser.add_argument('--prefix',required=True)
    parser.add_argument('--full');parser.add_argument('--resumed');parser.add_argument('--binding',required=True)
    parser.add_argument('--output-manifest',required=True);bind(parser.parse_args())


if __name__=='__main__':main()
