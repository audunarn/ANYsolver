"""Narrow sparse saved-family stationary WORK bound, not a product solver.

Only auxiliary quadratic work is symmetric. Native K, state, supports and C are
never replaced. Dense materialization is restricted to local18/24 blocks.
The fixed coefficient-one constraint Gram vanishes on the original kernel.
"""
import json
import math
from pathlib import Path
import numpy as np
from scipy import sparse,linalg
from scipy.sparse.linalg import splu
from scipy.sparse.csgraph import reverse_cuthill_mckee
from scripts.r8_f03_saved_coarse_work_oracle_dev import (
    Refused,Unresolved,require,up,add,mul,div,sub_lower,gamma,norm_f,norm_inf,
    multiplication_error,array_add_upper,array_mul_upper,mm,plus,eigen_bound,load_saved)

STORAGE_CAP=128*1024**2
PRODUCT_TERM_CAP=8_000_000

def finite(a):require(np.isfinite(a.data).all(),'nonfinite sparse arithmetic')
def canonical(a):
    require(sparse.issparse(a) and a.has_canonical_format,'canonical sparse input required; duplicates/unsorted inputs refused')
    require(a.dtype==np.dtype('float64'),'binary64 sparse arithmetic required')
def fnorm(a):return norm_f(a.data)
def sparse_bytes(a):return a.data.nbytes+a.indices.nbytes+a.indptr.nbytes

def add_error(a,b):
    # Canonical sparse addition performs one addition for each shared entry.
    # gamma(2) also covers rounding the nonnegative absolute sparse sum:
    # u/(1-u)^2 < gamma(2), plus an absolute underflow term.
    canonical(a);canonical(b)
    require(a.shape==b.shape and a.shape[0]==a.shape[1],'square sparse addition bound required')
    # sqrt(number of output entries)<=rows for this explicitly square seam.
    absolute=abs(a)+abs(b);finite(absolute)
    return add(mul(gamma(2),fnorm(absolute)),mul(TINY,a.shape[0]))

TINY=float(np.nextafter(0.,1.))

def guarded_product(a,b):
    """Sparse product and Frobenius roundoff bound; forecast before multiplication."""
    canonical(a);canonical(b);a=a.tocsr();b=b.tocsr()
    counts=np.diff(b.indptr)
    visits=sum(int(counts[j]) for j in a.indices)
    require(visits<=PRODUCT_TERM_CAP,'sparse product term/storage eligibility exceeded')
    forecast=min(a.shape[0]*b.shape[1],visits)
    # Result+absolute product+two factor copies+one residual, canonical CSR.
    required=3*(16*forecast+8*(a.shape[0]+1))+2*(sparse_bytes(a)+sparse_bytes(b))
    require(required<=STORAGE_CAP,'sparse intermediate forecast exceeds128MiB')
    value=(a@b).tocsr();absolute=(abs(a)@abs(b)).tocsr()
    # Sparse multiplication already accumulates each output entry; sorting its
    # internal index order is exact, unlike summing duplicate caller inputs.
    value.sort_indices();absolute.sort_indices()
    finite(value);finite(absolute)
    require(sparse_bytes(value)+sparse_bytes(absolute)<=STORAGE_CAP,'actual sparse product storage exceeded')
    n=a.shape[1];g=gamma(2*n+2);floor=mul(2*n+2,TINY)
    # Exact absolute product includes gradual-underflow error in its own dot sums.
    size_upper=up(math.sqrt(a.shape[0]*b.shape[1]))
    absnorm=div(add(fnorm(absolute),mul(size_upper,floor)),sub_lower(1,g))
    error=add(mul(g,absnorm),mul(size_upper,floor))
    return value,error,dict(term_visits=visits,forecast_nnz=forecast,actual_nnz=value.nnz,forecast_bytes=required)

def sym_work(a):
    total=a+a.T;finite(total);value=(total*.5).tocsr()
    error=add(mul(add_error(a,a.T),.5),mul(TINY,a.shape[0]))
    return value,error

def scale(a,row,col):
    canonical(a)
    co=a.tocoo();first=co.data*np.asarray(row)[co.row];value=first*np.asarray(col)[co.col]
    require(np.isfinite(value).all(),'nonrepresentable sparse scaling')
    bound=array_add_upper(array_mul_upper(multiplication_error(first),np.abs(np.asarray(col)[co.col])),multiplication_error(value))
    result=sparse.coo_matrix((value,(co.row,co.col)),shape=a.shape).tocsr()
    return result,norm_f(bound)

