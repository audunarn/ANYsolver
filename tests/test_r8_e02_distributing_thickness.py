"""Fixed prospective geometry and strict legacy/new input/output separation."""
from pathlib import Path
import hashlib
from copy import deepcopy
import json
import numpy as np,pytest
from scripts.r8_e02_distributing_thickness import build_case,parse_result,SCHEMA
from scripts.r8_e02_distributing_feasibility import build_case as old_build,parse_result as old_parse,LOADS,PORT
from scripts.r8_e02_rigid_tip_reference import ReferenceParseError
from test_r8_e02_distributing_feasibility import _synthetic


@pytest.fixture(scope='module')
def cases():return {name:build_case(name) for name in ('Mx','Fy')}


@pytest.mark.parametrize('name',('Mx','Fy'))
def test_fixed_geometry_preserves_physics_and_resource_guards(cases,name):
    deck,metadata,area=cases[name]
    assert metadata['schema']==SCHEMA and (metadata['nx'],metadata['ny'],metadata['nz'])==(40,16,4)
    assert len(metadata['elements'])==2560 and 3*len(metadata['physical_nodes'])<100000
    assert min(p[2] for p in metadata['physical_nodes'].values())==-.01
    assert max(p[2] for p in metadata['physical_nodes'].values())==.01
    assert len({p[2] for p in metadata['physical_nodes'].values()})==9
    assert all(metadata['physical_nodes'][n][0]==0. for n in metadata['root_nodes'])
    assert '*RIGID BODY' not in deck and '*EQUATION' not in deck and '*ELEMENT,TYPE=C3D20R' in deck
    assert area.area_m2==pytest.approx(.01,abs=1e-17)
    np.testing.assert_allclose(area.centroid_m,(.9,-.025,0.),atol=1e-16,rtol=0)
    action=area.action(LOADS[name][:3],LOADS[name][3:]);force,moment=action.resultant()
    np.testing.assert_allclose(force,LOADS[name][:3],atol=2e-12,rtol=0)
    np.testing.assert_allclose(moment,np.array(LOADS[name][3:])+np.cross(PORT,LOADS[name][:3]),atol=2e-12,rtol=0)
    t=np.array((1e-6,-2e-6,3e-6));w=np.array((1e-5,-2e-5,3e-5))
    u={n:t+np.cross(w,p) for n,p in metadata['physical_nodes'].items()}
    observed=area.recover(u)
    np.testing.assert_allclose(observed.rotation_components_rad,w,atol=2e-18,rtol=0)
    assert action.work(u)==pytest.approx(np.dot(force,t)+np.dot(moment,w),abs=2e-17)
    # Verify the actual encoded deck action, rather than only the pre-rounding
    # area operator. No tiny coefficients are discarded to satisfy CCX syntax.
    encoded=deck.split('*CLOAD\n')[1].split('*NODE PRINT')[0].splitlines()
    f=np.zeros(3);m=np.zeros(3);work=0.
    assert len(encoded)==np.count_nonzero(action.forces_n)
    for line in encoded:
        node,dof,value=line.split(',');assert len(value)<=20
        vector=np.zeros(3);vector[int(dof)-1]=float(value);node=int(node)
        f+=vector;m+=np.cross(metadata['physical_nodes'][node],vector)
        work+=np.dot(vector,u[node])
    np.testing.assert_allclose(f,force,atol=2e-12,rtol=0)
    np.testing.assert_allclose(m,moment,atol=2e-12,rtol=0)
    assert work==pytest.approx(action.work(u),abs=2e-17)


@pytest.mark.parametrize('name',('Mx','Fy'))
def test_new_parser_reconstructs_case_and_old_parser_rejects_it(cases,name):
    _,metadata,_=cases[name];dat,stdout=_synthetic(metadata)
    assert parse_result(dat,stdout,json.loads(json.dumps(metadata)))['status']=='PARSED_DEVELOPMENT_ONLY'
    with pytest.raises(ReferenceParseError):old_parse(dat,stdout,metadata)
    other=deepcopy(metadata);other['nz']=2
    with pytest.raises(ReferenceParseError):parse_result(dat,stdout,other)
    with pytest.raises(ReferenceParseError):parse_result(dat,stdout.replace('1 cpu','2 cpu'),metadata)
    with pytest.raises(ReferenceParseError):parse_result(dat,stdout.replace('Job finished',''),metadata)


def test_saved_legacy_six_decks_metadata_and_parses_are_exact():
    root=Path(__file__).resolve().parents[1]/'.qualification/b3-ge-e4-pl/r8-distributing-multihost-dev-20261004-v1'
    binding=json.loads((root/'paired-binding-v1.json').read_text(encoding='utf-8'))
    for nx,ny in ((10,4),(20,8),(40,16)):
        for name in ('Mx','Fy'):
            case=root/f'ccx-{nx}x{ny}-{name}-v1'
            deck,metadata,_=old_build(name,nx,ny)
            # Historical execution used CRLF; its actual bytes and the generator's
            # canonical LF hash are separately bound, not silently conflated.
            assert deck==(case/'reference.inp').read_text(encoding='ascii')
            assert hashlib.sha256(deck.encode('ascii')).hexdigest()==metadata['deck_sha256']
            assert hashlib.sha256((case/'reference.inp').read_bytes()).hexdigest()==binding['cases'][f'{nx}x{ny}-{name}']['deck_sha256']
            assert json.loads(json.dumps(metadata))==json.loads((case/'metadata.json').read_text(encoding='utf-8'))
            parsed=old_parse((case/'reference.dat').read_text(),(case/'execution-v1/stdout.log').read_text(),metadata)
            assert json.loads(json.dumps(parsed))==json.loads((case/'parsed-v1.json').read_text(encoding='utf-8'))


def test_historical_and_new_guards_remain_explicit():
    with pytest.raises(ValueError):old_build('Mx',80,32)
    with pytest.raises(ValueError):build_case('My')
