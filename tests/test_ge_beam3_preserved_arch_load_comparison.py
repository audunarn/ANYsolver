"""Small synthetic reader tests; no native beam, BVP or resource run."""
import ast
from hashlib import sha256
import inspect
import sys

import pytest
from docs.reference_cases import ge_beam3_preserved_arch_load_comparison as audit


def seal(value, key):
    value.pop(key, None); value[key] = sha256(audit.canonical(value)).hexdigest()
    return value


def fixtures():
    initial = seal(dict(target=0), 'record_sha256'); previous = initial['record_sha256']; rows = []
    for index, target in enumerate(audit.TARGETS, 1):
        row = dict(target=index, displacement_target=target, parameter=105.+index,
            previous_sha256=previous, histories=[dict(stations=[dict(rows=[[0., 0.]])])])
        seal(row, 'record_sha256'); rows.append(row); previous = row['record_sha256']
    checkpoint = seal(dict(schema='GE_BEAM3_PHYSICAL_FIBRE_TRANSLATION_CONTROL_CHAIN_V1',
        program=dict(schema='GE_BEAM3_KINEMATIC_SEEDED_SPATIAL_NEWTON_FIBRE_CONTROL_V1'),
        node_ids=list(range(1, 10)), element_ids=list(range(1, 5)), completed_targets=4,
        initial=initial, records=rows), 'checkpoint_sha256')
    ref = dict(schema='GE_BEAM3_PRESERVED_FIBRE_ARCH_GEOMETRIC_COMPARISON_V1',
        production_qualified=False, mechanics_replayed=False,
        section_comparison='NOMINAL_ELASTIC_EA_1E6_GA_4E5_EI_100_NOT_EXACT_DYADIC_SECTION_CERTIFICATE',
        rows=[dict(displacement=t, reference_load=100., native_load=120., reference_profile='BVP9',
            stiffness_scale=1e6, same_equilibrium_branch_proved=False, production_qualified=False)
            for t in (*audit.TARGETS, .075, .1, .15, .2)])
    return checkpoint, ref


def rechain(checkpoint):
    previous = checkpoint['initial']['record_sha256']
    for row in checkpoint['records']:
        row['previous_sha256'] = previous
        seal(row, 'record_sha256'); previous = row['record_sha256']
    seal(checkpoint, 'checkpoint_sha256')


def test_reader_recomputes_errors_and_preserves_input_bytes():
    checkpoint, reference = fixtures(); before = audit.canonical([checkpoint, reference])
    rows = audit.inspect_records(checkpoint, reference)
    assert [r['four_macro_relative_load_error'] for r in rows] == [.06, .07, .08, .09]
    assert all(r['two_macro_relative_load_error'] == .2 for r in rows)
    assert audit.canonical([checkpoint, reference]) == before


@pytest.mark.parametrize('incident', ['target', 'seal', 'previous', 'partial', 'nodes', 'plastic',
    'history_boolean', 'empty_history', 'reference_replay', 'qualified', 'profile', 'units',
    'duplicate_reference', 'load_zero', 'load_nan', 'load_boolean'])
def test_mutation_refusal_even_with_resealed_synthetic_input(incident):
    checkpoint, reference = fixtures(); row = checkpoint['records'][0]; ref = reference['rows'][0]
    if incident == 'target': row['displacement_target'] = .011
    elif incident == 'seal': row['record_sha256'] = 'f'*64
    elif incident == 'previous': row['previous_sha256'] = 'f'*64
    elif incident == 'partial': checkpoint['records'].pop()
    elif incident == 'nodes': checkpoint['node_ids'].pop()
    elif incident == 'plastic': row['histories'][0]['stations'][0]['rows'][0][0] = .01
    elif incident == 'history_boolean': row['histories'][0]['stations'][0]['rows'][0][0] = False
    elif incident == 'empty_history': row['histories'] = []
    elif incident == 'reference_replay': reference['mechanics_replayed'] = True
    elif incident == 'qualified': ref['production_qualified'] = True
    elif incident == 'profile': ref['reference_profile'] = 'OTHER'
    elif incident == 'units': ref['stiffness_scale'] = 1.
    elif incident == 'duplicate_reference': reference['rows'][1]['displacement'] = .01
    elif incident == 'load_zero': ref['reference_load'] = 0.
    elif incident == 'load_nan': ref['reference_load'] = float('nan')
    else: ref['reference_load'] = True
    if incident not in ('seal', 'previous'): rechain(checkpoint)
    else: seal(checkpoint, 'checkpoint_sha256')
    with pytest.raises(ValueError): audit.inspect_records(checkpoint, reference)


@pytest.mark.parametrize('raw', [b'{"x":1,"x":2}\n', b'{"x":NaN}\n', b'{"x":Infinity}\n',
    b'{"x":1e999}\n', b' {"x":1}\n', b'{}\r\n', b''])
def test_strict_json_rejects_ambiguous_or_nonfinite_data(raw):
    with pytest.raises(ValueError): audit.parse(raw)


def test_hash_bound_output_never_repairs_historical_result(monkeypatch):
    checkpoint, reference = fixtures(); raw = audit.canonical(checkpoint); ref = audit.canonical(reference)
    with pytest.raises(ValueError): audit.synthesize(raw, ref, source_commit='1'*40)
    monkeypatch.setattr(audit, 'CHECKPOINT_BYTES', len(raw))
    monkeypatch.setattr(audit, 'CHECKPOINT_SHA', sha256(raw).hexdigest())
    monkeypatch.setattr(audit, 'REFERENCE_LF_SHA', sha256(ref).hexdigest())
    first = audit.canonical(audit.synthesize(raw, ref, source_commit='1'*40))
    assert first == audit.canonical(audit.synthesize(raw, ref, source_commit='1'*40))
    value = audit.parse(first)
    for key in ('historical_request_successful', 'original_canonical_comparison_repaired',
                'mechanics_replayed', 'reference_recomputed', 'production_qualified',
                'geometry_or_frame_comparison_completed', 'same_equilibrium_branch_proved'):
        assert value[key] is False
    assert value['status'] == 'DEVELOPMENT_LOAD_COMPARISON_ONLY'
    with pytest.raises(ValueError): audit.synthesize(raw+b' ', ref, source_commit='1'*40)
    with pytest.raises(ValueError): audit.synthesize(raw, ref+b' ', source_commit='1'*40)


def test_reader_imports_only_standard_library_without_dynamic_loading():
    tree = ast.parse(inspect.getsource(audit))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import): assert all(a.name.split('.')[0] in sys.stdlib_module_names for a in node.names)
        if isinstance(node, ast.ImportFrom): assert node.module.split('.')[0] in sys.stdlib_module_names
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in ('__import__', 'eval', 'exec')


def test_failed_request_and_reference_authority_are_exact():
    assert audit.FAILED_REQUEST == 'b89e903dc17d44408ce0c42d11c6b61f'
    assert audit.CHECKPOINT_BYTES == 95786
    assert audit.CHECKPOINT_SHA == 'bcf90a0eca2923ee04ab00bf61b6e1eabdac40779671f90666bdbc2964420a1f'
    assert audit.REFERENCE_LF_SHA == 'c2401dfc756cf7d95005ee6c92f43ae5960c82b361e7477a68cd2b676e025728'
