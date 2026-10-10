"""Constructed source controls only: no CCX run or scientific acceptance."""
import copy
import json
import math
import struct
from pathlib import Path

import numpy as np
import pytest

from scripts.r8_e02_rigid_precision import (
    ORIGINAL, ELIMINATED, build_precision_deck, parse_precision_result,
    physical_pose_and_work, root_elimination_proof, root_wrench, compare_precision_pair,
)
from scripts.r8_e02_rigid_tip_reference import ReferenceParseError, build_deck


def fixture(variant=ELIMINATED, load="Mx", sign=1):
    deck, manifest = build_precision_deck(10, 4, sign, load, variant=variant)
    b = manifest["base"]
    translation, theta = (2e-6,-3e-6,4e-6), (1.7e-5,2e-6,-3e-6)
    port = b["control_nodes"][b["controls"]["patch_ref"]]
    u = {n:(0.,0.,0.) for n in b["physical_nodes"]}
    for n in b["patch_nodes"]:
        r = np.array(b["physical_nodes"][n])-port
        u[n] = tuple(np.array(translation)+np.cross(theta,r))
    # Independent reaction distribution: pure root Mx couple for default load.
    rf = {n:(0.,0.,0.) for n in b["root_nodes"]}
    lo = min(b["root_nodes"],key=lambda n:b["physical_nodes"][n][1])
    hi = max(b["root_nodes"],key=lambda n:b["physical_nodes"][n][1])
    rf[lo], rf[hi] = (0.,0.,5.), (0.,0.,-5.)
    chunks = [b"1C\n1UPGM               CalculiX\n1UVERSION           Version 2.23\n",
              f'2C {len(u)} 3\n'.encode()]
    chunks += [struct.pack("<i3d",n,*p) for n,p in b["physical_nodes"].items()]
    chunks += [f'3C {len(b["elements"])} 2\n'.encode()]
    order = list(range(12))+list(range(16,20))+list(range(12,16))
    chunks += [struct.pack("<24i",e,4,0,1,*(c[j] for j in order)) for e,c in b["elements"].items()]
    for number,name,prefix,values in ((1,"DISP","D",u),(2,"FORC","F",rf)):
        chunks += [f'1PSTEP {number} 1 1\n100CL 101 1.000000000 {len(values)} 0 1 3\n-4 {name} 4 1\n'.encode()]
        chunks += [f'-5 {prefix}{j} 1 2 {j} 0\n'.encode() for j in (1,2,3)]
        chunks += [b"-5 ALL 1 2 0 0 1ALL\n"]
        chunks += [struct.pack("<i3d",n,*v) for n,v in values.items()]
    chunks += [b"9999\n"]
    controls = {n:(0.,0.,0.) for n in b["control_nodes"]}
    controls[b["controls"]["patch_ref"]] = translation
    controls[b["controls"]["patch_rot"]] = theta
    reactions = {n:(0.,0.,0.) for n in controls}
    dat = ""
    for name,group,values in (("displacements","CONTROLS",controls),
            ("forces","CONTROLS",reactions),
            ("displacements","PATCH",{n:u[n] for n in b["patch_nodes"]}),
            ("displacements","ROOT",{n:u[n] for n in b["root_nodes"]})):
        dat += f'{name} (vx,vy,vz) for set {group} and time 1.0000000E+00\n\n'
        dat += ''.join(f'{n} '+ ' '.join(f'{v:.6E}' for v in p)+'\n' for n,p in values.items())
    dat += 'internal energy (element, energy) for set SOLID and time 1.0000000E+00\n\n'
    dat += ''.join(f'{e} 1.000000E-08\n' for e in b["elements"])
    stdout = 'CalculiX Version 2.23,\n Using up to 1 cpu(s)\n Job finished\n'
    return b''.join(chunks),dat,stdout,deck,manifest,u,rf


