"""Authority-only protocol tests; no numerical imports or mechanics runs."""
import copy
import pytest
from docs.reference_cases import ge_beam3_arc_spatial_refinement as gate


@pytest.mark.parametrize('n,step',((True,1),(3,1),(4,0),(8,True),(12,13)))
def test_extent(n,step):
    with pytest.raises(ValueError):gate.historical(n,step)


@pytest.fixture
def valid(monkeypatch):
    registered={'sha256':'a'*64,'bytes':100,'relative_path':'registered'}
    ready=dict(schema='GE_BEAM3_ARC_FACTOR_CAPTURE_V1',revision='b'*40,macros=4,step=1,
        checkpoint=registered,packet='packet',native_arc_replay=True,production_qualified=False)
    receipt=dict(success=True,reason='COMPLETED',exit_code=0,after=[0,0,1],before=[1,0,1],elapsed=1.,cleanup_error=None,error=None)
    packet=dict(checkpoint_sha256='a'*64)
    data=dict(ready=ready,receipt=receipt,packet=packet)
    monkeypatch.setattr(gate,'bound',lambda key:data[key])
    monkeypatch.setattr(gate,'historical',lambda n,s:(b'raw',registered))
    value=dict(schema='GE_BEAM3_SPATIAL_INSPECTION_ASSIGNMENT_V1',revision='b'*40,ready='ready',receipt='receipt')
    return value,data


def test_complete_assignment(valid):gate.assignment(valid[0])


@pytest.mark.parametrize('mutation',('active','failure','timeout','memory','revision','history','packet','claim','extra'))
def test_assignment_mutations(valid,mutation):
    value,data=valid
    if mutation=='active':data['receipt']['after'][1]=1
    elif mutation=='failure':data['receipt']['exit_code']=1
    elif mutation=='timeout':data['receipt']['elapsed']=601.
    elif mutation=='memory':data['receipt']['before'][2]=25*1024**3
    elif mutation=='revision':data['ready']['revision']='c'*40
    elif mutation=='history':data['ready']['native_arc_replay']=False
    elif mutation=='packet':data['packet']['checkpoint_sha256']='c'*64
    elif mutation=='claim':data['ready']['production_qualified']=True
    else:value['extra']=None
    with pytest.raises(ValueError):gate.assignment(value)
