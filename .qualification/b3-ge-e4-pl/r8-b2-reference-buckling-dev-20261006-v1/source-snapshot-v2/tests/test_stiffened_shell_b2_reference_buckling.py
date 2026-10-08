"""Development work/equation controls, not full F12/B14 qualification."""
import importlib.util
from pathlib import Path
from dataclasses import replace
import numpy as np
import pytest
from scipy.linalg import eig
from scipy.spatial.transform import Rotation
from anysolver import stiffened_shell as api
from anysolver.control import CancellationToken
from anysolver._stiffened_shell_b2_reference_buckling import (
    beam_reference_derivatives,member_green_hessian,point_green_hessian,compile_geometric,
)

spec=importlib.util.spec_from_file_location("b2_buckling_example",Path(__file__).parents[1]/"examples/stiffened_shell_b2_reference_buckling.py")
example=importlib.util.module_from_spec(spec);spec.loader.exec_module(example)

def test_actual_public_q4_reference_buckling_and_full_descriptor_qz():
    owner=api.create_analysis(example.definition())
    try:
        assert owner.reference_buckling_capabilities.eligible
        load=np.zeros(48);load[[12,30]]=-1.
        request=api.B2ReferenceBucklingRequest(load,(example.traction_source(),))
        before=owner.solve_linear(load)
        result=owner.buckling(request)
        assert result.status == "ok",result.failure_reason
        assert max(result.equation_residuals)<=1e-8
        assert max(result.constraint_residuals)<=1e-9
        np.testing.assert_array_equal(owner.solve_linear(load).displacements,before.displacements)
        g,_=compile_geometric(owner,request,before)
        k=(owner._T.T@owner._K@owner._T).toarray();c=(owner._C@owner._T).toarray();d=-(owner._T.T@g@owner._T).toarray()
        a=np.block([[k,c.T],[c,np.zeros((len(c),len(c)))]])
        b=np.zeros_like(a);b[:len(k),:len(k)]=d
        eigen=eig(a,b,right=False)
        finite=sorted(v.real for v in eigen if np.isfinite(v) and abs(v.imag)<1e-9*abs(v.real) and v.real>0.)
        np.testing.assert_allclose(result.load_factors[0],finite[0],rtol=1e-8,atol=0.)
        assert np.count_nonzero(b[len(k):]) == 0
        assert result.identity and not result.production_qualified
    finally: owner.close()

def test_member_reference_derivatives_match_independent_objective_finite_trace():
    definition=example.definition()
    physical=definition.members[0];operator=physical.local_operator();length=physical.length_m
    station=.37;j,_,h,_=beam_reference_derivatives(operator,station)
    q=np.sin(np.arange(12)+.2)*.3
    def finite(q):
        r0=Rotation.from_rotvec(q[3:6]).as_matrix();r1=Rotation.from_rotvec(q[9:12]).as_matrix()
        qc=r0@Rotation.from_rotvec(.5*Rotation.from_matrix(r0.T@r1).as_rotvec()).as_matrix()
        endpoints=np.array(((-length/2,0.,0.),(length/2,0.,0.)))+np.stack((q[:3],q[6:9]))
        middle=endpoints.mean(axis=0);local=(endpoints-middle)@qc
        d=np.r_[local[0]-(-length/2,0.,0.),Rotation.from_matrix(qc.T@r0).as_rotvec(),local[1]-(length/2,0.,0.),Rotation.from_matrix(qc.T@r1).as_rotvec()]
        trace=operator.trace(d,stations=(station,)).pose[0]
        position=middle+qc@(np.array(((station-.5)*length,0.,0.))+trace[:3])
        rotation=Rotation.from_matrix(qc@Rotation.from_rotvec(trace[3:]).as_matrix()).as_rotvec()
        return np.r_[position,rotation]
    expected=np.einsum('iab,a,b->i',h,q,q)
    errors=[]
    for step in (1e-3,3e-4,1e-4):
        first=(finite(step*q)-finite(-step*q))/(2*step)
        second=(finite(step*q)+finite(-step*q)-2*finite(np.zeros(12)))/step**2
        np.testing.assert_allclose(first,j@q,rtol=1e-6,atol=1e-10)
        # Existing derivative-control floors: 1 m / 1 rad for port coordinates.
        errors.append(np.max(abs(second-expected)/np.maximum(1.,abs(expected))))
    assert sum(error<=1e-6 for error in errors)>=2,errors

