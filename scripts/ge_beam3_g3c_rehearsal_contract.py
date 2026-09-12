"""Inert, exact inventory for the bounded G3c history rehearsal; no executor."""
from hashlib import sha256
from pathlib import Path
import os
import subprocess
import ge_beam3_g3c_history_contract as inherited

ROOT = Path(__file__).resolve().parents[1]
PATH = 'docs/reference_cases/ge_beam3_g3c_rehearsal_contract_v1.json'
BASE = 'ef3df43c4e724e7b2e3d4b98510ed4e2eecd3367'
TREE = '772e7b6708c9c5d2d37f42261662e871584a9de8'
PARENT_SHA = '7afe9d79096338c122280c20f83b6e7c5681ea0a382e32cb15e1e9349b9372e6'
EXTENT = [
    'docs/GE_BEAM3_G3C_REHEARSAL_CONTRACT.md', PATH,
    'scripts/ge_beam3_g3c_rehearsal_contract.py',
    'tests/test_ge_beam3_g3c_rehearsal_contract.py',
]
REPLAY = {
    ('R08_POLICY_FIXTURE', 'well_shaped_native_element_identity'),
    ('R17_NATIVE_FULL_RESIDUAL', 'nonzero_finite_residual_component'),
    ('R18_NATIVE_FULL_JACOBIAN', 'nonzero_finite_jacobian_component'),
    *{('R19_NATIVE_SCHUR', m) for m in ('lift', 'correction', 'condensed_tangent', 'condensed_residual')},
    ('R20_NATIVE_POSE', 'total_u'), ('R20_NATIVE_POSE', 'proper_but_wrong_Q'),
    ('R22_ADAPTER_FIELDS', 'deformation'),
    *{('R23_ADAPTER_DIAGNOSTIC', m) for m in ('candidate_sha', 'previous_sha', 'well_shaped_adapter_definition_sha256')},
}


def parent():
    raw = inherited.normalized(ROOT/inherited.CONTRACT)
    if sha256(raw).hexdigest() != PARENT_SHA:
        raise ValueError('inherited contract hash')
    return inherited.validate_contract(inherited.strict(raw))


def rejection(category, member):
    if (category, member) in REPLAY:
        return 'GENUINE_REPLAY_MISMATCH'
    if (category, member) == ('R16_OUTER_STATE_HASHES', 'initial_sha'):
        return 'VIRGIN_INITIAL_HASH_MISMATCH'
    if (category, member) == ('R09_RUNTIME', 'changed_implementation_review'):
        return 'RUNNER_AUTHORITY_BEFORE_CONSTRUCTION'
    return 'PREFLIGHT_BEFORE_CONSTRUCTION'


def expected():
    old = parent()
    histories = [r for motion, scale in [('NONE', .01), ('CM3', 10.)]
                 for r in old['history_matrix'] if r['variant'] == 'BASE'
                 and r['common_motion'] == motion and r['force_scale'] == scale]
    probes = [dict(origin=o, category=c['id'], member=m, rejection=rejection(c['id'], m))
              for o in old['mutation_origins'] for c in old['mutation_categories'] for m in c['members']]
    return dict(
        schema='GE_BEAM3_G3C_REHEARSAL_CONTRACT_V1', stage='DESIGN_ONLY',
        base=dict(commit=BASE, tree=TREE), extent=EXTENT,
        inherited_contract_sha256=PARENT_SHA,
        prerequisite_execution_review_sha256='56914ccb130eb7280b50614df66be9481c723e5c637ba1f8dc89850724adbc8b',
        execution_authorized=False, full_g3c_qualified=False, production_activation_authorized=False,
        histories=histories, mutation_probes=probes, limits=old['limits'], tolerances=old['tolerances'],
        separate_counts=dict(histories=10, accepted_stage_events=70, stored_prefix_packets=80,
                             mutation_categories=24, members_per_origin=71, mutation_probes=142,
                             positive_origin_replays=2, full_replay_mutations=26),
        waves=['NONE5', 'CM3_5', 'POSITIVE_ORIGIN_REPLAY2', 'PREFLIGHT_BY_ORIGIN2',
               'VIRGIN_AND_REVIEW4', 'REPLAY_NEGATIVE_6_6_6_6_2'],
        scheduling='SEQUENTIAL_WAVES_STOP_ON_FAILURE_MAX_THREE_CHILDREN_NO_RETRY',
        checkpoint_authority='EXTERNAL_PRODUCER_MANIFEST_EXACT_BYTES_AND_SHA256_ALL_PREFIXES',
        negative_authority='SEPARATE_REHASHED_ATTACK_FIXTURES_NEVER_POSITIVE_EVIDENCE',
        mutation_noop_allowed=False, catch_arbitrary_exception_as_pass=False,
        open_obligations=old['obligations'], full_matrix_replaced=False)


def validate(value):
    if inherited.canonical(value) != inherited.canonical(expected()):
        raise ValueError('exact rehearsal schema/inventory mismatch')
    return value


def audit():
    c = validate(inherited.strict(inherited.normalized(ROOT/PATH)))
    inherited.audit(parent())
    review = ROOT/'docs/reference_cases/ge_beam3_g3c_history_execution_review_v1.json'
    if sha256(inherited.normalized(review)).hexdigest() != c['prerequisite_execution_review_sha256']:
        raise ValueError('accepted smoke/prefix review changed')
    env = {k:v for k,v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
               GIT_CONFIG_SYSTEM=os.devnull, GIT_NO_REPLACE_OBJECTS='1', GIT_ATTR_NOSYSTEM='1')
    def git(*args):
        return subprocess.check_output(['git', '-c', 'safe.directory='+ROOT.as_posix(),
            '-c', 'core.autocrlf=true', '-c', 'core.eol=crlf',
            '-c', 'core.excludesFile='+os.devnull,
            '-c', 'core.attributesFile='+os.devnull, *args], cwd=ROOT, env=env, timeout=15)
    if git('rev-parse', BASE+'^{tree}').decode().strip() != TREE:
        raise ValueError('base tree mismatch')
    git('merge-base', '--is-ancestor', BASE, 'HEAD')
    changed = set(filter(None, git('diff', '--name-only', BASE).decode().splitlines()))
    changed.update(filter(None, git('ls-files', '--others', '--exclude-standard').decode().splitlines()))
    if changed != set(EXTENT):
        raise ValueError('exact design extent mismatch')
    if any(git('ls-tree', BASE, '--', path).strip() for path in EXTENT):
        raise ValueError('design must be additive')
    return dict(stage='DESIGN_ONLY_NO_MECHANICS', counts=c['separate_counts'])


if __name__ == '__main__':
    print(inherited.canonical(audit()).decode(), end='')
