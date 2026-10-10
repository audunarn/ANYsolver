"""Physical signs, common-station semantics and refusal controls; no solve."""
import copy
import json
from pathlib import Path
import struct

import numpy as np
import pytest

from scripts.r8_e02_native_rigid_tip import geometry
from scripts.r8_e02_rigid_precision import build_precision_deck
from scripts.r8_e02_rigid_torque_fields import CASE,_observations,compare_fields,external_common_fields,validate_native


def native_fixture():
    nodes,_,_,patch,root=geometry(40,16)
    q=[]
    for x,y,z in nodes.values():
        # Infinitesimal rigid Mx pose: u_y=-theta*z, u_z=theta*y.
        q.append((0.,0.,2e-5*y,2e-5,0.,0.))
    return dict(case=copy.deepcopy(CASE),node_ids=list(nodes),coordinates_m=list(nodes.values()),
        shell_coordinates=q,patch_nodes=list(patch),root_nodes=list(root),
        director_contract='reference-linear spatial theta; delta d=theta cross e_z',
        port_coordinates=[0.,-1e-6,0.,2e-5,0.,0.],guards={'constructed':True})


def solid_fixture():
    deck,m=build_precision_deck(40,16,1,'Mx')
    b=m['base'];u={n:(0.,-2e-5*p[2],2e-5*p[1]) for n,p in b['physical_nodes'].items()}
    root={n:(0.,0.,0.) for n in b['root_nodes']}
    chunks=[b'1C\n1UPGM               CalculiX\n1UVERSION           Version 2.23\n',f"2C {len(u)} 3\n".encode()]
    chunks += [struct.pack('<i3d',n,*p) for n,p in b['physical_nodes'].items()]
    chunks += [f"3C {len(b['elements'])} 2\n".encode()]
    order=list(range(12))+list(range(16,20))+list(range(12,16))
    chunks += [struct.pack('<24i',e,4,0,1,*(ids[j] for j in order)) for e,ids in b['elements'].items()]
    for index,name,prefix,values in ((1,'DISP','D',u),(2,'FORC','F',root)):
        chunks += [f'1PSTEP {index} 1 1\n100CL 101 1.000000000 {len(values)} 0 1 3\n-4 {name} 4 1\n'.encode()]
        chunks += [f'-5 {prefix}{j} 1 2 {j} 0\n'.encode() for j in (1,2,3)]
        chunks += [b'-5 ALL 1 2 0 0 1ALL\n']
        chunks += [struct.pack('<i3d',n,*v) for n,v in values.items()]
    chunks += [b'9999\n']
    return b''.join(chunks),deck,m


def test_common_physical_secant_rigid_rotation_sign_and_no_geometric_normal_assumption():
    data,deck,m=solid_fixture()
    u,theta,secant=external_common_fields(data,deck,m)
    assert u.shape==(41,17,3)
    assert theta[:,:,0]==pytest.approx(np.full((41,17),2e-5),abs=1e-18)
    assert theta[:,:,1]==pytest.approx(np.zeros((41,17)),abs=1e-18)
    assert secant[:,:,1]==pytest.approx(np.full((41,17),-2e-5),abs=1e-18)
    q=validate_native(native_fixture())
    observed=_observations(q[:,:,:3],q[:,:,3:5])
    assert observed['shear_y_indicator']==pytest.approx(np.zeros((41,17)),abs=1e-17)
    # Independent director field need not coincide with geometric normal.
    observed=_observations(q[:,:,:3],q[:,:,3:5]*.5)
    assert observed['shear_y_indicator']==pytest.approx(np.full((41,17),1e-5),abs=1e-17)


def test_quadratic_twist_stencil_and_zero_pair_mismatch():
    q=validate_native(native_fixture())
    x=np.arange(41)[:,None]*.025;y=np.arange(17)[None,:]*.0125-.1
    q[:,:,2]=3e-5*x*y
    observed=_observations(q[:,:,:3],q[:,:,3:5])
    assert observed['transverse_mixed_twist_per_m']==pytest.approx(np.full((41,17),3e-5),abs=1e-16)
    data,deck,m=solid_fixture()
    r=compare_fields(native_fixture(),data,deck,m)
    assert r['status']=='PHYSICAL_FIELD_DEVELOPMENT_ONLY' and not r['acceptance']
    assert r['mid_surface_translation_delta_max_m']==pytest.approx((0.,0.,0.),abs=1e-18)
    assert r['free_span_width_average_tilt_difference_rad']==pytest.approx(0.,abs=1e-18)
    assert list(r['region_metrics'])==['root_neighborhood','smooth_free_span','patch_derivative_neighborhood','rigid_patch_interior']


def test_distributed_tilt_difference_allocations_telescope_without_causal_claim():
    data,deck,m=solid_fixture()
    native=native_fixture()
    native['shell_coordinates']=[list(q) for q in native['shell_coordinates']]
    for xyz,q in zip(native['coordinates_m'],native['shell_coordinates']):
        q[3] += 1e-6*xyz[0]
    r=compare_fields(native,data,deck,m)
    values=r['tilt_difference_allocation']
    assert sum(v['accumulated_tilt_difference_rad'] for v in values)==pytest.approx(8e-7,abs=1e-18)
    assert [v['signed_fraction_of_free_span_difference'] for v in values]==pytest.approx((.0625,.875,.0625),abs=1e-12)
    assert 'does not prove' in r['causality']


@pytest.mark.parametrize('field',('case','node_ids','coordinates_m','shell_coordinates','patch_nodes','root_nodes','director_contract'))
def test_refuse_incomplete_changed_or_ambiguous_native_contract(field):
    native=native_fixture();native[field]=None
    with pytest.raises((ValueError,TypeError)):
        validate_native(native)


def test_refuse_other_mesh_load_sign_reference_variant_and_tampered_deck():
    data,deck,m=solid_fixture()
    for nx,ny,sign,load in ((20,8,1,'Mx'),(40,16,-1,'Mx'),(40,16,1,'My')):
        other,manifest=build_precision_deck(nx,ny,sign,load)
        with pytest.raises(ValueError):
            external_common_fields(data,other,manifest)
    with pytest.raises(ValueError):
        external_common_fields(data,deck+'**changed\n',m)


def test_saved_external_exact_case_has_common_mid_and_both_thickness_faces():
    root=Path(__file__).resolve().parents[1]
    path=root/'.development/e02-rigid-precision-20261009-v1/numerical-attempt3/static-fixed-root-elimination'
    if not (path/'reference.frd').exists():pytest.skip('saved external development fields absent')
    u,tilt,secant=external_common_fields((path/'reference.frd').read_bytes(),
        (path/'reference.inp').read_text(),json.loads((path/'candidate.json').read_text()))
    assert np.isfinite(u).all() and np.isfinite(tilt).all()
    assert u.shape==(41,17,3) and tilt.shape==(41,17,2)
    assert np.max(np.abs(u[0]))==0.
    assert tilt[36,:,0]==pytest.approx(np.full(17,1.7446813052594985e-5),rel=1e-13)
