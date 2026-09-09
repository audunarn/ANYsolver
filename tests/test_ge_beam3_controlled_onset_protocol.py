"""Authority/search tests with synthetic counts; no beam computations."""
import copy
import pytest
from docs.reference_cases import ge_beam3_controlled_onset_protocol as p


def records(root=.0456):
    rows=[]
    for i in range(11):
        d,_,_=p.search(rows,.039)
        rows.append(dict(index=i,drop=d,load=.02775,planar_negative=1,lateral_negative=int(d>root),
            anchor_error=0. if i==0 else None,checkpoint_sha256='a'*64,packet_sha256='b'*64))
    return rows


def test_eight_midpoints_and_distinct_owned_programmes():
    rows=records();nxt,lo,hi=p.search(rows,.039)
    assert nxt is None and lo['drop']<=.0456<hi['drop'] and hi['drop']-lo['drop']<.000098
    assert p.targets(.03)==(.01,.02,.03) and p.targets(.045)==(.01,.02,.03,.045)


@pytest.mark.parametrize('value',(True,0.,.029,.056,float('nan'),float('inf')))
def test_invalid_targets(value):
    with pytest.raises(ValueError):p.targets(value)


@pytest.mark.parametrize('mutation',('duplicate','index','target','hash','boolean','anchor','extra','lower','upper','many','nan'))
def test_search_mutations(mutation):
    rows=records()
    if mutation=='duplicate':rows.append(rows[-1])
    elif mutation=='index':rows[2]['index']=1
    elif mutation=='target':rows[4]['drop']+=.00001
    elif mutation=='hash':rows[1]['packet_sha256']='bad'
    elif mutation=='boolean':rows[1]['lateral_negative']=False
    elif mutation=='anchor':rows[0]['anchor_error']=2e-11
    elif mutation=='extra':rows[1]['extra']=None
    elif mutation=='lower':rows[1]['lateral_negative']=1
    elif mutation=='upper':rows[2]['lateral_negative']=0
    elif mutation=='many':rows[3]['lateral_negative']=2
    else:rows[2]['load']=float('nan')
    with pytest.raises(ValueError):p.search(rows,.039)


def refs():return {'1':dict(left=dict(drop=.04564716575317947,load=.02774721379),right=dict(drop=.04564717069285733,load=.02774721301))}


def test_fine_engineering_adjudication_is_not_process_success():
    good=p.finish(records(),12,.039,refs());bad=p.finish(records(.041),12,.039,refs())
    assert good['finest_engineering_pass'] is True and bad['finest_engineering_pass'] is False
    assert bad['disposition']=='NO_GO_FINEST_CONTROLLED_ONSET_COMPARISON'
    assert good['production_qualified'] is False and good['first_root_proven'] is False
    assert p.finish(records(.041),4,.039,refs())['finest_engineering_pass'] is None


def test_unfinished_rejected():
    with pytest.raises(ValueError):p.finish(records()[:-1],12,.039,refs())


def test_authority_hash_before_numerics(monkeypatch):
    monkeypatch.setattr(p,'read',lambda path:b'changed')
    with pytest.raises(ValueError,match='authority'):p.reference()
    with pytest.raises(ValueError,match='authority'):p.anchor(4)


@pytest.mark.parametrize('n',(True,2,3,16))
def test_extent(n):
    with pytest.raises(ValueError):p.extent(n)
