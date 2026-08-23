"""Structured high-precision Q1D strip producer."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Sequence

import mpmath as mp

import e4_pl_q1b_common as common


STUDY_ID = "study_e4_pl_q1d.q1c_ultrathin_conditioning_closure_v1"
CANDIDATE_ID = "candidate_e4_pl_q1d.wg2020_ultrathin_block_precision_v1"
SCHEMA = "anysolver.s4.e4-pl-q1d-precision-proof-v1"
SHARDS = ("FULL_BLOCK_LDL", "DRILL_SCHUR", "ULTRATHIN_REFINEMENT")
PRECISIONS = (128, 192, 256)


def _zeros(rows: int, columns: int) -> mp.matrix:
    return mp.matrix(rows, columns)


def _lu_solve_matrix(matrix: mp.matrix, right: mp.matrix) -> mp.matrix:
    result=_zeros(matrix.rows,right.cols)
    for column in range(right.cols):
        solved=mp.lu_solve(matrix,right[:,column])
        for row in range(matrix.rows): result[row,column]=solved[row]
    return result


def _shape(r: mp.mpf, s: mp.mpf) -> list[mp.mpf]:
    return [(1-r)*(1-s)/4, (1+r)*(1-s)/4, (1+r)*(1+s)/4, (1-r)*(1+s)/4]


def _derivatives(r: mp.mpf, s: mp.mpf) -> tuple[list[mp.mpf], list[mp.mpf]]:
    return ([-(1-s)/4, (1-s)/4, (1+s)/4, -(1+s)/4], [-(1-r)/4, -(1+r)/4, (1+r)/4, (1-r)/4])


def _compatible(dx: mp.mpf, dy: mp.mpf, r: mp.mpf, s: mp.mpf) -> mp.matrix:
    nr, ns = _derivatives(r, s); nx = [2*x/dx for x in nr]; ny = [2*x/dy for x in ns]; out = _zeros(8, 20)
    for i in range(4):
        b=5*i; out[0,b]=nx[i]; out[1,b+1]=ny[i]; out[2,b]=ny[i]; out[2,b+1]=nx[i]; out[3,b+4]=nx[i]; out[4,b+3]=-ny[i]; out[5,b+4]=ny[i]; out[5,b+3]=-nx[i]
    def natural(rr: mp.mpf, ss: mp.mpf, direction: int) -> mp.matrix:
        shp=_shape(rr,ss); dr,ds=_derivatives(rr,ss); derivative=dr if direction==0 else ds; row=_zeros(1,20); xd=dx/2 if direction==0 else 0; yd=dy/2 if direction==1 else 0
        for j in range(4):
            b=5*j; row[0,b+2]=derivative[j]; row[0,b+3]=-yd*shp[j]; row[0,b+4]=xd*shp[j]
        return row
    gr=(1-s)*natural(0,-1,0)/2+(1+s)*natural(0,1,0)/2; gs=(1+r)*natural(1,0,1)/2+(1-r)*natural(-1,0,1)/2
    for column in range(20): out[6,column]=2*gr[0,column]/dx; out[7,column]=2*gs[0,column]/dy
    return out


def _interpolations(dx: mp.mpf, dy: mp.mpf, r: mp.mpf, s: mp.mpf) -> tuple[mp.matrix, mp.matrix]:
    xr,ys=dx/2,dy/2; ns=_zeros(8,14); ne=_zeros(8,21)
    for i in range(8): ns[i,i]=1; ne[i,i]=1
    seed=((s,0),(0,r),(0,0)); sv=((xr*xr*seed[0][0],xr*xr*seed[0][1]),(ys*ys*seed[1][0],ys*ys*seed[1][1]),(xr*ys*seed[2][0],xr*ys*seed[2][1]))
    for row,column in ((0,8),(3,10)):
        for i in range(3):
            for j in range(2): ns[row+i,column+j]=sv[i][j]; ne[row+i,column+j]=sv[i][j]
    ss=((s,0),(0,r)); shear=((xr*ss[0][0],xr*ss[0][1]),(ys*ss[1][0],ys*ss[1][1]))
    for i in range(2):
        for j in range(2): ns[6+i,12+j]=shear[i][j]; ne[6+i,12+j]=shear[i][j]
    m7=((r,0,0,0,r*s,0,0),(0,s,0,0,0,r*s,0),(0,0,r,s,0,0,r*s)); scales=(xr*xr,ys*ys,xr*ys)
    for i in range(3):
        for j in range(7): ne[i,14+j]=scales[i]*m7[i][j]
    return ns,ne


def _material(thickness: mp.mpf) -> mp.matrix:
    e=mp.mpf(15); nu=mp.mpf(1)/4; g=mp.mpf(6); ks=mp.mpf(5)/6; out=_zeros(8,8); template=((1,nu,0),(nu,1,0),(0,0,(1-nu)/2))
    for i in range(3):
        for j in range(3): out[i,j]=e*thickness/(1-nu*nu)*template[i][j]; out[3+i,3+j]=e*thickness**3/(12*(1-nu*nu))*template[i][j]
    out[6,6]=ks*g*thickness; out[7,7]=ks*g*thickness; return out


def _centre(dx: mp.mpf, dy: mp.mpf) -> mp.matrix:
    f0=(mp.mpf(1)/4,)*4; fr=(-mp.mpf(1)/4,mp.mpf(1)/4,mp.mpf(1)/4,-mp.mpf(1)/4); fs=(-mp.mpf(1)/4,-mp.mpf(1)/4,mp.mpf(1)/4,mp.mpf(1)/4); frs=(mp.mpf(1)/4,-mp.mpf(1)/4,mp.mpf(1)/4,-mp.mpf(1)/4); xr,ys,jc=dx/2,dy/2,dx*dy/4; out=_zeros(3,24)
    for coordinate in range(24):
        node,component=divmod(coordinate,6); ur=fr[node] if component==0 else 0; us=fs[node] if component==0 else 0; urs=frs[node] if component==0 else 0; vr=fr[node] if component==1 else 0; vs=fs[node] if component==1 else 0; vrs=frs[node] if component==1 else 0; d0=f0[node] if component==5 else 0; dr=fr[node] if component==5 else 0; ds=fs[node] if component==5 else 0; n0=xr*us-ys*vr; nr=xr*urs-ys*vrs
        out[0,coordinate]=d0+n0/(2*jc); out[1,coordinate]=dr+nr/(2*jc); out[2,coordinate]=ds
    return out


def _local_matrix(divisions: int, thickness: mp.mpf) -> mp.matrix:
    dx=mp.mpf(1)/divisions; dy=mp.mpf(1)/10; gp=(-1/mp.sqrt(3),1/mp.sqrt(3)); gauss=((gp[0],gp[0]),(gp[1],gp[0]),(gp[1],gp[1]),(gp[0],gp[1])); jac=dx*dy/4; f=_zeros(21,14); gq=_zeros(14,20); h=_zeros(21,21); material=_material(thickness)
    for r,s in gauss:
        ns,ne=_interpolations(dx,dy,r,s); compatible=_compatible(dx,dy,r,s); f-=jac*(ne.T*ns); gq+=jac*(ns.T*compatible); h+=jac*(ne.T*material*ne)
    d35=_zeros(35,35)
    for i in range(14):
        for j in range(21): d35[i,14+j]=f[j,i]; d35[14+j,i]=f[j,i]
    for i in range(21):
        for j in range(21): d35[14+i,14+j]=h[i,j]
    q=_zeros(24,35)
    for node in range(4):
        for component in range(5):
            for column in range(14): q[6*node+component,column]=gq[column,5*node+component]
    core=-(q*_lu_solve_matrix(d35,q.T)); gram=_zeros(3,3)
    for r,s in gauss:
        p=(1,r,s)
        for i in range(3):
            for j in range(3): gram[i,j]+=thickness*jac*p[i]*p[j]
    centre=_centre(dx,dy); pl=6*centre.T*gram*centre
    x=(-dx/2,dx/2,dx/2,-dx/2); y=(-dy/2,-dy/2,dy/2,dy/2); xi=(-1,1,1,-1); eta=(-1,-1,1,1); h4=(1,-1,1,-1); area=dx*dy
    dot=lambda a,b: sum((a[i]*b[i] for i in range(4)),mp.mpf(0)); b1=[(dot(eta,y)*xi[i]-dot(xi,y)*eta[i])/(4*area) for i in range(4)]; b2=[(-dot(eta,x)*xi[i]+dot(xi,x)*eta[i])/(4*area) for i in range(4)]; gamma=[(h4[i]-dot(h4,x)*b1[i]-dot(h4,y)*b2[i])/4 for i in range(4)]; gamma24=_zeros(24,1)
    for i in range(4): gamma24[6*i+5]=gamma[i]
    total=core+pl+(mp.mpf(2)/1000)*6*thickness*area*(gamma24*gamma24.T)
    return (total+total.T)/2


def _slice(matrix: mp.matrix, rows: list[int], columns: list[int]) -> mp.matrix:
    return mp.matrix([[matrix[i,j] for j in columns] for i in rows])


def _blocks(divisions: int, thickness: mp.mpf) -> tuple[list[mp.matrix],list[mp.matrix],list[mp.matrix],str]:
    local=_local_matrix(divisions,thickness); left=list(range(6))+list(range(18,24)); right=list(range(6,18)); ll=_slice(local,left,left); lr=_slice(local,left,right); rr=_slice(local,right,right); active0=[5,11]; active=list(range(12)); diagonals=[]; off=[]
    for section in range(divisions+1):
        block=ll if section==0 else rr if section==divisions else rr+ll; indices=active0 if section==0 else active; diagonals.append(_slice(block,indices,indices))
        if section<divisions: off.append(_slice(lr,indices,active))
    loads=[_zeros(len(active0) if i==0 else 12,1) for i in range(divisions+1)]; loads[-1][2]=mp.mpf(1)/2; loads[-1][8]=mp.mpf(1)/2
    tokens=[[_token(local[i,j]) for j in range(24)] for i in range(24)]; digest=hashlib.sha256((json.dumps(tokens,sort_keys=True,separators=(",",":"))+"\n").encode()).hexdigest().upper(); return diagonals,off,loads,digest


def _block_solve(diagonals: list[mp.matrix], off: list[mp.matrix], loads: list[mp.matrix]) -> tuple[list[mp.matrix],mp.mpf,mp.mpf]:
    schur=[diagonals[0].copy()]; reduced=[loads[0].copy()]
    for i in range(1,len(diagonals)):
        inv_off=_lu_solve_matrix(schur[-1],off[i-1]); inv_load=mp.lu_solve(schur[-1],reduced[-1]); schur.append(diagonals[i]-off[i-1].T*inv_off); reduced.append(loads[i]-off[i-1].T*inv_load)
    solution=[_zeros(block.rows,1) for block in diagonals]; solution[-1]=mp.lu_solve(schur[-1],reduced[-1])
    for i in range(len(solution)-2,-1,-1): solution[i]=mp.lu_solve(schur[i],reduced[i]-off[i]*solution[i+1])
    max_residual=mp.mpf(0); max_scale=mp.mpf(0)
    for i,(block,x,load) in enumerate(zip(diagonals,solution,loads,strict=True)):
        residual=block*x-load
        if i: residual+=off[i-1].T*solution[i-1]
        if i<len(off): residual+=off[i]*solution[i+1]
        max_residual=max(max_residual,max((abs(v) for v in residual),default=mp.mpf(0))); row_norm=max((sum(abs(block[r,c]) for c in range(block.cols)) for r in range(block.rows)),default=mp.mpf(0)); max_scale=max(max_scale,row_norm*max((abs(v) for v in x),default=mp.mpf(0))+max((abs(v) for v in load),default=mp.mpf(0)))
    tip=(solution[-1][2]+solution[-1][8])/2; return solution,tip,max_residual/max_scale


def _token(value: mp.mpf) -> str:
    return mp.nstr(value,90,strip_zeros=False,min_fixed=0,max_fixed=0)


def _case(divisions: int, thickness: str, bits: int, *, include_solution: bool=False) -> dict[str,Any]:
    with mp.workprec(bits):
        t=mp.mpf(thickness); diagonals,off,loads,digest=_blocks(divisions,t); solution,tip,residual=_block_solve(diagonals,off,loads); eb=1/(mp.mpf(15)*(mp.mpf("0.1")*t**3/12)*3); ratio=tip/eb
        row={"bits":bits,"division":divisions,"displacement":_token(tip),"local_matrix_sha256":digest,"relative_error_eb":_token(abs(ratio-1)),"response_ratio_eb":_token(ratio),"scaled_residual":_token(residual),"thickness_ratio":thickness}
        if include_solution: row["solution"]=[[_token(value) for value in block] for block in solution]
        return row


def produce(shard: str) -> dict[str,Any]:
    if shard not in SHARDS: raise common.Q1BError("unknown Q1D shard")
    if shard in SHARDS[:2]: rows=[_case(32,"1e-6",bits,include_solution=bits==256) for bits in PRECISIONS]
    else: rows=[_case(division,thickness,256,include_solution=True) for thickness in ("1e-5","1e-6") for division in (16,32)]
    payload={"rows":rows,"shard":shard}; return {"candidate_id":CANDIDATE_ID,"payload":payload,"payload_sha256":common.sha256(common.canonical_bytes(payload)),"production":"NO_GO_PRODUCTION_RESTRICTION_UNCHANGED","schema":SCHEMA,"study_id":STUDY_ID}


def main(argv: Sequence[str]|None=None) -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--emit-precision-proof",action="store_true",required=True); parser.add_argument("--shard",choices=SHARDS,required=True); parser.add_argument("--output",type=Path,required=True); args=parser.parse_args(argv)
    try: common.write_exclusive(args.output,produce(args.shard)); return 0
    except (OSError,ValueError,ZeroDivisionError,common.Q1BError) as exc: print(str(exc),file=sys.stderr); return 2


if __name__=="__main__": raise SystemExit(main())
