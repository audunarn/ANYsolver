"""Offline five-channel director-hinge controls; no external/structural solve."""
import copy
import math
import struct
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest

from scripts import r8_bl5_released_director_reference as ref


@pytest.fixture(scope='module')
def specimen():
    return ref.build_reference()


def values(model, function):
    return {n:np.array(function(np.array(p)),dtype=float) for n,p in model['physical_nodes'].items()}


def binary(model,u,rf):
    nodes,elements=model['physical_nodes'],model['elements']
    chunks=[b'    1C\n    1UPGM               CalculiX\n    1UVERSION           Version 2.23\n',
            f'    2C {len(nodes)} 3\n'.encode()]
    chunks += [struct.pack('<i3d',n,*p) for n,p in nodes.items()]
    chunks += [f'    3C {len(elements)} 2\n'.encode()]
    order=(0,1,2,3,4,5,6,7,8,9,10,11,16,17,18,19,12,13,14,15)
    chunks += [struct.pack('<24i',e,4,0,1,*(ids[j] for j in order)) for e,ids in elements.items()]
    for number,name,prefix,field in ((1,'DISP','D',u),(2,'FORC','F',rf)):
        chunks += [f'    1PSTEP {number} 1 1\n  100CL 101 1.000000000 {len(field)} 0 1 3\n -4 {name} 4 1\n'.encode()]
        chunks += [f' -5 {prefix}{j} 1 2 {j} 0\n'.encode() for j in range(1,4)]
        chunks += [b' -5 ALL 1 2 0 0 1ALL\n']
        chunks += [struct.pack('<i3d',n,*v) for n,v in field.items()]
    return b''.join(chunks)+b' 9999\n'


def test_explicit_deck_identity_geometry_section_and_equation_semantics(specimen):
    deck,model=specimen
    assert len(model['physical_nodes']) == 102 and len(model['elements']) == 8
    assert deck.count('*EQUATION\n') == 25
    assert '*TIE' not in deck and '*RIGID BODY' not in deck and '*BEAM SECTION' not in deck
    assert '*ELEMENT,TYPE=C3D20,' in deck
    assert '*NODE OUTPUT,DOUBLE,NSET=ALL\nU' in deck
    assert '*NODE OUTPUT,DOUBLE,NSET=ROOT\nRF' in deck
    assert model['section']['area_m2'] == pytest.approx(.0024)
    assert model['section']['Iy_m4'] == pytest.approx(7.2e-7)
    assert model['section']['Iz_m4'] == pytest.approx(3.2e-7)
    assert ref.require_metadata(copy.deepcopy(model)) == model
    dependent=[next(iter(row)) for station in model['stations'] for row in ref.deck_rows(station)]
    assert len(set(dependent)) == 25
    assert all(n not in model['root_nodes'] for n,_ in dependent)
    assert all(term not in dependent for station in model['stations'] for row in ref.deck_rows(station)
               for term in list(row)[1:])
    destination=os.environ.get('ANYSOLVER_RELEASED_REFERENCE_PREPARE')
    if destination:
        directory=Path(destination); directory.mkdir(exist_ok=False)
        (directory/'released.inp').write_bytes(deck.encode('ascii'))
        assert hashlib.sha256((directory/'released.inp').read_bytes()).hexdigest()==model['deck_sha256']
        (directory/'model.json').write_text(json.dumps(model,indent=2)+'\n',encoding='ascii')
        (directory/'external-status.json').write_text('{"status":"NOT_EXECUTED","authority":"external smoke withheld"}\n')


def test_effective_runtime():
    import numba
    from threadpoolctl import threadpool_info
    assert numba.config.DISABLE_JIT and numba.get_num_threads()==1
    assert all(pool['num_threads']==1 for pool in threadpool_info())


def test_cli_prepares_exact_hashed_deck_bytes(monkeypatch,tmp_path):
    directory=tmp_path/'prepared'
    monkeypatch.setattr(sys,'argv',['reference','prepare','--output',str(directory)])
    ref.main()
    model=json.loads((directory/'model.json').read_text())
    assert hashlib.sha256((directory/'released.inp').read_bytes()).hexdigest()==model['deck_sha256']


@pytest.mark.parametrize('channel',range(6))
def test_rigid_reference_fields_and_unchanged_moment_origin(specimen,channel):
    _,model=specimen
    translation=np.zeros(3); spin=np.zeros(3)
    (translation if channel<3 else spin)[channel%3]=1.
    field=values(model,lambda p:translation+np.cross(spin,p))
    for station in model['stations']:
        np.testing.assert_allclose(ref.gap(station,field),0.,rtol=0.,atol=2e-14)
        action=ref.transpose_action(station,(3.,-2.,1.,.4,-.6))
        for origin in ((0.,0.,0.),(.3,-.2,.4)):
            np.testing.assert_allclose(ref.wrench(model['physical_nodes'],action,origin),0.,rtol=0.,atol=2e-14)


