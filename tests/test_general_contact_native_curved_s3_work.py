"""Independent local curved / moving-S3 work controls; no owner admission."""
from math import pi
import json,os
from pathlib import Path
import numpy as np
import pytest
from numpy.polynomial.legendre import leggauss
from scipy.spatial.transform import Rotation

from anysolver import create_shell_element
from anysolver.fe_core import FEModel
from anysolver.general_contact.s3_skin_work import S3SkinWorkAdapter
from anysolver.general_contact.native_material_s3 import NativeMaterialS3Patch
from anysolver.general_contact.native_curved_s3_work import NativeCurvedMaterialS3Work,PROFILE
from anysolver.general_contact.native_surface_quadrature import NativeRoundSurfaceRule
from anysolver.general_contact.native_surface_normal import StraightNormalIntegrationSettings
from test_general_contact_native_retained_station import _reference
from test_general_contact_native_surface_bounds import _independent_point


def _case():
    reference=_reference(True)
    rule=NativeRoundSurfaceRule(7,reference,.03,xi_range=(.1,.9),
        angle_range=(4.,5.3),axial_order=1,angular_order=1)
    patch=NativeMaterialS3Patch(rule,(1,2,3),normal_stiffness_Pa_per_m=1e4,
        integration_settings=StraightNormalIntegrationSettings(1e-10,1e-8,1e-6,64,1.),
        geometry_tolerance_m=1e-10,rim_clearance_m=1e-6)
    model=FEModel('curved material local work');model.add_material('elastic',1e8,.3)
    for node,xy in zip((13,5,22),((-4.,-3.),(4.,-3.),(0.,5.))):
        model.add_node(node,*xy,-.01)
    model.add_element(21,create_shell_element(21,(13,5,22),'elastic',thickness=.02,
        formulation='e4-pl-s3-v2d',reference_normal=(0.,0.,1.),reference_surface_offset=0.))
    skin=S3SkinWorkAdapter.from_model(model,8,21,'top')
    work=NativeCurvedMaterialS3Work(patch,skin)
    p=reference.coordinates.copy();p[:,2]=-.06;p[1]+=(.003,-.002,-.001)
    rotations=np.stack([Rotation.from_rotvec(v).as_matrix() for v in
                        ((.025,-.015,.01),(-.02,.01,-.015))])
    u=np.linspace(-.002,.003,skin.work_map.shape[1])
    return work,p,np.zeros((3,3)),rotations,u


def _corners(work,u):
    # Reconstruct physical skin independently, respecting non-numerical node order.
    skin=work.shell;indices=work.shell_translation_dofs[:,0]
    q=np.array([u[first:first+6] for first in indices])
    return skin.reference_positions+q[:,:3]+skin.physical_offset*np.cross(q[:,3:],skin.director)


def _oracle(work,p,low,U,u,order=40):
    corners=_corners(work,u);n=np.cross(corners[1]-corners[0],corners[2]-corners[0]);n/=np.linalg.norm(n)
    x,w=leggauss(order);al,ar=work.contact.rule.definition['angle_range']
    lo,hi=work.contact.rule.definition['xi_range'];r=work.contact.radius;k=work.contact.stiffness
    energy=0.;force=np.zeros(3);moment=np.zeros(3)
    for q,v in zip(x,w):
        xi=(lo+hi)/2+(hi-lo)*q/2;j=np.sqrt(1+.16*xi*xi)
        for a,b in zip(x,w):
            angle=(al+ar)/2+(ar-al)*a/2
            point=_independent_point(xi,angle,r,p,low,U,False)
            gap=n@(point-corners[0]);measure=v*b*(hi-lo)*(ar-al)/4*r*(j+.4*r*np.cos(angle)/j**2)
            reaction=k*max(0.,-gap)*measure*n
            energy+=.5*k*min(gap,0.)**2*measure
            force+=reaction;moment+=np.cross(point,reaction)
    return energy,force,moment


def _moved(p,low,U,u,d,h):
    pp=p.copy()
    for i in range(3):pp[i]+=h*d[6*i:6*i+3]
    uu=np.stack([Rotation.from_rotvec(h*d[18+3*i:21+3*i]).as_matrix()@U[i] for i in range(2)])
    return pp,low,uu,u+h*d[42:]


