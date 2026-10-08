"""New direction keeps physical action, strict identity and old route guards."""
from copy import deepcopy
import json
import numpy as np,pytest
from scripts import r8_e02_distributing_feasibility as old
from scripts.r8_e02_distributing_thickness import build_case as thickness
from scripts import r8_e02_distributing_my as new
from scripts.r8_e02_rigid_tip_reference import ReferenceParseError
from test_r8_e02_distributing_feasibility import _synthetic


@pytest.fixture(scope='module')
def case():return new.build_case()


def test_decoded_my_deck_wrench_and_work(case):
    text,metadata,area=case
    assert metadata['schema']==new.SCHEMA and metadata['case']=='My'
    assert (metadata['nx'],metadata['ny'],metadata['nz'])==(40,16,4)
    assert len(metadata['elements'])==2560 and 3*len(metadata['physical_nodes'])<100000
    original,_,_=thickness('Mx')
    assert text.split('*CLOAD\n')[0]==original.split('*CLOAD\n')[0]
    assert text.split('*NODE PRINT')[1:]==original.split('*NODE PRINT')[1:]
    f=np.zeros(3);m=np.zeros(3);work=0.
    t=np.array((1e-6,-2e-6,3e-6));w=np.array((1e-5,-2e-5,3e-5))
    field={n:t+np.cross(w,p) for n,p in metadata['physical_nodes'].items()}
    action=area.action(new.WRENCH[:3],new.WRENCH[3:])
    lines=text.split('*CLOAD\n')[1].split('*NODE PRINT')[0].splitlines()
    assert len(lines)==np.count_nonzero(action.forces_n)
    for line in lines:
        node,dof,value=line.split(',');assert len(value)<=20
        n=int(node);v=np.zeros(3);v[int(dof)-1]=float(value)
        f+=v;m+=np.cross(metadata['physical_nodes'][n],v);work+=np.dot(v,field[n])
    np.testing.assert_allclose(f,(0,0,0),atol=2e-12,rtol=0)
    np.testing.assert_allclose(m,(0,1,0),atol=2e-12,rtol=0)
    assert work==pytest.approx(action.work(field),abs=2e-17)
    assert work==pytest.approx(w[1],abs=2e-17)


def test_my_reconstruction_and_malformed_identity(case):
    _,metadata,_=case;dat,stdout=_synthetic(metadata)
    assert new.parse_result(dat,stdout,json.loads(json.dumps(metadata)))['status']=='PARSED_DEVELOPMENT_ONLY'
    wrong=deepcopy(metadata);wrong['applied_wrench']=(0.,0.,0.,1.,0.,0.)
    with pytest.raises(ReferenceParseError):new.parse_result(dat,stdout,wrong)
    with pytest.raises(ReferenceParseError):old.parse_result(dat,stdout,metadata)
    with pytest.raises(ReferenceParseError):new.parse_result(dat,stdout.replace('1 cpu','2 cpu'),metadata)
    with pytest.raises(ReferenceParseError):new.parse_result(dat,stdout.replace('Job finished',''),metadata)
    for value in (float('nan'),object()):
        wrong=deepcopy(metadata);wrong['applied_wrench']=value
        with pytest.raises(ReferenceParseError):new.parse_result(dat,stdout,wrong)


def test_native_dispatch_and_legacy_guards(monkeypatch):
    received=[]
    def capture(nx,ny,loads):received.append((nx,ny,dict(loads)));return 'captured'
    monkeypatch.setattr(old,'_native_load_cases',capture)
    assert old.native_cases(20,8)=='captured' and received[-1]==(20,8,old.LOADS)
    monkeypatch.setattr(new,'_native_load_cases',capture)
    assert new.native_case()=='captured' and received[-1]==(40,16,{'My':new.WRENCH})
    assert tuple(old.LOADS)==('Mx','Fy')
    with pytest.raises(ValueError):old.build_case('My',40,16)
    with pytest.raises(ValueError):thickness('My')