def test_equivalent_deck_rows_and_physical_transpose_work(specimen):
    _,model=specimen
    field=values(model,lambda p:(p[0]**2+p[1]*p[2],math.sin(p[0])+p[2],p[0]*p[1]-p[2]**2))
    for station in model['stations']:
        physical=ref.gap(station,field)
        actual=np.array([math.fsum(c*field[n][axis] for (n,axis),c in row.items()) for row in ref.deck_rows(station)])
        np.testing.assert_allclose(actual[:3],physical[:3],rtol=0.,atol=2e-14)
        np.testing.assert_allclose(actual[3:],ref.HB*physical[3:]+physical[:2],rtol=0.,atol=2e-14)
        lam=np.array((3.,-2.,1.,.4,-.6)); action=ref.transpose_action(station,lam)
        assert math.fsum(float(f@field[n]) for n,f in action.items()) == pytest.approx(float(lam@physical),abs=2e-14)


@pytest.mark.parametrize('axis',(0,1,2))
def test_director_rotations_and_compensated_free_normal_spin(specimen,axis):
    _,model=specimen; station=model['stations'][2]
    point=np.array(model['physical_nodes'][station['shell_top']]); spin=np.eye(3)[axis]*.2
    field={n:(np.cross(spin,np.array(p)-point) if n in model['beam_nodes'] else np.zeros(3))
           for n,p in model['physical_nodes'].items()}
    expected=np.array((0.,0.,0.,spin[1],-spin[0]))
    np.testing.assert_allclose(ref.gap(station,field),expected,rtol=0.,atol=2e-14)
    lam=np.array((3.,-2.,1.,.4,-.6)); action=ref.transpose_action(station,lam)
    assert math.fsum(float(f@field[n]) for n,f in action.items()) == pytest.approx(float(lam@expected),abs=2e-14)
    # Full yaw tie would reject this permitted local variation; the actual
    # material y-face secant measures yaw, which the five rows deliberately omit.
    if axis==2:
        midside={tuple(p):n for n,p in model['physical_nodes'].items() if n in model['beam_nodes']}
        plus=midside[(.5,ref.BAR_WIDTH/2,(ref.HS+ref.HB)/2)]
        minus=midside[(.5,-ref.BAR_WIDTH/2,(ref.HS+ref.HB)/2)]
        forbidden_yaw=-(field[plus][0]-field[minus][0])/ref.BAR_WIDTH
        assert forbidden_yaw == pytest.approx(.2)
        np.testing.assert_allclose(ref.gap(station,field),0.,rtol=0.,atol=2e-14)


def test_independent_director_transverse_shear_not_surface_normal(specimen):
    _,model=specimen; slope=.2
    field=values(model,lambda p:(0.,0.,slope*p[0]))
    for station in model['stations']:
        np.testing.assert_allclose(ref.gap(station,field),0.,rtol=0.,atol=2e-14)
        observed=(field[station['shell_top']]-field[station['shell_bottom']])[:2]/ref.HS
        np.testing.assert_allclose(observed,0.,rtol=0.,atol=2e-14)
        # Physical xz shear = dw/dx + director_x; substituting geometric
        # normal_x=-dw/dx would suppress the nonzero admitted shear.
        assert slope+observed[0] == pytest.approx(.2)
        assert abs(observed[0]-(-slope)) > .1


def test_independent_elastic_internal_covectors_affine_patch_energy(specimen):
    _,model=specimen; strain=1e-5
    field=values(model,lambda p:(strain*p[0],-ref.NU*strain*p[1],-ref.NU*strain*p[2]))
    covectors=ref.internal_covectors(model,field)
    work=math.fsum(float(force@field[n]) for forces in covectors.values() for n,force in forces.items())
    volume=ref.LENGTH*(ref.WIDTH*ref.HS+ref.BAR_WIDTH*ref.HB)
    assert work == pytest.approx(ref.E*strain**2*volume,rel=2e-12)
    for forces in covectors.values():
        np.testing.assert_allclose(ref.wrench(model['physical_nodes'],forces),0.,rtol=0.,atol=2e-9)


def bound_fixture(monkeypatch,tmp_path):
    executable=tmp_path/'synthetic-ccx.exe'; executable.write_bytes(b'offline parser fixture; not a solver')
    digest=lambda value:hashlib.sha256(value).hexdigest()
    monkeypatch.setattr(ref,'CCX_SHA256',digest(executable.read_bytes()))
    deck,model=ref.build_reference(); u=values(model,lambda p:(0.,0.,0.))
    rf={n:(0.,0.,0.) for n in model['root_nodes']}
    data=binary(model,u,rf); stdout='Job finished'; sta='1 1 1 1 1.0 1.0 1.0'
    binding=dict(schema='R8_BL5_RELEASED_REFERENCE_EXECUTION_V1',status='completed',exit_code=0,
        command=[str(executable.resolve()),'-i','released'],working_directory=str(tmp_path.resolve()),
        executable_sha256=ref.CCX_SHA256,model_sha256=model['model_sha256'],
        files={'released.inp':digest(deck.encode('ascii')),'released.frd':digest(data),
               'stdout.log':digest(stdout.encode()),'stderr.log':digest(b''),'released.sta':digest(sta.encode())})
    return deck,model,data,stdout,sta,binding,executable


