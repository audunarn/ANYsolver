"""Bounded private shell development; no graph or recovery qualification."""
import itertools
import json
import numpy as np
import pytest
from anysolver import _ge_beam3_g3c_local_shell as s
from anysolver._ge_beam3_variational_shell import deformation as old_deformation

SHAPES = ('square', 'rectangle', 'right', 'equilateral')
STEPS = (1e-4, 1e-5, 1e-6)

def exp(v):
    angle = np.linalg.norm(v)
    k = np.array([[0., -v[2], v[1]], [v[2], 0., -v[0]], [-v[1], v[0], 0.]])
    if angle < 1e-12: return np.eye(3)+k+.5*k@k
    return np.eye(3)+np.sin(angle)/angle*k+(1-np.cos(angle))/angle**2*k@k

def log(q):
    cosine = np.clip((np.trace(q)-1)/2, -1., 1.)
    angle = np.arccos(cosine)
    v = np.array([q[2,1]-q[1,2], q[0,2]-q[2,0], q[1,0]-q[0,1]])/2
    return v*(1+angle**2/6) if angle < 1e-6 else v*angle/np.sin(angle)

def err(a, b):
    a, b = np.asarray(a), np.asarray(b)
    assert np.isfinite(a).all() and np.isfinite(b).all()
    norms = [np.linalg.norm(a-b), np.linalg.norm(a), np.linalg.norm(b)]
    assert np.isfinite(norms).all()
    return norms[0]/max(1., *norms[1:])

def equal(a, b): assert err(a, b) <= 1e-11

def make(shape, order=None, W=None, shift=None, polarity=1):
    if shape in ('square', 'rectangle'):
        ref = np.array([[0.,0.,0.], [1.,0.,0.], [1.,1.,0.], [0.,1.,0.]])
        if shape == 'rectangle': ref[:, 0] *= 2
    else:
        ref = np.array([[0.,0.,0.], [1.,0.,0.], [0.,1.,0.]])
        if shape == 'equilateral': ref[2, :2] = [.5, np.sqrt(3)/2]
    n = len(ref); ids = np.arange(101, 101+n)
    normal = np.array([0.,0.,1.]); direction = np.array([1.,0.,0.])
    if order is not None: ref = ref[order].copy(); ids = ids[order]
    if W is not None: ref = ref@W.T+shift; normal = W@normal; direction = W@direction
    return s.LocalShell('Q4' if n == 4 else 'S3-V2D', tuple(map(int, ids)), ref, normal, direction,
                        director_polarity=polarity)

def state(p):
    n = len(p.descriptor()['node_ids'])
    u = .009*np.sin(np.arange(6*n)+.4)
    q = np.array([exp(np.array([.09,-.04,.06])+.004*i*np.array([1.,2.,-1.])) for i in range(n)])
    return u, q

def independent(reference, u, qa):
    n = len(reference); x = reference+u.reshape(n,6)[:, :3]
    Xc = reference-reference.mean(axis=0); xc = x-x.mean(axis=0)
    left, _, right = np.linalg.svd(xc.T@Xc)
    correction = np.diag([1.,1.,np.linalg.det(left@right)])
    R = left@correction@right
    q = np.array([exp(row[3:])@base for row, base in zip(u.reshape(n,6),qa)])
    d = np.empty((n,6)); d[:,:3] = xc@R-Xc
    d[:,3:] = [log(R.T@qi) for qi in q]
    return d.ravel(), R, q

def permutations(n):
    if n == 3: return list(itertools.permutations(range(3)))
    return [tuple((i+k)%4 for i in base) for base in ((0,1,2,3),(0,3,2,1)) for k in range(4)]