def inverse_factor_bounds(l,diagonal):
    """Outward absolute triangular recurrences; no inverse entries are formed.

    T=D^-1/2 L^-1: row and column sums bound ||T||inf and ||T||1.
    Then lambda_min(L D L^T)>=1/(||T||inf*||T||1).
    Absolute recurrences may be conservative; their failure is not instability.
    """
    canonical(l);l=l.tocsr();n=l.shape[0]
    require(l.shape==(n,n) and len(diagonal)==n,'factor dimensions mismatch')
    require(np.isfinite(diagonal).all() and np.all(diagonal>0),'candidate diagonal not strictly positive')
    require(sparse.triu(l,1).nnz==0 and np.array_equal(l.diagonal(),np.ones(n)),'unit lower factor required')
    row=np.zeros(n)
    for i in range(n):
        begin,end=l.indptr[i:i+2];terms=[mul(abs(float(v)),row[int(j)]) for j,v in zip(l.indices[begin:end],l.data[begin:end]) if j<i]
        row[i]=add(1.,*terms)
    # sqrt lower ⇒ reciprocal upper; stored D is the exact candidate diagonal.
    weights=np.array([div(1.,float(np.nextafter(math.sqrt(float(v)),-math.inf))) for v in diagonal])
    tinf=max(mul(float(w),float(v)) for w,v in zip(weights,row))
    lt=l.T.tocsr();column=np.zeros(n)
    for i in reversed(range(n)):
        begin,end=lt.indptr[i:i+2];terms=[mul(abs(float(v)),column[int(j)]) for j,v in zip(lt.indices[begin:end],lt.data[begin:end]) if j>i]
        column[i]=add(float(weights[i]),*terms)
    tone=float(max(column));inverse_norm2_squared=mul(tinf,tone)
    margin=float(np.nextafter(1./inverse_norm2_squared,-math.inf))
    return dict(triangular_inverse_infinity_upper=tinf,triangular_inverse_one_upper=tone,
        inverse_norm2_squared_upper=inverse_norm2_squared,candidate_minimum_lower=margin)

def factor_certificate(h,formation_error,*,factor_factory=splu,ordering=None):
    """Certify exact positive Gram surrogate only against complete true-work error."""
    require(math.isfinite(float(formation_error)) and formation_error>=0,'finite nonnegative formation error required')
    canonical(h);h=h.tocsc(copy=True);finite(h)
    difference=h-h.T;difference.eliminate_zeros()
    require(difference.nnz==0,'auxiliary stored work must be symmetric')
    require(sparse_bytes(h)<=STORAGE_CAP,'factor input storage exceeded')
    n=h.shape[0]
    order=np.asarray(reverse_cuthill_mckee(h,symmetric_mode=True) if ordering is None else ordering)
    require(order.dtype.kind in 'iu' and sorted(map(int,order))==list(range(n)),'symmetric ordering must be a permutation')
    h=h[order][:,order].tocsc();h.sort_indices();h.eliminate_zeros()
    co=h.tocoo();band=int(max(np.abs(co.row-co.col),default=0))
    # Threshold0 prefers nonzero diagonal but can force row exchanges at zero.
    # Before factorization use general triangular n²+n storage, independent of
    # pivoting. Band forecast is informational ONLY, not large-model admission.
    band_slots=2*n*(band+1)
    factor_slots=n*(n+1)
    worst_factor_bytes=16*factor_slots+16*(n+1)+sparse_bytes(h)
    require(worst_factor_bytes<=STORAGE_CAP,'worst-case factor storage exceeds128MiB; scaling eligibility unresolved')
    try:factor=factor_factory(h,permc_spec='NATURAL',diag_pivot_thresh=0.,options={'SymmetricMode':True,'Equil':False})
    except RuntimeError as exc:raise Unresolved('sparse candidate factorization failed') from exc
    pr=np.asarray(factor.perm_r);pc=np.asarray(factor.perm_c)
    if not np.array_equal(pr,pc):raise Unresolved('factor row/column permutations differ')
    require(sorted(map(int,pr))==list(range(h.shape[0])),'factor permutation invalid')
    l=factor.L.tocsr();u=factor.U.tocsr();finite(l);finite(u)
    canonical(l);canonical(u)
    require(sparse_bytes(l)+sparse_bytes(u)<=STORAGE_CAP,'factor fill exceeds128MiB')
    require(l.nnz+u.nnz<=factor_slots,'unexpected factor fill exceeds triangular forecast')
    diagonal=u.diagonal()
    if not np.all(diagonal>0):raise Unresolved('positive surrogate diagonal unavailable (min='+str(float(min(diagonal)))+'); constraints may remove bad motions')
    try:bounds=inverse_factor_bounds(l,diagonal)
    except Unresolved as exc:raise Unresolved('absolute triangular inverse bound unresolved: '+str(exc)) from exc
    # Actual SuperLU permutations map original indices to factor coordinates.
    permutation=np.argsort(pr);hp=h[permutation][:,permutation].tocsr();hp.sort_indices()
    ld=l.multiply(diagonal[None,:]).tocsr();finite(ld)
    ld_error=norm_f(multiplication_error(ld.data))
    gram,gram_error,cost=guarded_product(ld,l.T)
    reconstruction=(hp-gram).tocsr();finite(reconstruction)
    # Exact L D L^T differs from computed Gram by scaling/product arithmetic.
    gram_total=add(gram_error,mul(ld_error,fnorm(l)))
    residual_upper=add(fnorm(reconstruction),add_error(hp,-gram),gram_total)
    total_error=add(float(formation_error),residual_upper)
    margin=bounds['candidate_minimum_lower']
    lower=float(np.nextafter(margin-total_error,-math.inf))
    candidate_du=sparse.diags(diagonal)@l.T
    mismatch=(u-candidate_du).tocsr()
    return dict(status='POSITIVE_STORED_CONSTRAINED_WORK' if lower>0 else 'UNRESOLVED',qualification=False,
        stronger_auxiliary_lower=lower,positive_surrogate_lower=margin,total_error_upper=total_error,
        factor_reconstruction_error_upper=residual_upper,formation_error_upper=float(formation_error),
        u_minus_d_lt_frobenius=fnorm(mismatch),factor_nnz=dict(L=l.nnz,U=u.nnz),factor_product=cost,
        permutation_equal=True,inverse_bounds=bounds,worst_factor_storage_bytes=worst_factor_bytes,
        symmetric_ordering='RCM' if ordering is None else 'explicit fixed permutation',bandwidth=band,factor_slot_upper=factor_slots,
        band_factor_slots_informational=band_slots,larger_family_eligibility='UNRESOLVED_NOT_AUTHORIZED',
        blocker=None if lower>0 else 'sparse absolute triangular inverse bound times complete error does not prove sign',
        full_native_inertia=None,physical_defect=False)

