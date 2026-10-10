"""Identity, coincident sampling and saved-field controls; no physical solve."""
import copy
import json
from pathlib import Path
import numpy as np
import pytest
from scripts.r8_e02_rigid_torque_refinement import (
    CASE80,DIRECTOR,common_sample,compare_refinement,geometry80,geometry_identity,mismatch_variation,
)

ROOT=Path(__file__).resolve().parents[1]

def fixture80():
    nodes,cells,patch,selected,root=geometry80()
    q=[[x,y,x*y,x+y,2*x-y,0.] for x,y,z in nodes.values()]
    return dict(case=copy.deepcopy(CASE80),node_ids=list(nodes),coordinates_m=list(nodes.values()),
        shell_node_count=2673,element_count=2560,geometry_sha256=geometry_identity()[0],
        shell_coordinates=q,beam_coordinates=[0.]*42,patch_nodes=list(selected),root_nodes=list(root),
        director_contract=DIRECTOR,guards={'external_final_pairing_J':1.})

def test_fine_mesh_and_complete_disjoint_root_patch_coverage():
    nodes,cells,patch,selected,root=geometry80()
    assert (len(nodes),len(cells),len(patch),len(selected),len(root))==(2673,2560,512,561,33)
    assert set(selected)=={n for c in patch for n in c}
    assert set(root)=={n for n,p in nodes.items() if p[0]==0}
    assert set(selected)=={n for n,p in nodes.items() if p[0]>=.8}
    assert not set(root)&set(selected)
    assert geometry_identity()[1]['case']['wrench']==[0.,0.,0.,1.,0.,0.]

def test_samples_are_exact_coincident_vertices_not_model_relabelling():
    f=fixture80();q,meta=common_sample(f)
    assert q.shape==(41,17,6)
    assert meta['actual_case']['nx']==80 and meta['actual_cells']==2560
    assert meta['observation_grid']==dict(nx=40,ny=16,sampled_points=697)
    for j in range(17):
        for i in range(41):
            assert np.array_equal(q[i,j],f['shell_coordinates'][2*j*81+2*i])
    q[0,0,0]=999
    assert f['shell_coordinates'][0][0]==0

@pytest.mark.parametrize('field,value',[
    ('element_count',640),('shell_node_count',697),('geometry_sha256','tampered'),
    ('root_nodes',[1]),('patch_nodes',[65]),('director_contract','geometric normal'),
    ('beam_coordinates',[0.]*18),('case',dict(CASE80,nx=160)),
])
def test_refuse_incomplete_or_changed_fine_model(field,value):
    f=fixture80();f[field]=value
    with pytest.raises(ValueError):common_sample(f)

def test_refuse_coordinate_tamper_and_nonfinite_fields():
    f=fixture80();f['coordinates_m'][1]=(1/80+.0001,-.1,0.)
    with pytest.raises(ValueError,match='physical coordinates'):common_sample(f)
    f=fixture80();f['shell_coordinates'][1][2]=float('nan')
    with pytest.raises(ValueError,match='finite'):common_sample(f)

def test_signed_cancellation_does_not_erase_absolute_variation_or_extrema():
    d=np.zeros(41);d[1]=2.;d[3]=3.;d[31]=-4.
    r=mismatch_variation(d)
    assert r['net_increment_rad']==0. and r['total_absolute_variation_rad']==18.
    assert all(b['signed_fraction'] is None for b in r['bands'])
    assert sum(b['absolute_variation_fraction'] for b in r['bands'])==pytest.approx(1.)
    assert r['minimum']==dict(x_m=.775,value_rad=-4.)
    assert r['maximum']==dict(x_m=.07500000000000001,value_rad=3.)

def test_saved_d3_pair_and_same_common_stencils():
    coarse=json.loads((ROOT/'.development/e02-rigid-torque-fields-20261009-v1/collect1/fields/native-fields.json').read_text())
    f=fixture80();cq=np.array(coarse['shell_coordinates']).reshape(17,41,6).transpose(1,0,2)
    for j in range(17):
        for i in range(41):f['shell_coordinates'][2*j*81+2*i]=cq[i,j].tolist()
    f['guards']=copy.deepcopy(coarse['guards'])
    saved=ROOT/'.development/e02-rigid-precision-20261009-v1/numerical-attempt3/static-fixed-root-elimination'
    r=compare_refinement(f,coarse,(saved/'reference.frd').read_bytes(),(saved/'reference.inp').read_text(),
        json.loads((saved/'candidate.json').read_text()))
    assert r['work_refinement_relative']==0.
    assert r['common_field_delta_component_max']==[0.]*6
    assert not r['acceptance'] and r['normalized_scientific_acceptance']=='NOT_EVALUATED'
    assert r['native40_external_tilt_variation']==r['native80_external_tilt_variation']
    interior=r['native40_external_tilt_variation']['bands'][1]
    assert interior['signed_fraction']==pytest.approx(.9939424468717669,abs=1e-10)
    assert interior['absolute_variation_fraction']==pytest.approx(.6760,abs=5e-5)
    assert r['actual_native_case']['nx']==80 and r['external_case']['nx']==40
