"""Mesh-local broken-trace Riesz diagnostic; no F03 or product qualification.

The independent endpoint trace space is a DG comparison norm. Its sparse
Riesz matrix is assembled from overlay cells and native yaw jumps. The
dual is computed by sparse solves, never a global primal graph inverse.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

if not os.environ.get('NUMBA_CACHE_DIR'):
    raise RuntimeError('set a writable NUMBA_CACHE_DIR before source import')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))

import numpy as np
from scipy import linalg,sparse
from scipy.sparse.linalg import splu

from _b3_e4_f03_native_fixture import build
from _b3_e4_f03_shell_trace import make_shell
from probe_b3_ge_e4_pl_g0_f03_broken_trace_v1 import graph,trace
from probe_b3_ge_e4_pl_g0_f03_k1_rank import candidate_spaces
from probe_b3_ge_e4_pl_g0_f03_kkt import assemble
from probe_b3_ge_e4_pl_g0_f03_signed_norm_v1 import L0,U,W0,couplings
from probe_b3_ge_e4_pl_g0_f03_trace_dual_v1 import primal_factors,normalized_metrics


def local_matrices(beam,shell,overlay):
    """R and E on independent left/right three-channel traces per cell.

    R has L2/L0, L0*H1 and L0*n_half_cells yaw-jump contributions, exactly
    matching the old pulled-back graph when restricted to image(E).
    """
    intervals=len(overlay)-1
    n=shell.free_count+len(beam.physical)+len(beam.internal)
    if intervals<=0 or np.any(np.diff(overlay)<=0):
        raise ValueError('invalid reference overlay')
    rows,cols,data=[],[],[]
    e=np.empty((6*intervals,n))
    mid_error=0.
    for cell,(a,b) in enumerate(zip(overlay[:-1],overlay[1:])):
        h=float(b-a)
        t1=trace(beam,shell,float(a+h/4))
        t2=trace(beam,shell,float(a+3*h/4))
        left=1.5*t1-.5*t2
        right=-.5*t1+1.5*t2
        e[6*cell:6*cell+3]=left
        e[6*cell+3:6*cell+6]=right
        mid_error=max(mid_error,float(np.linalg.norm(
            trace(beam,shell,float((a+b)/2))-(left+right)/2)/
            max(np.linalg.norm(left),np.linalg.norm(right),1.)))
        mass=h/(6*L0)*np.array(((2.,1.),(1.,2.)))
        slope=L0/h*np.array(((1.,-1.),(-1.,1.)))
        local=mass+slope
        for channel in range(3):
            for side in range(2):
                for other in range(2):
                    rows.append(6*cell+3*side+channel)
                    cols.append(6*cell+3*other+channel)
                    data.append(local[side,other])
    native_jumps=0
    for j in range(1,beam.n_half_cells):
        station=j/beam.n_half_cells
        index=int(np.argmin(np.abs(overlay-station)))
        if index in (0,intervals) or abs(overlay[index]-station)>1e-12:
            raise ValueError('native yaw station absent from overlay')
        # Only native cell yaw has a physical trace jump. Translations
        # remain independent in the ambient DG space, so equivalence to
        # the physically restricted image must be checked separately.
        left=6*(index-1)+3
        right=6*index
        coefficient=L0*beam.n_half_cells
        for channel in (2,):
            for row,col,value in ((left+channel,left+channel,coefficient),
                                  (right+channel,right+channel,coefficient),
                                  (left+channel,right+channel,-coefficient),
                                  (right+channel,left+channel,-coefficient)):
                rows.append(row)
                cols.append(col)
                data.append(value)
        native_jumps+=1
    r=sparse.coo_matrix((data,(rows,cols)),shape=(len(e),len(e))).tocsc()
    r.sum_duplicates()
    return r,e,mid_error,native_jumps


def tests_at(n,cell,xi,space):
    """Native P1 or biorthogonal cell-translation rows and P0 yaw row."""
    result=np.zeros((3*n,3))
    if space=='k4':
        left,right=1-xi,xi
    elif space=='local-dual':
        left,right=2-3*xi,3*xi-1
    else:
        raise ValueError('unsupported diagnostic space')
    if cell:
        result[cell-1,0]=left
        result[n+cell-1,1]=left
    result[cell,0]=right
    result[n+cell,1]=right
    result[2*n+cell,2]=1.
    return result


def local_functional(beam,overlay,space):
    """Exact cellwise P1-test/P1-trace integral, with supported node 0."""
    intervals=len(overlay)-1
    n=beam.n_half_cells
    f=np.zeros((3*n,6*intervals))
    for cell,(a,b) in enumerate(zip(overlay[:-1],overlay[1:])):
        h=float(b-a)
        native=min(int((a+b)*.5*n),n-1)
        left=tests_at(n,native,float(a*n-native),space)
        right=tests_at(n,native,float(b*n-native),space)
        f[:,6*cell:6*cell+3]=h*(2*left+right)/6
        f[:,6*cell+3:6*cell+6]=h*(left+2*right)/6
    return f


def restricted_image_grams(c,graph,sq):
    """Dense bounded verification oracle only; not the local dual path."""
    scaled=(graph*sq[:,None])*sq[None,:]/(U*U)
    eig,vec=linalg.eigh(scaled)
    maximum=float(eig[-1])
    if maximum<=0 or eig[0]<-1e-10*maximum:
        raise ValueError('invalid restricted physical graph')
    cs=c*sq[None,:]/(U*L0)
    output={}
    for cutoff in (1e-12,1e-10,1e-8):
        positive=eig>cutoff*maximum
        residual=float(np.linalg.norm(cs@vec[:,~positive])/
                       max(np.linalg.norm(cs),np.finfo(float).tiny))
        lift=(cs@vec[:,positive])/np.sqrt(eig[positive])[None,:]
        output[str(cutoff)]=(lift@lift.T,int(np.count_nonzero(positive)),residual,
                             float(eig[positive][0]/maximum),
                             float(eig[~positive][-1]/maximum)
                             if np.any(~positive) else 0.)
    return output,float(eig[-1])


def measure(topology,n_beam,n_shell):
    beam,shell=build(n_beam),make_shell(n_shell,topology)
    spaces={s.name:s for s in candidate_spaces(beam,shell)}
    overlay=assemble(beam,shell,spaces['p1-beam']).integration_knots
    r,e,mid,jumps=local_matrices(beam,shell,overlay)
    if mid>1e-10 or jumps!=beam.n_half_cells-1:
        raise ValueError('overlay trace or native jump mismatch')
    lu=splu(r)
    if len(e)>2500:
        raise ValueError('bounded local trace diagnostic exceeds 2500 rows')
    sq,p,condense,pp,rr,er,skew=primal_factors(beam,shell)
    signs=np.r_[np.ones(p),np.sign(er)]
    old_graph,_,_=graph(beam,shell,overlay)
    pulled=e.T@(r@e)
    graph_parity=float(np.linalg.norm(
        (pulled-old_graph)*sq[:,None]*sq[None,:])/
        max(np.linalg.norm(old_graph*sq[:,None]*sq[None,:]),
            np.finfo(float).tiny))
    if graph_parity>1e-10:
        raise ValueError(f'local Riesz pullback differs from graph: {graph_parity}')
    output={'topology':topology,'n_beam':n_beam,'n_shell':n_shell,
            'trace_dofs':len(e),'riesz_nnz':r.nnz,
            'riesz_fill_nnz':lu.L.nnz+lu.U.nnz,
            'native_jumps':jumps,'midpoint_error':mid,
            'graph_pullback_parity':graph_parity,'spaces':{},
            'status':'MESH_LOCAL_DG_NORM_SCREEN_NOT_F03_ACCEPTANCE'}
    old=couplings(beam,shell)
    for name,(c,_) in old.items():
        f=local_functional(beam,overlay,name)
        assembled=f@e
        parity=float(np.linalg.norm((assembled-c)*sq[None,:])/
                     max(np.linalg.norm(c*sq[None,:]),np.finfo(float).tiny))
        if parity>1e-10:
            raise ValueError(f'{name} local functional fails C=F E: {parity}')
        dual=f@lu.solve(f.T)
        dual=(dual+dual.T)/(2*L0*L0)
        eig=linalg.eigvalsh(dual)
        if eig[0]<=1e-10*eig[-1]:
            raise ValueError(f'{name} DG functional is dependent')
        # Congruent scaling of the physical KKT and functional. R is a
        # trace norm of physical gaps, so the common U scale cancels.
        cs=c*sq[None,:]/(U*L0)
        cp,cr=cs[:,:p],cs[:,p:]
        b=np.hstack(((cp-cr@condense)@pp,cr@rr))
        restricted_variants,graph_max=restricted_image_grams(
            c,old_graph,sq)
        cutoff_results={}
        for cutoff,(restricted,rank,kernel,retained,dropped) in restricted_variants.items():
            if kernel>1e-8:
                raise ValueError(f'{name} functional acts on graph kernel at {cutoff}')
            image_eig=linalg.eigvalsh(restricted)
            if image_eig[0]<=1e-10*image_eig[-1]:
                raise ValueError(f'{name} restricted dual deficient at {cutoff}')
            difference=linalg.eigvalsh(dual-restricted)
            if difference[0]<-1e-9*eig[-1]:
                raise ValueError(f'{name} ambient dual below image at {cutoff}')
            equivalence=linalg.eigh(dual,restricted,eigvals_only=True)
            cutoff_results[cutoff]={
                'image_rank':rank,'image_kernel_residual':kernel,
                'smallest_retained_over_graph_max':retained,
                'largest_dropped_over_graph_max':dropped,
                'ambient_over_image_min':float(equivalence[0]),
                'ambient_over_image_max':float(equivalence[-1]),
                'ambient_minus_image_min_eigen':float(difference[0])}
        metrics=normalized_metrics(dual,b,signs)
        if metrics is None:
            raise ValueError(f'{name} DG dual lacks verified SPD margin')
        output['spaces'][name]={'constraint_parity':parity,
            'dual_min_eigen':float(eig[0]),
            'dual_max_eigen':float(eig[-1]),
            'image_graph_max_eigen':graph_max,
            'image_cutoff_sensitivity':cutoff_results,
            **metrics}
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--topology',choices=('Q4','S3-V2D'),required=True)
    parser.add_argument('--n-beam',type=int,required=True)
    parser.add_argument('--n-shell',type=int,required=True)
    args=parser.parse_args()
    if args.n_beam not in (4,8,16) or args.n_shell not in (1,4,8,16,64):
        parser.error('bounded diagnostic mesh inventory only')
    print(json.dumps(measure(args.topology,args.n_beam,args.n_shell),
                     allow_nan=False,sort_keys=True))


if __name__=='__main__':
    main()
