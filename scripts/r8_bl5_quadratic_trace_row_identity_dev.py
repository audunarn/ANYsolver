"""Prove same-grid weak P0 and nine-station rows sit in the 85-row space.

This is a bounded discrete-row identity, not a native BL5 stability result.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from scripts import r8_bl5_strong_hinge_pair_dev as pair
from scripts import r8_bl5_mx_matched_refinement_dev as matched
from scripts import r8_bl5_mx_coupled_shell_refinement_dev as shell_ref
from scripts import r8_bl5_mx_torsion_refinement_dev as beam_ref


def digest(path:Path)->str:
    return sha256(path.read_bytes()).hexdigest()


def evaluate()->dict:
    runtime=pair._runtime()
    shell_nodes,shell_elements=shell_ref._shell_mesh(*pair.LEVEL)
    beam_nodes,beam_elements=beam_ref._mesh(*pair.LEVEL)
    model=shell_ref._combined(shell_nodes,shell_elements,beam_nodes,beam_elements)
    nx=pair.LEVEL[0]
    weak,measure=matched._weak_rows(model,nx)
    sampled=pair._strong_rows(model,nx+1).toarray()
    complete=pair._strong_rows(model,2*nx+1).toarray()
    simpson=np.zeros((5*nx,5*(2*nx+1)))
    select=np.zeros((5*(nx+1),5*(2*nx+1)))
    for channel in range(5):
        for edge in range(nx):
            simpson[channel*nx+edge,channel*(2*nx+1)+2*edge:channel*(2*nx+1)+2*edge+3]=measure[edge]*np.array((1.,4.,1.))/6.
        for station in range(nx+1):
            select[channel*(nx+1)+station,channel*(2*nx+1)+2*station]=1.
    weak_reconstruction=simpson @ complete
    sampled_reconstruction=select @ complete
    absolute_weak=float(np.max(abs(weak_reconstruction-weak.toarray())))
    relative_weak=float(np.linalg.norm(weak_reconstruction-weak.toarray(),ord=np.inf)/max(np.linalg.norm(weak.toarray(),ord=np.inf),1e-30))
    absolute_sampled=float(np.max(abs(sampled_reconstruction-sampled)))
    if (relative_weak>1e-12 or absolute_sampled>1e-12 or
            np.linalg.matrix_rank(simpson)!=5*nx or
            np.linalg.matrix_rank(select)!=5*(nx+1)):
        raise ValueError("complete quadratic row space does not contain physical weak and sampled rows")
    return {"identity":"R8_BL5_C3D20_QUADRATIC_ROW_IDENTITY_DEV_V1",
        "status":"DISCRETE_ROW_IDENTITY_NOT_QUALIFIED",
        "source_sha256":digest(Path(__file__)),"level":pair.LEVEL,
        "physical_dofs":complete.shape[1],"weak_rows":weak.shape[0],
        "sampled_rows":sampled.shape[0],"complete_rows":complete.shape[0],
        "simpson_rank":int(np.linalg.matrix_rank(simpson)),
        "selection_rank":int(np.linalg.matrix_rank(select)),
        "weak_row_absolute_error":absolute_weak,
        "weak_row_relative_error":relative_weak,
        "sampled_row_absolute_error":absolute_sampled,
        "runtime":runtime,
        "interpretation":"P0 integrals and nine-station samples are exact linear combinations of 85 complete-quadratic rows on this body only; no native inf-sup or physical fidelity claim"}


def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve earlier row identity")
    result=evaluate()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({key:result[key] for key in (
        "status","weak_row_relative_error","sampled_row_absolute_error",
        "simpson_rank","selection_rank")}))


if __name__=="__main__":
    main()
