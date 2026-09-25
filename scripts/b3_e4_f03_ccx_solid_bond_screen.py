"""Bounded 3D solid plate/stiffener bond discriminator, not G0 acceptance.

The plate and finite square stiffener share interface nodes. No beam/shell
MPC, drilling spring, penalty, or inferred reference offset is present.
The two imposed plate-edge shears distinguish a line-tangent rotation from
the rotation of a finite bonded region at a free stiffener termination.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

import numpy as np


WORKTREE = Path(__file__).resolve().parents[1]
EXE = Path("C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/"
           "calculix-223/CalculiX-2.23.0-win-x64/bin/ccx.exe")
EXE_SHA = "27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f"
TIMEOUT_SECONDS = 120
GAMMA = 1e-4
PLATE_X_MM = (-500, -250, 0, 250, 500, 750, 1000, 1250, 1500)
PLATE_Y_MM = (-500, -250, -50, 0, 50, 250, 500)
PLATE_Z_MM = (-35, 0, 35)
BAR_X_MM = (0, 250, 500, 750, 1000)
BAR_Y_MM = (-50, 0, 50)
BAR_Z_MM = (35, 85, 135)
STATIONS_MM = (0, 250, 500, 750, 1000)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cuts(values: tuple[int, ...], factor: int) -> tuple[Fraction, ...]:
    if type(factor) is not int or factor not in (1, 2):
        raise ValueError("bounded solid mesh factor must be 1 or 2")
    return tuple(Fraction(a)+(Fraction(b-a)*k)/factor
                 for a,b in zip(values[:-1],values[1:])
                 for k in range(factor))+(Fraction(values[-1]),)


def _number(value: float) -> str:
    # CalculiX input fields are bounded; these coordinates are rational mm cuts.
    return f"{value:.12g}"


def _set_lines(indices: set[int] | list[int]) -> list[str]:
    ordered=sorted(indices)
    return [",".join(str(v) for v in ordered[i:i+12])
            for i in range(0,len(ordered),12)]


def build(factor: int, shear: str) -> tuple[str, dict]:
    """Return an exact-coordinate conforming C3D8 deck and probe identity."""
    if shear not in ("uy_x", "ux_y", "tip_mx", "tip_fz"):
        raise ValueError("undeclared solid-bond loading")
    px,py,pz=(_cuts(v,factor) for v in
              (PLATE_X_MM,PLATE_Y_MM,PLATE_Z_MM))
    bx,by,bz=(_cuts(v,factor) for v in
              (BAR_X_MM,BAR_Y_MM,BAR_Z_MM))
    coordinates: dict[tuple[Fraction,Fraction,Fraction],int]={}
    plate_nodes=set()
    bar_nodes=set()

    def node(key: tuple[Fraction,Fraction,Fraction]) -> int:
        if key not in coordinates:
            coordinates[key]=len(coordinates)+1
        return coordinates[key]

    for z in pz:
        for y in py:
            for x in px:
                plate_nodes.add(node((x,y,z)))
    for z in bz:
        for y in by:
            for x in bx:
                bar_nodes.add(node((x,y,z)))

    def cells(xs,ys,zs):
        for iz in range(len(zs)-1):
            for iy in range(len(ys)-1):
                for ix in range(len(xs)-1):
                    x0,x1=xs[ix:ix+2]
                    y0,y1=ys[iy:iy+2]
                    z0,z1=zs[iz:iz+2]
                    yield tuple(node(p) for p in (
                        (x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),
                        (x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)))

    plate_cells=tuple(cells(px,py,pz))
    bar_cells=tuple(cells(bx,by,bz))
    if len(set(coordinates.values()))!=len(coordinates):
        raise AssertionError("duplicate solid node identity")
    interface={(x,y,Fraction(35)) for x in bx for y in by}
    if not all(coordinates[p] in plate_nodes & bar_nodes for p in interface):
        raise AssertionError("plate/bar interface is not conforming")
    boundary={coordinates[(x,y,z)] for z in pz for y in py for x in px
              if x in (px[0],px[-1]) or y in (py[0],py[-1])}
    if boundary & (bar_nodes-plate_nodes):
        raise AssertionError("bar has a directly prescribed node")
    station_nodes={str(s): sorted(coordinates[(Fraction(s),y,z)]
                                  for y in by for z in bz)
                   for s in STATIONS_MM}
    surface_x=(250,500,750) if factor==1 else (375,500,625)
    surface={(x,y):coordinates[(Fraction(x),Fraction(y),Fraction(35))]
             for x in surface_x for y in (-50,0,50)}
    probe=set().union(*station_nodes.values(),surface.values())
    lines=["** BOUNDED C3D8 PLATE AND CONFORMING SOLID STIFFENER; DEVELOPMENT ONLY",
           f"** factor={factor}; shear={shear}; gamma={_number(GAMMA)}",
           "*NODE,NSET=AllNodes"]
    inverse={index:key for key,index in coordinates.items()}
    for index in range(1,len(inverse)+1):
        xyz=inverse[index]
        lines.append(f"{index},"+",".join(_number(float(v)/1000) for v in xyz))
    lines.append("*ELEMENT,TYPE=C3D8,ELSET=Plate")
    for eid,cell in enumerate(plate_cells,1):
        lines.append(f"{eid},"+",".join(map(str,cell)))
    lines.append("*ELEMENT,TYPE=C3D8,ELSET=Stiffener")
    for eid,cell in enumerate(bar_cells,len(plate_cells)+1):
        lines.append(f"{eid},"+",".join(map(str,cell)))
    lines.extend(("*MATERIAL,NAME=Isotropic", "*ELASTIC", "210000000000,0.3",
                  "*SOLID SECTION,ELSET=Plate,MATERIAL=Isotropic",
                  "*SOLID SECTION,ELSET=Stiffener,MATERIAL=Isotropic",
                  "*NSET,NSET=Probe"))
    lines.extend(_set_lines(probe))
    lines.append("*NSET,NSET=PlateEdge")
    lines.extend(_set_lines(boundary))
    lines.extend(("*STEP", "*STATIC", "*BOUNDARY"))
    for index in sorted(boundary):
        x,y,_=inverse[index]
        values=((0.,GAMMA*float(x)/1000,0.) if shear=="uy_x" else
                (GAMMA*float(y)/1000,0.) if shear=="ux_y" else
                (0.,0.,0.))
        for dof,value in enumerate(values,1):
            lines.append(f"{index},{dof},{dof},{_number(value)}")
    applied={}
    if shear in ("tip_mx","tip_fz"):
        tip=tuple(coordinates[(Fraction(1000),y,z)] for y in by for z in bz)
        # Trapezoidal face integration of a distributed force/couple; each
        # discrete load has the exact requested resultant about the bar axis.
        weights={index:(.5 if j in (0,len(by)-1) else 1.)*
                        (.5 if k in (0,len(bz)-1) else 1.)
                 for j,y in enumerate(by) for k,z in enumerate(bz)
                 for index in (coordinates[(Fraction(1000),y,z)],)}
        if shear=="tip_fz":
            normalizer=sum(weights.values())
            applied={index:(0.,0.,1000.*weight/normalizer)
                     for index,weight in weights.items()}
        else:
            polar=sum(weight*(float(inverse[index][1]/1000)**2+
                              (float(inverse[index][2]/1000)-.085)**2)
                      for index,weight in weights.items())
            applied={index:(0.,-100.*weight*(float(inverse[index][2]/1000)-.085)/polar,
                            100.*weight*float(inverse[index][1]/1000)/polar)
                     for index,weight in weights.items()}
        if set(applied)!=set(tip):
            raise AssertionError("incomplete loaded end face")
        lines.append("*CLOAD")
        for index,force in sorted(applied.items()):
            for dof,value in enumerate(force,1):
                if value:
                    lines.append(f"{index},{dof},{_number(value)}")
    lines.extend(("*NODE PRINT,NSET=Probe", "U",
                  "*NODE PRINT,NSET=PlateEdge", "RF",
                  "*END STEP"))
    meta={"factor":factor,"shear":shear,"gamma":GAMMA,
          "node_count":len(coordinates),"plate_elements":len(plate_cells),
          "bar_elements":len(bar_cells),"shared_interface_nodes":len(interface),
          "boundary_nodes":len(boundary),"boundary_node_ids":sorted(boundary),
          "probe_node_ids":sorted(probe),
          "bar_station_nodes":station_nodes,
          "probe_coordinates_m":{str(index):[float(v)/1000 for v in inverse[index]]
                                 for index in probe},
          "boundary_coordinates_m":{str(index):[float(v)/1000 for v in inverse[index]]
                                    for index in boundary},
          "applied_nodal_forces_N":{str(index):list(force)
                                    for index,force in applied.items()},
          "surface_nodes":{f"{x},{y}":index for (x,y),index in surface.items()},
          "model":"3D conforming C3D8 plate/bar; plate [-.5,1.5]x[-.5,.5]x[-.035,.035] m; bar [0,1]x[-.05,.05]x[.035,.135] m; E=210 GPa, nu=.3",
          "boundary":"all three translations on plate perimeter follow declared affine shear; bar has no direct supports or loads"}
    return "\n".join(lines)+"\n",meta


def parse_nodal_vectors(dat: str, expected: set[int],
                        quantity: str, node_set: str) -> dict[int,np.ndarray]:
    lines=dat.splitlines()
    starts=[i for i,line in enumerate(lines)
            if re.search(rf"(?i)^\s*{re.escape(quantity)}\s*\(",line) and
            re.search(rf"(?i)for set {re.escape(node_set)}\b",line)]
    if len(starts)!=1:
        raise ValueError(f"one {node_set} {quantity} block required")
    result={}
    for line in lines[starts[0]+1:]:
        parts=line.split()
        if not parts:
            if result:
                break
            continue
        if len(parts)!=4 or not parts[0].isdigit():
            if result:
                break
            continue
        node=int(parts[0])
        value=np.array([float(v) for v in parts[1:]])
        if node in result or not np.isfinite(value).all():
            raise ValueError("invalid or repeated nodal vector")
        result[node]=value
    if set(result)!=expected:
        raise ValueError("incomplete nodal vector inventory")
    return result


def parse_probe_displacements(dat: str, expected: set[int]) -> dict[int,np.ndarray]:
    return parse_nodal_vectors(dat,expected,"displacements","PROBE")


def _wrench(forces: dict[int,np.ndarray], xyz: dict[str,list[float]]) -> list[float]:
    resultant=np.sum(tuple(forces.values()),axis=0)
    moment=np.sum(tuple(np.cross(np.array(xyz[str(index)]),force)
                        for index,force in forces.items()),axis=0)
    return [*resultant.tolist(),*moment.tolist()]


def recover(meta: dict, displacement: dict[int,np.ndarray],
            reactions: dict[int,np.ndarray] | None = None) -> dict:
    surface=meta["surface_nodes"]
    def value(x,y):
        return displacement[surface[f"{x},{y}"]]
    left,right=((250,750) if meta["factor"]==1 else (375,625))
    def local(x,y):
        a,b=((left,500) if x<500 else (500,right))
        return value(a,y)+(value(b,y)-value(a,y))*((x-a)/(b-a))
    tangent=(local(550,0)[1]-local(450,0)[1])/.1
    patch=np.array([(x/1000,y/1000) for x in (450,550)
                     for y in (-50,50)],dtype=float)
    pu=np.array([local(x,y)[:2] for x in (450,550)
                  for y in (-50,50)])
    centered=patch-patch.mean(axis=0)
    patch_yaw=float(np.sum(centered[:,0]*pu[:,1]-centered[:,1]*pu[:,0])/
                    np.sum(centered**2))
    stations={}
    for station,indices in meta["bar_station_nodes"].items():
        xyz=np.array([meta["probe_coordinates_m"][str(node)] for node in indices])
        center=np.array([float(station)/1000,0.,.085])
        design=np.zeros((3*len(indices),6))
        response=np.array([displacement[node] for node in indices]).reshape(-1)
        for i,relative in enumerate(xyz-center):
            x,y,z=relative
            design[3*i:3*i+3,:3]=np.eye(3)
            design[3*i:3*i+3,3:]=((0.,z,-y),(-z,0.,x),(y,-x,0.))
        fitted=np.linalg.lstsq(design,response,rcond=None)[0]
        residual=(response-design@fitted).reshape(-1,3)
        stations[station]={"translation_m":fitted[:3].tolist(),
                           "section_rotation_rad":fitted[3:].tolist(),
                           "max_warping_residual_m":float(np.linalg.norm(residual,axis=1).max()),
                           "node_count":len(indices)}
    result={"centerline_tangent_yaw_rad":float(tangent),
            "surface_square_patch_yaw_rad":patch_yaw,
            "surface_square_patch_half_width_m":.05,
            "station_motion":stations}
    if reactions is not None:
        applied={int(index):np.array(force) for index,force in
                 meta["applied_nodal_forces_N"].items()}
        applied_wrench=(_wrench(applied,meta["probe_coordinates_m"])
                        if applied else [0.]*6)
        support_wrench=_wrench(reactions,meta["boundary_coordinates_m"])
        result["applied_wrench_N_Nm"]=applied_wrench
        result["support_wrench_N_Nm"]=support_wrench
        result["wrench_imbalance_N_Nm"]=(np.array(applied_wrench)+
                                          np.array(support_wrench)).tolist()
    return result


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--suite",choices=("shear","loads"),default="shear")
    args=parser.parse_args()
    if digest(EXE)!=EXE_SHA:
        raise ValueError("CalculiX executable identity changed")
    head=subprocess.run(("git","rev-parse","HEAD"),cwd=WORKTREE,
                        check=True,capture_output=True,text=True).stdout.strip()
    if subprocess.run(("git","status","--porcelain"),cwd=WORKTREE,
                      check=True,capture_output=True,text=True).stdout.strip():
        raise ValueError("solid bond screen requires clean source")
    root=args.root.resolve()
    root.mkdir(parents=True,exist_ok=False)
    manifest={"status":"EXPLORATORY_NOT_G0_ACCEPTANCE",
              "question":("finite physical bond yaw under two affine shears"
                          if args.suite=="shear" else
                          "physical solid-bond end torque and transverse-force transfer"),
              "source_head":head,"source_sha256":digest(Path(__file__)),
              "executable":str(EXE),"executable_sha256":EXE_SHA,
              "cases":[(factor,shear) for factor in (1,2)
                       for shear in (("uy_x","ux_y") if args.suite=="shear"
                                     else ("tip_mx","tip_fz"))],
              "limit":{"omp_threads":1,"timeout_seconds_each":TIMEOUT_SECONDS},
              "limits_of_claim":["3D solid idealization, not E4 or B3",
                                 "two development mesh levels, not convergence qualification",
                                 "prescribed plate perimeter and free bar ends"]}
    (root/"manifest.json").write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n")
    records=[]
    for factor,shear in manifest["cases"]:
        name=f"solid-{factor}-{shear}"
        folder=root/name
        folder.mkdir()
        deck,meta=build(factor,shear)
        (folder/f"{name}.inp").write_text(deck,encoding="ascii")
        (folder/"model.json").write_text(json.dumps(meta,sort_keys=True,indent=2)+"\n")
        environment=os.environ.copy()
        environment["OMP_NUM_THREADS"]="1"
        start=time.perf_counter()
        failure=None
        try:
            run=subprocess.run((str(EXE),"-i",name),cwd=folder,env=environment,
                               capture_output=True,timeout=TIMEOUT_SECONDS,check=False)
            code,stdout,stderr=run.returncode,run.stdout,run.stderr
        except subprocess.TimeoutExpired as exc:
            code,stdout,stderr=None,exc.stdout or b"",exc.stderr or b""
            failure="TIMEOUT_120_SECONDS"
        (folder/"stdout.log").write_bytes(stdout)
        (folder/"stderr.log").write_bytes(stderr)
        parsed=None
        if failure is None and code!=0:
            failure=f"CALCULIX_EXIT_{code}"
        if failure is None:
            try:
                out=stdout.decode(errors="replace")
                sta=(folder/f"{name}.sta").read_text(errors="replace")
                dat=(folder/f"{name}.dat").read_text(errors="replace")
                status_rows=[re.match(r"^\s*1\s+1\s+1\s+\d+\s+([\d.Ee+-]+)\s+([\d.Ee+-]+)\s+([\d.Ee+-]+)\s*$",line)
                             for line in sta.splitlines()]
                complete=[m for m in status_rows if m is not None]
                if (out.count("Job finished")!=1 or len(complete)!=1 or
                    abs(float(complete[0].group(1))-1.)>1e-10 or
                    re.search(r"(?i)\b(warning|error|fatal)\b",out+sta+dat+
                              stderr.decode(errors="replace"))):
                    raise ValueError("solver diagnostic or incomplete job")
                probes=parse_probe_displacements(dat,set(meta["probe_node_ids"]))
                reactions=parse_nodal_vectors(dat,set(meta["boundary_node_ids"]),
                                              "forces","PLATEEDGE")
                parsed=recover(meta,probes,reactions)
            except (OSError,ValueError) as exc:
                failure=f"PARSE_{type(exc).__name__}: {exc}"
        record={"case":name,"status":"EXPLORATORY_COMPLETE" if failure is None
                else "EXPLORATORY_FAILURE","failure":failure,"exit_code":code,
                "seconds":time.perf_counter()-start,"model":meta,
                "response":parsed,
                "files_sha256":{p.name:digest(p) for p in sorted(folder.iterdir())
                                if p.is_file()}}
        (folder/"result.json").write_text(json.dumps(record,sort_keys=True,
                                      indent=2,allow_nan=False)+"\n")
        records.append(record)
        print(json.dumps({"case":name,"status":record["status"],
                          "failure":failure,"seconds":record["seconds"]}),flush=True)
        if failure:
            break
    (root/"result.json").write_text(json.dumps(records,sort_keys=True,
                                     indent=2,allow_nan=False)+"\n")
    return 0 if len(records)==4 and all(r["failure"] is None for r in records) else 1


if __name__=="__main__":
    raise SystemExit(main())
