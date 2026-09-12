"""Read-only original-producer authority. Never rewrites leases or packets."""
from hashlib import sha256
from pathlib import Path, PureWindowsPath
import stat
import subprocess
import ge_beam3_g3c_rehearsal_bridge_contract as contract
import run_ge_beam3_g3c_rehearsal as producer

ROOT=Path(__file__).resolve().parents[1]
canonical=producer.canonical
environment=producer.environment
SPEC=contract.expected()['producer']
ARCHIVE=Path(SPEC['archive_root'])
CONTRACT_SHA='cf4b353df83a3267978681e5a808b46c46307ce5138769701fd945a762ca6b97'
REVIEW_SHA='8b347976ea4cde82fb4fcbba9de3f6f05fe8e4c8b184795365dc39b4c04d5b55'


def identity():
    return dict(contract_sha256=CONTRACT_SHA,archive_manifest_sha256=SPEC['archive_manifest_sha256'],
                producer_commit=SPEC['commit'],producer_tree=SPEC['tree'],
                producer_review_sha256=SPEC['implementation_review_sha256'])


def validate_identity(value):
    if canonical(value)!=canonical(identity()): raise ValueError('exact role-separated bridge identity')


def design_authority():
    contract.audit()
    if sha256(contract.common.normalized(ROOT/contract.PATH)).hexdigest()!=CONTRACT_SHA:
        raise ValueError('bridge contract hash')
    raw=contract.common.normalized(ROOT/'docs/reference_cases/ge_beam3_g3c_rehearsal_bridge_design_review_v1.json')
    if sha256(raw).hexdigest()!=REVIEW_SHA: raise ValueError('bridge design review hash')
    review=environment.strict(raw)
    if review['decision']!='ACCEPTED_G3C_R06_CONSUMER_BRIDGE_DESIGN_ONLY' or review['findings']:
        raise ValueError('bridge design not accepted')
    for path,fp in review['scope']['files'].items():
        if contract.common.fingerprint(contract.common.normalized(ROOT/path))!=fp:
            raise ValueError('reviewed bridge design changed')


def archive_manifest():
    # Check directories before descending: never follow a reparse tree.
    environment.regular(ARCHIVE/'archive-manifest.json')
    files=set(); todo=[ARCHIVE]
    while todo:
        directory=todo.pop()
        for path in directory.iterdir():
            if path.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                raise ValueError('reparse archive entry')
            if path.is_dir(): todo.append(path)
            elif path.is_file(): files.add(path.relative_to(ARCHIVE).as_posix())
            else: raise ValueError('nonregular archive entry')
    raw=(ARCHIVE/'archive-manifest.json').read_bytes()
    if sha256(raw).hexdigest()!=SPEC['archive_manifest_sha256']: raise ValueError('fixed archive manifest hash')
    value=environment.strict(raw)
    if (value['archive_root']!=SPEC['archive_root'] or len(value['files'])!=172
            or files!=set(value['files'])|{'archive-manifest.json'}):
        raise ValueError('complete fixed archive inventory')
    for name,fp in value['files'].items():
        if Path(name).is_absolute() or '..' in Path(name).parts: raise ValueError('archive path escape')
        if contract.common.fingerprint(environment.regular(ARCHIVE/name).read_bytes())!=fp:
            raise ValueError('archived raw input changed: '+name)
    return value


def original_inputs(inputs,deadline=None):
    if len(inputs)!=SPEC['inputs_count'] or sha256(canonical(inputs)).hexdigest()!=SPEC['inputs_sha256']:
        raise ValueError('original full input digest')
    git=producer.inherited.git
    if git('rev-parse',SPEC['commit']+'^{tree}')!=SPEC['tree']: raise ValueError('original producer tree')
    git('merge-base','--is-ancestor',SPEC['commit'],'HEAD')
    rows={}
    for line in git('ls-tree','-r',SPEC['commit']).splitlines():
        metadata,path=line.split('\t',1); mode,kind,blob=metadata.split()
        if kind!='blob' or mode not in ('100644','100755'): raise ValueError('original regular Git blob required')
        rows[path]=blob
    if set(rows)!=set(inputs): raise ValueError('original input/tree inventory mismatch')
    # One bounded binary Git call, not thousands of per-path processes.
    result=subprocess.run(['git','-c','safe.directory='+ROOT.as_posix(),'cat-file','--batch'],
        cwd=ROOT,env=environment.git_env(),input=('\n'.join(rows.values())+'\n').encode('ascii'),
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,timeout=30)
    data=result.stdout; offset=0
    for path,blob in rows.items():
        producer.check_deadline(deadline)
        end=data.index(b'\n',offset); header=data[offset:end].decode().split(); offset=end+1
        if len(header)!=3 or header[:2]!=[blob,'blob']: raise ValueError('original Git blob response')
        size=int(header[2]); raw=data[offset:offset+size]; offset+=size
        if data[offset:offset+1]!=b'\n': raise ValueError('original Git blob framing')
        offset+=1
        if contract.common.fingerprint(raw.replace(b'\r\n',b'\n'))!=inputs[path]:
            raise ValueError('original input does not match immutable Git blob: '+path)
        if path not in contract.expected()['correction_modify']:
            current=environment.regular(ROOT/path).read_bytes().replace(b'\r\n',b'\n')
            if contract.common.fingerprint(current)!=inputs[path]: raise ValueError('unchanged producer input changed: '+path)
    if offset!=len(data): raise ValueError('extra original blob response')