def test_output_only_candidate_and_exact_original_geometry_load_identity():
    _,_,_,deck,m,_,_ = fixture()
    original,base = build_deck(10,4,1,"Mx")
    assert m["base"] == base
    assert '*RIGID BODY,NSET=ROOT' not in deck
    assert 'ROOT,1,3,0.\n*' in deck
    assert '*RIGID BODY,NSET=PATCH' in deck
    assert '*NODE OUTPUT,DOUBLE,NSET=ALL\nU' in deck
    assert '*NODE OUTPUT,DOUBLE,NSET=ROOT\nRF' in deck
    assert '*EL PRINT,ELSET=SOLID\nELSE' in deck
    assert '*RIGID BODY,NSET=ROOT' in original
    assert build_deck(10,4,1,"Mx") == (original,base)


@pytest.mark.parametrize('nz', (2,4,8))
def test_fixed_root_row_space_and_all_thickness_midside_coverage(nz):
    _,m = build_precision_deck(20,8,1,"Mx",nz=nz)
    b = m["base"]
    proof = root_elimination_proof(b)
    assert proof["both_directions_proved"]
    assert proof["fixed_physical_dofs"] == 3*len(b["root_nodes"])
    # Grounded old six-coordinate map gives zero at every corner/midside node.
    for n in b["root_nodes"]:
        assert tuple(np.cross(np.zeros(3), b["physical_nodes"][n])) == (0.,0.,0.)
    assert root_elimination_proof(json.loads(json.dumps(b))) == proof


@pytest.mark.parametrize('load', ('Fz','Mx','My'))
@pytest.mark.parametrize('sign', (-1,1))
def test_physical_port_and_independent_force_moment_work_map(load,sign):
    *_,m,u,rf = fixture(load=load,sign=sign)
    result = physical_pose_and_work(m["base"],u)
    assert result["translation_m"] == pytest.approx((2e-6,-3e-6,4e-6),abs=1e-18)
    assert result["theta_rad"] == pytest.approx((1.7e-5,2e-6,-3e-6),abs=1e-18)
    assert result["external_final_pairing_J"] == pytest.approx(result["port_pairing_J"],rel=1e-13)
    assert result["load_moment_about_port_Nm"] == pytest.approx(m["base"]["applied_moment_Nm"],abs=1e-13)


def test_root_dual_wrench_and_virtual_work_with_nonzero_lever_arms():
    *_,m,u,rf = fixture()
    b = m["base"]
    wrench = root_wrench(b,rf)
    assert wrench == pytest.approx((0,0,0,-1,0,0))
    v,theta = np.array((.1,-.2,.3)),np.array((.4,-.5,.6))
    work = math.fsum(float(np.array(f)@(v+np.cross(theta,b["physical_nodes"][n]))) for n,f in rf.items())
    assert work == pytest.approx(float(np.array(wrench[:3])@v+np.array(wrench[3:])@theta))
    bad = dict(rf); bad.pop(next(iter(bad)))
    with pytest.raises(ReferenceParseError,match='reaction'):
        root_wrench(b,bad)
    wrong = {n:tuple(-x for x in f) for n,f in rf.items()}
    assert root_wrench(b,wrong)[3] == pytest.approx(1.)


def test_integrated_print_energy_is_independent_but_no_gate_pass():
    data,dat,stdout,deck,m,_,_ = fixture()
    r = parse_precision_result(data,dat,stdout,deck,m)
    assert r['root_binary_field_is_reaction'] and not r['acceptance']
    assert r['root_wrench_residual'] == pytest.approx((0,0,0,0,0,0))
    assert r['independent_integrated_internal_energy_J'] == pytest.approx(80e-8)
    assert r['energy_print_rounding_bound_J'] > 1e-8*r['independent_integrated_internal_energy_J']
    assert not r['can_certify_energy_work_1e_minus_8']
    assert not r['control_nodes_in_binary']
    assert r['paired_original_DAT_root_wrench_within_rounding'] is None


@pytest.mark.parametrize('before', ('displacements (vx,vy,vz) for set CONTROLS',
    'forces (vx,vy,vz) for set CONTROLS','displacements (vx,vy,vz) for set PATCH',
    'displacements (vx,vy,vz) for set ROOT'))
