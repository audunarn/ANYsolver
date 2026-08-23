"""Bounded Q1C producer using the immutable Q1B element kernel."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
import sys
from typing import Any, Sequence

import numpy as np
from scipy import linalg

import e4_pl_q1b_assembled_producer as q1b
import e4_pl_q1b_common as common


STUDY_ID = "study_e4_pl_q1c.q1b_locking_diagnosis_and_conditioning_repair_v1"
CANDIDATE_ID = "candidate_e4_pl_q1c.wg2020_locking_diagnosis_physical_block_scaling_v1"
SCHEMA = "anysolver.s4.e4-pl-q1c-diagnostic-proof-v1"
SHARDS = ("SPATIAL_DISCRETIZATION", "THICKNESS_LOCKING", "CONDITIONING_SEPARATION")
THICKNESSES = ("1e-2", "1e-3", "1e-4", "1e-5", "1e-6")
DIVISIONS = (4, 8, 16, 32)


def _hex(value: float) -> str:
    if not math.isfinite(value):
        raise common.Q1BError("nonfinite diagnostic")
    return float(value).hex()


def _system(divisions: int, thickness: float) -> tuple[np.ndarray, np.ndarray, list[tuple[float,float,float]], list[int]]:
    width=0.1
    nodes=[(index/divisions,y,0.0) for y in (0.0,width) for index in range(divisions+1)]
    stride=divisions+1
    elements=[(index,index+1,stride+index+1,stride+index) for index in range(divisions)]
    matrices=q1b._assemble(nodes,elements,thickness)
    force=np.zeros(6*len(nodes)); right=[index for index,node in enumerate(nodes) if node[0]==1.0]
    for index in right: force[6*index+2]=1/len(right)
    return matrices["total"],force,nodes,right


def _indices(nodes: list[tuple[float,float,float]]) -> tuple[np.ndarray,np.ndarray,np.ndarray]:
    physical=np.array([6*index+component for index,node in enumerate(nodes) if node[0]!=0.0 for component in range(5)],dtype=int)
    drill=np.array([6*index+5 for index in range(len(nodes))],dtype=int)
    _,full=q1b._supported_indices(nodes)
    return physical,drill,full


def _equilibrated_solve(matrix: np.ndarray, load: np.ndarray) -> tuple[np.ndarray,np.ndarray]:
    diagonal=np.abs(np.diag(matrix)); floor=max(float(np.max(diagonal))*1e-30,np.finfo(float).tiny)
    scale=np.sqrt(np.maximum(diagonal,floor)); equilibrated=matrix/(scale[:,None]*scale[None,:])
    return linalg.solve(equilibrated,load/scale,assume_a="sym")/scale,equilibrated


def _solve(divisions: int, thickness: float, *, condensed: bool) -> dict[str,Any]:
    stiffness,force,nodes,right=_system(divisions,thickness); physical,drill,full=_indices(nodes)
    solution=np.zeros_like(force)
    if condensed:
        kpp=stiffness[np.ix_(physical,physical)]; kpd=stiffness[np.ix_(physical,drill)]; kdd=stiffness[np.ix_(drill,drill)]
        inverse_coupling=linalg.solve(kdd,kpd.T,assume_a="sym"); inverse_load=linalg.solve(kdd,force[drill],assume_a="sym")
        reduced=kpp-kpd@inverse_coupling; load=force[physical]-kpd@inverse_load
        physical_solution,equilibrated=_equilibrated_solve(reduced,load)
        solution[physical]=physical_solution; solution[drill]=inverse_load-inverse_coupling@physical_solution
        free=full
    else:
        free=full; reduced=stiffness[np.ix_(free,free)]; load=force[free]
        solution[free],equilibrated=_equilibrated_solve(reduced,load)
    displacement=float(np.mean([solution[6*index+2] for index in right]))
    eb=1.0/(15.0*(0.1*thickness**3/12.0)*3.0)
    rm=eb+1.0/((5.0/6.0)*6.0*0.1*thickness)
    full_reduced=stiffness[np.ix_(full,full)]; full_load=force[full]
    residual=float(np.linalg.norm(full_reduced@solution[full]-full_load,ord=np.inf)/(np.linalg.norm(full_reduced,ord=np.inf)*max(np.linalg.norm(solution[full],ord=np.inf),1.0)+np.linalg.norm(full_load,ord=np.inf)))
    return {
        "backward_error":_hex(residual),"condition_equilibrated":_hex(float(np.linalg.cond(equilibrated))),
        "condition_unscaled":_hex(float(np.linalg.cond(reduced))),"displacement":_hex(displacement),
        "division":divisions,"drill_treatment":"SCHUR_CONDENSED" if condensed else "DIRECT_FULL","eb_reference":_hex(eb),
        "relative_error_eb":_hex(abs(displacement/eb-1.0)),"relative_error_rm":_hex(abs(displacement/rm-1.0)),
        "response_ratio_eb":_hex(abs(displacement/eb)),"rm_reference":_hex(rm),"thickness_ratio":thickness.hex(),
    }


def produce(shard: str) -> dict[str,Any]:
    if shard not in SHARDS: raise common.Q1BError("unknown Q1C shard")
    if shard=="SPATIAL_DISCRETIZATION":
        rows=[_solve(n,1e-4,condensed=True) for n in DIVISIONS]
    elif shard=="THICKNESS_LOCKING":
        rows=[_solve(32,float(token),condensed=True) for token in THICKNESSES]
    else:
        rows=[]
        for token in THICKNESSES:
            full=_solve(32,float(token),condensed=False); condensed=_solve(32,float(token),condensed=True)
            rows.append({"condensed":condensed,"direct_full":full,"thickness_ratio":float(token).hex()})
    payload={"rows":rows,"shard":shard}
    return {"candidate_id":CANDIDATE_ID,"payload":payload,"payload_sha256":common.sha256(common.canonical_bytes(payload)),"production":"NO_GO_PRODUCTION_RESTRICTION_UNCHANGED","q1b_commit":"3df23199893eb136b2682c5190d1405b52dbdd58","schema":SCHEMA,"study_id":STUDY_ID}


def _parser() -> argparse.ArgumentParser:
    parser=argparse.ArgumentParser(); parser.add_argument("--emit-diagnostic",action="store_true",required=True); parser.add_argument("--shard",choices=SHARDS,required=True); parser.add_argument("--output",type=Path,required=True); return parser


def main(argv: Sequence[str]|None=None) -> int:
    try:
        args=_parser().parse_args(argv); common.write_exclusive(args.output,produce(args.shard)); return 0
    except (OSError,ValueError,common.Q1BError) as exc:
        print(str(exc),file=sys.stderr); return 2


if __name__=="__main__": raise SystemExit(main())
