"""Cancellation-aware bounded triangular comparison candidate, DEVELOPMENT ONLY.

No numerical imports, source assessment, new ordering/J/kappa, global inverse,
or inertia claim. Exact local inverses have order<=18; global storage is sparse.
The caller must separately bind a certified residual RHS to the unchanged LU.
"""
from dataclasses import dataclass
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
from scripts.r8_f03_finite_local_dev import ExactBudget,Unresolved,identity,solve
from scripts.r8_f03_finite_sparse_dev import Caps as OutwardCaps,directed,normal

CAPS={'dimension':8000,'input_fill':1_000_000,'block_order':18,'operations':30_000_000,
      'bits':4096,'block_row_fill':144_000,'metadata_bytes':32_000_000}


@dataclass(frozen=True)
class Band:
    lo:F
    hi:F


def exact_budget():
    return ExactBudget(operation_cap=CAPS['operations'],bit_cap=CAPS['bits'])


def require_budget(budget):
    if (type(budget)is not ExactBudget or type(budget.operation_cap)is not int or
            type(budget.bit_cap)is not int or not 0<budget.operation_cap<=CAPS['operations'] or
            not 0<budget.bit_cap<=CAPS['bits'] or type(budget.operations)is not int or
            not 0<=budget.operations<=budget.operation_cap):
        raise Unresolved('explicit bounded exact operation/bit budget required')
    return budget


def checked(band,budget):
    if type(band)is not Band or type(band.lo)is not F or type(band.hi)is not F:
        raise Unresolved('exact rational interval storage required')
    budget.check(band.lo);budget.check(band.hi)
    if band.lo>band.hi:raise Unresolved('reversed exact factor interval')
    return band


def center_radius(band,budget):
    return budget.check((band.lo+band.hi)/2),budget.check((band.hi-band.lo)/2)


def point(value):
    if type(value)is not F:raise Unresolved('explicit exact rational factor point required')
    return Band(value,value)


def binary64_point(value):
    if type(value)is not float:raise Unresolved('actual binary64 factor storage required')
    return point(F(normal(value)))


def partition(n,width):
    if type(n)is not int or not 0<n<=CAPS['dimension']:
        raise Unresolved('block comparison dimension cap')
    if type(width)is not int or not 1<=width<=CAPS['block_order']:
        raise Unresolved('contiguous block order cap')
    return tuple((i,min(n,i+width)) for i in range(0,n,width))


def validate(entries,n,lower,budget):
    # All dimension/fill checks precede any dimension-sized allocation.
    partition(n,1)
    if type(lower)is not bool or type(entries)is not dict or len(entries)>CAPS['input_fill']:
        raise Unresolved('bounded sparse triangular factor required')
    for key,band in entries.items():
        if type(key)is not tuple or len(key)!=2 or any(type(i)is not int or not 0<=i<n for i in key):
            raise Unresolved('factor coordinate storage')
        checked(band,budget);i,j=key
        if ((lower and j>i) or (not lower and j<i)) and (band.lo or band.hi):
            raise Unresolved('signed factor triangular structure violation')
    for i in range(n):
        budget.check(F())
        if (i,i)not in entries:raise Unresolved('missing factor diagonal')


def product(a,b,budget,absolute_left=False):
    rows=len(a);inner=len(b);cols=len(b[0])
    out=[[F() for _ in range(cols)] for _ in range(rows)]
    for i in range(rows):
        for j in range(cols):
            total=F()
            for k in range(inner):
                value=abs(a[i][k]) if absolute_left else a[i][k]
                total=budget.check(total+budget.check(value*b[k][j]))
            out[i][j]=total
    return out


def local_inverse(center,radius,budget):
    """Exact center inverse W, Q=|W|R, beta<1 gives a uniform inverse box.

    For any RHS magnitude term g, |(D0+dD)^-1 rhs| is bounded by
    g + Q*1 * max(g)/(1-beta), where g bounds |W rhs|.
    """
    require_budget(budget)
    if type(center)not in (list,tuple):raise Unresolved('explicit bounded local block required')
    size=len(center)
    if not 1<=size<=CAPS['block_order']:raise Unresolved('local inverse order cap')
    for values in (center,radius):
        if type(values)not in (list,tuple) or len(values)!=size or any(type(row)not in (list,tuple) or len(row)!=size for row in values):
            raise Unresolved('bounded square local block required')
        for row in values:
            for value in row:
                if type(value)is not F:raise Unresolved('exact local block scalar required')
                budget.check(value)
    if any(value<0 for row in radius for value in row):raise Unresolved('negative local interval radius')
    w=solve(center,identity(size),budget,order_cap=CAPS['block_order'])
    q=product(w,radius,budget,absolute_left=True)
    sums=[]
    for row in q:
        total=F()
        for value in row:total=budget.check(total+value)
        sums.append(total)
    beta=max(sums)
    if beta>=1:raise Unresolved('interval-singular or unresolved diagonal block inverse')
    return w,sums,beta


