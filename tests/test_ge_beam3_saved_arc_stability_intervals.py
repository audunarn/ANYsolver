"""Authority and interval classification only; no mechanics execution."""
import pytest
from docs.reference_cases import ge_beam3_saved_arc_stability_intervals as gate


@pytest.mark.parametrize('n,step',((True,6),(2,6),(3,6),(4,1),(4,12),(8,True),(12,8),(12,13)))
def test_extent(n,step):
    with pytest.raises(ValueError):gate.historical(n,step)


@pytest.fixture
def valid(monkeypatch):
    identity=dict(sha256='a'*64,bytes=100,relative_path='registered')
    ready=dict(schema='GE_BEAM3_INTERMEDIATE_ARC_CAPTURE_V1',revision='b'*40,macros=4,step=6,
        checkpoint=identity,packet='packet',native_arc_replay=True,production_qualified=False)
    receipt=dict(success=True,reason='COMPLETED',exit_code=0,after=[0,0,1],before=[1,0,1],elapsed=1.,cleanup_error=None,error=None)
    data=dict(ready=ready,receipt=receipt,packet=dict(checkpoint_sha256='a'*64))
    monkeypatch.setattr(gate,'bound',lambda k:data[k]);monkeypatch.setattr(gate,'historical',lambda n,s:(b'raw',identity))
    return dict(schema='GE_BEAM3_INTERMEDIATE_INERTIA_ASSIGNMENT_V1',revision='b'*40,ready='ready',receipt='receipt'),data


def test_assignment(valid):gate.assignment(valid[0])


@pytest.mark.parametrize('mutation',('active','failure','timeout','memory','revision','history','packet','claim','extra','nan_time'))
def test_mutations(valid,mutation):
    value,data=valid
    if mutation=='active':data['receipt']['after'][1]=1
    elif mutation=='failure':data['receipt']['exit_code']=1
    elif mutation=='timeout':data['receipt']['elapsed']=601.
    elif mutation=='memory':data['receipt']['before'][2]=25*1024**3
    elif mutation=='revision':data['ready']['revision']='c'*40
    elif mutation=='history':data['ready']['native_arc_replay']=False
    elif mutation=='packet':data['packet']['checkpoint_sha256']='c'*64
    elif mutation=='claim':data['ready']['production_qualified']=True
    elif mutation=='nan_time':data['receipt']['elapsed']=float('nan')
    else:value['extra']=None
    with pytest.raises(ValueError):gate.assignment(value)


def rows():
    return [dict(macros=4,step=s,drop=float(i),load=float(i),checkpoint_sha256=str(i)*64,
        counts=dict(planar=p,lateral=l)) for i,(s,p,l) in enumerate(((1,0,0),(6,0,0),(7,1,0),(9,1,1),(12,2,1)))]


def test_changes_preserve_actual_endpoints():
    source=rows();v=gate.intervals(source)
    assert len(v['changed_count_intervals'])==3
    assert v['changed_count_intervals'][0]['left'] is source[1]
    assert v['changed_count_intervals'][0]['right'] is source[2]
    assert v['root_uniqueness_established'] is False and v['production_qualified'] is False


def test_decreases_are_not_suppressed():
    source=rows();source[4]['counts']['planar']=0
    assert gate.intervals(source)['changed_count_intervals'][-1]['right']['counts']['planar']==0


@pytest.mark.parametrize('mutation',('missing','order','mesh','boolean','negative','family','nan','hash','claim','boolean_step'))
def test_sample_mutations(mutation):
    source=rows()
    if mutation=='missing':source.pop()
    elif mutation=='order':source.reverse()
    elif mutation=='mesh':source[1]['macros']=8
    elif mutation=='boolean':source[1]['counts']['planar']=True
    elif mutation=='negative':source[1]['counts']['planar']=-1
    elif mutation=='nan':source[1]['drop']=float('nan')
    elif mutation=='hash':source[1]['checkpoint_sha256']='bad'
    elif mutation=='claim':source[1]['production_qualified']=True
    elif mutation=='boolean_step':source[0]['step']=True
    else:source[1]['counts']['extra']=0
    with pytest.raises(ValueError):gate.intervals(source)
