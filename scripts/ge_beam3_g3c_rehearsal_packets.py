"""Exclusive raw packet manifests. Inert: never constructs a numerical owner."""
from hashlib import sha256
from pathlib import Path
import os
import stat
import ge_beam3_g3c_restart_preflight as p
import ge_beam3_g3c_rehearsal_contract as design


def fingerprint(raw):
    return dict(bytes=len(raw), sha256=sha256(raw).hexdigest())


def contained(root, name):
    root=Path(root).absolute()
    if type(name) is not str or not name or Path(name).name!=name or ':' in name or name in ('.','..'):
        raise ValueError('flat registered packet filename required')
    path=root/name
    for item in (path,*path.parents):
        info=item.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&1024:
            raise ValueError('reparse packet path')
    if not path.is_file() or path.resolve().parent!=root.resolve():
        raise ValueError('regular contained packet required')
    return path


def read_bound(root, name, expected):
    raw=contained(root,name).read_bytes()
    if p.canonical(fingerprint(raw))!=p.canonical(expected) or not raw:
        raise ValueError('packet byte/hash mismatch')
    return raw


def exclusive(path, raw):
    if type(raw) is not bytes: raise ValueError('raw bytes required')
    parent=Path(path).absolute().parent
    for item in (parent,*parent.parents):
        info=item.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&1024:
            raise ValueError('reparse output path')
    with Path(path).open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())


def store(root, raw, case, prefix, runtime):
    # Authority for storing bytes is the actual producer call; this check only
    # checks syntax. It does not claim replay authentication of imported bytes.
    value=p.preflight(raw,sha256(raw).hexdigest(),expected_runtime_sha256=runtime)
    if value.epoch!=prefix or (value.fixture_id+'::'+value.variant)!='::'.join(case.split('::')[:2]):
        raise ValueError('producer packet selector/prefix mismatch')
    if value.common_motion!=case.split('::')[-1]: raise ValueError('producer packet motion mismatch')
    verify_commands(raw,case,prefix)
    name=f'prefix-{prefix:03d}.json'
    exclusive(Path(root)/name,raw)
    return dict(case_id=case,prefix=prefix,name=name,**fingerprint(raw))


def manifest(lease_sha, case, stages, runtime, rows):
    result=dict(kind='G3C_REHEARSAL_PACKET_MANIFEST',lease_sha256=lease_sha,
                case_id=case,accepted_stages=stages,runtime_sha256=runtime,packets=rows)
    validate_manifest(result,lease_sha,case,stages,runtime)
    return result


def validate_manifest(value, lease_sha, case, stages, runtime):
    if set(value)!={'kind','lease_sha256','case_id','accepted_stages','runtime_sha256','packets'}:
        raise ValueError('packet manifest schema')
    expected=dict(kind='G3C_REHEARSAL_PACKET_MANIFEST',lease_sha256=lease_sha,
                  case_id=case,accepted_stages=stages,runtime_sha256=runtime)
    if p.canonical({k:v for k,v in value.items() if k!='packets'})!=p.canonical(expected):
        raise ValueError('packet manifest authority mismatch')
    rows=value['packets']
    if type(rows) is not list or len(rows)!=stages+1: raise ValueError('complete prefix inventory required')
    for i,row in enumerate(rows):
        if (type(row) is not dict or set(row)!={'case_id','prefix','name','bytes','sha256'}
                or type(row['prefix']) is not int or row['prefix']!=i or row['case_id']!=case
                or row['name']!=f'prefix-{i:03d}.json' or type(row['bytes']) is not int
                or not 0<row['bytes']<=8*1024**2):
            raise ValueError('packet row schema/order/count')
        p.hash_value(row['sha256'])


def verify_directory(root, value, lease_sha, case, stages, runtime):
    validate_manifest(value,lease_sha,case,stages,runtime)
    if {f.name for f in Path(root).iterdir()}!={r['name'] for r in value['packets']}:
        raise ValueError('extra/missing packet files')
    previous=None
    for row in value['packets']:
        raw=read_bound(root,row['name'],{k:row[k] for k in ('bytes','sha256')})
        packet=p.preflight(raw,row['sha256'],expected_runtime_sha256=runtime)
        if packet.epoch!=row['prefix'] or packet.fixture_id!=case.split('::')[0] or packet.variant!='BASE' or packet.common_motion!=case.split('::')[-1]:
            raise ValueError('packet contents selector mismatch')
        current=verify_commands(raw,case,row['prefix'])
        if previous is not None and (current['initial_sha256']!=previous['initial_sha256']
                or current['final_state']['previous_sha256']!=previous['final_sha256']
                or p.canonical(current['history'][:-1])!=p.canonical(previous['history'])):
            raise ValueError('stored prefix chain mismatch')
        previous=current


def verify_commands(raw,case,prefix):
    row=next((r for r in design.expected()['histories'] if r['case_id']==case),None)
    if row is None or type(prefix) is not int or not 0<=prefix<=row['accepted_stages']:
        raise ValueError('registered producer case/prefix required')
    value=p.strict(raw)
    commands=design.inherited.commands(row['common_motion'],row['force_scale'])[:prefix]
    if p.canonical([e['command'] for e in value['history']])!=p.canonical(commands):
        raise ValueError('registered producer command/scale mismatch')
    return value
