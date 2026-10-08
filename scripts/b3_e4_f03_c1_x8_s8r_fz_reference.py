"""Fixed eight-interval fz action on an independent CalculiX S8R plate.

Development discriminator only. The same continuous line force density is
integrated on each S8R resolution; no native material-line constraint is
enforced here and no multiplier policy is selected.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np

from scripts.b3_e4_f03_ccx_six_channel_compliance import _run
from scripts.b3_e4_f03_ccx_solid_bond_screen import (
    EXE, EXE_SHA, digest, unexpected_solver_diagnostics,
)
from scripts.b3_e4_f03_plate_patch_work import local_grid
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_frd_u
from scripts._b3_e4_ccx_3d_tip_work_parser import _values


ROOT = Path(__file__).resolve().parents[1]
ACTION = ROOT / "docs/agent_plans/B3_E4_F03_C1_MATERIAL_LINE_X8_FZ_RIESZ_AUDIT_DEV_V1.json"
ACTION_SHA = "1ba05a44d9ad989c63299174e5be5e9e3f6caa8f982e9c5afb3b75c8c6421c6c"
THICKNESS = .035
Y_LINE = 0.


def _mesh(level: int):
    xs, ys = local_grid(level, transverse_cells=4)
    points = {}
    cells = []

    def node(ix2: int, iy2: int) -> int:
        key = (ix2, iy2)
        if key not in points:
            x = (xs[ix2//2] if ix2 % 2 == 0 else
                 (xs[ix2//2]+xs[ix2//2+1])/2)
            y = (ys[iy2//2] if iy2 % 2 == 0 else
                 (ys[iy2//2]+ys[iy2//2+1])/2)
            points[key] = (len(points)+1, float(x), float(y))
        return points[key][0]

    for j in range(len(ys)-1):
        for i in range(len(xs)-1):
            cells.append((node(2*i,2*j), node(2*i+2,2*j),
                          node(2*i+2,2*j+2), node(2*i,2*j+2),
                          node(2*i+1,2*j), node(2*i+2,2*j+1),
                          node(2*i+1,2*j+2), node(2*i,2*j+1)))
    if len(points) > 10000 or len(cells) > 1000:
        raise ValueError("bounded S8R reference size exceeded")
    return xs, ys, points, cells


def _loads(xs, ys, points, actions):
    j = np.flatnonzero(np.isclose(ys, Y_LINE, atol=1e-14, rtol=0.))
    if len(j) != 1:
        raise ArithmeticError("material line is not a mesh row")
    y2 = 2*int(j[0])
    loads = {}
    for i, (a, b) in enumerate(zip(xs[:-1], xs[1:])):
        if a < .9-1e-12 or b > 1.+1e-12:
            continue
        interval = min(7, int(np.floor((a-.9)/(.1/8)+1e-9)))
        if interval < 0 or b > .9+(interval+1)*(.1/8)+1e-12:
            raise ArithmeticError("S8R cell crosses a fixed P0 action break")
        density = actions[interval]/(.1/8)
        for key, weight in (((2*i,y2),1/6), ((2*i+1,y2),4/6),
                            ((2*i+2,y2),1/6)):
            index = points[key][0]
            loads[index] = loads.get(index,0.)+density*(b-a)*weight
    if not loads:
        raise ArithmeticError("no resolved line action")
    by_id = {index:(x,y) for index,x,y in points.values()}
    actual_force = float(sum(loads.values()))
    expected_force = float(sum(actions))
    actual_moment_y = float(-sum(by_id[n][0]*f for n,f in loads.items()))
    expected_moment_y = float(-sum((.9+(k+.5)*(.1/8))*f
                                   for k,f in enumerate(actions)))
    force_defect = abs(actual_force-expected_force)/max(1.,sum(map(abs,actions)))
    moment_defect = abs(actual_moment_y-expected_moment_y)/max(
        1.,sum(abs(f)*abs(.9+(k+.5)*(.1/8))
               for k,f in enumerate(actions)))
    if max(force_defect,moment_defect) > 1e-12:
        raise ArithmeticError("line action force or moment integration failed")
    return loads, {"force_N":actual_force,"moment_y_Nm":actual_moment_y,
                   "force_relative_defect":force_defect,
                   "moment_relative_defect":moment_defect}


def _deck(points, cells, loads):
    ordered = sorted(points.values())
    clamp = [n for n,x,_y in ordered if abs(x+.5)<1e-12]
    if not clamp:
        raise ArithmeticError("missing left-root clamp")
    lines = ["** G0 PRIVATE FIXED X8 FZ ACTION S8R PLATE", "*NODE,NSET=AllNodes"]
    lines += [f"{n},{x:.17g},{y:.17g},0" for n,x,y in ordered]
    lines += ["*ELEMENT,TYPE=S8R,ELSET=Plate"]
    lines += [f"{i},"+",".join(map(str,cell))
              for i,cell in enumerate(cells,1)]
    lines += ["*MATERIAL,NAME=Steel", "*ELASTIC", "210000000000,0.3",
              "*SHELL SECTION,ELSET=Plate,MATERIAL=Steel",
              f"{THICKNESS:.17g}", "*STEP", "*STATIC", "*BOUNDARY"]
    lines += [f"{n},1,6,0" for n in clamp]
    lines += ["*CLOAD"]
    lines += [f"{n},3,{f:.17g}" for n,f in sorted(loads.items())]
    # CalculiX expands S8R into 3D bricks. Request the complete shell/solid
    # response; the original AllNodes set alone produced an empty DISP block.
    lines += ["*NODE FILE", "U", "*END STEP"]
    return "\n".join(lines)+"\n", clamp


def _expanded_midplane_nodes(frd: Path, points, loads):
    """Map shell translations to generated mid or averaged face nodes."""
    coordinates = {}
    inside = False
    blocks = 0
    for line in frd.open(errors="replace"):
        if line.startswith("    2C"):
            inside = True
            blocks += 1
            continue
        if inside and line.startswith(" -3"):
            break
        if inside and line.startswith(" -1"):
            n, xyz = _values(line)
            coordinates[n] = np.asarray(xyz)
    if blocks != 1 or not coordinates:
        raise ValueError("one complete expanded S8R FRD coordinate block required")
    mapped = {}
    max_error = 0.
    centre_count = 0
    face_pair_count = 0
    originals = {n:(x,y) for n,x,y in points.values()}
    for original in loads:
        x,y = originals[original]
        def match(z):
            target = np.array((x,y,z))
            return [(n,float(np.linalg.norm(xyz-target)))
                    for n,xyz in coordinates.items()
                    if np.max(np.abs(xyz-target)) <= 3e-6]
        centre, bottom, top = match(0.),match(-THICKNESS/2),match(THICKNESS/2)
        if len(centre) == 1:
            mapped[original] = ((centre[0][0],1.),)
            max_error = max(max_error,centre[0][1])
            centre_count += 1
        elif not centre and len(bottom) == len(top) == 1:
            mapped[original] = ((bottom[0][0],.5),(top[0][0],.5))
            max_error = max(max_error,bottom[0][1],top[0][1])
            face_pair_count += 1
        else:
            raise ValueError("expanded S8R centre/face shell node mapping is ambiguous")
    mapped_ids = [n for entries in mapped.values() for n,_ in entries]
    if len(set(mapped_ids)) != len(mapped_ids):
        raise ValueError("expanded shell node mapping is not one to one")
    return mapped, max_error, len(coordinates), centre_count, face_pair_count


def run(level: int, root: Path, *, preflight_only: bool) -> dict:
    if level not in (8,16):
        raise ValueError("only registered x8/x16 physical comparator levels")
    if digest(ACTION) != ACTION_SHA or digest(EXE) != EXE_SHA:
        raise ValueError("saved action or executable identity changed")
    action = json.loads(ACTION.read_text())
    if (action["geometry"] != "C1 Q4 x8/y4; B3-18; 1:1 bond" or
            action["space_kind"] != "piecewise_constant" or
            not action["fz_riesz_audit"]):
        raise ValueError("saved isolated fz action identity changed")
    actions = np.asarray(action["report"]["fz_riesz_audit"][
        "isolated_fz_dual_action_N"],dtype=float)
    if actions.shape != (8,) or not np.isfinite(actions).all():
        raise ValueError("eight finite physical action resultants required")
    xs,ys,points,cells = _mesh(level)
    loads,wrench = _loads(xs,ys,points,actions)
    deck,clamp = _deck(points,cells,loads)
    folder = root/f"s8r-x{level}"
    if folder.exists():
        raise FileExistsError(folder)
    folder.mkdir(parents=True)
    stem = f"fixed-x8-fz-s8r-x{level}"
    deck_path = folder/f"{stem}.inp"
    deck_path.write_text(deck,encoding="utf-8")
    code,elapsed,peak,failure = None,0.,0,None
    work = None
    if not preflight_only:
        code,stdout,stderr,elapsed,peak,failure = _run(stem,folder)
        (folder/"stdout.log").write_bytes(stdout)
        (folder/"stderr.log").write_bytes(stderr)
        if failure is None:
            if code != 0:
                failure = f"CALCULIX_EXIT_{code}"
            else:
                diagnostics = unexpected_solver_diagnostics(
                    stdout.decode(errors="replace")+
                    stderr.decode(errors="replace")+
                    (folder/f"{stem}.cvg").read_text(errors="replace"),
                    c1_penalty=False)
                if stdout.decode(errors="replace").count("Job finished") != 1 or diagnostics:
                    failure = f"SOLVER_DIAGNOSTICS_{diagnostics[:5]}"
                else:
                    frds = list(folder.glob("*.frd"))
                    if len(frds) != 1:
                        failure = "ONE_FULL_FIELD_FRD_REQUIRED"
                    else:
                        u = _read_frd_u(frds[0])
                        (mapping, location_error, expanded_nodes,
                         centre_count, face_pair_count) = (
                            _expanded_midplane_nodes(frds[0],points,loads))
                        if not {n for entries in mapping.values()
                                for n,_ in entries}.issubset(u):
                            failure = "LINE_RESPONSE_MISSING"
                        else:
                            work = float(sum(f*sum(w*u[node][2]
                                  for node,w in mapping[n])
                                             for n,f in loads.items()))
                            if not np.isfinite(work) or work <= 0.:
                                failure = "NONPOSITIVE_OR_NONFINITE_WORK"
    result = {
        "classification":"fixed physical fz action; independent S8R plate diagnostic",
        "status": ("PREFLIGHT_PASSED" if preflight_only else
                   "EXPLORATORY_COMPLETE" if failure is None else "EXPLORATORY_FAILURE"),
        "failure":failure,"level":level,"nodes":len(points),"elements":len(cells),
        "clamp_nodes":len(clamp),"loaded_nodes":len(loads),"wrench":wrench,
        "plate_action_work_J":work,"e4_shell_action_work_J":action["report"][
            "fz_riesz_audit"]["shell_exact_drill_supremal_work_sq"],
        "seconds":elapsed,"peak_solver_rss_bytes":peak,"exit_code":code,
        "source_commit":subprocess.check_output(
            ("git","rev-parse","HEAD"),cwd=ROOT,text=True).strip(),
        "runner_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "action_sha256":ACTION_SHA,"solver_sha256":EXE_SHA,
        "deck_sha256":digest(deck_path),
        "frd_midplane_mapping": ({"max_location_error_m":location_error,
                                   "expanded_nodes":expanded_nodes,
                                   "mapped_line_nodes":len(mapping),
                                   "centre_nodes":centre_count,
                                   "averaged_face_pairs":face_pair_count}
                                  if not preflight_only and failure is None else None),
        "limits":["120 s per solve","2 GiB peak RSS","one numerical thread",
                  "fixed x8 P0 physical action on independent S8R plate",
                  "not G0B qualification or a multiplier-space selection"],
    }
    (folder/"result.json").write_text(json.dumps(result,indent=2,
        sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--level",type=int,choices=(8,16),required=True)
    parser.add_argument("--output-root",type=Path,required=True)
    parser.add_argument("--preflight-only",action="store_true")
    args=parser.parse_args()
    result=run(args.level,args.output_root,preflight_only=args.preflight_only)
    print(json.dumps({key:result[key] for key in (
        "status","failure","level","nodes","elements","wrench",
        "plate_action_work_J","seconds","peak_solver_rss_bytes")},sort_keys=True))
    if result["failure"] is not None:
        raise SystemExit(1)


if __name__=="__main__":
    main()
