"""Bounded physical plate-only C3D20R/E4 terminal-patch work comparison.

This is an exploratory external reference, not a coupled connection or G0 gate.
Both plates receive the same consistent top-face traction on x=[.9,1] m,
y=[-.05,.05] m and have the full x=-.5 m edge clamped.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import time

import numpy as np
from threadpoolctl import threadpool_info, threadpool_limits

from scripts._b3_e4_f03_e4_trial_panel import FlatE4TrialPanel
from scripts._b3_e4_f03_shell_finite_pose_candidate import reference_nodes
from scripts._b3_e4_f03_shell_spatial_linear_port import physical_shell_stiffness
from scripts._b3_e4_f03_shell_trace import make_shell
from scripts.b3_e4_f03_ccx_solid_bond_screen import (
    EXE, EXE_SHA, TIMEOUT_SECONDS, _number, _quad8_shape, _set_lines,
    _wrench, build, digest, parse_nodal_vectors,
)
from scripts.b3_e4_f03_terminal_shell_work import response


PATCH_X=(.9,1.)
PATCH_Y=(-.05,.05)
PATCH_AREA=.01
LOADS=("tip_mx","tip_fz")


def traction(y: float, loading: str) -> float:
    if loading == "tip_mx":
        return 100. / (.1 * (2*.05**3/3.)) * y
    if loading == "tip_fz":
        return 1000. / PATCH_AREA
    raise ValueError("undeclared plate-patch load")


def expected_wrench(loading: str) -> np.ndarray:
    return np.array((0.,0.,0.,100.,0.,0.) if loading=="tip_mx" else
                    (0.,0.,1000.,0.,-950.,0.))


def build_solid_plate(factor: int, loading: str) -> tuple[str,dict]:
    if factor not in (1,2,4) or loading not in LOADS:
        raise ValueError("bounded quadratic plate-patch case required")
    coupled,_=build(factor,"tip_mx",boundary_policy="left_root",
                    bond_policy="terminal",element_family="C3D20R")
    lines=coupled.splitlines()
    node_start=lines.index("*NODE,NSET=AllNodes")+1
    plate_header=lines.index("*ELEMENT,TYPE=C3D20R,ELSET=Plate")
    bar_header=lines.index("*ELEMENT,TYPE=C3D20R,ELSET=Stiffener")
    node_rows={int(line.split(",",1)[0]):line
               for line in lines[node_start:plate_header]}
    coords={index:np.array([float(v) for v in row.split(",")[1:]])
            for index,row in node_rows.items()}
    element_rows=lines[plate_header+1:bar_header]
    if len(element_rows)%2:
        raise AssertionError("quadratic plate connectivity was not paired")
    cells=[]
    for first,second in zip(element_rows[::2],element_rows[1::2]):
        a=[int(v) for v in first.split(",")]
        b=[int(v) for v in second.split(",")]
        if len(a)!=16 or len(b)!=5:
            raise AssertionError("quadratic plate connectivity changed")
        cells.append((a[0],tuple(a[1:]+b)))
    plate_nodes={node for _,cell in cells for node in cell}
    clamp={index for index in plate_nodes if abs(coords[index][0]+.5)<1e-12}
    if not clamp or any(abs(coords[i][0]+.5)>1e-12 for i in clamp):
        raise AssertionError("plate clamp inventory changed")
    points,weights=np.polynomial.legendre.leggauss(3)
    load={}
    faces=0
    for _,cell in cells:
        face=tuple(cell[i] for i in (4,5,6,7,12,13,14,15))
        xyz=np.array([coords[i] for i in face])
        if (not np.all(np.abs(xyz[:,2]-.035)<1e-12) or
            xyz[:,0].min()<PATCH_X[0]-1e-12 or
            xyz[:,0].max()>PATCH_X[1]+1e-12 or
            xyz[:,1].min()<PATCH_Y[0]-1e-12 or
            xyz[:,1].max()>PATCH_Y[1]+1e-12):
            continue
        faces+=1
        jac=(xyz[:,0].max()-xyz[:,0].min())*(
             xyz[:,1].max()-xyz[:,1].min())/4
        if jac<=0.:
            raise AssertionError("nonpositive plate-patch face measure")
        for xi,wi in zip(points,weights):
            for eta,wj in zip(points,weights):
                shape=_quad8_shape(float(xi),float(eta))
                y=float(shape@xyz[:,1])
                value=float(wi*wj*jac*traction(y,loading))
                for index,shape_value in zip(face,shape):
                    load[index]=load.get(index,0.)+value*float(shape_value)
    if faces!=2*factor*factor or not load:
        raise AssertionError("plate-patch face inventory changed")
    forces={i:np.array((0.,0.,f)) for i,f in load.items()}
    locations={str(i):coords[i].tolist() for i in load}
    wrench=np.asarray(_wrench(forces,locations))
    if np.linalg.norm(wrench-expected_wrench(loading))>1e-8:
        raise AssertionError("plate-patch load has wrong physical wrench")
    output=["** BOUNDED PLATE-ONLY C3D20R PATCH WORK; DEVELOPMENT ONLY",
            f"** factor={factor}; loading={loading}",
            "*NODE,NSET=AllNodes"]
    output.extend(node_rows[i] for i in sorted(plate_nodes))
    output.append("*ELEMENT,TYPE=C3D20R,ELSET=Plate")
    output.extend(element_rows)
    output.extend(("*MATERIAL,NAME=Isotropic","*ELASTIC","210000000000,0.3",
                   "*SOLID SECTION,ELSET=Plate,MATERIAL=Isotropic",
                   "*NSET,NSET=LoadedPatch"))
    output.extend(_set_lines(sorted(load)))
    output.append("*NSET,NSET=PlateClamp")
    output.extend(_set_lines(sorted(clamp)))
    output.extend(("*STEP","*STATIC","*BOUNDARY"))
    for index in sorted(clamp):
        for dof in (1,2,3):
            output.append(f"{index},{dof},{dof},0")
    output.append("*CLOAD")
    for index,value in sorted(load.items()):
        if abs(value)>1e-14:
            output.append(f"{index},3,{_number(value)}")
    output.extend(("*NODE PRINT,NSET=LoadedPatch","U",
                   "*NODE PRINT,NSET=PlateClamp","RF","*END STEP"))
    meta={"factor":factor,"loading":loading,"plate_elements":len(cells),
          "plate_nodes":len(plate_nodes),"patch_faces":faces,
          "loaded_node_ids":sorted(load),"clamp_node_ids":sorted(clamp),
          "coordinates_m":{str(i):coords[i].tolist() for i in load.keys()|clamp},
          "nodal_fz_n":{str(i):value for i,value in load.items()},
          "applied_wrench_N_Nm":wrench.tolist(),
          "support":"all plate x=-.5 m nodes fixed in x/y/z",
          "patch":"top z=.035 m, x=[.9,1] m, y=[-.05,.05] m",
          "load_definition":("t_z proportional to y, exact 100 N m Mx"
                             if loading=="tip_mx" else
                             "uniform t_z, 1000 N Fz at x=.95 m")}
    return "\n".join(output)+"\n",meta


def shell_patch_force(panel,loading: str) -> tuple[np.ndarray,np.ndarray]:
    if loading not in LOADS:
        raise ValueError("undeclared plate-patch load")
    force=np.zeros(6*panel.node_count)
    points,weights=np.polynomial.legendre.leggauss(3)
    def breaks(low,high,grid):
        return (low,*[v for v in grid if low+1e-12<v<high-1e-12],high)
    xgrid=[-.5+i/panel.n_s for i in range(panel.x_interval_count+1)]
    ygrid=[-.5+j/panel.n_y for j in range(panel.n_y+1)]
    xs=breaks(*PATCH_X,xgrid)
    ys=breaks(*PATCH_Y,ygrid)
    for x0,x1 in zip(xs[:-1],xs[1:]):
        for y0,y1 in zip(ys[:-1],ys[1:]):
            jac=(x1-x0)*(y1-y0)/4
            for xi,wi in zip(points,weights):
                x=(x0+x1)/2+(x1-x0)*float(xi)/2
                for eta,wj in zip(points,weights):
                    y=(y0+y1)/2+(y1-y0)*float(eta)/2
                    indices,shape=panel._shape(x,y)
                    for index,value in zip(indices,shape):
                        force[6*index+2]+=float(wi*wj*jac*traction(y,loading)*value)
    nodal=force.reshape(-1,6)
    xyz=reference_nodes(panel)
    wrench=np.r_[nodal[:,:3].sum(axis=0),
                 (np.cross(xyz,nodal[:,:3])+nodal[:,3:]).sum(axis=0)]
    if np.linalg.norm(wrench-expected_wrench(loading))>1e-8:
        raise AssertionError("E4 plate-patch load has wrong physical wrench")
    return force,wrench


def shell_case(level: int,loading: str) -> dict:
    panel=make_shell(level,"Q4",n_y=level)
    shell=FlatE4TrialPanel(panel)
    count=6*panel.node_count
    stiffness=shell.evaluate(np.zeros(count),.95).tangent
    physical=physical_shell_stiffness(panel).toarray()
    fixed={6*j*(panel.x_interval_count+1)+axis
           for j in range(panel.n_y+1) for axis in range(6)}
    free=np.array([i for i in range(count) if i not in fixed])
    load,wrench=shell_patch_force(panel,loading)
    measured=response(stiffness,load,free,physical=physical)
    return {"formulation":"Q4","level":level,"loading":loading,
            "nodes":panel.node_count,"elements":panel.element_count,
            "applied_wrench_N_Nm":wrench.tolist(),"response":measured}


def run(root: Path, factors: tuple[int,...], levels: tuple[int,...]) -> None:
    source=subprocess.check_output(("git","rev-parse","HEAD"),text=True).strip()
    if subprocess.check_output(("git","status","--porcelain"),text=True).strip():
        raise RuntimeError("plate-patch screen requires clean source")
    if digest(EXE)!=EXE_SHA:
        raise RuntimeError("CalculiX executable identity changed")
    root.mkdir(parents=True,exist_ok=False)
    manifest={"status":"EXPLORATORY_NOT_G0_ACCEPTANCE",
              "question":"Does physical E4 plate-only patch work agree with a section-resolved C3D20R plate under identical geometry, support and top-face traction?",
              "decision":"Material plate-only discrepancy directs shell map/stiffness investigation; agreement directs bonded-region and B3 warping investigation. Neither outcome selects a native attachment or line multiplier.",
              "source_sha":source,"runner_sha256":digest(Path(__file__)),
              "ccx_executable":str(EXE),"ccx_sha256":EXE_SHA,
              "solid_factors":factors,"shell_levels":levels,"loads":LOADS,
              "geometry":"plate [-.5,1.5]x[-.5,.5] m, thickness .07 m; top patch x=[.9,1], y=[-.05,.05] m",
              "material":"isotropic E=210 GPa, nu=.3",
              "supports":"full x=-.5 m plate edge fixed",
              "limits":{"ccx_seconds_each":TIMEOUT_SECONDS,"omp_threads":1,
                        "blas_threads":1},
              "scope":"linear plate-only external comparison; no bonded-beam, contact, nonlinear, exact face-minimum or production qualification",
              "python":platform.python_version(),"numpy":np.__version__}
    with threadpool_limits(limits=1):
        manifest["effective_threadpools"]=threadpool_info()
        (root/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
        records=[]
        for factor in factors:
            for loading in LOADS:
                name=f"plate-{factor}-{loading}"
                folder=root/name
                folder.mkdir()
                deck,meta=build_solid_plate(factor,loading)
                (folder/f"{name}.inp").write_text(deck,encoding="ascii")
                (folder/"model.json").write_text(json.dumps(meta,indent=2)+"\n")
                started=time.perf_counter()
                failure=None
                env=os.environ.copy()
                env["OMP_NUM_THREADS"]="1"
                try:
                    proc=subprocess.run((str(EXE),"-i",name),cwd=folder,
                                        env=env,capture_output=True,
                                        timeout=TIMEOUT_SECONDS,check=False)
                    code,stdout,stderr=proc.returncode,proc.stdout,proc.stderr
                except subprocess.TimeoutExpired as exc:
                    code,stdout,stderr=None,exc.stdout or b"",exc.stderr or b""
                    failure="TIMEOUT_120_SECONDS"
                (folder/"stdout.log").write_bytes(stdout)
                (folder/"stderr.log").write_bytes(stderr)
                if failure is None and code!=0:
                    failure=f"CALCULIX_EXIT_{code}"
                measured=None
                if failure is None:
                    try:
                        out=stdout.decode(errors="replace")
                        dat=(folder/f"{name}.dat").read_text(errors="replace")
                        sta=(folder/f"{name}.sta").read_text(errors="replace")
                        completed=[m for line in sta.splitlines()
                                   if (m:=re.match(
                                       r"^\s*1\s+1\s+1\s+\d+\s+([\d.Ee+-]+)\s+([\d.Ee+-]+)\s+([\d.Ee+-]+)\s*$",
                                       line)) is not None]
                        if (out.count("Job finished")!=1 or
                            len(completed)!=1 or
                            abs(float(completed[0].group(1))-1.)>1e-10 or
                            re.search(r"(?i)\b(warning|error|fatal)\b",
                                      out+sta+dat+stderr.decode(errors="replace"))):
                            raise ValueError("solver diagnostic or incomplete job")
                        disp=parse_nodal_vectors(dat,set(meta["loaded_node_ids"]),
                                                 "displacements","LoadedPatch")
                        reactions=parse_nodal_vectors(dat,set(meta["clamp_node_ids"]),
                                                      "forces","PlateClamp")
                        work=sum(meta["nodal_fz_n"][str(i)]*disp[i][2]
                                 for i in meta["loaded_node_ids"])
                        reaction_wrench=np.array(_wrench(reactions,meta["coordinates_m"]))
                        imbalance=np.linalg.norm(reaction_wrench+
                            np.array(meta["applied_wrench_N_Nm"]))
                        if (not np.isfinite(work) or work<=0 or
                            imbalance>1e-4*max(100.,1000.)):
                            raise ValueError("invalid plate work or global wrench balance")
                        measured={"compliance_work_j":float(work),
                                  "reaction_wrench_N_Nm":reaction_wrench.tolist(),
                                  "wrench_imbalance_N_Nm":float(imbalance)}
                    except (OSError,ValueError) as exc:
                        failure=f"PARSE_{type(exc).__name__}: {exc}"
                record={"case":name,"status":"EXPLORATORY_COMPLETE" if failure is None
                        else "EXPLORATORY_FAILURE","failure":failure,
                        "exit_code":code,"seconds":time.perf_counter()-started,
                        "response":measured,
                        "files_sha256":{p.name:digest(p) for p in folder.iterdir()
                                        if p.is_file()}}
                (folder/"result.json").write_text(json.dumps(record,indent=2,
                                                     allow_nan=False)+"\n")
                records.append(record)
                (root/"solid_results.json").write_text(json.dumps(records,indent=2,
                                                        allow_nan=False)+"\n")
                print(json.dumps({"case":name,"status":record["status"],
                                  "failure":failure}),flush=True)
                if failure:
                    return
        shell_records=[]
        for level in levels:
            for loading in LOADS:
                try:
                    item=shell_case(level,loading)
                    record={"case":f"shell-{level}-{loading}",
                            "status":"EXPLORATORY_COMPLETE","response":item}
                except Exception as exc:
                    record={"case":f"shell-{level}-{loading}",
                            "status":"EXPLORATORY_FAILURE",
                            "failure":f"{type(exc).__name__}: {exc}"}
                    shell_records.append(record)
                    (root/"shell_results.json").write_text(json.dumps(
                        shell_records,indent=2,allow_nan=False)+"\n")
                    raise
                shell_records.append(record)
                (root/"shell_results.json").write_text(json.dumps(
                    shell_records,indent=2,allow_nan=False)+"\n")
                print(json.dumps({"case":record["case"],
                                  "status":record["status"]}),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--factor",type=int,choices=(1,2,4),nargs="+",default=(1,2,4))
    parser.add_argument("--shell-level",type=int,choices=(2,4,8),nargs="+",default=(2,4,8))
    args=parser.parse_args()
    run(args.root,tuple(args.factor),tuple(args.shell_level))