def test_curved_moving_s3_independent_work_wrenches_and_full_mixed_tangent():
    work,p,low,U,u=_case();result=work.evaluate(p,low,U,u);c=result.contact
    reference=_oracle(work,p,low,U,u)
    assert result.profile==PROFILE and c.minimum_rim_clearance_m>1.
    assert c.potential_j==pytest.approx(reference[0],rel=1e-9,abs=1e-10)
    np.testing.assert_allclose(c.beam_force_n,reference[1],rtol=1e-9,atol=1e-8)
    np.testing.assert_allclose(c.beam_moment_nm,reference[2],rtol=1e-9,atol=1e-8)
    force_error=np.linalg.norm(c.beam_force_n+c.shell_force_n)
    moment_error=np.linalg.norm(c.beam_moment_nm+c.shell_moment_nm)
    assert force_error<1e-11 and moment_error<1e-11
    assert np.linalg.norm(result.tangent[:42,42:].toarray())>1.
    rng=np.random.default_rng(1641);errors=[]
    for shell_only in (False,True):
        d=rng.normal(size=len(result.residual))*.003;d[24:42]=0.
        if shell_only:d[:42]=0.
        for h in (1e-5,2e-6):
            plus=work.evaluate(*_moved(p,low,U,u,d,h));minus=work.evaluate(*_moved(p,low,U,u,d,-h))
            derivative=(plus.residual-minus.residual)/(2*h)
            error=np.linalg.norm(result.tangent@d-derivative)/np.linalg.norm(derivative)
            assert error<1e-5;errors.append(float(error))
            assert (plus.contact.potential_j-minus.contact.potential_j)/(2*h)==pytest.approx(
                result.residual@d,rel=1e-5,abs=1e-9)
    # Small-rotation S3 authoritative couples use its reference director map.
    q=-result.residual[42:].reshape(-1,6)
    dofs=work.shell_translation_dofs[:,0]//6
    np.testing.assert_allclose(q[dofs,3:],
        work.shell.physical_offset*np.cross(work.shell.director,q[dofs,:3]),atol=1e-11)
    path=os.environ.get('CONTACT_APP_RESULT_RECORD')
    if path:Path(path+'-curved-s3-local.json').write_text(json.dumps(dict(
        scope='local complete moving-target work only',force_balance_n=float(force_error),
        moment_balance_nm=float(moment_error),tangent_errors=errors,
        energy_error_j=abs(c.potential_j-reference[0]),evaluations=c.integration_evaluations,
        intervals=c.integration_intervals,estimated_errors=[c.energy_error_j,c.force_error_n,c.tangent_error_n_per_m]),indent=2))


def test_curved_s3_rejects_rim_inversion_mutation_and_unadmitted_path():
    work,p,low,U,u=_case()
    assert work.geometry_gap(p,low,U,u)[1]>1.
    outside=p.copy();outside[:,1]+=10.
    with pytest.raises(ValueError,match='rim'):work.evaluate(outside,low,U,u)
    flipped=np.zeros_like(u);dofs=work.shell_translation_dofs
    flipped[dofs[1]] = work.shell.reference_positions[0]-work.shell.reference_positions[1]
    with pytest.raises(ValueError):work.evaluate(p,low,U,flipped)
    with pytest.raises(NotImplementedError,match='whole-path'):work.certify_orientation_path()
    work.contact.stiffness*=2
    with pytest.raises(ValueError,match='changed'):work.evaluate(p,low,U,u)


def test_curved_s3_whole_moving_path_and_endpoint_safe_hidden_target_collapse():
    from anysolver.general_contact.native_surface_s3_friction import NativeS3MaterialConfiguration
    from anysolver.general_contact.native_surface_path import material_path_pose
    work,p,low,U,u=_case();start=NativeS3MaterialConfiguration(p,low,U,u)
    move=np.tile((.001,-.002,.001),(3,1));spin=np.array(((.002,-.001,.001),(-.001,.001,-.002)))
    du=np.linspace(.001,-.002,len(u))
    control=work.certify_path(start,move,spin,du,gap_tolerance_m=.2,maximum_intervals=64)
    assert control.certified and control.intervals<=64 and control.orientation_lower>0
    for t in np.linspace(0.,1.,17):
        current=material_path_pose(start,move,spin,du,t)
        gap,rim=work.geometry_gap(current.positions,current.position_low,current.cell_rotations,current.shell_displacement)
        assert gap>=control.gap_lower_m and rim>work.contact.rim_clearance
    zero=np.zeros_like(u);start=NativeS3MaterialConfiguration(p,low,U,zero)
    end=np.zeros_like(u);dofs=work.shell_translation_dofs
    corners=work.shell.reference_positions
    for i in range(3):end[dofs[i,:2]]=-2*corners[i,:2]
    # Both endpoints have positive target orientation; the affine middle collapses.
    work.geometry_gap(p,low,U,zero);work.geometry_gap(p,low,U,end)
    hidden=work.certify_path(start,np.zeros((3,3)),np.zeros((2,3)),end,
        gap_tolerance_m=.2,maximum_intervals=64)
    assert not hidden.certified and 'target orientation' in hidden.reason