def test_full_point_curvature_matches_objective_polar_and_beam_pose_work():
    from anysolver._ge_beam3_pose_joint import RigidPoseJoint
    from anysolver._b2_f10_f11_point_attachment import compile_reference_point
    owner=api.create_analysis(example.definition())
    try:
        member,_=owner._members[0][1]
        vertices=np.array(((0.,0.,0.),(1.,0.,0.),(1.,1.,0.),(0.,1.,0.)))
        offset=np.array((0.,.03,.04));station=0.
        law=compile_reference_point(member.definition,vertices,station=station,offset_local_m=offset)
        multiplier=np.array((.4,-.2,.3,.07,-.05,.11))
        hessian=point_green_hessian(law,vertices,member,station,offset,multiplier)
        r=vertices-vertices.mean(axis=0);length=member.definition.length_m
        frame=member.definition.local_frame_rows().T;transform=member.local_dof_map()
        joint=RigidPoseJoint(np.stack((law.shell_reference_m,law.beam_reference_m)),law.reference_frames)
        def work(q):
            shell=vertices+q[:24].reshape(-1,6)[:,:3];center=shell.mean(axis=0)
            u,_,vt=np.linalg.svd((shell-center).T@r)
            rotation=u@np.diag((1.,1.,np.linalg.det(u@vt)))@vt
            local=transform@q[24:];r0=Rotation.from_rotvec(local[3:6]).as_matrix();r1=Rotation.from_rotvec(local[9:12]).as_matrix()
            qc=r0@Rotation.from_rotvec(.5*Rotation.from_matrix(r0.T@r1).as_rotvec()).as_matrix()
            ends=np.array(((-length/2,0.,0.),(length/2,0.,0.)))+np.stack((local[:3],local[6:9]));middle=ends.mean(axis=0)
            coordinates=(ends-middle)@qc
            d=np.r_[coordinates[0]-(-length/2,0.,0.),Rotation.from_matrix(qc.T@r0).as_rotvec(),coordinates[1]-(length/2,0.,0.),Rotation.from_matrix(qc.T@r1).as_rotvec()]
            trace=member.operator.trace(d,stations=(station,)).pose[0]
            beam_rotation=qc@Rotation.from_rotvec(trace[3:]).as_matrix()
            beam_position=np.asarray(member.definition.reference_points_m[0])+frame@(middle+qc@(np.array(((station-.5)*length,0.,0.))+trace[:3])+np.array((length/2,0.,0.))+beam_rotation@offset)
            return joint.evaluate(np.stack((center,beam_position)),np.stack((rotation@law.reference_frames[0],frame@beam_rotation)),multiplier).potential
        q=np.sin(np.arange(36)+.2)*.3
        expected=q@hessian@q
        errors=[]
        for step in (1e-3,3e-4,1e-4):
            actual=(work(step*q)+work(-step*q)-2*work(np.zeros(36)))/step**2
            errors.append(abs(actual-expected)/max(1.,abs(expected)))
        assert sum(error<=1e-6 for error in errors)>=2,errors
        assert np.linalg.norm(hessian-law.candidate_prestress_curvature(multiplier))>0.
    finally: owner.close()

def test_same_resultants_do_not_determine_wagner_stress_work():
    source=example.traction_source()
    # Add symmetric axial area samples at two different radii: their resultant
    # sum and first moments vanish, while their polar stress moment differs.
    yz=np.r_[source.coordinates_yz_m,[[.2,0.],[-.2,0.],[0.,.1],[0.,-.1]]]
    w=np.r_[source.area_weights_m2,np.ones(4)*.01]
    maps=np.concatenate((source.traction_map,np.zeros((4,3,6))))
    maps[-4:,0,0]=(1.,1.,-1.,-1.)
    other=api.B2SectionTractionQuadrature("beam","self-equilibrated-stress-counterexample",yz,w,maps)
    owner=api.create_analysis(example.definition())
    try:
        member,slots=owner._members[0][1]
        q=np.zeros(12);q[6]=-.001
        a=member_green_hessian(member,q,source);b=member_green_hessian(member,q,other)
        assert np.linalg.norm(a-b)>0.
        assert source.identity != other.identity
    finally: owner.close()