def prepare(k,c,free,fixed,blocks,*,augment=True):
    """Local sparse stationary work plus fixed coefficient-one constraint Gram."""
    require(sparse.issparse(k) and sparse.issparse(c),'original sparse K/C required')
    require(k.has_canonical_format and c.has_canonical_format,'canonical original sparse inputs required')
    require(sparse_bytes(k)+sparse_bytes(c)<=STORAGE_CAP,'input sparse storage exceeds128MiB')
    k=k.tocsr(copy=True);c=c.tocsr(copy=True);free=np.array(free,copy=True);fixed=np.array(fixed,copy=True)
    require(k.dtype==c.dtype==np.dtype('float64'),'binary64 inputs required')
    finite(k);finite(c)
    require(free.dtype.kind in 'iu' and fixed.dtype.kind in 'iu','integer support/free inventory required')
    require(k.shape[0]==k.shape[1] and c.shape[1]==k.shape[0],'K/C dimensions mismatch')
    require(sorted(map(int,np.r_[free,fixed]))==list(range(k.shape[0])),'support coverage mismatch')
    p=np.array([v for b in blocks for v in b],dtype=int);x=np.setdiff1d(free,p)
    require(len(set(map(int,p)))==len(p) and set(map(int,p))<=set(map(int,free)),'resultant ownership mismatch')
    require(c[:,p].nnz==0,'constraints contain stress resultants')
    a=k[x][:,x].tocsr();pre=a.copy();local=[]
    for block in blocks:
        block=np.array(block);require(0<len(block)<=18,'local resultant limit18')
        require(k[block][:,np.setdiff1d(p,block)].nnz==0,'resultant blocks coupled')
        e=-k[block][:,block].toarray();require(np.array_equal(e,e.T),'local exact symmetry unresolved')
        ev,_=eigen_bound(e)
        if ev['minimum']<=ev['radius']:raise Unresolved('negative local resultant block unresolved')
        try:inv=linalg.solve(e,np.eye(len(block)),assume_a='pos')
        except linalg.LinAlgError as exc:raise Unresolved('local inverse candidate failed') from exc
        eh,ee=mm(e,inv);r,er=plus(np.eye(len(block)),-eh)
        rho=add(norm_inf(r),mul(up(math.sqrt(len(block))),add(ee,er)))
        if rho>=1:raise Unresolved('local inverse residual bound unresolved')
        inv_error=mul(up(math.sqrt(len(block))),div(mul(norm_inf(inv),rho),sub_lower(1,rho)))
        b=k[x][:,block].tocsr();f=k[block][:,x].tocsr()
        neighbours=np.union1d(b.nonzero()[0],f.nonzero()[1]);require(len(neighbours)<=24,'native local coupling closure exceeds24')
        bd=b[neighbours].toarray();fd=f[:,neighbours].toarray()
        bh,_=mm(bd,inv);update,_=mm(bh,fd)
        sp=sparse.coo_matrix((update.ravel(),(np.repeat(neighbours,len(neighbours)),np.tile(neighbours,len(neighbours)))),shape=a.shape).tocsr()
        pre=pre+sp;finite(pre)
        require(sparse_bytes(pre)<=STORAGE_CAP,'stationary intermediate storage exceeds128MiB')
        local.append((neighbours,bd,fd,inv,inv_error,ev,rho))
    diagonal=np.abs(pre.diagonal());require(np.all(diagonal>0),'nonzero stationary diagonal required')
    g=1/np.sqrt(diagonal);require(np.isfinite(g).all() and np.all(g>0),'finite invertible G required')
    formed,error=scale(a,g,g);local_info=[]
    for neighbours,b,f,inv,inv_error,ev,rho in local:
        gn=g[neighbours];bg=gn[:,None]*b;fg=f*gn[None,:]
        eb=norm_f(multiplication_error(bg));ef=norm_f(multiplication_error(fg))
        bi,ebi=mm(bg,inv);update,eu=mm(bi,fg)
        local_error=add(mul(norm_f(bg),mul(inv_error,norm_f(fg))),mul(ebi,norm_f(fg)),eu,
            mul(eb,mul(add(norm_f(inv),inv_error),add(norm_f(fg),ef))),mul(norm_f(bg),mul(add(norm_f(inv),inv_error),ef)))
        sp=sparse.coo_matrix((update.ravel(),(np.repeat(neighbours,len(neighbours)),np.tile(neighbours,len(neighbours)))),shape=a.shape).tocsr()
        error=add(error,local_error,add_error(formed,sp));formed=formed+sp;finite(formed)
        require(sparse_bytes(formed)<=STORAGE_CAP,'scaled stationary storage exceeds128MiB')
        local_info.append(dict(negative_eigen=ev,inverse_residual_upper=rho,formation_error_upper=local_error))
    work,esym=sym_work(formed);error=add(error,esym)
    record=dict(physical_coordinates=len(x),local_blocks=local_info,stationary_formation_error_upper=error,
        congruence_min=float(min(g)),congruence_max=float(max(g)),constraint_gram_coefficient=1 if augment else 0)
    if augment:
        cg,ecg=scale(c[:,x],np.ones(c.shape[0]),g)
        row=np.array([1./fnorm(cg[i]) if cg[i].nnz else 0. for i in range(c.shape[0])])
        require(np.isfinite(row).all() and np.all(row>0),'nonzero finite row normalization required')
        rcg,ercg=scale(cg,row,np.ones(len(x)))
        input_error=add(mul(float(max(row)),ecg),ercg)
        gram,eg,cost=guarded_product(rcg.T,rcg)
        gram_error=add(eg,mul(mul(2,fnorm(rcg)),input_error),mul(input_error,input_error))
        gram,egs=sym_work(gram);gram_error=add(gram_error,egs)
        error=add(error,gram_error,add_error(work,gram));work=work+gram
        # Sum of stored symmetric matrices is exactly stored symmetric.
        record.update(constraint_gram_error_upper=gram_error,constraint_gram_product=cost,
            row_congruence_min=float(min(row)),row_congruence_max=float(max(row)))
    return work,error,record

