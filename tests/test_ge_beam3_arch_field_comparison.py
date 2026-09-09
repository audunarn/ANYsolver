"""Small reference sampling/recovery checks; no native equilibrium run."""
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest

from docs.reference_cases import ge_beam3_arch_field_comparison as field
from docs.reference_cases import ge_beam3_curved_p5_arch_reference as ref


@pytest.mark.parametrize('samples', [[], [-1.], [-1., 0., 0.], [-1., -.2, -.3, 0.],
    [-1., True, 0.], [-1., float('nan'), 0.], [-2., 0.], [-1., .1], [[-1., 0.]], list(np.linspace(-1, 0, 4098))])
def test_invalid_sampling_rejected_before_any_bvp(monkeypatch, samples):
    monkeypatch.setattr(ref, 'solve_bvp', lambda *a, **k: pytest.fail('BVP reached'))
    with pytest.raises(ValueError): ref.solve(.01, sample_parameters=samples)


def test_explicit_sampling_uses_collocation_polynomial_without_changing_default_solve():
    default = ref.solve(.01, axial=1., shear=.4, bending=.0001, profile='BVP9')
    requested = sorted(set(map(float, default.parameter)) | {-.123456789, -1./3})
    expanded = ref.solve(.01, axial=1., shear=.4, bending=.0001, profile='BVP9', sample_parameters=requested)
    assert expanded.load == default.load and expanded.strain_energy == default.strain_energy
    indices = [requested.index(float(x)) for x in default.parameter]
    np.testing.assert_array_equal(expanded.fields[:, indices], default.fields)
    assert len(expanded.parameter) == 131 and not expanded.parameter.flags.writeable
    expected = ref.equations(expanded.parameter, expanded.fields, expanded.force, .1, 1., .4, .0001)
    assert np.isfinite(expected).all()


def fixture():
    # Explicit nonzero-angle planar fields with known force/moment signs.
    return SimpleNamespace(parameter=np.array([-1., -.5, 0.]),
        fields=np.array([[-1., -.49, 0.], [0., .06, .09], [.2, .1, 0.], [.002, -.003, .004]]),
        force=np.array([-.02, -.01]), axial=1., shear=.4, bending=.0001)


def test_reference_material_components_reconstruct_spatial_force_moment_and_work():
    data = field.reference_fields(fixture(), [-.5, .5])
    stress = data['strain']*field.STIFFNESS
    np.testing.assert_allclose(np.einsum('nij,nj->ni', data['frames'], stress[:, :3]), data['force'], atol=1e-11, rtol=1e-15)
    np.testing.assert_allclose(np.einsum('nij,nj->ni', data['frames'], stress[:, 3:]), data['moment'], atol=1e-11, rtol=1e-15)
    assert data['force'][0, 1] == -data['force'][1, 1]
    np.testing.assert_array_equal(data['moment'][0], data['moment'][1])
    for strain, resultant, frame in zip(data['strain'], stress, data['frames']):
        spatial_work = (frame@strain[:3])@(frame@resultant[:3])+(frame@strain[3:])@(frame@resultant[3:])
        assert abs(float(strain@resultant-spatial_work)) < 1e-11
    with pytest.raises(ValueError): field.reference_fields(fixture(), [-.123])


def exact_rows():
    expected = field.reference_fields(fixture(), [-.5, .5])
    rows = [dict(measure=.5, strain=e.tolist(), strain_low=[0.]*6,
        resultants=(field.STIFFNESS*e).tolist(), resultants_low=[0.]*6,
        current_frame=f.tolist()) for e, f in zip(expected['strain'], expected['frames'])]
    energy = sum(.25*float(e@(field.STIFFNESS*e)) for e in expected['strain'])
    return rows, expected, energy


def test_exact_synthetic_fields_have_zero_energy_error_and_detect_mutations():
    rows, expected, energy = exact_rows()
    result = field.compare_stations(rows, expected, energy)
    assert result['nominal_energy_norm_relative_error'] == 0
    assert result['integrated_energy_relative_error'] == 0
    assert result['spatial_force_max_relative_error'] < 1e-15
    rows[0]['strain'][4] += .1
    assert field.compare_stations(rows, expected, energy)['nominal_energy_norm_relative_error'] > 0


@pytest.mark.parametrize('mutation', ['force', 'moment', 'frame', 'measure', 'nonfinite', 'boolean'])
def test_field_mutations_cannot_pass_unnoticed(mutation):
    rows, expected, energy = exact_rows()
    if mutation == 'force':
        rows[0]['resultants'][2] += 100.
        assert field.compare_stations(rows, expected, energy)['spatial_force_max_relative_error'] > .001
    elif mutation == 'moment':
        rows[0]['resultants'][4] += 100.
        assert field.compare_stations(rows, expected, energy)['spatial_moment_max_relative_error'] > .001
    else:
        if mutation == 'frame': rows[0]['current_frame'][0][0] = 2.
        if mutation == 'measure': rows[0]['measure'] = -1.
        if mutation == 'nonfinite': rows[0]['strain'][0] = float('inf')
        if mutation == 'boolean': rows[0]['strain'][0] = True
        with pytest.raises(ValueError): field.compare_stations(rows, expected, energy)


@pytest.mark.parametrize('macros,size,digest', [(6,141754,'20a1a48cf6e2dfdc669c4f2d823deb89a9da8c6560ab716eb32e95b1b917a940'),
    (12,278640,'ca95e88b6d354c3aeeb4bcebc1f49791cb3b1cef0781644f3be0e696e3a33683')])
def test_recovery_reproduces_actual_preserved_hash_without_equilibrium_run(macros,size,digest):
    from docs.reference_cases import ge_beam3_fibre_arch_refinement as family
    path = Path(f'C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-fibre-arch{macros}-20260907-v1/checkpoint-diagnostic.json')
    if not path.is_file():
        pytest.skip('External development checkpoint not installed; not qualification evidence')
    raw = path.read_bytes()
    assert len(raw) == size and sha256(raw).hexdigest() == digest
    packet = field.geometry.preserved(raw, digest)
    model = family.model(macros)
    rows, locations = field.native_recovery(model, packet['records'][0])
    assert len(rows) == macros and len(locations) == 8*macros
    packet['records'][0]['recovery_sha256'] = '0'*64
    with pytest.raises(ValueError, match='recovery hash'): field.native_recovery(model, packet['records'][0])
