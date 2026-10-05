"""Independent analytic parabola/circle quadrature at one saved accepted pose.

No production station, projection, root, normal-derivative or quadrature kernel.
Not a global integration-error certificate or another coupled equilibrium solve.
"""
from hashlib import sha256
from pathlib import Path
from math import acos,atan2,ceil,floor,pi
import json,os,sys,time
import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy.integrate import quad_vec
REPO=Path('C:/ANYworkspaceWork/ANYsolver-contact-main-reconcile-20261001')
sys.path.insert(0,str(REPO/'tests'))
from test_general_contact_native_curved_s3_static import _analysis
RAW=Path(__file__).parent/'installed_seeded_k8e7_component_enclosure/actual_result.json-enforcement.checkpoint'

def oracle(work,p,low,U,u,order,eps):
    skin=work.shell;dofs=work.shell_translation_dofs
    bases=dofs[:,0];q=np.array([u[b:b+6] for b in bases])
    corners=skin.reference_positions+q[:,:3]+skin.physical_offset*np.cross(q[:,3:],skin.director)
    e1=corners[1]-corners[0];e2=corners[2]-corners[0]
    cross=np.cross(e1,e2);length=np.linalg.norm(cross);n=cross/length
    dn=np.zeros((3,9));origin=np.zeros((3,9));origin[:,:3]=np.eye(3)
    for i in range(9):
        v=np.zeros((3,3));v.flat[i]=1.
        dc=np.cross(v[1]-v[0],e2)+np.cross(e1,v[2]-v[0])
        dn[:,i]=(dc-n*np.dot(n,dc))/length
    M=np.zeros((9,len(u)))
    for vertex,base in enumerate(bases):
        M[3*vertex:3*vertex+3,base:base+3]=np.eye(3)
        for j in range(3):M[3*vertex:3*vertex+3,base+3+j]=skin.physical_offset*np.cross(np.eye(3)[j],skin.director)
    gl,gw=leggauss(order);radius=work.contact.radius;k=work.contact.stiffness
    al,ar=work.contact.rule.definition['angle_range'];lo,hi=work.contact.rule.definition['xi_range']
    def axial(xi):
        # This fixture is explicitly on the second physical cell.
        j=np.sqrt(1+.16*xi*xi);transverse=np.array((.4*xi,1.,0.))/j
        lift=np.array((0.,.2*xi*(1-xi),0.))
        centre=(1-xi)*(p[1]+low[1])+xi*(p[2]+low[2])+U[1]@lift
        A=float(n@(centre-corners[0]));B=float(n@(U[1]@np.array((0.,0.,radius))))
        C=float(n@(U[1]@(-radius*transverse)))
        points=[al,ar];amp=np.hypot(B,C)
        if amp and abs(A)<=amp:
            phase=atan2(C,B);root=acos(np.clip(-A/amp,-1.,1.))
            for angle in (phase-root,phase+root):
                points.extend(angle+turn*2*pi for turn in range(ceil((al-angle)/(2*pi)),floor((ar-angle)/(2*pi))+1))
        points=sorted(set(points));out=np.zeros(42+len(u))
        for left,right in zip(points,points[1:]):
            mid=(left+right)/2
            if A+B*np.cos(mid)+C*np.sin(mid)>=0:continue
            for angle,weight in zip(mid+(right-left)*gl/2,gw*(right-left)/2):
                arm=U[1]@(lift+radius*(-np.sin(angle)*transverse+np.cos(angle)*np.array((0.,0.,1.))))
                point=(1-xi)*(p[1]+low[1])+xi*(p[2]+low[2])+arm
                gap=float(n@(point-corners[0]));gradient=np.zeros_like(out)
                gradient[6:9]=(1-xi)*n;gradient[12:15]=xi*n
                gradient[21:24]=np.cross(arm,n)
                gradient[42:]=M.T@(dn.T@(point-corners[0])-origin.T@n)
                # The fixture's reference radial frame is (z,-transverse).
                # Its tangent stretch is j-.4*r*sin(angle)/j**2.
                measure=weight*radius*(j-.4*radius*np.sin(angle)/j**2)
                out+=k*gap*measure*gradient
        return out
    value,error,info=quad_vec(axial,lo,hi,epsabs=eps,epsrel=eps,limit=64,full_output=True)
    if not info.success:raise RuntimeError('independent axial integration: '+info.message)
    return value,dict(error_estimate=float(error),evaluations=info.neval,angular_order=order,tolerance=eps)

def test_independent_saved_fine_residual_and_linearized_tip():
    start=time.monotonic();raw=RAW.read_bytes()
    owner=_analysis(physical_fibres=True,plastic_fibres=True,normal_stiffness_Pa_per_m=8e7,integration_budget_policy='certified_active',root_tangent_enclosure_policy='componentwise')
    state,_=owner._restore(raw,sha256(raw).hexdigest());m=state.mechanical;u=state.shell_displacement
    work=owner.pairs[0].work;nodes=owner.context.nodes[0]
    args=(work,m.positions[nodes],m.position_low[nodes],m.cell_rotations[0],u)
    independent,first=oracle(*args,12,1e-10)
    refined,second=oracle(*args,24,1e-12)
    base=work.evaluate(*args[1:])
    _,K,_=owner._assemble_structural(m,u,1.,owner.initial.native_histories)
    slots=np.r_[owner.context.slots[0],owner.context.count+np.arange(len(u))]
    rows,cols=np.meshgrid(slots,slots,indexing='ij');np.add.at(K,(rows,cols),base.tangent.toarray())
    free=np.r_[owner.context.free,owner.context.count+owner.shell_free]
    def response(local):
        delta=np.zeros(len(K));np.add.at(delta,slots,local)
        correction=np.zeros(len(K));correction[free]=np.linalg.solve(K[np.ix_(free,free)],-delta[free])
        return float(correction[6*owner.context.node_ids.index(3)+2])
    correction=response(refined-base.residual);refinement=response(refined-independent)
    scale=0.00014923981490251538
    record=dict(checkpoint_sha256=sha256(raw).hexdigest(),scope='fixed-pose independent residual and local sensitivity only',
        elapsed_s=time.monotonic()-start,controls=[first,second],
        relative_residual_difference=float(np.linalg.norm(refined-base.residual)/np.linalg.norm(refined)),
        residual_refinement_norm=float(np.linalg.norm(refined-independent)),
        tip_correction_m=correction,tip_relative_correction=abs(correction/scale),
        refinement_tip_correction_m=refinement,refinement_tip_relative_correction=abs(refinement/scale),
        log_stiffness_tip_derivative_m=response(base.residual),
        log_stiffness_tip_relative_derivative=abs(response(base.residual)/scale))
    Path(os.environ['CONTACT_APP_RESULT_RECORD']+'-independent-residual.json').write_text(json.dumps(record,indent=2))
    assert record['refinement_tip_relative_correction']<=.0002,record
    assert record['tip_relative_correction']<=.002,record
    assert record['relative_residual_difference']<=1e-5,record