def test_strict_binary_parser_exposes_unbalanced_fixture_without_acceptance(monkeypatch,tmp_path):
    deck,model,data,stdout,sta,binding,executable=bound_fixture(monkeypatch,tmp_path)
    result=ref.parse_output(data,stdout,sta,model,deck_bytes=deck.encode('ascii'),
                            execution_binding=binding,executable_path=executable,working_directory=tmp_path)
    assert result['status']=='PARSED_REFERENCE_NOT_ASSESSED'
    assert result['free_equilibrium_unexplained_max']==1.
    assert result['applied_pairing_J']==0.
    assert set(result['domain_cuts'])=={'shell','beam'}
    assert not result['physical_comparison_permitted']
    unverified=ref.parse_output(data,stdout,sta,model,deck_bytes=deck.encode('ascii'))
    assert unverified['status']=='UNVERIFIED_EXECUTION'
    assert 'displacement' not in unverified


@pytest.mark.parametrize('kind',('metadata','hash','exit','completion','sta','truncated','nonfinite','mpc','support','load','nodeck'))
def test_parser_rejects_wrong_identity_partial_or_invalid_output(monkeypatch,tmp_path,kind):
    deck,model,data,stdout,sta,binding,executable=bound_fixture(monkeypatch,tmp_path)
    if kind=='metadata': model['geometry_m']['length']=2.
    if kind=='hash': executable.write_bytes(b'changed executable bytes')
    if kind=='exit': binding['exit_code']=1
    if kind=='completion': stdout='partial'
    if kind=='sta': sta='1 1 1 1 .5 .5 .5'
    if kind=='truncated': data=data[:-1]
    if kind=='nonfinite':
        n=next(iter(model['physical_nodes'])); data=data.replace(struct.pack('<i3d',n,0.,0.,0.),struct.pack('<i3d',n,math.nan,0.,0.))
    if kind=='mpc': deck=deck.replace('*EQUATION\n2','*EQUATION\n3',1)
    if kind=='support': deck=deck.replace('ROOT,1,3,0.','ROOT,1,2,0.')
    if kind=='load': deck=deck.replace(f"{model['load_node']},3,1.",f"{model['load_node']},3,2.")
    # Invalid complete output may itself be faithfully hash-bound. Exercise
    # dataset/completion semantics, rather than only stale manifest rejection.
    if kind in ('completion','sta','truncated','nonfinite'):
        binding['files']['released.frd']=hashlib.sha256(data).hexdigest()
        binding['files']['stdout.log']=hashlib.sha256(stdout.encode()).hexdigest()
        binding['files']['released.sta']=hashlib.sha256(sta.encode()).hexdigest()
    with pytest.raises(ref.ReferenceParseError):
        ref.parse_output(data,stdout,sta,model,deck_bytes=None if kind=='nodeck' else deck.encode('ascii'),execution_binding=binding,
                         executable_path=executable,working_directory=tmp_path)


def test_root_RF_bookkeeping_retains_interface_difference(specimen):
    _,model=specimen; field=values(model,lambda p:(1e-5*p[0],0.,0.))
    elements=ref.internal_covectors(model,field)
    internal={n:np.zeros(3) for n in model['physical_nodes']}
    for forces in elements.values():
        for n,value in forces.items(): internal[n]+=value
    rf={n:internal[n] for n in model['root_nodes']}
    result=ref.recover_response(model,field,rf)
    assert result['root_internal_RF_difference_max']==0.
    assert result['support_RF_difference_max']>1.
    assert 'separately recovered interface' in result['root_RF_interpretation']


def test_actual_saved_smoke_equations_work_and_RF_bookkeeping():
    source=os.environ.get('ANYSOLVER_RELEASED_SAVED_SMOKE')
    if not source: pytest.skip('actual external response is separately authorized and saved')
    directory=Path(source)
    model=json.loads((directory/'model.json').read_text())
    manifest=json.loads((directory/'execution-binding.json').read_text())
    result=ref.parse_output((directory/'released.frd').read_bytes(),
        (directory/'stdout.log').read_bytes().decode('utf-8'),
        (directory/'released.sta').read_bytes().decode('utf-8'),model,
        deck_bytes=(directory/'released.inp').read_bytes(),execution_binding=manifest,
        executable_path=manifest['command'][0],working_directory=directory,
        stderr=(directory/'stderr.log').read_bytes().decode('utf-8'))
    # Existing development numerical controls, not physical accuracy criteria.
    assert result['free_equilibrium_unexplained_max'] <= 1e-8
    assert np.max(np.abs(result['full_constraint_gap'])) <= 1e-9
    assert np.max(np.abs(result['total_external_wrench'])) <= 1e-8
    assert result['root_internal_RF_difference_max'] <= 1e-8
    assert result['support_RF_difference_max'] > 1.
    assert abs(result['internal_pairing_J']-result['applied_pairing_J']) <= 1e-8
    assert abs(result['interface_pairing_J']) <= 1e-8
    assert result['support_pairing_J']==0.
    assert not result['physical_comparison_permitted']
    with (directory/'parsed-v2.json').open('x',encoding='ascii') as stream:
        stream.write(ref._json(result))
