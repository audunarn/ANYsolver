"""Inert full-scope history/restart registry and authority audit."""
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = 'docs/reference_cases/ge_beam3_g3c_history_restart_contract_v1.json'
GRAPHS = ('J_B2_PAIR', 'J_B3_PAIR', 'J_Q4_PAIR', 'J_S3_PAIR', 'J_MULTIFAMILY_LOOP')
VARIANTS = ('BASE', 'SHUFFLED_INSERTION', 'RENUMBERED', 'CONNECTIVITY_REVERSED', 'PROPER_GLOBAL_TRANSFORM')
MOTIONS = ('NONE', 'CM0', 'CM1', 'CM2', 'CM3')
SCALES = (.01, 1., 10.)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode('ascii')


def strict(raw):
    if type(raw) is not bytes or not 0 < len(raw) <= 8*1024**2:
        raise ValueError('bounded canonical bytes required')
    def pairs(rows):
        result = {}
        for key, value in rows:
            if key in result:
                raise ValueError('duplicate key')
            result[key] = value
        return result
    def bad(value):
        raise ValueError('nonfinite JSON')
    value = json.loads(raw.decode('ascii'), object_pairs_hook=pairs, parse_constant=bad)
    if canonical(value) != raw:
        raise ValueError('noncanonical JSON')
    return value


def fingerprint(raw):
    return {'bytes': len(raw), 'sha256': sha256(raw).hexdigest()}


def normalized(path):
    return path.read_bytes().replace(b'\r\n', b'\n')


def commands(motion, scale):
    if motion not in MOTIONS or type(scale) is not float or scale not in SCALES:
        raise ValueError('registered history selector required')
    rows = [] if motion == 'NONE' else [dict(kind='PREPARE_COMMON_MOTION', step=i) for i in range(1, 5)]
    return rows + [dict(kind='LOAD_STAGE', load_factor=value, force_scale=scale, root_stage=i)
                   for i, value in enumerate((0., .5, 1., .25, 0.))]


def matrix():
    return [dict(case_id=f'{graph}::{variant}::S{index}::{motion}', graph=graph,
                 variant=variant, force_scale=scale, common_motion=motion,
                 accepted_stages=len(commands(motion, scale)),
                 commands_sha256=sha256(canonical(commands(motion, scale))).hexdigest())
            for graph in GRAPHS for variant in VARIANTS
            for index, scale in enumerate(SCALES) for motion in MOTIONS]


def prefixes():
    return [dict(case_id=row['case_id'], prefix=prefix)
            for row in matrix() for prefix in range(row['accepted_stages']+1)]


def validate_contract(c):
    if c['schema'] != 'GE_BEAM3_G3C_HISTORY_RESTART_CONTRACT_V1' or c['stage'] != 'DESIGN_ONLY':
        raise ValueError('contract schema/stage')
    if c['implementation_authorized'] is not False or c['execution_authorized'] is not False:
        raise ValueError('design cannot authorize mechanics')
    if canonical(c['history_matrix']) != canonical(matrix()) or c['prefix_matrix_sha256'] != sha256(canonical(prefixes())).hexdigest():
        raise ValueError('complete ordered matrix changed')
    if canonical(c['counts']) != canonical(dict(graph_variants=25, history_probes=375, accepted_stage_events=3075,
                          restart_prefix_probes=3450, formal_cycles=2)):
        raise ValueError('coverage reduced or relabeled')
    expected = dict(child_seconds=600, wave_seconds=1800, memory_bytes=24*1024**3,
                    numerical_threads=1, max_workers=3, inactivity_seconds=120,
                    automatic_retry=False, restart_bytes=8*1024**2, accepted_history=128)
    if canonical(c['limits']) != canonical(expected):
        raise ValueError('execution limits changed')
    if canonical(c['tolerances']) != canonical(dict(invariant=1e-11, directional=1e-7, steps=[1e-4, 1e-5, 1e-6],
                               deterministic='BYTE_EQUALITY')):
        raise ValueError('scientific tolerances changed')
    if c['restart_schema'] != 'GE_BEAM3_G3C_STABLE_GRAPH_RESTART_V1':
        raise ValueError('wrong successor restart schema')
    layout = dict(c['inherited_layouts']['checkpoint'])
    layout.update(schema='literal:GE_BEAM3_G3C_STABLE_GRAPH_RESTART_V1',
                  policy='literal:GE_BEAM3_G3C_STABLE_MIXED_ELASTIC_OWNER_V1')
    if c['checkpoint_layout'] != layout:
        raise ValueError('checkpoint layout weakened')
    if len(c['mutation_categories']) != 24 or len({r['id'] for r in c['mutation_categories']}) != 24:
        raise ValueError('mutation coverage changed')
    cases = {r['case_id']:r for r in matrix()}
    for row in c['mutation_origins']:
        if row['case_id'] not in cases or type(row['prefix']) is not int or not 0 <= row['prefix'] <= cases[row['case_id']]['accepted_stages']:
            raise ValueError('invalid mutation origin')
    return c


def audit(c, root=ROOT):
    validate_contract(c)
    env = {k:v for k,v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull,
               GIT_NO_REPLACE_OBJECTS='1', GIT_ATTR_NOSYSTEM='1')
    def git(*args):
        return subprocess.check_output(['git', '-c', 'safe.directory='+root.as_posix(),
             '-c', 'core.autocrlf=true', '-c', 'core.eol=crlf', '-c', 'core.attributesFile='+os.devnull,
             *args], cwd=root, env=env, timeout=15)
    base = c['base']['commit']
    if git('rev-parse', base+'^{tree}').decode().strip() != c['base']['tree']:
        raise ValueError('base tree mismatch')
    blobs = {}
    for item in git('ls-tree', '-r', '-z', base).split(b'\0'):
        if item:
            metadata, path = item.split(b'\t', 1)
            blobs[path.decode()] = metadata.split()[2].decode()
    seen = set()
    for row in c['bindings']:
        path = row['path']
        if path in seen or Path(path).is_absolute() or '..' in Path(path).parts:
            raise ValueError('invalid authority path')
        seen.add(path)
        if blobs.get(path) != row['blob'] or fingerprint(normalized(root/path)) != row['fingerprint']:
            raise ValueError('inherited authority changed: '+path)
    previous = strict(normalized(root/'docs/reference_cases/ge_beam3_g3c_mixed_owner_contract_v1.json'))
    if c['obligations'] != previous['next_tests'] or c['inherited_layouts'] != previous['layouts']:
        raise ValueError('original obligations/layouts changed')
    return dict(kind='DESIGN_ONLY_NO_MECHANICS', history_probes=len(matrix()),
                restart_prefix_probes=len(prefixes()), bindings=len(seen))


if __name__ == '__main__':
    print(canonical(audit(strict(normalized(ROOT/CONTRACT)))).decode(), end='')
