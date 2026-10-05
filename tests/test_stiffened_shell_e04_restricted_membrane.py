"""Focused harness contracts; numerical execution is scheduled by the orchestrator."""
import importlib.util
import json
from pathlib import Path

import pytest


def module():
    path = Path(__file__).parents[1] / 'scripts' / 'r8_e04_restricted_membrane.py'
    spec = importlib.util.spec_from_file_location('restricted_membrane', path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def test_actual_external_oracle_rejects_missing_material_inventory():
    m = module()
    class Missing:
        def eleResponse(self, *args):
            return ()
    with pytest.raises(m.UnsupportedQuantity, match='finite actual values'):
        m.external_layers(Missing())


def test_plate_fiber_engineering_shear_and_inferred_history_are_explicit():
    m = module()
    # A purely elastic plane-stress engineering-shear state has zero inferred p.
    eps = (2e-6, -1e-6, 3e-6, 0., 0.)
    sx = m.E / (1 - m.NU**2) * (eps[0] + m.NU * eps[1])
    sy = m.E / (1 - m.NU**2) * (eps[1] + m.NU * eps[0])
    assert m.plastic_from_actual(eps, (sx, sy, m.G * eps[2])) == pytest.approx((0.,) * 4, abs=1e-20)
    # Engineering shear contributes half its square to the tensor norm.
    assert m.equivalent_increment((0.,) * 4, (0., 0., 0., .003)) == pytest.approx(.003 / 3**.5)


def test_admission_rejects_nonaffine_or_rotating_patch():
    m = module()
    disp = {n: (2e-5 * x, 0., 0., 0., 0., 0.)
            for n, (x, _, _) in zip(m.SHELL_IDS, m.SHELL_XYZ)}
    assert m.check_patch(disp)[0] == pytest.approx(2e-5)
    disp[2] = (1.1e-5, 0., 0., 0., 0., 0.)
    with pytest.raises(ValueError, match='patch lost'):
        m.check_patch(disp)
    disp[2] = (1e-5, 0., 0., 0., 0., 1e-4)
    with pytest.raises(ValueError, match='patch lost'):
        m.check_patch(disp)


def test_actual_fiber_queries_are_complete_and_not_shell_resultant_proxies():
    m = module()
    class Oracle:
        def __init__(self):
            self.calls = []
        def eleResponse(self, e, *args):
            self.calls.append((e, args))
            return (0.,) * 5
    oracle = Oracle()
    layers = m.external_layers(oracle)
    assert len(layers) == 40 and len(oracle.calls) == 80
    assert {a[-1] for _, a in oracle.calls} == {'strain', 'stress'}
    assert all(a[0] == 'material' and a[2] == 'fiber' for _, a in oracle.calls)


def test_load_balance_and_work_use_actual_shell_stress():
    m = module()
    eps = 1e-5
    sx = (m.FORCE - 2 * m.E * m.AREA * eps) / (m.WIDTH * m.THICKNESS)
    disp = {n: (eps * x, 0., 0., 0., 0., 0.)
            for n, (x, _, _) in zip(m.SHELL_IDS, m.SHELL_XYZ)}
    layers = [dict(strain=(eps, 0., 0.), stress=(sx, .3 * sx, 0.))]
    beam_work = 2 * m.E * m.AREA * eps**2 * m.LENGTH
    row = m.patch_record(1., disp, layers, beam_work)
    assert row['virtual_work_residual_j'] == pytest.approx(0., abs=1e-12)
    with pytest.raises(ValueError, match='balance/work failed'):
        m.patch_record(1., disp, layers, beam_work + .01)


def test_fixture_preserves_all_retained_ports_without_beam_fixities():
    m = module()
    definition = m.native_definition()
    assert len(definition.beams) == 2
    assert len(definition.shell.q4_elements) == 2
    assert len(definition.points) == 6
    assert len(definition.fixed) == 32
    assert all(f.domain == 'shell' for f in definition.fixed)
    assert definition.shell.j2_curve.sigma_prop == 1e6
    assert definition.shell_reference_policy == 'CURVED_Q4_POINT_MATERIAL_REFERENCE_V1_DEV'


def test_compare_route_uses_completed_json_inputs_without_numerical_imports(tmp_path, monkeypatch):
    m = module()
    paths = []
    for route in ('native', 'external'):
        folder = tmp_path / route
        folder.mkdir()
        data = [dict(factor=f, engineering_axial_strain=1e-5,
                     layer_stress_pa=[1e6, .3e6, 0.]) for f in m.TARGETS]
        m.save(folder / 'status.json', dict(route=route,
            status='COMPLETED_SUPPLEMENTAL_' + route.upper(), script_sha256='a' * 64))
        path = folder / (route + '.json')
        m.save(path, data)
        paths.append(path)
    def reject_runtime(*args):
        raise AssertionError('comparison must not import numerical runtimes')
    monkeypatch.setattr(m, 'runtime_identity', reject_runtime)
    output = tmp_path / 'comparison'
    m.main(['--route', 'compare', '--output', str(output),
            '--native-input', str(paths[0]), '--external-input', str(paths[1])])
    result = json.loads((output / 'comparison.json').read_text())
    assert len(result) == len(m.TARGETS)
    assert all(row['strain_difference'] == 0 for row in result)
    assert json.loads((output / 'status.json').read_text())['status'] == 'COMPLETED_SUPPLEMENTAL_COMPARE'


def test_compare_route_rejects_failed_evidence_and_truncated_stress(tmp_path):
    m = module()
    m.save(tmp_path / 'status.json', dict(route='native', status='FAILED'))
    m.save(tmp_path / 'native.json', [])
    with pytest.raises(ValueError, match='completed route evidence'):
        m.read_completed_input(tmp_path / 'native.json', 'native')
    incomplete = [dict(factor=f, engineering_axial_strain=1e-5,
                       layer_stress_pa=[1e6, .3e6]) for f in m.TARGETS]
    with pytest.raises(m.UnsupportedQuantity, match='complete three-component'):
        m.compare(incomplete, incomplete)


def test_comparison_requires_matching_originating_source_and_fixture():
    m = module()
    historical = dict(script_sha256='a' * 64)
    # Historical paired runs remain comparable after a comparator-only edit.
    assert m.matching_input_identity(historical, historical)['originating_script_sha256'] == 'a' * 64
    with pytest.raises(ValueError, match='script identities'):
        m.matching_input_identity(historical, dict(script_sha256='b' * 64))
    with pytest.raises(ValueError, match='script identities'):
        m.matching_input_identity({}, {})
    future = dict(historical, fixture_signature_sha256=m.fixture_signature())
    assert m.matching_input_identity(future, future)['fixture_signature_sha256'] == m.fixture_signature()
    with pytest.raises(ValueError, match='fixture signatures'):
        m.matching_input_identity(future, historical)
    with pytest.raises(ValueError, match='fixture signatures'):
        m.matching_input_identity(future, dict(historical, fixture_signature_sha256='c' * 64))
