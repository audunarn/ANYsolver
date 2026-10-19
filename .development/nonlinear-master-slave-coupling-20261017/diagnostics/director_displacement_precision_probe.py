"""Same-input planar trace displacement arithmetic; no equilibrium solve."""
import argparse,copy,json,pickle
from decimal import Decimal as D, localcontext
from fractions import Fraction
from math import factorial
from pathlib import Path
import numpy as np
import arc_reference as arc
import shell_precision_probe as hp
import anysolver._director_trace as dt
import anysolver.corotational as cr
from anysolver.nonlinear_static import _assemble_nonlinear_system
from anysolver.matrix_assembly import assemble_stiffness_matrix,assemble_load_vector
from anysolver.assembly import build_constraint_transformation
from assessment_support import identical,source_identity


def stable_value(X,slave,e,xi,x):
    theta=[dt._Jet(v) for v in np.r_[x[3:6],x[9:12]]]
    R0=dt._exp(theta[:3]); R1=dt._exp(theta[3:]); phi=dt._log(R0.T@R1)
    W=dt._skew(phi); z=sum(t*t for t in phi)
    def difference(coefficients,offset):
        result=dt._Jet(0.)
        for n in range(len(coefficients)-1,-1,-1):
            power=2*n+offset
            factor=(xi-1.)*sum(xi**k for k in range(power))
            result=result*z+coefficients[n]*factor
        return result
    delta=dt._scale(W,difference(dt._COSC,1))+dt._scale(W@W,difference(dt._SINCC,2))
    Qdiff=(R0@delta@dt._inverse(dt._left(phi))@R0.T)*xi
    a,b,_=dt._coefficients(theta[:3]); W0=dt._skew(theta[:3]); E0=dt._scale(W0,a)+dt._scale(W0@W0,b)
    a,b,_=dt._coefficients(phi*xi); V=dt._skew(phi*xi); Ex=dt._scale(V,a)+dt._scale(V@V,b)
    Rdiff=E0+R0@Ex; Q=np.eye(3,dtype=object)*xi+Qdiff
    closure=[]; high=[]; low=[]
    for j in range(3):
        chord=Fraction(float(X[1,j]))-Fraction(float(X[0,j])); hi=float(chord)
        high.append(hi); low.append(float(chord-Fraction(hi)))
        closure.append(float(Fraction(float(X[0,j]))+Fraction(float(xi))*chord+Fraction(float(e[j]))-Fraction(float(slave[j]))))
    pos=x[:3]+Q@(x[6:9]-x[:3])+Qdiff@np.array(high)+Qdiff@np.array(low)+Rdiff@e+np.array(closure)
    return np.array([o.v for o in list(pos)+list(dt._log(np.eye(3,dtype=object)+Rdiff))]),np.array(closure)


def precise_value(X,slave,e,xi,x):
    X,slave,e,x=map(hp.decimal_array,(X,slave,e,x)); t=D.from_float(float(xi))
    if any(x[j]!=0 for j in (3,5,9,11)): raise ValueError('nonplanar saved state')
    phi=np.array([D(0),x[10]-x[4],D(0)],dtype=object); W=hp.skew(phi); z=sum(a*a for a in phi)
    def left(v):
        zz=sum(a*a for a in v); w=hp.skew(v)
        def series(offset):
            result=D(0)
            for n in range(39,-1,-1): result=result*zz+D((-1)**n)/D(factorial(2*n+offset))
            return result
        return hp.decimal_array(np.eye(3))+w*series(2)+(w@w)*series(3)
    def inverse(A):
        a,b,c=A[:,0],A[:,1],A[:,2]; bc=hp.cross(b,c)
        return np.array([bc,hp.cross(c,a),hp.cross(a,b)],dtype=object)/sum(a[j]*bc[j] for j in range(3))
    R0=hp.exp(np.array([D(0),x[4],D(0)],dtype=object)); R=R0@hp.exp(phi*t)
    Q=(R0@left(phi*t)@inverse(left(phi))@R0.T)*t
    pos=X[0]+x[:3]+Q@(X[1]-X[0]+x[6:9]-x[:3])+R@e-slave
    return np.array([*pos,D(0),x[4]+t*phi[1],D(0)],dtype=object)


