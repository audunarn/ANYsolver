"""Hash-bound load-only audit of preserved data; no mechanics/reference solve.

This cannot repair or replace the missing canonical result of request b89e903d.
Only standard-library imports are allowed. Output is diagnostic and unqualified.
"""
import argparse
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]
CHECKPOINT_SHA = 'bcf90a0eca2923ee04ab00bf61b6e1eabdac40779671f90666bdbc2964420a1f'
CHECKPOINT_BYTES = 95786
REFERENCE_LF_SHA = 'c2401dfc756cf7d95005ee6c92f43ae5960c82b361e7477a68cd2b676e025728'
REFERENCE_PATH = 'docs/reference_cases/ge_beam3_fibre_arch_comparison_development_evidence.json'
REFERENCE_COMMIT = '3f05a4ee728f632aace088e67bdf9d97bcf805ed'
REFERENCE_BLOB = '9eae70f2b25c3764691c6756892cdd1427fa37be'
FAILED_REQUEST = 'b89e903dc17d44408ce0c42d11c6b61f'
TARGETS = (.01, .025, .04, .055)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode('ascii')


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result: raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def _constant(value):
    raise ValueError('nonfinite JSON constant')


def parse(raw):
    if type(raw) is not bytes or not 0 < len(raw) <= 2*1024*1024:
        raise ValueError('bounded JSON bytes required')
    value = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_constant)
    if canonical(value) != raw: raise ValueError('strict canonical JSON required')
    return value


def _seal(value, key):
    if not isinstance(value, dict) or key not in value:
        raise ValueError('missing checkpoint seal')
    body = {k: v for k, v in value.items() if k != key}
    if sha256(canonical(body)).hexdigest() != value[key]: raise ValueError('checkpoint seal mismatch')


def _finite(value):
    if type(value) is not float or not math.isfinite(value): raise ValueError('finite float required')
    return value


def inspect_records(checkpoint, reference, *, macros=4):
    """Structural/semantic checks after external identity checks; unit-testable."""
    if type(macros) is not int or macros not in (4, 6, 12):
        raise ValueError('registered four/six/twelve-macro audit scope required')
    label = {4: 'four', 6: 'six', 12: 'twelve'}[macros]
    if (checkpoint['schema'] != 'GE_BEAM3_PHYSICAL_FIBRE_TRANSLATION_CONTROL_CHAIN_V1'
            or checkpoint['program']['schema'] != 'GE_BEAM3_KINEMATIC_SEEDED_SPATIAL_NEWTON_FIBRE_CONTROL_V1'
            or type(checkpoint['completed_targets']) is not int or checkpoint['completed_targets'] != 4
            or len(checkpoint['records']) != 4 or checkpoint['node_ids'] != list(range(1, 2*macros+2))
            or checkpoint['element_ids'] != list(range(1, macros+1))):
        raise ValueError('registered macro checkpoint scope mismatch')
    if (reference['schema'] != 'GE_BEAM3_PRESERVED_FIBRE_ARCH_GEOMETRIC_COMPARISON_V1'
            or reference['production_qualified'] is not False or reference['mechanics_replayed'] is not False
            or reference['section_comparison'] != 'NOMINAL_ELASTIC_EA_1E6_GA_4E5_EI_100_NOT_EXACT_DYADIC_SECTION_CERTIFICATE'):
        raise ValueError('preserved reference scope mismatch')
    _seal(checkpoint, 'checkpoint_sha256'); _seal(checkpoint['initial'], 'record_sha256')
    if type(checkpoint['initial']['target']) is not int or checkpoint['initial']['target'] != 0:
        raise ValueError('checkpoint initial target')
    previous = checkpoint['initial']['record_sha256']; result = []
    reference_rows = reference['rows']
    if len(reference_rows) != 8 or len({row['displacement'] for row in reference_rows}) != 8:
        raise ValueError('unique preserved reference targets required')
    for index, (target, row, prior) in enumerate(zip(TARGETS, checkpoint['records'], reference_rows[:4]), 1):
        _seal(row, 'record_sha256')
        if (type(row['target']) is not int or row['target'] != index or row['previous_sha256'] != previous
                or _finite(row['displacement_target']) != target or _finite(prior['displacement']) != target
                or prior['reference_profile'] != 'BVP9' or prior['stiffness_scale'] != 1e6
                or prior['same_equilibrium_branch_proved'] is not False or prior['production_qualified'] is not False):
            raise ValueError('ordered targets, chain or reference interpretation mismatch')
        histories = row['histories']
        if not histories or any(not cell['stations'] for cell in histories):
            raise ValueError('physical history evidence missing')
        count = 0
        for cell in histories:
            for station in cell['stations']:
                if not station['rows']: raise ValueError('physical fibre history missing')
                for fibre in station['rows']:
                    if not fibre: raise ValueError('empty fibre history')
                    for value in fibre:
                        if _finite(value) != 0.: raise ValueError('elastic reference not valid for plastic history')
                        count += 1
        native = _finite(row['parameter']); load = _finite(prior['reference_load'])
        coarse = _finite(prior['native_load'])
        if load <= 0.: raise ValueError('positive preserved reference load required')
        result.append(dict(displacement=target, **{f'native_{label}_macro_load': native},
            preserved_reference_load=load, native_two_macro_load=coarse,
            **{f'{label}_macro_relative_load_error': abs(native-load)/abs(load)},
            two_macro_relative_load_error=abs(coarse-load)/abs(load),
            inspected_zero_history_coordinates=count, checkpoint_record_sha256=row['record_sha256']))
        previous = row['record_sha256']
    return result


