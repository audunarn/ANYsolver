"""One same-float-input Decimal pullback/gauge discriminant, no FE solve."""
import argparse,copy,json,pickle
from decimal import Decimal as D, localcontext
from pathlib import Path
from math import factorial
import numpy as np
import arc_reference as arc
import anysolver.corotational as cr
from anysolver.matrix_assembly import assemble_stiffness_matrix,assemble_load_vector
from anysolver.assembly import build_constraint_transformation
from assessment_support import identical,source_identity


def decimal_array(a): return np.array([D.from_float(float(x)) for x in np.asarray(a).flat],dtype=object).reshape(np.shape(a))
def norm(v): return sum(x*x for x in v).sqrt()
def cross(a,b): return np.array([a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]],dtype=object)
def mean(a): return np.array([sum(a[:,j])/D(len(a)) for j in range(a.shape[1])],dtype=object)
def frame(a,dx,de):
    t=dx@a; t=t/norm(t); n=cross(t,de@a); n=n/norm(n)
    return np.column_stack((t,cross(n,t),n))
def skew(v): return np.array([[D(0),-v[2],v[1]],[v[2],D(0),-v[0]],[-v[1],v[0],D(0)]],dtype=object)
def exp(v):
    z=sum(x*x for x in v)
    def series(offset):
        result=D(0)
        for n in range(39,-1,-1): result=result*z+D((-1)**n)/D(factorial(2*n+offset))
        return result
    W=skew(v)
    return decimal_array(np.eye(3))+W*series(1)+(W@W)*series(2)
def atan(x):
    t=x/(D(1)+(D(1)+x*x).sqrt()); z=t*t; value=D(0)
    for n in range(139,-1,-1): value=value*z+D((-1)**n)/D(2*n+1)
    return D(2)*t*value
def log(R):
    a=np.array([R[2,1]-R[1,2],R[0,2]-R[2,0],R[1,0]-R[0,1]],dtype=object)/D(2)
    s=norm(a); c=(sum(R[i,i] for i in range(3))-D(1))/D(2)
    if s < D('1e-25'): return a
    if c<=0: raise ValueError('diagnostic control outside small relative-angle domain')
    return a*(atan(s/c)/s)
def precise_deformation(X,u,dx,de):
    R=frame(X+u[:,:3],dx,de)@frame(X,dx,de).T
    arm=X-mean(X); trans=u[:,:3]-mean(u[:,:3]); out=np.empty(u.shape,dtype=object)
    for i in range(len(X)):
        out[i,:3]=R.T@trans[i]+(R.T-decimal_array(np.eye(3)))@arm[i]
        out[i,3:]=log(R.T@exp(u[i,3:]))
    return out.reshape(-1)
def centered_deformation(original):
    def evaluate(ref,el,value,**kwargs):
        if ref.category!='shell' or ref.center_dN is None: return original(ref,el,value,**kwargs)
        u=np.asarray(value).reshape(el.num_nodes,6)
        arm=cr._centered_nodal_vectors(ref.coordinates); trans=cr._centered_nodal_vectors(u[:,:3]); geom=arm+trans
        R=cr._shell_center_frame(el,geom)@ref.frame.T
        diff=cr._stable_shell_rotation_difference(R) if kwargs.get('stable_shell_rotation',False) else R.T-np.eye(3)
        ud=np.zeros_like(u)
        for i in range(el.num_nodes):
            ud[i,:3]=R.T@trans[i]+diff@arm[i]
            ud[i,3:]=cr.rotation_vector_from_matrix(R.T@cr.rotation_matrix_from_vector(u[i,3:]))
        return ud.reshape(-1),R,geom
    return evaluate