@pytest.mark.parametrize('shape', SHAPES)
def test_independent_pose_actual_reference_rank_and_rigid_modes(shape):
    p = make(shape); desc = p.descriptor(); ref = np.array(desc['coordinates']); n = len(ref)
    u, qa = state(p); out = p.evaluate(u, qa)
    d, R, q = independent(ref, u, qa)
    equal(out.kinematics.deformation, d); equal(out.kinematics.frame, R); equal(out.kinematics.rotations, q)
    model, e, mat, origin = s.family_objects(desc)
    f, k, _ = e.compute_nonlinear_response(model.mesh, mat, d, origin, 3, True)
    equal(out.local_force, f); equal(out.local_tangent, k)
    zero = p.evaluate(np.zeros(6*n), np.tile(np.eye(3),(n,1,1)))
    K = e.compute_stiffness_matrix(model.mesh, mat)
    equal(zero.chart_hessian, K)
    rigid = np.zeros((6*n,6))
    for i, x in enumerate(ref):
        rigid[6*i:6*i+3, :3] = np.eye(3)
        for j in range(3): rigid[6*i:6*i+3,3+j] = np.cross(np.eye(3)[j],x)
        rigid[6*i+3:6*i+6,3:] = np.eye(3)
    equal(K@rigid, np.zeros((6*n,6)))
    assert np.linalg.matrix_rank(K, tol=1e-11*np.linalg.norm(K)) == 6*n-6
    assert not out.recovery_complete and not out.production_qualified and not out.state_committed

@pytest.mark.parametrize('shape', SHAPES)
def test_all_steps_complete_map_energy_chart_and_spatial_derivatives(shape):
    p = make(shape); u, qa = state(p); out = p.evaluate(u, qa)
    v = np.cos(np.arange(len(u))+.7); v /= np.linalg.norm(v)
    equal(out.chart_hessian, out.chart_hessian.T)
    geometric = np.einsum('i,ijk->jk', out.local_force, out.kinematics.second)
    assert np.linalg.norm(geometric) > 1e-7
    for h in STEPS:
        plus, minus = p.evaluate(u+h*v,qa), p.evaluate(u-h*v,qa)
        assert err(out.kinematics.differential@v,(plus.kinematics.deformation-minus.kinematics.deformation)/(2*h)) <= 1e-7
        assert err(np.einsum('ijk,k->ij',out.kinematics.second,v),(plus.kinematics.differential-minus.kinematics.differential)/(2*h)) <= 1e-7
        assert err(out.chart_force@v,(plus.energy-minus.energy)/(2*h)) <= 1e-7
        assert err(out.chart_hessian@v,(plus.chart_force-minus.chart_force)/(2*h)) <= 1e-7
        assert err(out.spatial_row_chart_tangent@v,(plus.spatial_force-minus.spatial_force)/(2*h)) <= 1e-7
        for j, ch in enumerate(out.channels):
            pc, mc = plus.channels[j], minus.channels[j]
            assert err(ch.force@out.kinematics.differential@v,(pc.energy-mc.energy)/(2*h)) <= 1e-7

@pytest.mark.parametrize('shape', SHAPES)
def test_common_pi_1_4pi_and_rebase_and_work_wrench(shape):
    p = make(shape); ref = np.array(p.descriptor()['coordinates']); n = len(ref)
    u, qa = state(p); before = p.evaluate(u, qa); rebased = u.copy(); rebased.reshape(n,6)[:,3:] = 0
    Q = before.kinematics.rotations
    base = p.evaluate(rebased, Q)
    equal(base.kinematics.deformation,before.kinematics.deformation)
    equal(base.spatial_force,before.spatial_force); equal(base.energy,before.energy)
    # State fields may differ by last-bit reconstruction; compare decoded numeric
    # values, never pretend a graph accepted-origin replay is being tested here.
    def compare(a,b,key=None):
        if isinstance(a,dict):
            assert a.keys()==b.keys()
            for k in a: compare(a[k],b[k],k)
        elif isinstance(a,list):
            assert len(a)==len(b)
            for x,y in zip(a,b): compare(x,y)
        elif isinstance(a,(int,float)) and not isinstance(a,bool): equal(a,b)
        elif key == 'state_integrity_sha256':
            # The authentic candidate seals bind the reconstructed binary64 local
            # vector. These are checked by the source, not equated across roundoff.
            assert isinstance(a,str) and len(a)==64 and isinstance(b,str) and len(b)==64
        else: assert a==b
    compare(json.loads(base.candidate),json.loads(before.candidate))
    assert p.evaluate(u,qa).candidate == before.candidate
    for vector in (np.zeros(3),np.array([.4,-.3,.2]),np.array([np.pi,0.,0.]),np.array([0.,1.4*np.pi,0.])):
        W = exp(vector); changed = rebased.copy()
        changed.reshape(n,6)[:,:3] = (ref+rebased.reshape(n,6)[:,:3])@W.T+[2,-3,1]-ref
        out = p.evaluate(changed,np.array([W@qi for qi in Q]))
        equal(out.kinematics.deformation,base.kinematics.deformation); equal(out.energy,base.energy)
        expected = base.spatial_force.reshape(n,6)
        equal(out.spatial_force.reshape(n,6),np.c_[expected[:,:3]@W.T,expected[:,3:]@W.T])
        force = out.spatial_force.reshape(n,6)
        equal(force[:,:3].sum(axis=0),np.zeros(3))
        equal((np.cross(ref+changed.reshape(n,6)[:,:3],force[:,:3])+force[:,3:]).sum(axis=0),np.zeros(3))

