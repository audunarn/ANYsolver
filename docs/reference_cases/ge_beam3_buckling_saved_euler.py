"""Evaluate saved accepted Euler factors, never rerun their preload mechanics."""
import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import sys


ARCHIVE = Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-euler-points-6536b4c-complete-20260908')
MANIFEST_SHA256 = '6331a22be4e8ee751b29a5765db2e728589e0ca77987eb5175f971a4495cc273'


def strict(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            if key in result: raise ValueError('duplicate preserved evidence key')
            result[key] = value
        return result
    def forbidden(value): raise ValueError('nonfinite preserved evidence')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=forbidden)


def run(revision, output):
    from docs.reference_cases.ge_beam3_fibre_arch_probe import guard, ROOT
    guard(revision)
    raw = (ARCHIVE/'archive-manifest.json').read_bytes()
    if sha256(raw).hexdigest() != MANIFEST_SHA256:
        raise ValueError('accepted Euler archive authority mismatch')
    manifest = strict(raw)
    inputs = {}
    def bound(name):
        data = (ARCHIVE/name).read_bytes()
        size, digest = manifest[name]
        if len(data) != size or sha256(data).hexdigest() != digest.lower():
            raise ValueError('preserved Euler member mismatch: '+name)
        inputs[name] = (size, digest.lower())
        return data
    packets = []
    for index in (0, 2, 3):
        prefix = 'cycle-a/n8/point-%02d/science/' % index
        point = strict(bound(prefix+'point-%02d.json' % index))
        state = bound(prefix+'state-%02d.json' % index)
        if (point['row']['checkpoint_sha256'] != sha256(state).hexdigest()
                or point['global_newton_programme_run'] is not True
                or point['manufactured_uniform_axial_equilibrium'] is not False
                or point['packet']['history_unchanged'] is not True):
            raise ValueError('actual accepted preload/packet authority mismatch')
        packets.append((index, point))
    # Numerical processing only after the preserved authority is verified.
    sys.path.insert(0, str(ROOT/'src'))
    import anysolver
    if Path(anysolver.__file__).resolve() != (ROOT/'src/anysolver/__init__.py').resolve():
        raise ValueError('saved-factor check did not import the frozen source package')
    import numpy as np
    from anysolver._ge_beam3_native_buckling import factor_buckling
    from anysolver._ge_beam3_p5_seeded.core import canonical
    destination = Path(output)
    destination.mkdir(exist_ok=False)
    rows = []
    for index, point in packets:
        print(dict(stage='saved-factor-buckling', index=index), flush=True)
        packet = point['packet']
        spectrum = factor_buckling(np.array(packet['left']), np.array(packet['right']),
            np.array(packet['geometric']), tuple(packet['free_dofs']), bounds=(0., 4.), num_modes=2)
        compression = point['row']['compression']
        predicted = compression*spectrum.multipliers
        errors = []
        if compression < 0:
            if spectrum.status != 'NO_MULTIPLIERS_IN_REQUESTED_WINDOW':
                raise ValueError('tensile saved state has a positive multiplier in the tested window')
        else:
            if len(predicted) != 2:
                raise ValueError('both bending predictions required')
            expected = np.array([1., 1.2])*(math.pi**2/16)
            errors = list(map(float, np.abs(predicted-expected)/expected))
            if max(errors) >= .02:
                raise ValueError('saved N8 frozen-current prediction fails two-percent Euler reference')
        rows.append(dict(index=index, source_checkpoint_sha256=point['row']['checkpoint_sha256'],
            compression=compression, spectrum=spectrum, critical_predictions=predicted,
            relative_euler_errors=errors, free_coordinates=len(spectrum.free_dofs)))
    for name in tuple(inputs): bound(name)
    if sha256((ARCHIVE/'archive-manifest.json').read_bytes()).hexdigest() != MANIFEST_SHA256:
        raise ValueError('Euler archive changed during read-only verification')
    guard(revision)
    result = dict(schema='GE_BEAM3_SAVED_EULER_LINEARIZED_BUCKLING_V1', revision=revision,
        source_manifest_sha256=MANIFEST_SHA256, inputs=inputs, rows=rows,
        preload_mechanics_rerun=False, nonlinear_critical_load_authorized=False,
        full_beam_qualification=False, production_qualified=False)
    with (destination/'saved-euler-buckling.json').open('xb') as stream:
        stream.write(canonical(result))
    print(dict(stage='saved-factor-check-complete', rows=len(rows)), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--revision', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    run(args.revision, args.output)