def test_refusals_cancellation_and_source_ownership():
    owner=api.create_analysis(example.definition())
    try:
        load=np.zeros(48);load[[12,30]]=-1.
        source=example.traction_source();request=api.B2ReferenceBucklingRequest(load,(source,))
        load[:]=99.
        assert request.preload[12] == -1.
        with pytest.raises(ValueError): source.traction_map.setflags(write=True)
        with pytest.raises(ValueError): owner.buckling(object())
        with pytest.raises(ValueError): owner.buckling(replace(request,section_tractions=()))
        couples=np.asarray(request.preload).copy();couples[3]=1.
        with pytest.raises(ValueError,match="couples"): owner.buckling(replace(request,preload=couples))
        token=CancellationToken();token.cancel()
        result=owner.buckling(request,cancellation=token)
        assert result.status == "cancelled" and not result.load_factors
    finally: owner.close()

@pytest.mark.parametrize("kind",("s3","mixed"))
def test_actual_public_s3_thin_uniform_reference_buckling(kind):
    owner=api.create_analysis(example.definition(kind))
    try:
        load=np.zeros(48);load[[12,30]]=-1.
        request=api.B2ReferenceBucklingRequest(load,(example.traction_source(),))
        result=owner.buckling(request)
        assert result.status == "ok",result.failure_reason
        assert max(result.constraint_residuals)<=1e-9
        assert max(result.equation_residuals)<=1e-8
    finally: owner.close()

def test_unexpected_runtime_error_propagates(monkeypatch):
    owner=api.create_analysis(example.definition())
    try:
        def programming_error(*args,**kwargs): raise RuntimeError("injected programming error")
        monkeypatch.setattr(owner,"solve_linear",programming_error)
        with pytest.raises(RuntimeError,match="injected programming error"):
            owner.buckling(api.B2ReferenceBucklingRequest(np.zeros(48),(example.traction_source(),)))
    finally: owner.close()

def test_section_forward_identity_rejects_catastrophic_cancellation():
    source=example.traction_source()
    yz=np.r_[source.coordinates_yz_m,[[.1,.1],[.1,.1]]]
    w=np.r_[source.area_weights_m2,[1.,1.]]
    maps=np.concatenate((source.traction_map,np.zeros((2,3,6))))
    maps[-2,0,0]=1e20;maps[-1,0,0]=-1e20
    with pytest.raises(ValueError,match="forward six-resultant"):
        api.B2SectionTractionQuadrature("beam","catastrophic-cancellation",yz,w,maps)

def test_s3_bending_request_refuses_actual_preload():
    from dataclasses import replace
    definition=example.definition("s3")
    # Release shell out-of-plane coordinates, allowing genuine bending and shear
    # from Cartesian forces, while preserving the existing static admission.
    free=[i for i in range(48) if i not in set(range(6))|set(range(18,24)) and i%6!=5]
    from scipy import sparse
    definition=replace(definition,transformation=sparse.eye(48,format="csr")[:,free])
    owner=api.create_analysis(definition)
    try:
        load=np.zeros(48);load[14]=-1.
        with pytest.raises(ValueError,match="shear prestress unsupported|S3 bending prestress unsupported"):
            owner.buckling(api.B2ReferenceBucklingRequest(load,(example.traction_source(),)))
    finally: owner.close()

def _finite_section_fields(operator,q,station,rho):
    """Independent finite objective trace + exact cubic reference derivative."""
    length=float(operator.length)
    r0=Rotation.from_rotvec(q[3:6]).as_matrix();r1=Rotation.from_rotvec(q[9:12]).as_matrix()
    qc=r0@Rotation.from_rotvec(.5*Rotation.from_matrix(r0.T@r1).as_rotvec()).as_matrix()
    ends=np.array(((-length/2,0.,0.),(length/2,0.,0.)))+np.stack((q[:3],q[6:9]));middle=ends.mean(axis=0)
    local=(ends-middle)@qc
    d=np.r_[local[0]-(-length/2,0.,0.),Rotation.from_matrix(qc.T@r0).as_rotvec(),local[1]-(length/2,0.,0.),Rotation.from_matrix(qc.T@r1).as_rotvec()]
    delta=1e-3
    p=operator.trace(d,stations=(station-2*delta,station-delta,station,station+delta,station+2*delta)).pose
    derivative=(p[0]-8*p[1]+8*p[3]-p[4])/(12*delta*length)
    phi=p[2,3:];theta=np.linalg.norm(phi)
    k=np.array(((0.,-phi[2],phi[1]),(phi[2],0.,-phi[0]),(-phi[1],phi[0],0.)))
    if theta<1e-3:
        a=.5-theta**2/24+theta**4/720;b=1/6-theta**2/120+theta**4/5040
    else:
        a=(1-np.cos(theta))/theta**2;b=(theta-np.sin(theta))/theta**3
    right=np.eye(3)-a*k+b*k@k
    rotation=qc@Rotation.from_rotvec(phi).as_matrix()
    axial=qc@(np.array((1.,0.,0.))+derivative[:3])+rotation@np.cross(right@derivative[3:],rho)
    return axial,rotation[:,1],rotation[:,2]

