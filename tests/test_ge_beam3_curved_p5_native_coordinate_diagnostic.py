"""Historical V1 defect witnesses, not a passing qualification of V1 mechanics."""

from fractions import Fraction
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from docs.reference_cases import ge_beam3_curved_p5_native_coordinate_diagnostic as diagnostic


@pytest.fixture(scope='module')
def witnesses():
    return [diagnostic.witness(*case) for case in diagnostic.CASES]


def test_frozen_native_rounding_defect_is_reproduced_in_actual_assembly(witnesses):
    records = [diagnostic.summarize(value) for value in witnesses]
    assert [r['native_axial_reference_passed'] for r in records] == [True, False, False]
    assert [r['nonzero_low_coordinate_count'] for r in records] == [0, 2, 2]
    for value in witnesses[1:]:
        assert np.count_nonzero(value['native_force']) == 0
        assert value['native_response'].potential == 0.
        assert value['exact_energy'] > 0
        assert all(s.response.strain[0] == 0. for s in value['native_response'].stations)
    assert all(r['accepted_state_unchanged'] for r in records)


def test_existing_compensated_operator_preserves_axial_work_and_station_recovery(witnesses):
    for value in witnesses:
        made = value['compensated_response']; strain = value['strain']
        assert np.linalg.norm(made.residual-value['expected_force']) <= 1e-11*np.linalg.norm(value['expected_force'])
        assert abs(made.potential-float(value['exact_energy'])) <= 1e-11*float(value['exact_energy'])
        for station in made.stations:
            assert abs(station.response.resultants[0]-strain) <= 1e-11*abs(strain)
            assert not station.response.plastic_active
        assert diagnostic.summarize(value) == diagnostic.summarize(value)


def test_two_term_authority_is_exact_and_owned():
    _, element, total, _ = diagnostic.problem(-54, 1)
    reference = element.core.reference.coordinates
    view = reference+total.reshape(3, 6)[:, :3]
    high, low = diagnostic.exact_position_pairs(reference, total, view)
    for index in np.ndindex((3, 3)):
        assert Fraction(float(high[index]))+Fraction(float(low[index])) == (
            Fraction(float(reference[index]))+Fraction(float(total.reshape(3, 6)[index])))
    saved = high.copy(), low.copy()
    reference[:] = 123.; total[:] = 456.; view[:] = 789.
    assert np.array_equal(high, saved[0]) and np.array_equal(low, saved[1])


@pytest.mark.parametrize('mutation', ['view', 'total_shape', 'reference_dtype', 'nonfinite', 'overflow'])
def test_coordinate_authority_rejects_bad_inputs(mutation):
    reference = np.array([[0., 0., 0.], [1., 0., 0.], [2., 0., 0.]])
    total = np.zeros(18); view = reference.copy()
    if mutation == 'view': view[0, 0] = np.nextafter(0., 1.)
    if mutation == 'total_shape': total = total.reshape(3, 6)
    if mutation == 'reference_dtype': reference = reference.astype(np.float32)
    if mutation == 'nonfinite': total[0] = np.nan
    if mutation == 'overflow': reference[0, 0] = total[0] = np.finfo(float).max
    with pytest.raises(ValueError): diagnostic.exact_position_pairs(reference, total, view)


def test_two_fresh_process_diagnostics_are_identical(tmp_path):
    root = Path(__file__).resolve().parents[1]
    environment = dict(os.environ)
    environment['PYTHONPATH'] = str(root/'src') + os.pathsep + environment.get('PYTHONPATH', '')
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        environment[key] = '1'
    records = []
    for label in ('first', 'second'):
        directory = tmp_path/label; directory.mkdir()
        result = subprocess.run([sys.executable, '-B', str(Path(diagnostic.__file__).resolve())],
            cwd=directory, env=environment, check=True, capture_output=True, timeout=30)
        # The diagnostic writes canonical JSON to stdout, not a scientific
        # certificate. Normalize Windows text-pipe newlines only.
        raw = result.stdout.replace(b'\r\n', b'\n')
        value = json.loads(raw)
        assert diagnostic.canonical(value) == raw
        assert not value['production_qualified'] and not value['activation_authorized']
        assert not value['formal_evidence_reclassified']
        records.append(raw)
    assert records[0] == records[1]


def test_reference_mismatch_cannot_be_hidden_by_the_small_absolute_scale(witnesses):
    from dataclasses import replace
    value = dict(witnesses[1])
    value['compensated_response'] = replace(value['compensated_response'], residual=np.zeros(18))
    with pytest.raises(ValueError, match='axial reference'): diagnostic.summarize(value)
    value = dict(witnesses[1])
    value['compensated_response'] = replace(value['compensated_response'], potential=0.)
    with pytest.raises(ValueError, match='potential reference'): diagnostic.summarize(value)


def test_preserved_diagnostic_has_exact_ratios_and_no_qualification_authority():
    root = Path(__file__).resolve().parents[1]
    path = root/'docs/reference_cases/ge_beam3_curved_p5_native_coordinate_evidence.json'
    raw = path.read_text(encoding='utf-8').encode('ascii')
    value = json.loads(raw)
    assert diagnostic.canonical(value) == raw
    assert value['source_commit'] == diagnostic.BASE
    assert value['schema'] == diagnostic.SCHEMA
    assert value['disposition'] == 'DEVELOPMENT_NATIVE_POSITION_REPRESENTATION_DEFECT'
    assert not any(value[k] for k in ('production_qualified','activation_authorized','formal_evidence_reclassified'))
    assert len(value['records']) == 3
    for record, (case_id, exponent, sign) in zip(value['records'], diagnostic.CASES):
        assert (record['case_id'], record['exponent'], record['sign']) == (case_id, exponent, sign)
        strain = Fraction(sign, 2**(-exponent))
        for key, expected in (('exact_strain_ratio', strain), ('exact_energy_ratio', strain**2)):
            assert all(type(number) is int for number in record[key])
            assert record[key] == [expected.numerator, expected.denominator]
        assert record['compensated_axial_reference_passed'] and record['accepted_state_unchanged']
        assert record['native_axial_reference_passed'] == (case_id == 'resolved_extension')
