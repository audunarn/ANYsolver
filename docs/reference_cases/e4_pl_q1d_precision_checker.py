"""Independent Q1D checker using rational recovery of the affine operator."""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any, Sequence

import mpmath as mp

import e4_pl_q1b_assembled_checker as affine
import e4_pl_q1b_common as common


STUDY_ID="study_e4_pl_q1d.q1c_ultrathin_conditioning_closure_v1"
CANDIDATE_ID="candidate_e4_pl_q1d.wg2020_ultrathin_block_precision_v1"
PROOF_SCHEMA="anysolver.s4.e4-pl-q1d-precision-proof-v1"
CHECK_SCHEMA="anysolver.s4.e4-pl-q1d-precision-check-v1"
CHECKER_ID="Q1D_INDEPENDENT_RATIONAL_SCALING_CHECKER"
SHARDS=("FULL_BLOCK_LDL","DRILL_SCHUR","ULTRATHIN_REFINEMENT")


def _token(value: mp.mpf) -> str:
    return mp.nstr(value,90,strip_zeros=False,min_fixed=0,max_fixed=0)


def _fraction(value: float) -> Fraction:
    return Fraction(float(value)).limit_denominator(10**9)


def _recovered_local(divisions: int, thickness: mp.mpf) -> mp.matrix:
    """Recover K(t)=t*A+t^3*B from independently assembled safe-scale rows."""
    dx=1.0/divisions; k1=affine._affine_element(dx,.1,1.0); k2=affine._affine_element(dx,.1,2.0); k3=affine._affine_element(dx,.1,3.0); cubic=(k2-2*k1)/6; linear=k1-cubic; result=mp.matrix(24)
    for i in range(24):
        for j in range(24):
            a=_fraction(linear[i,j]); b=_fraction(cubic[i,j]); predicted=3*a+27*b; observed=_fraction(k3[i,j])
            if predicted!=observed: raise common.Q1BError("independent affine thickness scaling mismatch")
            result[i,j]=(mp.mpf(a.numerator)/a.denominator)*thickness+(mp.mpf(b.numerator)/b.denominator)*thickness**3
    return (result+result.T)/2


def _slice(matrix: mp.matrix, rows: list[int], columns: list[int]) -> mp.matrix:
    return mp.matrix([[matrix[i,j] for j in columns] for i in rows])


def _lu_solve_matrix(matrix: mp.matrix, right: mp.matrix) -> mp.matrix:
    result=mp.matrix(matrix.rows,right.cols)
    for column in range(right.cols):
        solved=mp.lu_solve(matrix,right[:,column])
        for row in range(matrix.rows): result[row,column]=solved[row]
    return result


def _blocks(divisions: int, thickness: mp.mpf) -> tuple[list[mp.matrix],list[mp.matrix],list[mp.matrix],str]:
    local=_recovered_local(divisions,thickness); left=list(range(6))+list(range(18,24)); right=list(range(6,18)); ll=_slice(local,left,left); lr=_slice(local,left,right); rr=_slice(local,right,right); diagonals=[]; off=[]
    for section in range(divisions+1):
        block=ll if section==0 else rr if section==divisions else rr+ll; indices=[5,11] if section==0 else list(range(12)); diagonals.append(_slice(block,indices,indices))
        if section<divisions: off.append(_slice(lr,indices,list(range(12))))
    loads=[mp.matrix(2 if i==0 else 12,1) for i in range(divisions+1)]; loads[-1][2]=mp.mpf(1)/2; loads[-1][8]=mp.mpf(1)/2; tokens=[[_token(local[i,j]) for j in range(24)] for i in range(24)]; digest=hashlib.sha256((json.dumps(tokens,sort_keys=True,separators=(",",":"))+"\n").encode()).hexdigest().upper(); return diagonals,off,loads,digest


