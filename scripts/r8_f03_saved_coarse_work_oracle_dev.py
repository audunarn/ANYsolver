"""SMALL saved binary64 stationary-work oracle; never an owner or F03 gate.

Dense arrays are confined to <=625 physical/585 kernel coordinates. K remains
unsymmetrized. Only the derived stationary WORK action is symmetrized explicitly.
All numerical bounds below concern stored inputs, not assembly/continuum error.
"""
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from scipy import linalg,sparse

U=2.**-53
TINY=float(np.nextafter(0.,1.))
MAX_BYTES=100*1024**2

class Refused(ValueError):pass
class Unresolved(RuntimeError):pass

def require(ok,message):
    if not ok:raise Refused(message)

def up(value):
    value=float(value)
    if not math.isfinite(value) or value<0:raise Unresolved('nonfinite/negative bound')
    result=float(np.nextafter(value,math.inf))
    if not math.isfinite(result):raise Unresolved('unrepresentable bound')
    return result

def add(*values):return up(math.fsum(values))
def mul(a,b):return up(float(a)*float(b))
def sub_lower(a,b):
    value=float(np.nextafter(float(a)-float(b),-math.inf))
    if value<=0:raise Unresolved('nonpositive lower denominator')
    return value
def div(a,b):
    if b<=0:raise Unresolved('nonpositive bound denominator')
    return up(float(a)/float(b))
def gamma(n):
    require(type(n) is int and n>=0,'integer operation count required')
    return div(n*U,sub_lower(1,n*U))

def array_add_upper(a,b):
    value=np.nextafter(np.asarray(a)+np.asarray(b),math.inf)
    if not np.isfinite(value).all() or np.any(value<0):raise Unresolved('unrepresentable nonnegative array bound')
    return value

def array_mul_upper(a,b):
    value=np.nextafter(np.asarray(a)*np.asarray(b),math.inf)
    if not np.isfinite(value).all() or np.any(value<0):raise Unresolved('unrepresentable nonnegative array bound')
    return value

def array_div_upper(a,b):
    if np.any(np.asarray(b)<=0):raise Unresolved('nonpositive array bound denominator')
    value=np.nextafter(np.asarray(a)/np.asarray(b),math.inf)
    if not np.isfinite(value).all() or np.any(value<0):raise Unresolved('unrepresentable nonnegative array bound')
    return value

def multiplication_error(value):
    return array_add_upper(array_mul_upper(gamma(1),np.abs(value)),TINY)

def norm_f(a):
    """Upper Frobenius norm, scaled to avoid squares under/overflow."""
    a=np.asarray(a);require(np.isfinite(a).all(),'nonfinite array')
    m=float(np.max(np.abs(a),initial=0.))
    if m==0:return 0.
    scaled=np.ravel(a/m)
    # Division/square errors <=gamma(3); fsum is correctly rounded.
    squares=math.fsum(float(x)*float(x) for x in scaled)
    return mul(m,up(math.sqrt(div(add(up(squares),mul(4*a.size,TINY)),sub_lower(1,gamma(3))))))

def norm_inf(a):
    return max((up(math.fsum(map(float,row))) for row in np.abs(a)),default=0.)

def mm(a,b):
    """Computed product + upper Frobenius error vs exact stored-input product.

    Standard gamma(2n) dot bound, including gradual-underflow absolute term.
    No LU/BLAS pivot or tiny observed residual is treated as an error bound.
    """
    a=np.asarray(a);b=np.asarray(b)
    value=a@b;absolute=np.abs(a)@np.abs(b)
    require(np.isfinite(value).all() and np.isfinite(absolute).all(),'nonrepresentable product')
    n=a.shape[1];g=gamma(2*n+2)
    under=mul(2*n+2,TINY)
    exact_absolute_upper=array_div_upper(array_add_upper(absolute,under),sub_lower(1,g))
    bound=array_add_upper(array_mul_upper(g,exact_absolute_upper),under)
    return value,norm_f(bound)

def plus(a,b):
    value=a+b
    require(np.isfinite(value).all(),'nonrepresentable sum')
    absolute=array_add_upper(np.abs(a),np.abs(b))
    return value,norm_f(array_add_upper(array_mul_upper(gamma(1),absolute),TINY))

