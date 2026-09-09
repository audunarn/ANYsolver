"""Final gate adjudication is fixed before observing performance samples."""
from copy import deepcopy
import pytest
from docs.reference_cases.ge_beam3_native_delivery_gate import performance_summary, OPERATIONS
from docs.reference_cases.ge_beam3_mixed_p3_package_gate import PackageGateError


def samples(ratio=1.):
    return [{label:dict(operations={family:{op:dict(wall_ns=1000.*(ratio if label=='candidate' else 1.))
        for op in OPERATIONS} for family in ('B2','B3')}) for label in ('base','candidate')} for _ in range(12)]


def test_exact_equal_samples_pass_with_zero_mad():
    value=performance_summary(samples())
    assert value['passed'] and value['pair_count']==12
    assert value['diagnostic_timings']['B2']['RESTART']['paired']['mad']==0.


def test_one_regressed_operation_blocks_all():
    rows=samples()
    for row in rows:row['candidate']['operations']['B3']['RESTART']['wall_ns']=1051.
    value=performance_summary(rows)
    assert not value['passed']
    assert not value['checks']['B3']['RESTART']['passed']
    assert value['checks']['B2']['RESTART']['passed']


def test_gate_uses_median_paired_ratios_not_ratio_of_medians():
    rows=samples()
    for i,row in enumerate(rows):
        for family in ('B2','B3'):
            for op in OPERATIONS:
                row['base']['operations'][family][op]['wall_ns']=100. if i<6 else 10000.
                row['candidate']['operations'][family][op]['wall_ns']=109. if i<6 else 10100.
    value=performance_summary(rows)
    assert value['checks']['B2']['RESTART']['median_paired_ratio']==1.05
    assert value['passed']


@pytest.mark.parametrize('value', (float('nan'),float('inf'),0.,-1.))
def test_nonfinite_or_nonpositive_timings_rejected(value):
    rows=samples(); rows[0]['base']['operations']['B2']['SOLVE']['wall_ns']=value
    with pytest.raises((ValueError,ZeroDivisionError,PackageGateError)):performance_summary(rows)


@pytest.mark.parametrize('count',(0,11,13))
def test_incomplete_or_extra_pairs_rejected(count):
    rows=samples();rows=(rows+[deepcopy(rows[0])])[:count]
    with pytest.raises(ValueError):performance_summary(rows)