def _solve(diagonals: list[mp.matrix],off: list[mp.matrix],loads: list[mp.matrix]) -> tuple[list[mp.matrix],mp.mpf,mp.mpf]:
    schur=[diagonals[0].copy()]; reduced=[loads[0].copy()]
    for i in range(1,len(diagonals)):
        inv_off=_lu_solve_matrix(schur[-1],off[i-1]); inv_load=mp.lu_solve(schur[-1],reduced[-1]); schur.append(diagonals[i]-off[i-1].T*inv_off); reduced.append(loads[i]-off[i-1].T*inv_load)
    solution=[mp.matrix(block.rows,1) for block in diagonals]; solution[-1]=mp.lu_solve(schur[-1],reduced[-1])
    for i in range(len(solution)-2,-1,-1): solution[i]=mp.lu_solve(schur[i],reduced[i]-off[i]*solution[i+1])
    residual_max=mp.mpf(0); scale_max=mp.mpf(0)
    for i,(block,x,load) in enumerate(zip(diagonals,solution,loads,strict=True)):
        residual=block*x-load
        if i: residual+=off[i-1].T*solution[i-1]
        if i<len(off): residual+=off[i]*solution[i+1]
        residual_max=max(residual_max,max((abs(v) for v in residual),default=mp.mpf(0))); row_norm=max((sum(abs(block[r,c]) for c in range(block.cols)) for r in range(block.rows)),default=mp.mpf(0)); scale_max=max(scale_max,row_norm*max((abs(v) for v in x),default=mp.mpf(0))+max((abs(v) for v in load),default=mp.mpf(0)))
    return solution,(solution[-1][2]+solution[-1][8])/2,residual_max/scale_max


def _number(value: Any) -> mp.mpf:
    if not isinstance(value,str) or len(value)>160: raise common.Q1BError("precision value schema mismatch")
    try: result=mp.mpf(value)
    except ValueError as exc: raise common.Q1BError("invalid precision value") from exc
    if not mp.isfinite(result): raise common.Q1BError("nonfinite precision value")
    return result


