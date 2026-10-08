"""Pure preparation controls for the fixed supplementary density reference."""
import copy
from fractions import Fraction as F
import importlib.abc
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from scripts import r8_bl5_density_reference_dev as reference


def rational_maps(prepared):
    return [{(n, d): F(value) for n, d, value in row}
            for row in prepared['exact_physical_row_coefficients']]


@pytest.fixture(scope='module')
def prepared_pair():
    return reference.prepare(4), reference.prepare(2)


def test_preparation_never_imports_product_or_opensees(monkeypatch):
    class ForbiddenImport(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname.split('.')[0] in ('anysolver', 'openseespy', 'openseespywin'):
                pytest.fail('pure preparation attempted native/product import: '+fullname)
    monkeypatch.setattr(sys, 'meta_path', [ForbiddenImport(), *sys.meta_path])
    prepared = reference.prepare(4)
    assert prepared['model']['nx'] == 64
    assert not any(name.split('.')[0] in ('anysolver', 'openseespy', 'openseespywin')
                   for name in sys.modules)


def test_all_channel_exact_density_nesting_including_endpoint_actions(prepared_pair):
    fine, coarse = map(rational_maps, prepared_pair)
    for support in range(2):
        for channel in range(5):
            left, right = 20*support+2*channel, 20*support+10+2*channel
            base = 10*support+2*channel
            keys = set(fine[left]) | set(fine[left+1]) | set(fine[right]) | set(fine[right+1]) | set(coarse[base]) | set(coarse[base+1])
            for key in keys:
                assert coarse[base].get(key, F(0)) == fine[left].get(key, F(0))+fine[right].get(key, F(0))
                assert coarse[base+1].get(key, F(0)) == (
                    -fine[left].get(key, F(0))+fine[left+1].get(key, F(0))+
                    fine[right].get(key, F(0))+fine[right+1].get(key, F(0)))/2
    # Original h16 cell means, not continuous affine endpoints or a new grid.
    for prepared, span in zip(prepared_pair, (4, 8)):
        for support in prepared['supports']:
            for cell, piece in enumerate(support['beam_pieces']):
                assert F(piece['xi_halfcell_mean_rational']) == F(2*cell+1-span, span)
        assert not any(d == 6 for row in rational_maps(prepared) for _, d in row)
    assert fine[2][100001, 2] == coarse[2][100001, 2] == F(1, 32)
    assert fine[3][100001, 2] == F(-3, 128)
    assert coarse[3][100001, 2] == F(-7, 256)


def test_required_inventory_load_sections_and_physical_ground(prepared_pair):
    for prepared, count in zip(prepared_pair, (4, 2)):
        model, expected = prepared['model'], prepared['expected_inventory']
        assert (model['nx'], model['ny'], model['beam_intervals'], model['support_count']) == (64, 16, 16, count)
        assert len(model['nodes']) == 1122 and len(model['shell_cells']) == 1024 and len(model['beam_cells']) == 16
        assert len(prepared['physical_rows']) == len(prepared['emitted_rows']) == 10*count
        assert len(expected['elements']) == 1040
        assert sum(sum(flags) for flags in expected['fixes'].values()) == 107
        assert expected['loads'] == {100017: [0., 0., 0., 0., 0., 10.]}
        assert model['fixes'][100001] == (1, 1, 1, 1, 1, 0)
        assert model['nodes'][100001] == (0., 0., .0675)
        assert model['nodes'][100017] == (1., 0., .0675)
        assert model['nodes'][1105] == (1., .2, 0.)
        assert prepared['sections'] == dict(E_PA=210e9, NU=.3, G_PA=80769230769.23077,
            SHELL_THICKNESS_M=.035, BEAM_AREA_M2=.01, BEAM_TORSION_M4=1.6666666666666667e-5,
            BEAM_BENDING_M4=8.333333333333334e-6, BEAM_SHEAR_AREA_M2=.008)
        assert [support['interval_m'] for support in prepared['supports']] == [[i/count, (i+1)/count] for i in range(count)]
        assert prepared['native_channel_major_from_reference'] == [10*s+2*c+m for c in range(5) for s in range(count) for m in range(2)]
    for key in ('nodes', 'fixes', 'shell_cells', 'beam_cells', 'beam_element_tags'):
        assert prepared_pair[0]['model'][key] == prepared_pair[1]['model'][key]


def test_exact_emitted_dependents_and_foreign_support_separation(prepared_pair):
    for prepared, stride in zip(prepared_pair, (4, 8)):
        dependent = []
        physical = rational_maps(prepared)
        emitted = [{(n, d): F(float(c)) for n, d, c in zip(row[::3], row[1::3], row[2::3])}
                   for row in prepared['emitted_rows']]
        for support in prepared['supports']:
            index = support['support_id']
            assert support['recovery_beam_nodes'] == [100001+stride*index+stride//4,
                                                     100001+stride*index+3*stride//4]
            selected = list(map(tuple, support['dependent_node_dofs']))
            assert len(set(selected)) == 10
            for i, row in enumerate(support['row_indices']):
                assert all(emitted[row].get(key, F(0)) == F(int(i == j)) for j, key in enumerate(selected))
            dependent.extend(selected)
        assert len(set(dependent)) == len(dependent)
        for support in prepared['supports']:
            local = set(map(tuple, support['dependent_node_dofs']))
            foreign = set(dependent)-local
            assert all(physical[row].get(key, F(0)) == 0 for row in support['row_indices'] for key in foreign)


@pytest.mark.parametrize('value', (True, False, 2., 4., 1, 3, 8, '4', None))
def test_fixed_tuple_admission_requires_plain_support_count(value):
    with pytest.raises(ValueError, match='plain integer'):
        reference.prepare(value)


@pytest.mark.parametrize('key,value', (('nx', 32), ('ny', 8), ('beam_intervals', 128),
                                      ('support_count', 8), ('nx', True)))
def test_model_tuple_cannot_expand_historical_admissions(prepared_pair, key, value):
    _, refinement, _, _, _, ref = reference.services()
    model = copy.deepcopy(prepared_pair[0]['model'])
    model[key] = value
    with pytest.raises(ValueError, match='physical tuple'):
        reference.aggregate_rows(model, ref)


@pytest.mark.parametrize('mutation', ('coordinate', 'beam_ground', 'tip', 'shell_cell', 'element_tags'))
def test_actual_physical_inventory_mutations_are_rejected(prepared_pair, mutation):
    affine, _, _, _, _, ref = reference.services()
    model = copy.deepcopy(prepared_pair[0]['model'])
    if mutation == 'coordinate':
        model['nodes'][100003] = (.125, .001, .0675)
    elif mutation == 'beam_ground':
        model['fixes'][100001] = (1, 1, 1, 1, 1, 1)
    elif mutation == 'tip':
        model['beam_tip'] = 100016
    elif mutation == 'shell_cell':
        model['shell_cells'] = (*model['shell_cells'][:-1], (1, 2, 3, 4))
    else:
        model['beam_element_tags'] = tuple(range(16))
    with pytest.raises(ValueError, match='physical|inventory'):
        reference.aggregate_rows(model, ref, affine)


@pytest.mark.parametrize('key,value', (('E_PA', 200e9), ('WIDTH_M', .3),
                                      ('BEAM_AXIS_Z_M', .05), ('BEAM_BOTTOM_ARM_M', .05)))
def test_reference_section_or_offset_mismatch_is_not_admitted(key, value):
    _, refinement, _, _, _, ref = reference.services()
    changed = SimpleNamespace(**{name: getattr(ref, name) for name in
        (*reference.SECTIONS, 'WIDTH_M', 'BEAM_AXIS_Z_M', 'BEAM_BOTTOM_ARM_M')})
    setattr(changed, key, value)
    with pytest.raises(ValueError, match='physical sections'):
        reference.geometry(changed, 4, refinement)


def test_changed_source_is_refused_before_any_service_load(monkeypatch):
    original = reference.sha
    def changed(path):
        return '0'*64 if Path(path).name == reference.AFFINE_SOURCE else original(path)
    def forbidden(*args, **kwargs):
        pytest.fail('changed source must be refused before loading services')
    monkeypatch.setattr(reference, 'sha', changed)
    monkeypatch.setattr(reference.importlib.util, 'spec_from_file_location', forbidden)
    with pytest.raises(ValueError, match='source identity'):
        reference.services()


def test_preparation_owns_its_nested_outputs(prepared_pair):
    prepared = reference.prepare(4)
    prepared['model']['nodes'][100001] = (9., 9., 9.)
    prepared['physical_rows'][0][2] = 17.
    prepared['supports'][0]['beam_shape_integrals_m'][0][100001] = 99.
    prepared['sections']['E_PA'] = 1.
    original = prepared_pair[0]
    assert original['model']['nodes'][100001] == (0., 0., .0675)
    assert original['physical_rows'][0][2] != 17.
    assert original['supports'][0]['beam_shape_integrals_m'][0][100001] == 1/32
    assert reference.SECTIONS['E_PA'] == original['sections']['E_PA'] == 210e9


def test_non_mz_and_existing_output_refused_without_execution(tmp_path):
    with pytest.raises(ValueError, match='Mz10'):
        reference.main(tmp_path, tmp_path/'bad', 4, 'fy')
    assert not (tmp_path/'bad').exists()
    output = tmp_path/'existing'
    output.mkdir()
    (output/'marker').write_text('preserve', encoding='utf-8')
    with pytest.raises(FileExistsError):
        reference.main(tmp_path, output, 4)
    assert (output/'marker').read_text(encoding='utf-8') == 'preserve'


def test_finalization_keeps_primary_error_and_records_cleanup_failure(tmp_path):
    class BrokenFinalize:
        def finalize(self, *args, **kwargs):
            raise MemoryError('injected cleanup allocation failure')
    summary = {'status': 'failed', 'error': {'type': 'KeyboardInterrupt', 'message': 'primary'}}
    reference.finalize(None, None, BrokenFinalize(), tmp_path, summary)
    saved = json.loads((tmp_path/'summary.json').read_text(encoding='utf-8'))
    assert saved['error']['type'] == 'KeyboardInterrupt'
    assert 'injected cleanup allocation failure' in saved['finalization_error']
    with pytest.raises(MemoryError):
        reference.finalize(None, None, BrokenFinalize(), tmp_path, {'status': 'completed'})
