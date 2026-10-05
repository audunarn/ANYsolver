"""Bounded CalculiX restricted axial material comparator; no qualification claim.

Four SPRING2 halves reproduce only the adopted identity-frame elastic GE axial
potential. CPS4 supplies independent actual plane-stress plastic output.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys

_source = Path(__file__).with_name('r8_e04_restricted_membrane.py')
_spec = importlib.util.spec_from_file_location('restricted_axial_patch', _source)
patch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(patch)

EXE_SHA256 = '27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f'
NATIVE_V3_SHA256 = 'b9e0d3294d2c5cbd9e3763f601d72d869f623fe374e7b84400683d29dfb1032a'
MANUAL = 'https://www.dhondt.de/ccx_2.23.pdf'
PRINT_SOURCE = 'https://raw.githubusercontent.com/Dhondtguido/CalculiX/master/src/printout.f'
PRINT_FORMAT_SOURCES = tuple('https://raw.githubusercontent.com/Dhondtguido/CalculiX/master/src/' + name
                            for name in ('printoutnode.f', 'printoutint.f'))
SPRING_INPUT_SOURCE = 'https://raw.githubusercontent.com/Dhondtguido/CalculiX/master/src/springs.f'
MODES = ('spring-control', 'shell-control', 'full')
SPRINGS = ((3, 101, 102), (4, 102, 103), (5, 104, 105), (6, 105, 106))
K = patch.E * patch.AREA / .5
IP_IDS = tuple((e, p) for e in (1, 2) for p in range(1, 9))
FORCE_GATE_N = 1e-4
WORK_GATE_J = 1e-8
REFERENCE_TOLERANCE = .01
_NUMBER = r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d+)?'
_HEADER = re.compile(r'^\s*(displacements|forces|stresses|strains|equivalent plastic strain)\s*\(([^)]*)\)\s*for set\s+(\w+)\s+and time\s+(' + _NUMBER + r')\s*$', re.I)


class ReferenceError(ValueError):
    pass


class InsufficientPrecision(ReferenceError):
    pass


def expected_nodes(mode):
    if mode == 'spring-control':
        return (101, 102)
    if mode == 'shell-control':
        return patch.SHELL_IDS
    if mode == 'full':
        return patch.SHELL_IDS + tuple(b for _, b in patch.PAIRS)
    raise ValueError('unknown mode')


def deck(mode):
    """Absolute forces in consecutive steps; no nonlinear geometric switch."""
    nodes = expected_nodes(mode)
    lines = ['*HEADING', 'Restricted axial response: CPS4 plus derived elastic half-cell springs', '*NODE']
    for n in nodes:
        if n < 100:
            xyz = patch.SHELL_XYZ[n - 1]
        else:
            xyz = (float((n - 101) % 3) * .5, float((n - 101) // 3) * patch.WIDTH, patch.OFFSET)
        lines.append(','.join((str(n), *(f'{v:.17g}' for v in xyz))))
    lines += ['*NSET,NSET=ALL', ','.join(map(str, nodes))]
    if mode != 'spring-control':
        lines += ['*ELEMENT,TYPE=CPS4,ELSET=SHELL']
        lines += [','.join(map(str, (e, *q))) for e, q in enumerate(patch.QUADS, 1)]
        lines += ['*MATERIAL,NAME=SHELLLAW', '*ELASTIC', f'{patch.E:.17g},{patch.NU:.17g}']
        if mode == 'full':
            lines += ['*PLASTIC,HARDENING=ISOTROPIC', f'{patch.SIG0:.17g},0.',
                      f'{patch.SIG0 + patch.H * .01:.17g},.01']
        lines += ['*SOLID SECTION,ELSET=SHELL,MATERIAL=SHELLLAW', f'{patch.THICKNESS:.17g}']
    if mode != 'shell-control':
        lines += ['*ELEMENT,TYPE=SPRING2,ELSET=AXIAL']
        springs = ((3, 101, 102),) if mode == 'spring-control' else SPRINGS
        lines += [','.join(map(str, row)) for row in springs]
        # springs.f reads only columns 1:20 with F20.0; longer scientific
        # literals silently lose their exponent despite a clean solver exit.
        lines += ['*SPRING,ELSET=AXIAL', '1,1', f'{K:.13e}']
    lines += ['*BOUNDARY']
    if mode != 'spring-control':
        lines += [f'{n},2,2,0.' for n in patch.SHELL_IDS]
        lines += ['1,1,1,0.', '4,1,1,0.']
        # Original CPS4 z is automatically constrained by its expansion.
    if mode != 'shell-control':
        lines += [f'{n},2,3,0.' for n in nodes if n >= 100]
        lines += ['101,1,1,0.']
        if mode == 'full':
            lines += ['104,1,1,0.']
    if mode == 'full':
        for shell, beam in patch.PAIRS:
            if shell not in (1, 4):
                lines += ['*EQUATION', '2', f'{beam},1,1.,{shell},1,-1.']
    factors = patch.TARGETS if mode == 'full' else (patch.TARGETS[0],)
    for factor in factors:
        lines += ['*STEP,INC=100', '*STATIC,DIRECT', '1.,1.', '*CLOAD,OP=NEW']
        if mode == 'spring-control':
            lines += [f'102,1,{factor * patch.FORCE:.17g}']
        else:
            lines += [f'{n},1,{factor * patch.FORCE / 2:.17g}' for n in (3, 6)]
        lines += ['*NODE PRINT,NSET=ALL,FREQUENCY=1,GLOBAL=YES', 'U,RF']
        if mode != 'spring-control':
            lines += ['*EL PRINT,ELSET=SHELL,FREQUENCY=1,GLOBAL=YES',
                      'S,E,PEEQ' if mode == 'full' else 'S,E']
        lines += ['*END STEP']
    text = '\n'.join(lines) + '\n'
    validate_numeric_field_widths(text)
    return text


def validate_numeric_field_widths(text):
    """CCX textpart numeric readers consume at most 20 columns per field."""
    for line_number, line in enumerate(text.splitlines(), 1):
        if line.startswith('*'):
            continue
        for field in line.split(','):
            token = field.strip()
            if re.fullmatch(_NUMBER, token) and len(token) > 20:
                raise ReferenceError(f'numeric input exceeds 20 columns at line {line_number}: {token}')


def printed_number(token):
    """Value and independent half-last-decimal uncertainty of the literal."""
    if not re.fullmatch(_NUMBER, token):
        raise ReferenceError(f'invalid/nonfinite numeric token: {token}')
    normalized = token.upper().replace('D', 'E')
    value = float(normalized)
    if not math.isfinite(value):
        raise ReferenceError('nonfinite printed output')
    mantissa, _, exponent = normalized.partition('E')
    decimals = len(mantissa.partition('.')[2])
    if value == 0. and any(c in '123456789' for c in mantissa):
        raise ReferenceError('nonzero printed literal underflows binary64')
    # Known normalized Fortran scientific output cannot round a representable
    # nonzero value to a zero mantissa at exponent zero. Its printed zero is
    # exact signed zero, unlike a generic fixed-decimal "0" literal.
    if value == 0. and exponent == '+00' and decimals >= 6:
        return value, 0.
    quantum = 10. ** (int(exponent or '0') - decimals)
    if not math.isfinite(quantum) or quantum == 0.:
        raise ReferenceError('printed precision quantum outside supported binary64 range')
    return value, .5 * quantum


def parse_dat(text, mode, partial=None):
    """Strict complete integration-point inventory, preserving valid prefixes."""
    partial = [] if partial is None else partial
    blocks = {}
    active = None
    previous_time = -math.inf
    labels = dict(displacements='U', forces='RF', stresses='S', strains='E',
                  **{'equivalent plastic strain': 'PEEQ'})
    schemas = dict(U=('vx', 'vy', 'vz'), RF=('fx', 'fy', 'fz'),
        S=('elem', 'integ.pnt.', 'sxx', 'syy', 'szz', 'sxy', 'sxz', 'syz'),
        E=('elem', 'integ.pnt.', 'exx', 'eyy', 'ezz', 'exy', 'exz', 'eyz'),
        PEEQ=('elem', 'integ.pnt.', 'pe'))
    required = ('U', 'RF') if mode == 'spring-control' else (
        ('U', 'RF', 'S', 'E', 'PEEQ') if mode == 'full' else ('U', 'RF', 'S', 'E'))
    for line_number, line in enumerate(text.splitlines(), 1):
        match = _HEADER.match(line)
        if match:
            kind = labels[match[1].lower()]
            if kind not in required:
                raise ReferenceError(f'unrequested material/output quantity {kind}')
            columns = tuple(v.strip().lower() for v in match[2].split(','))
            if columns != schemas[kind]:
                raise ReferenceError(f'unknown {kind} component semantics')
            if match[3].upper() != ('ALL' if kind in ('U', 'RF') else 'SHELL'):
                raise ReferenceError('unexpected output set')
            time = printed_number(match[4])[0]
            if time <= 0 or time < previous_time:
                raise ReferenceError('nonpositive or out-of-order total time')
            previous_time = time
            if (time, kind) in blocks:
                raise ReferenceError('duplicate quantity/time block')
            active = dict(time=time, kind=kind, rows={}, rounding={})
            blocks[time, kind] = active
            partial.append(active)
            continue
        stripped = line.strip()
        if not stripped:
            continue
        if 'for set' in line.lower() or '*error' in line.lower():
            raise ReferenceError(f'unknown/failed output header at line {line_number}')
        tokens = stripped.split()
        if active is not None and re.match(r'^[+-]?\d', tokens[0]):
            kind = active['kind']
            ids = 1 if kind in ('U', 'RF') else 2
            count = (3 if ids == 1 else (1 if kind == 'PEEQ' else 6)) + ids
            if len(tokens) != count or any(not token.isdigit() for token in tokens[:ids]):
                raise ReferenceError(f'incomplete/unknown numeric row at line {line_number}')
            key = int(tokens[0]) if ids == 1 else tuple(map(int, tokens[:2]))
            if key in active['rows']:
                raise ReferenceError('duplicate node/material point')
            values = tuple(printed_number(token) for token in tokens[ids:])
            if any('E' not in token.upper() and 'D' not in token.upper() for token in tokens[ids:]):
                raise ReferenceError('unsupported missing exponent in scientific output row')
            active['rows'][key] = tuple(v for v, _ in values)
            active['rounding'][key] = tuple(r for _, r in values)
        elif active is not None:
            active = None
    times = sorted({time for time, _ in blocks})
    endpoints = tuple(float(i) for i in range(1, len(patch.TARGETS) + 1)) if mode == 'full' else (1.,)
    if not times or times[-1] != endpoints[-1] or any(t > endpoints[-1] for t in times):
        raise ReferenceError('missing or unexpected final total step time')
    for time in times:
        for kind in required:
            block = blocks.get((time, kind))
            expected = set(expected_nodes(mode) if kind in ('U', 'RF') else IP_IDS)
            if block is None or set(block['rows']) != expected:
                raise ReferenceError(f'incomplete {kind} node/material inventory at time {time}')
    if any(t not in times for t in endpoints):
        raise ReferenceError('missing ordered step endpoint inventory')
    return [dict(time=t, **{kind: blocks[t, kind] for kind in required}) for t in endpoints]


def clean_execution(returncode, stdout, stderr):
    log = stdout + '\n' + stderr
    if returncode != 0 or 'Job finished' not in stdout or re.search(
            r'\*ERROR|\bFATAL\b|no convergence|too many cutbacks', log, re.I):
        raise ReferenceError('CalculiX did not finish cleanly; raw logs retained')


def parse_sta(text, mode):
    rows = []
    for line in text.splitlines():
        tokens = line.split()
        if not tokens or not tokens[0].isdigit():
            continue
        if len(tokens) != 7 or not all(t.isdigit() for t in tokens[:4]):
            raise ReferenceError('unknown accepted-increment STA inventory')
        step, increment, attempt, iterations = map(int, tokens[:4])
        total_time, step_time, increment_time = (printed_number(t)[0] for t in tokens[4:])
        if min(step, increment, attempt) <= 0 or iterations < 0 or min(total_time, step_time, increment_time) <= 0:
            raise ReferenceError('invalid accepted increment/time')
        if rows and (total_time <= rows[-1]['total_time'] or (step, increment) <= (rows[-1]['step'], rows[-1]['increment'])):
            raise ReferenceError('duplicate/out-of-order accepted increments')
        rows.append(dict(step=step, increment=increment, attempt=attempt, iterations=iterations,
                         total_time=total_time, step_time=step_time, increment_time=increment_time))
    count = len(patch.TARGETS) if mode == 'full' else 1
    if not rows or {r['step'] for r in rows} != set(range(1, count + 1)) or rows[-1]['total_time'] != count:
        raise ReferenceError('incomplete accepted increment history')
    matched = len(rows) == count and all(r['step'] == i and r['increment'] == 1
        and r['step_time'] == 1. and r['increment_time'] == 1. and r['total_time'] == float(i)
        for i, r in enumerate(rows, 1))
    return dict(accepted_increments=rows, matched_one_increment_per_native_target=matched)


def uncertain_check(residual, rounding, tolerance, label):
    if abs(residual) - rounding > tolerance:
        raise ReferenceError(f'{label}: measured residual {residual:g}, printed uncertainty {rounding:g}')
    if abs(residual) + rounding > tolerance:
        raise InsufficientPrecision(f'{label}: uncertainty interval cannot certify physical threshold {tolerance:g}; residual={residual:g}, rounding={rounding:g}')


def controls(records, mode):
    row = records[0]
    force = patch.TARGETS[0] * patch.FORCE
    if mode == 'spring-control':
        u = row['U']['rows']
        expected = force / K
        measured = u[102][0] - u[101][0]
        bound = row['U']['rounding'][102][0] + row['U']['rounding'][101][0]
        uncertain_check(measured - expected, bound, expected * REFERENCE_TOLERANCE, 'bare SPRING2 k control')
        # RF is a reaction only at this unloaded root.
        uncertain_check(row['RF']['rows'][101][0] + force,
            row['RF']['rounding'][101][0], force * REFERENCE_TOLERANCE, 'bare spring root reaction')
        return dict(control_pass=True, spring_stiffness_n_per_m=K,
                    measured_extension_m=measured, expected_extension_m=expected)
    modulus = patch.E / (1 - patch.NU**2)
    expected = force / (patch.WIDTH * patch.THICKNESS * modulus)
    return shell_observables(row, patch.TARGETS[0], mode, elastic_expected=expected)


def shell_observables(record, factor, mode='full', elastic_expected=None):
    """Actual CPS4 tensor strain/stress/PEEQ and exact reduced spring work."""
    u = record['U']['rows']
    ub = record['U']['rounding']
    epsilon = (u[3][0] + u[6][0]) / (2 * patch.LENGTH)
    eps_bound = (ub[3][0] + ub[6][0]) / (2 * patch.LENGTH)
    for n in patch.SHELL_IDS:
        x = patch.SHELL_XYZ[n - 1][0]
        uncertain_check(u[n][0] - epsilon * x, ub[n][0] + eps_bound * x, 1e-10, 'affine shell extension')
        uncertain_check(u[n][1], ub[n][1], 1e-10, 'fixed shell transverse displacement')
        uncertain_check(u[n][2], ub[n][2], 1e-10, 'actual original shell out-of-plane displacement')
    stress = record['S']['rows']
    strain = record['E']['rows']
    layers = []
    uniform_stress_precision_insufficient = False
    for key in IP_IDS:
        s, e = stress[key], strain[key]
        sb, eb = record['S']['rounding'][key], record['E']['rounding'][key]
        # .dat E contains tensor shears; convert to engineering xy once.
        uncertain_check(e[0] - epsilon, eb[0] + eps_bound, 1e-10, 'material axial strain')
        for j in (1, 3, 4, 5):
            uncertain_check(e[j], eb[j], 1e-10, 'zero transverse/shear strain')
        uncertain_check(s[2], sb[2], .01, 'actual plane stress sigma_zz')
        for j in (3, 4, 5):
            uncertain_check(s[j], sb[j], .01, 'actual zero shear stress')
        for j in range(6):
            residual = s[j] - stress[IP_IDS[0]][j]
            bound = sb[j] + record['S']['rounding'][IP_IDS[0]][j]
            if abs(residual) > .01 + bound:
                raise ReferenceError('nonuniform shell material stress beyond independent print bounds')
            uniform_stress_precision_insufficient |= abs(residual) + bound > .01
        layer = dict(element=key[0], point=key[1], stress=s, tensor_strain=e,
                     engineering_strain=(e[0], e[1], 2 * e[3]))
        if mode == 'full':
            alpha = record['PEEQ']['rows'][key][0]
            if not 0 <= alpha < .01:
                raise ReferenceError('actual PEEQ outside matched material branch')
            layer['actual_peeq'] = alpha
        layers.append(layer)
    sx = math.fsum(s[0] for s in stress.values()) / len(stress)
    sx_bound = math.fsum(b[0] for b in record['S']['rounding'].values()) / len(stress)
    if elastic_expected is not None:
        scale = patch.E / (1 - patch.NU**2)
        uncertain_check(epsilon - elastic_expected, eps_bound, elastic_expected * REFERENCE_TOLERANCE, 'elastic CPS4 axial modulus')
        for key in IP_IDS:
            for j, expected in enumerate((scale * elastic_expected, patch.NU * scale * elastic_expected)):
                uncertain_check(stress[key][j] - expected, record['S']['rounding'][key][j],
                                abs(expected) * REFERENCE_TOLERANCE, 'elastic CPS4 stress control')
    beam_work = 0.
    beam_work_bound = 0.
    beam_force_bound = 0.
    if mode == 'full':
        for shell, beam in patch.PAIRS:
            uncertain_check(u[beam][0] - u[shell][0], ub[beam][0] + ub[shell][0], 1e-10, 'exact reduced axial bond')
            for j in (1, 2):
                uncertain_check(u[beam][j], ub[beam][j], 1e-10, 'fixed beam transverse coordinate')
        for _, left, right in SPRINGS:
            extension = u[right][0] - u[left][0]
            bound = ub[right][0] + ub[left][0]
            beam_work += K * extension**2
            beam_work_bound += K * (2 * abs(extension) * bound + bound**2)
        beam_force_bound = 2 * patch.E * patch.AREA * eps_bound
    shell_work = patch.WIDTH * patch.THICKNESS * patch.LENGTH * sx * epsilon
    shell_work_bound = patch.WIDTH * patch.THICKNESS * patch.LENGTH * (
        abs(sx) * eps_bound + abs(epsilon) * sx_bound + sx_bound * eps_bound)
    external_work = factor * patch.FORCE * patch.LENGTH * epsilon
    work_bound = shell_work_bound + beam_work_bound + factor * patch.FORCE * patch.LENGTH * eps_bound
    force_residual = patch.WIDTH * patch.THICKNESS * sx + (
        2 * patch.E * patch.AREA * epsilon if mode == 'full' else 0.) - factor * patch.FORCE
    force_bound = patch.WIDTH * patch.THICKNESS * sx_bound + beam_force_bound
    result = dict(time=record['time'], factor=factor, engineering_axial_strain=epsilon,
        axial_strain_print_bound=eps_bound, layer_stress_pa=(sx,
            math.fsum(s[1] for s in stress.values()) / len(stress),
            math.fsum(s[3] for s in stress.values()) / len(stress)),
        shell_stress_print_bound_pa=sx_bound, actual_layers=layers,
        layer_stress_print_bounds_pa=tuple(math.fsum(b[j] for b in record['S']['rounding'].values()) / len(stress)
                                          for j in (0, 1, 3)),
        shell_axial_virtual_work_j=shell_work, derived_beam_axial_virtual_work_j=beam_work,
        external_virtual_work_j=external_work, axial_force_residual_n=force_residual,
        axial_force_print_bound_n=force_bound,
        virtual_work_residual_j=shell_work + beam_work - external_work,
        virtual_work_print_bound_j=work_bound,
        uniform_stress_precision_insufficient=uniform_stress_precision_insufficient,
        control_pass=elastic_expected is not None, full_support_wrench_claimed=False,
        unsupported_quantities=('general beam moments', 'beam fibre stresses', 'full support wrench'))
    if mode == 'full':
        roots = (1, 4, 101, 104)
        result.update(actual_root_axial_rf_n={n: record['RF']['rows'][n][0] for n in roots},
            root_axial_reaction_residual_n=math.fsum(record['RF']['rows'][n][0] for n in roots) + factor * patch.FORCE,
            root_axial_reaction_print_bound_n=math.fsum(record['RF']['rounding'][n][0] for n in roots))
    # Retain measured values before a precision failure through the caller.
    return result


def validate_balances(row):
    uncertain_check(row['axial_force_residual_n'], row['axial_force_print_bound_n'], FORCE_GATE_N, 'axial force balance')
    uncertain_check(row['virtual_work_residual_j'], row['virtual_work_print_bound_j'], WORK_GATE_J, 'endpoint virtual work')
    uncertain_check(row['root_axial_reaction_residual_n'], row['root_axial_reaction_print_bound_n'], FORCE_GATE_N, 'actual unloaded-root axial reaction sum')


def balance_checks(row):
    checks = {}
    for label, residual, bound, threshold in (
        ('material_axial_balance', row['axial_force_residual_n'], row['axial_force_print_bound_n'], FORCE_GATE_N),
        ('endpoint_virtual_work', row['virtual_work_residual_j'], row['virtual_work_print_bound_j'], WORK_GATE_J),
        ('actual_root_axial_reactions', row['root_axial_reaction_residual_n'], row['root_axial_reaction_print_bound_n'], FORCE_GATE_N)):
        try:
            uncertain_check(residual, bound, threshold, label)
            checks[label] = dict(status='PASS', residual=residual, independent_print_bound=bound, physical_threshold=threshold)
        except InsufficientPrecision as exc:
            checks[label] = dict(status='INSUFFICIENT_PRINT_PRECISION', residual=residual,
                independent_print_bound=bound, physical_threshold=threshold, reason=str(exc))
    return checks


def compare(native, external):
    if len(native) != len(patch.TARGETS) or len(external) != len(patch.TARGETS):
        raise ReferenceError('complete matched eight-step history required')
    elastic_eps = patch.TARGETS[0] * patch.FORCE / (
        patch.WIDTH * patch.THICKNESS * patch.E / (1 - patch.NU**2) + 2 * patch.E * patch.AREA)
    elastic_stress = patch.E / (1 - patch.NU**2) * elastic_eps
    answer = []
    for target, n, e in zip(patch.TARGETS, native, external, strict=True):
        if n['factor'] != target or e['factor'] != target:
            raise ReferenceError('reference factor history mismatch')
        if len(n['layer_stress_pa']) != 3 or len(e['layer_stress_pa']) != 3:
            raise ReferenceError('complete actual membrane stress components required')
        values = []
        for name, measured, reference, bound, floor in (
            ('axial_strain', e['engineering_axial_strain'], n['engineering_axial_strain'], e['axial_strain_print_bound'], elastic_eps),
            ('sigma_xx', e['layer_stress_pa'][0], n['layer_stress_pa'][0], e['layer_stress_print_bounds_pa'][0], elastic_stress),
            ('sigma_yy', e['layer_stress_pa'][1], n['layer_stress_pa'][1], e['layer_stress_print_bounds_pa'][1], patch.NU * elastic_stress)):
            if not all(map(math.isfinite, (measured, reference, bound, floor))) or bound < 0:
                raise ReferenceError('finite comparison quantities and nonnegative print bounds required')
            scale = max(abs(reference), abs(floor))
            if bound > REFERENCE_TOLERANCE * scale:
                raise InsufficientPrecision('printed uncertainty cannot resolve prospective 1% response screen')
            difference = measured - reference
            values.append(dict(quantity=name, difference=difference,
                print_bound=bound, exact_elastic_floor=floor, denominator=scale,
                normalized_difference=abs(difference) / scale,
                within_one_percent_response_screen=abs(difference) + bound <= REFERENCE_TOLERANCE * scale))
        answer.append(dict(factor=target, quantities=values))
    return answer


def json_safe(value):
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [json_safe(v) for v in value]
    return value


def save(path, value):
    path.write_text(json.dumps(json_safe(value), indent=2, allow_nan=False), encoding='utf-8')


def control_authority(path, mode):
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('status') != 'COMPLETED_CONTROL' or data.get('mode') != mode or data.get('exe_sha256') != EXE_SHA256:
        raise ReferenceError(f'completed pinned {mode} evidence required before full history')
    if data.get('fixture_signature_sha256') != patch.fixture_signature() or data.get('deck_sha256') != sha256(deck(mode).encode('ascii')).hexdigest():
        raise ReferenceError('control evidence belongs to a different fixture or deck')
    return sha256(path.read_bytes()).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=MODES, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--exe', type=Path)
    parser.add_argument('--timeout-seconds', type=int, default=600)
    parser.add_argument('--native-input', type=Path)
    parser.add_argument('--spring-control-json', type=Path)
    parser.add_argument('--shell-control-json', type=Path)
    args = parser.parse_args(argv)
    if not 1 <= args.timeout_seconds <= 600:
        parser.error('timeout must lie in [1,600] seconds')
    args.output.mkdir(parents=True, exist_ok=False)
    text = deck(args.mode)
    (args.output / 'reference.inp').write_bytes(text.encode('ascii'))
    status = dict(status='DECK_PREPARED', mode=args.mode, qualified=False,
        e04_external_row_closed=False, manual=MANUAL, output_source=PRINT_SOURCE,
        output_format_sources=PRINT_FORMAT_SOURCES,
        spring_input_source=SPRING_INPUT_SOURCE,
        script_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        patch_source_sha256=sha256(_source.read_bytes()).hexdigest(),
        fixture_signature_sha256=patch.fixture_signature(),
        deck_sha256=sha256(text.encode('ascii')).hexdigest(),
        python=sys.executable, python_version=sys.version)
    partial = []
    observables = []
    save(args.output / 'status.json', status)
    if args.exe is None:
        return
    try:
        if sha256(args.exe.read_bytes()).hexdigest() != EXE_SHA256:
            raise ReferenceError('unapproved CalculiX executable SHA256')
        status['exe_sha256'] = EXE_SHA256
        environment = {k: os.environ.get(k) for k in (
            'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
            'NUMEXPR_NUM_THREADS', 'NUMBER_OF_CPUS')}
        status['numerical_environment'] = environment
        if any(environment[k] != '1' for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
                                               'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS')):
            raise ReferenceError('supervised numerical environment must be one thread')
        if args.mode == 'full':
            if args.spring_control_json is None or args.shell_control_json is None or args.native_input is None:
                raise ReferenceError('full history requires completed spring/shell controls and actual native input')
            status['control_status_sha256'] = dict(
                spring=control_authority(args.spring_control_json, 'spring-control'),
                shell=control_authority(args.shell_control_json, 'shell-control'))
        status['status'] = 'IN_PROGRESS'
        save(args.output / 'status.json', status)
        with (args.output / 'stdout.log').open('wb') as stdout, (args.output / 'stderr.log').open('wb') as stderr:
            result = subprocess.run([str(args.exe.resolve()), '-i', 'reference'], cwd=args.output,
                stdout=stdout, stderr=stderr, timeout=args.timeout_seconds, check=False)
        status['returncode'] = result.returncode
        clean_execution(result.returncode, (args.output / 'stdout.log').read_text(errors='replace'),
                        (args.output / 'stderr.log').read_text(errors='replace'))
        records = parse_dat((args.output / 'reference.dat').read_text(errors='strict'), args.mode, partial)
        save(args.output / 'parsed.json', records)
        increments = parse_sta((args.output / 'reference.sta').read_text(errors='strict'), args.mode)
        status.update(increments)
        save(args.output / 'accepted-increments.json', increments)
        if args.mode != 'full':
            observed = controls(records, args.mode)
            save(args.output / 'control.json', observed)
            status['status'] = 'COMPLETED_CONTROL'
        else:
            for factor, row in zip(patch.TARGETS, records, strict=True):
                expected = (patch.TARGETS[0] * patch.FORCE / (
                    patch.WIDTH * patch.THICKNESS * patch.E / (1 - patch.NU**2)
                    + 2 * patch.E * patch.AREA)) if not observables else None
                observed = shell_observables(row, factor, elastic_expected=expected)
                observables.append(observed)
                save(args.output / 'actual-observables.json', observables)
                observed['balance_checks'] = balance_checks(observed)
                observed['tight_balance_check'] = ('PASS' if all(r['status'] == 'PASS'
                    for r in observed['balance_checks'].values()) else 'INSUFFICIENT_PRINT_PRECISION')
                save(args.output / 'actual-observables.json', observables)
            peeq = [r['actual_peeq'] for row in observables for r in row['actual_layers']]
            if not peeq or max(peeq) <= 0.:
                raise ReferenceError('actual CPS4 PEEQ never activated')
            for left, right in zip(observables, observables[1:]):
                if any(b['actual_peeq'] < a['actual_peeq'] for a, b in zip(left['actual_layers'], right['actual_layers'], strict=True)):
                    raise ReferenceError('actual PEEQ decreased along uninterrupted history')
            native, native_status = patch.read_completed_input(args.native_input, 'native')
            signature = native_status.get('fixture_signature_sha256')
            if signature is None:
                if native_status.get('script_sha256') != NATIVE_V3_SHA256:
                    raise ReferenceError('unsigned native input must be pinned executed v3 source')
            elif signature != patch.fixture_signature():
                raise ReferenceError('native reference physical/history fixture differs')
            status['native_input_sha256'] = sha256(args.native_input.read_bytes()).hexdigest()
            comparison = compare(native, observables)
            save(args.output / 'comparison.json', comparison)
            status['one_percent_response_screen_pass'] = all(q['within_one_percent_response_screen']
                for row in comparison for q in row['quantities'])
            status['tight_balance_precision_insufficient'] = any(r['tight_balance_check'] != 'PASS' for r in observables)
            status['uniform_stress_precision_insufficient'] = any(r['uniform_stress_precision_insufficient'] for r in observables)
            status['status'] = ('PARTIAL_EVIDENCE' if status['tight_balance_precision_insufficient']
                or status['uniform_stress_precision_insufficient'] or not increments['matched_one_increment_per_native_target']
                else 'COMPLETED_RESTRICTED_REFERENCE') if status['one_percent_response_screen_pass'] else 'RESPONSE_SCREEN_FAILED'
    except BaseException as exc:
        status.update(status='NUMERICAL_NON_SUCCESS', error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        save(args.output / 'partial-parser-prefix.json', partial)
        save(args.output / 'status.json', status)


if __name__ == '__main__':
    main()