def _verify_row(row: Any, *, expected_division: int, expected_thickness: str, expected_bits: int, solution_required: bool) -> dict[str,mp.mpf]:
    keys={"bits","division","displacement","local_matrix_sha256","relative_error_eb","response_ratio_eb","scaled_residual","thickness_ratio"}|({"solution"} if solution_required else set())
    if not isinstance(row,dict) or set(row)!=keys or row["division"]!=expected_division or row["thickness_ratio"]!=expected_thickness or row["bits"]!=expected_bits: raise common.Q1BError("precision row schema or identity mismatch")
    with mp.workprec(expected_bits):
        thickness=mp.mpf(expected_thickness); diagonals,off,loads,digest=_blocks(expected_division,thickness); solution,tip,residual=_solve(diagonals,off,loads); eb=1/(15*(mp.mpf(".1")*thickness**3/12)*3); ratio=tip/eb; expected={"displacement":tip,"relative_error_eb":abs(ratio-1),"response_ratio_eb":ratio,"scaled_residual":residual}
        if not isinstance(row["local_matrix_sha256"],str) or len(row["local_matrix_sha256"])!=64 or row["local_matrix_sha256"]!=row["local_matrix_sha256"].upper(): raise common.Q1BError("producer local matrix digest schema mismatch")
        # The independent path recovers exact rational thickness coefficients
        # from safe-scale binary64 assemblies.  Half-precision agreement is a
        # conservative cross-implementation bound and still exceeds the frozen
        # 1e-18 scientific decision margin by many orders at every rung.
        tolerance=mp.power(2,-expected_bits//2)
        for key,value in expected.items():
            observed=_number(row[key])
            if abs(observed-value)>tolerance*max(1,abs(value)): raise common.Q1BError(f"independent precision value mismatch: {key}")
        if solution_required:
            observed_solution=row["solution"]
            if not isinstance(observed_solution,list) or len(observed_solution)!=len(solution): raise common.Q1BError("precision solution block count mismatch")
            for observed_block,expected_block in zip(observed_solution,solution,strict=True):
                if not isinstance(observed_block,list) or len(observed_block)!=expected_block.rows: raise common.Q1BError("precision solution block shape mismatch")
                for observed_value,expected_value in zip(observed_block,expected_block,strict=True):
                    if abs(_number(observed_value)-expected_value)>tolerance*max(1,abs(expected_value)): raise common.Q1BError("precision solution value mismatch")
        return expected


def verify(path: Path) -> dict[str,Any]:
    raw,proof=common.read_json(path); required={"candidate_id","payload","payload_sha256","production","schema","study_id"}
    if not isinstance(proof,dict) or set(proof)!=required or proof["schema"]!=PROOF_SCHEMA or proof["candidate_id"]!=CANDIDATE_ID or proof["study_id"]!=STUDY_ID or proof["production"]!="NO_GO_PRODUCTION_RESTRICTION_UNCHANGED": raise common.Q1BError("Q1D proof wrapper mismatch")
    payload=proof["payload"]
    if not isinstance(payload,dict) or set(payload)!={"rows","shard"} or payload["shard"] not in SHARDS or proof["payload_sha256"]!=common.sha256(common.canonical_bytes(payload)): raise common.Q1BError("Q1D proof payload mismatch")
    shard=payload["shard"]; rows=payload["rows"]; contradictions=[]; disagreements=[]; precision_unresolved=False; facts={}
    if shard in SHARDS[:2]:
        if not isinstance(rows,list) or len(rows)!=3: raise common.Q1BError("precision ladder coverage mismatch")
        values=[_verify_row(row,expected_division=32,expected_thickness="1e-6",expected_bits=bits,solution_required=bits==256) for row,bits in zip(rows,(128,192,256),strict=True)]; delta=abs(values[1]["response_ratio_eb"]-values[2]["response_ratio_eb"]); precision_unresolved=delta>mp.mpf("1e-18") or values[2]["scaled_residual"]>mp.mpf("1e-24"); facts={"precision_stable":delta<=mp.mpf("1e-18"),"scaled_residual_below_limit":values[2]["scaled_residual"]<=mp.mpf("1e-24"),"ultrathin_error_below_two_percent":values[2]["relative_error_eb"]<mp.mpf(".02")}
        if not facts["ultrathin_error_below_two_percent"]: contradictions.append("ULTRATHIN_ANALYTICAL_ERROR")
    else:
        expected=[(16,"1e-5"),(32,"1e-5"),(16,"1e-6"),(32,"1e-6")]
        if not isinstance(rows,list) or len(rows)!=len(expected): raise common.Q1BError("refinement coverage mismatch")
        values=[_verify_row(row,expected_division=division,expected_thickness=thickness,expected_bits=256,solution_required=True) for row,(division,thickness) in zip(rows,expected,strict=True)]; drift=abs(values[1]["response_ratio_eb"]-values[3]["response_ratio_eb"]); facts={"response_ratio_drift_below_limit":drift<=mp.mpf(".005"),"spatial_error_decreases_at_1e_5":values[1]["relative_error_eb"]<values[0]["relative_error_eb"],"spatial_error_decreases_at_1e_6":values[3]["relative_error_eb"]<values[2]["relative_error_eb"],"ultrathin_error_below_two_percent":values[3]["relative_error_eb"]<mp.mpf(".02")}
        if not facts["response_ratio_drift_below_limit"] or not facts["ultrathin_error_below_two_percent"]: contradictions.append("ULTRATHIN_LOCKING_RESPONSE")
        if not facts["spatial_error_decreases_at_1e_5"] or not facts["spatial_error_decreases_at_1e_6"]: contradictions.append("REFINEMENT_REGRESSION")
    return {"candidate_id":CANDIDATE_ID,"checker_id":CHECKER_ID,"classification_facts":facts,"contradictions":contradictions,"disagreements":disagreements,"precision_unresolved":precision_unresolved,"production":"NO_GO_PRODUCTION_RESTRICTION_UNCHANGED","proof_sha256":common.sha256(raw),"schema":CHECK_SCHEMA,"shard":shard,"study_id":STUDY_ID}


def main(argv: Sequence[str]|None=None) -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--verify-precision-proof",action="store_true",required=True); parser.add_argument("--proof",type=Path,required=True); parser.add_argument("--output",type=Path,required=True); args=parser.parse_args(argv)
    try: common.write_exclusive(args.output,verify(args.proof)); return 0
    except (OSError,ValueError,ZeroDivisionError,common.Q1BError) as exc: print(str(exc),file=sys.stderr); return 2


if __name__=="__main__": raise SystemExit(main())
