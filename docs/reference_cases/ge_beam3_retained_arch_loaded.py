"""Read-only loaded arch snapshot checks; never a new continuation solve."""
import argparse
from hashlib import sha256
import math
import os
from pathlib import Path
import subprocess
import sys

from docs.reference_cases.ge_beam3_retained_prestress_protocol import canonical, strict_bytes, read
from docs.reference_cases.ge_beam3_fibre_arch_probe import ROOT, guard
from docs.reference_cases.e4_pl_s3_v2_bounded_process import THREAD_ENVIRONMENT

BASE = '89446eeac882ff48707b6aeae1c3f3e56e4f2fb3'
ARCHIVE = Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-arch-repeats-307c48d-20260908')
MANIFEST_SHA = '14d83c2b09cce8acf04649ce5e4f4d09fbbb500986ad2bac949ad0a0cb9dd4aa'
SCHEMA = 'GE_BEAM3_LOADED_ARCH_SNAPSHOT_CHECK_V1'
IDENTITIES = ('potential', 'residual', 'hessian', 'spatial_jacobian', 'kinematics',
              'virtual_work', 'recovery', 'frame', 'station_work', 'external_virtual_work')


def extent(macros, step):
    if type(macros) is not int or macros not in (2, 12) or type(step) is not int or step not in (1, 12):
        raise ValueError('registered smoke/finest mesh and pre/post-limit steps required')


def historical(macros, step, archive=ARCHIVE):
    """Authenticate preserved input before importing mechanics or numerical code."""
    extent(macros, step)
    raw = read(archive/'archive-manifest.json')
    if sha256(raw).hexdigest() != MANIFEST_SHA:
        raise ValueError('preserved archive manifest changed')
    manifest = strict_bytes(raw)
    def packet(name):
        data = read(archive/name)
        if manifest[name] != [len(data), sha256(data).hexdigest().upper()]:
            raise ValueError('preserved packet changed')
        strict_bytes(data)
        return data
    name = f'cycle-a/n{macros}/step-{step:02d}/science/state-{step:02d}.json'
    state = packet(name)
    comparison = strict_bytes(packet(f'cycle-a/n{macros}/comparison.json'))
    row = comparison['rows'][step-1]
    if row['step'] != step or not (row['slope'] > 0. if step == 1 else row['slope'] < 0.):
        raise ValueError('registered accepted branch position')
    return state, dict(manifest_sha256=MANIFEST_SHA, checkpoint_sha256=sha256(state).hexdigest(),
                      checkpoint_bytes=len(state), source_path=name, accepted_slope=row['slope'])


def validate(value):
    keys = {'schema', 'macros', 'step', 'input', 'poses', 'derivatives', 'native_replay_identical',
            'state_unchanged', 'transformed_global_solve', 'full_spatial_stability',
            'production_qualified', 'independent_review'}
    if type(value) is not dict or set(value) != keys or value['schema'] != SCHEMA:
        raise ValueError('loaded snapshot schema')
    extent(value['macros'], value['step'])
    if any(value[k] is not True for k in ('native_replay_identical', 'state_unchanged')):
        raise ValueError('native replay and unchanged state required')
    if any(value[k] is not False for k in ('transformed_global_solve', 'full_spatial_stability', 'production_qualified')):
        raise ValueError('unsupported qualification claim')
    if value['independent_review'] != 'PENDING':
        raise ValueError('independent review has not occurred')
    _, expected = historical(value['macros'], value['step'])
    if value['input'] != expected: raise ValueError('historical input binding')
    poses = value['poses']
    if type(poses) is not list or [p.get('name') for p in poses] != ['general', 'large-dyadic']:
        raise ValueError('ordered complete poses required')
    def errors(data, names, tolerance):
        if type(data) is not dict or set(data) != set(names): raise ValueError('complete error inventory')
        if any(type(v) is not float or not math.isfinite(v) or not 0. <= v <= tolerance for v in data.values()):
            raise ValueError('error exceeds frozen gate')
    for p in poses:
        if set(p) != {'name', 'elements'} or len(p['elements']) != value['macros']:
            raise ValueError('complete element coverage')
        for e in p['elements']: errors(e, IDENTITIES, 1e-11)
    if len(value['derivatives']) != value['macros']: raise ValueError('complete derivative coverage')
    for rows in value['derivatives']:
        if len(rows) != 9: raise ValueError('three directions by three difference steps')
        for row in rows: errors(row, ('energy', 'chart', 'spatial'), 1e-7)
    canonical(value)


