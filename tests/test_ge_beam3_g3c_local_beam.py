"""Local implementation development only; not G3c graph qualification."""
import numpy as np
import pytest
from anysolver._ge_beam3_g3c_local_beam import LocalBeam, deformation
from anysolver.fe_core import FEModel,Material
from anysolver.elements import BeamElement,QuadraticBeamElement

SECTION=dict(area=1,Iy=.2,Iz=.3,J=.1,shear_factor_y=.8,shear_factor_z=.7,orientation=[0,0,1])
def exp(v):
    theta=np.linalg.norm(v); K=np.array([[0.,-v[2],v[1]],[v[2],0.,-v[0]],[-v[1],v[0],0.]])
    if theta<1e-12: return np.eye(3)+K+.5*K@K
    return np.eye(3)+np.sin(theta)/theta*K+(1-np.cos(theta))/theta**2*(K@K)
def log(R):
    c=np.clip((np.trace(R)-1)/2,-1,1); theta=np.arccos(c)
    v=np.array([R[2,1]-R[1,2],R[0,2]-R[2,0],R[1,0]-R[0,1]])/2
    return v*(1+theta**2/6) if theta<1e-6 else v*theta/np.sin(theta)
def err(a,b):
    return np.linalg.norm(np.asarray(a)-b)/max(1.,np.linalg.norm(a),np.linalg.norm(b))
def equal(a,b): assert err(a,b)<=1e-11
def make(n,reverse=False):
    ids=tuple(range(101,101+n)); ref=np.zeros((n,3)); ref[:,0]=np.linspace(0,1,n)
    anchor=ids[0 if n==2 else 1]
    if reverse: ids=ids[::-1]; ref=ref[::-1].copy()
    return LocalBeam('B'+str(n),ids,ref,anchor,100,.25,SECTION)
def state(n):
    z=.013*np.sin(np.arange(6*n)+.4)
    q=np.array([exp(np.array([.4,-.2,.3])+.01*i*np.array([1.,2.,-1.])) for i in range(n)])
    return z,q
def independent(p,z,q):
    d=p.descriptor(); ref=np.array(d['coordinates']); n=len(ref)
    current=ref+z.reshape(n,6)[:,:3]
    Q=np.array([exp(row[3:])@qi for row,qi in zip(z.reshape(n,6),q)])
    R=Q[d['node_ids'].index(d['anchor_node'])]
    local=np.empty((n,6)); local[:,:3]=(current-current.mean(axis=0))@R-(ref-ref.mean(axis=0))
    local[:,3:]=[log(R.T@qi) for qi in Q]
    m=FEModel('independent fresh local')
    for node,x in zip(d['node_ids'],ref): m.add_node(node,*x)
    cls=BeamElement if n==2 else QuadraticBeamElement
    e=cls(1,d['node_ids'],cross_section=dict(d['section'],geometric_nonlinearity='von_karman'))
    material=Material('independent',d['E'],d['nu'])
    f,k,_=e.compute_nonlinear_response(m.mesh,material,local.ravel(),None,3,True)
    return local.ravel(),f,k,e.compute_stiffness_matrix(m.mesh,material)

@pytest.mark.parametrize('n',(2,3))
def test_actual_reference_operator_and_finite_local_values(n):
    p=make(n); zero=np.zeros(6*n); I=np.tile(np.eye(3),(n,1,1))
    out=p.evaluate(zero,I); _,_,_,K=independent(p,zero,I)
    equal(out.chart_force,np.zeros(6*n)); equal(out.chart_hessian,K)
    z,q=state(n); out=p.evaluate(z,q); local,f,k,_=independent(p,z,q)
    equal(out.kinematics.deformation,local); equal(out.local_force,f); equal(out.local_tangent,k)
    equal(out.chart_hessian,out.chart_hessian.T)
    assert not out.production_qualified and not out.state_committed and not out.recovery_complete