@pytest.mark.parametrize('shape', SHAPES)
def test_all_numberings_passive_coordinates_and_director_reversal(shape):
    p = make(shape); u,qa = state(p); n = len(qa); base = p.evaluate(u,qa)
    for ordering in permutations(n):
        order = np.array(ordering); dofs = np.arange(6*n).reshape(n,6)[order].ravel()
        out = make(shape, order=order).evaluate(u[dofs].copy(),qa[order].copy())
        equal(out.energy,base.energy); equal(out.chart_force,base.chart_force[dofs])
        equal(out.chart_hessian,base.chart_hessian[np.ix_(dofs,dofs)])
    W = exp(np.array([0.,0.,np.pi/2])); moved = make(shape,W=W,shift=np.array([2.,-3.,1.]))
    z = np.c_[u.reshape(n,6)[:,:3]@W.T,u.reshape(n,6)[:,3:]@W.T].ravel()
    out = moved.evaluate(z,np.array([W@q@W.T for q in qa])); equal(out.energy,base.energy)
    equal(out.spatial_force.reshape(n,6),np.c_[base.spatial_force.reshape(n,6)[:,:3]@W.T,base.spatial_force.reshape(n,6)[:,3:]@W.T])
    reversed_director = make(shape,polarity=-1).evaluate(u,qa)
    equal(reversed_director.energy,base.energy); equal(reversed_director.local_force,base.local_force)

@pytest.mark.parametrize('shape', SHAPES)
def test_old_map_matching_physical_pose_and_common_chart(shape):
    p = make(shape); ref = np.array(p.descriptor()['coordinates']); u,qa = state(p)
    qa[:] = np.eye(3)
    new = s.deformation(ref,u,qa); old = old_deformation(ref,u)
    equal(new.deformation,old[0]); equal(new.differential,old[1]); equal(new.second,old[2])
    # Nonzero accepted matrices: compose total logs only in this independently
    # known test pose; directional differences transform the old map to eta.
    u,qa = state(p); v = np.sin(np.arange(len(u))+.2); v/=np.linalg.norm(v)
    new = s.deformation(ref,u,qa)
    def old_in_new_chart(z):
        total = z.copy(); total.reshape(-1,6)[:,3:] = [log(exp(row[3:])@q) for row,q in zip(z.reshape(-1,6),qa)]
        return old_deformation(ref,total)[0]
    equal(new.deformation,old_in_new_chart(u))
    for h in STEPS:
        assert err(new.differential@v,(old_in_new_chart(u+h*v)-old_in_new_chart(u-h*v))/(2*h)) <= 1e-7

@pytest.mark.parametrize('shape', SHAPES)
def test_top_gap_log_domain_and_guard_before_evaluation(shape,monkeypatch):
    p = make(shape); ref = np.array(p.descriptor()['coordinates']); n=len(ref); I=np.tile(np.eye(3),(n,1,1))
    def forbidden(*args): raise AssertionError('family must not run after invalid kinematics')
    monkeypatch.setattr(s,'family_objects',forbidden)
    u=np.zeros((n,6)); u[:,:3]=-ref; u[:,0]=np.arange(n)-ref[:,0]
    with pytest.raises(ValueError,match='nonunique'): p.evaluate(u.ravel(),I)
    with pytest.raises(ValueError): p.evaluate(np.full(6*n,np.nan),I)
    bad=I.copy(); bad[0,0,0]=-1
    with pytest.raises(ValueError,match='proper'): p.evaluate(np.zeros(6*n),bad)
    q=np.tile(exp(np.array([.95*np.pi,0.,0.])),(n,1,1))
    with pytest.raises(ValueError): p.evaluate(np.zeros(6*n),q)
    z=np.zeros((n,6)); z[0,3]=.91*np.pi
    with pytest.raises(ValueError,match='cutback'): p.evaluate(z.ravel(),I)