def evaluate(macros, step):
    raw, binding = historical(macros, step)
    import numpy as np
    from fractions import Fraction
    from docs.reference_cases import ge_beam3_retained_arch_case as case
    from docs.reference_cases.ge_beam3_controlled_history_cases import pose, transformed_positions
    from anysolver._ge_beam3_p5_seeded.core import canonical as native_canonical
    from anysolver._ge_beam3_p5.algebra import rotation
    from anysolver._ge_beam3_generalized_static_boundary import spatial_jacobian

    print(dict(stage='native-prefix-replay', macros=macros, step=step), flush=True)
    context = case.arc.Context(case.model(macros), case.program(macros))
    state, records = context.restore(raw, expected_sha256=binding['checkpoint_sha256'])
    if context.checkpoint(records) != raw: raise ValueError('native replay differs')
    before = native_canonical(state)
    # Keep Context-issued authority; transformed snapshots never enter the global
    # clamped model or masquerade as issued equilibrium states.
    context._require_issued(state)
    physical = context.physical
    def error(a, b):
        a, b = np.asarray(a), np.asarray(b)
        return float(np.linalg.norm(a-b))/max(1., float(np.linalg.norm(b)))
    def advanced(x, low, q, u, p, delta):
        h, l = x.copy(), low.copy()
        for n in range(3):
            for j in range(3):
                v = Fraction(float(x[n,j]))+Fraction(float(low[n,j]))+Fraction(float(delta[6*n+j]))
                h[n,j] = float(v); l[n,j] = float(v-Fraction(float(h[n,j])))
        return h, l, np.array([rotation(delta[6*n+3:6*n+6])@q[n] for n in range(3)]), \
            np.array([rotation(delta[18+3*c:21+3*c])@u[c] for c in range(2)]), p+delta[24:]
    poses = [dict(name=n, elements=[]) for n in ('general', 'large-dyadic')]
    derivatives = []
    for i, (_, element) in enumerate(physical.elements):
        nodes = physical.nodes[i]; op = element.operator; origin = state.origins[i]
        args = (state.mechanical.positions[nodes], state.mechanical.position_low[nodes],
                state.mechanical.nodal_frames[nodes], state.mechanical.cell_rotations[i], state.mechanical.resultants[i])
        origin_bytes = native_canonical(origin)
        base = op.evaluate(*args, origin=origin); hessian = base.hessian+base.hessian_low
        jacobian = spatial_jacobian(base.residual, hessian)
        recovery = op.recover(args[3], args[4], origin=origin)
        for result in poses:
            s, t = pose(result['name']); x, low = transformed_positions(args[0], args[1], s, t)
            other = op.evaluate(x, low, s@args[2], s@args[3], args[4], origin=origin)
            transform = np.eye(42); transform[:24,:24] = np.kron(np.eye(8), s)
            d = np.sin(np.arange(42)+.23)*.01
            metrics = dict(potential=error(other.potential, base.potential),
                residual=error(other.residual, transform@base.residual),
                hessian=error(other.hessian+other.hessian_low, transform@hessian@transform.T),
                spatial_jacobian=error(spatial_jacobian(other.residual, other.hessian+other.hessian_low), transform@jacobian@transform.T),
                kinematics=error(other.kinematics, base.kinematics),
                virtual_work=error(other.residual@(transform@d), base.residual@d),
                recovery=0., frame=0., station_work=0., external_virtual_work=0.)
            transformed = op.recover(s@args[3], args[4], origin=origin)
            for a, b in zip(transformed, recovery, strict=True):
                for key in ('strain', 'resultants'):
                    metrics['recovery'] = max(metrics['recovery'], error(a[key]+a[key+'_low'], b[key]+b[key+'_low']))
                metrics['frame'] = max(metrics['frame'], error(a['current_frame'], s@b['current_frame']))
                wa = (a['strain']+a['strain_low'])@(a['resultants']+a['resultants_low'])
                wb = (b['strain']+b['strain_low'])@(b['resultants']+b['resultants_low'])
                metrics['station_work'] = max(metrics['station_work'], error(wa, wb))
                if native_canonical(a['history']) != native_canonical(b['history']): raise ValueError('recovery history changed')
            force = np.array([0., -state.parameter, 0.]); dx = d[:3]
            metrics['external_virtual_work'] = error((s@force)@(s@dx), force@dx)
            if native_canonical(other.history) != native_canonical(base.history): raise ValueError('trial history changed')
            result['elements'].append(metrics)
        rows = []
        # Independent finite differences validate analytic derivatives; they are
        # test diagnostics, never element mechanics or a numerical tangent.
        for phase in (.23, 1.17, 2.31):
            d = np.sin((np.arange(42)+1)*phase)*.01
            for eps in (2e-5, 1e-5, 5e-6):
                a = op.evaluate(*args, origin=origin, increment=eps*d)
                b = op.evaluate(*args, origin=origin, increment=-eps*d)
                plus = op.evaluate(*advanced(*args, eps*d), origin=origin)
                minus = op.evaluate(*advanced(*args, -eps*d), origin=origin)
                rows.append(dict(energy=error((a.potential-b.potential)/(2*eps), base.residual@d),
                    chart=error((a.residual-b.residual)/(2*eps), hessian@d),
                    spatial=error((plus.residual-minus.residual)/(2*eps), jacobian@d)))
        derivatives.append(rows)
        if native_canonical(origin) != origin_bytes: raise ValueError('committed origin changed')
        print(dict(stage='loaded-element-complete', macros=macros, step=step, element=i+1), flush=True)
    context._require_issued(state)
    if native_canonical(state) != before or context.checkpoint(records) != raw: raise ValueError('accepted state changed')
    value = dict(schema=SCHEMA, macros=macros, step=step, input=binding, poses=poses, derivatives=derivatives,
        native_replay_identical=True, state_unchanged=True, transformed_global_solve=False,
        full_spatial_stability=False, production_qualified=False, independent_review='PENDING')
    validate(value)
    return value


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--revision', required=True)
    parser.add_argument('--macros', type=int, required=True); parser.add_argument('--step', type=int, required=True)
    parser.add_argument('--output', required=True); args = parser.parse_args()
    guard(args.revision); historical(args.macros, args.step)
    if subprocess.check_output(['git', 'diff', '--name-only', BASE, 'HEAD', '--', 'src'], cwd=ROOT).strip():
        raise ValueError('this gate cannot change mechanics')
    if sys.flags.optimize or any(os.environ.get(k) != v for k,v in THREAD_ENVIRONMENT.items()):
        raise ValueError('assertions and one numerical thread required')
    target = Path(args.output).resolve()
    if target.is_relative_to(ROOT) or target.exists(): raise ValueError('fresh external output required')
    sys.path.insert(0, str(ROOT/'src'))
    value = evaluate(args.macros, args.step)
    guard(args.revision); historical(args.macros, args.step)
    from docs.reference_cases.ge_beam3_retained_prestress_wave import publish
    publish(target, value)
    print(dict(stage='loaded-evidence-complete'), flush=True)


if __name__ == '__main__': main()