@pytest.mark.parametrize('n',(2,3))
def test_complete_chart_and_spatial_directional_derivatives(n):
    p=make(n); z,q=state(n); v=np.cos(np.arange(6*n)+.7); v/=np.linalg.norm(v)
    out=p.evaluate(z,q)
    for h in (1e-4,1e-5,1e-6):
        plus=p.evaluate(z+h*v,q); minus=p.evaluate(z-h*v,q)
        assert err(out.chart_hessian@v,(plus.chart_force-minus.chart_force)/(2*h))<=1e-7
        assert err(out.spatial_row_chart_tangent@v,(plus.spatial_force-minus.spatial_force)/(2*h))<=1e-7
        assert err(out.kinematics.differential@v,(plus.kinematics.deformation-minus.kinematics.deformation)/(2*h))<=1e-7
        assert err(np.einsum('ijk,k->ij',out.kinematics.second,v),(plus.kinematics.differential-minus.kinematics.differential)/(2*h))<=1e-7

@pytest.mark.parametrize('n',(2,3))
def test_unrestricted_common_rotation_and_rebase(n):
    p=make(n); z,q=state(n); ref=np.array(p.descriptor()['coordinates'])
    Q=np.array([exp(row[3:])@qi for row,qi in zip(z.reshape(n,6),q)])
    u=z.copy(); u.reshape(n,6)[:,3:]=0
    out=p.evaluate(u,Q); old=p.evaluate(z,q)
    equal(out.kinematics.deformation,old.kinematics.deformation)
    equal(out.spatial_force,old.spatial_force)
    for angle in (np.array([np.pi,0,0]),np.array([0,1.4*np.pi,0]),np.array([.4,-.3,.2])):
        W=exp(angle); moved=u.copy()
        moved.reshape(n,6)[:,:3]=(ref+u.reshape(n,6)[:,:3])@W.T+[2,-3,1]-ref
        result=p.evaluate(moved,np.array([W@qi for qi in Q]))
        equal(result.kinematics.deformation,out.kinematics.deformation)
        equal(result.spatial_force.reshape(n,6),np.column_stack((out.spatial_force.reshape(n,6)[:,:3]@W.T,out.spatial_force.reshape(n,6)[:,3:]@W.T)))

@pytest.mark.parametrize('n',(2,3))
def test_reversal_retains_physical_anchor(n):
    p=make(n); reverse=make(n,True); z,q=state(n)
    a=p.evaluate(z,q); b=reverse.evaluate(z.reshape(n,6)[::-1].copy().ravel(),q[::-1].copy())
    order=np.arange(6*n).reshape(n,6)[::-1].ravel()
    equal(b.chart_force,a.chart_force[order]); equal(b.chart_hessian,a.chart_hessian[np.ix_(order,order)])

@pytest.mark.parametrize('n',(2,3))
def test_principal_mean_incident_and_rejected_fit_cases_are_admitted(n):
    p=make(n); d=p.descriptor(); ref=np.array(d['coordinates']); anchor=d['node_ids'].index(d['anchor_node'])
    delta=np.pi/10000
    angles=(-delta,delta) if n==2 else (-2*delta,delta,delta)
    q=np.array([exp(np.array([v,0.,0.])) for v in angles])
    before=deformation(ref,np.zeros(6*n),q,anchor)
    W=exp(np.array([np.pi,0.,0.]))
    u=np.zeros((n,6)); u[:,:3]=ref@W.T-ref
    after=deformation(ref,u.ravel(),np.array([W@qi for qi in q]),anchor)
    equal(after.deformation,before.deformation)
    if n==3:
        q=np.array([exp(np.array([v,0.,0.])) for v in (-2*np.pi/3,0,2*np.pi/3)])
        deformation(ref,np.zeros(6*n),q,anchor)
    else:
        q=np.array([np.eye(3),exp(np.array([8*np.pi/9,0.,0.]))])
        W=exp(np.array([0,np.pi/2,0])); u[:,:3]=ref@W.T-ref
        deformation(ref,u.ravel(),q,anchor)

def test_all_pairs_not_only_anchor_are_guarded():
    p=make(3); q=np.array([exp(np.array([v,0.,0.])) for v in (-.46*np.pi,0,.46*np.pi)])
    with pytest.raises(ValueError): p.evaluate(np.zeros(18),q)