def previous_reference(value,wave,manifest):
    if wave=='none':
        if value is not None: raise ValueError('original NONE predecessor must be absent')
        return
    if type(value) is not dict or set(value)!={'path','bytes','sha256'}:
        raise ValueError('original CM3 predecessor shape')
    # Raw CM3 bytes are already pinned. Compare its unmodified Windows path
    # against the exact archive origin mapping, then read only archived NONE.
    expected=PureWindowsPath(manifest['original_roots']['none'])/'wave.json'
    if (type(value['path']) is not str or PureWindowsPath(value['path'])!=expected
            or canonical({k:value[k] for k in ('bytes','sha256')})!=canonical(SPEC['waves']['none'])):
        raise ValueError('original serialized reference mapping')


def validate_process(process,result,lane,lease_raw):
    if (set(process)!={'kind','scope_id','status','lane','elapsed_seconds','returncode','active_processes','peak_tree_bytes','lease_sha256','files'}
            or process['kind']!='G3C_REHEARSAL_CHILD_DIAGNOSTIC' or process['scope_id']!=producer.SCOPE
            or process['lane']!=lane or canonical(process)!=canonical(result) or process['status']!='PASSED'
            or type(process['returncode']) is not int or process['returncode']!=0
            or type(process['active_processes']) is not int or process['active_processes']!=0
            or type(process['elapsed_seconds']) is not float or not 0<=process['elapsed_seconds']<600
            or type(process['peak_tree_bytes']) is not int or not 0<=process['peak_tree_bytes']<=24*1024**3
            or process['lease_sha256']!=sha256(lease_raw).hexdigest()):
        raise ValueError('original terminal/resource evidence')


def verify(deadline=None):
    producer.check_deadline(deadline); design_authority(); manifest=archive_manifest()
    if producer.history.runtime_identity()!=SPEC['runtime_sha256']: raise ValueError('original runtime changed')
    if producer.inherited.infrastructure.CAPSULE_SHA!=SPEC['environment_sha256']:
        raise ValueError('original environment identity')
    collected={}; inputs=None; candidate={k:SPEC[k] for k in ('commit','tree')}
    for wave in SPEC['allowed_roles']:
        raw=environment.regular(ARCHIVE/wave/'wave.json').read_bytes()
        if contract.common.fingerprint(raw)!=SPEC['waves'][wave]: raise ValueError('original wave identity')
        value=environment.strict(raw)
        if (set(value)!={'kind','scope_id','wave','status','elapsed_seconds','results','previous'}
                or value['kind']!='G3C_REHEARSAL_WAVE_DIAGNOSTIC' or value['scope_id']!=producer.SCOPE
                or value['wave']!=wave or value['status']!='PASSED'
                or type(value['elapsed_seconds']) is not float or not 0<=value['elapsed_seconds']<1800
                or set(value['results'])!=set(producer.WAVES[wave])): raise ValueError('original complete wave required')
        previous_reference(value['previous'],wave,manifest)
        for lane in producer.WAVES[wave]:
            producer.check_deadline(deadline); out=ARCHIVE/wave/lane
            lease_raw=environment.regular(out/'lease.json').read_bytes(); lease=environment.strict(lease_raw)
            if inputs is None:
                inputs=lease['inputs']; original_inputs(inputs,deadline)
            producer.verify_lease(lease,candidate,inputs,SPEC['implementation_review_sha256'],lane,wave)
            if canonical(lease['previous'])!=canonical(value['previous']): raise ValueError('original lease linkage')
            producer.verify_review(environment.regular(out/'review.json').read_bytes(),SPEC['implementation_review_sha256'],candidate,inputs)
            process=environment.strict(environment.regular(out/'process.json').read_bytes())
            validate_process(process,value['results'][lane],lane,lease_raw)
            producer.verify_child_files(out,process,lease)
            collected[lane]=(out,lease)
    if len(collected)!=10: raise ValueError('all original histories required')
    producer.check_deadline(deadline)
    return collected