def congruence(a,g):
    first=g[:,None]*a;value=first*g[None,:]
    require(np.isfinite(value).all(),'nonrepresentable congruence')
    first_error=multiplication_error(first)
    err=norm_f(array_add_upper(array_mul_upper(first_error,np.abs(g[None,:])),multiplication_error(value)))
    return value,err

def eigen_bound(a):
    """Complete eigenbasis residual bound, including nonorthogonality.

    B=V diag(w) V^-1 + E V^-1. Bauer-Fike gives radius
    ||E||2 sqrt(1+eta)/(1-eta), eta>=||V^TV-I||2.
    B is actually stored symmetric. Lower: Bauer-Fike bounds all its eigenvalues.
    Upper: the first-column Hermitian Rayleigh residual gives lambda_min(B)
    <=w_min+||E_min||/||v_min||, with ||v_min||>=sqrt(1-eta). The returned
    global radius also dominates that bound, so both interval ends are justified.
    """
    require(np.array_equal(a,a.T),'eigen oracle requires stored symmetric work matrix')
    w,v=linalg.eigh(a,driver='evd')
    require(np.isfinite(w).all() and np.isfinite(v).all(),'nonfinite eigensystem')
    av,eav=mm(a,v);vd=v*w[None,:]
    evd=norm_f(multiplication_error(vd))
    residual,esub=plus(av,-vd)
    gram,eg=mm(v.T,v);gram_minus,egsub=plus(gram,-np.eye(len(w)))
    eta=add(norm_f(gram_minus),eg,egsub)
    if eta>=1:raise Unresolved('eigenvector rank/orthogonality unresolved')
    error=add(norm_f(residual),eav,evd,esub)
    radius=mul(error,div(up(math.sqrt(add(1,eta))),sub_lower(1,eta)))
    return dict(minimum=float(w[0]),maximum=float(w[-1]),radius=radius,orthogonality_upper=eta),v[:,0].copy()

