"""Independent linear relative-pair discriminator, not native qualification."""
from pathlib import Path
import json,os,sys
import numpy as np
import pytest
from scipy.integrate import quad

sys.path.insert(0,str(Path(__file__).parents[1]/'docs/d1_review_support'))
from d3_beam_foundation_reference import cantilever_foundation_reference


@pytest.mark.parametrize('beam_bending',(1.2,.75+.45*1e5/(1e6+1e5)))
@pytest.mark.parametrize('line_stiffness',(100.,1000.,4000.))
def test_tip_loaded_relative_pair_reference_work_and_gap(beam_bending,line_stiffness):
    # Equal beams: delta=w_B-w_A, Drel=D/2, Srel=S/2, Prel=P/2.
    # Variation of U=(D/4)*int(delta''**2)+contact gives this reduction.
    L=2.;c=.001;D=beam_bending/2;S=200.;P=.0025/2;k=line_stiffness
    ref=cantilever_foundation_reference(length=L,clearance=c,bending=D,
        shear=S,load=0.,tip_force=P,line_stiffness=k)
    output=os.environ.get('CONTACT_APP_RESULT_RECORD')
    report=dict(scope='linear continuous relative pair only; not nonlinear native acceptance',
        beam_bending_nm2=beam_bending,relative_bending_nm2=D,relative_shear_n=S,
        relative_tip_force_n=P,line_stiffness_n_per_m2=k,clearance_m=c,
        front_m=ref.front,tip_penetration_m=ref.state(L)[0]-c,
        gap_budget_m=5e-5,boundary_residual=ref.boundary_residual,
        front_residual=ref.front_residual)
    if output:Path(output+f'-pair-reference-{beam_bending:.8f}-k{k:.0f}.json').write_text(json.dumps(report,indent=2))
    M0,Q0=ref.state(0.)[2:]
    for x in (0.,.37*ref.front,ref.front):
        expected=np.array((M0*x*x/(2*D)-Q0*x**3/(6*D)+Q0*x/S,
            M0*x/D-Q0*x*x/(2*D),M0-Q0*x,Q0))
        np.testing.assert_allclose(ref.state(x),expected,rtol=1e-11,atol=1e-13)
    np.testing.assert_allclose(ref.state(L)[2:],(0.,P),rtol=1e-10,atol=1e-12)
    reaction=quad(lambda x:k*(ref.state(x)[0]-c),ref.front,L,
        epsabs=1e-13,epsrel=1e-10)[0]
    assert abs(reaction-ref.reaction)<=1e-12
    energy=quad(lambda x:ref.state(x)[2]**2/D+ref.state(x)[3]**2/S,0.,L,
        points=(ref.front,),epsabs=1e-13,epsrel=1e-10)[0]
    contact_work=quad(lambda x:k*(ref.state(x)[0]-c)*ref.state(x)[0],ref.front,L,
        epsabs=1e-13,epsrel=1e-10)[0]
    assert abs(energy+contact_work-P*ref.state(L)[0])<=1e-12
    assert ref.contact_velocity_lower>0.


@pytest.mark.parametrize('endpoint_stiffness',(0.,.1))
def test_combined_tip_and_distributed_loading_with_endpoint_work(endpoint_stiffness):
    """Check the new natural tip work with independent dimensional identities."""
    L=2.;c=.001;D=.6;S=200.;P=.00125;q=.0001;k=100.
    ref=cantilever_foundation_reference(length=L,clearance=c,bending=D,
        shear=S,load=q,tip_force=P,line_stiffness=k,
        endpoint_stiffness=endpoint_stiffness)
    M0,Q0=ref.state(0.)[2:]
    for x in (0.,.37*ref.front,ref.front):
        expected=np.array((M0*x*x/(2*D)-Q0*x**3/(6*D)+q*x**4/(24*D)
            +Q0*x/S-q*x*x/(2*S),
            M0*x/D-Q0*x*x/(2*D)+q*x**3/(6*D),
            M0-Q0*x+q*x*x/2,Q0-q*x))
        np.testing.assert_allclose(ref.state(x),expected,rtol=1e-11,atol=1e-13)
    wtip,_,Mtip,Qtip=ref.state(L)
    endpoint_force=endpoint_stiffness*(wtip-c)
    np.testing.assert_allclose((Mtip,Qtip+endpoint_force),(0.,P),
        rtol=1e-10,atol=1e-12)
    integrate=lambda fun:quad(fun,0.,L,points=(ref.front,),
        epsabs=1e-13,epsrel=1e-10)[0]
    reaction=integrate(lambda x:k*max(0.,ref.state(x)[0]-c))
    assert abs(reaction+endpoint_force-ref.reaction)<=1e-12
    structural_work=integrate(lambda x:ref.state(x)[2]**2/D+ref.state(x)[3]**2/S)
    contact_work=integrate(lambda x:k*max(0.,ref.state(x)[0]-c)*ref.state(x)[0])
    external_work=q*integrate(lambda x:ref.state(x)[0])+P*wtip
    assert abs(structural_work+contact_work+endpoint_force*wtip-external_work)<=1e-12
    assert ref.contact_velocity_lower>0.