def analyze(k,c,free,fixed,blocks,*,augment=True,factor_factory=splu):
    info=dict(status='UNRESOLVED',qualification=False,physical_defect=False,full_native_inertia=None)
    try:
        h,error,record=prepare(k,c,free,fixed,blocks,augment=augment)
        info.update(record);info['formation_error_upper']=error
        info.update(factor_certificate(h,error,factor_factory=factor_factory))
    except (Refused,Unresolved) as exc:info.update(blocker=str(exc),exception=repr(exc))
    return info

def run_saved(manifest,output):
    output=Path(output);output.mkdir(exist_ok=False);result=dict(status='FAILED',qualification=False)
    try:
        binding,k,c,free,fixed,blocks=load_saved(manifest)
        control=binding['coarse_control'];control_path=Path(control['path'])
        from scripts.r8_f03_saved_coarse_work_oracle_dev import sha
        require(sha(control_path)==control['sha256'],'stored coarse control mutated')
        baseline=json.loads(control_path.read_text(encoding='utf-8'))
        require(baseline['status']=='POSITIVE_STORED_COARSE_MECHANICAL_WORK' and baseline['minimum_lower']>0,'positive coarse control unavailable')
        result=analyze(k,c,free,fixed,blocks)
        result.update(input_manifest=binding,scope='coefficient-one auxiliary stationary work; constrained positivity sufficient only',
            continuum_error='NOT_ASSESSED',growing_family='OPEN',coarse_control_minimum_lower=baseline['minimum_lower'],
            comparison='same stored coarse K/C; sparse sufficient bound may remain unresolved despite bounded dense positivity')
        return result
    except BaseException as exc:
        import traceback
        result.update(exception=repr(exc),traceback=traceback.format_exc())
        raise
    finally:(output/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
