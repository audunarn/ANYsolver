"""Impact-focused saved-density body-port controls; two body RHS only."""
import json
import os
from pathlib import Path
import numpy as np
import pytest
from scipy import sparse
from scripts import r8_bl5_body_port_probe as tool

CHECKED=set()
pytestmark=pytest.mark.skipif(not (os.environ.get('ANYSOLVER_PORT_SAVED') and os.environ.get('ANYSOLVER_PORT_RAW')),
    reason='explicit saved-density DEV body-port runner required; no ordinary CI numerical probe')


@pytest.fixture(scope='module',autouse=True)
def reused_prerequisites():
    name=os.environ.get('ANYSOLVER_PORT_REUSE')
    if name:
        record=json.loads(Path(name).read_text())
        assert record['state']=='EXACT_PASSED_PREREQUISITE_FUNCTIONS_REUSED'
        CHECKED.update(record['checked'])


@pytest.fixture(scope='module')
def saved():
    return tool.load_saved(os.environ['ANYSOLVER_PORT_SAVED'])


@pytest.fixture(scope='module')
def prepared(saved):
    return tool.prepare(saved)


def save(name,value):
    tool.write(Path(os.environ['ANYSOLVER_PORT_RAW'])/name,value)


def test_saved_identity_and_body_work(saved):
    fields=tool.continuum_fields(saved);save('saved-fields-preflight.json',fields)
    assert all(row['work_relative_error']<=1e-8 for row in fields['body'].values())
    assert len(fields['point_gaps'])==8
    assert max(abs(np.asarray(fields['integrated_gap_position_m2_director_m'])))<=1e-9
    # No equality requirement on point gaps: P0 only constrains the integrals.
    CHECKED.add('saved')


def test_immutable_input_refusal(tmp_path):
    (tmp_path/'input-v1.json').write_text('{}')
    with pytest.raises(ValueError,match='bytes changed'):tool.load_saved(tmp_path)
    CHECKED.add('identity')


def test_exact_specimen_and_density_units(prepared):
    owner,loads,rigid,record=prepared
    assert owner._K.shape==(168,168) and owner._C.shape==(20,168)
    assert np.array_equal(owner._fixed,np.array([6*i+j for i in (0,5,10) for j in range(6)]))
    assert record['density_units']==['N/m']*12+['N']*8
    assert rigid.shape==(78,6)
    save('native-preflight.json',record)
    CHECKED.add('geometry')


def test_opposite_sign_common_supported_work(saved,prepared):
    owner,loads,_,_=prepared;model,k,c,u,lam,f=saved
    sa=np.array(((0.,.03),(0.,-.04),(0.,.07)))
    ba=np.array(((.02,-.03),(.05,.02),(-.01,.09)))
    native,_,field=tool.matched.global_common_field(owner,sa,np.zeros(3),ba,(.04,-.06,.08),supported=True)
    order,*_=tool.continuum.layout(model);ref=np.concatenate([field[n] for n in order])
    gap_n=owner._C@native;gap_r=c@ref
    np.testing.assert_allclose(gap_n,-gap_r,rtol=0,atol=1e-13)
    wn=float(loads@native);wr=float((f-c.T@lam)@ref)
    assert abs(wn-wr)/max(abs(wr),1e-12)<=1e-8
    save('common-work.json',dict(native_pairing_J=wn,continuum_pairing_J=wr,
        scope='Genuinely globally representable supported affine/director/rigid bar-section subset only'))
    CHECKED.add('sign')


def test_six_mode_balance_before_gauge(prepared):
    _,loads,rigid,record=prepared
    assert max(abs(tool.require_balanced(loads[90:],rigid)))<=1e-8
    bad=loads[90:].copy();bad[2]+=1.
    with pytest.raises(ValueError,match='nonzero physical rigid work'):tool.require_balanced(bad,rigid)
    CHECKED.add('balance')


def test_original_operator_quiet_row_reduction():
    k=sparse.csr_matrix([[1e16,1.,-1e16]])
    q=np.ones(3);load=np.ones(1)
    assert float((k@q-load)[0])==-1.
    assert np.array_equal(tool.precise_residual(k,q,load),np.zeros(1))
    assert np.array_equal(tool.precise_residual(k,q,np.zeros(1)),np.ones(1))
    CHECKED.add('reduction')


def test_two_body_rhs_and_actual_material_energy(saved,prepared):
    assert {'saved','identity','geometry','sign','balance','reduction'}<=CHECKED,'prerequisite failure: body solves withheld'
    result=tool.run_probe(saved,prepared,Path(os.environ['ANYSOLVER_PORT_RAW'])/'probe')
    assert result['material_energy_relative_error']<=1e-8
    assert result['compute_inventory']==dict(native_shell_RHS=1,native_beam_RHS=1,coupled_calibration=0,external_runs=0)