def test_detached_definition_outputs_and_invalid_routes():
    p=make(2); z,q=state(2); descriptor=p.descriptor(); descriptor['E']=200
    a=p.evaluate(z,q); b=p.evaluate(z,q)
    assert a.chart_hessian.tobytes()==b.chart_hessian.tobytes()
    with pytest.raises(ValueError): a.chart_hessian.flags.writeable=True
    assert not hasattr(p,'commit') and not hasattr(p,'checkpoint')
    for field,value in (('fiber_plasticity',True),('geometric_nonlinearity','corotational'),('initial_stress',1)):
        with pytest.raises(ValueError):
            LocalBeam('B2',(101,102),np.array([[0.,0.,0.],[1.,0.,0.]]),101,100,.25,dict(SECTION,**{field:value}))
    with pytest.raises(AttributeError): p._body+=b' '
    object.__setattr__(p,'_body',p._body+b' ')
    with pytest.raises(ValueError): p.evaluate(z,q)

def test_mutation_of_caller_arrays_cannot_split_kinematic_and_chart_inputs(monkeypatch):
    import anysolver._ge_beam3_g3c_local_beam as module
    p=make(2); z,q=state(2); expected=p.evaluate(z.copy(),q.copy())
    original=module.deformation
    def observed(*args):
        result=original(*args)
        z[:]=.2; q[:]=np.eye(3)
        return result
    monkeypatch.setattr(module,'deformation',observed)
    actual=p.evaluate(z,q)
    equal(actual.spatial_force,expected.spatial_force)
    equal(actual.spatial_row_chart_tangent,expected.spatial_row_chart_tangent)

@pytest.mark.parametrize('n',(2,3))
def test_physical_orientation_scale_never_uses_legacy_fallback(n):
    p=make(n); d=p.descriptor(); z,q=state(n); results=[]
    for scale in (1.,1e-200,1e200):
        section=dict(SECTION,orientation=[0,scale,0])
        a=LocalBeam(d['family'],tuple(d['node_ids']),np.array(d['coordinates']),d['anchor_node'],100,.25,section)
        assert a.descriptor()['section']['orientation']==[0.,1.,0.]
        results.append(a.evaluate(z,q))
    for value in results[1:]: equal(value.chart_hessian,results[0].chart_hessian)

def test_coherent_definition_swap_during_trial_rejects(monkeypatch):
    import anysolver._ge_beam3_g3c_local_beam as module
    p=make(2); d=p.descriptor(); z,q=state(2)
    other=LocalBeam('B2',tuple(d['node_ids']),np.array(d['coordinates']),d['anchor_node'],200,.25,SECTION)
    for name in ('_body','_seal'):
        with pytest.raises(AttributeError): setattr(p,name,getattr(other,name))
    original=module.deformation
    def changed(*args):
        result=original(*args)
        object.__setattr__(p,'_body',other._body); object.__setattr__(p,'_seal',other._seal)
        return result
    monkeypatch.setattr(module,'deformation',changed)
    with pytest.raises(ValueError): p.evaluate(z,q)

def test_nonfinite_computed_kinematics_fail_closed():
    p=make(2); ref=np.array(p.descriptor()['coordinates']); z=np.zeros((2,6)); z[:,0]=1e308
    with np.errstate(over='ignore',invalid='ignore'),pytest.raises(ValueError):
        deformation(ref,z.ravel(),np.tile(np.eye(3),(2,1,1)),0)

def test_runner_rejects_changed_bound_source_and_payload(tmp_path):
    import importlib.util,json,shutil
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    spec=importlib.util.spec_from_file_location('local_runner',root/'scripts/run_ge_beam3_g3c_local.py')
    runner=importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
    c=json.loads((root/'docs/reference_cases/ge_beam3_g3c_objective_beam_frame_contract_v1.json').read_bytes())
    paths=[r['path'] for r in c['sources']]+list(c['payloads'])
    for name in paths:
        target=tmp_path/name; target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(root/name,target)
    runner.verify_equation_bindings(c,tmp_path)
    for name in ('src/anysolver/elements.py','docs/GE_BEAM3_G3C_OBJECTIVE_BEAM_FRAME_CONTRACT.md'):
        target=tmp_path/name; original=target.read_bytes(); target.write_bytes(original+b'\n')
        with pytest.raises(ValueError): runner.verify_equation_bindings(c,tmp_path)
        target.write_bytes(original)