def inflate(g,row_sums,beta,budget):
    cols=len(g[0]);maximum=[max(row[j] for row in g) for j in range(cols)]
    denominator=budget.check(1-beta)
    return [[budget.check(g[i][j]+budget.check(budget.check(row_sums[i]*maximum[j])/denominator))
             for j in range(cols)] for i in range(len(g))]


def block_triangular_bound(entries,rhs,*,lower,width=18,budget=None):
    """For EVERY admitted triangular factor T and |f|<=rhs, |T^-1 f|<=result.

    Preserves signed cancellation in D0^-1 E0 before bounding each block edge.
    No global inverse columns; one block row and bounded local blocks at a time.
    """
    if type(rhs)not in (tuple,list):raise Unresolved('explicit bounded residual vector required')
    budget=require_budget(budget or exact_budget());n=len(rhs);blocks=partition(n,width)
    validate(entries,n,lower,budget)
    if type(rhs)not in (tuple,list) or any(type(v)is not F or v<0 for v in rhs):
        raise Unresolved('nonnegative exact residual bound required')
    for value in rhs:budget.check(value)
    for _ in range(n):budget.check(F())
    rows=[{} for _ in range(n)]
    for (i,j),band in entries.items():rows[i][j]=band
    result=[F()]*n;diagnostics=[];maximum_row_fill=0
    order=range(len(blocks)) if lower else range(len(blocks)-1,-1,-1)
    for block in order:
        first,last=blocks[block];size=last-first
        centers=[[F()]*size for _ in range(size)];radii=[[F()]*size for _ in range(size)]
        neighbors=set();row_fill=0
        for i in range(first,last):
            for j,band in rows[i].items():
                budget.check(F());row_fill+=1
                if row_fill>CAPS['block_row_fill']:raise Unresolved('sparse block row fill cap')
                if first<=j<last:centers[i-first][j-first],radii[i-first][j-first]=center_radius(band,budget)
                elif band.lo or band.hi:neighbors.add(j//width)
        maximum_row_fill=max(maximum_row_fill,row_fill)
        w,qs,beta=local_inverse(centers,radii,budget)
        g=product(w,[[v]for v in rhs[first:last]],budget,absolute_left=True)
        values=[row[0]for row in inflate(g,qs,beta,budget)]
        for other in sorted(neighbors):
            start,stop=blocks[other];cols=stop-start
            ec=[[F()]*cols for _ in range(size)];er=[[F()]*cols for _ in range(size)]
            for i in range(first,last):
                for j,band in rows[i].items():
                    budget.check(F())
                    if start<=j<stop:ec[i-first][j-start],er[i-first][j-start]=center_radius(band,budget)
            signed=product(w,ec,budget);uncertain=product(w,er,budget,absolute_left=True)
            magnitude=[[budget.check(abs(signed[i][j])+uncertain[i][j])for j in range(cols)]for i in range(size)]
            edge=inflate(magnitude,qs,beta,budget)
            for i in range(size):
                for j in range(cols):values[i]=budget.check(values[i]+budget.check(edge[i][j]*result[start+j]))
        result[first:last]=values
        diagnostics.append({'block':block,'coordinates':(first,last),'inverse_order':size,'diagonal_uncertainty_beta':beta,
                            'neighbor_blocks':len(neighbors)})
    return {'bound':result,'blocks':blocks,'diagnostics':diagnostics,'maximum_sparse_block_row_fill':maximum_row_fill,
            'operations_used':budget.operations,'method':'signed bounded local inverse/coupling then nonnegative block propagation'}


def permutation_maps(pr,pc,n,budget):
    require_budget(budget)
    partition(n,1)
    if type(pr)not in (tuple,list) or type(pc)not in (tuple,list) or len(pr)!=n or len(pc)!=n:
        raise Unresolved('complete fixed SuperLU permutation maps required')
    for values in (pr,pc):
        if any(type(v)is not int for v in values):raise Unresolved('integer permutation storage required')
        for _ in values:budget.check(F())
        if sorted(values)!=list(range(n)):raise Unresolved('invalid fixed SuperLU permutation')
    return tuple(pr),tuple(pc)


def permuted_residual_rhs(original,pr,pc,budget):
    """Pr[pr[j],j]=1; Pc[j,pc[j]]=1. Only Pr acts on original row sums."""
    pr,pc=permutation_maps(pr,pc,len(original),budget);out=[F()]*len(original)
    for i,value in enumerate(original):
        if type(value)is not F or value<0:raise Unresolved('exact original residual row magnitude required')
        out[pr[i]]=budget.check(value)
    return out


def lu_block_comparison(lower,upper,permuted_rhs,pr,pc,*,width=18,provenance,budget=None):
    """Bound-only candidate; residual must ALREADY enclose Pr A Pc-LU+uncertainty.

    This API provides no physics, target/inertia admission or qualification.
    A verified q<1 is sufficient only with the caller's complete residual proof.
    """
    if type(permuted_rhs)not in (tuple,list):raise Unresolved('explicit bounded residual vector required')
    budget=require_budget(budget or exact_budget());n=len(permuted_rhs);pr,pc=permutation_maps(pr,pc,n,budget)
    if type(provenance)is not dict or any(type(provenance.get(k))is not str or not provenance[k]
            for k in ('pencil_identity','factor_identity','residual_identity','residual_coordinates')):
        raise Unresolved('missing same-pencil/factor/residual provenance')
    if provenance['residual_coordinates']!='Pr A Pc':raise Unresolved('residual coordinate convention mismatch')
    lb=block_triangular_bound(lower,permuted_rhs,lower=True,width=width,budget=budget)
    ub=block_triangular_bound(upper,lb['bound'],lower=False,width=width,budget=budget)
    q=max(ub['bound']);caps=OutwardCaps(operations=CAPS['operations']-budget.operations,bits=CAPS['bits'])
    outward=directed(q,True,caps)
    return {'status':'BOUND_ONLY_Q_LT_ONE'if outward<1 else 'UNRESOLVED','q_exact':q,'q_upper':outward,
            'factor_coordinate_bound':ub['bound'],'original_coordinate_bound':[ub['bound'][pc[j]]for j in range(n)],
            'lower':lb,'upper':ub,'permutations':{'perm_r':pr,'perm_c':pc},'width':width,
            'operations_used':budget.operations+caps.used,'provenance':dict(provenance),
            'inertia':None,'coercivity':None,'physical_acceptance':None,'qualification':False}


def saved_candidate_inputs(folder,expected_hashes,budget=None):
    """Explicit caller operation; NOT called at import or by this preparation.

    Frozen original residual rows are already outward in factor coordinates.
    Require trusted hashes for the complete saved pencil/target binding, not
    just a plausible successful factor. No source reconstruction or assessment.
    """
    required={'assessment.json','sparse-factors.json','halfpoint-box.json','sparse-reference.json',
              'exact-targets.json','sparse-stored.json','binding.json'}
    if type(expected_hashes)is not dict or set(expected_hashes)!=required:
        raise Unresolved('complete trusted saved-pencil hash binding required')
    folder=Path(folder);data={};budget=require_budget(budget or exact_budget())
    if sum((folder/name).stat().st_size for name in required)>CAPS['metadata_bytes']:
        raise Unresolved('aggregate saved metadata byte cap before allocation')
    for name in sorted(required):
        path=folder/name
        if path.stat().st_size>CAPS['metadata_bytes']:raise Unresolved('saved metadata byte cap before allocation')
        raw=path.read_bytes()
        if len(raw)>CAPS['metadata_bytes']:raise Unresolved('saved metadata byte cap')
        if type(expected_hashes[name])is not str or hashlib.sha256(raw).hexdigest()!=expected_hashes[name]:
            raise Unresolved('saved source/pencil/factor identity mismatch')
        data[name]=json.loads(raw)
    a=data['assessment.json'];f=data['sparse-factors.json'];n=a['dimension'];partition(n,1)
    if f['shape']!=[n,n] or data['halfpoint-box.json']['dimension']!=n:
        raise Unresolved('saved fixed pencil/factor shape mismatch')
    def decode(records):
        if type(records)is not list or len(records)>CAPS['input_fill']:raise Unresolved('saved factor fill cap')
        entries={}
        for item in records:
            budget.check(F())
            if type(item)is not list or len(item)!=3:raise Unresolved('saved factor scalar record')
            i,j,s=item
            if type(i)is not int or type(j)is not int or not 0<=i<n or not 0<=j<n:
                raise Unresolved('saved bounded factor coordinates required')
            if type(s)is not str or len(s)>32:raise Unresolved('saved bounded explicit binary64 text required')
            key=(i,j)
            if key in entries:raise Unresolved('duplicate saved factor entry')
            try:value=float(s)
            except (ValueError,OverflowError)as error:raise Unresolved('invalid binary64 factor text')from error
            if str(value)!=s:raise Unresolved('saved scalar text is not canonical original binary64')
            entries[key]=binary64_point(value)
        return entries
    rhs=a['certificate']['residual_row_bound']
    if type(rhs)is not list or len(rhs)!=n or any(type(v)is not float or normal(v)<0 for v in rhs):
        raise Unresolved('saved outward nonnegative residual storage')
    provenance={'pencil_identity':expected_hashes['halfpoint-box.json'],'factor_identity':expected_hashes['sparse-factors.json'],
                'residual_identity':expected_hashes['assessment.json'],'residual_coordinates':'Pr A Pc'}
    return {'lower':decode(f['L']),'upper':decode(f['U']),'permuted_rhs':[F(normal(v))for v in rhs],
            'pr':f['perm_r'],'pc':f['perm_c'],'provenance':provenance,'retained_prior_q':a['certificate']['contraction_upper'],
            'unchanged_kappa':a['kappa'],'unchanged_J':a['congruence'],'retained_raw_target_flags':{k:a[k]for k in ('raw_stored_inertia','raw_stored_coercivity')},
            'expected_hashes':dict(expected_hashes),'input_operations_used':budget.operations}
