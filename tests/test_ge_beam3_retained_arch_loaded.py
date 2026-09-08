"""Protocol tests only; full loaded mechanics runs are separately bounded."""
import ast
import copy
import inspect
import pytest
from docs.reference_cases import ge_beam3_retained_arch_loaded as gate


def specimen():
    _, binding = gate.historical(2, 1)
    return dict(schema=gate.SCHEMA, macros=2, step=1, input=binding,
        poses=[dict(name=name, elements=[{k:0. for k in gate.IDENTITIES} for _ in range(2)])
               for name in ('general', 'large-dyadic')],
        derivatives=[[dict(energy=0., chart=0., spatial=0.) for _ in range(9)] for _ in range(2)],
        native_replay_identical=True, state_unchanged=True, transformed_global_solve=False,
        full_spatial_stability=False, production_qualified=False, independent_review='PENDING')


def test_complete_schema(): gate.validate(specimen())


@pytest.mark.parametrize('field', gate.IDENTITIES)
def test_identity_mutation(field):
    value = specimen(); value['poses'][0]['elements'][0][field] = 1.01e-11
    with pytest.raises(ValueError): gate.validate(value)


@pytest.mark.parametrize('field', ('energy', 'chart', 'spatial'))
def test_derivative_mutation(field):
    value = specimen(); value['derivatives'][0][0][field] = 1.01e-7
    with pytest.raises(ValueError): gate.validate(value)


@pytest.mark.parametrize('field', ('native_replay_identical', 'state_unchanged', 'transformed_global_solve',
                                  'full_spatial_stability', 'production_qualified'))
def test_claim_mutation(field):
    value = specimen(); value[field] = not value[field]
    with pytest.raises(ValueError): gate.validate(value)


@pytest.mark.parametrize('mutation', ('pose', 'element', 'direction', 'hash', 'bytes', 'review', 'nan', 'bool', 'extra'))
def test_coverage_and_authority_mutation(mutation):
    v = copy.deepcopy(specimen())
    if mutation == 'pose': v['poses'].reverse()
    elif mutation == 'element': v['poses'][0]['elements'].pop()
    elif mutation == 'direction': v['derivatives'][0].pop()
    elif mutation == 'hash': v['input']['checkpoint_sha256'] = '0'*64
    elif mutation == 'bytes': v['input']['checkpoint_bytes'] += 1
    elif mutation == 'review': v['independent_review'] = 'ACCEPTED'
    elif mutation == 'nan': v['poses'][0]['elements'][0]['potential'] = float('nan')
    elif mutation == 'bool': v['poses'][0]['elements'][0]['potential'] = False
    else: v['extra'] = None
    with pytest.raises(ValueError): gate.validate(v)


@pytest.mark.parametrize('macros,step', ((True,1), (4,1), (12,2), (12,True)))
def test_extent(macros, step):
    with pytest.raises(ValueError): gate.extent(macros, step)


@pytest.mark.parametrize('raw', (b'{"a":1,"a":1}\n', b'{"a":NaN}\n', b'{ "a":1}\n'))
def test_strict_json(raw):
    with pytest.raises(ValueError): gate.strict_bytes(raw)


def test_no_continuation_or_reference_solve():
    tree = ast.parse(inspect.getsource(gate))
    calls = [n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
    assert 'solve' not in calls and 'restore' in calls
    assert 'evaluate' in calls and 'recover' in calls
