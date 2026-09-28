"""Separate x8 S8R solve under the native Q4-projected fz nodal action.

The result distinguishes load-space aliasing from shell stiffness in the
fixed physical P0 fz witness. It is not a continuous-line convergence test.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np

from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_weak_line_candidate import LineMultiplierSpace
from scripts.b3_e4_f03_c1_x8_s8r_fz_reference import (
    ACTION, ACTION_SHA, ROOT, _deck, _expanded_midplane_nodes, _mesh,
)
from scripts.b3_e4_f03_c1_native_mixed_metric import T
from scripts.b3_e4_f03_c1_material_line_mixed_metric import _hash
from scripts.b3_e4_f03_material_line_position import MaterialLinePosition
from scripts.b3_e4_f03_material_line_space_screen import _rows
from scripts.b3_e4_f03_plate_patch_work import local_grid
from scripts.b3_e4_f03_square_section_control import square_torsion_constant
from scripts.b3_e4_f03_ccx_six_channel_compliance import _run
from scripts.b3_e4_f03_ccx_solid_bond_screen import (
    EXE, EXE_SHA, digest, unexpected_solver_diagnostics,
)
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_frd_u


OUTPUT = (ROOT/".qualification/b3-ge-e4-pl/"
          "f03-c1-x8-s8r-q4-projected-action-dev-20260928-v1")


def _q4_action(xs, ys, points, actions):
    j = np.flatnonzero(np.isclose(ys,0.,atol=1e-14,rtol=0.))
    if len(j) != 1:
        raise ArithmeticError("Q4 material line not on mesh node row")
    y2 = 2*int(j[0])
    loads = {}
    for k in range(8):
        a, b = xs[7+k], xs[8+k]
        if abs(a-(.9+k*.1/8)) > 1e-12 or abs(b-(.9+(k+1)*.1/8)) > 1e-12:
            raise ArithmeticError("registered x8 Q4 cuts changed")
        for ix2 in (2*(7+k),2*(8+k)):
            node = points[(ix2,y2)][0]
            loads[node] = loads.get(node,0.)+actions[k]/2
    return loads


def main():
    if digest(ACTION) != ACTION_SHA or digest(EXE) != EXE_SHA:
        raise ValueError("fixed physical action or solver identity changed")
    record = json.loads(ACTION.read_text())
    actions = np.asarray(record["report"]["fz_riesz_audit"][
        "isolated_fz_dual_action_N"],dtype=float)
    xs,ys,points,cells = _mesh(8)
    loads = _q4_action(xs,ys,points,actions)
    shell_xs,shell_ys=local_grid(8,transverse_cells=4)
    if not (np.array_equal(xs,shell_xs) and np.array_equal(ys,shell_ys)):
        raise ArithmeticError("reference and native mesh cuts differ")
    beam=build(18,z_offset=.0675,
               torsion_constant=square_torsion_constant(),
               reference_profile="c1_tangent_2um")
    line=MaterialLinePosition(xs,ys,beam,thickness=T)
    rows,_masses=_rows(line,LineMultiplierSpace(
        "piecewise_constant",tuple(np.linspace(0.,1.,9))))
    dual=np.zeros(len(rows))
    dual[2::6]=actions
    native_shell=rows[:,:6*len(xs)*len(ys)].T@dual
    by_id={node:(x,y) for node,x,y in points.values()}
    assembled=np.zeros_like(native_shell)
    for node,force in loads.items():
        x,y=by_id[node]
        ix=np.flatnonzero(np.isclose(xs,x,atol=1e-12,rtol=0.))
        iy=np.flatnonzero(np.isclose(ys,y,atol=1e-12,rtol=0.))
        if len(ix)!=1 or len(iy)!=1:
            raise ArithmeticError("projected Q4 force is not on a native node")
        assembled[6*(int(iy[0])*len(xs)+int(ix[0]))+2]+=force
    defect=float(np.linalg.norm(assembled-native_shell)/max(1.,
                  np.linalg.norm(native_shell)))
    if defect>1e-12:
        raise ArithmeticError("Q4 nodal load does not match native C-transpose")
    continuous=json.loads((ROOT/".qualification/b3-ge-e4-pl/"
        "f03-c1-x8-s8r-fz-reference-dev-20260928-v4/s8r-x8/result.json").read_text())
    if (continuous["status"]!="EXPLORATORY_COMPLETE" or
            continuous["action_sha256"]!=ACTION_SHA):
        raise ValueError("independent continuous-action S8R result unavailable")
    deck,clamp=_deck(points,cells,loads)
    folder=OUTPUT/"s8r-x8-q4-projection"
    if folder.exists():
        raise FileExistsError(folder)
    folder.mkdir(parents=True)
    stem="fixed-x8-fz-s8r-q4-projection"
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
        "classification":"independent S8R response to native Q4-projected fz nodal action",
        "status":"EXPLORATORY_COMPLETE" if failure is None else "EXPLORATORY_FAILURE",
        "failure":failure,"q4_native_transpose_relative_defect":defect,
        "q4_nodal_action_N":{str(k):v for k,v in loads.items()},
        "q4_action_force_N":float(sum(loads.values())),
        "q4_action_moment_y_Nm":float(-sum(by_id[k][0]*v
                                                for k,v in loads.items())),
        "q4_s8r_work_J":work,
        "s8r_continuous_x8_work_J":continuous["plate_action_work_J"],
        "e4_shell_work_J":record["report"]["fz_riesz_audit"][
            "shell_exact_drill_supremal_work_sq"],
        "mapping":mapping_info,"seconds":elapsed,"peak_solver_rss_bytes":peak,
        "exit_code":code,"nodes":len(points),"elements":len(cells),
        "clamp_nodes":len(clamp),
        "source_commit":subprocess.check_output(("git","rev-parse","HEAD"),
                                                 cwd=ROOT,text=True).strip(),
        "runner_sha256":_hash(Path(__file__)),"action_sha256":ACTION_SHA,
        "continuous_reference_sha256":digest(ROOT/".qualification/b3-ge-e4-pl/"
            "f03-c1-x8-s8r-fz-reference-dev-20260928-v4/s8r-x8/result.json"),
        "solver_sha256":EXE_SHA,"deck_sha256":digest(deck_path),
        "limits":["120 s","2 GiB RSS","one numerical thread",
                  "single fixed x8 discrete-action discriminator, not physical convergence"],
    }
    (folder/"result.json").write_text(json.dumps(result,sort_keys=True,
        indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({k:result[k] for k in (
        "status","failure","q4_native_transpose_relative_defect",
        "q4_s8r_work_J","s8r_continuous_x8_work_J","e4_shell_work_J",
        "seconds","peak_solver_rss_bytes")},sort_keys=True))
    if failure is not None:
        raise SystemExit(1)


if __name__=="__main__":
    main()
