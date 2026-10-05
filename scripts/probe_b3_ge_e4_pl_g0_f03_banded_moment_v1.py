"""Banded shell-port moment application against a bounded dense oracle."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import time

import numpy as np
from scipy import linalg


def relative(a,b):
    return float(np.linalg.norm(a-b)/max(np.linalg.norm(b),np.finfo(float).tiny))


def column_relative(a,b):
    reference=np.linalg.norm(b,axis=0)
    floor=max(1e-6*float(np.max(reference)),np.finfo(float).tiny)
    return float(np.max(np.linalg.norm(a-b,axis=0)/np.maximum(reference,floor)))


def banded(matrix, rhs, bandwidth):
    """Apply only the registered diagonal or tridiagonal moment block."""
    n=len(matrix)
    if bandwidth==0:
        diagonal=np.diag(matrix)
        if np.min(diagonal)<=0:
            raise ValueError('nonpositive diagonal moment block')
        extracted=np.diag(diagonal)
        data=diagonal
        solution=rhs/diagonal[:,None]
    else:
        diagonal=np.diag(matrix)
        upper=np.diag(matrix,1)
        lower=np.diag(matrix,-1)
        ab=np.zeros((3,n))
        ab[0,1:]=upper
        ab[1]=diagonal
        ab[2,:-1]=lower
        extracted=np.diag(diagonal)+np.diag(upper,1)+np.diag(lower,-1)
        # Positive elimination pivots confirm the registered SPD block.
        pivots=diagonal.copy()
        for i in range(1,n):
            pivots[i]-=lower[i-1]*upper[i-1]/pivots[i-1]
        if np.min(pivots)<=0:
            raise ValueError('nonpositive tridiagonal moment pivot')
        data=ab
        solution=linalg.solve_banded((1,1),ab,rhs,check_finite=True)
    off=relative(matrix,extracted)
    return solution,off,data.nbytes


def native(topology,n_beam,n_shell):
    if not os.environ.get('NUMBA_CACHE_DIR'):
        raise RuntimeError('set a dedicated writable NUMBA_CACHE_DIR')
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
    from _b3_e4_f03_native_fixture import build
    from _b3_e4_f03_shell_trace import make_shell
    from probe_b3_ge_e4_pl_g0_f03_k1_rank import candidate_spaces
    from probe_b3_ge_e4_pl_g0_f03_kkt import assemble, scales
    from probe_b3_ge_e4_pl_g0_f03_local_trace_norm_v1 import (
        local_matrices,local_functional)
    from probe_b3_ge_e4_pl_g0_f03_signed_norm_v1 import L0,U,couplings
    from probe_b3_ge_e4_pl_g0_f03_shell_port_lift_v1 import port_coordinates

    beam,shell=build(n_beam),make_shell(n_shell,topology)
    spaces={s.name:s for s in candidate_spaces(beam,shell)}
    overlay=assemble(beam,shell,spaces['p1-beam']).integration_knots
    r,e,mid,jumps=local_matrices(beam,shell,overlay)
    if mid>1e-10 or jumps!=n_beam-1 or len(e)>2500:
        raise ValueError('bounded native overlay admission failed')
    sq,_=scales(beam,shell,3*n_beam)
    eh=e*sq[None,:]/U
    q=port_coordinates(beam,shell)
    sh=e@q/U
    if relative(sh[:2,:2],np.eye(2)/U)>1e-12 or np.max(np.abs(sh[:2,2:]))>1e-10:
        raise ValueError('physical shell root port identity failed')
    out={'kind':'native','topology':topology,'n_beam':n_beam,'n_shell':n_shell,
         'trace_rows':len(e),'primal_columns':eh.shape[1],
         'overlay_intervals':len(overlay)-1,'spaces':{},
         'status':'BANDED_MOMENT_PARITY_NOT_F03_ACCEPTANCE'}
    for name,(c,_) in couplings(beam,shell).items():
        f=local_functional(beam,overlay,name)
        fh=f/L0
        if relative(f@e*sq[None,:],c*sq[None,:])>1e-10:
            raise ValueError('native row functional mismatch')
        d=np.vstack((fh@sh,sh[:2,:]))
        target=np.vstack((fh@eh,eh[:2,:]))
        began=time.perf_counter()
        dense=linalg.solve(d,target)
        dense_seconds=time.perf_counter()-began
        began=time.perf_counter()
        port=linalg.solve(d[-2:,:2],target[-2:])
        remainder=target[:3*n_beam]-d[:3*n_beam,:2]@port
        t=d[:3*n_beam,2:]
        offblock=t.copy()
        for axis in range(3):
            j=slice(axis*n_beam,(axis+1)*n_beam)
            offblock[j,j]=0
        cross=relative(offblock,t)
        if cross>1e-12 or np.max(np.abs(d[-2:,2:]))>1e-10:
            raise ValueError('rooted moment blocks are coupled unexpectedly')
        parts=[]
        block_off=[]
        band_bytes=0
        for axis in range(3):
            j=slice(axis*n_beam,(axis+1)*n_beam)
            solve,off,bytes_=banded(t[j,j],remainder[j],
                                    1 if axis<2 and name=='k4' else 0)
            parts.append(solve)
            block_off.append(off)
            band_bytes+=bytes_
        if max(block_off)>1e-12:
            raise ValueError('registered banded moment structure differs')
        sparse=np.vstack((port,*parts))
        banded_seconds=time.perf_counter()-began
        coefficient=column_relative(sparse,dense)
        traced=column_relative(sh@sparse,sh@dense)
        moment=relative(fh@sh@sparse,fh@eh)
        root=relative((sh@sparse)[:2],eh[:2])
        idempotence=relative((sh@sparse)@(q/sq[:,None]),sh)
        if max(coefficient,traced)>1e-10 or max(moment,root,idempotence)>1e-9:
            raise ValueError('banded apply differs from dense mechanical oracle')
        out['spaces'][name]={'cross_block_relative':cross,
                             'max_off_band_relative':max(block_off),
                             'coefficient_parity':coefficient,
                             'trace_parity':traced,
                             'moment_residual':moment,
                             'root_residual':root,
                             'idempotence_residual':idempotence,
                             'explicit_band_storage_bytes':band_bytes,
                             'rhs_bytes':remainder.nbytes,
                             'dense_oracle_seconds':dense_seconds,
                             'banded_apply_seconds':banded_seconds}
    return out


def synthetic(n):
    h=1/n
    coordinate=np.arange(1,n+1)
    rhs=(np.sin(2*np.pi*coordinate/n)+.25*(-1.)**coordinate)[:,None]
    observations={}
    for name in ('k4','local-dual','yaw-p0'):
        if name=='k4':
            diagonal=np.full(n,2*h/3)
            diagonal[-1]=h/3
            upper=np.full(n-1,h/6)
            ab=np.zeros((3,n))
            ab[0,1:]=upper
            ab[1]=diagonal
            ab[2,:-1]=upper
            started=time.perf_counter()
            solution=linalg.solve_banded((1,1),ab,rhs,check_finite=True)
            elapsed=time.perf_counter()-started
            reconstructed=diagonal[:,None]*solution
            reconstructed[1:]+=upper[:,None]*solution[:-1]
            reconstructed[:-1]+=upper[:,None]*solution[1:]
            storage=ab.nbytes+rhs.nbytes+solution.nbytes
        else:
            diagonal=np.full(n,h)
            if name=='local-dual':
                diagonal[-1]=h/2
            started=time.perf_counter()
            solution=rhs/diagonal[:,None]
            elapsed=time.perf_counter()-started
            reconstructed=diagonal[:,None]*solution
            storage=diagonal.nbytes+rhs.nbytes+solution.nbytes
        residual=relative(reconstructed,rhs)
        if residual>1e-11:
            raise ValueError('synthetic moment residual exceeds registered limit')
        observations[name]={'relative_residual':residual,
                            'explicit_array_bytes':storage,
                            'solve_seconds':elapsed}
    return {'kind':'synthetic','n_beam':n,'spaces':observations,
            'status':'LINEAR_STORAGE_SCREEN_NOT_NATIVE_F03_ACCEPTANCE'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--topology',choices=('Q4','S3-V2D'))
    group.add_argument('--synthetic-n',type=int)
    parser.add_argument('--n-beam',type=int)
    parser.add_argument('--n-shell',type=int)
    args=parser.parse_args()
    if args.topology:
        if (args.n_beam,args.n_shell) not in ((4,4),(8,8),(16,16),(8,1),(8,64)):
            parser.error('unregistered native mesh')
        result=native(args.topology,args.n_beam,args.n_shell)
    else:
        if args.synthetic_n not in (64,256,1024,4096,16384):
            parser.error('unregistered synthetic size')
        result=synthetic(args.synthetic_n)
    print(json.dumps(result,allow_nan=False,sort_keys=True))


if __name__=='__main__':
    main()