def test_q4_checkerboard_and_independent_signed_work_sentinels():
    p=make('square'); I=np.tile(np.eye(3),(4,1,1)); u=np.zeros((4,6));u[:,2]=[.01,-.01,.01,-.01]
    out=p.evaluate(u.ravel(),I); channels={c.name:c for c in out.channels}
    baseline=json.loads(channels['QUALIFIED_MIXED_PHYSICAL'].stations)
    vk=json.loads(channels['COMPATIBLE_VK_MEMBRANE'].stations)
    equal(baseline['source_physical']['membrane_strain'],np.zeros((4,3)))
    assert np.linalg.norm(vk['strain'])>1e-6
    assert channels['REMOVED_COMPATIBLE_LINEAR_MEMBRANE'].sign==-1
    for c in out.channels:
        if c.numerical: assert json.loads(c.stations) is None
    # Frozen deterministic mixed mode, not coefficient tuning. Diagnose the
    # erroneous use of one Beff with mixed and compatible-linear resultants.
    u,qa=state(p); out=p.evaluate(u,qa); ch={c.name:c for c in out.channels}
    baseline=json.loads(ch['QUALIFIED_MIXED_PHYSICAL'].stations)
    vk=json.loads(ch['COMPATIBLE_VK_MEMBRANE'].stations)
    lin=json.loads(ch['REMOVED_COMPATIBLE_LINEAR_MEMBRANE'].stations)
    physical=baseline['source_physical']; Nm=np.array(physical['membrane_resultants'])
    # Square source center/Equation7 frames coincide up to source transport.
    src=np.array(baseline['source_mixed']['frame']); center=np.array(vk['reference_frame'])
    Ng=s.tensor(Nm,src); local=np.array([center.T@v@center for v in Ng])
    Nm=np.c_[local[:,0,0],local[:,1,1],local[:,0,1]]
    extra=np.einsum('g,gij,gi->j',vk['weights'],np.array(vk['strain_differential'])-lin['strain_differential'],Nm-lin['resultants'])
    assert np.linalg.norm(extra)>1e-10

def test_owned_definition_detached_results_reentry_and_finite_sums(monkeypatch):
    p=make('right'); u,qa=state(p); before=p.evaluate(u,qa)
    assert isinstance(before.candidate,bytes)
    for a in (before.local_force,before.chart_hessian,before.kinematics.rotations,before.channels[0].force):
        with pytest.raises(ValueError): a.flat[0]=0
        with pytest.raises(ValueError): a.setflags(write=True)
    with pytest.raises(AttributeError): p._body=b'{}'
    with pytest.raises(AttributeError): del p._body
    original=s.family_objects
    def change_caller(desc):
        u[:]=1.; qa[:]=0.
        with pytest.raises(RuntimeError): p.evaluate(u,qa)
        return original(desc)
    monkeypatch.setattr(s,'family_objects',change_caller)
    out=p.evaluate(u.copy(),qa.copy())
    equal(out.local_force,before.local_force)
    with pytest.raises(ValueError): s.channel('x',1,np.inf,np.zeros(2),np.eye(2))
    with pytest.raises(ValueError): s.equal(np.full(2,1e308),np.full(2,1e308),'overflow')
    with pytest.raises(ValueError): s.canonical(dict(x=float('nan')))
    for kw in ({'normal':np.zeros(3)}, {'material_direction':np.array([0.,0.,1.])}, {'director_polarity':True}):
        args=dict(family='S3-V2D',node_ids=(101,102,103),coordinates=np.array(p.descriptor()['coordinates']),
                  normal=np.array([0.,0.,1.]),material_direction=np.array([1.,0.,0.]))
        args.update(kw)
        with pytest.raises(ValueError): s.LocalShell(**args)
