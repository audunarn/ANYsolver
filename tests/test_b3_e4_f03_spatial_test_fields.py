"""Low-order virtual fields and independent physical-square moment checks."""
from fractions import Fraction
import json

import numpy as np
import pytest
from numpy.polynomial.legendre import leggauss

from scripts import _b3_e4_f03_spatial_contract as c
from scripts import _b3_e4_f03_spatial_tests as t


def test_fixed_order_and_lossless_definition():
    assert len(t.FIELD_IDS)==27 and len(set(t.FIELD_IDS))==27
    assert t.FIELD_IDS[:9]==(
        'rigid_tx','rigid_ty','rigid_rz',
        'left_tx','left_ty','left_rz','right_tx','right_ty','right_rz')
    assert t.FIELD_IDS[9]=='supported_0_i0_j0'
    assert t.FIELD_IDS[-1]=='supported_1_i2_j2'
    record=t.definition_record()
    assert record['field_ids']==list(t.FIELD_IDS)
    assert len(record['fields'])==27
    assert Fraction(*map(int,record['geometry']['gamma']))==c.Q_GAMMA
    assert len(json.dumps(record))<200_000
    for row in record['fields']:
        for component in row['components']:
            for i,j,num,den in component:
                assert i>=0 and j>=0 and Fraction(int(num),int(den))


def test_rigid_gamma_support_and_physical_strain():
    s=np.array([0.,.13,.5,.81,1.])
    tr=t.trace(s)
    assert tr['values'].shape==(5,27,3)
    assert tr['derivative'].shape==(5,27,3)
    np.testing.assert_allclose(tr['values'][:,0,0],c.U0)
    np.testing.assert_allclose(tr['values'][:,1,1],c.U0)
    np.testing.assert_allclose(tr['values'][:,2,1],c.U0/c.L0*s,rtol=0,atol=1e-20)
    np.testing.assert_allclose(tr['values'][:,2,2],
                               c.U0/c.L0*float(c.Q_GAMMA),rtol=0,atol=1e-20)
    np.testing.assert_allclose(tr['derivative'][:,2,1],c.U0/c.L0)
    np.testing.assert_allclose(tr['derivative'][:,2,2],0,atol=1e-20)
    x=np.array([-.5,.25,1.5]);y=np.array([.32,-.17,-.41])
    state=t.fields(x,y)
    assert state['values'].shape==(3,27,2)
    assert state['strain'].shape==(3,27,3)
    np.testing.assert_allclose(state['strain'][:,2],0,atol=1e-20)
    np.testing.assert_allclose(state['strain'][:,3,0],-c.U0/2)
    for x_edge in (Fraction(-1,2),Fraction(3,2)):
        for _,ux,uy in t._INVENTORY[9:]:
            for component in (ux,uy):
                assert sum((v*x_edge**i*Fraction(1,7)**j
                            for i,j,v in component),Fraction(0))==0
    np.testing.assert_allclose(state['values'][[0,2],9:],0,atol=2e-19)
    X=x-.5
    np.testing.assert_allclose(state['values'][:,9,0],c.U0*(1-X*X),atol=1e-20)
    np.testing.assert_allclose(state['strain'][:,9,0],-2*c.U0*X,atol=1e-20)


@pytest.mark.parametrize('station',[.137,.83])
def test_direct_gauss_on_four_physical_squares(station):
    # Independently integrate fields themselves, not their stored trace polynomials.
    nodes,weights=leggauss(8)
    direct=np.zeros((27,3))
    for sx in (-1,1):
        for sy in (-1,1):
            xx=station+sx*c.DX+c.HALFWIDTH*nodes
            yy=sy*c.DY+c.HALFWIDTH*nodes
            xg,yg=np.meshgrid(xx,yy,indexing='xy')
            u=t.fields(xg,yg)['values']
            w=np.outer(weights,weights)/16
            direct[:,0]+=np.einsum('ij,ijf->f',w,u[...,0])
            direct[:,1]+=np.einsum('ij,ijf->f',w,u[...,1])
            yaw=((xg-station)[...,None]*u[...,1]-yg[...,None]*u[...,0])/c.J
            direct[:,2]+=np.einsum('ij,ijf->f',w,yaw)
    np.testing.assert_allclose(t.trace(station)['values'],direct,
                               rtol=3e-14,atol=2e-19)


def test_station_derivative_and_array_ownership():
    station=.37;h=1e-5
    tr=t.trace(station)
    finite=(t.trace(station+h)['values']-t.trace(station-h)['values'])/(2*h)
    np.testing.assert_allclose(tr['derivative'],finite,rtol=3e-9,atol=2e-14)
    first=t.fields(np.array([.1,.2]),.11)
    first['values'][...,0,0]=123.
    second=t.fields(np.array([.1,.2]),.11)
    assert np.all(second['values'][...,0,0]!=123.)
    with pytest.raises(ValueError): t.trace(1.001)
    with pytest.raises(ValueError): t.fields(np.nan,0.)
    with pytest.raises(ValueError): t.fields(.25,.6)
