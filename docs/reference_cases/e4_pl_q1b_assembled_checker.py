"""Independent Q1B evidence checker.

The checker does not import the producer.  It independently reconstructs the
decisive affine locking strip operator and validates all nonclassifying shard
coverage and interval semantics.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

import numpy as np
from scipy import linalg

import e4_pl_q1b_common as common


IMPLEMENTATION_ID = "Q1B_INDEPENDENT_AFFINE_AND_EVIDENCE_CHECKER"
RUNNER_ID = IMPLEMENTATION_ID


def _derivatives(r: float, s: float) -> tuple[np.ndarray,np.ndarray]:
    return np.array((-(1-s),1-s,1+s,-(1+s)))/4, np.array((-(1-r),-(1+r),1+r,1-r))/4


def _shape(r: float,s: float) -> np.ndarray:
    return np.array(((1-r)*(1-s),(1+r)*(1-s),(1+r)*(1+s),(1-r)*(1+s)))/4


def _affine_compatible(dx: float,dy: float,r: float,s: float) -> np.ndarray:
    nr,ns=_derivatives(r,s); nx=2*nr/dx; ny=2*ns/dy; out=np.zeros((8,20))
    for i in range(4):
        b=5*i; out[0,b]=nx[i]; out[1,b+1]=ny[i]; out[2,b]=ny[i]; out[2,b+1]=nx[i]
        out[3,b+4]=nx[i]; out[4,b+3]=-ny[i]; out[5,b+4]=ny[i]; out[5,b+3]=-nx[i]
    def natural(rr: float,ss: float,direction: int) -> np.ndarray:
        shp=_shape(rr,ss); dr,ds=_derivatives(rr,ss); derivative=dr if direction==0 else ds; row=np.zeros(20)
        xd=dx/2 if direction==0 else 0.; yd=dy/2 if direction==1 else 0.
        for j in range(4):
            b=5*j; row[b+2]=derivative[j]; row[b+3]=-yd*shp[j]; row[b+4]=xd*shp[j]
        return row
    gr=.5*(1-s)*natural(0,-1,0)+.5*(1+s)*natural(0,1,0)
    gs=.5*(1+r)*natural(1,0,1)+.5*(1-r)*natural(-1,0,1)
    out[6]=2*gr/dx; out[7]=2*gs/dy
    return out


def _affine_interpolations(dx: float,dy: float,r: float,s: float) -> tuple[np.ndarray,np.ndarray]:
    xr,ys=dx/2,dy/2
    ts=np.diag((xr*xr,ys*ys,xr*ys)); te=np.diag((xr*xr,ys*ys,xr*ys))
    ns=np.zeros((8,14)); ne=np.zeros((8,21)); ns[:,:8]=np.eye(8); ne[:,:8]=np.eye(8)
    seed=np.array(((s,0),(0,r),(0,0)),dtype=float); sv=ts@seed; ev=te@seed
    for row,column in ((0,8),(3,10)): ns[row:row+3,column:column+2]=sv; ne[row:row+3,column:column+2]=ev
    shear=np.diag((xr,ys)); ss=np.array(((s,0),(0,r)),dtype=float); ns[6:8,12:14]=shear@ss; ne[6:8,12:14]=shear@ss
    m7=np.array(((r,0,0,0,r*s,0,0),(0,s,0,0,0,r*s,0),(0,0,r,s,0,0,r*s)),dtype=float)
    ne[:3,14:21]=te@m7
    return ns,ne


def _material(thickness: float) -> np.ndarray:
    e,nu,g,ks=15.,.25,6.,5/6
    template=np.array(((1,nu,0),(nu,1,0),(0,0,(1-nu)/2)))
    out=np.zeros((8,8)); out[:3,:3]=e*thickness/(1-nu*nu)*template; out[3:6,3:6]=e*thickness**3/(12*(1-nu*nu))*template; out[6:,6:]=ks*g*thickness*np.eye(2)
    return out


def _centre(dx: float,dy: float) -> np.ndarray:
    f0=np.ones(4)/4; fr=np.array((-1,1,1,-1))/4; fs=np.array((-1,-1,1,1))/4; frs=np.array((1,-1,1,-1))/4
    xr,ys,jc=dx/2,dy/2,dx*dy/4; out=np.zeros((3,24))
    for coordinate in range(24):
        node,component=divmod(coordinate,6)
        ur=fr[node] if component==0 else 0.; us=fs[node] if component==0 else 0.; urs=frs[node] if component==0 else 0.
        vr=fr[node] if component==1 else 0.; vs=fs[node] if component==1 else 0.; vrs=frs[node] if component==1 else 0.
        d0=f0[node] if component==5 else 0.; dr=fr[node] if component==5 else 0.; ds=fs[node] if component==5 else 0.
        n0=xr*us-ys*vr; nr=xr*urs-ys*vrs; ns=0.
        out[0,coordinate]=d0+n0/(2*jc); out[1,coordinate]=dr+nr/(2*jc); out[2,coordinate]=ds+ns/(2*jc)
    return out


def _affine_element(dx: float,dy: float,thickness: float) -> np.ndarray:
    gp=(-1/math.sqrt(3),1/math.sqrt(3)); gauss=((gp[0],gp[0]),(gp[1],gp[0]),(gp[1],gp[1]),(gp[0],gp[1])); jac=dx*dy/4
    f=np.zeros((21,14)); gq=np.zeros((14,20)); h=np.zeros((21,21)); material=_material(thickness)
    for r,s in gauss:
        ns,ne=_affine_interpolations(dx,dy,r,s); compatible=_affine_compatible(dx,dy,r,s)
        f-=jac*(ne.T@ns); gq+=jac*(ns.T@compatible); h+=jac*(ne.T@material@ne)
    d35=np.zeros((35,35)); d35[:14,14:]=f.T; d35[14:,:14]=f; d35[14:,14:]=h
    q20=np.zeros((20,35)); q20[:,:14]=gq.T; q=np.zeros((24,35))
    for node in range(4): q[6*node:6*node+5]=q20[5*node:5*node+5]
    core=-q@linalg.solve(d35,q.T,assume_a="sym")
    gram=np.zeros((3,3))
    for r,s in gauss:
        p=np.array((1,r,s)); gram+=thickness*jac*np.outer(p,p)
    centre=_centre(dx,dy); pl=6*centre.T@gram@centre
    # The affine rectangle residual mode is reconstructed from its nodes.
    x=np.array((-dx/2,dx/2,dx/2,-dx/2)); y=np.array((-dy/2,-dy/2,dy/2,dy/2)); xi=np.array((-1,1,1,-1)); eta=np.array((-1,-1,1,1)); h4=np.array((1,-1,1,-1)); area=dx*dy
    b1=((eta@y)*xi-(xi@y)*eta)/(4*area); b2=(-(eta@x)*xi+(xi@x)*eta)/(4*area); gamma=(h4-(h4@x)*b1-(h4@y)*b2)/4
    gamma24=np.zeros(24); gamma24[5::6]=gamma; hg=2*.001*6*thickness*area*np.outer(gamma24,gamma24)
    return core+pl+hg


def _independent_locking(divisions: int,thickness: float) -> float:
    dx,dy=1/divisions,.1; element=_affine_element(dx,dy,thickness); node_count=2*(divisions+1); stiffness=np.zeros((6*node_count,6*node_count)); stride=divisions+1
    for index in range(divisions):
        nodes=(index,index+1,stride+index+1,stride+index); dofs=np.array([6*n+c for n in nodes for c in range(6)]); stiffness[np.ix_(dofs,dofs)]+=element
    fixed=np.array([c for n in (0,stride) for c in range(5)]); free=np.setdiff1d(np.arange(6*node_count),fixed); force=np.zeros(6*node_count)
    for n in (divisions,stride+divisions): force[6*n+2]=.5
    q=np.zeros_like(force); q[free]=linalg.solve(stiffness[np.ix_(free,free)],force[free],assume_a="sym")
    displacement=float((q[6*divisions+2]+q[6*(stride+divisions)+2])/2); reference=1/(15*(.1*thickness**3/12)*3)
    return abs(displacement/reference-1)


def _validate_bounds(value: Any) -> None:
    if isinstance(value,dict):
        if set(value)=={"hi","lo"}: common.Bound.from_record(value)
        else:
            for child in value.values(): _validate_bounds(child)
    elif isinstance(value,list):
        for child in value: _validate_bounds(child)


def verify(record_path: Path) -> dict[str,Any]:
    raw,record=common.read_json(record_path)
    required={"candidate_id","coverage","cycle","implementation_id","payload_sha256","production","schema","shard","study_id"}
    common.strict_record(record,required,common.SHARD_SCHEMA)
    if record["candidate_id"]!=common.CANDIDATE_ID or record["study_id"]!=common.STUDY_ID or record["shard"] not in common.SHARDS or record["cycle"] not in (1,2): raise common.Q1BError("shard identity mismatch")
    if record["payload_sha256"]!=common.sha256(common.canonical_bytes(record["coverage"])): raise common.Q1BError("shard payload hash mismatch")
    _validate_bounds(record["coverage"]); contradiction=[]; disagreement=[]; coverage=record["coverage"]
    if record["shard"]=="ASSEMBLED_STABILITY":
        rows=coverage.get("rows",[]); expected=[(family,level) for family in common.GEOMETRY_FAMILIES for level in common.REFINEMENTS]
        if [(row.get("family"),row.get("level")) for row in rows]!=expected: disagreement.append("STABILITY_COVERAGE")
        if coverage.get("domain_certificate",{}).get("status")!="UNRESOLVED_NOT_FINITE_SAMPLE_SUBSTITUTION": disagreement.append("DOMAIN_CERTIFICATE_OVERCLAIM")
        if coverage.get("certified_failure"): contradiction.append("ASSEMBLED_STABILITY")
    elif record["shard"]=="LOCKING_REFINEMENT":
        rows=coverage.get("rows",[]); expected=[(n,t) for n in common.LOCKING_DIVISIONS for t in common.THICKNESS_RATIOS]
        if [(row.get("division"),row.get("thickness_ratio")) for row in rows]!=expected: disagreement.append("LOCKING_COVERAGE")
        # Independently reconstruct the first claimed threshold violation.
        claimed=next((row for row in rows if common.Bound.from_record(row["relative_error"]).lo>2e-2),None)
        if claimed is not None:
            observed=_independent_locking(int(claimed["division"]),float(claimed["thickness_ratio"]))
            if observed<=2e-2: disagreement.append("LOCKING_CONTRADICTION_NOT_REPRODUCED")
            else: contradiction.append("LOCKING_ANALYTICAL_ERROR")
        if bool(coverage.get("certified_failure")) != bool(claimed): disagreement.append("LOCKING_FAILURE_FLAG")
    else:
        rows=coverage.get("rows",[])
        if [row.get("family") for row in rows]!=list(common.GEOMETRY_FAMILIES): disagreement.append("NONINTRUSION_COVERAGE")
        for row in rows:
            if common.Bound.from_record(row["reaction_split_error"]).lo>1e-10 or common.Bound.from_record(row["physical_drill_contamination"]).lo>1e-10: contradiction.append("NONINTRUSION_SEPARATION")
        if bool(coverage.get("certified_failure")) != bool(contradiction): disagreement.append("NONINTRUSION_FAILURE_FLAG")
    return {"candidate_id":common.CANDIDATE_ID,"checker_id":IMPLEMENTATION_ID,"contradictions":sorted(set(contradiction)),"cycle":record["cycle"],"disagreements":sorted(set(disagreement)),"production":"NO_GO_PRODUCTION_RESTRICTION_UNCHANGED","schema":common.CHECK_SCHEMA,"shard":record["shard"],"shard_record_sha256":common.sha256(raw),"study_id":common.STUDY_ID}


def _parser() -> argparse.ArgumentParser:
    parser=argparse.ArgumentParser(); group=parser.add_mutually_exclusive_group(required=True); group.add_argument("--check-shard",action="store_true"); group.add_argument("--authority-check-only",action="store_true")
    parser.add_argument("--repository-root",type=Path,required=True); parser.add_argument("--contract",type=Path,required=True); parser.add_argument("--contract-sha256",required=True); parser.add_argument("--authority",type=Path,required=True); parser.add_argument("--authority-sha256",required=True); parser.add_argument("--record",type=Path); parser.add_argument("--output",type=Path); return parser


def main(argv: Sequence[str]|None=None) -> int:
    args=_parser().parse_args(argv)
    try:
        common.validate_execution_authority(repository_root=args.repository_root,contract_path=args.contract,contract_sha256=args.contract_sha256,authority_path=args.authority,authority_sha256=args.authority_sha256,runner_id=RUNNER_ID)
        if args.authority_check_only:
            print(common.canonical_bytes({"runner_id":RUNNER_ID,"status":"PASS"}).decode(),end=""); return 0
        if args.record is None or args.output is None: raise common.Q1BError("record and output are required")
        common.write_exclusive(args.output,verify(args.record)); return 0
    except (OSError,ValueError,np.linalg.LinAlgError,common.Q1BError) as exc: print(str(exc),file=sys.stderr); return 2


if __name__=="__main__": raise SystemExit(main())