@pytest.mark.parametrize("generalized",(False,True))
def test_full_sectional_scalar_green_work_independent_second_variation(generalized):
    definition=example.definition()
    if generalized:
        section=np.diag((90.,28.,35.,.4,.3,.5));section[0,4]=section[4,0]=.2;section[1,5]=section[5,1]=.1
        definition=replace(definition,members=(replace(definition.members[0],section=api.LinearSection.generalized(section)),))
    owner=api.create_analysis(definition)
    try:
        member,_=owner._members[0][1];operator=member.operator;source=example.traction_source()
        preload=np.array((.03,-.02,.04,.03,-.02,.025,-.01,.04,-.03,-.02,.03,-.04))
        nodes,weights=np.polynomial.legendre.leggauss(4);stations=(nodes+1.)/2
        resultants=operator.recover_sections(preload,stations=stations).resultants
        assert np.all(np.max(abs(resultants),axis=0)>1e-4)
        hessian=member_green_hessian(member,preload,source)
        direction=.3*np.sin(np.arange(12)+.2)
        def work(q):
            total=0.
            for station,weight,resultant in zip(stations,weights,resultants):
                for yz,area,mapping in zip(source.coordinates_yz_m,source.area_weights_m2,source.traction_map):
                    stress=mapping@resultant
                    axial,y,z=_finite_section_fields(operator,q,float(station),np.r_[0.,yz])
                    total += weight*float(operator.length)/2*area*(.5*stress[0]*(axial@axial-1.)+stress[1]*(axial@y)+stress[2]*(axial@z))
            return total
        expected=direction@hessian@direction;assert abs(expected)>1e-4
        errors=[]
        for step in (1e-3,3e-4,1e-4):
            actual=(work(step*direction)+work(-step*direction)-2*work(np.zeros(12)))/step**2
            errors.append(abs(actual-expected)/max(1.,abs(expected)))
        assert sum(error<=1e-6 for error in errors)>=2,errors
    finally: owner.close()

def test_oblique_global_first_station_offset_differential_and_zero_prescription_guard():
    physical=example.definition().members[0]
    rotation=Rotation.from_rotvec((.31,-.24,.17)).as_matrix()
    moved=replace(physical,reference_points_m=tuple(tuple(rotation@np.asarray(x)+(2.,-1.,.4)) for x in physical.reference_points_m),local_y_global=tuple(rotation@np.asarray(physical.local_y_global)))
    operator=moved.local_operator();frame=moved.local_frame_rows().T;transform=moved.local_dof_map()
    offset=np.array((.01,.03,-.02))
    for station in (0.,.37,1.):
        j,_,_,_=beam_reference_derivatives(operator,station)
        port=j.copy();port[:3] += np.cross(j[3:].T,offset).T
        expected=np.kron(np.eye(2),frame)@port@transform
        actual=moved.trace_global(np.zeros(12),stations=(station,),offset_local_m=offset).jacobian[0]
        np.testing.assert_allclose(actual,expected,rtol=1e-10,atol=1e-12)
    definition=example.definition();prescribed=np.zeros(48);prescribed[0]=.001
    owner=api.create_analysis(replace(definition,prescribed_offset=prescribed))
    try:
        assert not owner.reference_buckling_capabilities.eligible
        with pytest.raises(ValueError,match="prescribed prestress split"):
            owner.buckling(api.B2ReferenceBucklingRequest(np.zeros(48),(example.traction_source(),)))
    finally: owner.close()