def test_actual_print_groups_accept_element_energy_before_or_between_nodal_groups(before):
    data,dat,stdout,deck,m,_,_ = fixture()
    start = dat.index('internal energy (')
    nodal,energy = dat[:start],dat[start:]
    index = nodal.index(before)
    changed = nodal[:index]+energy+nodal[index:]
    assert parse_precision_result(data,changed,stdout,deck,m) == parse_precision_result(data,dat,stdout,deck,m)


def test_saved_ccx_two_space_time_header_and_bounded_ascii_whitespace():
    data,dat,stdout,deck,m,_,_ = fixture()
    old = 'internal energy (element, energy) for set SOLID and time 1.0000000E+00'
    real = ' internal energy (element, energy) for set SOLID and time  0.1000000E+01'
    expected = parse_precision_result(data,dat,stdout,deck,m)
    assert parse_precision_result(data,dat.replace(old,real),stdout,deck,m) == expected
    assert parse_precision_result(data,dat.replace(old,real.replace('time  ','time\t ')),stdout,deck,m) == expected
    for bad in (real.replace('time  ','time\n '),real.replace('time  ','time\u00a0 '),
                real.replace('time  ','time         '),real.replace('SOLID','OTHER'),
                real.replace('(element, energy)','(elem, integ.pnt.,energy)')):
        with pytest.raises(ReferenceParseError,match='ELSE'):
            parse_precision_result(data,dat.replace(old,bad),stdout,deck,m)


def test_saved_original_full_binary_and_dat_replay_without_equilibrium():
    evidence = Path(__file__).resolve().parents[1]/'.development/e02-rigid-precision-20261009-v1/numerical-attempt2/original-rigid-root'
    if not (evidence/'reference.frd').exists():
        pytest.skip('saved development result is not present in this checkout')
    deck = (evidence/'reference.inp').read_text()
    manifest = json.loads((evidence/'candidate.json').read_text())
    result = parse_precision_result((evidence/'reference.frd').read_bytes(),
        (evidence/'reference.dat').read_text(),(evidence/'stdout.txt').read_text(),deck,manifest)
    assert result['variant'] == ORIGINAL
    assert not result['root_binary_field_is_reaction'] and not result['acceptance']
    assert result['port']['external_final_pairing_J'] > 0
    assert result['independent_integrated_internal_energy_J'] > 0
    assert result['root_displacement_max_m'] == 0


def _packet(f):
    data,dat,stdout,deck,manifest,*_ = f
    return dict(data=data,dat=dat,stdout=stdout,deck=deck,manifest=manifest)


def _saved_packet(path):
    return dict(data=(path/'reference.frd').read_bytes(),dat=(path/'reference.dat').read_text(),
        stdout=(path/'stdout.txt').read_text(),deck=(path/'reference.inp').read_text(),
        manifest=json.loads((path/'candidate.json').read_text()))


def test_saved_pair_report_retains_support_failure_without_hiding_physical_equality():
    evidence=Path(__file__).resolve().parents[1]/'.development/e02-rigid-precision-20261009-v1'
    original=evidence/'numerical-attempt2/original-rigid-root'
    eliminated=evidence/'numerical-attempt3/static-fixed-root-elimination'
    if not (eliminated/'reference.frd').exists():
        pytest.skip('saved pair is absent from this checkout')
    r=compare_precision_pair(_saved_packet(original),_saved_packet(eliminated))
    assert not r['supporting_original_DAT_wrench_check_passed'] and not r['acceptance']
    assert r['failed_support_components'] == ['Fx','Fy','Fz','My']
    assert r['physical_displacement_binary64_vectors_equal']
    assert r['physical_displacement_node_count'] == 7493
    assert r['physical_pose_delta'] == {'translation_m':[0.,0.,0.],'theta_rad':[0.,0.,0.]}
    assert r['final_pairing_delta_J'] == 0. and r['integrated_energy_delta_J'] == 0.
    assert r['new_direct_root_wrench_max_abs_residual'] < 1e-8
    assert r['normalized_root_balance_acceptance'] == 'NOT_EVALUATED'
    assert not r['original_ROOT_field_reaction_interpretation_supported']


