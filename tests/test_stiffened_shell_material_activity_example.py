from types import SimpleNamespace as Record
import numpy as np
import pytest
from examples.stiffened_shell_coupled_plastic_history import _shell_activity


def sample(q4=.1,s3=.2):
    return Record(shell_q4_material=(Record(element_id=1,alpha=np.full(12,q4)),),
                  shell_s3_material=(Record(element_id=2,alpha=np.full(9,s3)),))


def test_native_family_activity_and_station_identity():
    before=sample();after=sample(s3=.3)
    assert _shell_activity(before)==(True,.2,{'q4':True,'s3':True})
    assert _shell_activity(after,before)==(True,.3,{'q4':False,'s3':True})
    assert _shell_activity(after,after)==(False,.3,{'q4':False,'s3':False})
    after.shell_q4_material+=(Record(element_id=3,alpha=np.full(12,.1)),)
    before.shell_q4_material=(Record(element_id=3,alpha=np.full(12,.1)),)+before.shell_q4_material
    assert _shell_activity(after,before)[2]=={'q4':False,'s3':True}


@pytest.mark.parametrize('fault',['duplicate','missing','shape','nonfinite','decrease'])
def test_activity_rejects_incompatible_histories(fault):
    before=sample();after=sample()
    if fault=='duplicate':after.shell_q4_material*=2
    elif fault=='missing':after.shell_s3_material=()
    elif fault=='shape':after.shell_s3_material[0].alpha=np.zeros(12)
    elif fault=='nonfinite':after.shell_s3_material[0].alpha[0]=np.nan
    else:after.shell_s3_material[0].alpha[3]=.1
    with pytest.raises((ValueError,AssertionError)):_shell_activity(after,before)


@pytest.mark.parametrize('family,size',[('q4',12),('s3',9)])
@pytest.mark.parametrize('case',['zero','initial','unchanged','below','above'])
def test_homogeneous_stationwise_parity(family,size,case):
    values=np.zeros((2,size)) if case=='zero' else np.full((2,size),.2)
    old=values.copy()
    if case in ('below','above'):
        values[1,3]+=(32 if case=='below' else 128)*np.finfo(float).eps*.2
    def record(array):
        result=Record(shell_q4_material=(),shell_s3_material=())
        setattr(result,'shell_'+family+'_material',tuple(
            Record(element_id=i+1,alpha=row) for i,row in enumerate(array)))
        return result
    previous=None if case in ('zero','initial') else record(old)
    before=np.zeros_like(values) if previous is None else old
    budget=64*np.finfo(float).eps*np.maximum(np.abs(values),np.abs(before))
    expected=bool(np.any(values-before>budget))
    assert _shell_activity(record(values),previous)==(expected,float(np.max(values)),{family:expected})