def main():
    p=argparse.ArgumentParser(); p.add_argument('inputs'); p.add_argument('output'); a=p.parse_args(); out=Path(a.output); out.mkdir(parents=True,exist_ok=False)
    model,load,*_=arc.build_model(16,'nonmatching',arc.oracle(.002,30.))
    for el in model.mesh.elements.values():
        if isinstance(el,arc.InterpolatedBeamShellMPCElement): el.connection_trace='director_integrated'
    K0,_=assemble_stiffness_matrix(model); F,_=assemble_load_vector(model,load)
    _,_,T,*_=build_constraint_transformation(K0,F,model); mapping=cr.build_nonlinear_rotating_mpc_map(model,T)
    entries=[e for e in mapping.entries if e.director_trace_geometry is not None]
    cases=[]
    for path in sorted(Path(a.inputs).glob('accepted-*.pkl')):
        value=pickle.loads(path.read_bytes()); cases.append((path.name,value['u'],value['states'],float(value['lam'])))
    total=model.mesh.dof_manager.total_dofs; zero=np.zeros(total); cases.append(('zero',zero,{},0.))
    rigid=np.zeros(total); R=cr.rotation_matrix_from_vector(np.array([0.,.2,0.])); c=np.array([.2,-.1,.05])
    for node in model.mesh.nodes.values(): rigid[node.dofs[:3]]=(R-np.eye(3))@node.coords()+c; rigid[node.dofs[3:]]=[0.,.2,0.]
    cases.append(('rigid',rigid,{},0.)); cases.append(('small',cases[0][1]*1e-7,{},0.))
    reports=[]; raw={}
    with localcontext() as context:
        context.prec=70
        for name,u,H,lam in cases:
            ubefore=u.copy(); hbefore=copy.deepcopy(H); errors={mode:np.zeros(total) for mode in ('absolute','stable')}; per=[]
            fint,K,_=_assemble_nonlinear_system(model,u,H,5,tangent=True,kinematics='corotational',corotational_tangent='work_conjugate')
            J=mapping.jacobian(u); unit=max(float(np.linalg.norm(J.T@F)),1.); achieved=max(float(np.linalg.norm(J.T@(lam*F))),1.)
            for entry in entries:
                X,slave,e,xi,_=entry.director_trace_geometry; x=u[entry.director_dofs()]
                precise=precise_value(X,slave,e,xi,x); expected=np.array(precise,dtype=float)
                old=dt.director_trace_state(X,slave,e,xi,x)[0]; stable,closure=stable_value(X,slave,e,xi,x)
                row=dict(eid=entry.element_id,closure=closure.tolist())
                for mode,value in (('absolute',old),('stable',stable)):
                    # Subtract in Decimal before rounding the error itself.
                    error=np.array([D.from_float(float(v))-p for v,p in zip(value,precise)],dtype=float)
                    errors[mode][np.r_[entry.slave_u_dofs,entry.slave_theta_dofs]]=error
                    row[mode+'_position_error']=float(np.linalg.norm(error[:3])); row[mode+'_rotation_error']=float(np.linalg.norm(error[3:]))
                per.append(row)
            aggregate=[]
            for mode,error in errors.items():
                force=K@error; reduced=J.T@force
                aggregate.append(dict(mode=mode,map_error=float(np.linalg.norm(error)),Kdu_full=float(np.linalg.norm(force)),Kdu_reduced=float(np.linalg.norm(reduced)),
                    Kdu_unit_external_normalized=float(np.linalg.norm(reduced))/unit,Kdu_achieved_external_normalized=float(np.linalg.norm(reduced))/achieved))
            assert np.array_equal(u,ubefore) and identical(H,hbefore)
            raw[name]=dict(errors=errors,u=u.copy(),states=copy.deepcopy(H),lam=lam)
            reports.append(dict(state=name,attachments=len(entries),lam=lam,unit_external=unit,achieved_external=achieved,aggregate=aggregate,attachments_detail=per))
    result=dict(identity=source_identity(),diagnostic_only=True,no_FE_solve=True,decimal_digits=70,inputs_unchanged=True,
                force_scale_limit='Actual current full tangent times map error; not a terminal residual or full constitutive/pullback error assessment',checks=reports)
    (out/'result.json').write_text(json.dumps(result,indent=2)); (out/'raw.pkl').write_bytes(pickle.dumps(raw)); print(json.dumps(result))


if __name__=='__main__': main()