def main():
    p=argparse.ArgumentParser(); p.add_argument('output'); p.add_argument('--all-shells',action='store_true'); a=p.parse_args(); out=Path(a.output); out.mkdir(parents=True,exist_ok=False)
    model,load,*_=arc.build_model(32,'matching',arc.oracle(0.,30.))
    K0,_=assemble_stiffness_matrix(model); F,_=assemble_load_vector(model,load)
    _,_,T,*_=build_constraint_transformation(K0,F,model); external=max(float(np.linalg.norm(T.T@F)),1.)
    refs=cr._corotational_cache(model); shells=[eid for eid,r in refs.items() if r.category=='shell']; selected=shells if a.all_shells else [shells[0],shells[len(shells)//2],shells[-1]]
    original=cr._corotational_deformation_state; centered=centered_deformation(original); rows=[]; raw={}
    aggregate={mode:np.zeros(model.mesh.dof_manager.total_dofs) for mode in ('absolute','centered')}
    with localcontext() as ctx:
        ctx.prec=70
        for eid in selected:
            el=model.mesh.elements[eid]; ref=refs[eid]; X=ref.coordinates; controls={}
            theta=np.pi/6*X[:,0]; u=np.zeros((len(X),6)); u[:,0]=np.sin(theta)/(np.pi/6)-X[:,0]; u[:,2]=(np.cos(theta)-1)/(np.pi/6); u[:,4]=theta
            controls['circular']=u
            if eid==selected[-1]:
                rigid=cr.rotation_matrix_from_vector(np.array([.2,-.15,.1])); v=np.zeros_like(u); v[:,:3]=(rigid@X.T).T-X+np.array([.2,-.3,.1]); v[:,3:]=[.2,-.15,.1]; controls['rigid']=v
                for name,A in [('affine',np.diag([.0003,-.0001,0.])),('shear',np.array([[0.,.0002,0.],[0.,0.,0.],[0.,0.,0.]]))]:
                    v=np.zeros_like(u); v[:,:3]=X@A.T; controls[name]=v
            _,dx,de=el.compute_shape_functions(0.,0.); dX=decimal_array(X); ddx=decimal_array(dx); dde=decimal_array(de)
            elastic=el.compute_stiffness_matrix(model.mesh,model.get_material(el.material_name)); dK=decimal_array(elastic)
            for name,u in controls.items():
                before=u.copy(); coordinates=X.copy(); du=decimal_array(u); ud=precise_deformation(dX,du,ddx,dde)
                B=np.empty((u.size,u.size),dtype=object); h=D('1e-25')
                for j in range(u.size):
                    plus=du.copy().reshape(-1); minus=plus.copy(); plus[j]+=h; minus[j]-=h
                    B[:,j]=(precise_deformation(dX,plus.reshape(u.shape),ddx,dde)-precise_deformation(dX,minus.reshape(u.shape),ddx,dde))/(D(2)*h)
                exact=np.asarray(B.T@(dK@ud),dtype=float); records=[]
                material=model.get_material(el.material_name)
                f_actual,*_=el.compute_nonlinear_response(model.mesh,material,np.asarray(ud,dtype=float),None,5,False)
                remainder=float(np.linalg.norm(f_actual-elastic@np.asarray(ud,dtype=float)))
                for mode,evaluate in [('absolute',original),('centered',centered)]:
                    value,R,geom=evaluate(ref,el,u.reshape(-1)); D0,U,G=cr._pullback_jacobian_factors(ref,el,geom,u[:,3:],R); bb=D0+U@G
                    ff,*_=el.compute_nonlinear_response(model.mesh,material,value,None,5,False); force=bb.T@ff
                    err=float(np.linalg.norm(force-exact))
                    if name=='circular':
                        dofs=np.concatenate([model.mesh.dof_manager.get_node_dofs(n) for n in el.node_ids])
                        np.add.at(aggregate[mode],dofs,force-exact)
                    records.append(dict(mode=mode,deformation_absolute_error=float(np.linalg.norm(value-np.asarray(ud,dtype=float))),
                        jacobian_absolute_error=float(np.linalg.norm(bb-np.asarray(B,dtype=float))),force_absolute_error=err,force_error_external_normalized=err/external))
                    raw[eid,name,mode]=dict(u=u.copy(),ud=value,B=bb,f=force)
                assert np.array_equal(u,before) and np.array_equal(X,coordinates)
                rows.append(dict(eid=eid,control=name,reference_force_norm=float(np.linalg.norm(exact)),constitutive_nonlinear_remainder=remainder,records=records))
    report=dict(identity=source_identity(),diagnostic_only=True,no_FE_solve=True,external_reference=external,decimal_digits=70,
                reference='Same float X/u and frozen float elastic stiffness; Decimal frame/deformation and 1e-25 symmetric pullback derivative; nonlinear local-law remainder reported separately',
                inputs_unchanged=True,checks=rows,
                aggregate=[dict(mode=mode,shells=len(selected),full_error_norm=float(np.linalg.norm(error)),
                    reduced_error_norm=float(np.linalg.norm(T.T@error)),
                    reduced_error_external_normalized=float(np.linalg.norm(T.T@error))/external)
                    for mode,error in aggregate.items()],
                limitations='Manufactured same-input shell pullback precision only; actual stalled-state residual, beam/other precision contributions and nonlinear solver stopping mechanism not measured')
    (out/'raw.pkl').write_bytes(pickle.dumps(raw)); (out/'result.json').write_text(json.dumps(report,indent=2)); print(json.dumps(report))


if __name__=='__main__': main()