def synthesize(checkpoint_raw, reference_lf_raw, *, source_commit):
    if (len(checkpoint_raw) != CHECKPOINT_BYTES or sha256(checkpoint_raw).hexdigest() != CHECKPOINT_SHA
            or sha256(reference_lf_raw).hexdigest() != REFERENCE_LF_SHA):
        raise ValueError('preserved input identity mismatch')
    if (type(source_commit) is not str or len(source_commit) != 40
            or any(c not in '0123456789abcdef' for c in source_commit)):
        raise ValueError('exact source commit required')
    rows = inspect_records(parse(checkpoint_raw), parse(reference_lf_raw))
    return dict(schema='GE_BEAM3_PRESERVED_FOUR_MACRO_LOAD_AUDIT_V1',
        status='DEVELOPMENT_LOAD_COMPARISON_ONLY', source_commit=source_commit,
        failed_request_id=FAILED_REQUEST, historical_request_successful=False,
        original_canonical_comparison_repaired=False, checkpoint_sha256=CHECKPOINT_SHA,
        checkpoint_bytes=CHECKPOINT_BYTES, reference_lf_sha256=REFERENCE_LF_SHA,
        reference_commit=REFERENCE_COMMIT, reference_blob=REFERENCE_BLOB, rows=rows,
        mechanics_replayed=False, reference_recomputed=False, geometry_or_frame_comparison_completed=False,
        same_equilibrium_branch_proved=False, independent_review='PENDING', production_qualified=False)


def guard(revision):
    def git(*args):
        return subprocess.check_output(['git', '-C', str(ROOT), *args], timeout=10).decode('ascii').strip()
    if git('rev-parse', 'HEAD') != revision or git('status', '--porcelain', '--untracked-files=all'):
        raise ValueError('clean frozen source required')
    if git('rev-parse', f'{REFERENCE_COMMIT}:{REFERENCE_PATH}') != REFERENCE_BLOB:
        raise ValueError('preserved Git reference authority mismatch')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--checkpoint', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(); guard(args.revision)
    if not args.output.is_absolute() or args.output.resolve().is_relative_to(Path('C:/Github').resolve()):
        raise ValueError('fresh external output required')
    if args.output.exists(): raise FileExistsError('exclusive diagnostic output already exists')
    # LF normalization applies only to the Git-held reference, never checkpoint bytes.
    if args.checkpoint.stat().st_size != CHECKPOINT_BYTES:
        raise ValueError('checkpoint size mismatch before reading')
    if (ROOT/REFERENCE_PATH).stat().st_size > 2*1024*1024:
        raise ValueError('reference size bound')
    reference = (ROOT/REFERENCE_PATH).read_bytes().replace(b'\r\n', b'\n')
    value = synthesize(args.checkpoint.read_bytes(), reference, source_commit=args.revision)
    raw = canonical(value); guard(args.revision)
    # Stage on the output volume. Publish only complete validated bytes, exclusively.
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pending = args.output.with_name(args.output.name+'.pending')
    with pending.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    if pending.read_bytes() != raw: raise ValueError('staged diagnostic mismatch')
    os.link(pending, args.output)
    print(json.dumps(dict(status=value['status'], bytes=len(raw), sha256=sha256(raw).hexdigest())))


if __name__ == '__main__': main()
