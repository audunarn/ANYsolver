"""Read-only exact reproduction and arithmetic measurement inspection."""
from copy import deepcopy
from hashlib import sha256
import statistics
import numpy as np
import pytest
from docs.reference_cases import ge_beam3_loaded_arch_refinement as probe

OUTPUT=probe.EXTERNAL/'ge-beam3-loaded-six-20260907-v2'
OLD=probe.EXTERNAL/'ge-beam3-loaded-six-20260907-v1'
BENCH=probe.EXTERNAL/'ge-beam3-dyadic-benchmark-20260907-v1'
REVISION='4204f3a38c65fc215a76c595f994a7a71c317d54'
SHA='f50285799e45a7fdbbcb7d9cad997b13e83a8e7bf38e6904c4c1e247595d5362'


@pytest.fixture
def saved():
    if not OUTPUT.exists(): pytest.skip('external reproduction unavailable')
    raw=probe.read(OUTPUT/'comparison.json')
    assert len(raw)==3490 and sha256(raw).hexdigest()==SHA
    return raw,probe.validate(OUTPUT,raw,REVISION)


def test_all_raw_artifacts_byte_identical(saved):
    for name in probe.ARTIFACTS: assert probe.read(OUTPUT/name)==probe.read(OLD/name)
    assert len(probe.ARTIFACTS)==10
    assert (probe.ROOT/'docs/reference_cases/ge_beam3_dyadic_loaded_six_result.json').read_bytes()==saved[0]


def test_entire_scientific_body_unchanged(saved):
    new=deepcopy(saved[1]); old=probe.parse(probe.read(OLD/'comparison.json'))
    assert new.pop('revision')==REVISION
    assert old.pop('revision')=='b66ce8d825708014c352449dd009af23a6f6b1f0'
    assert probe.canonical(new)==probe.canonical(old)
    assert new['production_qualified'] is False and new['independent_review']=='PENDING'


def test_saved_paired_arithmetic_statistics():
    if not BENCH.exists(): pytest.skip('external arithmetic measurement unavailable')
    raw=probe.read(BENCH/'benchmark.json')
    assert len(raw)==1554 and sha256(raw).hexdigest()=='5a9ca8a039aaa943547a01ad3923ffbdba41d9bc6f3804cee34ce27d4d25516d'
    value=probe.parse(raw)
    assert value['dimension']==69 and value['inertia']==[64,5,0] and value['equal'] is True
    assert value['timed_pairs']==11 and value['warmup_pairs']==1
    for name,records in value['timings'].items():
        assert len(records)==11 and all(r['wall']>0 and r['cpu']>0 for r in records)
        walls=[r['wall'] for r in records]; median=statistics.median(walls)
        assert value['summary'][name]==dict(median=median,mad=statistics.median(abs(x-median) for x in walls),
            p95=float(np.percentile(walls,95)))
    assert value['production_qualified'] is False and value['mechanics_changed'] is False


@pytest.mark.parametrize('key',['coordinate_limit','exact_dimension_limit','new_native_spectra','new_reference_solves'])
def test_arithmetic_success_does_not_authorize_scope_mutation(saved,key):
    value=deepcopy(saved[1]); value[key]+=1
    with pytest.raises(ValueError): probe.validate(OUTPUT,probe.canonical(value),REVISION)
