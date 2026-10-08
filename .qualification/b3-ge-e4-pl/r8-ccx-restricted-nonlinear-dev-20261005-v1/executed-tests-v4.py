"""Pure deck/parser/output contracts; numerical jobs belong to the orchestrator."""
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


def module():
    path = Path(__file__).parents[1] / 'scripts' / 'r8_e04_ccx_restricted_membrane.py'
    spec = importlib.util.spec_from_file_location('ccx_axial_patch', path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def dat_fixture(m, mode='full', precision=12):
    lines = []
    factors = m.patch.TARGETS if mode == 'full' else (m.patch.TARGETS[0],)
    headers = dict(U='displacements (vx,vy,vz)', RF='forces (fx,fy,fz)',
        S='stresses (elem, integ.pnt.,sxx,syy,szz,sxy,sxz,syz)',
        E='strains (elem, integ.pnt.,exx,eyy,ezz,exy,exz,eyz)',
        PEEQ='equivalent plastic strain (elem, integ.pnt.,pe)')
    for time, factor in enumerate(factors, 1):
        force = factor * m.patch.FORCE
        modulus = m.patch.E / (1 - m.patch.NU**2)
        stiffness = m.patch.WIDTH * m.patch.THICKNESS * modulus
        if mode == 'full':
            stiffness += 2 * m.patch.E * m.patch.AREA
        epsilon = force / stiffness
        quantities = ('U', 'RF') if mode == 'spring-control' else (
            ('U', 'RF', 'S', 'E', 'PEEQ') if mode == 'full' else ('U', 'RF', 'S', 'E'))
        for kind in quantities:
            lines += [f'{headers[kind]} for set {"ALL" if kind in ("U", "RF") else "SHELL"} and time {time:.7e}', '']
            if kind in ('U', 'RF'):
                for n in m.expected_nodes(mode):
                    if kind == 'U':
                        x = m.patch.SHELL_XYZ[n - 1][0] if n < 100 else ((n - 101) % 3) * .5
                        values = (force / m.K if mode == 'spring-control' and n == 102 else
                                  (0. if mode == 'spring-control' else epsilon * x), 0., 0.)
                    else:
                        values = (-force if mode == 'spring-control' and n == 101 else 0., 0., 0.)
                    lines.append(str(n) + ' ' + ' '.join(f'{v:.{precision}e}' for v in values))
            else:
                for e, point in m.IP_IDS:
                    if kind == 'S':
                        values = (modulus * epsilon, m.patch.NU * modulus * epsilon, 0., 0., 0., 0.)
                    elif kind == 'E':
                        values = (epsilon, 0., -m.patch.NU / m.patch.E * modulus * epsilon * (1 + m.patch.NU), 0., 0., 0.)
                    else:
                        values = (0.,)
                    lines.append(f'{e} {point} ' + ' '.join(f'{v:.{precision}e}' for v in values))
            lines.append('')
    return '\n'.join(lines)


def test_full_deck_uses_exact_reduction_and_uninterrupted_absolute_history():
    m = module()
    text = m.deck('full')
    assert text.count('*STEP,') == 8
    assert text.count('*STATIC,DIRECT\n1.,1.') == 8
    assert text.count('*CLOAD,OP=NEW') == 8
    assert text.count('*EQUATION') == 4
    spring_constant = text.split('*SPRING,ELSET=AXIAL\n1,1\n')[1].splitlines()[0]
    assert '.' in spring_constant and float(spring_constant) == pytest.approx(m.K)
    assert '*PLASTIC,HARDENING=ISOTROPIC\n1000000,0.\n2000000,.01' in text
    assert '*SOLID SECTION,ELSET=SHELL,MATERIAL=SHELLLAW\n0.002' in text
    assert all(word not in text for word in ('NLGEOM', 'RIGID BODY', 'TYPE=U1', 'TYPE=T3D2'))
    boundary = text.split('*BOUNDARY\n')[1].split('*EQUATION')[0]
    restraints = [tuple(line.split(',')) for line in boundary.splitlines() if line.strip()]
    assert all(not (int(node) in m.patch.SHELL_IDS and int(first) <= 3 <= int(last))
               for node, first, last, value in restraints)
    assert '101,0,0,0.01' in text and '104,0,0.10000000000000001,0.01' in text


def test_parser_requires_complete_actual_material_history():
    m = module()
    records = m.parse_dat(dat_fixture(m), 'full')
    assert [r['time'] for r in records] == list(range(1, 9))
    assert all(len(r[k]['rows']) == 16 for r in records for k in ('S', 'E', 'PEEQ'))
    assert len(records[0]['U']['rows']) == 12
    assert all(len(r['S']['rows'][1, 1]) == 6 for r in records)


@pytest.mark.parametrize('change, message', (
    ('missing_peeq', 'incomplete PEEQ'), ('duplicate', 'duplicate node'),
    ('missing_point', 'material inventory'), ('extra_point', 'material inventory'),
    ('nonfinite', 'invalid/nonfinite'), ('wrong_time', 'out-of-order'),
    ('wrong_components', 'component semantics')))
def test_parser_rejects_corrupt_or_incomplete_evidence(change, message):
    m = module()
    text = dat_fixture(m)
    if change == 'missing_peeq':
        begin = text.index('equivalent plastic strain')
        end = text.index('displacements', begin)
        text = text[:begin] + text[end:]
    elif change == 'duplicate':
        first = text.splitlines()[2]
        text = text.replace(first, first + '\n' + first, 1)
    elif change == 'missing_point':
        lines = text.splitlines()
        index = next(i for i, line in enumerate(lines) if line.startswith('1 8 '))
        del lines[index]
        text = '\n'.join(lines)
    elif change == 'extra_point':
        first = next(line for line in text.splitlines() if line.startswith('1 8 '))
        text = text.replace(first, first + '\n' + first.replace('1 8 ', '1 9 ', 1), 1)
    elif change == 'nonfinite':
        first = text.splitlines()[2]
        text = text.replace(first, '1 nan 0.000000000000e+00 0.000000000000e+00', 1)
    elif change == 'wrong_time':
        text = text.replace('and time 2.0000000e+00', 'and time 5.0000000e-01', 1)
    else:
        text = text.replace('exx,eyy,ezz,exy,exz,eyz', 'exx,eyy,ezz,gxy,gxz,gyz', 1)
    partial = []
    with pytest.raises(m.ReferenceError, match=message):
        m.parse_dat(text, 'full', partial)
    assert partial


def test_analytical_controls_are_independent_of_native_response():
    m = module()
    for mode in ('spring-control', 'shell-control'):
        observed = m.controls(m.parse_dat(dat_fixture(m, mode), mode), mode)
        assert observed['control_pass']
    rows = m.parse_dat(dat_fixture(m, 'shell-control'), 'shell-control')
    rows[0]['S']['rows'][1, 1] = (1.,) * 6
    with pytest.raises(m.ReferenceError):
        m.controls(rows, 'shell-control')


def test_rounding_bound_is_literal_and_cannot_weaken_physical_gate():
    m = module()
    value, bound = m.printed_number('1.234567D+06')
    assert value == 1234567 and bound == .5
    assert m.printed_number('0.000000E+00') == (0., 0.)
    assert m.printed_number('-0.000000D+00') == (0., 0.)
    assert m.printed_number('0')[1] == .5
    with pytest.raises(m.ReferenceError, match='underflows'):
        m.printed_number('1.000000E-999')
    with pytest.raises(m.InsufficientPrecision, match='physical threshold'):
        m.uncertain_check(0., 2e-4, 1e-4, 'balance')
    with pytest.raises(m.InsufficientPrecision, match='cannot certify'):
        m.uncertain_check(.8e-4, .4e-4, 1e-4, 'ambiguous interval')
    with pytest.raises(m.ReferenceError, match='measured residual'):
        m.uncertain_check(2e-4, .4e-4, 1e-4, 'actual mismatch')
    records = m.parse_dat(dat_fixture(m, precision=6), 'full')
    row = m.shell_observables(records[-1], 1.)
    assert row['uniform_stress_precision_insufficient']
    assert row['actual_layers'][0]['actual_peeq'] == 0.


def test_accepted_increment_inventory_distinguishes_native_target_path():
    m = module()
    text = 'STEP INC ATT ITRS TOT TIME STEP TIME INC TIME\n' + '\n'.join(
        f'{i} 1 1 2 {float(i):.6e} 1.000000e+00 1.000000e+00' for i in range(1, 9))
    assert m.parse_sta(text, 'full')['matched_one_increment_per_native_target']
    text = text.replace('1 1 1 2 1.000000e+00 1.000000e+00 1.000000e+00',
        '1 1 1 2 5.000000e-01 5.000000e-01 5.000000e-01\n1 2 1 2 1.000000e+00 1.000000e+00 5.000000e-01')
    assert not m.parse_sta(text, 'full')['matched_one_increment_per_native_target']


def test_failed_execution_is_never_success_and_raw_logs_survive(tmp_path, monkeypatch):
    m = module()
    exe = tmp_path / 'fake.exe'
    exe.write_bytes(b'test-only executable identity')
    monkeypatch.setattr(m, 'EXE_SHA256', sha256(exe.read_bytes()).hexdigest())
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        monkeypatch.setenv(name, '1')
    def failed(*args, stdout, stderr, **kwargs):
        stdout.write(b'*ERROR: nonlinear failure\nJob finished\n')
        stderr.write(b'failed mechanics retained\n')
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(m.subprocess, 'run', failed)
    output = tmp_path / 'failed'
    with pytest.raises(m.ReferenceError, match='finish cleanly'):
        m.main(['--mode', 'spring-control', '--exe', str(exe), '--output', str(output)])
    assert json.loads((output / 'status.json').read_text())['status'] == 'NUMERICAL_NON_SUCCESS'
    assert 'failed mechanics retained' in (output / 'stderr.log').read_text()
    assert (output / 'reference.inp').exists()


def test_reference_response_screen_uses_exact_elastic_floor_and_bounds():
    m = module()
    native = [dict(factor=f, engineering_axial_strain=1e-5,
                   layer_stress_pa=(1e6, .3e6, 0.)) for f in m.patch.TARGETS]
    external = [dict(r, axial_strain_print_bound=1e-12,
                     shell_stress_print_bound_pa=.5,
                     layer_stress_print_bounds_pa=(.5, .5, 0.)) for r in native]
    comparison = m.compare(native, external)
    assert all(q['within_one_percent_response_screen'] for r in comparison for q in r['quantities'])
    external[0]['engineering_axial_strain'] = 1.02e-5
    assert not m.compare(native, external)[0]['quantities'][0]['within_one_percent_response_screen']


def test_actual_root_reactions_are_separate_from_material_balance():
    m = module()
    records = m.parse_dat(dat_fixture(m), 'full')
    for n in (1, 4, 101, 104):
        records[0]['RF']['rows'][n] = (-m.patch.TARGETS[0] * m.patch.FORCE / 4, 0., 0.)
    row = m.shell_observables(records[0], m.patch.TARGETS[0])
    assert row['root_axial_reaction_residual_n'] == pytest.approx(0.)
    assert m.balance_checks(row)['actual_root_axial_reactions']['status'] == 'PASS'
    row['root_axial_reaction_residual_n'] = 1.
    with pytest.raises(m.ReferenceError, match='actual_root_axial_reactions'):
        m.balance_checks(row)


def test_control_evidence_binds_exact_fixture_and_deck(tmp_path):
    m = module()
    path = tmp_path / 'control-status.json'
    record = dict(status='COMPLETED_CONTROL', mode='spring-control', exe_sha256=m.EXE_SHA256,
                  fixture_signature_sha256=m.patch.fixture_signature(),
                  deck_sha256=sha256(m.deck('spring-control').encode('ascii')).hexdigest())
    m.save(path, record)
    assert len(m.control_authority(path, 'spring-control')) == 64
    record['deck_sha256'] = 'a' * 64
    m.save(path, record)
    with pytest.raises(m.ReferenceError, match='different fixture or deck'):
        m.control_authority(path, 'spring-control')


def test_observed_original_shell_uz_is_required_zero():
    m = module()
    records = m.parse_dat(dat_fixture(m, 'shell-control'), 'shell-control')
    u = records[0]['U']['rows'][2]
    records[0]['U']['rows'][2] = (u[0], u[1], 1e-6)
    with pytest.raises(m.ReferenceError, match='out-of-plane displacement'):
        m.controls(records, 'shell-control')


def test_comparison_uses_each_stress_components_own_print_exponent():
    m = module()
    sx, bx = m.printed_number('-2.381900E+04')
    sy, by = m.printed_number('1.194000E+05')
    assert by == pytest.approx(10 * bx)
    native = [dict(factor=f, engineering_axial_strain=1e-5,
                   layer_stress_pa=(sx, sy, 0.)) for f in m.patch.TARGETS]
    external = [dict(r, axial_strain_print_bound=1e-12, shell_stress_print_bound_pa=bx,
                     layer_stress_print_bounds_pa=(bx, by, 0.)) for r in native]
    quantities = m.compare(native, external)[0]['quantities']
    assert quantities[1]['print_bound'] == bx
    assert quantities[2]['print_bound'] == by


def test_all_numeric_input_fields_fit_actual_ccx_twenty_column_readers():
    m = module()
    for mode in m.MODES:
        text = m.deck(mode)
        fields = [token.strip() for line in text.splitlines() if not line.startswith('*')
                  for token in line.split(',') if m.re.fullmatch(m._NUMBER, token.strip())]
        assert fields and all(len(token) <= 20 for token in fields)
        if mode != 'shell-control':
            literal = text.split('*SPRING,ELSET=AXIAL\n1,1\n')[1].splitlines()[0]
            assert '.' in literal and float(literal[:20]) == pytest.approx(m.K)
    truncated = f'{m.K:.17e}'
    assert len(truncated) > 20 and truncated[:20].lower().endswith('e')
    assert float(truncated[:20].split('e')[0]) != pytest.approx(m.K)
    with pytest.raises(m.ReferenceError, match='exceeds 20 columns'):
        m.validate_numeric_field_widths('*SPRING,ELSET=AXIAL\n1,1\n' + truncated + '\n')


def test_iteration_diagnostic_changes_only_the_adopted_time_controls():
    m = module()
    original = m.deck('full')
    diagnostic = m.deck('full', iteration_diagnostic=True)
    card = '\n'.join(m.ITERATION_DIAGNOSTIC_LINES) + '\n'
    assert diagnostic.count(card) == 8
    assert diagnostic.replace(card, '') == original
    assert '*CONTROLS' not in original and 'PARAMETERS=FIELD' not in diagnostic
    assert sha256(original.encode('ascii')).hexdigest() != sha256(diagnostic.encode('ascii')).hexdigest()
    fields = m.ITERATION_DIAGNOSTIC_LINES[1].split(',')
    assert fields == ['25', '25', '25', '24', '10', '4', '0', '5', '0', '0']
    assert m.ITERATION_DIAGNOSTIC_LINES[2].split(',') == ['0.25', '0.5', '0.75', '0.85', '0.', '0.', '1.5', '0.']


def test_iteration_diagnostic_is_full_only_and_records_diagnostic_status(tmp_path):
    m = module()
    for mode in ('spring-control', 'shell-control'):
        with pytest.raises(ValueError, match='only for full'):
            m.deck(mode, iteration_diagnostic=True)
        invalid = tmp_path / mode
        with pytest.raises(SystemExit) as caught:
            m.main(['--mode', mode, '--iteration-diagnostic', '--output', str(invalid)])
        assert caught.value.code == 2 and not invalid.exists()
    output = tmp_path / 'diagnostic-deck'
    m.main(['--mode', 'full', '--iteration-diagnostic', '--output', str(output)])
    status = json.loads((output / 'status.json').read_text())
    assert status['status'] == 'DECK_PREPARED' and status['diagnostic_only']
    assert status['iteration_controls']['IC'] == 24
    assert all(status['iteration_controls'][name] == 25 for name in ('I0', 'IR', 'IP'))
    assert not status['qualified'] and not status['e04_external_row_closed']
