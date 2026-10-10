"""Complete saved-state retained oracle, explicitly supervised execution only."""
import os
from pathlib import Path
import pytest
pytestmark=pytest.mark.skipif('F06_CELL_MOMENT_OUTPUT' not in os.environ,
    reason='requires fresh root-adopted saved-data supervisor')

def test_complete_independent_cell_moment_and_retained_rows():
    from scripts.r8_f06_cell_moment_oracle_dev import run
    results=run(Path(os.environ['F06_CELL_MOMENT_OUTPUT']))
    assert len(results)==2
    for result in results:
        assert len(result['rows'])==48 and len(result['moment_rows'])==12
        assert result['h']==.002 and result['denominator']>=1e-10
        assert result['full48_independent_error']<=1e-6,result
        # The complete private smooth-path comparison is supporting evidence;
        # the original saved raw failure must remain visible and unchanged.
        assert result['full48_intended_path_error']<=1e-6,result
        assert result['original_full48_raw_error']>1e-6,result


def control_fixture():
    from scripts.r8_f06_cell_moment_oracle_dev import D,eye
    X=[[D(0),D(0),D(0)],[D(1),D(0),D(0)],[D(2),D(0),D(0)]]
    return X,[eye() for _ in range(3)],[eye() for _ in range(2)],[D(0)]*18,[D(0)]*42


def test_control_known_force_only_spatial_couple():
    from decimal import localcontext
    from scripts.r8_f06_cell_moment_oracle_dev import D,moment_rows
    X,Q,U,p,d=control_fixture();p[1]=D(2);d[18]=D('.3');d[25]=D(3)
    with localcontext() as ctx:
        ctx.prec=80;r,dr=moment_rows(X,Q,U,p,d)
    assert r==[D(0),D(0),D(-2),D(0),D(0),D(0)]
    assert dr==[D(0),D('.6'),D(-3),D(0),D(0),D(0)]


def test_control_reference_endpoint_signs_and_varying_resultants():
    from decimal import localcontext
    from scripts.r8_f06_cell_moment_oracle_dev import D,moment_rows
    X,Q,U,p,d=control_fixture();p[6:9]=[D(1),D(2),D(3)];p[9:12]=[D(4),D(6),D(8)]
    d[30:33]=[D(2),D(3),D(5)];d[33:36]=[D(7),D(11),D(13)]
    with localcontext() as ctx:
        ctx.prec=80;r,dr=moment_rows(X,Q,U,p,d)
    assert r==[D(-3),D(-4),D(-5),D(0),D(0),D(0)]
    assert dr==[D(-5),D(-8),D(-8),D(0),D(0),D(0)]


def test_control_nonorthogonal_stored_frame_extension():
    # Closed scalar z-axis specialization, not the matrix directional code.
    from decimal import localcontext
    from scripts.r8_f06_cell_moment_oracle_dev import D,moment_rows,log_terms
    X,Q,U,p,d=control_fixture();eps=D('.00002');tau=D('0.000000000000002')
    Q[0]=[[D(1),-eps,D(0)],[eps,D(1)+tau,D(0)],[D(0),D(0),D(1)]]
    p[8]=D(3);d[5]=D(1)
    with localcontext() as ctx:
        ctx.prec=80;r,dr=moment_rows(X,Q,U,p,d)
        f,fp,fpp=log_terms(D(1)+tau/2);t=1+tau/2
        expected_r=3*(f*t-fp*eps**2)
        expected_dr=3*(fpp*eps**3-3*fp*t*eps-f*eps)
    assert abs(r[2]-expected_r)<D('1e-70')
    assert abs(dr[2]-expected_dr)<D('1e-70')
    assert any(abs(v)>D(0) for v in (expected_r-3,expected_dr))


def test_control_series_domain_refusal():
    from scripts.r8_f06_cell_moment_oracle_dev import D,log_terms
    with pytest.raises(AssertionError,match='series outside bound'):log_terms(D('.8'))