def test_pair_report_refuses_wrong_variant_and_exact_load_mismatch():
    original=_packet(fixture(ORIGINAL))
    eliminated=_packet(fixture(ELIMINATED))
    r=compare_precision_pair(original,eliminated)
    assert not r['supporting_original_DAT_wrench_check_passed']
    assert r['physical_displacement_binary64_vectors_equal'] and not r['acceptance']
    for bad in (original,_packet(fixture(ELIMINATED,load='My'))):
        with pytest.raises(ReferenceParseError,match='paired'):
            compare_precision_pair(original,bad)


def test_original_root_field_remains_explicitly_unsupported():
    data,dat,stdout,deck,m,_,_ = fixture(ORIGINAL)
    r = parse_precision_result(data,dat,stdout,deck,m)
    assert not r['root_binary_field_is_reaction']
    assert r['root_wrench_residual'] is None and not r['acceptance']
    assert any('MPC' in b for b in r['blockers'])


def test_reaction_sign_error_and_print_consistency_never_become_acceptance():
    data,dat,stdout,deck,m,u,rf = fixture()
    n = next(n for n,f in rf.items() if f != (0.,0.,0.))
    bad = data.replace(struct.pack('<i3d',n,*rf[n]),
                       struct.pack('<i3d',n,*(-x for x in rf[n])))
    r = parse_precision_result(bad,dat,stdout,deck,m)
    assert max(abs(x) for x in r['root_wrench_residual']) > .1
    assert not r['acceptance']
    old_dat = dat[:dat.index('internal energy (')]
    r = parse_precision_result(data,dat,stdout,deck,m,paired_original_dat=old_dat)
    assert not r['paired_original_DAT_root_wrench_within_rounding']
    assert not r['acceptance']


def test_refuse_nonfixed_nonlinear_or_unregistered_ground_deck():
    data,dat,stdout,deck,m,_,_ = fixture()
    for wrong in (deck.replace('ROOT,1,3,0.','ROOT,1,3,0.1'),
                  deck.replace('*STEP','*STEP,NLGEOM'),
                  deck.replace('ROOT,1,3,0.','ROOT,1,2,0.')):
        with pytest.raises(ReferenceParseError):
            parse_precision_result(data,dat,stdout,wrong,m)


@pytest.mark.parametrize('change', ('sign','load_name','geometry_m','controls','root_nodes','physical_nodes'))
def test_tampered_geometry_load_lever_arm_or_root_is_refused(change):
    data,dat,stdout,deck,m,_,_ = fixture()
    bad = copy.deepcopy(m)
    bad['base'][change] = {'changed':True} if change not in ('sign','load_name') else (-1 if change=='sign' else 'My')
    with pytest.raises(ReferenceParseError):
        parse_precision_result(data,dat,stdout,deck,bad)
    with pytest.raises(ReferenceParseError):
        parse_precision_result(data,dat,stdout,deck+'**extra\n',m)


def test_omitted_reaction_and_incomplete_or_unsupported_energy_refused():
    data,dat,stdout,deck,m,_,_ = fixture()
    for bad in (data[:-32],data.replace(b'FORC',b'STRE',1)):
        with pytest.raises(ReferenceParseError):
            parse_precision_result(bad,dat,stdout,deck,m)
    for bad in (dat.rsplit('\n',2)[0]+'\n',dat.replace('internal energy (element, energy)','internal energy density (elem, integ.pnt.,energy)'),dat+'1 1.000000E-08\n'):
        with pytest.raises(ReferenceParseError):
            parse_precision_result(data,bad,stdout,deck,m)


def test_nonrigid_physical_patch_is_refused():
    *_,m,u,rf = fixture()
    node = m['base']['patch_nodes'][0]
    u[node] = (1.,0.,0.)
    with pytest.raises(ReferenceParseError,match='not a rigid'):
        physical_pose_and_work(m['base'],u)