def analyze(k,c,free,fixed,blocks):
    """Own inputs and assess every direction of this bounded stationary kernel."""
    require(sparse.issparse(k) and sparse.issparse(c),'sparse original K/C required')
    k=k.tocsr(copy=True);c=c.tocsr(copy=True)
    free=np.array(free,copy=True);fixed=np.array(fixed,copy=True)
    blocks=tuple(tuple(b) for b in blocks)
    require(k.dtype==c.dtype==np.dtype('float64'),'binary64 input required')
    require(k.shape[0]==k.shape[1] and c.shape[1]==k.shape[0],'operator shape mismatch')
    require(np.isfinite(k.data).all() and np.isfinite(c.data).all(),'nonfinite input')
    require(free.dtype.kind in 'iu' and fixed.dtype.kind in 'iu','integer support inventory required')
    require(sorted(map(int,np.r_[free,fixed]))==list(range(k.shape[0])),'support coverage mismatch')
    p=np.array([i for b in blocks for i in b],dtype=int)
    require(len(set(map(int,p)))==len(p) and set(map(int,p))<=set(map(int,free)),'resultant inventory mismatch')
    x=np.setdiff1d(free,p);n=len(x);m=c.shape[0];d=n-m
    require(0<m<n<=625 and 0<d<=585,'SMALL oracle dimension exceeded; no escalation')
    # Peak live matrices, absolute products, eig/QR copies/workspace: <=30 n²
    # binary64 arrays +8 m*n arrays, including result buffers. No global inverse.
    dense_bytes=30*n*n*8+8*m*n*8
    require(dense_bytes<MAX_BYTES,'declared dense working storage exceeds100MiB')
    require(c[:,p].nnz==0,'constraint includes independent stress resultants')
    local=[];s=k[x][:,x].toarray()
    for b in blocks:
        b=np.array(b);require(0<len(b)<=18,'local block limit18')
        other=np.setdiff1d(p,b);require(k[b][:,other].nnz==0,'coupled resultant blocks')
        e=-k[b][:,b].toarray();require(np.array_equal(e,e.T),'local exact symmetry unproved')
        eb,_=eigen_bound(e)
        if eb['minimum']<=eb['radius']:raise Unresolved('local negative-block proof unresolved')
        h=linalg.solve(e,np.eye(len(b)),assume_a='pos')
        eh,eeh=mm(e,h);r,er=plus(np.eye(len(b)),-eh)
        rho=add(norm_inf(r),mul(up(math.sqrt(len(b))),add(eeh,er)))
        if rho>=1:raise Unresolved('local inverse residual bound unresolved')
        hinf=norm_inf(h);herr=mul(up(math.sqrt(len(b))),div(mul(hinf,rho),sub_lower(1,rho)))
        left=k[x][:,b].toarray();right=k[b][:,x].toarray()
        lh,el=mm(left,h);update,eu=mm(lh,right);s,_=plus(s,update)
        local.append((left,right,h,herr,dict(size=len(b),negative_eigen=eb,inverse_residual_upper=rho,inverse_error_2_upper=herr)))
    diagonal=np.abs(np.diag(s))
    require(np.all(diagonal>0),'zero/nonfinite stationary diagonal; congruence undefined')
    g=1/np.sqrt(diagonal)
    require(np.isfinite(g).all() and np.all(g>0),'noninvertible congruence')
    # Re-form in the declared fixed binary64 congruence; prior s only chooses G.
    sg,formation=congruence(k[x][:,x].toarray(),g)
    local_evidence=[]
    for left,right,h,herr,ev in local:
        lg=g[:,None]*left;rg=right*g[None,:]
        elg=norm_f(multiplication_error(lg))
        erg=norm_f(multiplication_error(rg))
        lh,elh=mm(lg,h);update,eup=mm(lh,rg)
        local_bound=add(mul(norm_f(lg),mul(herr,norm_f(rg))),
            mul(elh,norm_f(rg)),eup,
            mul(elg,mul(add(norm_f(h),herr),add(norm_f(rg),erg))),
            mul(norm_f(lg),mul(add(norm_f(h),herr),erg)))
        sg,eadd=plus(sg,update);formation=add(formation,local_bound,eadd)
        ev['scaled_formation_error_upper']=local_bound;local_evidence.append(ev)
    total,esym=plus(sg,sg.T);work=total*.5
    # division by2 exact except possible subnormal underflow
    formation=add(formation,mul(esym,.5),mul(TINY,n))
    require(np.array_equal(work,work.T),'stored work symmetrization failed')
    cx=c[:,x].toarray();cg=cx*g[None,:]
    ecg=norm_f(multiplication_error(cg))
    qfull,r=linalg.qr(cg.T,mode='full');q=qfull[:,m:].copy()
    # Right inverse is local constraint40×40 plus bounded625×40, not model inverse.
    r0=linalg.solve_triangular(r[:m,:m],qfull[:,:m].T,lower=False).T
    cr,ecr=mm(cg,r0);diff,ediff=plus(np.eye(m),-cr)
    rhoc=add(norm_f(diff),ecr,ediff,mul(ecg,norm_f(r0)))
    if rhoc>=1:raise Unresolved('constraint right-inverse bound unresolved')
    leakage,el=mm(cg,q);leak=add(norm_f(leakage),el,mul(ecg,norm_f(q)))
    delta=div(mul(norm_f(r0),leak),sub_lower(1,rhoc))
    qtq,eq=mm(q.T,q);diff,ed=plus(qtq,-np.eye(d));etaq=add(norm_f(diff),eq,ed)
    if etaq>=1 or np.nextafter(math.sqrt(sub_lower(1,etaq)),-math.inf)<=delta:raise Unresolved('exact-kernel basis rank unresolved')
    qnorm=up(math.sqrt(add(1,etaq)));wnorm=add(norm_f(work),formation)
    basis_error=mul(wnorm,add(mul(mul(2,qnorm),delta),mul(delta,delta)))
    wq,ewq=mm(work,q);b,eb=mm(q.T,wq)
    bs,eadd=plus(b,b.T);bwork=bs*.5
    projection_error=add(mul(qnorm,ewq),eb,mul(eadd,.5),mul(TINY,d))
    combined=add(mul(mul(qnorm,qnorm),formation),basis_error,projection_error)
    spectral,vector=eigen_bound(bwork)
    uncertainty=add(combined,spectral['radius'])
    lower=float(np.nextafter(spectral['minimum']-uncertainty,-math.inf))
    upper=float(np.nextafter(spectral['minimum']+uncertainty,math.inf))
    status='POSITIVE_STORED_COARSE_MECHANICAL_WORK' if lower>0 else ('NEGATIVE_STORED_COARSE_MECHANICAL_WORK' if upper<0 else 'UNRESOLVED')
    # Equivalent coefficient in original x-array Euclidean norm, not a new metric.
    original_denominator=mul(mul(max(g),max(g)),mul(add(qnorm,delta),add(qnorm,delta)))
    original_lower=float(np.nextafter(lower/original_denominator,-math.inf)) if lower>0 else None
    return dict(status=status,qualification=False,full_kernel_directions=d,physical_coordinates=n,constraints=m,
        declared_dense_working_bytes=dense_bytes,local_blocks=local_evidence,
        formation_error_upper=formation,constraint_right_inverse_residual_upper=rhoc,
        constraint_leakage_upper=leak,exact_basis_distance_upper=delta,basis_orthogonality_upper=etaq,
        basis_work_error_upper=basis_error,projection_arithmetic_error_upper=projection_error,
        eigensystem=spectral,combined_uncertainty=uncertainty,minimum_lower=lower,minimum_upper=upper,
        original_array_norm_lower=original_lower,congruence_min=float(min(g)),congruence_max=float(max(g)),
        operator_scope='stationary symmetric WORK of original stored unsymmetrized K; no full-K inertia',
        continuum_formation_error='NOT_ASSESSED',growing_family='OPEN',
        blocker=None if status!='UNRESOLVED' else 'all-direction sign margin does not exceed combined uncertainty')

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load_saved(manifest):
    """Strict saved current16 identity; never imports fixture/model/owner."""
    manifest=json.loads(Path(manifest).read_text(encoding='utf-8-sig'))
    require(manifest['family']==[16,4,16,2] and manifest['endpoint_node']==117,'only saved current16 admitted')
    directory=Path(manifest['saved_directory']).resolve()
    names=('K.npz','C.npz','compiled-layout.npz','states.npz','inputs.json','result.json')
    expected={str((directory/n).resolve()) for n in names}
    require(set(manifest['saved_inputs'])==expected,'exact complete saved-file binding required')
    require(all(Path(p).resolve().parent==directory for p in manifest['saved_inputs']),'escaped saved-file binding')
    for p,h in manifest['saved_inputs'].items():require(sha(p)==h,'saved input mutation: '+p)
    record=json.loads((directory/'result.json').read_text())
    require(record['family']==[16,4,16,2] and record['endpoint_node']==117 and record['status']=='UNRESOLVED_KERNEL','saved actual disposition mismatch')
    require(record['operator_identity']['actual_multiplier_space']=='BL5_P0_span_2','actual basis mismatch')
    k=sparse.load_npz(directory/'K.npz');c=sparse.load_npz(directory/'C.npz')
    def matrix_sha(a):
        a=a.tocsr(copy=True)
        return hashlib.sha256(str((a.shape,str(a.dtype))).encode()+a.indptr.tobytes()+a.indices.tobytes()+a.data.tobytes()).hexdigest()
    require(matrix_sha(k)==record['operator_identity']['k_sha256'] and matrix_sha(c)==record['operator_identity']['c_sha256'],'canonical saved operator identity mismatch')
    require(k.shape==(804,804) and c.shape==(40,804),'actual coarse shape mismatch')
    with np.load(directory/'compiled-layout.npz',allow_pickle=False) as layout:
        free=layout['free'].copy();fixed=layout['fixed'].copy();p=layout['resultants'].copy()
        for name in ('shell','beam_nodes','retained_rotations','resultants'):
            require(np.array_equal(layout[name],record['roles'][name]),'role inventory mismatch')
        require(len(p)==144,'eight18-coordinate resultant blocks required')
    return manifest,k,c,free,fixed,tuple(tuple(map(int,p[i:i+18])) for i in range(0,144,18))

def run_saved(manifest,output):
    """One saved operator evaluation, fail-preserving result; no physical solve."""
    output=Path(output);output.mkdir(exist_ok=False);result=dict(status='FAILED',qualification=False)
    try:
        bound,k,c,free,fixed,blocks=load_saved(manifest)
        result=analyze(k,c,free,fixed,blocks)
        result['input_manifest']=bound
        return result
    except (Refused,Unresolved) as exc:
        result.update(status='UNRESOLVED',blocker=str(exc),exception=repr(exc));return result
    finally:(output/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
