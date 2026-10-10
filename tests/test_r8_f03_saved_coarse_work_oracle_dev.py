"""Independent SMALL manufactured controls; no fixture/model/owner import."""
import json
from fractions import Fraction
import numpy as np
import pytest
from scipy import sparse
from scripts.r8_f03_saved_coarse_work_oracle_dev import analyze,load_saved,Refused,eigen_bound,mm,array_add_upper,array_mul_upper,array_div_upper,sha

def toy(physical=2.,left=.5,right=.5,stress=-2.):
    k=np.array([[physical,0,left],[0,3.,0],[right,0,stress]],dtype=float)
    return sparse.csr_matrix(k),sparse.csr_matrix([[1.,1.,0.]]),np.arange(3),np.array([],dtype=int),((2,),)

def test_all_direction_positive_and_resultant_only_negative_is_not_mechanical_instability():
    args=toy();r=analyze(*args)
    assert args[0][2,2]<0 and r['status']=='POSITIVE_STORED_COARSE_MECHANICAL_WORK'
    expected=(2.+.5*.5/2+3)/2
    # Independently eliminate D, constrain x=(a,-a), then apply declared G.
    g1=1/np.sqrt(2.+.5*.5/2);g2=1/np.sqrt(3)
    expected_scaled=(g1*g2)**2*(2.+.5*.5/2+3)/(g1*g1+g2*g2)
    assert r['minimum_lower']<=expected_scaled<=r['minimum_upper']
    assert r['original_array_norm_lower']>0 and r['qualification'] is False

def test_indefinite_physical_kernel_is_refused_as_positive():
    r=analyze(*toy(physical=-5.))
    assert r['status']=='NEGATIVE_STORED_COARSE_MECHANICAL_WORK' and r['minimum_upper']<0

def test_nonsymmetric_elimination_retains_independent_left_right():
    # B*E^-1*F is negative; averaging B/F would create a positive square.
    r=analyze(*toy(physical=1.,left=10.,right=-10.,stress=-1.))
    assert r['status']=='NEGATIVE_STORED_COARSE_MECHANICAL_WORK'
    assert r['local_blocks'][0]['scaled_formation_error_upper']>0

def test_near_floor_is_unresolved_not_false_positive():
    k=sparse.csr_matrix(np.diag([1.,-1.+1e-15,-1.]))
    r=analyze(k,sparse.csr_matrix([[1.,1.,0.]]),np.arange(3),np.array([],dtype=int),((2,),))
    assert r['status']=='UNRESOLVED' and r['minimum_lower']<=0<=r['minimum_upper']

def test_operator_inputs_are_not_mutated():
    args=toy();a=args[0].copy();c=args[1].copy();free=args[2].copy()
    analyze(*args)
    assert (args[0]!=a).nnz==0 and (args[1]!=c).nnz==0 and np.array_equal(args[2],free)

def test_overdimension_refuses_before_dense_materialization(monkeypatch):
    def forbidden(*a,**kw):raise AssertionError('dense fine model')
    monkeypatch.setattr(sparse.csr_matrix,'toarray',forbidden)
    with pytest.raises(Refused,match='dimension'):
        analyze(sparse.eye(627,format='csr'),sparse.csr_matrix(([1.],([0],[0])),shape=(1,627)),np.arange(627),np.array([],dtype=int),((626,),))

def test_saved_input_mutation_refused_before_load(tmp_path):
    p=tmp_path/'K.npz';p.write_bytes(b'changed')
    bindings={}
    for name in ('K.npz','C.npz','compiled-layout.npz','states.npz','inputs.json','result.json'):
        target=tmp_path/name;target.write_bytes(b'original');bindings[str(target.resolve())]=sha(target)
    p.write_bytes(b'changed')
    manifest=tmp_path/'manifest.json';manifest.write_text(json.dumps(dict(family=[16,4,16,2],endpoint_node=117,saved_directory=str(tmp_path),saved_inputs=bindings)))
    with pytest.raises(Refused,match='mutation'):load_saved(manifest)

@pytest.mark.parametrize('bindings',[{}, {'elsewhere.npz':'0'*64}])
def test_missing_or_escaped_saved_bindings_refused(tmp_path,bindings):
    manifest=tmp_path/'manifest.json';manifest.write_text(json.dumps(dict(family=[16,4,16,2],endpoint_node=117,saved_directory=str(tmp_path),saved_inputs=bindings)))
    with pytest.raises(Refused,match='complete saved-file'):load_saved(manifest)

def test_ineligible_nonnegative_resultant_and_actual_stress_constraint():
    with pytest.raises(Exception,match='local negative'):analyze(*toy(stress=2.))
    k,c,free,fixed,blocks=toy();c=sparse.csr_matrix([[1.,1.,1.]])
    with pytest.raises(Refused,match='stress resultants'):analyze(k,c,free,fixed,blocks)

def test_complete_eigenbasis_and_product_bound_against_literal_toy():
    a=np.array([[3.,1e-12],[1e-12,2.]])
    e,_=eigen_bound(a)
    actual=(5.-np.sqrt(1+4e-24))/2
    assert e['minimum']-e['radius']<=actual<=e['minimum']+e['radius']
    b=np.array([[1e16,1.,-1e16],[.25,2.,.5]])
    c=np.ones((3,1));p,error=mm(b,c)
    exact=np.array([[1.],[2.75]])
    assert np.linalg.norm(p-exact)<=error

@pytest.mark.parametrize('a,b',[(2.**-1022,2.**-52),(2.**-1074,1.5),(1.0000000000000002,1.0000000000000002),(1e150,1e-150)])
def test_outward_array_primitives_against_exact_binary_fractions(a,b):
    fa,fb=Fraction(a),Fraction(b)
    assert Fraction(float(array_add_upper(a,b)))>=fa+fb
    assert Fraction(float(array_mul_upper(a,b)))>=fa*fb
    assert Fraction(float(array_div_upper(a,b)))>=fa/fb