def test_curved_s3_hidden_rim_crossing_gap_failure_caps_and_cancellation():
    from anysolver.general_contact.native_surface_s3_friction import NativeS3MaterialConfiguration
    from anysolver.control import CancellationToken
    work,p,low,U,u=_case();start=NativeS3MaterialConfiguration(p,low,U,u)
    move=np.tile((0.,10.,0.),(3,1))
    value=work.certify_path(start,move,np.zeros((2,3)),np.zeros_like(u),
        gap_tolerance_m=.2,maximum_intervals=8)
    assert not value.certified
    tight=work.certify_path(start,np.zeros((3,3)),np.zeros((2,3)),np.zeros_like(u),
        gap_tolerance_m=1e-6,maximum_intervals=8)
    assert not tight.certified and tight.intervals<=8
    token=CancellationToken();token.cancel()
    with pytest.raises(Exception,match='cancel'):
        work.certify_path(start,np.zeros((3,3)),np.zeros((2,3)),np.zeros_like(u),
            gap_tolerance_m=.2,maximum_intervals=8,cancellation_token=token)


def test_curved_s3_moving_normal_lever_preserves_exact_partition_at_large_origin():
    from anysolver.general_contact.native_curved_s3_work import _relative_center,_S3CandidateIntegration
    work,p,low,U,u=_case();corners=work.shell.reference_positions.copy()
    candidate=_S3CandidateIntegration(work,corners)
    p=np.array(((0.,0.,-.06),(0.,0.,-.06),(1.,0.,-.06)))
    arm=np.array((.001,.002,-.03));before=candidate._gap_work_jet(-.09,p,low,1,.1,arm)
    shift=np.array((2.**48,0.,0.));translated=_S3CandidateIntegration(work,corners+shift)
    after=translated._gap_work_jet(-.09,p+shift,low,1,.1,arm)
    np.testing.assert_array_equal(before.gradient,after.gradient)
    np.testing.assert_array_equal(before.hessian,after.hessian)
    flat=np.tile(shift,(3,1))
    np.testing.assert_array_equal(_relative_center(flat,low,1,.1,shift),0.)


def test_curved_s3_axial_front_complete_target_work_and_independent_partition():
    from types import SimpleNamespace
    from test_general_contact_native_curved_plane_work import _independent_axial_front_integral
    work,p,low,U,u=_case();u[:]=0.;U[:]=np.eye(3)
    p=work.contact.beam_reference.coordinates.copy();p[:,2]=.02+.04*p[:,0]
    value=work.evaluate(p,low,U,u)
    oracle=_independent_axial_front_integral(SimpleNamespace(rule=work.contact.rule,
        stiffness=work.contact.stiffness,normal=np.array((0.,0.,1.))),p,low,U)
    assert value.contact.potential_j==pytest.approx(oracle[0],rel=1e-9,abs=1e-10)
    np.testing.assert_allclose(value.contact.beam_force_n,oracle[1],rtol=1e-9,atol=1e-8)
    np.testing.assert_allclose(value.contact.beam_moment_nm,oracle[2],rtol=1e-9,atol=1e-8)
    np.testing.assert_allclose(value.contact.beam_moment_nm+value.contact.shell_moment_nm,0.,atol=1e-10)
    d=np.random.default_rng(506).normal(size=len(value.residual))*.001;d[24:42]=0.
    errors=[]
    for h in (1e-5,2e-6):
        plus=work.evaluate(*_moved(p,low,U,u,d,h));minus=work.evaluate(*_moved(p,low,U,u,d,-h))
        derivative=(plus.residual-minus.residual)/(2*h)
        error=np.linalg.norm(value.tangent@d-derivative)/np.linalg.norm(derivative)
        assert error<1e-5;errors.append(float(error))
    path=os.environ.get('CONTACT_APP_RESULT_RECORD')
    if path:Path(path+'-curved-s3-front.json').write_text(json.dumps(dict(
        tangent_errors=errors,energy_error_j=abs(value.contact.potential_j-oracle[0]),
        force_error_n=float(np.linalg.norm(value.contact.beam_force_n-oracle[1])),
        moment_error_nm=float(np.linalg.norm(value.contact.beam_moment_nm-oracle[2])),
        estimated_errors=[value.contact.energy_error_j,value.contact.force_error_n,value.contact.tangent_error_n_per_m],
        intervals=value.contact.integration_intervals,evaluations=value.contact.integration_evaluations),indent=2))
