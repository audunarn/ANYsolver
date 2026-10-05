"""Matched Q4-trace CalculiX S4 plate under the saved native fz action.

This one-level physical comparator retains the original Q4 nodal action and
plate geometry. It does not establish mesh convergence or G0 acceptance.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np

from scripts.b3_e4_f03_c1_x8_s8r_fz_reference import (
    ACTION, ACTION_SHA, ROOT, THICKNESS, _expanded_midplane_nodes,
)
from scripts.b3_e4_f03_c1_x8_s8r_q4_action import _q4_action
from scripts.b3_e4_f03_c1_x8_s8r_fz_reference import _mesh as _s8r_mesh
from scripts.b3_e4_f03_plate_patch_work import local_grid
from scripts.b3_e4_f03_ccx_six_channel_compliance import _run
from scripts.b3_e4_f03_ccx_solid_bond_screen import (
    EXE, EXE_SHA, digest, unexpected_solver_diagnostics,
)
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_frd_u


OUTPUT=(ROOT/".qualification/b3-ge-e4-pl/"
        "f03-c1-x8-s4-q4-action-dev-20260928-v1")
S8R_RESULT=(ROOT/".qualification/b3-ge-e4-pl/"
    "f03-c1-x8-s8r-q4-projected-action-dev-20260928-v1/"
    "s8r-x8-q4-projection/result.json")


def _mesh():
    xs,ys=local_grid(8,transverse_cells=4)
    points={(2*i,2*j):(1+j*len(xs)+i,float(x),float(y))
            for j,y in enumerate(ys) for i,x in enumerate(xs)}
    cells=[(points[(2*i,2*j)][0],points[(2*i+2,2*j)][0],
            points[(2*i+2,2*j+2)][0],points[(2*i,2*j+2)][0])
           for j in range(len(ys)-1) for i in range(len(xs)-1)]
    return xs,ys,points,cells


def _deck(points,cells,loads):
    ordered=sorted(points.values())
    clamp=[n for n,x,_y in ordered if abs(x+.5)<1e-12]
    if not clamp:
        raise ArithmeticError("left-root S4 clamp missing")
    lines=["** G0 PRIVATE FIXED X8 Q4 ACTION S4 PLATE",
           "*NODE,NSET=AllNodes"]
    lines += [f"{n},{x:.17g},{y:.17g},0" for n,x,y in ordered]
    lines += ["*ELEMENT,TYPE=S4,ELSET=Plate"]
    lines += [f"{i},"+",".join(map(str,cell))
              for i,cell in enumerate(cells,1)]
    lines += ["*MATERIAL,NAME=Steel","*ELASTIC","210000000000,0.3",
              "*SHELL SECTION,ELSET=Plate,MATERIAL=Steel",
              f"{THICKNESS:.17g}","*STEP","*STATIC","*BOUNDARY"]
    lines += [f"{n},1,6,0" for n in clamp]
    lines += ["*CLOAD"]
    lines += [f"{n},3,{f:.17g}" for n,f in sorted(loads.items())]
    lines += ["*NODE FILE","U","*END STEP"]
    return "\n".join(lines)+"\n",clamp


def main():
    if digest(ACTION)!=ACTION_SHA or digest(EXE)!=EXE_SHA:
        raise ValueError("fixed action or solver identity changed")
    s8r=json.loads(S8R_RESULT.read_text())
    if s8r["status"]!="EXPLORATORY_COMPLETE":
        raise ValueError("matched S8R Q4 action result is unavailable")
    action=json.loads(ACTION.read_text())
    lambdas=np.asarray(action["report"]["fz_riesz_audit"][
        "isolated_fz_dual_action_N"],dtype=float)
    xs,ys,points,cells=_mesh()
    loads=_q4_action(xs,ys,points,lambdas)
    _x,_y,old_points,_cells=_s8r_mesh(8)
    old_loads=_q4_action(xs,ys,old_points,lambdas)
    old_positions={n:(x,y) for n,x,y in old_points.values()}
    new_positions={n:(x,y) for n,x,y in points.values()}
    by_position={new_positions[n]:v for n,v in loads.items()}
    defect=max(abs(by_position[old_positions[n]]-v)
               for n,v in old_loads.items())/max(1.,max(map(abs,old_loads.values())))
    if defect>1e-14:
        raise ArithmeticError("S4 and native-proven S8R nodal action differ")
    deck,clamp=_deck(points,cells,loads)
    folder=OUTPUT/"s4-x8-q4-projection"
    if folder.exists():
        raise FileExistsError(folder)
    folder.mkdir(parents=True)
    stem="fixed-x8-fz-s4-q4-projection"
    deck_path=folder/f"{stem}.inp"
    deck_path.write_text(deck,encoding="utf-8")
    code,stdout,stderr,elapsed,peak,failure=_run(stem,folder)
    (folder/"stdout.log").write_bytes(stdout)
    (folder/"stderr.log").write_bytes(stderr)
    work=None
    mapping_info=None
    if failure is None:
        if code!=0:
            failure=f"CALCULIX_EXIT_{code}"
        else:
            diagnostics=unexpected_solver_diagnostics(
                stdout.decode(errors="replace")+
                stderr.decode(errors="replace")+
                (folder/f"{stem}.cvg").read_text(errors="replace"),
                c1_penalty=False)
            if stdout.decode(errors="replace").count("Job finished")!=1 or diagnostics:
                failure=f"SOLVER_DIAGNOSTICS_{diagnostics[:5]}"
            else:
                frd=folder/f"{stem}.frd"
                if not frd.exists():
                    failure="FULL_FIELD_FRD_MISSING"
                else:
                    mapping,error,expanded,centres,pairs=(
                        _expanded_midplane_nodes(frd,points,loads))
                    response=_read_frd_u(frd)
                    if not {n for entries in mapping.values()
                            for n,_ in entries}.issubset(response):
                        failure="LINE_RESPONSE_MISSING"
                    else:
                        work=float(sum(force*sum(weight*response[node][2]
                            for node,weight in mapping[original])
                            for original,force in loads.items()))
                        mapping_info={"max_location_error_m":error,
                                      "expanded_nodes":expanded,
                                      "centre_nodes":centres,
                                      "face_pairs":pairs}
                        if not np.isfinite(work) or work<=0:
                            failure="NONPOSITIVE_OR_NONFINITE_WORK"
    result={
        "classification":"independent S4 plate under native Q4-projected fz action",
        "status":"EXPLORATORY_COMPLETE" if failure is None else "EXPLORATORY_FAILURE",
        "failure":failure,"s4_s8r_q4_action_max_relative_defect":defect,
        "s4_work_J":work,"s8r_q4_work_J":s8r["q4_s8r_work_J"],
        "e4_shell_work_J":s8r["e4_shell_work_J"],
        "mapping":mapping_info,"seconds":elapsed,"peak_solver_rss_bytes":peak,
        "exit_code":code,"nodes":len(points),"elements":len(cells),
        "clamp_nodes":len(clamp),
        "source_commit":subprocess.check_output(("git","rev-parse","HEAD"),
                                                 cwd=ROOT,text=True).strip(),
        "runner_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "action_sha256":ACTION_SHA,"s8r_q4_result_sha256":digest(S8R_RESULT),
        "solver_sha256":EXE_SHA,"deck_sha256":digest(deck_path),
        "limits":["single fixed x8 Q4-trace comparison","120 s",
                  "2 GiB sampled RSS","one numerical thread",
                  "not converged physical reference or G0 acceptance"],
    }
    (folder/"result.json").write_text(json.dumps(result,sort_keys=True,
        indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({k:result[k] for k in (
        "status","failure","s4_s8r_q4_action_max_relative_defect",
        "s4_work_J","s8r_q4_work_J","e4_shell_work_J","seconds")},sort_keys=True))
    if failure is not None:
        raise SystemExit(1)


if __name__=="__main__":
    main()
